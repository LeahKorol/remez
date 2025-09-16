"""
FastAPI service for the FAERS Pipeline
"""
import asyncio
import importlib
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse
from starlette.status import HTTP_201_CREATED, HTTP_404_NOT_FOUND

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("faers-api")

# Load configuration
def load_config():
    """Load pipeline configuration from JSON file"""
    pipeline_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(pipeline_dir, "config", "pipeline_config.json")
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Loaded configuration from {config_path}")
        return config
    except Exception as e:
        logger.warning(f"Failed to load config from {config_path}: {str(e)}")
        # Return default config
        return {
            "pipeline": {"version": "1.0.0"},
            "data": {
                "external_dir": "data/external/faers",
                "output_dir": "pipeline_output"
            },
            "processing": {"threads": 7, "clean_on_failure": True}
        }

# Load config on startup
PIPELINE_CONFIG = load_config()

# Initialize FastAPI app
app = FastAPI(
    title="FAERS Analysis Pipeline API",
    description="API for running and managing FAERS data analysis pipelines",
    version="1.0.0",
)

# Store to track running pipelines and their status
# In a production environment, this would be a database
pipeline_tasks: Dict[str, Dict] = {}

# Models for request/response
class PipelineRequest(BaseModel):
    year_start: int = Field(..., description="Starting year for analysis")
    year_end: int = Field(..., description="Ending year for analysis")
    quarter_start: int = Field(..., ge=1, le=4, description="Starting quarter (1-4)")
    quarter_end: int = Field(..., ge=1, le=4, description="Ending quarter (1-4)")
    query_id: Optional[int] = Field(None, description="Optional query ID")

class PipelineResponse(BaseModel):
    task_id: str = Field(..., description="Unique ID for tracking the pipeline task")
    status: str = Field(..., description="Current status of the pipeline")
    started_at: str = Field(..., description="Timestamp when the pipeline started")
    
class PipelineStatus(BaseModel):
    task_id: str = Field(..., description="Unique ID for tracking the pipeline task")
    status: str = Field(..., description="Current status of the pipeline")
    started_at: str = Field(..., description="Timestamp when the pipeline started")
    completed_at: Optional[str] = Field(None, description="Timestamp when the pipeline completed")
    results_file: Optional[str] = Field(None, description="Path to results file if available")
    error: Optional[str] = Field(None, description="Error message if pipeline failed")

class PipelineList(BaseModel):
    tasks: List[PipelineStatus] = Field(..., description="List of all pipeline tasks")

def run_pipeline_task(task_id: str, req: PipelineRequest):
    """Background task to run the pipeline and update status."""
    started_at = datetime.utcnow().isoformat()
    pipeline_tasks[task_id] = {
        "status": "running",
        "started_at": started_at,
        "completed_at": None,
        "results_file": None,
        "error": None,
    }
    try:
        # Import pipeline modules dynamically
        pipeline_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, pipeline_dir)
        mark_data = importlib.import_module("mark_data")
        report = importlib.import_module("report")
        save_to_db = importlib.import_module("save_to_db")

        year_q_from = f"{req.year_start}q{req.quarter_start}"
        year_q_to = f"{req.year_end}q{req.quarter_end}"
        query_id = req.query_id

        # Directory structure from config
        data_config = PIPELINE_CONFIG.get("data", {})
        processing_config = PIPELINE_CONFIG.get("processing", {})
        
        # Define paths
        pipeline_output_dir = os.path.join(pipeline_dir, data_config.get("output_dir", "pipeline_output"))
        dir_internal = os.path.join(pipeline_output_dir, f"{query_id if query_id else 'temp'}")
        dir_interim = os.path.join(dir_internal, "interim")
        dir_processed = os.path.join(dir_internal, "processed")
        dir_reports = os.path.join(dir_processed, "reports")
        marked_data_dir = os.path.join(dir_interim, "marked_data_v2")
        
        # Create directories if they don't exist
        os.makedirs(dir_internal, exist_ok=True)
        os.makedirs(dir_interim, exist_ok=True)
        os.makedirs(dir_processed, exist_ok=True)
        os.makedirs(dir_reports, exist_ok=True)
        
        # Use the actual data directory from config
        dir_external = os.path.join(pipeline_dir, data_config.get("external_dir", "data/external/faers"))
        config_dir = os.path.join(pipeline_dir, "config")
        
        # Verify data files exist
        available_quarters = []
        file_types = ["demo", "drug", "outc", "reac", "ther"]
        
        for q in range(req.quarter_start, req.quarter_end + 1):
            quarter = f"{req.year_start}q{q}"
            has_all_files = True
            
            for file_type in file_types:
                expected_file = f"{file_type}{quarter}.csv.zip"
                if not os.path.exists(os.path.join(dir_external, expected_file)):
                    logger.warning(f"Missing file: {expected_file}")
                    has_all_files = False
            
            if has_all_files:
                available_quarters.append(quarter)
                logger.info(f"Found complete data for quarter: {quarter}")
        
        if not available_quarters:
            raise ValueError(f"No complete data found for requested quarters {year_q_from} to {year_q_to}")
        
        # Log the data files being used
        logger.info(f"Using FAERS data from: {dir_external}")
        logger.info(f"Available quarters: {available_quarters}")
        logger.info(f"Processing from {year_q_from} to {year_q_to}")

        # Step 1: Mark data
        logger.info("Starting Step 1: Mark data")
        mark_data.main(
            year_q_from=year_q_from,
            year_q_to=year_q_to,
            dir_in=dir_external,
            config_dir=config_dir,
            dir_out=marked_data_dir,
            threads=processing_config.get("threads", 7),
            clean_on_failure=processing_config.get("clean_on_failure", True),
        )
        # Step 2: Generate reports
        logger.info("Starting Step 2: Generate reports")
        report.main(
            dir_marked_data=marked_data_dir,
            dir_raw_data=dir_external,
            config_dir=config_dir,
            dir_reports=dir_reports,
            output_raw_exposure_data=True,
        )
        
        # Step 3: Save to DB if needed
        results_file = os.path.join(dir_reports, "results.json")
        if query_id:
            logger.info(f"Starting Step 3: Save results to database for query ID {query_id}")
            save_to_db.save_ror_values(results_file=results_file, query_id=query_id)
        
        # Update task status
        pipeline_tasks[task_id]["status"] = "completed"
        pipeline_tasks[task_id]["completed_at"] = datetime.utcnow().isoformat()
        pipeline_tasks[task_id]["results_file"] = results_file
        logger.info(f"Pipeline completed successfully. Results saved to {results_file}")
    except Exception as e:
        logger.error(f"Error in pipeline: {str(e)}")
        pipeline_tasks[task_id]["status"] = "failed"
        pipeline_tasks[task_id]["completed_at"] = datetime.utcnow().isoformat()
        pipeline_tasks[task_id]["error"] = str(e)
        raise

