"""
FastAPI main application entry point
"""

import logging
from contextlib import asynccontextmanager

from api.v1.router import api_router
from core.config import get_settings
from core.logging import setup_logging
from database import create_db_and_tables
from fastapi import FastAPI
from models import *


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    logger = logging.getLogger("faers-api")
    logger.info("FAERS API starting up...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    create_db_and_tables()
    yield
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
