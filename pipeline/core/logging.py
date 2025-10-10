"""
Logging configuration
"""

import logging
import sys
from pathlib import Path

from core.config import get_settings

settings = get_settings()


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup application logging configuration"""

    # Create logs directory if it doesn't exist
    logs_dir: Path = settings.get_logs_dir()
    logs_dir.mkdir(exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",  # no milliseconds
        handlers=[
            # Console handler
            logging.StreamHandler(sys.stdout),
            # File handler
            logging.FileHandler(logs_dir / "faers-api.log"),
        ],
    )

    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    # Create application logger
    logger = logging.getLogger("faers-api")
    logger.setLevel(getattr(logging, log_level.upper()))

    return logger
