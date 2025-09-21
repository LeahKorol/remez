"""
Main API router combining all route modules
"""

from api.v1.routes.health import router as health_router
from api.v1.routes.pipeline import router as pipeline_router
from fastapi import APIRouter

api_router = APIRouter()

# Include route modules
api_router.include_router(pipeline_router, prefix="/pipeline", tags=["pipeline"])

api_router.include_router(health_router, tags=["health"])
