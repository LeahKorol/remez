"""
Unit tests for pipeline status endpoint
"""

import pytest
from constants import TaskStatus
from fastapi.testclient import TestClient
from models.models import TaskResults
from starlette.status import HTTP_200_OK, HTTP_422_UNPROCESSABLE_CONTENT


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
