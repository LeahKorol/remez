"""
FastAPI main application entry point
"""

from contextlib import asynccontextmanager
import logging

from api.v1.router import api_router
from core.config import get_settings
from core.logging import setup_logging
from core.http_client import http_client
from database import create_db_and_tables
from fastapi import FastAPI
from models import *


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    settings = get_settings()
    logger = setup_logging(settings.LOG_LEVEL)
    faers_logger = logging.getLogger("FAERS")
    logger.info("FAERS API starting up...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    q_min, q_max = settings.get_faers_quarter_bounds()
    faers_logger.info(f"FAERS quarter bounds set to {q_min}..{q_max}")
    create_db_and_tables()
    await http_client.get_or_create()
    yield
    await http_client.stop()
    logger.info("FAERS API shutting down...")


def create_application() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()

    app = FastAPI(
        title="FAERS Analysis Pipeline API",
        description="API for running and managing FAERS data analysis pipelines",
        version="1.0.0",
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
