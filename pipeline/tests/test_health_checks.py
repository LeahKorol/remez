"""Tests for health check endpoints."""

from pathlib import Path

import pytest
from core.health_checks import (
    check_directory_exists,
    check_directory_writable,
    is_config_loaded,
    is_http_client_ready,
)


class MockSettings:
    """Mock settings class for testing."""

    def __init__(self, environment=None, data_path=None):
        self.ENVIRONMENT = environment
        self._data_path = data_path

    def get_external_data_path(self):
        return self._data_path


@pytest.fixture
def valid_settings():
    """Fixture providing valid settings."""
    return MockSettings(environment="production", data_path=Path("/data"))


@pytest.fixture
def invalid_settings():
    """Fixture providing invalid settings."""
    return MockSettings(environment=None, data_path=Path("/data"))


class TestConfigLoadedCheck:
    """Test config_loaded check."""

    def test_config_loaded_when_valid(self, valid_settings):
        """Test config check passes with valid settings."""
        result = is_config_loaded(valid_settings)
        assert result is True

    def test_config_loaded_when_missing_environment(self, invalid_settings):
        """Test config check fails when environment is missing."""
        result = is_config_loaded(invalid_settings)
        assert result is False


class TestExternalDataDirExistsCheck:
    """Test external_data_dir_exists check."""

    def test_directory_exists_when_present(self, tmp_path):
        """Test directory check passes when directory exists."""
        result = check_directory_exists(tmp_path)
        assert result is True

    def test_directory_exists_when_missing(self, tmp_path):
        """Test directory check fails when directory doesn't exist."""
        non_existent = tmp_path / "does_not_exist"
        result = check_directory_exists(non_existent)
        assert result is False


class TestOutputDirWritableCheck:
    """Test output_dir_writable check."""

    def test_directory_writable_when_has_permissions(self, tmp_path):
        """Test writability check passes when directory is writable."""
        result = check_directory_writable(tmp_path)
        assert result is True

        # Verify cleanup - no test files left behind
        test_files = list(tmp_path.glob(".healthcheck_*.tmp"))
        assert len(test_files) == 0


@pytest.mark.asyncio
class TestHttpClientReadyCheck:
    """Test http_client_ready check."""

    async def test_http_client_ready_when_initialized(self, mocker):
        """Test HTTP client check passes when client is initialized."""

        # Create a mock that succeeds
        mock_get_or_create = mocker.patch(
            "core.http_client.http_client.get_or_create", return_value=True
        )

        result = await is_http_client_ready()

        # Verify the result and that the mock was used exactly once
        assert result is True
        mock_get_or_create.assert_called_once()

    async def test_http_client_ready_when_not_initialized(self, mocker):
        """Test HTTP client check fails when client not initialized."""
        # Store the mock object when creating it to verify it was called
        mock_get_or_create = mocker.patch(
            "core.http_client.http_client.get_or_create",
            side_effect=RuntimeError("Not Initialised"),
        )
        result = await is_http_client_ready()
        assert result is False
        mock_get_or_create.assert_called_once()
