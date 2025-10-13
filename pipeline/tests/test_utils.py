import math

import pytest
from models import TaskResults
from utils import normalise_empty_ror_fields


class TestNormaliseEmptyRorFields:
    """Test cases for the normalise_empty_ror_fields function"""

    @pytest.mark.parametrize(
        "ror_values, ror_lower, ror_upper, expected_ror_values, expected_ror_lower, expected_ror_upper, test_description",
        [
            # Test case 1: All fields are None (should become empty lists)
            (None, None, None, [], [], [], "all_fields_none"),
            # Test case 2: All fields are [math.nan] (should become empty lists)
            ([math.nan], [math.nan], [math.nan], [], [], [], "all_fields_nan"),
            # Test case 3: Mixed None and [math.nan] (should become empty lists)
            (None, [math.nan], None, [], [], [], "mixed_none_and_nan_1"),
            ([math.nan], None, [math.nan], [], [], [], "mixed_none_and_nan_2"),
            # Test case 4: Regular float values (should remain unchanged)
            (
                [1.5, 2.3],
                [0.8, 1.2],
                [2.1, 3.4],
                [1.5, 2.3],
                [0.8, 1.2],
                [2.1, 3.4],
                "regular_float_values",
            ),
            # Test case 5: Empty lists (should remain unchanged)
            ([], [], [], [], [], [], "empty_lists"),
            # Test case 6: Mixed regular values and edge cases
            (
                [1.0, 2.0],
                None,
                [math.nan],
                [1.0, 2.0],
                [],
                [],
                "mixed_regular_and_edge_1",
            ),
            (
                None,
                [0.5, 1.5],
                [2.0, 3.0],
                [],
                [0.5, 1.5],
                [2.0, 3.0],
                "mixed_regular_and_edge_2",
            ),
            # Test case 7: Single values
            ([5.5], [4.2], [6.8], [5.5], [4.2], [6.8], "single_values"),
            # Test case 8: Zero values (should remain unchanged)
            ([0.0], [0.0], [0.0], [0.0], [0.0], [0.0], "zero_values"),
            # Test case 9: Negative values (should remain unchanged)
            ([-1.5], [-2.0], [-1.0], [-1.5], [-2.0], [-1.0], "negative_values"),
        ],
    )
    def test_normalise_empty_ror_fields(
        self,
        ror_values,
        ror_lower,
        ror_upper,
        expected_ror_values,
        expected_ror_lower,
        expected_ror_upper,
        test_description,
    ):
        """Test normalise_empty_ror_fields with various input combinations using parametrize"""
        # Create a TaskResults instance with test data
        task = TaskResults(
            external_id=f"test_task_{test_description}",
            ror_values=ror_values,
            ror_lower=ror_lower,
            ror_upper=ror_upper,
        )

        normalise_empty_ror_fields(task)

        # Assert the results
        assert task.ror_values == expected_ror_values, (
            f"ror_values: expected {expected_ror_values}, got {task.ror_values}"
        )
        assert task.ror_lower == expected_ror_lower, (
            f"ror_lower: expected {expected_ror_lower}, got {task.ror_lower}"
        )
        assert task.ror_upper == expected_ror_upper, (
            f"ror_upper: expected {expected_ror_upper}, got {task.ror_upper}"
        )
