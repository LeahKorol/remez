import pytest
from django.contrib.auth import get_user_model
from rest_framework import serializers

from analysis.models import DrugName, Query, ReactionName, Result, ResultStatus
from analysis.serializers import (
    DrugNameSerializer,
    QuerySerializer,
    ReactionNameSerializer,
)


@pytest.fixture
def query_test_data():
    """Set up test data"""
    user = get_user_model().objects.create_user(
        email="testuser@example.com", password="password123"
    )
    drug1 = DrugName.objects.create(name="Drug A")
    drug2 = DrugName.objects.create(name="Drug B")
    reaction1 = ReactionName.objects.create(name="Reaction X")
    reaction2 = ReactionName.objects.create(name="Reaction Y")

    query = Query.objects.create(
        user=user,
        name="Test Query",
        quarter_start=1,
        quarter_end=2,
        year_start=2020,
        year_end=2020,
    )
    query.drugs.set([drug1.id])
    query.reactions.set([reaction1.id])
    
    # Create the associated Result object
    result = Result.objects.create(
        query=query,
        status=ResultStatus.PENDING,
        ror_values=[],
        ror_lower=[],
        ror_upper=[]
    )

    return {
        "user": user,
        "drug1": drug1,
        "drug2": drug2,
        "reaction1": reaction1,
        "reaction2": reaction2,
        "query": query,
        "result": result,
    }


