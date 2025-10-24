import asyncio
import logging
import shutil
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path
from utils import Quarter, generate_quarters

import httpx
from constants import RorFields, TaskStatus
from core.config import get_settings

from errors import DataFilesNotFoundError
from mark_data import main as mark_data_main
from models.models import TaskResults
from models.schemas import AvailableDataResponse, PipelineRequest, QuarterData
from report import main as report_main
from services.task_repository import TaskRepository
from utils import get_ror_fields, normalise_empty_ror_fields

# Global static settings
settings = get_settings()
executor = ProcessPoolExecutor(settings.PIPELINE_MAX_WORKERS)

logger: logging.Logger = logging.getLogger(__name__)
# Once a task process is spawned, this value is overridden by a custom logger for that task.
task_logger: logging.Logger = logging.getLogger(__name__)


# -----------------------------
# Logger helper
# -----------------------------
def configure_task_logger(task_id: int) -> logging.Logger:
    """
    Set up logging for a subprocess.
    Each task process uses its own logger to prevent log output from mixing when processes run concurrently.
    """
    logs_dir: Path = settings.get_logs_dir()
    log_filename = f"{logs_dir}/{str(task_id)}.log"

    # Create logs directory if it doesn't exist
    logs_dir.mkdir(exist_ok=True)

    # Create a logger for this process
    logger = logging.getLogger(str(task_id))
    logger.setLevel(settings.LOG_LEVEL)

    # Remove any existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create file handler & overwrite the file content if exists
    file_handler = logging.FileHandler(log_filename, mode="w")
    file_handler.setLevel(settings.LOG_LEVEL)

    # Create console handler (stderr)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(settings.LOG_LEVEL)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s"
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# -----------------------------
# Pipeline helper functions
# -----------------------------
def handle_task_failure(task: TaskResults, error_message: str, send_callback: bool = True):
    """Handle task failures by updating task status in DB and sending callback."""
    # Mark task as failed and update database
    try:
        TaskRepository.update_status(task, TaskStatus.FAILED)
    except Exception as db_error:
        task_logger.error(f"Failed to update task {task.id} status in database: {str(db_error)}")
    
    # Send failure notification via callback if requested
    if send_callback:
        try:
            send_results_to_callback(task)
            task_logger.info(f"Failure notification sent via callback for task {task.id}")
        except Exception as callback_error:
            task_logger.error(f"Failed to send callback for task {task.id}: {str(callback_error)}")
    
    task_logger.info(f"Pipeline task {task.id} failure handling completed")





def verify_data_files_exist(request: PipelineRequest, dir_external):
    available_quarters = []
    requested_quarters = []
    file_types = ["demo", "drug", "outc", "reac"]
    quarters = generate_quarters(Quarter(request.year_start, request.quarter_start), Quarter(request.year_end, request.quarter_end))

    for q in quarters:
        requested_quarters.append(q.__str__())
        has_all_files = True
        for file_type in file_types:
            expected_file = dir_external / f"{file_type}{q.__str__()}.csv.zip"
            if not expected_file.exists():
                task_logger.warning(f"Missing file: {expected_file}")
                has_all_files = False
        if has_all_files:
            available_quarters.append(q.__str__())
            task_logger.info(f"Found complete data for quarter: {q}")

    if not available_quarters or len(available_quarters) < len(requested_quarters):
        raise DataFilesNotFoundError(
            year_start=request.year_start,
            quarter_start=request.quarter_start,
            year_end=request.year_end,
            quarter_end=request.quarter_end,
            requested_quarters=requested_quarters,
            available_quarters=available_quarters
        )

    return available_quarters


def mark_data(
    year_q_from,
    year_q_to,
    dir_external,
    config_dict,
    marked_data_dir,
):
    task_logger.info("Starting Step 1: Mark data")
    mark_data_main(
        year_q_from=year_q_from,
        year_q_to=year_q_to,
        dir_in=str(dir_external),
        config_dict=config_dict,
        dir_out=str(marked_data_dir),
        threads=settings.PIPELINE_THREADS,
        clean_on_failure=False,
        custom_logger=task_logger,
    )
    task_logger.info("Data marking step completed successfully")


def generate_reports(marked_data_dir, dir_external, config_dict, dir_reports):
    task_logger.info("Starting Step 2: Generate reports")
    report_main(
        dir_marked_data=str(marked_data_dir),
        dir_raw_data=str(dir_external),
        config_dict=config_dict,
        dir_reports=str(dir_reports),
        output_raw_exposure_data=True,
        return_plot_data_only=True,
        custom_logger=task_logger,
    )
    results_file = dir_reports / "results.json"
    task_logger.info(
        f"Report step completed successfully. Results saved to {results_file}"
    )
    return results_file


def save_results_to_db(task: TaskResults, results_file):
    """Save pipeline results to database using TaskRepository."""
    ror_fields = get_ror_fields(results_file)
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now()
    task.ror_values = ror_fields[RorFields.ROR_VALUES]
    task.ror_lower = ror_fields[RorFields.ROR_LOWER]
    task.ror_upper = ror_fields[RorFields.ROR_UPPER]

    TaskRepository.save_task_results(task)
    task_logger.info(f"Results for task {task.id} saved to DB")


