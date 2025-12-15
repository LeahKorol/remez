from datetime import timedelta

import pytest
from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from analysis.models import DrugName, Query, ReactionName, Result, ResultStatus
from analysis.serializers import QuerySerializer

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user1(db):
    user = User.objects.create_user(email="user1@example.com", password="testpassword1")
    email_address = EmailAddress.objects.get(user=user)
    email_address.verified = True
    email_address.save()
    return user


@pytest.fixture
def user2(db):
    user = User.objects.create_user(email="user2@example.com", password="testpassword2")
    email_address = EmailAddress.objects.get(user=user)
    email_address.verified = True
    email_address.save()
    return user


@pytest.fixture
def drug(db):
    return DrugName.objects.create(name="drug")


@pytest.fixture
def reaction(db):
    return ReactionName.objects.create(name="reaction")


@pytest.fixture
def required_fields(drug, reaction):
    return {
        "quarter_start": 1,
        "quarter_end": 2,
        "year_start": 2020,
        "year_end": 2020,
        "drugs": [drug.id],
        "reactions": [reaction.id],
    }


@pytest.fixture
def query1(user1, drug, reaction):
    query = Query.objects.create(
        user=user1,
        name="User1 Query 1",
        quarter_start=1,
        quarter_end=2,
        year_start=2020,
        year_end=2020,
    )
    query.drugs.set([drug.id])
    query.reactions.set([reaction.id])
    Result.objects.create(
        query=query,
        status=ResultStatus.PENDING,
        ror_values=[],
        ror_lower=[],
        ror_upper=[],
    )
    return query


@pytest.fixture
def query2(user1, drug, reaction):
    """Fixture for second query belonging to user1"""
    query = Query.objects.create(
        user=user1,
        name="User1 Query 2",
        quarter_start=1,
        quarter_end=2,
        year_start=2021,
        year_end=2021,
    )
    query.drugs.set([drug.id])
    query.reactions.set([reaction.id])
    # Create associated Result object
    Result.objects.create(
        query=query,
        status=ResultStatus.PENDING,
        ror_values=[],
        ror_lower=[],
        ror_upper=[],
    )
    return query


@pytest.fixture
def query3(user2, drug, reaction):
    """Fixture for query belonging to user2"""
    query = Query.objects.create(
        user=user2,
        name="User2 Query",
        quarter_start=1,
        quarter_end=2,
        year_start=2022,
        year_end=2022,
    )
    query.drugs.set([drug.id])
    query.reactions.set([reaction.id])
    # Create associated Result object
    Result.objects.create(
        query=query,
        status=ResultStatus.PENDING,
        ror_values=[],
        ror_lower=[],
        ror_upper=[],
    )
    return query


@pytest.fixture
def result1(query1):
    """Fixture for result belonging to user1"""
    result, created = Result.objects.update_or_create(
        query=query1,  # lookup by query1 (user1's query)
        defaults={
            "status": ResultStatus.COMPLETED,
            "ror_values": [1.5, 2.0],
            "ror_lower": [1.2, 1.8],
            "ror_upper": [1.8, 2.2],
        },
    )
    return result


@pytest.fixture
def result2(query3):
    """Fixture for result belonging to user2"""
    result, created = Result.objects.update_or_create(
        query=query3,  # lookup by query3 (user2's query)
        defaults={
            "status": ResultStatus.PENDING,
            "ror_values": [],
            "ror_lower": [],
            "ror_upper": [],
        },
    )
    return result


@pytest.fixture
def result_data():
    """Fixture for result data"""
    return {
        "status": ResultStatus.COMPLETED,
        "ror_values": [2.5, 3.0],
        "ror_lower": [2.0, 2.5],
        "ror_upper": [3.0, 3.5],
    }


