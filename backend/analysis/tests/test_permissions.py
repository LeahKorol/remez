from types import SimpleNamespace

import pytest
from rest_framework.test import APIClient

from analysis.permissions import IsPipelineService


@pytest.fixture
def api_client():
    """Fixture for API client"""
    return APIClient()


class TestIsPipelineServicePermission:
    """Test cases for IsPipelineService permission class"""

    @pytest.fixture
    def permission(self):
        """Fixture for permission instance"""
        return IsPipelineService()

    @pytest.fixture
    def mock_request(self, api_client):
        """Fixture for creating mock requests"""

        def _create_request(**kwargs):
            return api_client.get("/", **kwargs).wsgi_request

        return _create_request

    def test_permission_granted_for_allowed_ip(
        self, settings, permission, mock_request
    ):
        """Test permission is granted for allowed IP"""
        settings.PIPELINE_SERVICE_IPS = ["192.168.1.100"]
        request = mock_request(REMOTE_ADDR="192.168.1.100")

        assert permission.has_permission(request, None) is True

    def test_permission_denied_for_disallowed_ip(
        self, settings, permission, mock_request
    ):
        """Test permission is denied for disallowed IP"""
        settings.PIPELINE_SERVICE_IPS = ["192.168.1.100"]
        request = mock_request(REMOTE_ADDR="10.0.0.1")

        assert permission.has_permission(request, None) is False

    def test_permission_denied_when_no_ip_configured(
        self, settings, permission, mock_request
    ):
        """Test permission is denied when no IP is configured in production"""
        settings.PIPELINE_SERVICE_IPS = []
        settings.DEBUG = False
        request = mock_request(REMOTE_ADDR="192.168.1.100")

        assert permission.has_permission(request, None) is False

    def test_permission_granted_when_no_ip_configured_in_debug(
        self, settings, permission, mock_request
    ):
        """Test permission is allowed in DEBUG mode when no IP is configured"""
        settings.PIPELINE_SERVICE_IPS = []
        settings.DEBUG = True
        request = mock_request(REMOTE_ADDR="192.168.1.100")

        assert permission.has_permission(request, None) is True

    @pytest.mark.parametrize(
        "test_ip, expected_result",
        [
            ("192.168.1.100", True),
            ("10.0.0.50", True),
            ("10.0.0.50", True),
            ("1.1.1.1", False),
        ],
    )
    def test_permission_multiple_ips(
        self, settings, permission, mock_request, test_ip, expected_result
    ):
        """Test permission works with multiple whitelisted IPs"""
        settings.PIPELINE_SERVICE_IPS = [
            "192.168.1.100",
            "10.0.0.50",
            "172.16.0.1",
        ]
        # All whitelisted IPs should pass
        assert (
            permission.has_permission(mock_request(REMOTE_ADDR=test_ip), None)
            is expected_result
        )

    def test_permission_granted_for_cidr_range(
        self, settings, permission, mock_request
    ):
        """Test permission accepts CIDR ranges in the whitelist."""
        settings.PIPELINE_SERVICE_IPS = ["172.21.0.0/16"]
        request = mock_request(REMOTE_ADDR="172.21.0.5")

        assert permission.has_permission(request, None) is True

    def test_permission_denied_for_raw_string_configuration(
        self, settings, permission, mock_request
    ):
        """Raw string whitelist values are rejected to avoid unsafe iteration semantics."""
        settings.PIPELINE_SERVICE_IPS = "192.168.1.100"
        settings.DEBUG = False
        request = mock_request(REMOTE_ADDR="192.168.1.100")

        assert permission.has_permission(request, None) is False

    def test_permission_ignores_x_forwarded_for_header(
        self, settings, permission, mock_request
    ):
        """Permission trusts REMOTE_ADDR and does not allow spoofed X-Forwarded-For."""
        settings.PIPELINE_SERVICE_IPS = ["192.168.1.100"]
        request = mock_request(
            REMOTE_ADDR="10.0.0.1",
            HTTP_X_FORWARDED_FOR="192.168.1.100, 10.0.0.1",
        )

        assert permission.has_permission(request, None) is False

    def test_permission_logs_denied_request_reason(
        self, settings, permission, mock_request, caplog
    ):
        """Denied requests are explicitly logged with endpoint, client IP, and reason."""
        settings.PIPELINE_SERVICE_IPS = []
        settings.DEBUG = False
        request = mock_request(REMOTE_ADDR="10.0.0.1")
        view = SimpleNamespace(action="update_by_task_id")

        with caplog.at_level("WARNING"):
            allowed = permission.has_permission(request, view)

        assert allowed is False
        assert any("Denied pipeline callback request." in message for message in caplog.messages)
        record = next(
            record for record in caplog.records if record.message == "Denied pipeline callback request."
        )
        assert record.client_ip == "10.0.0.1"
        assert record.endpoint == "update_by_task_id"
        assert record.rejection_reason == "empty_pipeline_service_ips"
