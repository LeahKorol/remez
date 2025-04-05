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


# The years there are records about in FAERS data
YEAR_START = 2004
YEAR_END = 2025

# use 'int64' for age to handle missing values
DEMO_COLUMN_TYPES = {
    "primaryid": int,
    "caseid": int,
    "event_dt_num": "string",
    "age": "int64",
    "age_cod": "string",
    "sex": "string",
    "wt": float,
    "wt_cod": "string",
}

DEMO_COLUMNS = list(DEMO_COLUMN_TYPES.keys())

DRUG_COLUMN_TYPES = {
    "primaryid": int,
    "caseid": int,
    "drugname": "string",
}

DRUG_COLUMNS = list(DRUG_COLUMN_TYPES.keys())
