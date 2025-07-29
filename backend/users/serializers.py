"""
Serializers for user-related functionality.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer
from django.db import transaction

# For overriding validate_email
from allauth.account.models import EmailAddress
from django.utils.translation import gettext_lazy as _
from allauth.account.adapter import get_adapter


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user object."""

    class Meta:
        model = get_user_model()
        fields = ["id", "email", "password", "name"]
        extra_kwargs = {
            "password": {"write_only": True, "min_length": 8},
            "id": {"read_only": True},
        }

    def create(self, validated_data):
        """Create a user with encrypted password and return the user."""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update a user and return it."""
        password = validated_data.pop("password", None)
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
