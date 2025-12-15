from datetime import timedelta

import pytest
from django.utils import timezone

from analysis.models import Query, Result, ResultStatus
from analysis.views import PipelineStatusCheckMixin


@pytest.fixture
def mixin_instance():
    return PipelineStatusCheckMixin()


@pytest.fixture
def mock_query(db, user1):
    return Query.objects.create(
        user=user1,
        name="Test Query",
        quarter_start=1,
        quarter_end=2,
        year_start=2020,
        year_end=2020,
    )


@pytest.fixture
def mock_result(mock_query):
    return Result.objects.create(query=mock_query, status=ResultStatus.PENDING)


@pytest.fixture
def user1(db):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.create_user(email="test@example.com", password="testpass")


@pytest.mark.django_db
class TestPipelineStatusCheckMixinCompletedStatus:
    @pytest.mark.parametrize("status", [ResultStatus.COMPLETED, ResultStatus.FAILED])
    def test_completed_or_failed_result_skips_pipeline_check(
        self, mocker, mixin_instance, mock_result, status
    ):
        mock_result.status = status
        mock_result.save()

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task"
        )

        mixin_instance.check_and_update_result_from_pipeline(mock_result)

        mock_check_status.assert_not_called()


@pytest.mark.django_db
class TestPipelineStatusCheckMixinTimeout:
    @pytest.mark.parametrize(
        "initial_status,timeout_mins,age_mins",
        [
            (ResultStatus.PENDING, 30, 35),
            (ResultStatus.RUNNING, 60, 65),
        ],
    )
    def test_result_timeout_marks_failed(
        self,
        mocker,
        settings,
        mixin_instance,
        mock_result,
        initial_status,
        timeout_mins,
        age_mins,
    ):
        settings.PIPELINE_TASK_TIMEOUT_MINUTES = timeout_mins
        old_time = timezone.now() - timedelta(minutes=age_mins)
        mock_result.query.created_at = old_time
        mock_result.query.save()
        mock_result.status = initial_status
        mock_result.save()

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task"
        )

        mixin_instance.check_and_update_result_from_pipeline(mock_result)

        mock_check_status.assert_not_called()
        mock_result.refresh_from_db()
        assert mock_result.status == ResultStatus.FAILED

    def test_pending_result_within_timeout_checks_pipeline(
        self, mocker, settings, mixin_instance, mock_result
    ):
        settings.PIPELINE_TASK_TIMEOUT_MINUTES = 60
        recent_time = timezone.now() - timedelta(minutes=30)
        mock_result.query.created_at = recent_time
        mock_result.query.save()
        mock_result.status = ResultStatus.PENDING
        mock_result.save()

        pipeline_response = {
            "id": mock_result.id,
            "status": ResultStatus.RUNNING,
            "ror_values": [],
            "ror_lower": [],
            "ror_upper": [],
        }

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task",
            return_value=pipeline_response,
        )

        mixin_instance.check_and_update_result_from_pipeline(mock_result)

        mock_check_status.assert_called_once_with(mock_result.id)
        mock_result.refresh_from_db()
        assert mock_result.status == ResultStatus.RUNNING

    def test_timeout_at_exact_threshold_marks_failed(
        self, mocker, settings, mixin_instance, mock_result
    ):
        settings.PIPELINE_TASK_TIMEOUT_MINUTES = 45
        exact_time = timezone.now() - timedelta(minutes=45, seconds=1)
        mock_result.query.created_at = exact_time
        mock_result.query.save()
        mock_result.status = ResultStatus.PENDING
        mock_result.save()

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task"
        )

        mixin_instance.check_and_update_result_from_pipeline(mock_result)

        mock_check_status.assert_not_called()
        mock_result.refresh_from_db()
        assert mock_result.status == ResultStatus.FAILED


