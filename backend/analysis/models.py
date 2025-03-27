from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q, CheckConstraint


class NameList(models.Model):
    """
    An abstract model for storing unique terms' names as drugs and reactions.

    Used to normalize names across related models by storing names once and
    using foreign key IDs elsewhere. This ensures consistency when querying or linking to NameList models.
    name = models.CharField(max_length=255, unique=True)
    """

    name = models.CharField(max_length=255, unique=True)

    class Meta:
        abstract = True  # This model won't create a table

    def __str__(self):
        return self.name


class DrugList(NameList):
    """Stores unique drug names extracted from FAERS data."""

    pass


class ReactionList(NameList):
    """Stores unique reaction names extracted from FAERS data."""

    pass


class Query(models.Model):
    """Represents a user's query with its parameters and results"""

    name = models.CharField(max_length=255, blank=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Input parameters
    drugs = models.ManyToManyField(DrugList)
    reactions = models.ManyToManyField(ReactionList)
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


# FAERS data models
# -----------------
# The following models are used to store the FAERS data in a more structured way.
# The original data is stored in CSV files, which are loaded into these models.


# Text choices classes for the models classes
# Source: https://pharmahub.org/app/site/resources/2018/01/00739/SafeRx_and_FAERS_Data_Interpretation.pdf
class AgeCode(models.TextChoices):
    DECADE = "DEC", "Decade"
    YEAR = "YR", "Year"
    MONTH = "MON", "Month"
    WEEK = "WK", "Week"
    DAY = "DY", "Day"
    HOUR = "HR", "Hour"


class Sex(models.TextChoices):
    UNKNOWN = "UNK", "Unknown"
    MALE = "M", "Male"
    FEMALE = "F", "Female"
    UNSPECIFIED = "U", "Unspecified"
    NOT_SPECIFIED = "NS", "Not Specified"


class WeightCode(models.TextChoices):
    KILOGRAM = "KG", "Kilograms"
    POUND = "LBS", "Pounds"
    GRAM = "GMS", "Grams"


class OutcomeCode(models.TextChoices):
    DEATH = "DE", "Death"
    LIFE_THREATENING = "LT", "Life-Threatening"
    HOSPITALIZATION = "HO", "Hospitalization - Initial or Prolonged"
    DISABILITY = "DS", "Disability"
    CONGENITAL_ANOMALY = "CA", "Congenital Anomaly"
    REQUIRED_INTERVENTION = (
        "RI",
        "Required Intervention to Prevent Permanent Impairment/Damage",
    )
    OTHER_SERIOUS = "OT", "Other Serious (Important Medical Event)"


# Models classes
class Case(models.Model):
    """
    Represents a case from the FAERS data. All related models below link to this one via foreign keys.
    This replaces the 'primaryid'-based linking used in the original FAERS data.
    """

    faers_primaryid = models.BigIntegerField(unique=True)
    faers_caseid = models.BigIntegerField()
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


class Demo(models.Model):
    """Stores data extracted from the FAERS demo CSV files (e.g., demo{year}q{quarter})."""

    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    event_dt_num = models.CharField(max_length=10, null=True)

    age = models.IntegerField(
        null=True, validators=[MinValueValidator(0), MaxValueValidator(130)]
    )
    age_cod = models.CharField(max_length=5, null=True, choices=AgeCode.choices)
    sex = models.CharField(max_length=5, null=True, choices=Sex.choices)
    wt = models.FloatField(
        null=True, validators=[MinValueValidator(0), MaxValueValidator(1000)]
    )
    wt_cod = models.CharField(max_length=5, null=True, choices=WeightCode.choices)

    def __str__(self):
        return f"Demo: {self.case_id}"


class Drug(models.Model):
    """Stores data extracted from the FAERS drug CSV files (e.g., drug{year}q{quarter})."""

    case = models.ForeignKey(Case, on_delete=models.CASCADE)  # An indexed field
    # An indexed field. Deleting the Drug will raise a ProtectedError
    drug = models.ForeignKey(DrugList, on_delete=models.PROTECT)

    def __str__(self):
        return f"Case: {self.case_id}, Drug: {self.drug_id}"


class Outcome(models.Model):
    """Stores data extracted from the FAERS outcome CSV files (e.g., outc{year}q{quarter})."""

    case = models.ForeignKey(Case, on_delete=models.CASCADE)  # An indexed field
    outc_cod = models.CharField(max_length=5, null=True, choices=OutcomeCode.choices)

    def __str__(self):
        return f"Case: {self.case_id}, Outcome: {self.get_outc_cod_display()}"


class Reaction(models.Model):
    """Stores data extracted from the FAERS reaction CSV files (e.g., reaction{year}q{quarter})."""

    case = models.ForeignKey(Case, on_delete=models.CASCADE)  # An indexed field
    # An indexed field. Deleting the Reaction will raise a ProtectedError
    reaction = models.ForeignKey(ReactionList, on_delete=models.PROTECT)

    def __str__(self):
        return f"Case: {self.case_id}, Reaction: {self.reaction_id}"
