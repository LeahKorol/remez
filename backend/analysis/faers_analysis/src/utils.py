"""
This file was originally copied from: https://github.com/bgbg/faers_analysis/blob/main/src/utils.py
Modified to validate and normalize FAERS data.
Added functionality starts  after marker # --- Custom Additions ---
"""

import base64
import io
import json
import logging
import os
import re
from glob import glob
from typing import Type

import numpy as np
import pandas as pd
import scipy.stats as stats

logger = logging.getLogger("FAERS")


def html_from_fig(fig, caption=None, width=None):
    figfile = io.BytesIO()
    fig.savefig(figfile, format="png")
    figfile.seek(0)  # rewind to beginning of file
    figdata_png = figfile.getvalue()  # extract string (stream of bytes)
    figdata_png = base64.b64encode(figdata_png).decode("utf8")
    if width is None:
        width = ""
    else:
        width = f'width="{width}"'
    ret = f'<figure><img src="data:image/png;base64,{figdata_png}"{width}>'
    if caption is not None:
        ret += f"<figcaption>{caption}</figcaption>"
    ret += "</figure>"
    return ret


class Quarter:
    def __init__(self, *args):
        if len(args) == 2:
            self.year = int(args[0])
            self.quarter = int(args[1])
        else:
            self.year, self.quarter = self.parse_string(args[0])

        self.__verify()

    @staticmethod
    def parse_string(s):
        m = re.search(r"^(\d\d\d\d)-?q(\d)$", s)
        if m is None:
            raise RuntimeError(
                f'Quarter definition "{s}" does not follow the format YYYYqQ'
            )
        year, quarter = m.groups()
        year = int(year)
        quarter = int(quarter)
        return (year, quarter)

    def __verify(self):
        assert 1900 < self.year < 2100
        assert self.quarter in {1, 2, 3, 4}

    def increment(self):
        year = self.year
        quarter = self.quarter
        quarter += 1
        if quarter > 4:
            quarter = 1
            year += 1
        return Quarter(year, quarter)

    def __eq__(self, other):
        if other is self:
            return True
        return (self.year == other.year) and (self.year == other.year)

    def __lt__(self, other):
        if self.year == other.year:
            return self.quarter < other.quarter
        else:
            return self.year < other.year

    def __hash__(self):
        return hash((self.year, self.quarter))

    def __str__(self):
        return f"{self.year}q{self.quarter}"


def generate_quarters(start, end):
    while start < end:  # NOTE: not including *end*
        yield start
        start = start.increment()


class ContingencyMatrix:
    def __init__(self, tbl=None):
        if tbl is None or tbl.empty:
            tbl = pd.DataFrame(columns=["exposure", "outcome", "n"])
        else:
            if tbl.shape == (2, 2):
                try:
                    tbl = (
                        pd.melt(
                            tbl.reset_index().fillna(0),
                            id_vars=["exposure"],
                            value_vars=[False, True],
                            value_name="n",
                        )
                        .set_index(["exposure", "outcome"])
                        .sort_index()
                    )
                except:
                    tbl = pd.DataFrame(columns=["exposure", "outcome", "n"])
            else:
                for c in ["exposure", "outcome", "n"]:
                    assert c in tbl.columns
                for c in ["exposure", "outcome"]:
                    tbl[c] = tbl[c].astype(bool)
                tbl = tbl.set_index(["exposure", "outcome"]).sort_index()
                for expo in (True, False):
                    for outcome in (True, False):
                        pair = (expo, outcome)
                        if pair not in tbl.index:
                            row = pd.Series({"n": 0}, name=pair)
                            tbl = tbl.append(row)
        self.tbl = tbl.sort_index()

    def __add__(self, other):
        self.tbl.n += other.tbl.n
        return self

    @classmethod
    def from_results_table(cls, data, config):
        exposure = data[f"exposed {config.name}"]
        exposure.name = "exposure"
        outcome = data[f"reacted {config.name}"]
        outcome.name = "outcome"
        crosstab = (
            pd.crosstab(exposure, outcome)
            .reindex([False, True], axis=0, fill_value=0)
            .reindex([False, True], axis=1, fill_value=0)
        )
        return ContingencyMatrix(crosstab)

    def get_count_value(self, exposure, outcome):
        ret = self.tbl.loc[(exposure, outcome)]["n"]
        return ret

    def ror_components(self, smoothing=0):
        # Smoothing is mentioned here https://pdfs.semanticscholar.org/9639/66a1e9ee60bfcdb13a1a98527022c7cc59ba.pdf
        a = self.get_count_value(True, True)
        b = self.get_count_value(True, False)
        c = self.get_count_value(False, True)
        d = self.get_count_value(False, False)
        assert a + b + c + d == self.tbl.n.sum()
        if smoothing < 0:
            smoothing = 1 / self.tbl.n.sum()
        return (a + smoothing, b + smoothing, c + smoothing, d + smoothing)

    def ror(self, alpha=0.05, smoothing=0):
        # https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2938757/
        a, b, c, d = self.ror_components(smoothing=smoothing)
        nominator = a * c
        denominator = b * c
        if denominator:
            ror = (a * d) / (b * c)
        else:
            ror = np.nan
        if alpha is not None:
            if np.all(np.array([a, b, c, d], dtype=bool)):
                # eq 2 from https://arxiv.org/pdf/1307.1078.pdf
                ln_ror = np.log(ror)
                standard_error_ln_ror = np.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
                interval = np.multiply(
                    stats.distributions.norm.interval(1 - alpha), standard_error_ln_ror
                )
                ci_ln_ror = ln_ror + interval
                ci = tuple(np.exp(ci_ln_ror))
            else:
                ci = (np.nan, np.nan)
            return ror, ci
        else:
            return ror

    def crosstab(self):
        ret = self.tbl.pivot_table(
            values="n", index="exposure", columns="outcome", aggfunc="sum"
        )
        return ret

    def __str__(self):
        ret = "Contingency matrix\n" + str(self.tbl)
        return ret

    def __repr__(self):
        return self.__str__()