def send_results_to_callback(task: TaskResults):
    callback_url = settings.PIPELINE_CALLBACK_URL
    if not callback_url:
        task_logger.warning("No callback URL configured, skipping sending results")
        return

    async def _send():
        # Configure client for single-use in subprocess context
        timeout = httpx.Timeout(30.0, connect=10.0)
        limits = httpx.Limits(
            max_connections=1,
            max_keepalive_connections=0,  # No persistent connections to avoid cleanup issues
        )

        # Scoped client ensures proper cleanup before event loop closes
        async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
            normalise_empty_ror_fields(task)
            task_logger.debug(f"Sending task data: {task}")
            # Convert task to JSON-compatible dict. Use mode="json" to handle datetime serialization as well.
            task_json = task.model_dump(mode="json")
            url = f"{callback_url}/{task_json['external_id']}/"

            response = await client.put(url, json=task_json)
            response.raise_for_status()

            task_logger.info(
                f"Sent results for task {task.id} to callback URL {callback_url}"
            )

    try:
        asyncio.run(_send())
    except Exception as e:
        task_logger.error(
            f"Failed to send results for task {task.id} to callback URL {callback_url}: {str(e)}",
            exc_info=True,
        )


def cleanup(calc_dir: Path):
    task_logger.info("removing internal data directories")
    clean_internal_dirs: bool = settings.PIPELINE_CLEAN_INTERNAL_DIRS

    if clean_internal_dirs:
        try:
            if calc_dir.exists():
                task_logger.debug(f"Deleting Calculations dir {calc_dir}")
                shutil.rmtree(calc_dir)
        except Exception as e:
            task_logger.warning(f"Failed to remove {calc_dir}: {e}")


# -----------------------------
# Main pipeline function
# -----------------------------
def run_pipeline(request: PipelineRequest, task: TaskResults):
    global task_logger
    task_logger = configure_task_logger(task.id)
    try:
        TaskRepository.update_status(task, TaskStatus.RUNNING)

        year_q_from = f"{request.year_start}q{request.quarter_start}"
        year_q_to = f"{request.year_end}q{request.quarter_end}"

        pipeline_output_dir = settings.get_output_path()
        dir_internal = pipeline_output_dir / str(task.id)
        dir_interim = dir_internal / "interim"
        dir_processed = dir_internal / "processed"
        dir_reports = dir_processed / "reports"
        marked_data_dir = dir_interim / "marked_data_v2"

        if dir_internal.exists():
            task_logger.warning(
                f"dir_internal exists for task_id {task.id}. Deleting..."
            )
            shutil.rmtree(dir_internal)

        for d in [dir_internal, dir_interim, dir_processed, dir_reports]:
            d.mkdir(parents=True)

        dir_external = settings.get_external_data_path()
        config_dict = {
            "drug": request.drugs,
            "reaction": request.reactions,
            "control": request.control,
        }

        verify_data_files_exist(request, dir_external)
        mark_data(
            year_q_from,
            year_q_to,
            dir_external,
            config_dict,
            marked_data_dir,
        )
        results_file = generate_reports(
            marked_data_dir, dir_external, config_dict, dir_reports
        )
        save_results_to_db(task, results_file)
        send_results_to_callback(task)

        # Step 5
        cleanup(Path(dir_internal))

        task_logger.info(f"Pipeline task {task.id} completed successfully")

    except DataFilesNotFoundError as e:
        error_msg = f"Data files not found for task {task.id}: {str(e)}"
        task_logger.error(error_msg, exc_info=True)
        handle_task_failure(task, error_msg, send_callback=True)
        
    except Exception as e:
        error_msg = f"Error in pipeline for task {task.id}: {str(e)}"
        task_logger.error(error_msg, exc_info=True)
        handle_task_failure(task, error_msg, send_callback=True)


# -----------------------------
# Trigger function
# -----------------------------
def start_pipeline(request: PipelineRequest, task: TaskResults):
    """Start the pipeline in a separate process"""
    logger.info(f"Triggering pipeline for task {task.id}")
    # Submit to process pool and immediately return
    executor.submit(run_pipeline, request, task)
    logger.debug(f"Task {task.id} was submitted sucesssfully")


def get_available_data() -> AvailableDataResponse:
    """Get information about available FAERS data quarters"""
    try:
        external_dir = settings.get_external_data_path()
        available_data = {}
        file_types = ["demo", "drug", "outc", "reac"]

        if not external_dir.exists():
            logger.warning(f"External data directory does not exist: {external_dir}")
            return AvailableDataResponse(
                incomplete_quarters=[],
                complete_quarters=[],
                file_details={},
            )

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

        # Convert to Pydantic models
        file_details = {
            quarter: QuarterData(files=data["files"], complete=data["complete"])
            for quarter, data in available_data.items()
        }

        # Sort quarters
        sorted_quarters = sorted(available_data.keys())
        complete_quarters = [
            q for q in sorted_quarters if available_data[q]["complete"]
        ]
        incomplete_quarters = [
            q for q in sorted_quarters if not available_data[q]["complete"]
        ]

        logger.info(
            f"Found {len(sorted_quarters)} quarters total: {len(complete_quarters)} complete, {len(incomplete_quarters)} incomplete"
        )

        return AvailableDataResponse(
            incomplete_quarters=incomplete_quarters,
            complete_quarters=complete_quarters,
            file_details=file_details,
        )

    except Exception as e:
        logger.error(f"Error retrieving available data: {str(e)}", exc_info=True)
        raise
