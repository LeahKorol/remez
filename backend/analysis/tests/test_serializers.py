from django.test import TestCase
from django.contrib.auth import get_user_model
from analysis.models import Query, DrugName, ReactionName
from analysis.serializers import (
    QuerySerializer,
    DrugNameSerializer,
    ReactionNameSerializer,
)
import pytest


class QuerySerializerTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        cls.user = get_user_model().objects.create_user(
            email="testuser@example.com", password="password123"
        )
        cls.drug1 = DrugName.objects.create(name="Drug A")
        cls.drug2 = DrugName.objects.create(name="Drug B")
        cls.reaction1 = ReactionName.objects.create(name="Reaction X")
        cls.reaction2 = ReactionName.objects.create(name="Reaction Y")

        cls.query = Query.objects.create(
            user=cls.user,
            name="Test Query",
            quarter_start=1,
            quarter_end=2,
            year_start=2020,
            year_end=2020,
        )
        cls.query.drugs.set([cls.drug1.id])
        cls.query.reactions.set([cls.reaction1.id])

    def test_serialization(self):
        """Test that serialization produces expected data"""
        serializer = QuerySerializer(instance=self.query)
        # Remove fields that change dynamically
        response_data = serializer.data.copy()
        response_data.pop("created_at", None)
        response_data.pop("updated_at", None)

        expected_data = {
            "id": self.query.id,
            "drugs": [self.drug1.id],  # ManyToManyField should return a list of IDs
            "reactions": [self.reaction1.id],
            "name": self.query.name,
            "user": self.query.user.id,  # ForeignKey should be serialized as ID
            "quarter_start": self.query.quarter_start,
            "quarter_end": self.query.quarter_end,
            "year_start": self.query.year_start,
            "year_end": self.query.year_end,
            "x_values": self.query.x_values,
            "y_values": self.query.y_values,
        }
        self.assertEqual(response_data, expected_data)

    def test_missing_drugs_fails(self):
        """Test validation fails if drugs are missing"""
        data = {
            "name": "New Query",
            "quarter_start": 1,
            "quarter_end": 2,
            "year_start": 2020,
            "year_end": 2020,
            "reactions": [self.reaction1.id],  # No drugs
        }
        serializer = QuerySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("drugs", serializer.errors)

    def test_missing_reactions_fails(self):
        """Test validation fails if reactions are missing"""
        data = {
            "name": "New Query",
            "quarter_start": 1,
            "quarter_end": 2,
            "year_start": 2020,
            "year_end": 2020,
            "drugs": [self.drug1.id],  # No reactions
        }
        serializer = QuerySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("reactions", serializer.errors)

    def test_create_query(self):
        """Test successful creation of a Query"""
        data = {
            "name": "Created Query",
            "quarter_start": 1,
            "quarter_end": 2,
            "year_start": 2020,
            "year_end": 2020,
            "drugs": [self.drug1.id, self.drug2.id],
            "reactions": [self.reaction1.id, self.reaction2.id],
        }
        serializer = QuerySerializer(data=data)
        self.assertTrue(serializer.is_valid())

        query = serializer.save(
            user=self.user
        )  # Manually assign user since it's read-only
        self.assertEqual(query.name, "Created Query")
        self.assertEqual(query.quarter_start, 1)
        self.assertEqual(query.quarter_end, 2)
        self.assertEqual(list(query.drugs.all()), [self.drug1, self.drug2])
        # Model instances with primary key value are hashable by default
        self.assertEqual(set(query.reactions.all()), {self.reaction1, self.reaction2})

    def test_update_query(self):
        """Test successful update of a Query"""
        data = {
            "name": "Updated Query",
            "quarter_start": 3,
            "quarter_end": 4,
            "year_start": 2020,
            "year_end": 2020,
            "drugs": [self.drug2.id],  # Change drugs
            "reactions": [self.reaction2.id],  # Change reactions
        }
        serializer = QuerySerializer(instance=self.query, data=data, partial=True)
        self.assertTrue(serializer.is_valid())

        updated_query = serializer.save()
        self.assertEqual(updated_query.name, "Updated Query")
        self.assertEqual(updated_query.quarter_start, 3)
        self.assertEqual(updated_query.quarter_end, 4)
        self.assertEqual(list(updated_query.drugs.all()), [self.drug2])
        self.assertEqual(list(updated_query.reactions.all()), [self.reaction2])

    def test_read_only_fields_cannot_be_updated(self):
        """Test that read-only fields cannot be updated"""
        data = {
            "id": 9999,  # Trying to modify ID
            "user": self.user.id,  # Trying to modify user
            "created_at": "2022-01-01T00:00:00Z",  # Trying to modify created_at
            "updated_at": "2022-01-01T00:00:00Z",
        }
        serializer = QuerySerializer(instance=self.query, data=data, partial=True)
        self.assertTrue(serializer.is_valid())

        updated_query = serializer.save()
        self.assertNotEqual(updated_query.id, 9999)  # ID should not change
        self.assertEqual(updated_query.user, self.user)  # User should remain unchanged
        self.assertNotEqual(
            updated_query.created_at.isoformat(), "2022-01-01T00:00:00Z"
        )  # Created_at should remain unchanged

    def test_partial_update_keeps_existing_relations(self):
        """Test that partial update does not remove ManyToMany fields if not provided"""
        data = {"name": "Partially Updated Query"}  # No drugs or reactions provided
        serializer = QuerySerializer(instance=self.query, data=data, partial=True)
        self.assertTrue(serializer.is_valid())

        updated_query = serializer.save()
        self.assertEqual(updated_query.name, "Partially Updated Query")
        self.assertEqual(
            list(updated_query.drugs.all()), [self.drug1]
        )  # Should remain unchanged
        self.assertEqual(
            list(updated_query.reactions.all()), [self.reaction1]
        )  # Should remain unchanged

    def test_partial_update_with_null_relations(self):
        """Test that explicitly setting drugs or reactions to an empty list fails"""
        data = {"drugs": [], "reactions": []}  # Explicitly removing relations
        serializer = QuerySerializer(instance=self.query, data=data, partial=True)
        self.assertFalse(serializer.is_valid())


@pytest.fixture
def term_instances(request):
    """Fixture to create test instances for each model"""
    model_class = request.param[0]
    instance1 = model_class.objects.create(name="Test 1")
    instance2 = model_class.objects.create(name="Test 2")
    return {
        "model_class": model_class,
        "serializer_class": request.param[1],
        "instance1": instance1,
        "instance2": instance2,
    }


@pytest.mark.parametrize(
    "term_instances",
    [
        (DrugName, DrugNameSerializer),
        (ReactionName, ReactionNameSerializer),
    ],
    indirect=True,
)
@pytest.mark.django_db
class TestTermNameModelSerializer:
    """Test TermName model serializers"""

    def test_serialization(self, term_instances):
        """Test that serialization produces expected data"""
        serializer = term_instances["serializer_class"](
            instance=term_instances["instance1"]
        )
        expected_data = {
            "id": term_instances["instance1"].id,
            "name": term_instances["instance1"].name,
        }
        assert serializer.data == expected_data

    def test_read_only_fields(self, term_instances):
        """Test that read-only fields cannot be updated"""
        data = {"id": 9999, "name": "new name"}
        serializer = term_instances["serializer_class"](
            instance=term_instances["instance1"], data=data, partial=True
        )
        assert serializer.is_valid()
        serializer.save()
        # term fields should remain unchanged
        assert term_instances["instance1"].id != 9999
        assert term_instances["instance1"].name != "new name"
