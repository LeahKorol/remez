"""Health check API routes."""

import logging
from datetime import datetime, timezone

from core.config import get_settings
from core.health_checks import perform_readiness_checks
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from models.schemas import HealthResponse, ReadinessResponse

logger = logging.getLogger("faers-api.health")
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Liveness check - is the process alive?"""
    settings = get_settings()

    return HealthResponse(
        api_version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
        environment=settings.ENVIRONMENT,
    )


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness_check() -> ReadinessResponse:
    """Readiness check - can the app serve requests?"""
    try:
        settings = get_settings()
        checks = await perform_readiness_checks(settings)
        all_ready = all(checks.values())

        if not all_ready:
            failed = [name for name, result in checks.items() if not result]
            logger.warning(f"Readiness check failed: {', '.join(failed)}")

        response = ReadinessResponse(
            checks=checks,
            timestamp=datetime.now(timezone.utc).isoformat(),
            error=None if all_ready else "One or more checks failed",
        )

    except Exception as e:
        logger.error(f"Readiness check error: {e}", exc_info=True)
        response = ReadinessResponse(
            checks={}, timestamp=datetime.now(timezone.utc).isoformat(), error=str(e)
        )

    status_code = (
        status.HTTP_200_OK if all_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return JSONResponse(content=response.model_dump(), status_code=status_code)
