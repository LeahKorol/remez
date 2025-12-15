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

    def get_pipeline_task(self, task_id: int, retry_http_error_cnt=3) -> Dict[str, any]:
        """
        Get detailed results of a completed task from the pipeline service.

        Note: The pipeline now identifies tasks by external_id. We route
        this call to the external lookup endpoint using the provided task_id
        (which equals the external_id of the result in our system).
        """
        url = f"{self.base_url}/api/v1/pipeline/external/{task_id}"

        try:
            logger.debug(f"Fetching detailed results for task_id: {task_id}")

            response = requests.get(
                url,
                timeout=self.timeout,
            )

            response.raise_for_status()
            response_data = response.json()
            logger.info(f"Retrieved detailed results for task_id {task_id}")
            return response_data

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Task results {task_id} not found in pipeline service")
                return None
            logger.error(
                f"Pipeline service HTTP error for task_id {task_id}: {e.response.status_code}"
            )
            if retry_http_error_cnt > 0:
                retry_http_error_cnt -= 1
                logger.info(
                    f"Retrying fetch for task_id {task_id}, attempts left: {retry_http_error_cnt}"
                )
                return self.get_pipeline_task(task_id, retry_http_error_cnt)
            return None

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Pipeline service connection error for task_id {task_id}: {str(e)}"
            )
            return None

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
