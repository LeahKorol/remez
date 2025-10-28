"""
Logging configuration
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
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
            # Rotating file handler (5MB per file, keep 3 backup files)
            RotatingFileHandler(
                logs_dir / "faers-api.log",
                maxBytes=5 * 1024 * 1024,  # 5 MB
                backupCount=3,
            ),
        ],
    )

    # Create application logger
    logger = logging.getLogger("faers-api")
    logger.setLevel(getattr(logging, log_level.upper()))

    return logger
