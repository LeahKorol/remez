"""
Configuration management with environment variables and defaults
"""

import logging
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings
from utils import Quarter

logger = logging.getLogger("FAERS")


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    HOST: str = "127.0.0.1"
    PORT: int = 8001

    # Logging settings
    LOG_LEVEL: str = "INFO"

    # Pipeline settings
    PIPELINE_THREADS: int = 7
    PIPELINE_CLEAN_INTERNAL_DIRS: bool = True
    PIPELINE_MAX_WORKERS: int = 20
    PIPELINE_MAX_RESULTS: int = 100
    PIPELINE_MIN_RESULT_RETENTION_MINUTES: int = 30
    PIPELINE_CALLBACK_URL: str = (
        "http://localhost:8000/api/v1/analysis/results/update-by-task"
    )

    # FAERS data bounds
    FAERS_FROM: str
    FAERS_TO: str

    # Data directories
    DATA_EXTERNAL_DIR: str = "data/external/faers"
    DATA_OUTPUT_DIR: str = "pipeline_output"
    LOGS_DIR: str = "logs"

    # Database settings
    SQLITE_FILE_NAME: str = "database.sqlite3"
    DATABASE_URL: str = f"sqlite:///{SQLITE_FILE_NAME}"

    # File paths
    BASE_DIR: Path = Path(__file__).parent.parent

    class Config:
        env_file = ".env"

    def get_external_data_path(self) -> Path:
        """Get the full path to external data directory"""
        return self.BASE_DIR / self.DATA_EXTERNAL_DIR

    def get_output_path(self) -> Path:
        """Get the full path to pipeline output directory"""
        return self.BASE_DIR / self.DATA_OUTPUT_DIR

    def get_logs_dir(self) -> Path:
        """Get the full path to logs directory"""
        return self.BASE_DIR / self.LOGS_DIR

    def get_faers_quarter_bounds(self) -> tuple[Quarter, Quarter]:
        """Return FAERS quarter bounds derived from env vars."""

        try:
            q_from = Quarter(self.FAERS_FROM)
            q_to = Quarter(self.FAERS_TO)
        except RuntimeError as err:
            logger.error(
                f"Invalid FAERS_FROM/FAERS_TO format ({self.FAERS_FROM}..{self.FAERS_TO}): {err}."
            )
            raise RuntimeError("Invalid FAERS_FROM/FAERS_TO format") from err

        if (q_to.year, q_to.quarter) < (q_from.year, q_from.quarter):
            logger.error(
                f"FAERS_FROM must be <= FAERS_TO ({self.FAERS_FROM}..{self.FAERS_TO})."
            )
            raise RuntimeError("FAERS_FROM must be <= FAERS_TO")

        return q_from, q_to


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
