from datetime import datetime
from typing import List

from constants import TaskStatus
from sqlmodel import JSON, Column, Field, SQLModel


class TaskBase(SQLModel):
    """Base model for pipeline tasks - returned when creating a new task"""

    id: int | None = Field(default=None, primary_key=True)
    status: TaskStatus = Field(default=TaskStatus.PENDING, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(),
        nullable=False,
        description="Task creation timestamp",
    )


class TaskResults(TaskBase, table=True):
    """Database model for storing task results"""

    __tablename__ = "tasks"

    completed_at: datetime | None = Field(default=None, nullable=True)
    ror_values: List[float] = Field(
        sa_column=Column("ror_values", JSON),
        default_factory=list,
        description="ROR values",
    )
    ror_lower: List[float] = Field(
        sa_column=Column("ror_lower", JSON),
        default_factory=list,
        description="Lower bound of ROR values",
    )
    ror_upper: List[float] = Field(
        sa_column=Column("ror_upper", JSON),
        default_factory=list,
        description="Upper bound of ROR values",
    )
