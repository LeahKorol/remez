from django.db.models import QuerySet, F, Manager


class CaseAwareQuerySet(QuerySet):
    """
    A custom QuerySet that provides annotation for accessing related Case fields.
    """

    def with_faers_ids(self) -> QuerySet:
        """Annotate the queryset with 'primaryid' and 'caseid' fields from the related Case model."""
        return self.annotate(
            primaryid=F("case__faers_primaryid"),
            caseid=F("case__faers_caseid"),
        )


class CaseAwareManager(Manager):
    """
    Custom manager that always returns querysets with related Case IDs pre-annotated.

    This ensures that all queries from the model using this manager will have
    'primaryid' and 'caseid' fields available by default, without needing to explicitly call with_faers_ids().
    """

    def get_queryset(self) -> CaseAwareQuerySet:
        """Override the default queryset to always include annotated Case IDs."""

        return CaseAwareQuerySet(self.model, using=self._db).with_faers_ids()
