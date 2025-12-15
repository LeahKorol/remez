"""
Pipeline API routes
"""

import logging

from constants import TaskStatus
from database import SessionDep
from errors import PipelineCapacityExceededError
from fastapi import APIRouter, HTTPException, status
from models.models import TaskBase, TaskResults
from models.schemas import (
    AvailableDataResponse,
    ErrorResponse,
    PipelineRequest,
    TaskListResponse,
    TaskSummary,
)
from services import pipeline_service
from services.task_repository import TaskRepository
from sqlmodel import select
from starlette.status import (
    HTTP_200_OK,
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
    "/external/{external_id}",
    response_model=TaskResults,
    summary="Get pipeline task by external_id",
    description="Get the current state of a pipeline task by external_id",
    responses={404: {"model": ErrorResponse, "description": "Task not found"}},
)
async def get_pipeline_by_external_id(
    external_id: str, session: SessionDep
) -> TaskResults:
    """Get the current state of a pipeline task by external_id"""
    try:
        logger.debug(f"Retrieving task by external_id: {external_id}")

        statement = select(TaskResults).where(TaskResults.external_id == external_id)
        task = session.exec(statement).first()

        if not task:
            logger.warning(f"Task not found for external_id: {external_id}")
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Task with external_id {external_id} not found",
            )

        logger.debug(
            f"Retrieved task id={task.id} for external_id={external_id} with status {task.status}"
        )
        return task

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving task by external_id {external_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve task by external_id",
        )


@router.get(
    "/status/{status}",
    response_model=TaskListResponse,
    status_code=HTTP_200_OK,
    summary="Get tasks by status",
    description="Get all tasks that have a specific status",
    responses={400: {"model": ErrorResponse, "description": "Invalid status"}},
)
async def get_tasks_by_status(
    status: TaskStatus, session: SessionDep
) -> TaskListResponse:
    """Get all tasks with a specific status"""
    try:
        logger.debug(f"Retrieving tasks with status: {status}")

        # Query tasks with the specified status
        statement = select(TaskResults).where(TaskResults.status == status)
        tasks = session.exec(statement).all()

        # Convert to TaskSummary objects
        task_summaries = [
            TaskSummary(id=task.id, external_id=task.external_id) for task in tasks
        ]

        logger.debug(f"Found {len(task_summaries)} tasks with status {status}")

        return TaskListResponse(tasks=task_summaries, count=len(task_summaries))

    except Exception as e:
        logger.error(
            f"Error retrieving tasks by status {status}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tasks by status",
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
