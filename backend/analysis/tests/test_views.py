from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from analysis.models import Query, DrugList, ReactionList
from analysis.serializers import QuerySerializer
from users.models import User
from django.conf import settings
from django.db import transaction


class QueryViewSetTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """Set up test data for authenticated users and queries."""
        cls.user1 = User.objects.create_user(
            email="user1@example.com", password="testpassword1"
        )
        cls.user2 = User.objects.create_user(
            email="user2@example.com", password="testpassword2"
        )

        # Create a drug & a reaction
        drug = DrugList.objects.create(name="drug")
        reaction = ReactionList.objects.create(name="reaction")

        cls.required_fields = {
            "quarter_start": 1,
            "quarter_end": 1,
            "drugs": [drug.id],
            "reactions": [reaction.id],
        }

        cls.query1 = Query.objects.create(
            user=cls.user1,
            name="User1 Query 1",
            quarter_start=1,
            quarter_end=1,
        )
        cls.query2 = Query.objects.create(
            user=cls.user1,
            name="User1 Query 2",
            quarter_start=1,
            quarter_end=1,
        )
        cls.query3 = Query.objects.create(
            user=cls.user2,
            name="User2 Query",
            quarter_start=1,
            quarter_end=1,
        )
        for query in [cls.query1, cls.query2, cls.query3]:
            query.drugs.set([drug.id])
            query.reactions.set([reaction.id])

        cls.list_url = reverse("query-list")  # URL for listing queries
        cls.detail_url = lambda query_id: reverse(
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
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.access_cookie = response.cookies[settings.REST_AUTH["JWT_AUTH_COOKIE"]]
        self.client.cookies[settings.REST_AUTH["JWT_AUTH_COOKIE"]] = (
            self.access_cookie
        )  # Attach JWT to client requests

    def test_list_queries_authenticated_user(self):
        """Test that an authenticated user can list only their own queries."""
        self.authenticate_user()
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # user1 has two queries

        expected_data = QuerySerializer([self.query2, self.query1], many=True).data
        expected_data_sorted = sorted(expected_data, key=lambda x: x["id"])
        response_data_sorted = sorted(response.data, key=lambda x: x["id"])
        self.assertEqual(response_data_sorted, expected_data_sorted)

    def test_list_queries_unauthenticated_user(self):
        """Test that an unauthenticated user cannot access the query list."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_query_owned_by_user(self):
        """Test that a user can retrieve their own query."""
        self.authenticate_user()
        response = self.client.get(self.detail_url(self.query1.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = QuerySerializer(self.query1).data
        self.assertEqual(response.data, expected_data)

    def test_retrieve_query_not_owned_by_user(self):
        """Test that a user cannot retrieve someone else's query."""
        self.authenticate_user()
        response = self.client.get(
            self.detail_url(self.query3.id)
        )  # user1 tries to access user2's query

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_query_authenticated_user(self):
        """Test that an authenticated user can create a query."""
        self.authenticate_user()
        data = {"name": "New Query by User1", **self.required_fields}
        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Query.objects.filter(user=self.user1).count(), 3
        )  # User1 now has 3 queries

    def test_create_query_unauthenticated_user(self):
        """Test that an unauthenticated user cannot create a query."""
        data = {"data": "Unauthorized Query", **self.required_fields}
        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Query.objects.count(), 3)  # No new queries should be added

    def test_delete_query_owned_by_user(self):
        """Test that a user can delete their own query."""
        self.authenticate_user()
        response = self.client.delete(self.detail_url(self.query1.id))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Query.objects.filter(id=self.query1.id).exists())

    def test_delete_query_not_owned_by_user(self):
        """Test that a user cannot delete someone else's query."""
        self.authenticate_user()
        response = self.client.delete(
            self.detail_url(self.query3.id)
        )  # User1 tries to delete User2's query

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(
            Query.objects.filter(id=self.query3.id).exists()
        )  # Query should still exist

    def test_partial_update_query_owned_by_user(self):
        """Test that a user can update their own query."""
        self.authenticate_user()
        updated_name = {"name": "Updated Query"}
        response = self.client.patch(self.detail_url(self.query1.id), updated_name)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.query1.refresh_from_db()
        self.assertEqual(self.query1.name, "Updated Query")

    def test_partial_update_query_not_owned_by_user(self):
        """Test that a user cannot update someone else's query."""
        self.authenticate_user()
        updated_name = {"name": "Attempted Unauthorized Update"}
        response = self.client.patch(self.detail_url(self.query3.id), updated_name)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.query3.refresh_from_db()
        self.assertNotEqual(
            self.query3.name, "Attempted Unauthorized Update"
        )  # Data remains unchanged

    def test_full_update_query_owned_by_user(self):
        """Test that a user can update their own query."""
        self.authenticate_user()
        updated_data = self.required_fields.copy()
        updated_data["name"] = "Updated Query"
        response = self.client.put(self.detail_url(self.query1.id), updated_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.query1.refresh_from_db()
        self.assertEqual(self.query1.name, "Updated Query")

    def test_full_update_query_not_owned_by_user(self):
        """Test that a user cannot update someone else's query."""
        self.authenticate_user()
        updated_data = self.required_fields.copy()
        updated_data["name"] = "Attempted Unauthorized Update"
        response = self.client.put(self.detail_url(self.query3.id), updated_data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.query3.refresh_from_db()
        self.assertNotEqual(
            self.query3.name, "Attempted Unauthorized Update"
        )  # Data remains unchanged
