"""
Custom exception classes for the pipeline module.
"""


class PipelineCapacityExceededError(Exception):
    """Raised when pipeline capacity is exceeded and no task slots can be reused."""
    pass


class DataFilesNotFoundError(Exception):
    """Raised when required FAERS data files are not found for the requested quarters"""

    def __init__(
        self,
        year_start: int,
        quarter_start: int,
        year_end: int,
        quarter_end: int,
        requested_quarters: list = None,
        available_quarters: list = None,
    ):
        self.requested_quarters = requested_quarters or []
        self.available_quarters = available_quarters or []

        # Build the error message with missing quarters
        year_q_from = f"{year_start}q{quarter_start}"
        year_q_to = f"{year_end}q{quarter_end}"

        missing_quarters = [
            q for q in self.requested_quarters if q not in self.available_quarters
        ]

        message = f"No complete data found for requested quarters {year_q_from} to {year_q_to}"

        if missing_quarters:
            message += f". Missing quarters: {', '.join(missing_quarters)}"

        if available_quarters:
            message += f". Available quarters: {', '.join(available_quarters)}"

        super().__init__(message)
