"""
Configuration management for the FAERS Pipeline API
"""

import json
import logging
import os
from functools import lru_cache

from pydantic import BaseSettings

logger = logging.getLogger("faers-api")


class Settings(BaseSettings):
    """Application settings"""

    api_title: str = "FAERS Analysis Pipeline API"
    api_description: str = "API for running and managing FAERS data analysis pipelines"
    api_version: str = "1.0.0"

    # Pipeline settings (loaded from JSON config)
    pipeline_version: str = "1.0.0"
    external_dir: str = "data/external/faers"
    output_dir: str = "pipeline_output"
    threads: int = 7
    clean_on_failure: bool = True

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


def load_pipeline_config():
    """Load pipeline configuration from JSON file"""
    pipeline_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    config_path = os.path.join(pipeline_dir, "config", "pipeline_config.json")

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        logger.info(f"Loaded configuration from {config_path}")
        return config
    except Exception as e:
        logger.warning(f"Failed to load config from {config_path}: {str(e)}")
        # Return default config
        return {
            "pipeline": {"version": "1.0.0"},
            "data": {
                "external_dir": "data/external/faers",
                "output_dir": "pipeline_output",
            },
            "processing": {"threads": 7, "clean_on_failure": True},
        }


# Load config on startup
PIPELINE_CONFIG = load_pipeline_config()
