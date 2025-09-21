"""
Pipeline service for managing FAERS data processing - Simple Version
"""

import asyncio
import functools
import logging
from datetime import datetime
from typing import Dict, List

from constants import RorFields, TaskStatus
from core.config import get_settings
from database import create_session
from fastapi import BackgroundTasks
from mark_data import main as mark_data_main
from models.models import TaskResults
from models.schemas import PipelineRequest
from report import main as report_main
from utils import get_ror_fields

logger = logging.getLogger("faers-api.pipeline")


class PipelineService:
    """Service for managing pipeline execution and status"""

    def __init__(self):
        self.tasks: Dict[int, TaskResults] = {}
        self.settings = get_settings()

    def start_pipeline(
        self,
        request: PipelineRequest,
        background_tasks: BackgroundTasks,
        task: TaskResults,
    ) -> None:
        """Start a new pipeline task - returns immediately"""

        # Create task entry in-memory
        self.tasks[task.id] = task
        logger.info(
            f"Created pipeline task {task.id} for {request.year_start}q{request.quarter_start}-{request.year_end}q{request.quarter_end}"
        )

        # Wrap run_pipeline_task with asyncio.run because BackgroundTasks requires a synchronous callable
        background_tasks.add_task(
            lambda: asyncio.run(self._run_pipeline_task(task.id, request))
        )

    def list_all_tasks(self) -> List[Dict]:
        """List all pipeline tasks"""
        return [
            {"task_id": task_id, **task_info}
            for task_id, task_info in self.tasks.items()
        ]

    def get_available_data(self) -> Dict:
        """Get information about available FAERS data quarters"""
        # TODO: Use pydantyc model for return type
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
            self.update_task_status(task_id, TaskStatus.RUNNING)

            year_q_from = f"{request.year_start}q{request.quarter_start}"
            year_q_to = f"{request.year_end}q{request.quarter_end}"

            # Setup paths
            pipeline_output_dir = self.settings.get_output_path()
            dir_internal = pipeline_output_dir / f"{str(task_id)}"
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
            self.verify_data_files_exists(dir_external, request)

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
            logger.info("Data marking step completed successfully")

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
            results_file = dir_reports / "results.json"
            logger.info(
                f"Report step completed successfully. Results saved to {results_file}"
            )

            # Step 3: Save to DB
            logger.info(
                f"Starting Step 3: Save results to database for task ID {task_id}"
            )
            self.save_task_results(task_id, results_file)
            logger.info(f"Results for task ID {task_id} saved to database successfully")

            logger.info(f"Pipeline task {task_id} completed successfully")

            # TODO: Step 4: Send ROR values to Django endpoint

            # TODO: Step 5: cleanup intermediate files if needed & remove task_id entry from self.tasks

        except Exception as e:
            logger.error(f"Error in pipeline: {str(e)}", exc_info=True)
            self.save_failed_task(task_id)
            logger.info(f"Pipeline task {task_id} marked as failed")

    def update_task_status(self, task_id: int, status: TaskStatus) -> None:
        """Set task status both in memory and in database"""
        if task_id not in self.tasks:
            raise KeyError(f"Task ID {task_id} not found in memory")

        # Update database first (fail fast if DB issue)
        with create_session() as session:
            task_db = session.get(TaskResults, task_id)
            if not task_db:
                raise ValueError(f"Task {task_id} not found in database")

            task_db.status = status
            session.add(task_db)
            session.commit()
            session.refresh(task_db)

        # Only update memory after successful DB update
        self.tasks[task_id].status = status

    @staticmethod
    def verify_data_files_exists(
        dir_external: str, request: PipelineRequest
    ) -> List[str]:
        # Verify data files exist
        available_quarters = []
        file_types = ["demo", "drug", "outc", "reac", "ther"]

        for q in range(request.quarter_start, request.quarter_end):
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
            year_q_from = f"{request.year_start}q{request.quarter_start}"
            year_q_to = f"{request.year_end}q{request.quarter_end}"
            raise ValueError(
                f"No complete data found for requested quarters {year_q_from} to {year_q_to}"
            )
        return available_quarters

    def save_task_results(self, task_id: int, results_file: str) -> None:
        ror_fields = get_ror_fields(results_file)
        task = self.tasks[task_id]

        # Update task fields
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        task.ror_values = ror_fields[RorFields.ROR_VALUES]
        task.ror_lower = ror_fields[RorFields.ROR_LOWER]
        task.ror_upper = ror_fields[RorFields.ROR_UPPER]

        with create_session() as session:
            task_db = session.get(TaskResults, task_id)
            if not task_db:
                raise ValueError(f"Task {task_id} not found in database")

            # Use model_dump(exclude_unset=True) to enable partial updates
            # It ensures only the fields in task that were assigned will be saved (and not fields with None/default values)
            task_data = task.model_dump(exclude_unset=True)
            task_db.sqlmodel_update(task_data)
            session.add(task_db)
            session.commit()
            session.refresh(task_db)

            self.tasks[task_id] = task_db

    def save_failed_task(self, task_id: int) -> None:
        task = self.tasks[task_id]

        # Update task status
        task.status = TaskStatus.FAILED
        task.completed_at = datetime.now()

        with create_session() as session:
            task_db = session.get(TaskResults, task_id)
            if not task_db:
                logger.error(f"Task {task_id} not found in database")
                return

            task_data = task.model_dump(exclude_unset=True)
            task_db.sqlmodel_update(task_data)
            session.add(task_db)
            session.commit()
            session.refresh(task_db)

            self.tasks[task_id] = task_db


# Global service instance
pipeline_service = PipelineService()
