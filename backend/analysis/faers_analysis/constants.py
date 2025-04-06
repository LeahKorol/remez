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

# Use float for age and weight to handle missing values.
# Don't use pandas nullable types, asnthese columns are converted to np arrays in the calculations
DEMO_COLUMN_TYPES = {
    "primaryid": int,
    "caseid": int,
    "event_dt_num": "string",
    "age": float,
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

OUTCOME_COLUMN_TYPES = {
    "primaryid": int,
    "caseid": int,
    "outc_cod": "string",
}

OUTCOME_COLUMNS = list(OUTCOME_COLUMN_TYPES.keys())

REACTION_COLUMN_TYPES = {
    "primaryid": int,
    "caseid": int,
    "pt": "string",  # FAERS call 'reaction' column as 'pt'
}

RECTION_COLUMNS = list(REACTION_COLUMN_TYPES.keys())
