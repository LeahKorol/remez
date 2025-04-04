import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest
from analysis.faers_analysis.src.utils import (
    normalize_string,
    empty_to_none,
    validate_event_dt_num,
    normalize_dataframe,
)


class TestHelpers:
    @pytest.mark.parametrize(
        "val, expected",
        [
            ("  hello ", "hello"),
            ("\tHeLLo! ", "hello"),
            ("###HELLO!!", "hello"),
            ("   ", None),
            ("", None),
            (None, None),
        ],
    )
    def test_normalize_string_lower(self, val, expected):
        assert normalize_string(val, lower=True) == expected

    @pytest.mark.parametrize(
        "val, expected",
        [
            ("  abc123 ", "ABC123"),
            ("@@@TEST###", "TEST"),
            ("", None),
            (None, None),
        ],
    )
    def test_normalize_string_upper(self, val, expected):
        assert normalize_string(val, lower=False) == expected

    @pytest.mark.parametrize(
        "val, expected",
        [
            (np.nan, None),
            ("", None),
            (" ", None),
            ("abc", "abc"),
            (123, 123),
        ],
    )
    def test_empty_to_none(self, val, expected):
        assert empty_to_none(val) == expected

    @pytest.mark.parametrize(
        "s, expected",
        [
            ("1/2/2020", True),
            ("01/02/2020", True),
            ("12/31/1999", True),
            ("13/1/2020", False),  # Invalid month
            ("2/30/2020", True),  # Pattern is valid, even if date isn't real
            ("2-2-2020", False),
            ("2020/2/2", False),
        ],
    )
    def test_validate_event_dt_num(self, s, expected):
        assert validate_event_dt_num(s) is expected

    def test_normalize_dataframe(self):
        df = pd.DataFrame(
            {
                "age": [25, None, 35],
                "sex": ["M", None, "F"],
            }
        )

        column_types = {
            "age": "float64",  # pandas assigns float64 to columns with NaN values
            "sex": "string",
        }

        normalize_dataframe(df, column_types)

        # Check types
        assert df["age"].dtype == "float64" 
        assert df["sex"].dtype.name == "string"

        # Check age column: non-string columns converts None to NaN
        pdt.assert_series_equal(df["age"], pd.Series([25, np.nan, 35], name="age"))

        # Check sex column: string column converts None to empty string
        assert df["sex"].tolist() == ["M", "", "F"]
