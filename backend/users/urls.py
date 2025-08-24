from django.urls import path, include
from users.views import CustomRegisterView, password_reset_confirm_redirect
from users.google_auth import google_login, google_register
from dj_rest_auth.views import PasswordResetConfirmView, PasswordResetView


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

    path("google/login/", google_login, name="google_login"),
    path("google/register/", google_register, name="google_register"),
]
