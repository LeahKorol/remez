import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)


def run_luigi_pipeline(year_start, year_end, quarter_start, quarter_end, query_id):
    """
    Trigger the pipeline using subprocess
    """
    try:
        # use the same python environment as Django uses (so required libraries are available)
        python_executable = sys.executable
        project_root = settings.BASE_DIR

        # run the pipeline from the pipeline directory so imports are resolved correctly
        pipeline_dir = Path(project_root, "analysis/pipeline")

        year_q_from = f"{year_start}q{quarter_start}"
        year_q_to = f"{year_end}q{quarter_end}"

        # Python command to trigger the pipeline inside a subprocess
        python_code = f"""
import sys, os, django
sys.path.insert(0, r'{pipeline_dir}')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{settings.SETTINGS_MODULE}')
django.setup()
import luigi
from analysis.pipeline.pipeline import Faers_Pipeline
task = Faers_Pipeline(year_q_from='{year_q_from}', year_q_to='{year_q_to}', query_id={query_id}, save_results_to_db={True})
result = luigi.build([task], workers=1, local_scheduler=True, detailed_summary=True)
exit(0 if result.scheduling_succeeded else 1)
"""

        cmd = [python_executable, "-c", python_code]

        logger.info(f"Starting Luigi pipeline: {year_q_from} to {year_q_to}")

        # Create log file
        pipeline_logs_dir = getattr(settings, "PIPELINE_LOGS_DIR", "pipeline_logs")
        log_filename = f"luigi_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_file_path = Path(project_root, pipeline_logs_dir, log_filename)

        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

        with open(log_file_path, "w") as log_file:
            process = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=project_root,  # use cwd tp solve relative paths problems
            )

        logger.info(f"Luigi pipeline started with PID: {process.pid}")
        logger.info(f"Log file: {log_file_path}")

        return process.pid

    except Exception as e:
        logger.error(f"Error starting Luigi pipeline: {str(e)}")
        raise
