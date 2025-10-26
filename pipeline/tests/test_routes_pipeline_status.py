"""
Unit tests for pipeline routes
"""

import pytest
from constants import TaskStatus
from errors import PipelineCapacityExceededError
from fastapi.testclient import TestClient
from models.models import TaskResults
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_CONTENT,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_500_INTERNAL_SERVER_ERROR,
)


@pytest.fixture
def test_client(test_app):
    """Create test client"""
    return TestClient(test_app)


@pytest.fixture
def sample_tasks(test_session):
    """Create sample tasks for testing"""
    tasks = [
        TaskResults(id=1, external_id="ext_001", status=TaskStatus.PENDING),
        TaskResults(id=2, external_id="ext_002", status=TaskStatus.RUNNING),
        TaskResults(id=3, external_id="ext_003", status=TaskStatus.COMPLETED),
        TaskResults(id=4, external_id="ext_004", status=TaskStatus.FAILED),
        TaskResults(id=5, external_id="ext_005", status=TaskStatus.PENDING),
        TaskResults(id=6, external_id="ext_006", status=TaskStatus.COMPLETED),
    ]

    for task in tasks:
        test_session.add(task)
    test_session.commit()

    return tasks


@pytest.fixture
def request_data():
    """Provide valid request data for pipeline run"""
    return {
        "year_start": 2023,
        "quarter_start": 1,
        "year_end": 2023,
        "quarter_end": 2,
        "drugs": ["aspirin"],
        "reactions": ["headache"],
        "external_id": "test_ext_123",
    }


class TestGetTasksByStatus:
    """Test cases for get_tasks_by_status endpoint"""

    @pytest.mark.parametrize(
        "status,expected_count,expected_ids",
        [
            (TaskStatus.PENDING, 2, [1, 5]),
            (TaskStatus.RUNNING, 1, [2]),
            (TaskStatus.COMPLETED, 2, [3, 6]),
            (TaskStatus.FAILED, 1, [4]),
        ],
    )
    def test_get_tasks_by_valid_status(
        self, test_client, sample_tasks, status, expected_count, expected_ids
    ):
        """Test getting tasks by valid status values"""
        response = test_client.get(f"/status/{status.value}")

        assert response.status_code == HTTP_200_OK
        data = response.json()

        # Check count
        assert data["count"] == expected_count
        assert len(data["tasks"]) == expected_count

        # Check task IDs
        actual_ids = {task["id"] for task in data["tasks"]}
        assert actual_ids == set(expected_ids)

    def test_get_tasks_by_status_no_results(self, test_client, test_session):
        """Test getting tasks when no tasks exist with the specified status"""
        # Don't add any sample tasks, so all status queries should return empty results

        response = test_client.get(f"/status/{TaskStatus.PENDING.value}")

        assert response.status_code == HTTP_200_OK
        data = response.json()

        assert data["count"] == 0
        assert data["tasks"] == []

    def test_get_tasks_by_invalid_status(self, test_client, sample_tasks):
        """Test getting tasks with an invalid status"""
        response = test_client.get("/status/invalid_status")

        assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT
        data = response.json()
        assert "detail" in data

    def test_get_tasks_by_status_empty_database(self, test_client):
        """Test getting tasks when database is empty"""
        response = test_client.get(f"/status/{TaskStatus.PENDING.value}")

        assert response.status_code is HTTP_200_OK
        data = response.json()

        assert data["count"] == 0
        assert data["tasks"] == []

    @pytest.mark.parametrize(
        "status",
        [
            TaskStatus.PENDING,
            TaskStatus.RUNNING,
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
        ],
    )
    def test_all_valid_statuses_work(self, test_client, sample_tasks, status):
        """Test that all valid TaskStatus enum values work"""
        response = test_client.get(f"/status/{status.value}")

        assert response.status_code == HTTP_200_OK
        data = response.json()

        # Check response structure
        assert isinstance(data, dict)
        assert "tasks" in data
        assert "count" in data
        assert isinstance(data["tasks"], list)
        assert isinstance(data["count"], int)
        assert data["count"] == len(data["tasks"])

    def test_response_task_summary_structure(self, test_client, sample_tasks):
        """Test that TaskSummary objects have correct structure"""
        response = test_client.get(f"/status/{TaskStatus.PENDING.value}")

        assert response.status_code == HTTP_200_OK
        data = response.json()

        assert data["tasks"]

        task = data["tasks"][0]

        # Verify all required fields are present
        assert "id" in task
        assert "external_id" in task

        # Verify no extra fields
        assert set(task.keys()) == {"id", "external_id"}

        # Verify correct types
        assert isinstance(task["id"], int)
        assert isinstance(task["external_id"], str)

    def test_case_sensitive_status(self, test_client, sample_tasks):
        """Test that status parameter is case sensitive"""
        # Try uppercase version of a valid status
        response = test_client.get("/status/PENDING")

        assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT

    def test_special_characters_in_status(self, test_client, sample_tasks):
        """Test status parameter with special characters"""
        response = test_client.get("/status/pending@#$")

        assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT
        data = response.json()
        assert "detail" in data

    def test_numeric_status(self, test_client, sample_tasks):
        """Test status parameter with numeric values"""
        response = test_client.get("/status/123")

        assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT
        data = response.json()
        assert "detail" in data