@pytest.mark.django_db
class TestQueryViewSet:
    """Test cases for QueryViewSet"""

    def authenticate_user(self, api_client, user=None, email=None, password=None):
        """Login and store JWT cookie for authentication.

        Args:
            api_client: The API client to authenticate
            user: User object (will use email from user if provided)
            email: Email string (used if user not provided)
            password: Password string (defaults based on email)
        """
        if user:
            email = user.email
            # Extract password from email pattern (user1@example.com -> testpassword1)
            password = f"testpassword{email.split('@')[0][-1]}"
        elif not email:
            email = "user1@example.com"
            password = password or "testpassword1"
        elif not password:
            # Extract password from email pattern
            password = f"testpassword{email.split('@')[0][-1]}"

        auth_url = "http://127.0.0.1:8000/api/v1/auth/login/"
        response = api_client.post(
            auth_url,
            data={"email": email, "password": password},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        access_cookie = response.cookies[settings.REST_AUTH["JWT_AUTH_COOKIE"]]
        api_client.cookies[settings.REST_AUTH["JWT_AUTH_COOKIE"]] = access_cookie

    def test_list_queries_authenticated_user(self, api_client, user1, query1, query2):
        """Test that an authenticated user can list only their own queries."""
        self.authenticate_user(api_client, user=user1)
        list_url = reverse("query-list")
        response = api_client.get(list_url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2  # user1 has two queries

        expected_data = QuerySerializer([query2, query1], many=True).data
        expected_data_sorted = sorted(expected_data, key=lambda x: x["id"])
        response_data_sorted = sorted(response.data, key=lambda x: x["id"])
        assert response_data_sorted == expected_data_sorted

    def test_list_queries_unauthenticated_user(self, api_client, query1):
        """Test that an unauthenticated user cannot access the query list."""
        list_url = reverse("query-list")
        response = api_client.get(list_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_query_owned_by_user(self, api_client, user1, query1):
        """Test that a user can retrieve their own query."""
        self.authenticate_user(api_client, user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query1.id})
        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        query1.result.status = (
            ResultStatus.FAILED
        )  # The pipeline doesnt run during the tests
        expected_data = QuerySerializer(query1).data
        assert response.data == expected_data

    def test_retrieve_query_not_owned_by_user(self, api_client, user1, query3):
        """Test that a user cannot retrieve someone else's query."""
        self.authenticate_user(api_client, user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query3.id})
        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_query_authenticated_user(
        self, mocker, api_client, user1, required_fields
    ):
        """Test that an authenticated user can create a query and associated result."""
        # Mock the pipeline service call to prevent real HTTP requests during unit tests
        mocker.patch("analysis.views.pipeline_service.trigger_pipeline_analysis")
        # Mock demo mode as disabled
        mocker.patch.object(settings, "NUM_DEMO_QUARTERS", -1)

        self.authenticate_user(api_client, user=user1)
        list_url = reverse("query-list")
        data = {"name": "New Query by User1", **required_fields}
        response = api_client.post(list_url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Query.objects.filter(user=user1).count() == 1

        # Verify that a Result object was also created
        query = Query.objects.get(user=user1)
        assert hasattr(query, "result")
        assert query.result.status == ResultStatus.PENDING

        # Verify the response contains result data
        assert "result" in response.data
        assert response.data["result"]["status"] == ResultStatus.PENDING

    def test_create_query_unauthenticated_user(self, api_client, required_fields):
        """Test that an unauthenticated user cannot create a query."""
        list_url = reverse("query-list")
        data = {"data": "Unauthorized Query", **required_fields}
        response = api_client.post(list_url, data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_query_owned_by_user(self, api_client, user1, query1):
        """Test that a user can delete their own query."""
        self.authenticate_user(api_client, user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query1.id})
        response = api_client.delete(detail_url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Query.objects.filter(id=query1.id).exists()

    def test_delete_query_not_owned_by_user(self, api_client, user1, query3):
        """Test that a user cannot delete someone else's query."""
        self.authenticate_user(api_client, user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query3.id})
        response = api_client.delete(detail_url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Query.objects.filter(id=query3.id).exists()

    def test_partial_update_query_owned_by_user(
        self, mocker, api_client, user1, query1
    ):
        """Test that a user can update their own query."""
        # Mock pipeline service to prevent real HTTP requests during unit tests
        mocker.patch("analysis.views.pipeline_service.trigger_pipeline_analysis")

        self.authenticate_user(api_client, user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query1.id})
        updated_name = {"name": "Updated Query"}
        response = api_client.patch(detail_url, updated_name)

        assert response.status_code == status.HTTP_200_OK
        query1.refresh_from_db()
        assert query1.name == "Updated Query"

    @pytest.mark.parametrize(
        "initial_status", [ResultStatus.PENDING, ResultStatus.RUNNING]
    )
    def test_update_ignored_when_task_in_progress(
        self, mocker, api_client, user1, query1, required_fields, initial_status
    ):
        """If result is pending/running, log and do not re-trigger pipeline even if ROR fields change."""
        mock_trigger = mocker.patch(
            "analysis.views.pipeline_service.trigger_pipeline_analysis"
        )
        mocker.patch.object(settings, "NUM_DEMO_QUARTERS", -1)

        # Set in-progress status
        query1.result.status = initial_status
        query1.result.save()

        self.authenticate_user(api_client, user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query1.id})

        # Change ROR fields
        updated_data = required_fields.copy()
        updated_data["name"] = "Updated Query"
        response = api_client.put(detail_url, updated_data)

        assert response.status_code == status.HTTP_200_OK
        # Ensure pipeline not triggered
        mock_trigger.assert_not_called()
        # Status remains in-progress
        query1.result.refresh_from_db()
        assert query1.result.status == initial_status

    @pytest.mark.parametrize(
        "initial_status,should_trigger,expected_status",
        [
            (ResultStatus.FAILED, True, ResultStatus.PENDING),
            (ResultStatus.RUNNING, False, ResultStatus.RUNNING),
            (ResultStatus.PENDING, False, ResultStatus.PENDING),
            (ResultStatus.COMPLETED, False, ResultStatus.COMPLETED),
        ],
    )
    def test_no_ror_change_resend_logic(
        self,
        mocker,
        api_client,
        user1,
        query1,
        initial_status,
        should_trigger,
        expected_status,
    ):
        """When no ROR fields change, resend only if previous status was FAILED"""
        # Ensure real pipeline path (demo disabled)
        mocker.patch.object(settings, "NUM_DEMO_QUARTERS", -1)

        # Spy on pipeline trigger
        mock_trigger = mocker.patch(
            "analysis.views.pipeline_service.trigger_pipeline_analysis"
        )

        # Set initial result status
        query1.result.status = initial_status
        query1.result.save()
        query1
        print(f"Initial result status: {query1.result.status}")

        self.authenticate_user(api_client, user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query1.id})

        # Change only non-ROR field (name), should never trigger pipeline
        resp = api_client.patch(detail_url, {"name": "Only Name Change"})

        assert resp.status_code == status.HTTP_200_OK

        if should_trigger:
            mock_trigger.assert_called_once()
        else:
            mock_trigger.assert_not_called()

        query1.result.refresh_from_db()
        assert query1.result.status == expected_status

    @pytest.mark.parametrize(
        "initial_status,should_trigger,expected_status",
        [
            (ResultStatus.FAILED, True, ResultStatus.PENDING),
            (ResultStatus.RUNNING, False, ResultStatus.RUNNING),
            (ResultStatus.PENDING, False, ResultStatus.PENDING),
            (ResultStatus.COMPLETED, True, ResultStatus.PENDING),
        ],
    )
    def test_ror_change_resend_logic(
        self,
        mocker,
        api_client,
        user1,
        query1,
        initial_status,
        should_trigger,
        expected_status,
    ):
        """When ROR fields change, resend only if previous status was COMPLETED or FAILED."""
        # Ensure real pipeline path (demo disabled)
        mocker.patch.object(settings, "NUM_DEMO_QUARTERS", -1)

        mock_trigger = mocker.patch(
            "analysis.views.pipeline_service.trigger_pipeline_analysis"
        )

        # Set initial result status
        query1.result.status = initial_status
        query1.result.save()

        self.authenticate_user(api_client, user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query1.id})

        # Change ROR field, should trigger pipeline for COMPLETED/FAILED status
        resp = api_client.patch(detail_url, {"year_start": "2018"})

        assert resp.status_code == status.HTTP_200_OK

        if should_trigger:
            mock_trigger.assert_called_once()
        else:
            mock_trigger.assert_not_called()

        query1.result.refresh_from_db()
        assert query1.result.status == expected_status

    def test_partial_update_query_not_owned_by_user(self, api_client, user1, query3):
        """Test that a user cannot update someone else's query."""
        self.authenticate_user(api_client, user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query3.id})
        updated_name = {"name": "Attempted Unauthorized Update"}
        response = api_client.put(detail_url, updated_name)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        query3.refresh_from_db()
        assert query3.name != "Attempted Unauthorized Update"

    def test_full_update_query_owned_by_user(
        self, mocker, api_client, user1, query1, required_fields
    ):
        """Test that a user can update their own query."""
        # Mock the pipeline service call to prevent real HTTP requests during unit tests
        mocker.patch("analysis.views.pipeline_service.trigger_pipeline_analysis")
        # Mock demo mode as disabled
        mocker.patch.object(settings, "NUM_DEMO_QUARTERS", -1)

        self.authenticate_user(api_client, user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query1.id})
        updated_data = required_fields.copy()
        updated_data["name"] = "Updated Query"
        response = api_client.put(detail_url, updated_data)

        assert response.status_code == status.HTTP_200_OK
        query1.refresh_from_db()
        assert query1.name == "Updated Query"

    def test_full_update_query_not_owned_by_user(
        self, api_client, user1, query3, required_fields
    ):
        """Test that a user cannot update someone else's query."""
        self.authenticate_user(api_client, user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query3.id})
        updated_data = required_fields.copy()
        updated_data["name"] = "Attempted Unauthorized Update"
        response = api_client.put(detail_url, updated_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        query3.refresh_from_db()
        assert query3.name != "Attempted Unauthorized Update"

    @pytest.mark.parametrize("invalid_quarter", [0, 5, -1, 10])
    def test_query_serializer_blocks_invalid_quarters(
        self, mocker, api_client, user1, query1, required_fields, invalid_quarter
    ):
        """Test that serializer blocks invalid quarter numbers."""
        # Mock the pipeline service call to prevent real HTTP requests during unit tests
        mock_trigger = mocker.patch(
            "analysis.views.pipeline_service.trigger_pipeline_analysis"
        )

        self.authenticate_user(api_client, user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query1.id})
        updated_data = required_fields.copy()
        updated_data["quarter_start"] = invalid_quarter
        response = api_client.put(detail_url, updated_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "quarter_start" in response.data

        # Verify pipeline service was NOT called due to validation error
        mock_trigger.assert_not_called()

    def test_year_start_lte_year_end(
        self, mocker, api_client, user1, query1, required_fields
    ):
        """Test that serializer blocks year_start greater than year_end."""
        # Mock the pipeline service call to prevent real HTTP requests during unit tests
        mock_trigger = mocker.patch(
            "analysis.views.pipeline_service.trigger_pipeline_analysis"
        )

        self.authenticate_user(api_client, user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query1.id})
        updated_data = required_fields.copy()
        updated_data["year_start"] = 2022
        updated_data["year_end"] = 2021
        response = api_client.put(detail_url, updated_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "year_start" in response.data

        # Verify pipeline service was NOT called due to validation error
        mock_trigger.assert_not_called()

    @pytest.mark.parametrize(
        "year_start, year_end, quarter_start, quarter_end, res_status",
        [
            (2021, 2021, 1, 2, status.HTTP_200_OK),
            (2021, 2021, 2, 1, status.HTTP_400_BAD_REQUEST),
            (2021, 2021, 4, 4, status.HTTP_400_BAD_REQUEST),
            (2021, 2022, 1, 2, status.HTTP_200_OK),
            (2021, 2022, 3, 2, status.HTTP_200_OK),
            (2021, 2022, 3, 3, status.HTTP_200_OK),
        ],
    )
    def test_quarter_start_lte_quarter_end(
        self,
        mocker,
        api_client,
        user1,
        query1,
        required_fields,
        year_start,
        year_end,
        quarter_start,
        quarter_end,
        res_status,
    ):
        """Test that serializer validates quarter and year ranges properly."""
        # Mock the pipeline service call to prevent real HTTP requests during unit tests
        mock_trigger = mocker.patch(
            "analysis.views.pipeline_service.trigger_pipeline_analysis"
        )
        # Mock demo mode as disabled
        mocker.patch.object(settings, "NUM_DEMO_QUARTERS", -1)

        self.authenticate_user(api_client, user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query1.id})

        updated_data = required_fields.copy()
        query1.result.status = (
            ResultStatus.COMPLETED
        )  # Set to completed to allow re-trigger
        query1.result.save()

        updated_data["quarter_start"] = quarter_start
        updated_data["quarter_end"] = quarter_end
        updated_data["year_start"] = year_start
        updated_data["year_end"] = year_end
        response = api_client.put(detail_url, updated_data)
        assert response.status_code == res_status
        if response.status_code != status.HTTP_200_OK:
            assert "quarter_start" in response.data
            # Verify pipeline service was NOT called due to validation error
            mock_trigger.assert_not_called()
        else:
            # Verify pipeline service was called for successful updates
            mock_trigger.assert_called_once()