class QuestionConfig:
    def __init__(self, name, drugs, reactions, control):
        self.name = name
        self.drugs = drugs
        self.reactions = reactions
        self.control = control

    @classmethod
    def load_config_items(cls, dir_config):
        ret = []
        for f in sorted(glob(os.path.join(dir_config, "*.json"))):
            ret.append(cls.config_from_json_file(f))

        for f in glob(os.path.join(dir_config, "[a-zA-Z0-9_]*.xls?")):
            ret.extend(cls.configs_from_excel_file(f))
        return ret

    @staticmethod
    def normalize_reaction_name(r):
        return r.strip().lower()

    @staticmethod
    def normalize_drug_name(d):
        ret = d.strip().lower()
        if ret.endswith("."):
            ret = ret[:-1]
        return ret

    @classmethod
    def config_from_json_file(cls, fn):
        name = os.path.split(fn)[-1].replace(".json", "")
        config = json.load(open(fn))
        drugs = [cls.normalize_drug_name(d) for d in config["drug"]]
        reactions = [cls.normalize_reaction_name(r) for r in config["reaction"]]
        if "control" in config:
            control = [cls.normalize_drug_name(d) for d in config["control"]]
        else:
            control = None
        return QuestionConfig(name, drugs=drugs, reactions=reactions, control=control)

    @classmethod
    def configs_from_excel_file(cls, fn):
        name = os.path.splitext(os.path.split(fn)[-1])[0]
        xl = pd.ExcelFile(fn)
        ret = []
        for sheetname in xl.sheet_names:
            tbl = xl.parse(sheetname)
            tbl.columns = [c.lower().strip() for c in tbl.columns]
            if len(tbl.columns) > 3:
                logger.warning(
                    f"Skipping {fn} sheet {sheetname} that has {len(tbl.columns)} columns"
                )
                continue
            drugs = tbl["drug"].dropna().tolist()
            reactions = tbl["reaction"].dropna().tolist()
            drugs = [cls.normalize_drug_name(d) for d in drugs]
            reactions = [cls.normalize_reaction_name(r) for r in reactions]
            if len(tbl.columns) == 3:
                control = [
                    cls.normalize_drug_name(d) for d in tbl["control"].dropna().tolist()
                ]
            else:
                control = None
            ret.append(
                QuestionConfig(
                    f"{name} - {sheetname}",
                    drugs=drugs,
                    reactions=reactions,
                    control=control,
                )
            )
        return ret

    @classmethod
    def config_from_json_object(cls, json_object):
        """
        Create a QuestionConfig instance from a JSON object.
        The JSON object should have 'name', 'drug', 'reaction', and optionally 'control' keys.
        """
        logging.debug(f"Creating QuestionConfig from JSON object: {json_object}")
        name = json_object["name"]
        drugs = [cls.normalize_drug_name(d) for d in json_object["drug"]]
        reactions = [cls.normalize_reaction_name(r) for r in json_object["reaction"]]
        control = (
            [cls.normalize_drug_name(d) for d in json_object.get("control", [])]
            if "control" in json_object and json_object["control"]
            else None
        )
        logging.debug(
            f"Created QuestionConfig: {name}, Drugs: {drugs}, Reactions: {reactions}, Control: {control}"
        )
        return cls(name, drugs=drugs, reactions=reactions, control=control)

    def filename_from_config(self, directory, extension=".csv"):
        if extension:
            assert extension.startswith(".")
        config_name = self.name
        return os.path.join(directory, f"{config_name}{extension}")

    def __repr__(self):
        return repr(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


def process_demo_data(df_demo, **kwargs):
    """ "This function was modified from read_demo_data"""
    to_year_conversion_factor = {
        "YR": 1.0,
        "DY": 365.25,
        "MON": 12,
        "DEC": 0.1,
        "WK": 52.2,
        "HR": 24 * 365.25,
    }
    to_year_conversion_factor = pd.Series(to_year_conversion_factor)

    to_kg_conversion_factor = {"KG": 1.0, "LBS": 2.20462}
    to_kg_conversion_factor = pd.Series(to_kg_conversion_factor)
    df_demo.wt = (
        df_demo.wt / to_kg_conversion_factor.reindex(df_demo.wt_cod.values).values
    )
    df_demo.age = (
        df_demo.age / to_year_conversion_factor.reindex(df_demo.age_cod.values).values
    )
    df_demo["event_date"] = pd.to_datetime(
        df_demo.event_dt_num, dayfirst=False, errors="ignore"
    )
    df_demo.drop(["age_cod", "wt_cod", "event_dt_num"], axis=1, inplace=True)
    return df_demo


def compute_df_uniqueness(df, cols=None, do_print=False, print_prefix=None):
    if do_print and print_prefix is None:
        print_prefix = ""
    n_total = len(df)
    n_unique = len(df.drop_duplicates(subset=cols))
    n_unique, n_total
    frac_unique = n_unique / n_total
    if do_print:
        print(
            f"{print_prefix}Of {n_total:6,d} entries {n_unique:6,d} are unique ({frac_unique * 100:.1f}%)"
        )
    return frac_unique


# --- Custom Additions ---
def validate_event_dt_num(event_dt_num: str):
    """
    Return True if the the string is in one of this format: MM/DD/YYYY, M/DD/YYYY, M/D/YYYY, MM/D/YYYY
    """
    if event_dt_num is None:
        return False
    pattern = r"^(0?[1-9]|1[0-2])/(0?[1-9]|[12][0-9]|3[01])/\d{4}$"
    return bool(re.fullmatch(pattern, event_dt_num))


def normalize_dataframe(df: pd.DataFrame, column_types: dict) -> Type[pd.DataFrame]:
    """
    Normalize a dataframe to use required types instead of 'object' type.
    - Replaces None values in numeric columns with np.nan
    - Converts each column to its specified dtype
    """
    if df is None:
        return

    for col, dtype in column_types.items():
        if dtype in ["float", "float64", "int", "int64", "int32", "float32"]:
            df[col] = df[col].replace({None: np.nan})

    # Convert each column to its specified dtype
    astype_map = {col: dtype for col, dtype in column_types.items()}
    df = df.astype(dtype=astype_map)

    return df


def empty_to_none(val):
    """
    Return None if val is None, pd.NA, np.nan or an empty string, otherwise return the val
    """
    if val is None:
        return None
    # Return None if val is pd.NA or np.nan
    if pd.isna(val):
        return None
    if isinstance(val, str) and val.strip() == "":
        return None
    return val


def normalize_string(s: str, lower=True) -> str:
    """
    Cleans a string by:
    - Stripping whitespace and replacing multiple spaces with a single space
    - Converting to lowercase if lower==True, else to uppercase
    - Trimming non-alphanumeric characters from the start and end (excluding brackets)

    Returns:
        A normalized string, or None if the result has no alphanumeric content.
    """
    if s is None:
        return None

    # Strip whitespace and replace multiple spaces with a single space
    s = " ".join(s.split())
    if lower:
        s = s.lower()
    else:
        s = s.upper()

    start, end = 0, len(s) - 1

    while start < end and not s[start].isalnum() and s[start] not in ["(", "[", "{"]:
        start += 1

    while end > start and not s[end].isalnum() and s[end] not in [")", "]", "}"]:
        end -= 1

    if start <= end:
        return s[start : end + 1]
    return None
