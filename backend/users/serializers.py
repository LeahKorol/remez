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

    username = None
    email = serializers.EmailField(required=True)
    name = serializers.CharField(max_length=255, required=False)

    # override function to check for duplicate emails even if they are not verified
    def validate_email(self, email):
        email = get_adapter().clean_email(email)
        if email and EmailAddress.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                _("A user is already registered with this e-mail address."),
            )
        return email

    @transaction.atomic
    def save(self, request):
        self.validate_email(self.data.get("email", ""))
        user = super().save(request)
        user.name = self.data.get("name")
        if user.name:
            user.save()
        return user
