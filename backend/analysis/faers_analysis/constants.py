from enum import Enum
from typing import List


class FaersTerms(Enum):
    DEMO = "demo"
    DRUG = "drug"
    OUTCOME = "outc"
    REACTION = "reac"

    @classmethod
    def values(cls) -> List[str]:
        return [term.value for term in cls]
