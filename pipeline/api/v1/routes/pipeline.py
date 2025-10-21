"""
Pipeline API routes
"""

import logging

from database import SessionDep
from errors import PipelineCapacityExceededError
from fastapi import APIRouter, HTTPException, status
from models.models import TaskBase, TaskResults
from models.schemas import (
    AvailableDataResponse,
    ErrorResponse,
    PipelineRequest,
)
from services import pipeline_service
from services.task_repository import TaskRepository
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_404_NOT_FOUND,
    HTTP_429_TOO_MANY_REQUESTS,
)

logger = logging.getLogger("faers-api.routes")
router = APIRouter()


@router.post(
    "/run",
    response_model=TaskBase,
    status_code=HTTP_201_CREATED,
    summary="Start a new pipeline execution",
    description="Trigger the FAERS analysis pipeline as a background task",
)
async def run_pipeline(request: PipelineRequest) -> TaskBase:
    """Start a new pipeline execution"""
    try:
        logger.info(
            f"Pipeline run requested: {request.year_start}q{request.quarter_start} to {request.year_end}q{request.quarter_end}"
        )
        # Try to create a new task using circular buffer logic
        task: TaskResults = TaskRepository.create_or_reuse_slot(request.external_id)
        pipeline_service.start_pipeline(request, task)
        return task

    except PipelineCapacityExceededError as e:
        logger.warning(
            f"Pipeline capacity exceeded for external_id {request.external_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            f"Unexpected error creating pipeline task: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create pipeline task",
        )


@router.get(
    "/{task_id}",
    response_model=TaskResults,
    summary="Get pipeline task results",
    description="Get the current state of a pipeline task",
    responses={404: {"model": ErrorResponse, "description": "Task not found"}},
)
async def get_pipeline_status(task_id: int, session: SessionDep) -> TaskResults:
    """Get the current state of a pipeline task"""
    try:
        task = session.get(TaskResults, task_id)

        if not task:
            logger.warning(f"Task not found: {task_id}")
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found"
            )
        logger.debug(f"Retrieved task {task_id} with status {task.status}")
        return task

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving task status {task_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve task status",
        )


@router.get(
    "/data/available",
    response_model=AvailableDataResponse,
    summary="Get available FAERS data",
    description="Get information about available FAERS data quarters",
)
async def get_available_data():
    """Get information about available FAERS data quarters"""
    try:
        data_info: AvailableDataResponse = pipeline_service.get_available_data()

        logger.debug(
            f"Retrieved data info: {len(data_info.complete_quarters)} complete quarters, {len(data_info.incomplete_quarters)} incomplete quarters"
        )

        return data_info

    except Exception as e:
        logger.error(f"Error retrieving available data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available data information",
        )