@pytest.mark.django_db
class TestPipelineStatusCheckMixinPipelineNotFound:
    @pytest.mark.parametrize(
        "initial_status", [ResultStatus.PENDING, ResultStatus.RUNNING]
    )
    def test_pipeline_none_marks_failed(
        self, mocker, mixin_instance, mock_result, initial_status
    ):
        mock_result.status = initial_status
        mock_result.save()

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task", return_value=None
        )

        mixin_instance.check_and_update_result_from_pipeline(mock_result)

        mock_check_status.assert_called_once_with(mock_result.id)
        mock_result.refresh_from_db()
        assert mock_result.status == ResultStatus.FAILED


@pytest.mark.django_db
class TestPipelineStatusCheckMixinCompletedWithDetails:
    def test_completed_status_fetches_detailed_results(
        self, mocker, mixin_instance, mock_result
    ):
        mock_result.status = ResultStatus.PENDING
        mock_result.save()

        task_results = {
            "id": mock_result.id,
            "status": ResultStatus.COMPLETED,
            "ror_values": [1.5, 2.0, 2.5],
            "ror_lower": [1.2, 1.8, 2.2],
            "ror_upper": [1.8, 2.2, 2.8],
        }

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task",
            return_value=task_results,
        )

        mixin_instance.check_and_update_result_from_pipeline(mock_result)

        mock_check_status.assert_called_once_with(mock_result.id)
        mock_result.refresh_from_db()
        assert mock_result.status == ResultStatus.COMPLETED
        assert mock_result.ror_values == [1.5, 2.0, 2.5]
        assert mock_result.ror_lower == [1.2, 1.8, 2.2]
        assert mock_result.ror_upper == [1.8, 2.2, 2.8]

    def test_completed_status_detailed_results_none_marks_failed(
        self, mocker, mixin_instance, mock_result
    ):
        mock_result.status = ResultStatus.RUNNING
        mock_result.save()

        pipeline_status = {"id": mock_result.id, "status": ResultStatus.COMPLETED}

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task",
            return_value=pipeline_status,
        )

        mixin_instance.check_and_update_result_from_pipeline(mock_result)

        mock_check_status.assert_called_once()
        mock_result.refresh_from_db()
        assert mock_result.status == ResultStatus.FAILED

    def test_completed_status_invalid_detailed_results_marks_failed(
        self, mocker, mixin_instance, mock_result
    ):
        mock_result.status = ResultStatus.PENDING
        mock_result.save()

        pipeline_status = {"id": mock_result.id, "status": ResultStatus.COMPLETED}

        invalid_results = {
            "id": mock_result.id,
            "status": "invalid_status",
            "ror_values": "not_a_list",
        }

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task",
            return_value=pipeline_status,
        )

        mixin_instance.check_and_update_result_from_pipeline(mock_result)

        mock_check_status.assert_called_once()
        mock_result.refresh_from_db()
        assert mock_result.status == ResultStatus.FAILED

    def test_completed_with_empty_ror_values(self, mocker, mixin_instance, mock_result):
        mock_result.status = ResultStatus.RUNNING
        mock_result.save()

        task_results = {
            "id": mock_result.id,
            "status": ResultStatus.COMPLETED,
            "ror_values": [],
            "ror_lower": [],
            "ror_upper": [],
        }

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task",
            return_value=task_results,
        )

        mixin_instance.check_and_update_result_from_pipeline(mock_result)

        mock_result.refresh_from_db()
        assert mock_result.status == ResultStatus.COMPLETED
        assert mock_result.ror_values == []
        assert mock_result.ror_lower == []
        assert mock_result.ror_upper == []


