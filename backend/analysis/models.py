from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q, CheckConstraint


class Drug(models.Model):
    name = models.CharField(max_length=255, unique=True)


class Reaction(models.Model):
    name = models.CharField(max_length=255, unique=True)


class Query(models.Model):
    """Represents a user's query with its parameters and results"""

    name = models.CharField(max_length=255, blank=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Input parameters
    drugs = models.ManyToManyField(Drug)
    reactions = models.ManyToManyField(Reaction)
    # TO-DO: DO NOT hard code the values
    quarter_start = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(49)]
    )
    quarter_end = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(50)]
    )

    # Result parameters:
    x_values = models.JSONField(default=list)
    y_values = models.JSONField(default=list)

    class Meta:
        ordering = ["-updated_at"]

        constraints = [
            CheckConstraint(
                check=Q(quarter_start__lte=models.F("quarter_end")),
                name="quarter_start_lte_quarter_end",
            )
        ]

    def __str__(self):
        return self.name if self.name else f"Query #{self.id}"


class Case(models.Model):
    """Represents a case from the Faers data"""

    faers_primary_id = models.BigIntegerField(unique=True)
    # An indexed field. Deleting the Drug will raise a ProtectedError
    drug = models.ForeignKey(Drug, on_delete=models.PROTECT)
    year = models.IntegerField(
        validators=[MinValueValidator(2000), MaxValueValidator(2030)]
    )
    quarter = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )

    class Meta:
        ordering = ["year", "quarter"]

    def __str__(self):
        return f"Case: {self.faers_primary_id}"


class CaseReaction(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE)  # An indexed field
    # An indexed field. Deleting the Reaction will raise a ProtectedError
    reaction = models.ForeignKey(Reaction, on_delete=models.PROTECT)

    def __str__(self):
        return f"Case: {self.case.id}, Reaction: {self.reaction.id}"
