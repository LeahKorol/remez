from django.test import TestCase
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.db import transaction
from django.contrib.auth import get_user_model
from analysis.models import Drug, Reaction, Query
from django.utils import timezone
import time


class DrugReactionTests(TestCase):
    def create_and_assert(self, model, name, expected_error=None):
        """
        Helper method to create a model instance and test uniqueness.

        :param model: The model class (e.g., Drug, Reaction).
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
        for model, name in [(Drug, "drug"), (Reaction, "reaction")]:
            self.create_and_assert(model, name)

    def test_name_field_is_unique(self):
        """Test that the name field enforces uniqueness for both models."""
        for model, name in [(Drug, "duplicate_drug"), (Reaction, "duplicate_reaction")]:
            self.create_and_assert(model, name)  # First creation should succeed
            self.create_and_assert(model, name, IntegrityError)  # Second should fail

    def test_name_field_is_255_long(self):
        """Test that name field enforces max length of 255 characters"""
        for model in [Drug, Reaction]:
            obj = model(name="l" * 256)
            with self.assertRaises(ValidationError):  # Database will enforce max_length
                obj.full_clean()


class QueryTests(TestCase):
    def setUp(self):
        self.drug = Drug.objects.create(name="drug")
        self.reaction = Reaction.objects.create(name="reaction")

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
