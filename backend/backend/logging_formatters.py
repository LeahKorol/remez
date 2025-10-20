"""Custom logging formatters for the backend project."""

import logging
import os

from django.conf import settings


class BaseRelativePathFormatter(logging.Formatter):
    """Base formatter that provides relative path functionality"""

    def _add_relative_path(self, record):
        """Add relative path to log record"""
        record.relpath = record.filename
        if hasattr(record, "pathname"):
            record.relpath = os.path.relpath(record.pathname, settings.BASE_DIR)
        return record


class ColoredRelativePathFormatter(BaseRelativePathFormatter):
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
        record = self._add_relative_path(record)

        # Add color
        level_color = self.COLORS.get(record.levelname, "")
        reset_color = self.COLORS["RESET"]
        colored_format = f"[%(asctime)s] {level_color}%(levelname)s{reset_color} (%(relpath)s:%(lineno)d): %(message)s"

        return logging.Formatter(colored_format, datefmt="%Y-%m-%d %H:%M:%S").format(
            record
        )


class RelativePathFormatter(BaseRelativePathFormatter):
    """File formatter that shows relative paths (no colors for file output)"""

    def format(self, record):
        record = self._add_relative_path(record)

        # Plain format without colors for file output
        plain_format = (
            "[%(asctime)s] %(levelname)s (%(relpath)s:%(lineno)d): %(message)s"
        )
        return logging.Formatter(plain_format, datefmt="%Y-%m-%d %H:%M:%S").format(
            record
        )
