"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.views.generic import TemplateView

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

spectacular_settings = {
    'TITLE': 'My API',
    'DESCRIPTION': 'My API description',
    'VERSION': '1.0.0',
    'TAGS': [
        {'name': 'Analysis', 'description': 'Analysis related operations'},
    ],
}

# functions for custom error pages
def custom_page_not_found(request, exception):
    return render(request, "errors/404.html", status=404)

def custom_server_error(request):
    return render(request, "errors/500.html", status=500)


urlpatterns = [
    path("admin/", admin.site.urls),
    # DRF Schema and Documentation
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "api/v1/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
    path("api/v1/auth/", include("users.urls")),
    path("api/v1/analysis/", include("analysis.urls")),
    path("", TemplateView.as_view(template_name="index.html"), name="react-spa"),
]

handler404 = "backend.urls.custom_page_not_found"
handler500 = "backend.urls.custom_server_error"