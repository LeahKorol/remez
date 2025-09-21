"""
Pipeline API routes
"""

import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from models.schemas import (
    AvailableDataResponse,
    ErrorResponse,
    PipelineList,
    PipelineRequest,
    PipelineResponse,
    PipelineStatus,
)
from services.pipeline_service import pipeline_service
from starlette.status import HTTP_201_CREATED, HTTP_404_NOT_FOUND

logger = logging.getLogger("faers-api.routes")
router = APIRouter()


@router.post(
    "/run",
    response_model=PipelineResponse,
    status_code=HTTP_201_CREATED,
    summary="Start a new pipeline execution",
    description="Trigger the FAERS analysis pipeline as a background task",
)
async def run_pipeline(request: PipelineRequest, backround_tasks: BackgroundTasks):
    """Start a new pipeline execution"""
    try:
        logger.info(
            f"Pipeline run requested: {request.year_start}q{request.quarter_start} to {request.year_end}q{request.quarter_end}"
        )

        # This returns immediately with a task ID
        task_id = pipeline_service.start_pipeline(request, backround_tasks)
        started_at = datetime.utcnow().isoformat()

        logger.info(f"Pipeline task {task_id} created successfully")

        return PipelineResponse(
            task_id=task_id, status="pending", started_at=started_at
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
    "/status/{task_id}",
    response_model=PipelineStatus,
    summary="Get pipeline task status",
    description="Get the current status of a pipeline task",
    responses={404: {"model": ErrorResponse, "description": "Task not found"}},
)
async def get_pipeline_status(task_id: str):
    """Get the status of a pipeline task"""
    try:
        task = pipeline_service.get_task_status(task_id)

        if not task:
            logger.warning(f"Task not found: {task_id}")
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found"
            )

        return PipelineStatus(task_id=task_id, **task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving task status {task_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve task status",
        )


@router.get(
    "/list",
    response_model=PipelineList,
    summary="List all pipeline tasks",
    description="Get a list of all pipeline tasks and their statuses",
)
async def list_pipelines():
    """List all pipeline tasks"""
    try:
        tasks_data = pipeline_service.list_all_tasks()
        tasks = [PipelineStatus(**task_data) for task_data in tasks_data]

        logger.debug(f"Retrieved {len(tasks)} pipeline tasks")

        return PipelineList(tasks=tasks, total_count=len(tasks))

    except Exception as e:
        logger.error(f"Error listing pipeline tasks: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pipeline tasks",
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
        data_info = pipeline_service.get_available_data()

        logger.debug(f"Retrieved data info for {data_info['total_quarters']} quarters")

        return AvailableDataResponse(**data_info)

    except Exception as e:
        logger.error(f"Error retrieving available data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available data information",
        )
