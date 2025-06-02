from django.urls import path, include

from users.views import CustomRegisterView
from dj_rest_auth.views import PasswordResetConfirmView, PasswordResetView
from users.views import password_reset_confirm_redirect

urlpatterns = [
    path("", include("dj_rest_auth.urls"), name="rest-auth"),
    path("registration/", CustomRegisterView.as_view(), name="rest-register"),
    path("password/reset/", PasswordResetView.as_view(), name="rest-password_reset"),
    path(
        "reset-password/<str:uidb64>/<str:token>/",
        password_reset_confirm_redirect,
        name="password_reset_confirm",
    ),
    path(
        "password/reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
]
