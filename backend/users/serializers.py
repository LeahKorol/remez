"""
Serializers for user-related functionality.
"""

from allauth.account.adapter import get_adapter

# For overriding validate_email
from allauth.account.models import EmailAddress
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer, PasswordResetSerializer
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from users.forms import CustomAllAuthPasswordResetForm


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user object."""

    class Meta:
        model = get_user_model()
        fields = ["id", "email", "password", "name", "google_id"]
        extra_kwargs = {
            "password": {"write_only": True, "min_length": 8},
            "id": {"read_only": True},
            "google_id": {"read_only": True},  # Google ID should only be set internally
        }

    def create(self, validated_data):
        """Create a user with encrypted password and return the user."""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update a user and return it."""
        password = validated_data.pop("password", None)
        # Ensure google_id is not updated externally
        validated_data.pop("google_id", None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user


class CustomRegisterSerializer(RegisterSerializer):
    """Custom serializer for user registration."""

    username = None  # Remove username field
    name = serializers.CharField(max_length=255, required=False)

    def validate_email(self, email):
        """
        Override the regular validate_email method to ensure that not-verified emails
        won't be duplicated.
        """
        email = get_adapter().clean_email(email)
        if email and EmailAddress.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                _("A user is already registered with this e-mail address."),
            )
        return email

    def custom_signup(self, request, user):
        super().custom_signup(request, user)
        user.name = self.data.get("name", "")
        user.save()


class CustomLoginSerializer(LoginSerializer):
    username = None  # Remove username field


class CustomPasswordResetSerializer(PasswordResetSerializer):
    """Customise password resets emails in dj-rest-auth & allauth"""

    @property
    def password_reset_form_class(self):
        return CustomAllAuthPasswordResetForm


class EmailCheckSerializer(serializers.Serializer):
    """Serializer for checking if an email exists."""

    email = serializers.EmailField(required=True, help_text="Email address to check")


class EmailExistsResponseSerializer(serializers.Serializer):
    """Serializer for email exists response."""

    exists = serializers.BooleanField(
        help_text="Whether the email exists in the system"
    )


class ResendEmailVerificationSerializer(serializers.Serializer):
    """Serializer for resend email verification request."""

    email = serializers.EmailField(
        required=True, help_text="Email address to resend verification"
    )


class MessageResponseSerializer(serializers.Serializer):
    """Serializer for message responses."""

    message = serializers.CharField(help_text="Response message")


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer for error responses."""

    error = serializers.CharField(help_text="Error message")


class GoogleLoginSerializer(serializers.Serializer):
    """Serializer for Google login request."""

    google_id = serializers.CharField(required=True, help_text="Google user ID")
    email = serializers.EmailField(required=True, help_text="User's email address")
    name = serializers.CharField(
        required=False, allow_blank=True, help_text="User's full name"
    )
    picture = serializers.URLField(
        required=False, allow_blank=True, help_text="User's profile picture URL"
    )
    verified_email = serializers.BooleanField(
        required=False, default=True, help_text="Whether email is verified by Google"
    )


class GoogleUserSerializer(serializers.Serializer):
    """Serializer for user data in Google auth responses."""

    id = serializers.IntegerField(help_text="User ID")
    email = serializers.EmailField(help_text="User's email address")
    name = serializers.CharField(help_text="User's full name")
    google_id = serializers.CharField(help_text="Google user ID")


class GoogleAuthResponseSerializer(serializers.Serializer):
    """Serializer for Google authentication response."""

    access = serializers.CharField(help_text="JWT access token")
    refresh = serializers.CharField(help_text="JWT refresh token")
    user = GoogleUserSerializer(help_text="User information")