@pytest.mark.django_db
class TestResultViewSetList:
    """Test cases for listing results"""

    def test_list_results_authenticated(self, api_client, user1, result1):
        """Test that authenticated users can list their own results"""
        api_client.force_authenticate(user=user1)
        list_url = reverse("result-list")
        response = api_client.get(list_url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == result1.id

    def test_list_results_unauthenticated(self, api_client, result1):
        """Test that unauthenticated users cannot list results"""
        list_url = reverse("result-list")
        response = api_client.get(list_url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_results_only_own_results(self, api_client, user1, result1, result2):
        """Test that users can only see their own results"""
        api_client.force_authenticate(user=user1)
        list_url = reverse("result-list")
        response = api_client.get(list_url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["query"] == result1.query.id

        # User1 should not see user2's results
        ids = [result["id"] for result in response.data]
        assert result2.id not in ids


@pytest.mark.django_db
class TestResultViewSetRetrieve:
    """Test cases for retrieving individual results"""

    def test_retrieve_own_result(self, api_client, user1, result1):
        """Test retrieving a specific result by ID"""
        api_client.force_authenticate(user=user1)
        detail_url = reverse("result-detail", kwargs={"id": result1.id})
        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == result1.id
        assert response.data["status"] == ResultStatus.COMPLETED

    def test_retrieve_other_user_result_forbidden(self, api_client, user1, result2):
        """Test that users cannot retrieve other users' results"""
        api_client.force_authenticate(user=user1)
        detail_url = reverse("result-detail", kwargs={"id": result2.id})
        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_queryset_uses_select_related(
        self, api_client, user1, result1, django_assert_num_queries
    ):
        """Test that queryset uses select_related for efficiency"""
        api_client.force_authenticate(user=user1)
        detail_url = reverse("result-detail", kwargs={"id": result1.id})

        with django_assert_num_queries(
            1
        ):  # Should be only 1 query due to select_related
            response = api_client.get(detail_url)
            assert response.status_code == status.HTTP_200_OK

    def test_retrieve_pending_result_checks_pipeline(
        self, mocker, api_client, user1, result1
    ):
        result1.status = ResultStatus.PENDING
        result1.save()

        pipeline_response = {
            "id": result1.id,
            "status": ResultStatus.RUNNING,
            "ror_values": [],
            "ror_lower": [],
            "ror_upper": [],
        }

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task",
            return_value=pipeline_response,
        )

        api_client.force_authenticate(user=user1)
        detail_url = reverse("result-detail", kwargs={"id": result1.id})
        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        mock_check_status.assert_called_once_with(result1.id)

        result1.refresh_from_db()
        assert result1.status == ResultStatus.RUNNING

    def test_retrieve_running_result_timeout_exceeded(
        self, mocker, api_client, user1, result1, settings
    ):
        settings.PIPELINE_TASK_TIMEOUT_MINUTES = 45
        old_time = timezone.now() - timedelta(minutes=50)
        result1.query.created_at = old_time
        result1.query.save()

        result1.status = ResultStatus.RUNNING
        result1.save()

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task"
        )

        api_client.force_authenticate(user=user1)
        detail_url = reverse("result-detail", kwargs={"id": result1.id})
        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        mock_check_status.assert_not_called()

        result1.refresh_from_db()
        assert result1.status == ResultStatus.FAILED

    def test_retrieve_pending_result_pipeline_returns_completed(
        self, mocker, api_client, user1, result1
    ):
        result1.status = ResultStatus.PENDING
        result1.save()

        pipeline_response = {
            "id": result1.id,
            "status": ResultStatus.COMPLETED,
            "ror_values": [2.1, 2.5, 3.0],
            "ror_lower": [1.8, 2.2, 2.7],
            "ror_upper": [2.4, 2.8, 3.3],
        }

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task",
            return_value=pipeline_response,
        )

        api_client.force_authenticate(user=user1)
        detail_url = reverse("result-detail", kwargs={"id": result1.id})
        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        mock_check_status.assert_called_once_with(result1.id)

        result1.refresh_from_db()
        assert result1.status == ResultStatus.COMPLETED
        assert result1.ror_values == [2.1, 2.5, 3.0]
        assert result1.ror_lower == [1.8, 2.2, 2.7]
        assert result1.ror_upper == [2.4, 2.8, 3.3]

    def test_retrieve_running_result_pipeline_not_found(
        self, mocker, api_client, user1, result1
    ):
        """Test that running result is marked as failed when pipeline returns 404"""
        result1.status = ResultStatus.RUNNING
        result1.save()

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task", return_value=None
        )

        api_client.force_authenticate(user=user1)
        detail_url = reverse("result-detail", kwargs={"id": result1.id})
        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        mock_check_status.assert_called_once_with(result1.id)

        result1.refresh_from_db()
        assert result1.status == ResultStatus.FAILED

    def test_retrieve_completed_result_no_pipeline_check(
        self, mocker, api_client, user1, result1
    ):
        result1.status = ResultStatus.COMPLETED
        result1.ror_values = [1.0, 2.0]
        result1.save()

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task"
        )

        api_client.force_authenticate(user=user1)
        detail_url = reverse("result-detail", kwargs={"id": result1.id})
        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        mock_check_status.assert_not_called()
        assert response.data["status"] == ResultStatus.COMPLETED


