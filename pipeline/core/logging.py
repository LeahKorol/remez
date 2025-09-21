"""
Logging configuration
"""

import logging
import sys
from pathlib import Path


def setup_logging(log_level: str = "INFO") -> None:
    """Setup application logging configuration"""

    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s",
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
