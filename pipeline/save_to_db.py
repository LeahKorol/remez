import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, Union

from utils import get_ror_fields

logger = logging.getLogger("FAERS")


def update_query_fields(
    fields: Dict[str, Any], query_id: int, db_path: str = "results.sqlite3"
) -> None:
    """Update query fields in the SQLite3 database."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS queries (
        id INTEGER PRIMARY KEY,
        data TEXT,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Check if record exists
    cursor.execute("SELECT id FROM queries WHERE id = ?", (query_id,))
    exists = cursor.fetchone()

    # Insert or update record
    if exists:
        cursor.execute(
            "UPDATE queries SET data = ?, status = ? WHERE id = ?",
            (json.dumps(fields), fields.get("status", "completed"), query_id),
        )
    else:
        cursor.execute(
            "INSERT INTO queries (id, data, status) VALUES (?, ?, ?)",
            (query_id, json.dumps(fields), fields.get("status", "completed")),
        )

    conn.commit()
    conn.close()


def save_ror_values(results_file: Union[str, Path], query_id: int) -> None:
    """Save ROR values to SQLite3 database and mark query as completed."""
    try:
        fields = get_ror_fields(results_file)
        logger.debug(f"Saving these fields to SQLite3 db:\n{fields}")
        fields["status"] = "completed"
        update_query_fields(fields, query_id)

    except ValueError as e:
        # Update status to failed if ROR extraction fails
        error_fields = {"status": "failed", "error": str(e)}
        update_query_fields(error_fields, query_id)
        logger.error(f"Error saving results to SQLite3 db: {str(e)}")
        raise
