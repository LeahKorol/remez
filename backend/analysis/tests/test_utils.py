import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

from analysis.utils import (
    empty_to_none,
    normalize_dataframe,
    normalize_string,
    validate_event_dt_num,
)


class TestHelpers:
    @pytest.mark.parametrize(
        "val, expected",
        [
            ("hello     world", "hello world"),
            ("hello\nworld", "hello world"),
            ("hello\tworld", "hello world"),
            ("hello\rworld", "hello world"),
            ("", None),
        ],
    )
    def test_normalise_string_remove_spaces(self, val, expected):
        assert normalize_string(val, lower=True) == expected

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
            (pd.NA, None),
            (None, None),
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
            (None, False),
            ("", False),
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
            "age": "float",  # numpy assigns float to NaN values
            "sex": "string",
        }

        df = normalize_dataframe(df, column_types)

        # Check types
        assert df["age"].dtype == "float"
        assert df["sex"].dtype.name == "string"

        # Check age column: non-string columns converts None to NaN
        pdt.assert_series_equal(df["age"], pd.Series([25, np.nan, 35], name="age"))

        # Check sex column: string column converts None to pd.NA
        assert df["sex"].tolist() == ["M", pd.NA, "F"]
