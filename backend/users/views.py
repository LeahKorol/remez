import logging
import os

from allauth.account.models import (
    EmailConfirmation,
    EmailConfirmationHMAC,
)
from allauth.account.utils import send_email_confirmation
from dj_rest_auth.jwt_auth import set_jwt_cookies
from dj_rest_auth.registration.views import RegisterView
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from users.serializers import (
    CustomRegisterSerializer,
    EmailCheckSerializer,
    EmailExistsResponseSerializer,
    ErrorResponseSerializer,
    MessageResponseSerializer,
    ResendEmailVerificationSerializer,
)

logger = logging.getLogger(__name__)
User = get_user_model()


@extend_schema(
    request=ResendEmailVerificationSerializer,
    responses={
        200: MessageResponseSerializer,
        400: ErrorResponseSerializer,
        500: ErrorResponseSerializer,
    },
    description="Resend email verification for a user",
)
@api_view(["POST"])
def resend_email_verification(request):
    """
    Resend email verification for a user.
    """
    try:
        serializer = ResendEmailVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email, is_active=True)

            # Check if user is already verified
            if user.emailaddress_set.filter(verified=True, primary=True).exists():
                return Response(
                    {"message": "This email is already verified."},
                    status=status.HTTP_200_OK,
                )

            # Send new verification email
            send_email_confirmation(request, user, signup=False)

            logger.info(f"Verification email resent to {email}")
            return Response(
                {"message": "Verification email sent successfully."},
                status=status.HTTP_200_OK,
            )

        except User.DoesNotExist:
            # Don't reveal if user exists or not for security
            return Response(
                {
                    "message": "If this email exists in our system, a verification email has been sent."
                },
                status=status.HTTP_200_OK,
            )

    except Exception as e:
        logger.error(f"Error in resending verification email: {e}")
        return Response(
            {"error": "Failed to send verification email."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class CustomRegisterView(RegisterView):
    """
    Custom registration view that extends the default RegisterView.

    This view overrides the finalize_response method to set JWT cookies
    in the response if JWT authentication is enabled in the settings.

    Methods:
        finalize_response(request, response, *args, **kwargs):
            Finalizes the response by setting JWT cookies if applicable.

    Attributes:
        None
    """

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        use_jwt = getattr(settings, "REST_AUTH", {}).get("USE_JWT", False)

        if use_jwt:
            if (
                response.status_code == 201
                and "access" in response.data
                and "refresh" in response.data
            ):
                access_token = response.data["access"]
                refresh_token = response.data["refresh"]
                set_jwt_cookies(response, access_token, refresh_token)
        return response

    serializer_class = CustomRegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)

        # Send email verification
        try:
            send_email_confirmation(request, user, signup=True)
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")

        return Response(
            {
                "detail": "Verification e-mail sent. Please check your email and click the verification link to activate your account.",
                "user_id": user.pk,
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )

    def perform_create(self, serializer):
        return serializer.save(self.request)


def email_verify_redirect(request, key):
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    return redirect(f"{frontend_url}/email-verify-result?verified=true")


def password_reset_confirm_redirect(request, uidb64, token):
    logger.info(
        f"Password reset confirm redirect called with uidb64: {uidb64} and token: {token}"
    )
    return HttpResponseRedirect(
        f"{settings.PASSWORD_RESET_CONFIRM_REDIRECT_BASE_URL}{uidb64}/{token}/"
    )


def verify_email_api(request, key):
    logger.info(f"Verifying email with key: {key}")
    try:
        email_confirmation = EmailConfirmationHMAC.from_key(key)
        if not email_confirmation:
            email_confirmation = EmailConfirmation.objects.get(key=key)

        email_confirmation.confirm(request)
        # Redirect to frontend with success message
        logger.info(f"Email verified successfully for key: {key}")
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return redirect(f"{frontend_url}/login?verified=true")
    except Exception as e:
        logger.error(f"Email verification failed for key: {key} with error: {e}")
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return redirect(f"{frontend_url}/login?verified=false")


@extend_schema(
    request=EmailCheckSerializer,
    responses={200: EmailExistsResponseSerializer},
    description="Check if an email address exists in the system",
)
@api_view(["POST"])
@permission_classes([AllowAny])
def check_email_exists(request):
    serializer = EmailCheckSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data["email"].strip().lower()
    exists = User.objects.filter(email__iexact=email).exists()

    response_data = {"exists": exists}
    response_serializer = EmailExistsResponseSerializer(response_data)
    return Response(response_serializer.data, status=status.HTTP_200_OK)
