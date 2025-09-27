import logging

from allauth.account.models import EmailAddress
from dj_rest_auth.jwt_auth import set_jwt_cookies
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)
User = get_user_model()


def get_tokens_for_user(user):
    """Generate JWT tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


@api_view(["POST"])
@permission_classes([AllowAny])
def google_login(request):
    """
    Handle Google login for existing users.
    """
    try:
        data = request.data
        google_id = data.get("google_id")
        email = data.get("email")
        name = data.get("name")
        picture = data.get("picture")
        verified_email = data.get("verified_email")

        # Validate required fields
        if not google_id or not email:
            return Response(
                {"error": "Google ID and email are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Try to find user by google_id first, then by email
        user = None

        # Check if user exists with this Google ID
        try:
            user = User.objects.get(google_id=google_id)
        except User.DoesNotExist:
            # Check if user exists with this email (for existing users who want to link Google)
            try:
                user = User.objects.get(email=email)
                # Link the Google account to existing user
                user.google_id = google_id
                if not user.name and name:
                    user.name = name
                user.save()
                logger.info(f"Linked Google account to existing user: {email}")
            except User.DoesNotExist:
                # User doesn't exist
                return Response(
                    {"error": "User not found. Please register first."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # Generate tokens
        tokens = get_tokens_for_user(user)

        # Prepare response
        response_data = {
            "access": tokens["access"],
            "refresh": tokens["refresh"],
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "google_id": user.google_id,
            },
        }

        response = Response(response_data, status=status.HTTP_200_OK)

        # Set JWT cookies if configured
        use_jwt = getattr(settings, "REST_AUTH", {}).get("USE_JWT", False)
        if use_jwt:
            set_jwt_cookies(response, tokens["access"], tokens["refresh"])

        logger.info(f"Google login successful for user: {email}")
        return response

    except Exception as e:
        logger.error(f"Google login error: {str(e)}")
        return Response(
            {"error": "Login failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def google_register(request):
    """
    Handle Google registration for new users.
    """
    try:
        data = request.data
        google_id = data.get("google_id")
        email = data.get("email")
        name = data.get("name", "")
        picture = data.get("picture")
        verified_email = data.get("verified_email")

        # Validate required fields
        if not google_id or not email:
            return Response(
                {"error": "Google ID and email are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "User with this email already exists. Please login instead."},
                status=status.HTTP_409_CONFLICT,
            )

        if User.objects.filter(google_id=google_id).exists():
            return Response(
                {"error": "Google account already registered. Please login instead."},
                status=status.HTTP_409_CONFLICT,
            )

        # Create new user
        user = User.objects.create_user(
            email=email,
            name=name,
            google_id=google_id,
            # For Google users, we can set a random password or leave it unusable
            # since they'll always login through Google
        )

        # Mark email as verified if Google says it's verified
        # The email adress entry was created in create_user
        if verified_email:
            EmailAddress.objects.filter(user=user, email=email).update(verified=True)

        # Generate tokens
        tokens = get_tokens_for_user(user)

        # Prepare response
        response_data = {
            "access": tokens["access"],
            "refresh": tokens["refresh"],
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "google_id": user.google_id,
            },
        }

        response = Response(response_data, status=status.HTTP_201_CREATED)

        # Set JWT cookies if configured
        use_jwt = getattr(settings, "REST_AUTH", {}).get("USE_JWT", False)
        if use_jwt:
            set_jwt_cookies(response, tokens["access"], tokens["refresh"])

        logger.info(f"Google registration successful for user: {email}")
        return response

    except Exception as e:
        logger.error(f"Google registration error: {str(e)}")
        return Response(
            {"error": "Registration failed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
