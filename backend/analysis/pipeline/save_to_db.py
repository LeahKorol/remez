from typing import Dict, Any, Union
from pathlib import Path
from analysis.models import Query
import logging
from utils import get_ror_fields

logger = logging.getLogger("FAERS")


def update_query_fields(fields: Dict[str, Any], query_id: int) -> None:
    """Update query fields in the database.
    """
    Query.objects.filter(id=query_id).update(**fields)


def save_ror_values(results_file: Union[str, Path], query_id: int) -> None:
    """Save ROR values to database and mark query as completed.
    """
    try:
        fields = get_ror_fields(results_file)
        logger.debug(f"Saving these fileds to db:\n{fields}")
        # fields["status"] = "completed"
        update_query_fields(fields, query_id)
        
    except ValueError as e:
        # Update status to failed if ROR extraction fails
        # update_query_fields({"status": "failed"}, query_id)
        logger.error(f"Error saving results to db: str{(e)}")
        raise