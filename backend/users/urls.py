from django.urls import path, include

from users.views import CustomRegisterView

urlpatterns = [
    path("", include("dj_rest_auth.urls"), name="rest-auth"),
    path("registration/", CustomRegisterView.as_view(), name="rest-register"),
]
