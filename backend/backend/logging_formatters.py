"""Custom logging formatters for the backend project."""

import logging
import os
from pathlib import Path
from django.conf import settings


class ColoredRelativePathFormatter(logging.Formatter):
    """Colored formatter that shows relative paths"""

    # Color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[91m",  # Bold Red
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record):
        # Convert absolute path to relative path from project root
        if hasattr(record, "pathname"):
            try:
                record.relpath = os.path.relpath(record.pathname, settings.BASE_DIR)
            except ValueError:
                # If can't compute relative path, fall back to module name
                record.relpath = record.module
        else:
            record.relpath = record.module

        # Add color
        level_color = self.COLORS.get(record.levelname, "")
        reset_color = self.COLORS["RESET"]
        colored_format = f"[%(asctime)s] {level_color}%(levelname)s{reset_color} (%(relpath)s:%(lineno)d): %(message)s"

        return logging.Formatter(colored_format, datefmt="%Y-%m-%d %H:%M:%S").format(record)
