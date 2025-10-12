import pytest
import requests
from django.conf import settings

from analysis.models import DrugName, ReactionName
from analysis.services.pipeline_service import PipelineService


@pytest.fixture
def drug(db):
    """Fixture for drug name"""
    return DrugName.objects.create(name="Test Drug")


@pytest.fixture
def reaction(db):
    """Fixture for reaction name"""
    return ReactionName.objects.create(name="Test Reaction")


@pytest.mark.django_db
class TestPipelineService:
    """Test cases for Pipeline Service integration"""

    def test_pipeline_service_initialization(self):
        """Test that pipeline service initializes with correct defaults"""
        service = PipelineService()
        assert service.base_url == "http://localhost:8001"
        assert service.timeout == 30

    def test_pipeline_service_with_custom_settings(self, mocker):
        """Test that pipeline service uses custom settings when available"""
        mocker.patch.object(settings, "PIPELINE_BASE_URL", "http://custom-api:9000")
        mocker.patch.object(settings, "PIPELINE_TIMEOUT", 60)

        service = PipelineService()
        assert service.base_url == "http://custom-api:9000"
        assert service.timeout == 60

    def test_trigger_pipeline_analysis_success(self, mocker, drug, reaction):
        """Test successful pipeline trigger"""
        # Setup mock response
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"task_id": "abc123", "status": "started"}
        mock_response.raise_for_status.return_value = None

        mock_post = mocker.patch(
            "analysis.services.pipeline_service.requests.post",
            return_value=mock_response,
        )

        service = PipelineService()

        result = service.trigger_pipeline_analysis(
            drugs=[drug],
            reactions=[reaction],
            result_id=123,
            year_start=2020,
            year_end=2021,
            quarter_start=1,
            quarter_end=4,
        )

        # Verify the call was made with correct parameters
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        assert call_args[1]["json"]["drugs"] == [drug.name]
        assert call_args[1]["json"]["reactions"] == [reaction.name]
        assert call_args[1]["json"]["external_id"] == '123'
        assert call_args[1]["json"]["year_start"] == 2020
        assert call_args[1]["json"]["year_end"] == 2021
        assert call_args[1]["json"]["quarter_start"] == 1
        assert call_args[1]["json"]["quarter_end"] == 4

        assert result == {"task_id": "abc123", "status": "started"}

    def test_trigger_pipeline_analysis_http_error(self, mocker, drug, reaction):
        """Test pipeline trigger with HTTP error"""
        mock_response = mocker.Mock()
        mock_response.status_code = 500

        # Create HTTPError with proper response object
        http_error = requests.HTTPError("Internal Server Error")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error

        mock_post = mocker.patch(
            "analysis.services.pipeline_service.requests.post",
            return_value=mock_response,
        )

        service = PipelineService()

        with pytest.raises(requests.RequestException):
            service.trigger_pipeline_analysis(
                drugs=[drug],
                reactions=[reaction],
                result_id=123,
                year_start=2020,
                year_end=2021,
                quarter_start=1,
                quarter_end=4,
            )

            mock_post.assert_called_once()

    def test_trigger_pipeline_analysis_timeout(self, mocker, drug, reaction):
        """Test pipeline trigger with timeout"""
        mock_post = mocker.patch(
            "analysis.services.pipeline_service.requests.post",
            side_effect=requests.Timeout("Request timed out"),
        )
        mock_post.side_effect = requests.Timeout("Request timed out")

        service = PipelineService()

        with pytest.raises(requests.RequestException):
            service.trigger_pipeline_analysis(
                drugs=[drug],
                reactions=[reaction],
                result_id=123,
                year_start=2020,
                year_end=2021,
                quarter_start=1,
                quarter_end=4,
            )

    def test_health_check_success(self, mocker):
        """Test successful health check"""
        mock_response = mocker.Mock()
        mock_response.status_code = 200

        mock_get = mocker.patch(
            "analysis.services.pipeline_service.requests.get",
            return_value=mock_response,
        )

        service = PipelineService()
        assert service.health_check() is True
        mock_get.assert_called_once()

    def test_health_check_failure(self, mocker):
        """Test failed health check"""
        mock_get = mocker.patch(
            "analysis.services.pipeline_service.requests.get",
            side_effect=requests.RequestException("Connection failed"),
        )

        service = PipelineService()
        assert service.health_check() is False
        mock_get.assert_called_once()
