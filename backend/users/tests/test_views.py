import os
from unittest.mock import MagicMock, patch

from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase


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
        # Check that no JWT cookies are set, as the user is not verified yet
        self.assertNotIn(settings.REST_AUTH["JWT_AUTH_COOKIE"], response.cookies)
        self.assertNotIn(
            settings.REST_AUTH["JWT_AUTH_REFRESH_COOKIE"], response.cookies
        )

        # Check that a confirmation email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            "[example.com] Please Confirm Your Email Address - REMEZ",
        )

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
        # Verify the user's email for login tests that require a verified user
        email_address = EmailAddress.objects.get(user=self.user)
        email_address.verified = True
        email_address.save()

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


class ResendEmailVerification(TestCase):
    base_url = "/api/v1/auth/resend-verification/"

    def setUp(self):
        """Set up test data"""
        self.user = get_user_model().objects.create_user(
            email="test@example.com", password="testpass123"
        )

    def test_resend_email_verification_success(self):
        """Test successful email verification resend"""
        response = self.client.post(
            path=self.base_url,
            data={"email": "test@example.com"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("Verification email sent successfully", response_data["message"])

    def test_resend_email_verification_missing_email(self):
        """Test resend verification with missing email"""
        response = self.client.post(
            path=self.base_url, data={}, content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn("required", response_data["email"][0])

    def test_resend_email_verification_already_verified(self):
        """Test resend verification for already verified email"""
        # Verify the user's email
        email_address = EmailAddress.objects.get(user=self.user)
        email_address.verified = True
        email_address.primary = True
        email_address.save()

        response = self.client.post(
            path=self.base_url,
            data={"email": "test@example.com"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("already verified", response_data["message"])

    def test_resend_email_verification_nonexistent_user(self):
        """Test resend verification for non-existent user"""
        response = self.client.post(
            path=self.base_url,
            data={"email": "nonexistent@example.com"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("If this email exists", response_data["message"])


class CheckEmailExists(TestCase):
    base_url = "/api/v1/auth/check-email/"

    def setUp(self):
        """Set up test data"""
        self.user = get_user_model().objects.create_user(
            email="existing@example.com", password="testpass123"
        )

    def test_check_email_exists_true(self):
        """Test check email exists returns true for existing email"""
        response = self.client.post(
            path=self.base_url,
            data={"email": "existing@example.com"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["exists"])

    def test_check_email_exists_false(self):
        """Test check email exists returns false for non-existing email"""
        response = self.client.post(
            path=self.base_url,
            data={"email": "nonexistent@example.com"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["exists"])

    def test_check_email_exists_case_insensitive(self):
        """Test check email exists is case insensitive"""
        response = self.client.post(
            path=self.base_url,
            data={"email": "EXISTING@EXAMPLE.COM"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["exists"])

    def test_check_email_exists_missing_email(self):
        """Test check email exists with missing email"""
        response = self.client.post(
            path=self.base_url, data={}, content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn("required", response_data["email"][0])


class PasswordResetConfirmRedirect(TestCase):
    def test_password_reset_confirm_redirect(self):
        """Test password reset confirm redirect"""
        with patch.object(
            settings,
            "PASSWORD_RESET_CONFIRM_REDIRECT_BASE_URL",
            "http://test.com/reset/",
        ):
            response = self.client.get("/api/v1/auth/reset-password/testuid/testtoken/")

            self.assertEqual(response.status_code, 302)
            expected_url = "http://test.com/reset/testuid/testtoken/"
            self.assertEqual(response.url, expected_url)


class VerifyEmailApi(TestCase):
    def test_verify_email_api_success(self):
        """Test email verification API success"""
        with patch("users.views.EmailConfirmationHMAC") as mock_hmac:
            mock_confirmation = MagicMock()
            mock_hmac.from_key.return_value = mock_confirmation

            with patch.dict(os.environ, {"FRONTEND_URL": "http://testfrontend.com"}):
                response = self.client.get("/api/v1/auth/verify-email/testkey/")

                self.assertEqual(response.status_code, 302)
                self.assertIn("testfrontend.com/login?verified=true", response.url)
                mock_confirmation.confirm.assert_called_once()

    def test_verify_email_api_failure(self):
        """Test email verification API failure"""
        with patch("users.views.EmailConfirmationHMAC") as mock_hmac:
            mock_hmac.from_key.side_effect = Exception("Test error")

            with patch.dict(os.environ, {"FRONTEND_URL": "http://testfrontend.com"}):
                response = self.client.get("/api/v1/auth/verify-email/testkey/")

                self.assertEqual(response.status_code, 302)
                self.assertIn("testfrontend.com/login?verified=false", response.url)

    def test_verify_email_api_hmac_fallback(self):
        """Test email verification API with HMAC fallback to EmailConfirmation"""
        with (
            patch("users.views.EmailConfirmationHMAC") as mock_hmac,
            patch("users.views.EmailConfirmation") as mock_confirmation_model,
        ):
            mock_hmac.from_key.return_value = None  # HMAC returns None
            mock_confirmation = MagicMock()
            mock_confirmation_model.objects.get.return_value = mock_confirmation

            with patch.dict(os.environ, {"FRONTEND_URL": "http://testfrontend.com"}):
                response = self.client.get("/api/v1/auth/verify-email/testkey/")

                self.assertEqual(response.status_code, 302)
                self.assertIn("testfrontend.com/login?verified=true", response.url)
                mock_confirmation_model.objects.get.assert_called_once_with(
                    key="testkey"
                )
                mock_confirmation.confirm.assert_called_once()


class CustomRegisterViewEdgeCases(TestCase):
    base_url = "/api/v1/auth/registration/"

    def test_finalize_response_with_jwt_enabled(self):
        """Test finalize_response when JWT is enabled and tokens are present"""
        valid_payload = {
            "email": "user@example.com",
            "password1": "t1234567",
            "password2": "t1234567",
        }

        # Mock JWT settings to be enabled
        with patch.object(settings, "REST_AUTH", {"USE_JWT": True}):
            response = self.client.post(
                path=self.base_url, data=valid_payload, content_type="application/json"
            )
            # The registration should succeed but no JWT cookies since user isn't verified yet
            self.assertEqual(response.status_code, 201)

    def test_finalize_response_with_jwt_disabled(self):
        """Test finalize_response when JWT is disabled"""
        valid_payload = {
            "email": "user2@example.com",
            "password1": "t1234567",
            "password2": "t1234567",
        }

        # Mock JWT settings to be disabled
        with patch.object(settings, "REST_AUTH", {"USE_JWT": False}):
            response = self.client.post(
                path=self.base_url, data=valid_payload, content_type="application/json"
            )
            self.assertEqual(response.status_code, 201)

    def test_create_email_verification_failure(self):
        """Test create method when email verification sending fails"""
        valid_payload = {
            "email": "user3@example.com",
            "password1": "t1234567",
            "password2": "t1234567",
        }

        # Mock send_email_confirmation to raise an exception
        with patch(
            "users.views.send_email_confirmation",
            side_effect=Exception("Email service down"),
        ):
            response = self.client.post(
                path=self.base_url, data=valid_payload, content_type="application/json"
            )
            # Should still succeed even if email fails
            self.assertEqual(response.status_code, 201)
            self.assertIn("Verification e-mail sent", response.json()["detail"])


class ResendEmailVerificationEdgeCases(TestCase):
    base_url = "/api/v1/auth/resend-verification/"

    def setUp(self):
        """Set up test data"""
        self.user = get_user_model().objects.create_user(
            email="test@example.com", password="testpass123"
        )

    def test_resend_email_verification_empty_body(self):
        """Test resend verification with empty request body"""
        # Send request with no body at all
        response = self.client.post(
            path=self.base_url, data="", content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn("required", response_data["email"][0])

    def test_resend_email_verification_inactive_user(self):
        """Test resend verification for inactive user"""
        # Create inactive user
        inactive_user = get_user_model().objects.create_user(
            email="inactive@example.com", password="testpass123", is_active=False
        )

        response = self.client.post(
            path=self.base_url,
            data={"email": "inactive@example.com"},
            content_type="application/json",
        )

        # Should return the same response as non-existent user for security
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("If this email exists", response_data["message"])