@pytest.mark.django_db
class TestResultViewSetRestrictions:
    """Test cases for create/update/delete restrictions"""

    def test_create_result_not_allowed(self, api_client, user1, query1, result_data):
        """Test that creating results via API is not allowed"""
        api_client.force_authenticate(user=user1)
        list_url = reverse("result-list")
        result_data["query"] = query1.id
        response = api_client.post(list_url, result_data)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_result_not_allowed(self, api_client, user1, result1):
        """Test that deleting results via API is not allowed"""
        api_client.force_authenticate(user=user1)
        detail_url = reverse("result-detail", kwargs={"id": result1.id})
        response = api_client.delete(detail_url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_update_result_not_allowed_for_regular_users(
        self, api_client, user1, result1
    ):
        """Test that regular users cannot update results"""
        api_client.force_authenticate(user=user1)
        detail_url = reverse("result-detail", kwargs={"id": result1.id})
        data = {"status": ResultStatus.COMPLETED}
        response = api_client.put(detail_url, data)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestResultViewSetUpdateByTaskId:
    """Test cases for external service update by task_id"""

    def test_update_by_task_id_authorized_ip(
        self, settings, api_client, result1, result_data
    ):
        """Test that external service can update by task_id with authorized IP"""
        settings.PIPELINE_SERVICE_IPS = ["192.168.1.100"]
        update_url = reverse("result-update-by-task-id", kwargs={"task_id": result1.id})

        response = api_client.put(
            update_url,
            result_data,
            REMOTE_ADDR="192.168.1.100",
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == ResultStatus.COMPLETED
        assert response.data["ror_values"] == [2.5, 3.0]

        # Verify database was updated
        result1.refresh_from_db()
        assert result1.status == result_data["status"]
        assert result1.ror_values == result_data["ror_values"]

    def test_update_by_task_id_unauthorized_ip(self, api_client, result1, result_data):
        """Test that unauthorized IP cannot update by task_id"""
        settings.PIPELINE_SERVICE_IPS = ["192.168.1.100"]
        update_url = reverse("result-update-by-task-id", kwargs={"task_id": result1.id})

        response = api_client.put(
            update_url,
            result_data,
            REMOTE_ADDR="10.0.0.1",  # Different IP
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_by_task_id_not_found(self, settings, api_client, result_data):
        """Test update with non-existent task_id"""
        settings.PIPELINE_SERVICE_IPS = ["192.168.1.100"]
        update_url = reverse("result-update-by-task-id", kwargs={"task_id": "1000000"})

        response = api_client.put(
            update_url,
            result_data,
            REMOTE_ADDR="192.168.1.100",
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.data["error"].lower()

    def update_by_task_id_invalid_id(self, settings, api_client, result_data):
        """Test update with invalid task_id format"""
        settings.PIPELINE_SERVICE_IPS = ["192.168.1.100"]

        update_url = reverse("result-update-by-task-id", kwargs={"task_id": "invalid"})

        response = api_client.put(
            update_url, result_data, REMOTE_ADDR="192.168.1.100", format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid task_id" in response.data["error"].lower()


@pytest.mark.django_db
class TestQueryRetrieveWithPipelineStatusChecks:
    """Test cases for query retrieve and pipeline status checks"""

    def test_retrieve_query_with_completed_result_no_pipeline_check(
        self, mocker, api_client, user1, query1
    ):
        """Test that completed results don't trigger pipeline status check"""
        query1.result.status = ResultStatus.COMPLETED
        query1.result.ror_values = [1.5, 2.0]
        query1.result.save()

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task"
        )

        api_client.force_authenticate(user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query1.id})

        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        mock_check_status.assert_not_called()

    @pytest.mark.parametrize(
        "initial_status", [ResultStatus.PENDING, ResultStatus.RUNNING]
    )
    def test_retrieve_query_with_error_status(
        self, mocker, api_client, user1, query1, initial_status
    ):
        """Test that result is marked as failed when pipeline returns 404"""
        query1.result.status = initial_status
        query1.result.save()

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task",
            return_value=None,  # Simulates 404 or error
        )

        api_client.force_authenticate(user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query1.id})

        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        mock_check_status.assert_called_once_with(query1.result.id)

        query1.result.refresh_from_db()
        assert query1.result.status == ResultStatus.FAILED

    @pytest.mark.parametrize(
        "initial_status, final_status",
        [
            (ResultStatus.PENDING, ResultStatus.RUNNING),
            (ResultStatus.RUNNING, ResultStatus.RUNNING),
            (ResultStatus.RUNNING, ResultStatus.FAILED),
        ],
    )
    def test_retrieve_query_with_pending_result_pipeline_returns_running(
        self, mocker, api_client, user1, query1, initial_status, final_status
    ):
        """Test that pending result is updated to running when pipeline returns running status"""
        query1.result.status = initial_status
        query1.result.save()

        pipeline_response = {
            "id": query1.result.id,
            "status": final_status,
            "ror_values": [],
            "ror_lower": [],
            "ror_upper": [],
        }

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task",
            return_value=pipeline_response,
        )

        api_client.force_authenticate(user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query1.id})

        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        mock_check_status.assert_called_once_with(query1.result.id)

        query1.result.refresh_from_db()
        assert query1.result.status == final_status

    def test_retrieve_query_running_pipeline_returns_completed(
        self, mocker, api_client, user1, query1
    ):
        """Test that running result is updated to completed with ROR values from pipeline"""
        query1.result.status = ResultStatus.RUNNING
        query1.result.save()

        pipeline_response = {
            "id": query1.result.id,
            "status": ResultStatus.COMPLETED,
            "ror_values": [2.5, 3.0],
            "ror_lower": [2.0, 2.5],
            "ror_upper": [3.0, 3.5],
        }

        mock_get_results = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task",
            return_value=pipeline_response,
        )

        api_client.force_authenticate(user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query1.id})

        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        mock_get_results.assert_called_once_with(query1.result.id)

        query1.result.refresh_from_db()
        assert query1.result.status == ResultStatus.COMPLETED
        assert query1.result.ror_values == [2.5, 3.0]
        assert query1.result.ror_lower == [2.0, 2.5]
        assert query1.result.ror_upper == [3.0, 3.5]

    def test_retrieve_query_pipeline_returns_invalid_data(
        self, mocker, api_client, user1, query1
    ):
        """Test that result is marked as failed when pipeline returns invalid data"""
        query1.result.status = ResultStatus.PENDING
        query1.result.save()

        pipeline_response = {
            "id": query1.result.id,
            "status": "invalid_status",  # Invalid status value
            "ror_values": "not_a_list",  # Invalid type
        }

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task",
            return_value=pipeline_response,
        )

        api_client.force_authenticate(user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query1.id})

        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        mock_check_status.assert_called_once_with(query1.result.id)

        query1.result.refresh_from_db()
        assert query1.result.status == ResultStatus.FAILED

    def test_retrieve_query_pipeline_status_unchanged(
        self, mocker, api_client, user1, query1
    ):
        """Test that result is not updated when pipeline returns same status"""
        query1.result.status = ResultStatus.RUNNING
        query1.result.ror_values = [1.0]
        query1.result.save()

        pipeline_response = {
            "id": query1.result.id,
            "status": ResultStatus.RUNNING,
            "ror_values": [1.0],
            "ror_lower": [],
            "ror_upper": [],
        }

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task",
            return_value=pipeline_response,
        )

        api_client.force_authenticate(user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query1.id})

        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        mock_check_status.assert_called_once_with(query1.result.id)

        query1.result.refresh_from_db()
        assert query1.result.status == ResultStatus.RUNNING
        assert query1.result.ror_values == [1.0]

    def test_retrieve_query_without_result_no_error(
        self, mocker, api_client, user1, drug, reaction
    ):
        """Test that queries without results don't cause errors"""
        query_no_result = Query.objects.create(
            user=user1,
            name="Query without result",
            quarter_start=1,
            quarter_end=2,
            year_start=2020,
            year_end=2020,
        )
        query_no_result.drugs.set([drug.id])
        query_no_result.reactions.set([reaction.id])

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task"
        )

        api_client.force_authenticate(user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query_no_result.id})

        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        mock_check_status.assert_not_called()


