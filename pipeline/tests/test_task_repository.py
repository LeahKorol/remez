"""
Unit tests for TaskRepository class.
"""

from datetime import datetime, timedelta

import pytest
from constants import TaskStatus
from errors import PipelineCapacityExceededError
from models.models import TaskResults
from services.task_repository import TaskRepository, task_creation_mutex
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture(scope="session")
def test_engine():
    """Create a single test database engine for the entire test session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    yield engine  # each test gets this engine

    engine.dispose()  # Cleanup: Dispose engine after all tests


@pytest.fixture
def test_session(test_engine):
    """Create a fresh test database session for each test with automatic cleanup."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    # Cleanup: Rollback transaction and close connection after each test
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(autouse=True)
def mock_create_session(test_session, mocker):
    """
    Mock the create_session function to redirect database operations to test database.

    This fixture intercepts calls to create_session() in TaskRepository and replaces
    them with our test_session. This ensures that:
    1. Tests don't affect the real database
    2. All database operations use the in-memory test database
    3. Tests are isolated from each other

    The mock handles the context manager protocol:
    - __enter__ returns our test_session
    - __exit__ handles cleanup (mocked to do nothing)
    """
    mock = mocker.patch("services.task_repository.create_session")
    # Mock the context manager behavior of create_session()
    mock.return_value.__enter__.return_value = test_session
    mock.return_value.__exit__.return_value = None
    return mock


@pytest.fixture
def mock_settings(mocker):
    """Mock settings for testing."""
    settings_mock = mocker.MagicMock()
    settings_mock.PIPELINE_MAX_RESULTS = 3
    settings_mock.PIPELINE_MIN_RESULT_RETENTION_MINUTES = 60
    return settings_mock


@pytest.fixture(autouse=True)
def patch_settings(mock_settings, mocker):
    """Patch the settings module."""
    mocker.patch("services.task_repository.settings", mock_settings)


@pytest.fixture(autouse=True)
def reset_mutex():
    """Reset the global task creation mutex between tests."""
    # Ensure mutex is released before each test
    if task_creation_mutex.locked():
        task_creation_mutex.release()

    yield

    # Clean up after test
    if task_creation_mutex.locked():
        task_creation_mutex.release()


@pytest.fixture
def create_test_task(test_session):
    """Helper to create test tasks."""

    def _create_task(
        external_id: str,
        status: TaskStatus = TaskStatus.PENDING,
        completed_at: datetime = None,
    ) -> TaskResults:
        task = TaskResults(
            external_id=external_id, status=status, completed_at=completed_at
        )
        test_session.add(task)
        test_session.commit()
        test_session.refresh(task)
        return task

    return _create_task


# ============================================================================
# TESTS
# ============================================================================


def test_create_or_reuse_slot_with_capacity(test_session, mock_settings):
    """Test task creation when there is available capacity."""
    # Arrange: Create fewer tasks than max limit
    mock_settings.PIPELINE_MAX_RESULTS = 5
    existing_task = TaskResults(external_id="existing_task")
    test_session.add(existing_task)
    test_session.commit()

    # Act
    new_task = TaskRepository.create_or_reuse_slot("new_task")

    # Assert
    assert new_task is not None
    assert new_task.external_id == "new_task"
    assert new_task.status == TaskStatus.PENDING
    assert new_task.created_at is not None
    assert new_task.completed_at is None

    total_count = len(test_session.exec(select(TaskResults)).all())
    assert total_count == 2  # total count increased


