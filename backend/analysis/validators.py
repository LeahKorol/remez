from django.conf import settings
from django.core.exceptions import ValidationError


def validate_configured_quarter_range(value):
    """Validate that a quarter value is within the configured FAERS range."""
    min_quarter = settings.FAERS_QUARTER_MIN
    max_quarter = settings.FAERS_QUARTER_MAX

    if value < min_quarter or value > max_quarter:
        raise ValidationError(
            f"Quarter must be between {min_quarter} and {max_quarter}."
        )
