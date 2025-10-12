from django.contrib.auth import get_user_model
from django.core.validators import (
    MaxLengthValidator,
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models
from django.db.models import CheckConstraint, Q

from analysis.constants import YEAR_END, YEAR_START

# Use TextField and not CharField as recommended in Postgres documentation (copy the url, not click):
# https://wiki.postgresql.org/wiki/Don't_Do_This#Don.27t_use_varchar.28n.29_by_default


class TermName(models.Model):
    """
    An abstract model for storing unique terms' names as drugs and reactions.

    Used to normalize names across related models by storing names once and
    using foreign key IDs elsewhere. This ensures consistency when querying or linking to TermName models.
    name = models.TextField(unique=True, validators=[MaxLengthValidator(255)])
    """

    name = models.TextField(unique=True, validators=[MaxLengthValidator(255)])

    class Meta:
        abstract = True  # This model won't create a table

    def __str__(self):
        return self.name


class DrugName(TermName):
    """Stores unique drug names extracted from FAERS data."""

    pass


class ReactionName(TermName):
    """Stores unique reaction names extracted from FAERS data."""

    pass


class Query(models.Model):
    """Represents a user's query with its parameters and results"""

    name = models.TextField(blank=True, validators=[MaxLengthValidator(255)])
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Input parameters
    drugs = models.ManyToManyField(DrugName)
    reactions = models.ManyToManyField(ReactionName)

    # Quarter parameters
    quarter_start = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    quarter_end = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    year_start = models.IntegerField(
        validators=[MinValueValidator(YEAR_START), MaxValueValidator(YEAR_END)]
    )
    year_end = models.IntegerField(
        validators=[MinValueValidator(YEAR_START), MaxValueValidator(YEAR_END)]
    )

    class Meta:
        ordering = ["-updated_at"]

        constraints = [
            CheckConstraint(
                condition=Q(year_start__lte=models.F("year_end")),
                name="year_start_lte_year_end",
            )
        ]

    def __str__(self):
        return self.name if self.name else f"Query #{self.id}"


# status chiches are same as the pipeline sevice uses
class ResultStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    RUNNING = "running", "Running"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class Result(models.Model):
    """Stores the results of a query for a specific drug-reaction pair"""

    query = models.OneToOneField(
        Query,
        on_delete=models.CASCADE,  # delete Result if Query is deleted
        related_name="result",  # access: query.result
    )
    # The status of running the query in the pipeline
    status = models.TextField(
        choices=ResultStatus.choices, default=ResultStatus.PENDING
    )

    # Result parameters - ROR values, lower and upper confidence intervals
    ror_values = models.JSONField(default=list)
    ror_lower = models.JSONField(default=list)
    ror_upper = models.JSONField(default=list)

    def __str__(self):
        return f"Result #{self.id} for Query #{self.query.id}"


# Note: Pipeline-related models (Case, Demo, Drug, Outcome, Reaction) have been removed
# as pipeline logic now runs in an external service. Only Query/Result models remain
# for the Django API, along with DrugName/ReactionName models for search functionality.