def test_create_or_reuse_slot_override_old_task(
    test_session, mock_settings, create_test_task
):
    """Test task creation when need to override an old completed task."""
    # Arrange: Fill capacity with old completed task
    mock_settings.PIPELINE_MAX_RESULTS = 1

    # Create old completed task (beyond retention time)
    old_time = datetime.now() - timedelta(minutes=75)
    old_task = create_test_task("old_task", TaskStatus.COMPLETED, old_time)

    # Act
    new_task = TaskRepository.create_or_reuse_slot("new_task")

    # Assert
    assert new_task.id == old_task.id  # Same task object, reused
    assert new_task.external_id == "new_task"
    assert new_task.status == TaskStatus.PENDING
    assert new_task.completed_at is None
    assert new_task.ror_values == []
    assert new_task.ror_lower == []
    assert new_task.ror_upper == []

    total_count = len(test_session.exec(select(TaskResults)).all())
    assert total_count == 1  # total count didn't increase


@pytest.mark.parametrize(
    "description, status, completed_at",
    [
        (
            "completed task",
            TaskStatus.COMPLETED,
            datetime.now() - timedelta(minutes=30),
        ),
        ("failed task", TaskStatus.FAILED, datetime.now() - timedelta(minutes=30)),
        ("running task", TaskStatus.RUNNING, None),
    ],
)
def test_create_or_reuse_slot_no_capacity(
    mock_settings, create_test_task, description, status, completed_at
):
    """Test task creation when there is no available capacity."""
    # Arrange: Fill capacity with recent tasks
    mock_settings.PIPELINE_MAX_RESULTS = 1
    create_test_task(description, status, completed_at)

    # Act & Assert
    with pytest.raises(PipelineCapacityExceededError) as exc_info:
        TaskRepository.create_or_reuse_slot("new_task")

    assert "Pipeline capacity exceeded" in str(exc_info.value)
    assert "1 slots" in str(exc_info.value)


def test_create_or_reuse_slot_prefers_oldest_completed(
    test_session, mock_settings, create_test_task
):
    """Test that the oldest completed task is selected for reuse."""
    # Arrange
    mock_settings.PIPELINE_MAX_RESULTS = 2
    mock_settings.PIPELINE_MIN_RESULT_RETENTION_MINUTES = 30

    oldest_time = datetime.now() - timedelta(minutes=60)

    create_test_task("newest", TaskStatus.RUNNING)
    oldest_task = create_test_task("oldest", TaskStatus.COMPLETED, oldest_time)

    # Act
    new_task = TaskRepository.create_or_reuse_slot("reused_task")

    # Assert: Should reuse the oldest task
    assert new_task.id == oldest_task.id
    assert new_task.external_id == "reused_task"


def test_create_or_reuse_slot_ignores_failed_within_retention(
    test_session, mock_settings, create_test_task
):
    """Test that failed tasks within retention period are not reused."""
    # Arrange
    mock_settings.PIPELINE_MAX_RESULTS = 2
    mock_settings.PIPELINE_MIN_RESULT_RETENTION_MINUTES = 60

    # Recent failed task (within retention)
    recent_time = datetime.now() - timedelta(minutes=30)
    create_test_task("recent_failed", TaskStatus.FAILED, recent_time)
    create_test_task("running", TaskStatus.RUNNING)

    # Act & Assert
    with pytest.raises(PipelineCapacityExceededError):
        TaskRepository.create_or_reuse_slot("new_task")


# Tests for update_status
def test_update_status_to_running(test_session, create_test_task):
    """Test updating task status to RUNNING."""
    # Arrange
    task = create_test_task("test_task")
    original_created_at = task.created_at

    # Act
    TaskRepository.update_status(task, TaskStatus.RUNNING)

    # Assert
    test_session.refresh(task)
    assert task.status == TaskStatus.RUNNING
    assert task.created_at == original_created_at
    assert task.completed_at is None


def test_update_status_to_completed(test_session, create_test_task):
    """Test updating task status to COMPLETED."""
    # Arrange
    task = create_test_task("test_task", TaskStatus.RUNNING)

    # Act
    TaskRepository.update_status(task, TaskStatus.COMPLETED)

    # Assert
    test_session.refresh(task)
    assert task.status == TaskStatus.COMPLETED
    assert task.completed_at is not None


