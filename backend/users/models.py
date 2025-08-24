from django.conf import settings
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


class UserManager(BaseUserManager):
    """Custom BaseUserManager for the app users."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password, **extra_fields):
        # user = self.create_user(email, password)
        # user.is_staff = True
        # user.is_superuser = True
        # user.save(using=self._db)

        # return user
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """The app custom user model."""

    # The email field must be unique since we use it as the unique
    # identifier (see below USERNAME_FIELD)
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    google_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        help_text="Google account ID for OAuth2 authentication.",
    )

    objects = UserManager()

    # We use the email field as the unique identifier
    USERNAME_FIELD = "email"
    # username = None  # Disable the username field
    REQUIRED_FIELDS = []

    
    def __str__(self):
        return self.email
