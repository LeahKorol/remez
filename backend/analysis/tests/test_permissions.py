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
        """Test permission is approved when no IP is configured"""
        settings.PIPELINE_SERVICE_IPS = []
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

    def test_permission_with_x_forwarded_for(self, settings, permission, mock_request):
        """Test permission uses X-Forwarded-For when available (proxy scenario)"""
        settings.PIPELINE_SERVICE_IPS = ["192.168.1.100"]
        request = mock_request(HTTP_X_FORWARDED_FOR="192.168.1.100, 10.0.0.1")

        assert permission.has_permission(request, None) is True

    def test_permission_x_forwarded_for_with_spaces(
        self, settings, permission, mock_request
    ):
        """Test permission handles X-Forwarded-For with various spacing"""
        settings.PIPELINE_SERVICE_IPS = ["192.168.1.100"]
        # Test with extra spaces
        request = mock_request(HTTP_X_FORWARDED_FOR="192.168.1.100 ,  10.0.0.1")

        assert permission.has_permission(request, None) is True
