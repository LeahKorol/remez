import asyncio
import logging
import shutil
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path

from constants import RorFields, TaskStatus
from core.config import get_settings
from core.http_client import http_client
from database import create_session
from mark_data import main as mark_data_main
from models.models import TaskResults
from models.schemas import PipelineRequest
from report import main as report_main
from utils import get_ror_fields

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
def update_task_status(task: TaskResults, status: TaskStatus):
    now = datetime.now()
    if status == TaskStatus.RUNNING:
        task.created_at = now
    else:
        task.completed_at = now
    task.status = status

    with create_session() as session:
        task_db = session.get(TaskResults, task.id)
        if task_db:
            task_db.sqlmodel_update(task.model_dump(exclude_unset=True))
            session.add(task_db)
            session.commit()
            session.refresh(task_db)
    task_logger.info(f"Task {task.id} status updated to {status}")


def verify_data_files_exists(request: PipelineRequest, dir_external):
    available_quarters = []
    file_types = ["demo", "drug", "outc", "reac", "ther"]

    for q in range(request.quarter_start, request.quarter_end + 1):
        quarter = f"{request.year_start}q{q}"
        has_all_files = True
        for file_type in file_types:
            expected_file = dir_external / f"{file_type}{quarter}.csv.zip"
            if not expected_file.exists():
                task_logger.warning(f"Missing file: {expected_file}")
                has_all_files = False
        if has_all_files:
            available_quarters.append(quarter)
            task_logger.info(f"Found complete data for quarter: {quarter}")

    if not available_quarters:
        year_q_from = f"{request.year_start}q{request.quarter_start}"
        year_q_to = f"{request.year_end}q{request.quarter_end}"
        raise ValueError(
            f"No complete data found for requested quarters {year_q_from} to {year_q_to}"
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
    ror_fields = get_ror_fields(results_file)
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now()
    task.ror_values = ror_fields[RorFields.ROR_VALUES]
    task.ror_lower = ror_fields[RorFields.ROR_LOWER]
    task.ror_upper = ror_fields[RorFields.ROR_UPPER]

    with create_session() as session:
        task_db = session.get(TaskResults, task.id)
        if task_db:
            task_db.sqlmodel_update(task.model_dump(exclude_unset=True))
            session.add(task_db)
            session.commit()
            session.refresh(task_db)

    task_logger.info(f"Results for task {task.id} saved to DB")


def send_results_to_callback(task: TaskResults):
    callback_url = settings.PIPELINE_CALLBACK_URL
    if not callback_url:
        task_logger.warning("No callback URL configured, skipping sending results")
        return

    async def _send():
        try:
            task_json = task.model_dump(mode="json")
            url = f"{callback_url}/{task_json['external_id']}/"
            await http_client.put(url, json=task_json)
            task_logger.info(
                f"Sent results for task {task.id} to callback URL {callback_url}"
            )
        except Exception as e:
            task_logger.error(
                f"Failed to send results for task {task.id} to callback URL {callback_url}: {str(e)}",
                exc_info=True,
            )

    asyncio.run(_send())


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
        update_task_status(task, TaskStatus.RUNNING)

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

        verify_data_files_exists(request, dir_external)
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

    except Exception as e:
        task_logger.error(
            f"Error in pipeline for task {task.id}: {str(e)}", exc_info=True
        )
        task.status = TaskStatus.FAILED
        task.completed_at = datetime.now()
        with create_session() as session:
            task_db = session.get(TaskResults, task.id)
            if task_db:
                task_db.sqlmodel_update(task.model_dump(exclude_unset=True))
                session.add(task_db)
                session.commit()
                session.refresh(task_db)
        task_logger.info(f"Pipeline task {task.id} marked as failed")


# -----------------------------
# Trigger function
# -----------------------------
def start_pipeline(request: PipelineRequest, task: TaskResults):
    """Start the pipeline in a separate process"""
    logger.info(f"Triggering pipeline for task {task.id}")
    # Submit to process pool and immediately return
    executor.submit(run_pipeline, request, task)
    logger.debug(f"Task {task.id} was submitted sucesssfully")
