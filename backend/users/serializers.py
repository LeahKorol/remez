"""
Serializers for user-related functionality.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from django.db import transaction

# For overriding validate_email
from allauth.account.models import EmailAddress
from django.utils.translation import gettext_lazy as _
from allauth.account.adapter import get_adapter


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user object."""

    class Meta:
        model = get_user_model()
        fields = ["email", "password", "name"]
        extra_kwargs = {"password": {"write_only": True, "min_length": 8}}


class CustomRegisterSerializer(RegisterSerializer):
    """Custom serializer for user registration."""

    username = None  # Remove username field
    email = serializers.EmailField(required=True)
    name = serializers.CharField(max_length=255, required=False)
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

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

    # Define transaction.atomic to rollback the save operation in case of error
    @transaction.atomic
    def save(self, request):
        user = super().save(request)
        user.name = self.data.get("name", "")
        user.save()
        return user
