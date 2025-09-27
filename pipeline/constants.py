from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class RorFields(str, Enum):
    ROR_VALUES = "ror_values"
    ROR_LOWER = "ror_lower"
    ROR_UPPER = "ror_upper"