import logging

from django.apps import AppConfig

from analysis.constants import FAERS_QUARTER_RANGE_END, FAERS_QUARTER_RANGE_START


class AnalysisConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "analysis"

    def ready(self) -> None:
        logger = logging.getLogger("FAERS")
        logger.info(
            "FAERS quarter bounds set to %s..%s",
            FAERS_QUARTER_RANGE_START,
            FAERS_QUARTER_RANGE_END,
        )
