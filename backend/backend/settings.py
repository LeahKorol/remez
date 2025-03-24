"""
Django settings for backend project.

Generated by 'django-admin startproject' using Django 5.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta
import os

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # DRF
    "rest_framework",
    # Auth
    "django.contrib.sites",
    "rest_framework.authtoken",
    "dj_rest_auth",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "dj_rest_auth.registration",
    # API documentation
    "drf_spectacular",
    # Enable CORS
    "corsheaders",
    # Project apps
    "users",
    "analysis",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # Enable CORS, Must be placed at the top
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",  # Third-party
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Jerusalem"  # Show dates in Israeli local time

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Project-spesific settings

# Custom user model
AUTH_USER_MODEL = "users.User"

SITE_ID = 1

# django-allauth configurations so that dj-rest-auth uses email / password authentication
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = "none"  # Do not require email confirmation
ACCOUNT_USER_MODEL_USERNAME_FIELD = None

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "dj_rest_auth.jwt_auth.JWTCookieAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

REST_AUTH = {
    # Custom serializers
    "USER_DETAILS_SERIALIZER": "users.serializers.UserSerializer",
    "REGISTER_SERIALIZER": "users.serializers.CustomRegisterSerializer",
    "LOGIN_SERIALIZER": "users.serializers.CustomLoginSerializer",
    # Do not need session authentication because we use JWT cookies
    "SESSION_LOGIN": False,
    # JWT configuration
    "USE_JWT": True,
    # Cookies names
    "JWT_AUTH_COOKIE": os.getenv("JWT_AUTH_COOKIE", "jwt-access"),
    "JWT_AUTH_REFRESH_COOKIE": os.getenv("JWT_AUTH_REFRESH_COOKIE", "jwt-refresh"),
    # If set to True, the cookie will only be sent over HTTPS connections
    "JWT_AUTH_SECURE": os.getenv("JWT_AUTH_SECURE", "False") == "True",
    # If set to True, refresh token will not be sent in the response body
    "JWT_AUTH_HTTPONLY": os.getenv("JWT_AUTH_HTTPONLY", "False") == "True",
    "JWT_AUTH_SAMESITE": "Lax",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        hours=int(os.getenv("ACCESS_TOKEN_LIFETIME_HOURS", 1))
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=int(os.getenv("REFRESH_TOKEN_LIFETIME_DAYS", 7))
    ),
}

# SECURITY WARNING: keep the JWT signing key used in production secret!
SIGNING_KEY = os.getenv("SIGNING_KEY")

# CORS settings
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
CORS_ALLOW_CREDENTIALS = True  # Allow using cookies for authentication
