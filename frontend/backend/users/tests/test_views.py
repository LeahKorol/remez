from django.test import TestCase
from django.conf import settings
from django.contrib.auth import get_user_model


class Registration(TestCase):
    base_url = "http://127.0.0.1:8000/api/v1/auth/registration/"

    def setUp(self):
        """Set up test data"""
        self.valid_payload = {
            "email": "user1@example.com",
            "password1": "t1234567",
            "password2": "t1234567",
        }

    def test_registration_success(self):
        """Test successful user registration"""
        response = self.client.post(
            path=self.base_url, data=self.valid_payload, content_type="application/json"
        )
        # print("\nResponse JSON:", response.json())
        # print("\nResponse cookies:", self.client.cookies)

        self.assertEqual(response.status_code, 201)
        # Check JWT cookies are set
        self.assertIn(settings.REST_AUTH["JWT_AUTH_COOKIE"], response.cookies)
        self.assertIn(settings.REST_AUTH["JWT_AUTH_REFRESH_COOKIE"], response.cookies)

    def test_registration_invalid_email(self):
        """Test registration with invalid email"""
        invalid_payload = self.valid_payload.copy()
        invalid_payload["email"] = "invalid-email"

        response = self.client.post(
            path=self.base_url, data=invalid_payload, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_registration_saving_details(self):
        """Test user's details are saved in the database"""
        payload = self.valid_payload.copy()
        payload["name"] = "test_name"
        payload["email"] = "user2@example.com"

        self.client.post(
            path=self.base_url, data=payload, content_type="application/json"
        )
        user = get_user_model().objects.get(email=payload["email"])
        self.assertEqual(user.name, payload["name"])
        self.assertEqual(user.email, payload["email"])


class Login(TestCase):
    base_url = "http://127.0.0.1:8000/api/v1/auth/login/"

    def setUp(self):
        """Set up test data"""
        self.user_data = {
            "email": "testuser@example.com",
            "password": "testpass123",
        }
        # Create a user for login tests
        self.user = get_user_model().objects.create_user(
            email=self.user_data["email"], password=self.user_data["password"]
        )

    def test_login_success(self):
        """Test successful login"""
        response = self.client.post(
            path=self.base_url, data=self.user_data, content_type="application/json"
        )
        # print("\nResponse JSON:", response.json())
        # print("\nResponse cookies:", response.cookies)

        self.assertEqual(response.status_code, 200)
        # Check JWT cookies are set
        self.assertIn(settings.REST_AUTH["JWT_AUTH_COOKIE"], response.cookies)
        self.assertIn(settings.REST_AUTH["JWT_AUTH_REFRESH_COOKIE"], response.cookies)

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        invalid_data = self.user_data.copy()
        invalid_data["password"] = "wrongpassword"

        response = self.client.post(
            path=self.base_url, data=invalid_data, content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)

    def test_login_user_not_found(self):
        """Test login with non-existent user"""
        non_existent_user = {
            "email": "nonexistent@example.com",
            "password": "testpass123",
        }

        response = self.client.post(
            path=self.base_url, data=non_existent_user, content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
