"""
Configuration management with environment variables and defaults
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


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
    PIPELINE_CALLBACK_URL: str = (
        "http://localhost:8000/api/v1/analysis/results/update-by-task"
    )

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


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