@app.post("/pipeline/run", response_model=PipelineResponse, status_code=HTTP_201_CREATED)
def run_pipeline(request: PipelineRequest, background_tasks: BackgroundTasks):
    """Trigger the pipeline as a background task."""
    task_id = str(uuid.uuid4())
    started_at = datetime.utcnow().isoformat()
    pipeline_tasks[task_id] = {
        "status": "pending",
        "started_at": started_at,
        "completed_at": None,
        "results_file": None,
        "error": None,
    }
    background_tasks.add_task(run_pipeline_task, task_id, request)
    return PipelineResponse(task_id=task_id, status="pending", started_at=started_at)

@app.get("/pipeline/status/{task_id}", response_model=PipelineStatus)
def get_pipeline_status(task_id: str):
    """Get the status of a pipeline run."""
    task = pipeline_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Task not found")
    return PipelineStatus(task_id=task_id, **task)

@app.get("/pipeline/list", response_model=PipelineList)
def list_pipelines():
    """List all pipeline tasks."""
    return PipelineList(tasks=[PipelineStatus(task_id=tid, **info) for tid, info in pipeline_tasks.items()])

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "api_version": "1.0.0", "timestamp": datetime.utcnow().isoformat()}

@app.get("/data/available")
def get_available_data():
    """Get information about available FAERS data quarters."""
    pipeline_dir = os.path.dirname(os.path.abspath(__file__))
    data_config = PIPELINE_CONFIG.get("data", {})
    dir_external = os.path.join(pipeline_dir, data_config.get("external_dir", "data/external/faers"))
    
    available_data = {}
    file_types = ["demo", "drug", "outc", "reac", "ther"]
    
    try:
        # Get all files in the directory
        all_files = os.listdir(dir_external)
        
        # Organize by quarters
        for file in all_files:
            for file_type in file_types:
                if file.startswith(file_type) and file.endswith(".csv.zip"):
                    # Extract quarter from filename (e.g., demo2020q1.csv.zip -> 2020q1)
                    quarter = file[len(file_type):-8]
                    if quarter not in available_data:
                        available_data[quarter] = {"files": [], "complete": False}
                    available_data[quarter]["files"].append(file)
        
        # Check which quarters have complete data
        for quarter, data in available_data.items():
            if len(data["files"]) == len(file_types):
                data["complete"] = True
        
        # Sort quarters
        sorted_quarters = sorted(available_data.keys())
        
        return {
            "available_quarters": sorted_quarters,
            "complete_quarters": [q for q in sorted_quarters if available_data[q]["complete"]],
            "file_details": available_data,
            "config": PIPELINE_CONFIG
        }
    except Exception as e:
        logger.error(f"Error retrieving available data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving available data: {str(e)}")