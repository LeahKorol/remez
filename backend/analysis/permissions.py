import ipaddress
import logging

from django.conf import settings
from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)


class IsPipelineService(BasePermission):
    """
    Permission class to check if request is from the authorized pipeline service IP.
    """

    message = "Forbidden: request is not allowed from this source."

    def has_permission(self, request, view):
        """
        Check if the request IP matches the configured pipeline service whitelist.
        """
        pipeline_service_ips = getattr(settings, "PIPELINE_SERVICE_IPS", None)
        client_ip = self.get_client_ip(request)
        endpoint = self.get_endpoint_name(request, view)

        if pipeline_service_ips in (None, ""):
            if settings.DEBUG:
                logger.warning(
                    "Allowing pipeline callback with empty whitelist in DEBUG mode.",
                    extra={
                        "client_ip": client_ip,
                        "endpoint": endpoint,
                        "rejection_reason": "debug_empty_whitelist_override",
                    },
                )
                return True
            self.log_denied_request(
                client_ip,
                endpoint,
                "missing_pipeline_service_ips",
            )
            return False

        if isinstance(pipeline_service_ips, str):
            self.log_denied_request(
                client_ip,
                endpoint,
                "invalid_pipeline_service_ips_type",
            )
            return False

        if not isinstance(pipeline_service_ips, (list, tuple)):
            self.log_denied_request(
                client_ip,
                endpoint,
                "unsupported_pipeline_service_ips_container",
            )
            return False

        normalized_rules = self.normalize_rules(pipeline_service_ips)

        if not normalized_rules:
            if settings.DEBUG:
                logger.warning(
                    "Allowing pipeline callback with empty whitelist in DEBUG mode.",
                    extra={
                        "client_ip": client_ip,
                        "endpoint": endpoint,
                        "rejection_reason": "debug_empty_whitelist_override",
                    },
                )
                return True
            self.log_denied_request(
                client_ip,
                endpoint,
                "empty_pipeline_service_ips",
            )
            return False

        if not client_ip:
            self.log_denied_request(client_ip, endpoint, "missing_client_ip")
            return False

        if any(self.ip_matches_rule(client_ip, allowed_ip) for allowed_ip in normalized_rules):
            logger.info(
                "Allowed pipeline callback request.",
                extra={
                    "client_ip": client_ip,
                    "endpoint": endpoint,
                    "rejection_reason": "",
                },
            )
            return True

        self.log_denied_request(client_ip, endpoint, "client_ip_not_whitelisted")
        return False

    def get_client_ip(self, request):
        """
        Extract client IP address from request.
        """
        return request.META.get("REMOTE_ADDR")

    def get_endpoint_name(self, request, view):
        if view and hasattr(view, "action") and view.action:
            return view.action

        resolver_match = getattr(request, "resolver_match", None)
        if resolver_match and resolver_match.view_name:
            return resolver_match.view_name

        return getattr(request, "path", "unknown")

    def normalize_rules(self, pipeline_service_ips):
        return [rule.strip() for rule in pipeline_service_ips if isinstance(rule, str) and rule.strip()]

    def ip_matches_rule(self, client_ip, allowed_value):
        if not client_ip or not allowed_value:
            return False

        try:
            return ipaddress.ip_address(client_ip) in ipaddress.ip_network(
                allowed_value, strict=False
            )
        except ValueError:
            return False

    def log_denied_request(self, client_ip, endpoint, reason):
        logger.warning(
            "Denied pipeline callback request.",
            extra={
                "client_ip": client_ip,
                "endpoint": endpoint,
                "rejection_reason": reason,
            },
        )
