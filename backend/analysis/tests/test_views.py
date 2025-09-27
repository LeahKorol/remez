import pytest
from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from analysis.models import DrugName, Query, ReactionName, Result, ResultStatus
from analysis.serializers import QuerySerializer

User = get_user_model()


@pytest.fixture
def api_client():
    """Fixture for API client"""
    return APIClient()


@pytest.fixture
def user1(db):
    """Fixture for first test user"""
    user = User.objects.create_user(email="user1@example.com", password="testpassword1")
    email_address = EmailAddress.objects.get(user=user)
    email_address.verified = True
    email_address.save()
    return user


@pytest.fixture
def user2(db):
    """Fixture for second test user"""
    user = User.objects.create_user(email="user2@example.com", password="testpassword2")
    email_address = EmailAddress.objects.get(user=user)
    email_address.verified = True
    email_address.save()
    return user


@pytest.fixture
def drug(db):
    """Fixture for drug name"""
    return DrugName.objects.create(name="drug")


@pytest.fixture
def reaction(db):
    """Fixture for reaction name"""
    return ReactionName.objects.create(name="reaction")


@pytest.fixture
def required_fields(drug, reaction):
    """Fixture for required query fields"""
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
    """Fixture for query belonging to user1"""
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
    return query


@pytest.fixture
def result1(query1):
    """Fixture for result belonging to user1"""
    return Result.objects.create(
        query=query1,
        status=ResultStatus.COMPLETED,
        ror_values=[1.5, 2.0],
        ror_lower=[1.2, 1.8],
        ror_upper=[1.8, 2.2],
    )


@pytest.fixture
def result2(query3):
    """Fixture for result belonging to user2"""
    return Result.objects.create(
        query=query3,
        status=ResultStatus.PENDING,
        ror_values=[],
        ror_lower=[],
        ror_upper=[],
    )


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
        expected_data = QuerySerializer(query1).data
        assert response.data == expected_data

    def test_retrieve_query_not_owned_by_user(self, api_client, user1, query3):
        """Test that a user cannot retrieve someone else's query."""
        self.authenticate_user(api_client, user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query3.id})
        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_query_authenticated_user(self, api_client, user1, required_fields):
        """Test that an authenticated user can create a query."""
        self.authenticate_user(api_client, user=user1)
        list_url = reverse("query-list")
        data = {"name": "New Query by User1", **required_fields}
        response = api_client.post(list_url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Query.objects.filter(user=user1).count() == 1

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

    def test_partial_update_query_owned_by_user(self, api_client, user1, query1):
        """Test that a user can update their own query."""
        self.authenticate_user(api_client, user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query1.id})
        updated_name = {"name": "Updated Query"}
        response = api_client.patch(detail_url, updated_name)

        assert response.status_code == status.HTTP_200_OK
        query1.refresh_from_db()
        assert query1.name == "Updated Query"

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
        self, api_client, user1, query1, required_fields
    ):
        """Test that a user can update their own query."""
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
        self, api_client, user1, query1, required_fields, invalid_quarter
    ):
        """Test that serializer blocks invalid quarter numbers."""
        self.authenticate_user(api_client, user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query1.id})
        updated_data = required_fields.copy()
        updated_data["quarter_start"] = invalid_quarter
        response = api_client.put(detail_url, updated_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "quarter_start" in response.data

    def test_year_start_lte_year_end(self, api_client, user1, query1, required_fields):
        """Test that serializer blocks year_start greater than year_end."""
        self.authenticate_user(api_client, user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query1.id})
        updated_data = required_fields.copy()
        updated_data["year_start"] = 2022
        updated_data["year_end"] = 2021
        response = api_client.put(detail_url, updated_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "year_start" in response.data

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
        """Test that serializer blocks quarter_start greater than quarter_end."""
        self.authenticate_user(api_client, user=user1)
        detail_url = reverse("query-detail", kwargs={"id": query1.id})
        updated_data = required_fields.copy()
        updated_data["quarter_start"] = quarter_start
        updated_data["quarter_end"] = quarter_end
        updated_data["year_start"] = year_start
        updated_data["year_end"] = year_end
        response = api_client.put(detail_url, updated_data)
        assert response.status_code == res_status
        if response.status_code != status.HTTP_200_OK:
            assert "quarter_start" in response.data


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
