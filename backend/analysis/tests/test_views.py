import pytest
from allauth.account.models import EmailAddress
from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import User

from analysis.models import DrugName, Query, ReactionName
from analysis.serializers import QuerySerializer


@pytest.mark.django_db
class TestQueryViewSet:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data for authenticated users and queries."""
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            email="user1@example.com", password="testpassword1"
        )
        email_address1 = EmailAddress.objects.get(user=self.user1)
        email_address1.verified = True
        email_address1.save()

        self.user2 = User.objects.create_user(
            email="user2@example.com", password="testpassword2"
        )
        email_address2 = EmailAddress.objects.get(user=self.user2)
        email_address2.verified = True
        email_address2.save()

        # Create a drug & a reaction
        drug = DrugName.objects.create(name="drug")
        reaction = ReactionName.objects.create(name="reaction")

        self.required_fields = {
            "quarter_start": 1,
            "quarter_end": 2,
            "year_start": 2020,
            "year_end": 2020,
            "drugs": [drug.id],
            "reactions": [reaction.id],
        }

        self.query1 = Query.objects.create(
            user=self.user1,
            name="User1 Query 1",
            quarter_start=1,
            quarter_end=2,
            year_start=2020,
            year_end=2020,
        )
        self.query2 = Query.objects.create(
            user=self.user1,
            name="User1 Query 2",
            quarter_start=1,
            quarter_end=2,
            year_start=2021,
            year_end=2021,
        )
        self.query3 = Query.objects.create(
            user=self.user2,
            name="User2 Query",
            quarter_start=1,
            quarter_end=2,
            year_start=2022,
            year_end=2022,
        )
        for query in [self.query1, self.query2, self.query3]:
            query.drugs.set([drug.id])
            query.reactions.set([reaction.id])

        self.list_url = reverse("query-list")  # URL for listing queries
        self.detail_url = lambda query_id: reverse(
            "query-detail", kwargs={"id": query_id}
        )  # URL for a single query

    def authenticate_user(self, email="user1@example.com", password="testpassword1"):
        """Login and store JWT cookie for authentication."""
        auth_url = "http://127.0.0.1:8000/api/v1/auth/login/"
        response = self.client.post(
            auth_url,
            data={"email": email, "password": password},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        self.access_cookie = response.cookies[settings.REST_AUTH["JWT_AUTH_COOKIE"]]
        self.client.cookies[settings.REST_AUTH["JWT_AUTH_COOKIE"]] = (
            self.access_cookie
        )  # Attach JWT to client requests

    def test_list_queries_authenticated_user(self):
        """Test that an authenticated user can list only their own queries."""
        self.authenticate_user()
        response = self.client.get(self.list_url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2  # user1 has two queries

        expected_data = QuerySerializer([self.query2, self.query1], many=True).data
        expected_data_sorted = sorted(expected_data, key=lambda x: x["id"])
        response_data_sorted = sorted(response.data, key=lambda x: x["id"])
        assert response_data_sorted == expected_data_sorted

    def test_list_queries_unauthenticated_user(self):
        """Test that an unauthenticated user cannot access the query list."""
        response = self.client.get(self.list_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_query_owned_by_user(self):
        """Test that a user can retrieve their own query."""
        self.authenticate_user()
        response = self.client.get(self.detail_url(self.query1.id))

        assert response.status_code == status.HTTP_200_OK
        expected_data = QuerySerializer(self.query1).data
        assert response.data == expected_data

    def test_retrieve_query_not_owned_by_user(self):
        """Test that a user cannot retrieve someone else's query."""
        self.authenticate_user()
        response = self.client.get(
            self.detail_url(self.query3.id)
        )  # user1 tries to access user2's query

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_query_authenticated_user(self):
        """Test that an authenticated user can create a query."""
        self.authenticate_user()
        data = {"name": "New Query by User1", **self.required_fields}
        response = self.client.post(self.list_url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert (
            Query.objects.filter(user=self.user1).count() == 3
        )  # User1 now has 3 queries

    def test_create_query_unauthenticated_user(self):
        """Test that an unauthenticated user cannot create a query."""
        data = {"data": "Unauthorized Query", **self.required_fields}
        response = self.client.post(self.list_url, data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Query.objects.count() == 3  # No new queries should be added

    def test_delete_query_owned_by_user(self):
        """Test that a user can delete their own query."""
        self.authenticate_user()
        response = self.client.delete(self.detail_url(self.query1.id))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Query.objects.filter(id=self.query1.id).exists()

    def test_delete_query_not_owned_by_user(self):
        """Test that a user cannot delete someone else's query."""
        self.authenticate_user()
        response = self.client.delete(
            self.detail_url(self.query3.id)
        )  # User1 tries to delete User2's query

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Query.objects.filter(
            id=self.query3.id
        ).exists()  # Query should still exist

    def test_partial_update_query_owned_by_user(self):
        """Test that a user can update their own query."""
        self.authenticate_user()
        updated_name = {"name": "Updated Query"}
        response = self.client.patch(self.detail_url(self.query1.id), updated_name)

        assert response.status_code == status.HTTP_200_OK
        self.query1.refresh_from_db()
        assert self.query1.name == "Updated Query"

    def test_partial_update_query_not_owned_by_user(self):
        """Test that a user cannot update someone else's query."""
        self.authenticate_user()
        updated_name = {"name": "Attempted Unauthorized Update"}
        response = self.client.patch(self.detail_url(self.query3.id), updated_name)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        self.query3.refresh_from_db()
        assert (
            self.query3.name != "Attempted Unauthorized Update"
        )  # Data remains unchanged

    def test_full_update_query_owned_by_user(self):
        """Test that a user can update their own query."""
        self.authenticate_user()
        updated_data = self.required_fields.copy()
        updated_data["name"] = "Updated Query"
        response = self.client.put(self.detail_url(self.query1.id), updated_data)

        assert response.status_code == status.HTTP_200_OK
        self.query1.refresh_from_db()
        assert self.query1.name == "Updated Query"

    def test_full_update_query_not_owned_by_user(self):
        """Test that a user cannot update someone else's query."""
        self.authenticate_user()
        updated_data = self.required_fields.copy()
        updated_data["name"] = "Attempted Unauthorized Update"
        response = self.client.put(self.detail_url(self.query3.id), updated_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        self.query3.refresh_from_db()
        assert (
            self.query3.name != "Attempted Unauthorized Update"
        )  # Data remains unchanged

    @pytest.mark.parametrize("invalid_quarter", [0, 5, -1, 10])
    def test_query_serializer_blocks_invalid_quarters(self, invalid_quarter):
        """Test that serializer blocks invalid quarter numbers."""
        self.authenticate_user()
        updated_data = self.required_fields.copy()
        updated_data["quarter_start"] = invalid_quarter
        response = self.client.put(self.detail_url(self.query1.id), updated_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "quarter_start" in response.data

    def test_year_start_lte_year_end(self):
        """Test that serializer blocks year_start greater than year_end."""
        self.authenticate_user()
        updated_data = self.required_fields.copy()
        updated_data["year_start"] = 2022
        updated_data["year_end"] = 2021
        response = self.client.put(self.detail_url(self.query1.id), updated_data)
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
        self, year_start, year_end, quarter_start, quarter_end, res_status
    ):
        """Test that serializer blocks quarter_start greater than quarter_end."""
        self.authenticate_user()
        updated_data = self.required_fields.copy()
        updated_data["quarter_start"] = quarter_start
        updated_data["quarter_end"] = quarter_end
        updated_data["year_start"] = year_start
        updated_data["year_end"] = year_end
        response = self.client.put(self.detail_url(self.query1.id), updated_data)
        assert response.status_code == res_status
        if response.status_code != status.HTTP_200_OK:
            assert "quarter_start" in response.data
