from fastapi import APIRouter, BackgroundTasks
from services.pipeline_runner import run_pipeline, get_status

router = APIRouter()

@router.post("/run/{query_id}")
async def run(query_id: int, background_tasks: BackgroundTasks):
    """
    Start the pipeline for a given query ID in the background.
    """
    background_tasks.add_task(run_pipeline, query_id)
    return {"query_id": query_id, "status": "started"}

@router.get("/status/{query_id}")
async def status(query_id: int):
    """
    Get the current status of the pipeline for a given query ID.
    """
    return get_status(query_id)