@pytest.mark.django_db
class TestQuerySerializer:
    def test_serialization(self, query_test_data):
        """Test that serialization produces expected data (drugs/reactions as id+name objects)"""
        query = query_test_data["query"]
        drug1 = query_test_data["drug1"]
        reaction1 = query_test_data["reaction1"]

        serializer = QuerySerializer(instance=query)
        # Remove fields that change dynamically
        response_data = serializer.data.copy()
        response_data.pop("created_at", None)
        response_data.pop("updated_at", None)

        expected_data = {
            "id": query.id,
            "drugs_details": [{"id": drug1.id, "name": drug1.name}],
            "reactions_details": [{"id": reaction1.id, "name": reaction1.name}],
            "name": query.name,
            "user": query.user.id,  # ForeignKey should be serialized as ID
            "quarter_start": query.quarter_start,
            "quarter_end": query.quarter_end,
            "year_start": query.year_start,
            "year_end": query.year_end,
            "result": {
                "id": query.result.id,
                "query": query.id,
                "status": query.result.status,
                "ror_values": query.result.ror_values,
                "ror_lower": query.result.ror_lower,
                "ror_upper": query.result.ror_upper,
            }
        }
        assert response_data == expected_data

    def test_missing_drugs_fails(self, query_test_data):
        """Test validation fails if drugs are missing"""
        reaction1 = query_test_data["reaction1"]
        data = {
            "name": "New Query",
            "quarter_start": 1,
            "quarter_end": 2,
            "year_start": 2020,
            "year_end": 2020,
            "reactions": [reaction1.id],  # No drugs
        }
        serializer = QuerySerializer(data=data)
        assert not serializer.is_valid()
        assert "drugs" in serializer.errors

    def test_missing_reactions_fails(self, query_test_data):
        """Test validation fails if reactions are missing"""
        drug1 = query_test_data["drug1"]
        data = {
            "name": "New Query",
            "quarter_start": 1,
            "quarter_end": 2,
            "year_start": 2020,
            "year_end": 2020,
            "drugs": [drug1.id],  # No reactions
        }
        serializer = QuerySerializer(data=data)
        assert not serializer.is_valid()
        assert "reactions" in serializer.errors

    def test_create_query(self, query_test_data):
        """Test successful creation of a Query and associated Result"""
        user = query_test_data["user"]
        drug1 = query_test_data["drug1"]
        drug2 = query_test_data["drug2"]
        reaction1 = query_test_data["reaction1"]
        reaction2 = query_test_data["reaction2"]

        data = {
            "name": "Created Query",
            "quarter_start": 1,
            "quarter_end": 2,
            "year_start": 2020,
            "year_end": 2020,
            "drugs": [drug1.id, drug2.id],
            "reactions": [reaction1.id, reaction2.id],
        }
        serializer = QuerySerializer(data=data)
        assert serializer.is_valid()

        query = serializer.save(user=user)  # Manually assign user
        assert query.name == "Created Query"
        assert query.quarter_start == 1
        assert query.quarter_end == 2
        assert list(query.drugs.all()) == [drug1, drug2]
        assert set(query.reactions.all()) == {reaction1, reaction2}
        
        # Check that Result object was created
        assert hasattr(query, 'result')
        assert query.result.status == 'pending'

    def test_update_query(self, query_test_data):
        """Test successful update of a Query"""
        query = query_test_data["query"]
        drug2 = query_test_data["drug2"]
        reaction2 = query_test_data["reaction2"]

        data = {
            "name": "Updated Query",
            "quarter_start": 3,
            "quarter_end": 4,
            "year_start": 2020,
            "year_end": 2020,
            "drugs": [drug2.id],
            "reactions": [reaction2.id],
        }
        serializer = QuerySerializer(instance=query, data=data, partial=True)
        assert serializer.is_valid()

        updated_query = serializer.save()
        assert updated_query.name == "Updated Query"
        assert updated_query.quarter_start == 3
        assert updated_query.quarter_end == 4
        assert list(updated_query.drugs.all()) == [drug2]
        assert list(updated_query.reactions.all()) == [reaction2]

    def test_read_only_fields_cannot_be_updated(self, query_test_data):
        """Test that read-only fields cannot be updated"""
        query = query_test_data["query"]
        user = query_test_data["user"]
        data = {
            "id": 9999,
            "user": user.id,
            "created_at": "2022-01-01T00:00:00Z",
            "updated_at": "2022-01-01T00:00:00Z",
        }
        serializer = QuerySerializer(instance=query, data=data, partial=True)
        assert serializer.is_valid()

        updated_query = serializer.save()
        assert updated_query.id != 9999
        assert updated_query.user == user
        assert updated_query.created_at.isoformat() != "2022-01-01T00:00:00Z"

    def test_partial_update_keeps_existing_relations(self, query_test_data):
        """Test that partial update does not remove ManyToMany fields if not provided"""
        query = query_test_data["query"]
        drug1 = query_test_data["drug1"]
        reaction1 = query_test_data["reaction1"]

        data = {"name": "Partially Updated Query"}
        serializer = QuerySerializer(instance=query, data=data, partial=True)
        assert serializer.is_valid()

        updated_query = serializer.save()
        assert updated_query.name == "Partially Updated Query"
        assert list(updated_query.drugs.all()) == [drug1]
        assert list(updated_query.reactions.all()) == [reaction1]

    def test_partial_update_with_null_relations(self, query_test_data):
        """Test that explicitly setting drugs or reactions to an empty list fails"""
        query = query_test_data["query"]
        data = {"drugs": [], "reactions": []}
        serializer = QuerySerializer(instance=query, data=data, partial=True)
        assert not serializer.is_valid()

    @pytest.mark.parametrize(
        "quarter_start, quarter_end, year_start, year_end, is_valid",
        [
            (2, 1, 2020, 2020, False),  # same year, start > end
            (1, 1, 2020, 2020, False),  # same year, start == end
            (1, 2, 2020, 2020, True),  # same year, start < end
            (1, 2, 2021, 2020, False),  # year_start > year_end, always invalid
            (2, 1, 2020, 2021, True),  # year_start < year_end, always valid
            (1, 1, 2020, 2021, True),
            (1, 2, 2020, 2021, True),
        ],
    )
    def test_quarter_start_lte_quarter_end_in_create_query(
        self,
        query_test_data,
        quarter_start,
        quarter_end,
        year_start,
        year_end,
        is_valid,
    ):
        """Test that quarter_start must be lte quarter_end within the same year"""
        drug1 = query_test_data["drug1"]
        reaction1 = query_test_data["reaction1"]
        data = {
            "name": "Quarter Validation Query",
            "quarter_start": quarter_start,
            "quarter_end": quarter_end,
            "year_start": year_start,
            "year_end": year_end,
            "drugs": [drug1.id],
            "reactions": [reaction1.id],
        }
        serializer = QuerySerializer(data=data)
        if is_valid:
            assert serializer.is_valid()
        else:
            assert not serializer.is_valid()
            assert "quarter_start" or "year_start" in serializer.errors

    @pytest.mark.parametrize(
        "quarter_end, year_end, is_valid",
        [
            (1, 2020, False),
            (2, 2020, False),
            (3, 2020, True),
            (3, 2019, False),
            (1, 2021, True),
            (2, 2021, True),
            (3, 2021, True),
        ],
    )
    def test_quarter_start_lte_quarter_end_in_update_query(
        self, query_test_data, quarter_end, year_end, is_valid
    ):
        """Test that quarter_start must be lte quarter_end within the same year"""
        user = query_test_data["user"]
        data = {
            "quarter_end": quarter_end,
            "year_end": year_end,
        }
        query = Query.objects.create(
            user=user,
            name="Test Query",
            quarter_start=2,
            quarter_end=3,
            year_start=2020,
            year_end=2020,
        )
        # Create associated Result object for this test query
        Result.objects.create(
            query=query,
            status=ResultStatus.PENDING,
            ror_values=[],
            ror_lower=[],
            ror_upper=[]
        )
        serializer = QuerySerializer(instance=query, data=data, partial=True)
        assert serializer.is_valid()
        if not is_valid:
            with pytest.raises(serializers.ValidationError) as excinfo:
                serializer.save()
            assert "quarter_start" or "year_start" in excinfo.value.detail
        else:
            serializer.save()


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
