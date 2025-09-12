import subprocess
from services.db import get_query, save_results
from pipeline.pipeline import Faers_Pipeline
import luigi
import os

# In-memory status tracking (simplest approach)
STATUS = {}

def run_pipeline(query_id: int):
    """
    Runs the pipeline for a given query ID.
    """
    STATUS[query_id] = "running"
    query = get_query(query_id)
    if not query:
        STATUS[query_id] = "not_found"
        return

    # Example: get parameters from query
    year_q_from = f"{query.year_start}q{query.quarter_start}"
    year_q_to = f"{query.year_end}q{query.quarter_end}"

    # Run Luigi pipeline
    try:
        luigi.build(
            [
                Faers_Pipeline(
                    year_q_from=year_q_from,
                    year_q_to=year_q_to
                )
            ],
            local_scheduler=True
        )
        # Optionally, retrieve results from the pipeline output
        results = {
            "ror_values": [],  # Implement actual logic
            "ror_lower": [],
            "ror_upper": []
        }
        save_results(query_id, results)
        STATUS[query_id] = "finished"
    except Exception as e:
        STATUS[query_id] = f"error: {str(e)}"

def get_status(query_id: int):
    """
    Returns the current status for a given query ID.
    """
    return {"query_id": query_id, "status": STATUS.get(query_id, "not_started")}
