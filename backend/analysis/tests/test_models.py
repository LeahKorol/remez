from django.test import TestCase
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.db import transaction
from django.contrib.auth import get_user_model
from analysis.models import DrugList, ReactionList, Query, Case, Drug, Reaction
from django.utils import timezone
import time


class NameListTests(TestCase):
    def create_and_assert(self, model, name, expected_error=None):
        """
        Helper method to create a model instance and test uniqueness.

        :param model: The model class (e.g., Drug, Reaction), inheriting from NameList.
        :param name: The name of the object to create.
        :param expected_error: If not None, expects an error.
        """
        if expected_error:
            with self.assertRaises(expected_error):
                with transaction.atomic():
                    model.objects.create(name=name)
        else:
            instance = model.objects.create(name=name)
            self.assertEqual(instance.name, name)

    def test_create_objects(self):
        """Test creating both Drug and Reaction objects."""
        for model, name in [(DrugList, "drug"), (ReactionList, "reaction")]:
            self.create_and_assert(model, name)

    def test_name_field_is_unique(self):
        """Test that the name field enforces uniqueness for both models."""
        for model, name in [
            (DrugList, "duplicate_drug"),
            (ReactionList, "duplicate_reaction"),
        ]:
            self.create_and_assert(model, name)  # First creation should succeed
            self.create_and_assert(model, name, IntegrityError)  # Second should fail

    def test_name_field_is_255_long(self):
        """Test that name field enforces max length of 255 characters"""
        for model in [DrugList, ReactionList]:
            obj = model(name="l" * 256)
            with self.assertRaises(ValidationError):  # Database will enforce max_length
                obj.full_clean()


class QueryTests(TestCase):
    def setUp(self):
        self.drug = DrugList.objects.create(name="drug")
        self.reaction = ReactionList.objects.create(name="reaction")

        email = "testanalysis@example.com"
        password = "t1234567"
        self.user = get_user_model().objects.create_user(email=email, password=password)

    def test_create_valid_query(self):
        """Ensure valid queries can be created."""
        before_creation = timezone.now()

        q_start, q_end = 0, 2
        query = Query.objects.create(
            user=self.user, quarter_start=q_start, quarter_end=q_end
        )

        after_creation = timezone.now()

        self.assertTrue(before_creation <= query.created_at <= after_creation)
        self.assertTrue(before_creation <= query.updated_at <= after_creation)

        self.assertEqual(query.user, self.user)
        self.assertEqual(query.quarter_start, q_start)
        self.assertEqual(query.quarter_end, q_end)

    def test_drugs_and_reactions_m2m_with_query(self):
        """Test adding drugs and reactions to a query"""
        query = Query.objects.create(user=self.user, quarter_start=0, quarter_end=2)
        query.drugs.add(self.drug)
        query.reactions.add(self.reaction)

        self.assertIn(self.drug, query.drugs.all())
        self.assertIn(self.reaction, query.reactions.all())

    def test_query_empty_name(self):
        """Test string representation when name is empty"""
        query = Query.objects.create(user=self.user, quarter_start=0, quarter_end=2)
        self.assertEqual(str(query), f"Query #{query.id}")

    def test_queries_order_by_update_time(self):
        """Ensure queries are ordered by updated_at"""
        query1 = Query.objects.create(user=self.user, quarter_start=0, quarter_end=2)
        time.sleep(0.1)  # Ensure timestamp difference
        query2 = Query.objects.create(user=self.user, quarter_start=0, quarter_end=2)

        queries = Query.objects.order_by("-updated_at")
        self.assertEqual(query2, queries[0])  # Newest should be first
        self.assertEqual(query1, queries[1])

    def test_updated_at_changes_on_update(self):
        """Ensure updated_at field changes when the object is updated"""
        query = Query.objects.create(user=self.user, quarter_start=0, quarter_end=2)
        old_updated_at = query.updated_at

        time.sleep(0.1)  # Ensure timestamp difference
        query.quarter_end = 3
        query.save()

        query.refresh_from_db()
        self.assertGreater(query.updated_at, old_updated_at)

    def test_quarter_start_greater_than_end(self):
        """Ensure IntegrityError is raised when quarter_start > quarter_end"""
        query = Query(user=self.user, quarter_start=3, quarter_end=2)
        with self.assertRaises(ValidationError):
            query.full_clean()

    def test_quarter_range_validation(self):
        """Ensure quarter_start cannot be less than 0"""
        query = Query(user=self.user, quarter_start=-1, quarter_end=2)
        with self.assertRaises(ValidationError):
            query.full_clean()


