import pytest
import requests
from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from analysis.models import DrugName, Query, ReactionName, Result, ResultStatus

User = get_user_model()


@pytest.fixture
def api_client():
    """Fixture for API client"""
    return APIClient()


@pytest.fixture
def user(db):
    """Fixture for test user"""
    user = User.objects.create_user(email="test@example.com", password="testpassword")
    email_address = EmailAddress.objects.get(user=user)
    email_address.verified = True
    email_address.save()
    return user


@pytest.fixture
def drug(db):
    """Fixture for drug name"""
    return DrugName.objects.create(name="Test Drug")


@pytest.fixture
def reaction(db):
    """Fixture for reaction name"""
    return ReactionName.objects.create(name="Test Reaction")


@pytest.fixture
def required_fields(drug, reaction):
    """Fixture for required query fields"""
    return {
        "quarter_start": 1,
        "quarter_end": 2,
        "year_start": 2020,
        "year_end": 2020,
        "drugs": [drug.id],
        "reactions": [reaction.id],
    }


def authenticate_user(api_client, user):
    """Helper to authenticate user"""
    api_client.force_authenticate(user=user)


@pytest.mark.django_db
class TestPipelineIntegration:
    """Integration tests for pipeline service with Query operations"""

    def test_create_query_pipeline_success(
        self, mocker, api_client, user, required_fields, drug, reaction
    ):
        """Test creating query successfully triggers pipeline with correct fields"""
        # Mock pipeline service
        mock_trigger = mocker.patch(
            "analysis.views.pipeline_service.trigger_pipeline_analysis"
        )
        # Disable demo mode
        mocker.patch.object(settings, "NUM_DEMO_QUARTERS", -1)

        authenticate_user(api_client, user)

        list_url = reverse("query-list")
        data = {"name": "Pipeline Success Query", **required_fields}
        response = api_client.post(list_url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED

        # Verify pipeline was called with correct parameters
        mock_trigger.assert_called_once()
        call_kwargs = mock_trigger.call_args[1]

        assert call_kwargs["year_start"] == 2020
        assert call_kwargs["year_end"] == 2020
        assert call_kwargs["quarter_start"] == 1
        assert call_kwargs["quarter_end"] == 2
        assert len(call_kwargs["drugs"]) == 1
        assert call_kwargs["drugs"][0] == drug
        assert len(call_kwargs["reactions"]) == 1
        assert call_kwargs["reactions"][0] == reaction

        # Verify result was created in PENDING status
        query = Query.objects.get(name="Pipeline Success Query")
        assert hasattr(query, "result")
        assert query.result.status == ResultStatus.PENDING
        assert "result_id" in call_kwargs
        assert call_kwargs["result_id"] == query.result.id

    def test_create_query_pipeline_failure(
        self, mocker, api_client, user, required_fields
    ):
        """Test creating query with pipeline failure marks result as failed"""
        # Mock pipeline service to raise exception
        mock_trigger = mocker.patch(
            "analysis.views.pipeline_service.trigger_pipeline_analysis",
            side_effect=requests.RequestException("Pipeline connection failed"),
        )
        # Disable demo mode
        mocker.patch.object(settings, "NUM_DEMO_QUARTERS", -1)

        authenticate_user(api_client, user)

        list_url = reverse("query-list")
        data = {"name": "Pipeline Failure Query", **required_fields}

        with pytest.raises(requests.RequestException):
            api_client.post(list_url, data, format="json")

        # Verify pipeline was called
        mock_trigger.assert_called_once()

        # Verify result was created and marked as failed
        query = Query.objects.get(name="Pipeline Failure Query")
        assert query.result.status == ResultStatus.FAILED

    def test_create_query_demo_mode(self, mocker, api_client, user, required_fields):
        """Test creating query in demo mode creates completed result without calling pipeline"""
        # Mock pipeline service - should NOT be called
        mock_trigger = mocker.patch(
            "analysis.views.pipeline_service.trigger_pipeline_analysis"
        )
        # Enable demo mode
        mocker.patch.object(settings, "NUM_DEMO_QUARTERS", 2)

        authenticate_user(api_client, user)

        list_url = reverse("query-list")
        data = {"name": "Demo Mode Query", **required_fields}
        response = api_client.post(list_url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED

        # Verify pipeline was NOT called in demo mode
        mock_trigger.assert_not_called()

        # Verify result was created with demo data and completed status
        query = Query.objects.get(name="Demo Mode Query")
        assert query.result.status == ResultStatus.COMPLETED
        assert len(query.result.ror_values) > 0  # Should have demo data
        assert len(query.result.ror_lower) > 0  # Should have demo data
        assert len(query.result.ror_upper) > 0  # Should have demo data

    def test_update_query_relevant_fields_triggers_pipeline(
        self, mocker, api_client, user, drug, reaction
    ):
        """Test updating relevant fields triggers pipeline recalculation"""
        # Create existing query with result
        query = Query.objects.create(
            user=user,
            name="Original Query",
            quarter_start=1,
            quarter_end=2,
            year_start=2020,
            year_end=2020,
        )
        query.drugs.set([drug.id])
        query.reactions.set([reaction.id])
        Result.objects.create(
            query=query,
            status=ResultStatus.COMPLETED,
            ror_values=[1.5, 2.0],
            ror_lower=[1.2, 1.8],
            ror_upper=[1.8, 2.2],
        )

        # Mock pipeline service
        mock_trigger = mocker.patch(
            "analysis.views.pipeline_service.trigger_pipeline_analysis"
        )
        # Disable demo mode
        mocker.patch.object(settings, "NUM_DEMO_QUARTERS", -1)

        authenticate_user(api_client, user)

        # Update relevant field (quarter range)
        detail_url = reverse("query-detail", kwargs={"id": query.id})
        data = {"quarter_start": 2, "quarter_end": 4}
        response = api_client.patch(detail_url, data, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Verify pipeline was called for recalculation
        mock_trigger.assert_called_once()
        call_kwargs = mock_trigger.call_args[1]

        # Verify updated parameters were used
        assert call_kwargs["quarter_start"] == 2  # Updated value
        assert call_kwargs["quarter_end"] == 4  # Updated value
        assert call_kwargs["year_start"] == 2020  # Original value
        assert call_kwargs["year_end"] == 2020  # Original value

        # Verify result status was reset to PENDING
        query.refresh_from_db()
        assert query.result.status == ResultStatus.PENDING

    def test_update_query_irrelevant_fields_no_pipeline_trigger(
        self, mocker, api_client, user, drug, reaction
    ):
        """Test updating irrelevant fields doesn't trigger pipeline"""
        # Create existing query with result
        query = Query.objects.create(
            user=user,
            name="Original Query",
            quarter_start=1,
            quarter_end=2,
            year_start=2020,
            year_end=2020,
        )
        query.drugs.set([drug.id])
        query.reactions.set([reaction.id])
        Result.objects.create(
            query=query,
            status=ResultStatus.COMPLETED,
            ror_values=[1.5, 2.0],
            ror_lower=[1.2, 1.8],
            ror_upper=[1.8, 2.2],
        )

        # Mock pipeline service - should NOT be called
        mock_trigger = mocker.patch(
            "analysis.views.pipeline_service.trigger_pipeline_analysis"
        )

        authenticate_user(api_client, user)

        # Update only irrelevant field (name)
        detail_url = reverse("query-detail", kwargs={"id": query.id})
        data = {"name": "Updated Name Only"}
        response = api_client.patch(detail_url, data, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Verify pipeline was NOT called
        mock_trigger.assert_not_called()

        # Verify result status unchanged
        query.refresh_from_db()
        assert query.result.status == ResultStatus.COMPLETED
        assert query.name == "Updated Name Only"

    def test_update_query_pipeline_failure(
        self, mocker, api_client, user, drug, reaction
    ):
        """Test updating query with pipeline failure marks result as failed"""
        # Create existing query with result
        query = Query.objects.create(
            user=user,
            name="Original Query",
            quarter_start=1,
            quarter_end=2,
            year_start=2020,
            year_end=2020,
        )
        query.drugs.set([drug.id])
        query.reactions.set([reaction.id])
        Result.objects.create(
            query=query,
            status=ResultStatus.COMPLETED,
            ror_values=[1.5, 2.0],
            ror_lower=[1.2, 1.8],
            ror_upper=[1.8, 2.2],
        )

        # Mock pipeline service to raise exception
        mock_trigger = mocker.patch(
            "analysis.views.pipeline_service.trigger_pipeline_analysis",
            side_effect=requests.RequestException("Pipeline error"),
        )
        # Disable demo mode
        mocker.patch.object(settings, "NUM_DEMO_QUARTERS", -1)

        authenticate_user(api_client, user)

        # Update relevant field that should trigger pipeline
        detail_url = reverse("query-detail", kwargs={"id": query.id})
        data = {"year_start": 2021, "year_end": 2021}

        with pytest.raises(requests.RequestException):
            api_client.patch(detail_url, data, format="json")

        # Verify pipeline was called
        mock_trigger.assert_called_once()

        # Verify result was marked as failed
        query.refresh_from_db()
        assert query.result.status == ResultStatus.FAILED

    def test_update_query_demo_mode(self, mocker, api_client, user, drug, reaction):
        """Test updating query in demo mode creates completed result without calling pipeline"""
        # Create existing query with result
        query = Query.objects.create(
            user=user,
            name="Original Query",
            quarter_start=1,
            quarter_end=2,
            year_start=2020,
            year_end=2020,
        )
        query.drugs.set([drug.id])
        query.reactions.set([reaction.id])
        Result.objects.create(
            query=query,
            status=ResultStatus.PENDING,
            ror_values=[],
            ror_lower=[],
            ror_upper=[],
        )

        # Mock pipeline service - should NOT be called
        mock_trigger = mocker.patch(
            "analysis.views.pipeline_service.trigger_pipeline_analysis"
        )
        # Enable demo mode
        mocker.patch.object(settings, "NUM_DEMO_QUARTERS", 2)

        authenticate_user(api_client, user)

        # Update relevant field that should trigger pipeline in normal mode
        detail_url = reverse("query-detail", kwargs={"id": query.id})
        data = {"quarter_start": 2, "quarter_end": 4}
        response = api_client.patch(detail_url, data, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Verify pipeline was NOT called in demo mode
        mock_trigger.assert_not_called()

        # Verify result was updated with demo data and completed status
        query.refresh_from_db()
        assert query.result.status == ResultStatus.COMPLETED
        assert len(query.result.ror_values) > 0  # Should have demo data
        assert len(query.result.ror_lower) > 0  # Should have demo data
        assert len(query.result.ror_upper) > 0  # Should have demo data