def test_update_status_nonexistent_task(test_session):
    """Test updating status of non-existent task."""
    # Arrange: Create task without adding to session
    task = TaskResults(external_id="nonexistent", id=999)

    # Act: Should not raise exception, just log warning
    TaskRepository.update_status(task, TaskStatus.COMPLETED)

    # Assert: Task should still have the status set locally
    assert task.status == TaskStatus.COMPLETED
    assert task.completed_at is not None


def test_update_status_preserves_other_fields(test_session, create_test_task):
    """Test that update_status preserves other task fields."""
    # Arrange
    task = create_test_task("test_task")
    task.ror_values = [1.5, 2.0]
    task.ror_lower = [1.0, 1.5]
    task.ror_upper = [2.0, 2.5]
    test_session.commit()

    # Act
    TaskRepository.update_status(task, TaskStatus.COMPLETED)

    # Assert
    test_session.refresh(task)
    assert task.ror_values == [1.5, 2.0]
    assert task.ror_lower == [1.0, 1.5]
    assert task.ror_upper == [2.0, 2.5]


def test_update_status_multiple_rapid_updates(test_session, create_test_task):
    """Test rapid consecutive status updates."""
    # Arrange
    task = create_test_task("test_task")

    # Act: Rapid status changes
    TaskRepository.update_status(task, TaskStatus.RUNNING)
    TaskRepository.update_status(task, TaskStatus.COMPLETED)
    TaskRepository.update_status(task, TaskStatus.FAILED)

    # Assert: Final status should be FAILED
    test_session.refresh(task)
    assert task.status == TaskStatus.FAILED


# Tests for save_task_results
def test_save_task_results_success(test_session, create_test_task):
    """Test successful saving of task results."""
    # Arrange
    task = create_test_task("test_task")
    task.ror_values = [1.5, 2.0, 3.0]
    task.ror_lower = [1.0, 1.5, 2.5]
    task.ror_upper = [2.0, 2.5, 3.5]
    task.status = TaskStatus.COMPLETED

    # Act
    TaskRepository.save_task_results(task)

    # Assert
    test_session.refresh(task)
    assert task.ror_values == [1.5, 2.0, 3.0]
    assert task.ror_lower == [1.0, 1.5, 2.5]
    assert task.ror_upper == [2.0, 2.5, 3.5]
    assert task.status == TaskStatus.COMPLETED


def test_save_task_results_nonexistent_task(test_session):
    """Test saving results for non-existent task."""
    # Arrange: Create task without adding to session
    task = TaskResults(external_id="nonexistent", id=999)
    task.ror_values = [1.0]

    # Act: Should not raise exception
    TaskRepository.save_task_results(task)

    # Assert: Task should still have the values set locally
    assert task.ror_values == [1.0]

def test_save_task_results_with_large_dataset(test_session, create_test_task):
    """Test saving task with large result dataset."""
    # Arrange
    task = create_test_task("test_task")
    large_values = list(range(1000))
    task.ror_values = [float(x) for x in large_values]
    task.ror_lower = [float(x - 0.5) for x in large_values]
    task.ror_upper = [float(x + 0.5) for x in large_values]

    # Act
    TaskRepository.save_task_results(task)

    # Assert
    test_session.refresh(task)
    assert len(task.ror_values) == 1000
    assert task.ror_values[0] == 0.0
    assert task.ror_values[999] == 999.0


def test_save_task_results_preserves_timestamps(test_session, create_test_task):
    """Test that save_task_results preserves timestamps."""
    # Arrange
    task = create_test_task("test_task")
    original_created_at = task.created_at
    task.completed_at = datetime.now()
    original_completed_at = task.completed_at
    task.ror_values = [1.0]

    # Act
    TaskRepository.save_task_results(task)

    # Assert
    test_session.refresh(task)
    assert task.created_at == original_created_at
    assert task.completed_at == original_completed_at