class CaseTests(TestCase):
    def setUp(self):
        self.faers_primary_id = 1111
        self.year = 2013
        self.quarter = 1

    def test_creation_with_valid_data(self):
        """Should successfully create a Case with valid data."""
        case = Case.objects.create(
            faers_primary_id=self.faers_primary_id,
            year=self.year,
            quarter=self.quarter,
        )
        self.assertEqual(case.faers_primary_id, self.faers_primary_id)
        self.assertEqual(case.year, self.year)
        self.assertEqual(case.quarter, self.quarter)

    def test_duplicate_faers_primary_id(self):
        """Should raise ValidationError when creating a Case with a duplicate faers_primary_id."""
        Case.objects.create(faers_primary_id=2222, year=self.year, quarter=self.quarter)
        duplicate_case = Case(
            faers_primary_id=2222, year=self.year, quarter=self.quarter
        )
        with self.assertRaises(ValidationError):
            duplicate_case.full_clean()

    def test_year_too_large(self):
        """Should raise ValidationError when year is greater than 2030."""
        case = Case(
            faers_primary_id=self.faers_primary_id, year=2031, quarter=self.quarter
        )
        with self.assertRaises(ValidationError):
            case.full_clean()

    def test_year_too_small(self):
        """Should raise ValidationError when year is less than 2000."""
        case = Case(
            faers_primary_id=self.faers_primary_id, year=1999, quarter=self.quarter
        )
        with self.assertRaises(ValidationError):
            case.full_clean()

    def test_quarter_too_large(self):
        """Should raise ValidationError when quarter is greater than 4."""
        case = Case(faers_primary_id=self.faers_primary_id, year=self.year, quarter=5)
        with self.assertRaises(ValidationError):
            case.full_clean()

    def test_quarter_too_small(self):
        """Should raise ValidationError when quarter is less than 1."""
        case = Case(faers_primary_id=self.faers_primary_id, year=self.year, quarter=0)
        with self.assertRaises(ValidationError):
            case.full_clean()

    def test_cases_are_ordered_by_year_and_quarter(self):
        """Cases should be ordered by year, then quarter (ascending)."""
        Case.objects.create(faers_primary_id=1, year=2022, quarter=3)
        Case.objects.create(faers_primary_id=2, year=2021, quarter=2)
        Case.objects.create(faers_primary_id=3, year=2021, quarter=1)
        Case.objects.create(faers_primary_id=4, year=2022, quarter=1)

        cases = list(Case.objects.all())
        ordered_ids = [case.faers_primary_id for case in cases]
        expected_order = [3, 2, 4, 1]

        self.assertEqual(ordered_ids, expected_order)


class DrugTests(TestCase):
    def setUp(self):
        self.drug = DrugList.objects.create(name="drug")
        self.case = Case.objects.create(faers_primary_id=1111, year=2013, quarter=1)

    def test_create_case_drug(self):
        """Should successfully link a Case to a Drug via CaseDrug."""
        casedrug = Drug.objects.create(case=self.case, drug=self.drug)
        self.assertEqual(casedrug.case, self.case)
        self.assertEqual(casedrug.drug, self.drug)

    def test_drug_has_multiple_cases(self):
        """A Drug should be able to access all related CaseDrug instances via the reverse relationship."""
        case2 = Case.objects.create(faers_primary_id=2222, year=2014, quarter=2)

        Drug.objects.create(case=self.case, drug=self.drug)
        Drug.objects.create(case=case2, drug=self.drug)

        related_cases = [cd.case for cd in self.drug.drug_set.all()]

        self.assertIn(self.case, related_cases)
        self.assertIn(case2, related_cases)
        self.assertEqual(len(related_cases), 2)

    def test_protect_on_drug_delete(self):
        """Deleting a Drug with existing CaseDrug references should raise IntegrityError."""
        Drug.objects.create(case=self.case, drug=self.drug)
        with self.assertRaises(IntegrityError):
            self.drug.delete()


class ReactionTests(TestCase):

    def setUp(self):
        self.case = Case.objects.create(
            faers_primary_id="3333",
            year=2013,
            quarter=1,
        )
        self.reaction = ReactionList.objects.create(name="Test Reaction")

    def test_create_case_reaction(self):
        case_reaction = Reaction.objects.create(
            case=self.case,
            reaction=self.reaction,
        )
        self.assertEqual(case_reaction.case, self.case)
        self.assertEqual(case_reaction.reaction, self.reaction)

    def test_str_representation(self):
        case_reaction = Reaction.objects.create(
            case=self.case,
            reaction=self.reaction,
        )
        expected_str = f"Case: {self.case.id}, Reaction: {self.reaction.id}"
        self.assertEqual(str(case_reaction), expected_str)

    def test_cascade_on_case_delete(self):
        case_reaction = Reaction.objects.create(
            case=self.case,
            reaction=self.reaction,
        )
        self.case.delete()
        self.assertFalse(Reaction.objects.filter(id=case_reaction.id).exists())

    def test_protect_on_reaction_delete(self):
        Reaction.objects.create(
            case=self.case,
            reaction=self.reaction,
        )
        with self.assertRaises(IntegrityError):
            self.reaction.delete()
