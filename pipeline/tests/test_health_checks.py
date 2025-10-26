"""Tests for health check endpoints."""

from pathlib import Path

import pytest
from core.health_checks import (
    HealthCheck,
    check_directory_exists,
    check_directory_writable,
    is_config_loaded,
    is_http_client_ready,
    perform_readiness_checks,
)


class MockSettings:
    def __init__(self, environment=None, data_path=None):
        self.ENVIRONMENT = environment
        self._data_path = data_path

    def get_external_data_path(self):
        return self._data_path


@pytest.fixture
def valid_settings():
    return MockSettings(environment="production", data_path=Path("/data"))


@pytest.fixture
def invalid_settings():
    return MockSettings(environment=None, data_path=Path("/data"))


class TestConfigLoadedCheck:
    def test_config_loaded_when_valid(self, valid_settings):
        result = is_config_loaded(valid_settings)
        assert result is True

    def test_config_loaded_when_missing_environment(self, invalid_settings):
        result = is_config_loaded(invalid_settings)
        assert result is False


class TestExternalDataDirExistsCheck:
    def test_directory_exists_when_present(self, tmp_path):
        result = check_directory_exists(tmp_path)
        assert result is True

    def test_directory_exists_when_missing(self, tmp_path):
        non_existent = tmp_path / "does_not_exist"
        result = check_directory_exists(non_existent)
        assert result is False


class TestOutputDirWritableCheck:
    def test_directory_writable_when_has_permissions(self, tmp_path):
        result = check_directory_writable(tmp_path)
        assert result is True

        test_files = list(tmp_path.glob(".healthcheck_*.tmp"))
        assert len(test_files) == 0


@pytest.mark.asyncio
class TestHttpClientReadyCheck:
    async def test_http_client_ready_when_initialized(self, mocker):
        mock_get_or_create = mocker.patch(
            "core.http_client.http_client.get_or_create", return_value=True
        )

        result = await is_http_client_ready()

        assert result is True
        mock_get_or_create.assert_called_once()

    async def test_http_client_ready_when_not_initialized(self, mocker):
        mock_get_or_create = mocker.patch(
            "core.http_client.http_client.get_or_create",
            side_effect=RuntimeError("Not Initialised"),
        )
        result = await is_http_client_ready()
        assert result is False
        mock_get_or_create.assert_called_once()


@pytest.mark.asyncio
class TestPerformReadinessChecks:
    """Test perform_readiness_checks function."""

    async def test_perform_readiness_checks_all_pass(self, mocker, tmp_path):
        mock_settings = mocker.MagicMock()
        mock_settings.ENVIRONMENT = "test"
        mock_settings.get_external_data_path.return_value = tmp_path
        mock_settings.OUTPUT_DIR = str(tmp_path)

        mocker.patch("core.health_checks.is_http_client_ready", return_value=True)

        result = await perform_readiness_checks(mock_settings)

        assert len(result) == 4
        assert result[HealthCheck.CONFIG_LOADED] is True
        assert result[HealthCheck.EXTERNAL_DATA_DIR_EXISTS] is True
        assert result[HealthCheck.OUTPUT_DIR_WRITABLE] is True
        assert result[HealthCheck.HTTP_CLIENT_READY] is True

    async def test_perform_readiness_checks_config_fails(self, mocker, tmp_path):
        mock_settings = mocker.MagicMock()
        mock_settings.ENVIRONMENT = None

        mocker.patch("core.health_checks.is_http_client_ready", return_value=True)

        result = await perform_readiness_checks(mock_settings)

        assert result[HealthCheck.CONFIG_LOADED] is False
        assert result[HealthCheck.EXTERNAL_DATA_DIR_EXISTS] is False

    async def test_perform_readiness_checks_external_data_dir_missing(
        self, mocker, tmp_path
    ):
        mock_settings = mocker.MagicMock()
        mock_settings.ENVIRONMENT = "test"
        mock_settings.get_external_data_path.return_value = tmp_path / "nonexistent"
        mock_settings.OUTPUT_DIR = str(tmp_path)

        mocker.patch("core.health_checks.is_http_client_ready", return_value=True)

        result = await perform_readiness_checks(mock_settings)

        assert result[HealthCheck.CONFIG_LOADED] is True
        assert result[HealthCheck.EXTERNAL_DATA_DIR_EXISTS] is False
        assert result[HealthCheck.OUTPUT_DIR_WRITABLE] is True
        assert result[HealthCheck.HTTP_CLIENT_READY] is True

    async def test_perform_readiness_checks_http_client_fails(self, mocker, tmp_path):
        mock_settings = mocker.MagicMock()
        mock_settings.ENVIRONMENT = "test"
        mock_settings.get_external_data_path.return_value = tmp_path
        mock_settings.OUTPUT_DIR = str(tmp_path)

        mocker.patch("core.health_checks.is_http_client_ready", return_value=False)

        result = await perform_readiness_checks(mock_settings)

        assert result[HealthCheck.CONFIG_LOADED] is True
        assert result[HealthCheck.EXTERNAL_DATA_DIR_EXISTS] is True
        assert result[HealthCheck.OUTPUT_DIR_WRITABLE] is True
        assert result[HealthCheck.HTTP_CLIENT_READY] is False

    async def test_perform_readiness_checks_external_data_path_exception(
        self, mocker, tmp_path
    ):
        mock_settings = mocker.MagicMock()
        mock_settings.ENVIRONMENT = "test"
        mock_settings.get_external_data_path.side_effect = Exception("Path error")
        mock_settings.OUTPUT_DIR = str(tmp_path)

        mocker.patch("core.health_checks.is_http_client_ready", return_value=True)

        result = await perform_readiness_checks(mock_settings)

        assert result[HealthCheck.CONFIG_LOADED] is True
        assert result[HealthCheck.EXTERNAL_DATA_DIR_EXISTS] is False
        assert result[HealthCheck.OUTPUT_DIR_WRITABLE] is True
        assert result[HealthCheck.HTTP_CLIENT_READY] is True

    async def test_perform_readiness_checks_output_dir_exception(
        self, mocker, tmp_path
    ):
        mock_settings = mocker.MagicMock()
        mock_settings.ENVIRONMENT = "test"
        mock_settings.get_external_data_path.return_value = tmp_path

        mocker.patch("core.health_checks.is_http_client_ready", return_value=True)

        result = await perform_readiness_checks(mock_settings)

        assert result[HealthCheck.CONFIG_LOADED] is True
        assert result[HealthCheck.EXTERNAL_DATA_DIR_EXISTS] is True
        assert result[HealthCheck.OUTPUT_DIR_WRITABLE] is False
        assert result[HealthCheck.HTTP_CLIENT_READY] is True
