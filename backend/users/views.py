from dj_rest_auth.registration.views import RegisterView
from dj_rest_auth.jwt_auth import set_jwt_cookies
from django.conf import settings
from django.http import HttpResponseRedirect
import logging

logger = logging.getLogger(__name__)


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


def password_reset_confirm_redirect(request, uidb64, token):
    logger.info(
        f"Password reset confirm redirect called with uidb64: {uidb64} and token: {token}"
    )
    return HttpResponseRedirect(
        f"{settings.PASSWORD_RESET_CONFIRM_REDIRECT_BASE_URL}{uidb64}/{token}/"
    )
