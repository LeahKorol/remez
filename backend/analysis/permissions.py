import logging

from django.conf import settings
from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)


class IsPipelineService(BasePermission):
    """
    Permission class to check if request is from the authorized pipeline service IP.
    """

    def has_permission(self, request, view):
        """
        Check if the request IP matches the PIPELINE_SERVICE_IP environment variable.
        """
        pipeline_service_ips = getattr(settings, "PIPELINE_SERVICE_IPS", None)

        if not pipeline_service_ips:
            logger.warning(
                "PIPELINE_SERVICE_IPS not configured. Allowing all requests."
            )
            return True

        client_ip = self.get_client_ip(request)
        return client_ip in pipeline_service_ips

    def get_client_ip(self, request):
        """
        Extract client IP address from request.
        Handles proxy headers like X-Forwarded-For.
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            # Get the first IP in the chain (client's real IP)
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
