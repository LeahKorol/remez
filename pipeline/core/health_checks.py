"""
Health check utilities.

Provides reusable functions to verify system readiness and component health.
"""

import logging
from enum import Enum
from pathlib import Path
from typing import Dict

from core.http_client import http_client

logger = logging.getLogger(__name__)


class HealthCheck(str, Enum):
    """Health check component identifiers."""

    CONFIG_LOADED = "config_loaded"
    EXTERNAL_DATA_DIR_EXISTS = "external_data_dir_exists"
    OUTPUT_DIR_WRITABLE = "output_dir_writable"
    HTTP_CLIENT_READY = "http_client_ready"


def is_config_loaded(settings) -> bool:
    try:
        # Check essential attributes exist
        has_environment = bool(settings.ENVIRONMENT)
        has_data_path = callable(getattr(settings, "get_external_data_path", None))

        return has_environment and has_data_path

    except AttributeError as e:
        logger.error(f"Missing required config attribute: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected config validation error: {e}", exc_info=True)
        return False


def check_directory_exists(path: Path) -> bool:
    try:
        if not path.exists():
            logger.warning(f"{path} does not exist: {path}")
            return False

        if not path.is_dir():
            logger.warning(f"{path} exists but is not a directory: {path}")
            return False

        return True

    except Exception as e:
        logger.error(f"Failed to check {path}: {e}", exc_info=True)
        return False


def check_directory_writable(path: Path) -> bool:
    """
    Verify directory is writable by creating and deleting a test file.
    """
    try:
        # First check directory exists
        if not check_directory_exists(path):
            return False

        # Create unique test file to avoid conflicts in concurrent checks
        test_file = path / f".healthcheck_{id(path)}.tmp"

        try:
            # Attempt write
            test_file.write_text("healthcheck", encoding="utf-8")

            # Verify file was created
            if not test_file.exists():
                logger.error(f"{path} write test file not created: {path}")
                return False

            # Clean up
            test_file.unlink()
            return True

        except PermissionError:
            logger.error(f"{path} is not writable (permission denied): {path}")
            return False
        except OSError as e:
            logger.error(f"{path} write test failed: {e}")
            return False

    except Exception as e:
        logger.error(
            f"Unexpected error checking {path} writability: {e}",
            exc_info=True,
        )
        return False


async def is_http_client_ready() -> bool:
    """
    Verify HTTP client is initialized and ready to use.
    """
    try:
        # Use global instance
        await http_client.get_or_create()
        return True

    except RuntimeError as e:
        logger.warning(f"HTTP client not initialized: {e}")
        return False
    except ImportError as e:
        logger.error(f"Failed to import HTTP client: {e}")
        return False
    except Exception as e:
        logger.error(f"HTTP client health check failed: {e}", exc_info=True)
        return False


async def perform_readiness_checks(settings) -> Dict[str, bool]:
    """
    Perform all readiness checks for the application.

    Args:
        settings: Application settings object

    Returns:
        Dictionary mapping check names to their boolean results
    """
    checks = {}

    # Check 1: Configuration loaded
    checks[HealthCheck.CONFIG_LOADED] = is_config_loaded(settings)

    # Check 2: External data directory exists
    if checks[HealthCheck.CONFIG_LOADED]:
        try:
            external_data_path = settings.get_external_data_path()
            checks[HealthCheck.EXTERNAL_DATA_DIR_EXISTS] = check_directory_exists(
                external_data_path
            )
        except Exception as e:
            logger.error(f"Failed to get external data path: {e}")
            checks[HealthCheck.EXTERNAL_DATA_DIR_EXISTS] = False
    else:
        checks[HealthCheck.EXTERNAL_DATA_DIR_EXISTS] = False

    # Check 3: Output directory writable
    try:
        output_dir = Path(getattr(settings, "OUTPUT_DIR", "."))
        checks[HealthCheck.OUTPUT_DIR_WRITABLE] = check_directory_writable(output_dir)
    except Exception as e:
        logger.error(f"Failed to check output directory: {e}")
        checks[HealthCheck.OUTPUT_DIR_WRITABLE] = False

    # Check 4: HTTP client ready
    checks[HealthCheck.HTTP_CLIENT_READY] = await is_http_client_ready()

    return checks
