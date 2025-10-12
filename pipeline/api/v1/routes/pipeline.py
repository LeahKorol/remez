"""
Pipeline API routes
"""

import logging

from database import SessionDep
from fastapi import APIRouter, HTTPException, status
from models.models import TaskBase, TaskResults
from models.schemas import (
    AvailableDataResponse,
    ErrorResponse,
    PipelineRequest,
)
from services import pipeline_service
from starlette.status import HTTP_201_CREATED, HTTP_404_NOT_FOUND

logger = logging.getLogger("faers-api.routes")
router = APIRouter()


@router.post(
    "/run",
    response_model=TaskBase,
    status_code=HTTP_201_CREATED,
    summary="Start a new pipeline execution",
    description="Trigger the FAERS analysis pipeline as a background task",
)
async def run_pipeline(
    request: PipelineRequest,
    session: SessionDep,
) -> TaskBase:
    """Start a new pipeline execution"""
    try:
        logger.info(
            f"Pipeline run requested: {request.year_start}q{request.quarter_start} to {request.year_end}q{request.quarter_end}"
        )
        task: TaskResults = TaskResults(external_id=request.external_id)
        session.add(task)
        session.commit()
        session.refresh(task)

        pipeline_service.start_pipeline(request, task)
        return task

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
        data_info = pipeline_service.get_available_data()

        logger.debug(f"Retrieved data info for {data_info['total_quarters']} quarters")

        return AvailableDataResponse(**data_info)

    except Exception as e:
        logger.error(f"Error retrieving available data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available data information",
        )
