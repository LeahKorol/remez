from django.urls import path, include

urlpatterns = [
    path("", include("dj_rest_auth.urls"), name="rest-auth"),
    path("registartion/", include("dj_rest_auth.registration.urls")),
]
