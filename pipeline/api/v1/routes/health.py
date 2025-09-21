"""
Health check API routes
"""

import logging
from datetime import datetime

from core.config import get_settings
from fastapi import APIRouter
from models.schemas import HealthResponse

logger = logging.getLogger("faers-api.health")
router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of the API",
)
async def health_check():
    """Health check endpoint"""
    settings = get_settings()

    return HealthResponse(
        status="healthy",
        api_version="1.0.0",
        timestamp=datetime.utcnow().isoformat(),
        environment=settings.ENVIRONMENT,
    )


@router.get(
    "/health/ready",
    summary="Readiness check",
    description="Check if the API is ready to serve requests",
)
async def readiness_check():
    """Readiness check endpoint"""
    try:
        settings = get_settings()

        # Basic checks
        checks = {
            "config_loaded": True,
            "external_data_dir_exists": settings.get_external_data_path().exists(),
            "output_dir_writable": True,  # Could add actual write test
        }

        all_healthy = all(checks.values())

        return {
            "status": "ready" if all_healthy else "not_ready",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}", exc_info=True)
        return {
            "status": "not_ready",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