@pytest.mark.django_db
class TestPipelineStatusCheckMixinStatusUpdate:
    @pytest.mark.parametrize(
        "initial_status,expected_status",
        [
            (ResultStatus.PENDING, ResultStatus.RUNNING),
            (ResultStatus.RUNNING, ResultStatus.RUNNING),
        ],
    )
    def test_status_update_to_running(
        self, mocker, mixin_instance, mock_result, initial_status, expected_status
    ):
        mock_result.status = initial_status
        mock_result.save()

        pipeline_response = {
            "id": mock_result.id,
            "status": ResultStatus.RUNNING,
            "ror_values": [],
            "ror_lower": [],
            "ror_upper": [],
        }

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task",
            return_value=pipeline_response,
        )

        mixin_instance.check_and_update_result_from_pipeline(mock_result)

        mock_check_status.assert_called_once()
        mock_result.refresh_from_db()
        assert mock_result.status == expected_status

    @pytest.mark.parametrize(
        "invalid_response,expected_status",
        [
            (
                {"id": 1, "status": "invalid_status_value", "ror_values": []},
                ResultStatus.FAILED,
            ),
            ({"id": 1}, ResultStatus.FAILED),
        ],
    )
    def test_invalid_pipeline_response_marks_failed(
        self, mocker, mixin_instance, mock_result, invalid_response, expected_status
    ):
        mock_result.status = ResultStatus.PENDING
        mock_result.save()

        invalid_response["id"] = mock_result.id

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task",
            return_value=invalid_response,
        )

        mixin_instance.check_and_update_result_from_pipeline(mock_result)

        mock_check_status.assert_called_once()
        mock_result.refresh_from_db()
        assert mock_result.status == expected_status


@pytest.mark.django_db
class TestPipelineStatusCheckMixinEdgeCases:
    def test_zero_timeout_threshold(
        self, mocker, settings, mixin_instance, mock_result
    ):
        settings.PIPELINE_TASK_TIMEOUT_MINUTES = 0
        mock_result.status = ResultStatus.PENDING
        mock_result.save()

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task"
        )

        mixin_instance.check_and_update_result_from_pipeline(mock_result)

        mock_check_status.assert_not_called()
        mock_result.refresh_from_db()
        assert mock_result.status == ResultStatus.FAILED

    def test_large_timeout_threshold(
        self, mocker, settings, mixin_instance, mock_result
    ):
        settings.PIPELINE_TASK_TIMEOUT_MINUTES = 10000
        mock_result.status = ResultStatus.PENDING
        mock_result.save()

        pipeline_response = {
            "id": mock_result.id,
            "status": ResultStatus.RUNNING,
            "ror_values": [],
            "ror_lower": [],
            "ror_upper": [],
        }

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task",
            return_value=pipeline_response,
        )

        mixin_instance.check_and_update_result_from_pipeline(mock_result)

        mock_check_status.assert_called_once()

    def test_result_with_existing_ror_values_overwritten(
        self, mocker, mixin_instance, mock_result
    ):
        mock_result.status = ResultStatus.RUNNING
        mock_result.ror_values = [1.0, 2.0]
        mock_result.ror_lower = [0.8, 1.8]
        mock_result.ror_upper = [1.2, 2.2]
        mock_result.save()

        new_results = {
            "id": mock_result.id,
            "status": ResultStatus.COMPLETED,
            "ror_values": [3.0, 4.0, 5.0],
            "ror_lower": [2.5, 3.5, 4.5],
            "ror_upper": [3.5, 4.5, 5.5],
        }

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task",
            return_value=new_results,
        )

        mixin_instance.check_and_update_result_from_pipeline(mock_result)

        mock_result.refresh_from_db()
        assert mock_result.ror_values == [3.0, 4.0, 5.0]
        assert mock_result.ror_lower == [2.5, 3.5, 4.5]
        assert mock_result.ror_upper == [3.5, 4.5, 5.5]

    def test_task_created_in_future_not_timeout(
        self, mocker, settings, mixin_instance, mock_result
    ):
        settings.PIPELINE_TASK_TIMEOUT_MINUTES = 30
        future_time = timezone.now() + timedelta(minutes=5)
        mock_result.query.created_at = future_time
        mock_result.query.save()
        mock_result.status = ResultStatus.PENDING
        mock_result.save()

        pipeline_response = {
            "id": mock_result.id,
            "status": ResultStatus.RUNNING,
            "ror_values": [],
            "ror_lower": [],
            "ror_upper": [],
        }

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task",
            return_value=pipeline_response,
        )

        mixin_instance.check_and_update_result_from_pipeline(mock_result)

        mock_check_status.assert_called_once()
        mock_result.refresh_from_db()
        assert mock_result.status == ResultStatus.RUNNING