@pytest.mark.django_db
class TestQueryRetrieveWithTimeoutAndCompletedResults:
    """Test cases for query retrieve with task timeout and completed result fetching"""

    @pytest.mark.parametrize(
        "initial_status", [ResultStatus.PENDING, ResultStatus.RUNNING]
    )
    def test_retrieve_query_task_timeout_exceeded(
        self, mocker, api_client, user1, query1, settings, initial_status
    ):
        """Test that pending result is marked as failed when task exceeds timeout threshold"""

        settings.PIPELINE_TASK_TIMEOUT_MINUTES = 60

        # Set query created_at to 61 minutes ago (exceeds timeout)
        old_time = timezone.now() - timedelta(minutes=61)
        query1.created_at = old_time
        query1.save()

        query1.result.status = initial_status
        query1.result.save()

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task"
        )

        api_client.force_authenticate(user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query1.id})

        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        # Pipeline should NOT be checked since timeout was exceeded
        mock_check_status.assert_not_called()

        query1.result.refresh_from_db()
        assert query1.result.status == ResultStatus.FAILED

    def test_retrieve_query_pending_task_within_timeout(
        self, mocker, api_client, user1, query1, settings
    ):
        """Test that pending result is checked when task is within timeout threshold"""

        settings.PIPELINE_TASK_TIMEOUT_MINUTES = 60

        # Set query created_at to 30 minutes ago (within timeout)
        recent_time = timezone.now() - timedelta(minutes=30)
        query1.created_at = recent_time
        query1.save()

        query1.result.status = ResultStatus.PENDING
        query1.result.save()

        pipeline_response = {
            "id": query1.result.id,
            "status": ResultStatus.RUNNING,
            "ror_values": [],
            "ror_lower": [],
            "ror_upper": [],
        }

        mock_check_status = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task",
            return_value=pipeline_response,
        )

        api_client.force_authenticate(user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query1.id})

        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        mock_check_status.assert_called_once_with(query1.result.id)

        query1.result.refresh_from_db()
        assert query1.result.status == ResultStatus.RUNNING

    def test_retrieve_query_completed_status_but_failed_to_fetch_details(
        self, mocker, api_client, user1, query1
    ):
        """Test that result is marked as failed when fetching detailed results fails"""
        query1.result.status = ResultStatus.PENDING
        query1.result.save()

        # Simulate failure to fetch detailed results
        mock_get_results = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task", return_value=None
        )

        api_client.force_authenticate(user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query1.id})

        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        mock_get_results.assert_called_once_with(query1.result.id)

        query1.result.refresh_from_db()
        assert query1.result.status == ResultStatus.FAILED

    def test_retrieve_query_completed_status_invalid_detailed_results(
        self, mocker, api_client, user1, query1
    ):
        """Test that result is marked as failed when detailed results are invalid"""
        # Arrange
        query1.result.status = ResultStatus.RUNNING
        query1.result.save()

        pipeline_status_response = {
            "id": query1.result.id,
            "status": ResultStatus.COMPLETED,
        }

        # Invalid detailed results (missing required fields)
        invalid_detailed_results = {
            "id": query1.result.id,
            "status": "invalid_status",
            "ror_values": "not_a_list",
        }

        mock_get_results = mocker.patch(
            "analysis.views.pipeline_service.get_pipeline_task",
            return_value=invalid_detailed_results,
        )

        api_client.force_authenticate(user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query1.id})

        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        mock_get_results.assert_called_once_with(query1.result.id)

        query1.result.refresh_from_db()
        assert query1.result.status == ResultStatus.FAILED
