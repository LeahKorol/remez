import logging
from typing import Dict, List

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class PipelineService:
    """
    Service class to handle communication with the pipeline service.

    This service sends requests to trigger pipeline analysis with the specified
    drugs, reactions, and result_id as external_id.
    """

    def __init__(self):
        self.base_url = getattr(settings, "PIPELINE_BASE_URL", "http://localhost:8001")
        self.timeout = getattr(settings, "PIPELINE_TIMEOUT", 30)

    def trigger_pipeline_analysis(
        self,
        year_start: int,
        year_end: int,
        quarter_start: int,
        quarter_end: int,
        drugs: List[Dict[str, any]],
        reactions: List[Dict[str, any]],
        result_id: int,
    ) -> Dict[str, any]:
        """
        Trigger pipeline analysis for the given parameters.

        Returns:
            Dict containing the pipeline response

        Raises:
            requests.RequestException: If the HTTP request fails
            ValueError: If the response format is invalid
        """
        payload = {
            "year_start": year_start,
            "year_end": year_end,
            "quarter_start": quarter_start,
            "quarter_end": quarter_end,
            "drugs": [drug.name for drug in drugs],
            "reactions": [reaction.name for reaction in reactions],
            "external_id": str(result_id),
        }

        url = f"{self.base_url}/api/v1/pipeline/run/"

        try:
            logger.info(f"Triggering pipeline analysis for result_id: {result_id}")
            logger.debug(f"Payload: {payload}")

            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )

            response.raise_for_status()

            response_data = response.json()
            logger.info(f"Pipeline triggered successfully for result_id: {result_id}")
            logger.debug(f"Response: {response_data}")

            return response_data

        except requests.exceptions.Timeout:
            error_msg = f"Pipeline service timeout after {self.timeout}s for result_id: {result_id}"
            logger.error(error_msg)
            raise requests.RequestException(error_msg)

        except requests.exceptions.HTTPError as e:
            error_msg = f"Pipeline service HTTP error for result_id: {result_id}: {e.response.status_code}"
            logger.error(error_msg)
            raise requests.RequestException(error_msg) from e

        except requests.exceptions.RequestException as e:
            error_msg = f"Pipeline service connection error for result_id: {result_id}: {str(e)}"
            logger.error(error_msg)
            raise

        except ValueError as e:
            error_msg = f"Invalid JSON response from pipeline service for result_id: {result_id}: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    def health_check(self) -> bool:
        """
        Check if the pipeline service is healthy.
        """
        try:
            url = f"{self.base_url}/health"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False


pipeline_service = PipelineService()
