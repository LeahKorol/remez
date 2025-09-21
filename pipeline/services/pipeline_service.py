"""
Pipeline service for managing FAERS data processing - Simple Version
"""

import asyncio
import functools
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from core.config import get_settings
from fastapi import BackgroundTasks
from models.schemas import PipelineRequest

logger = logging.getLogger("faers-api.pipeline")


class PipelineService:
    """Service for managing pipeline execution and status"""

    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.settings = get_settings()

    def start_pipeline(
        self, request: PipelineRequest, background_tasks: BackgroundTasks
    ) -> str:
        """Start a new pipeline task - returns immediately"""
        task_id = str(uuid.uuid4())
        started_at = datetime.utcnow().isoformat()

        # Create task entry immediately
        self.tasks[task_id] = {
            "status": "pending",
            "started_at": started_at,
            "completed_at": None,
            "results_file": None,
            "error": None,
        }

        logger.info(
            f"Created pipeline task {task_id} for {request.year_start}q{request.quarter_start}-{request.year_end}q{request.quarter_end}"
        )

        # Wrap run_pipeline_task with asyncio.run because BackgroundTasks requires a synchronous callable
        background_tasks.add_task(
            lambda: asyncio.run(self._run_pipeline_task(task_id, request))
        )

        return task_id

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get the status of a pipeline task"""
        return self.tasks.get(task_id)

    def list_all_tasks(self) -> List[Dict]:
        """List all pipeline tasks"""
        return [
            {"task_id": task_id, **task_info}
            for task_id, task_info in self.tasks.items()
        ]

    def get_available_data(self) -> Dict:
        """Get information about available FAERS data quarters"""
        try:
            external_dir = self.settings.get_external_data_path()
            available_data = {}
            file_types = ["demo", "drug", "outc", "reac", "ther"]

            if not external_dir.exists():
                logger.warning(
                    f"External data directory does not exist: {external_dir}"
                )
                return {
                    "available_quarters": [],
                    "complete_quarters": [],
                    "file_details": {},
                    "total_quarters": 0,
                }

            all_files = [f.name for f in external_dir.iterdir() if f.is_file()]

            # Organize by quarters
            for file in all_files:
                for file_type in file_types:
                    if file.startswith(file_type) and file.endswith(".csv.zip"):
                        quarter = file[len(file_type) : -8]
                        if quarter not in available_data:
                            available_data[quarter] = {"files": [], "complete": False}
                        available_data[quarter]["files"].append(file)

            # Check which quarters have complete data
            for quarter, data in available_data.items():
                if len(data["files"]) == len(file_types):
                    data["complete"] = True

            # Sort quarters
            sorted_quarters = sorted(available_data.keys())
            complete_quarters = [
                q for q in sorted_quarters if available_data[q]["complete"]
            ]

            logger.info(
                f"Found {len(sorted_quarters)} quarters, {len(complete_quarters)} complete"
            )

            return {
                "available_quarters": sorted_quarters,
                "complete_quarters": complete_quarters,
                "file_details": available_data,
                "total_quarters": len(sorted_quarters),
            }

        except Exception as e:
            logger.error(f"Error retrieving available data: {str(e)}", exc_info=True)
            raise

    async def _run_pipeline_task(self, task_id: str, request: PipelineRequest):
        """Background task to run the pipeline"""
        try:
            # Update status to running
            self.tasks[task_id]["status"] = "running"

            # Import pipeline modules
            from mark_data import main as mark_data_main
            from report import main as report_main
            from save_to_db import save_ror_values

            year_q_from = f"{request.year_start}q{request.quarter_start}"
            year_q_to = f"{request.year_end}q{request.quarter_end}"
            query_id = request.query_id

            # Setup paths
            pipeline_output_dir = self.settings.get_output_path()
            dir_internal = pipeline_output_dir / f"{query_id if query_id else 'temp'}"
            dir_interim = dir_internal / "interim"
            dir_processed = dir_internal / "processed"
            dir_reports = dir_processed / "reports"
            marked_data_dir = dir_interim / "marked_data_v2"

            # Create directories if they don't exist
            dir_internal.mkdir(parents=True, exist_ok=True)
            dir_interim.mkdir(parents=True, exist_ok=True)
            dir_processed.mkdir(parents=True, exist_ok=True)
            dir_reports.mkdir(parents=True, exist_ok=True)

            # Get paths
            dir_external = self.settings.get_external_data_path()
            config_dir = self.settings.get_config_path()

            # Verify data files exist
            available_quarters = []
            file_types = ["demo", "drug", "outc", "reac", "ther"]

            for q in range(request.quarter_start, request.quarter_end + 1):
                quarter = f"{request.year_start}q{q}"
                has_all_files = True

                for file_type in file_types:
                    expected_file = dir_external / f"{file_type}{quarter}.csv.zip"
                    if not expected_file.exists():
                        logger.warning(f"Missing file: {expected_file}")
                        has_all_files = False

                if has_all_files:
                    available_quarters.append(quarter)
                    logger.info(f"Found complete data for quarter: {quarter}")

            if not available_quarters:
                raise ValueError(
                    f"No complete data found for requested quarters {year_q_from} to {year_q_to}"
                )

            # Log the data files being used
            logger.info(f"Using FAERS data from: {dir_external}")
            logger.info(f"Available quarters: {available_quarters}")
            logger.info(f"Processing from {year_q_from} to {year_q_to}")

            # Step 1: Mark data
            logger.info("Starting Step 1: Mark data")
            await asyncio.get_event_loop().run_in_executor(
                None,
                functools.partial(
                    mark_data_main,
                    year_q_from=year_q_from,
                    year_q_to=year_q_to,
                    dir_in=str(dir_external),
                    config_dir=str(config_dir),
                    dir_out=str(marked_data_dir),
                    threads=self.settings.PIPELINE_THREADS,
                    clean_on_failure=self.settings.PIPELINE_CLEAN_ON_FAILURE,
                ),
            )

            # Step 2: Generate reports
            logger.info("Starting Step 2: Generate reports")
            await asyncio.get_event_loop().run_in_executor(
                None,
                functools.partial(
                    report_main,
                    dir_marked_data=str(marked_data_dir),
                    dir_raw_data=str(dir_external),
                    config_dir=str(config_dir),
                    dir_reports=str(dir_reports),
                    output_raw_exposure_data=True,
                    return_plot_data_only=True,
                ),
            )

            # Step 3: Save to DB if needed
            results_file = dir_reports / "results.json"
            if query_id:
                logger.info(
                    f"Starting Step 3: Save results to database for query ID {query_id}"
                )
                save_ror_values(results_file=results_file, query_id=query_id)

            # Update task status
            self.tasks[task_id]["status"] = "completed"
            self.tasks[task_id]["completed_at"] = datetime.utcnow().isoformat()
            self.tasks[task_id]["results_file"] = str(results_file)
            logger.info(
                f"Pipeline completed successfully. Results saved to {results_file}"
            )

        except Exception as e:
            logger.error(f"Error in pipeline: {str(e)}", exc_info=True)
            self.tasks[task_id]["status"] = "failed"
            self.tasks[task_id]["completed_at"] = datetime.utcnow().isoformat()
            self.tasks[task_id]["error"] = str(e)


# Global service instance
pipeline_service = PipelineService()
