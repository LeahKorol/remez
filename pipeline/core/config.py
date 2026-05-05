"""
Configuration management with environment variables and defaults
"""

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        extra="ignore",
    )

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
    FAERS_QUARTER_MIN: int = 1
    FAERS_QUARTER_MAX: int = 4

    # Data directories
    DATA_EXTERNAL_DIR: str = "data/external/faers"
    DATA_OUTPUT_DIR: str = "pipeline_output"
    LOGS_DIR: str = "logs"

    # Database settings
    SQLITE_FILE_NAME: str = "database.sqlite3"
    DATABASE_URL: str = f"sqlite:///{SQLITE_FILE_NAME}"

    # File paths
    BASE_DIR: Path = Path(__file__).parent.parent

    @model_validator(mode="after")
    def validate_quarter_range(self):
        if not 1 <= self.FAERS_QUARTER_MIN <= self.FAERS_QUARTER_MAX <= 4:
            raise ValueError(
                "Invalid FAERS quarter configuration. "
                "Expected 1 <= FAERS_QUARTER_MIN <= FAERS_QUARTER_MAX <= 4."
            )
        return self

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_flag(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
                return False
        return value

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