# ============================================================================
# TESTS FOR POST /run endpoint
# ============================================================================


def test_run_pipeline_success(test_client, mocker, request_data):
    """Test successful pipeline execution start"""
    mock_task_repository = mocker.patch(
        "api.v1.routes.pipeline.TaskRepository.create_or_reuse_slot"
    )
    mock_pipeline_service = mocker.patch(
        "api.v1.routes.pipeline.pipeline_service.start_pipeline"
    )

    mock_task = TaskResults(id=1, external_id="test_ext_123", status=TaskStatus.PENDING)
    mock_task_repository.return_value = mock_task

    response = test_client.post("/run", json=request_data)

    assert response.status_code == HTTP_201_CREATED
    data = response.json()
    assert data["id"] == 1
    assert data["external_id"] == "test_ext_123"
    assert data["status"] == "pending"

    mock_task_repository.assert_called_once_with("test_ext_123")
    mock_pipeline_service.assert_called_once()


def test_run_pipeline_capacity_exceeded(test_client, mocker, request_data):
    """Test pipeline execution when capacity is exceeded"""
    mock_task_repository = mocker.patch(
        "api.v1.routes.pipeline.TaskRepository.create_or_reuse_slot"
    )
    mock_task_repository.side_effect = PipelineCapacityExceededError(
        "Pipeline capacity exceeded"
    )

    response = test_client.post("/run", json=request_data)

    assert response.status_code == HTTP_429_TOO_MANY_REQUESTS
    data = response.json()
    assert "Pipeline capacity exceeded" in data["detail"]


@pytest.mark.parametrize(
    "invalid_field,invalid_value",
    [
        ("year_start", 2026),
        ("quarter_start", 5),
        ("year_end", 2000),
        ("quarter_end", 5),
        ("drugs", []),
        ("reactions", []),
        ("external_id", ""),
    ],
)
def test_run_pipeline_invalid_request(test_client, invalid_field, invalid_value):
    """Test pipeline execution with invalid request data"""
    request_data = {
        "year_start": 2023 if invalid_field != "year_start" else invalid_value,
        "year_end": 2023 if invalid_field != "year_end" else invalid_value,
        "quarter_start": 1 if invalid_field != "quarter_start" else invalid_value,
        "quarter_end": 2 if invalid_field != "quarter_end" else invalid_value,
        "drugs": ["aspirin"] if invalid_field != "drugs" else invalid_value,
        "reactions": ["headache"] if invalid_field != "reactions" else invalid_value,
        "external_id": "test_ext_123"
        if invalid_field != "external_id"
        else invalid_value,
    }

    response = test_client.post("/run", json=request_data)

    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT
    data = response.json()
    assert (
        invalid_field in data["detail"][0]["loc"]
        or invalid_field in data["detail"][0]["msg"]
    )


# ============================================================================
# TESTS FOR GET /{task_id} endpoint
# ============================================================================


def test_get_pipeline_status_success(test_client, test_session):
    """Test successful retrieval of pipeline task status"""
    task = TaskResults(id=1, external_id="test_ext_123", status=TaskStatus.RUNNING)
    test_session.add(task)
    test_session.commit()

    response = test_client.get("/1")

    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert data["id"] == 1
    assert data["external_id"] == "test_ext_123"
    assert data["status"] == "running"


def test_get_pipeline_status_not_found(test_client):
    """Test retrieval of non-existent pipeline task"""
    response = test_client.get("/999")

    assert response.status_code == HTTP_404_NOT_FOUND
    data = response.json()
    assert "Task 999 not found" in data["detail"]


def test_get_pipeline_status_invalid_task_id(test_client):
    """Test retrieval with invalid task ID"""
    response = test_client.get("/invalid_id")

    assert response.status_code == HTTP_422_UNPROCESSABLE_CONTENT
    data = response.json()
    assert "detail" in data


# ============================================================================
# TESTS FOR GET /data/available endpoint
# ============================================================================


def test_get_available_data_success(test_client, mocker):
    """Test successful retrieval of available data"""
    response = test_client.get("/data/available")

    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert "complete_quarters" in data
    assert "incomplete_quarters" in data
    assert "file_details" in data


def test_get_available_data_service_error(test_client, mocker):
    """Test available data retrieval when service raises an error"""
    mock_pipeline_service = mocker.patch(
        "api.v1.routes.pipeline.pipeline_service.get_available_data"
    )
    mock_pipeline_service.side_effect = Exception("Service error")

    response = test_client.get("/data/available")

    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert "Failed to retrieve available data information" in data["detail"]
