"""
Task repository for managing TaskResults lifecycle and persistence.
"""

import logging
import threading
from datetime import datetime, timedelta

from constants import TaskStatus
from core.config import get_settings
from database import create_session
from errors import PipelineCapacityExceededError
from models.models import TaskResults
from sqlmodel import select

# Global mutex for task creation
task_creation_mutex = threading.Lock()

logger = logging.getLogger(__name__)
settings = get_settings()


class TaskRepository:
    """Repository for TaskResults management with circular buffer logic."""

    @staticmethod
    def create_or_reuse_slot(external_id: str) -> TaskResults:
        """Create new task or reuse oldest eligible completed task slot."""
        with task_creation_mutex:  # Atomic section
            with create_session() as session:
                max_limit = settings.PIPELINE_MAX_RESULTS
                min_retention_minutes = settings.PIPELINE_MIN_RESULT_RETENTION_MINUTES

                total_count = len(session.exec(select(TaskResults)).all())

                if total_count < max_limit:
                    # Still have room - create new task
                    task = TaskResults(external_id=external_id)
                    session.add(task)
                    session.commit()
                    session.refresh(task)
                    logger.info(
                        f"Created new task {task.id} for external_id {external_id}"
                    )
                    return task

                # At limit - find oldest completed task that can be reused
                min_completed_time = datetime.now() - timedelta(
                    minutes=min_retention_minutes
                )

                statement = (
                    select(TaskResults)
                    .where(
                        TaskResults.status.in_(
                            [TaskStatus.COMPLETED, TaskStatus.FAILED]
                        ),
                        TaskResults.completed_at <= min_completed_time,
                    )
                    .order_by(TaskResults.completed_at)
                )

                oldest_completed = session.exec(statement).first()

                if not oldest_completed:
                    # No reusable tasks available - capacity exceeded
                    logger.warning(
                        "Pipeline capacity exceeded: no reusable task slots available"
                    )
                    raise PipelineCapacityExceededError(
                        f"Pipeline capacity exceeded. All {max_limit} slots are busy or results are too recent to override."
                    )

                # Override the oldest eligible completed task
                old_task_id = oldest_completed.id
                old_completed_at = oldest_completed.completed_at
                oldest_completed.external_id = external_id
                oldest_completed.status = TaskStatus.PENDING
                oldest_completed.created_at = datetime.now()
                oldest_completed.completed_at = None
                # Clear old results
                oldest_completed.ror_values = []
                oldest_completed.ror_lower = []
                oldest_completed.ror_upper = []

                session.commit()
                session.refresh(oldest_completed)
                logger.info(
                    f"Reused task slot {old_task_id} (was completed {old_completed_at}) for external_id {external_id}"
                )
                return oldest_completed

    @staticmethod
    def update_status(task: TaskResults, status: TaskStatus):
        """Update task status and timestamps."""
        if status == TaskStatus.COMPLETED or status == TaskStatus.FAILED:
            task.completed_at = datetime.now()

        task.status = status

        with create_session() as session:
            task_db = session.get(TaskResults, task.id)
            if task_db:
                task_db.sqlmodel_update(task.model_dump(exclude_unset=True))
                session.add(task_db)
                session.commit()
                session.refresh(task_db)
        logger.info(f"Task {task.id} status updated to {status}")

    @staticmethod
    def save_task_results(task: TaskResults):
        """Save task results to database."""
        with create_session() as session:
            task_db = session.get(TaskResults, task.id)
            if task_db:
                task_db.sqlmodel_update(task.model_dump(exclude_unset=True))
                session.add(task_db)
                session.commit()
                session.refresh(task_db)
        logger.info(f"Results for task {task.id} saved to database")
