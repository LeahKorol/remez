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
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Logging settings
    LOG_LEVEL: str = "INFO"

    # Pipeline settings
    PIPELINE_THREADS: int = 7
    PIPELINE_CLEAN_ON_FAILURE: bool = True

    # Data directories
    DATA_EXTERNAL_DIR: str = "data/external/faers"
    DATA_OUTPUT_DIR: str = "pipeline_output"
    CONFIG_DIR: str = "config"

    # Database settings
    SQLITE_FILE_NAME: str = "database.sqlite3"
    DATABASE_URL: str = f"sqlite:///{SQLITE_FILE_NAME}"

    # File paths
    BASE_DIR: Path = Path(__file__).parent.parent

    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_external_data_path(self) -> Path:
        """Get the full path to external data directory"""
        return self.BASE_DIR / self.DATA_EXTERNAL_DIR

    def get_output_path(self) -> Path:
        """Get the full path to pipeline output directory"""
        return self.BASE_DIR / self.DATA_OUTPUT_DIR

    def get_config_path(self) -> Path:
        """Get the full path to config directory"""
        return self.BASE_DIR / self.CONFIG_DIR


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
