from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from users.forms import CustomAllAuthPasswordResetForm
from users.serializers import (
    CustomLoginSerializer,
    CustomPasswordResetSerializer,
    CustomRegisterSerializer,
    UserSerializer,
)


class SerializerTestMixin:
    """Mixin class with common helper methods for serializer tests"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.User = get_user_model()
        cls.factory = RequestFactory()

    def create_user(self, email="test@example.com", password="testpass123", **kwargs):
        """Helper method to create a user"""
        return self.User.objects.create_user(email=email, password=password, **kwargs)

    def create_verified_user(
        self, email="test@example.com", password="testpass123", **kwargs
    ):
        """Helper method to create a user with verified email"""
        user = self.create_user(email=email, password=password, **kwargs)
        self.create_verified_email(user, email)
        return user

    def create_verified_email(self, user, email=None):
        """Helper method to create a verified email address for a user"""
        email = email or user.email
        EmailAddress.objects.filter(email=email).update(
            user=user, email=email, verified=True, primary=True
        )
        return EmailAddress.objects.get(email=email)

    def create_unverified_email(self, user, email=None):
        """Helper method to create an unverified email address for a user"""
        email = email or user.email
        EmailAddress.objects.filter(email=email).update(
            user=user, email=email, verified=False, primary=True
        )
        return EmailAddress.objects.get(email=email)

    def get_valid_user_data(self, **overrides):
        """Helper method to get valid user data"""
        data = {
            "email": "newuser@example.com",
            "password": "testpass123",
            "name": "New User",
        }
        data.update(overrides)
        return data

    def get_valid_registration_data(self, **overrides):
        """Helper method to get valid registration data"""
        data = {
            "email": "newuser@example.com",
            "password1": "testpass123",
            "password2": "testpass123",
            "name": "New User",
        }
        data.update(overrides)
        return data

    def create_serializer_with_context(self, serializer_class, data=None, **kwargs):
        """Helper method to create a serializer with request context"""
        request = self.factory.post("/")
        context = {"request": request}
        return serializer_class(data=data, context=context, **kwargs)

    def assert_serializer_valid(self, serializer):
        """Helper method to assert serializer is valid with better error messages"""
        if not serializer.is_valid():
            self.fail(f"Serializer errors: {serializer.errors}")

    def assert_serializer_invalid(self, serializer, field=None):
        """Helper method to assert serializer is invalid"""
        self.assertFalse(serializer.is_valid())
        if field:
            self.assertIn(field, serializer.errors)


class UserSerializerTests(SerializerTestMixin, TestCase):
    def setUp(self):
        """Set up test data"""
        self.user_data = self.get_valid_user_data(
            email="test@example.com", name="Test User"
        )
        self.user = self.create_user(**self.user_data)

    def test_create_user_success(self):
        """Test creating a user with valid data"""
        data = self.get_valid_user_data(
            email="newuser@example.com", password="newpass123"
        )
        serializer = UserSerializer(data=data)

        self.assert_serializer_valid(serializer)
        user = serializer.save()

        self.assertEqual(user.email, data["email"])
        self.assertEqual(user.name, data["name"])
        self.assertTrue(user.check_password(data["password"]))

    def test_create_user_password_too_short(self):
        """Test creating user with password less than 8 characters fails"""
        data = self.get_valid_user_data(password="short")
        serializer = UserSerializer(data=data)

        self.assert_serializer_invalid(serializer, "password")

    def test_create_user_invalid_email(self):
        """Test creating user with invalid email fails"""
        data = self.get_valid_user_data(email="invalid-email")
        serializer = UserSerializer(data=data)

        self.assert_serializer_invalid(serializer, "email")

    def test_update_user_success(self):
        """Test updating user data successfully"""
        data = {"name": "Updated Name", "email": "updated@example.com"}
        serializer = UserSerializer(instance=self.user, data=data, partial=True)

        self.assert_serializer_valid(serializer)
        updated_user = serializer.save()

        self.assertEqual(updated_user.name, data["name"])
        self.assertEqual(updated_user.email, data["email"])

    def test_update_user_password(self):
        """Test updating user password"""
        data = {"password": "newpassword123"}
        serializer = UserSerializer(instance=self.user, data=data, partial=True)

        self.assert_serializer_valid(serializer)
        updated_user = serializer.save()

        self.assertTrue(updated_user.check_password(data["password"]))

    def test_update_user_google_id_ignored(self):
        """Test that google_id cannot be updated externally"""
        original_google_id = self.user.google_id
        data = {"google_id": "new_google_id_123"}
        serializer = UserSerializer(instance=self.user, data=data, partial=True)

        self.assert_serializer_valid(serializer)
        updated_user = serializer.save()

        # Google ID should remain unchanged
        self.assertEqual(updated_user.google_id, original_google_id)

    def test_serializer_fields(self):
        """Test that serializer includes correct fields"""
        serializer = UserSerializer(instance=self.user)
        expected_fields = {"id", "email", "name", "google_id"}

        self.assertEqual(set(serializer.data.keys()), expected_fields)

    def test_password_write_only(self):
        """Test that password field is write-only"""
        serializer = UserSerializer(instance=self.user)

        # Password should not be in serialized data
        self.assertNotIn("password", serializer.data)

    def test_id_read_only(self):
        """Test that ID field is read-only"""
        data = self.get_valid_user_data(email="test2@example.com", name="Test User 2")
        data["id"] = 999
        serializer = UserSerializer(data=data)

        self.assert_serializer_valid(serializer)
        user = serializer.save()

        # ID should be auto-generated, not from input
        self.assertNotEqual(user.id, 999)

    def test_google_id_read_only(self):
        """Test that google_id field is read-only"""
        data = self.get_valid_user_data(email="test3@example.com", name="Test User 3")
        data["google_id"] = "should_be_ignored"
        serializer = UserSerializer(data=data)

        self.assert_serializer_valid(serializer)
        user = serializer.save()

        # Google ID should not be set from input
        self.assertIsNone(user.google_id)


class CustomRegisterSerializerTests(SerializerTestMixin, TestCase):
    def test_register_user_success(self):
        """Test successful user registration"""
        data = self.get_valid_registration_data()
        serializer = CustomRegisterSerializer(data=data)

        self.assert_serializer_valid(serializer)

    def test_register_user_no_username_field(self):
        """Test that username field is not required"""
        data = self.get_valid_registration_data()
        serializer = CustomRegisterSerializer(data=data)

        self.assert_serializer_valid(serializer)
        # Username should not be in validated data
        self.assertNotIn("username", serializer.validated_data)

    def test_register_user_name_optional(self):
        """Test that name field is optional"""
        data = self.get_valid_registration_data()
        data.pop("name")  # Remove name field
        serializer = CustomRegisterSerializer(data=data)

        self.assert_serializer_valid(serializer)

    def test_register_user_password_mismatch(self):
        """Test registration fails with password mismatch"""
        data = self.get_valid_registration_data(password2="differentpass")
        serializer = CustomRegisterSerializer(data=data)

        self.assert_serializer_invalid(serializer)

    def _test_email_validation_fails(self, existing_email, test_email, verified=True):
        """Helper method to test email validation failures"""
        user = self.create_user(email=existing_email)
        if verified:
            self.create_verified_email(user, existing_email)
        else:
            self.create_unverified_email(user, existing_email)

        data = self.get_valid_registration_data(email=test_email)
        serializer = CustomRegisterSerializer(data=data)

        self.assert_serializer_invalid(serializer, "email")

    def test_validate_email_duplicate_verified(self):
        """Test email validation fails for existing verified email"""
        self._test_email_validation_fails(
            "existing@example.com", "existing@example.com"
        )

        # Check specific error message for verified emails
        data = self.get_valid_registration_data(email="existing@example.com")
        serializer = CustomRegisterSerializer(data=data)
        serializer.is_valid()
        self.assertIn("already registered", str(serializer.errors["email"][0]))

    def test_validate_email_duplicate_unverified(self):
        """Test email validation fails for existing unverified email"""
        self._test_email_validation_fails(
            "unverified@example.com", "unverified@example.com", verified=False
        )

    def test_validate_email_case_insensitive(self):
        """Test email validation is case insensitive"""
        self._test_email_validation_fails("test@example.com", "TEST@EXAMPLE.COM")

    def _test_custom_signup(self, name_value, expected_name=""):
        """Helper method to test custom_signup functionality"""
        request = self.factory.post("/")
        user = self.create_user()

        # Create serializer with proper data
        data = self.get_valid_registration_data()
        if name_value is not None:
            data["name"] = name_value
        else:
            data.pop("name", None)

        serializer = CustomRegisterSerializer(data=data)
        self.assert_serializer_valid(serializer)

        # Test custom_signup method
        serializer.custom_signup(request, user)

        user.refresh_from_db()
        self.assertEqual(user.name, expected_name or name_value or "")

    def test_custom_signup_saves_name(self):
        """Test that custom_signup saves the name field"""
        self._test_custom_signup("Test Name")

    def test_custom_signup_empty_name(self):
        """Test custom_signup with empty name"""
        self._test_custom_signup(None, "")


class CustomLoginSerializerTests(SerializerTestMixin, TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = self.create_verified_user()

    def test_login_serializer_no_username_field(self):
        """Test that login serializer doesn't require username"""
        data = {"email": "test@example.com", "password": "testpass123"}
        serializer = self.create_serializer_with_context(CustomLoginSerializer, data)

        self.assert_serializer_valid(serializer)

    def test_login_serializer_invalid_credentials(self):
        """Test login with invalid credentials"""
        data = {"email": "test@example.com", "password": "wrongpassword"}
        serializer = self.create_serializer_with_context(CustomLoginSerializer, data)

        self.assert_serializer_invalid(serializer)


class CustomPasswordResetSerializerTests(SerializerTestMixin, TestCase):
    def test_password_reset_form_class(self):
        """Test that custom password reset form class is used"""
        serializer = CustomPasswordResetSerializer()

        self.assertEqual(
            serializer.password_reset_form_class, CustomAllAuthPasswordResetForm
        )

    def test_password_reset_serializer_valid_email(self):
        """Test password reset with valid email"""
        self.create_user(email="test@example.com")
        data = {"email": "test@example.com"}
        serializer = CustomPasswordResetSerializer(data=data)

        self.assert_serializer_valid(serializer)

    def test_password_reset_serializer_invalid_email(self):
        """Test password reset with invalid email format"""
        data = {"email": "invalid-email"}
        serializer = CustomPasswordResetSerializer(data=data)

        self.assert_serializer_invalid(serializer, "email")

    def test_password_reset_serializer_nonexistent_email(self):
        """Test password reset with nonexistent email"""
        data = {"email": "nonexistent@example.com"}
        serializer = CustomPasswordResetSerializer(data=data)

        # Should still be valid (don't reveal if email exists)
        self.assert_serializer_valid(serializer)
