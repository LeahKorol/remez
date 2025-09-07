from pathlib import Path

import pandas as pd
import pytest

import analysis.faers_analysis.constants as const
from analysis.faers_analysis.src.mark_data import load_quarder_files
from analysis.faers_analysis.src.mark_data import main as mark_data_main
from analysis.faers_analysis.src.report import main as report_main
from analysis.faers_analysis.src.utils import Quarter
from analysis.models import Case, Demo, Drug, DrugName, Outcome, Reaction, ReactionName


def test_load_quarter_files_invalid_model_name():
    with pytest.raises(ValueError):
        load_quarder_files("invalid_model", "2023Q1")


@pytest.fixture
def quarter():
    return Quarter(2021, 2)


@pytest.fixture
@pytest.mark.django_db
def case(quarter):
    return Case.objects.create(
        faers_primaryid=111,
        faers_caseid=222,
        year=quarter.year,
        quarter=quarter.quarter,
    )


@pytest.fixture
@pytest.mark.django_db
def demo(case):
    return Demo.objects.create(
        case=case,
        event_dt_num="20210601",
        age=25,
        age_cod="YR",
        sex="M",
        wt=70.0,
        wt_cod="KG",
    )


@pytest.fixture
@pytest.mark.django_db
def drug(case):
    return Drug.objects.create(
        case=case, drug=DrugName.objects.create(name="ibuprofen")
    )


@pytest.fixture
@pytest.mark.django_db
def outcome(case):
    return Outcome.objects.create(case=case, outc_cod="DE")


@pytest.fixture
@pytest.mark.django_db
def reaction(case):
    return Reaction.objects.create(
        case=case, reaction=ReactionName.objects.create(name="nausea")
    )


@pytest.fixture
def minimal_json_config():
    # Provide a minimal valid config for mark_data
    return {
        "name": "test_config",
        "drug": ["aspirin"],
        "reaction": ["headache"],
        "control": None,
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model_fixture, model, columns, column_types",
    [
        ("demo", Demo, const.DEMO_COLUMNS, const.DEMO_COLUMN_TYPES),
        ("drug", Drug, const.DRUG_COLUMNS, const.DRUG_COLUMN_TYPES),
        ("outcome", Outcome, const.OUTCOME_COLUMNS, const.OUTCOME_COLUMN_TYPES),
        ("reaction", Reaction, const.REACTION_COLUMNS, const.REACTION_COLUMN_TYPES),
    ],
)
def test_load_quarder_files(model_fixture, model, columns, column_types, request):
    # Load test data
    request.getfixturevalue(model_fixture)

    # Pass single quarter
    quarter = Quarter(2021, 2)
    df = load_quarder_files(model, [quarter])

    # Check that returned object is a DataFrame
    assert isinstance(df, pd.DataFrame)
    assert df.shape[0] >= 1
    for col in df.columns:
        assert col in columns
        assert df[col].dtype == column_types[col]


@pytest.mark.django_db
def test_load_quarter_files_multiple_quarters(drug, case):
    """Test the reuested quarters only are returned when sending multiple quarters"""
    quarters = [Quarter(case.year + 1, 1), Quarter(case.year + 2, 3)]
    unexist_drug = DrugName.objects.create(name="unexist_drug")

    drugs = [
        Drug.objects.create(
            case=Case.objects.create(
                faers_primaryid=222,
                faers_caseid=222,
                year=quarters[0].year,
                quarter=quarters[0].quarter,
            ),
            drug=drug.drug,
        ),
        Drug.objects.create(
            case=Case.objects.create(
                faers_primaryid=333,
                faers_caseid=333,
                year=quarters[1].year,
                quarter=quarters[1].quarter,
            ),
            drug=drug.drug,
        ),
        Drug.objects.create(case=case, drug=unexist_drug),
    ]

    df = load_quarder_files(Drug, quarters)

    assert df.shape[0] == 2
    assert drugs[0].drug.name in df["drugname"].values
    assert drugs[1].drug.name in df["drugname"].values
    assert unexist_drug.name not in df["drugname"].values


@pytest.mark.django_db(transaction=True)
def test_mark_data_main(demo, drug, outcome, reaction, quarter, django_db_setup):
    """
    Test the main function to ensure it runs without errors.
    This test assumes the config files exist in the spesified directories.
    """
    year_q_from = f"{quarter.year}q{quarter.quarter}"
    year_q_to = f"{quarter.year}q{Quarter.increment(quarter).quarter}"

    mark_data_main(
        year_q_from=year_q_from,
        year_q_to=year_q_to,
        config_dir=f"{Path(__file__).resolve().parent}/output/config",
        dir_out=f"{Path(__file__).resolve().parent}/output/mark_data",
    )

    # If no exceptions are raised, the test passes
    assert True


@pytest.mark.django_db(transaction=True)
def test_mark_data_config_from_json(
    minimal_json_config,
    tmp_path,
    demo,
    drug,
    outcome,
    reaction,
    quarter,
    django_db_setup,
):
    output_dir = tmp_path
    year_q_from = f"{quarter.year}q{quarter.quarter}"
    year_q_to = f"{quarter.year}q{Quarter.increment(quarter).quarter}"
    mark_data_main(
        year_q_from=year_q_from,
        year_q_to=year_q_to,
        config_dir=None,
        json_config=minimal_json_config,
        dir_out=str(output_dir),
        threads=1,
        clean_on_failure=True,
    )
    assert (output_dir / f"{year_q_from}.pkl").exists(), (
        f"{year_q_from}.pkl was not created"
    )
    assert (output_dir / "marked_data.pkl").exists(), "marked_data.pkl was not created"


def test_mark_data_error_on_no_config(tmp_path):
    output_dir = tmp_path
    with pytest.raises(
        ValueError, match="Either config_dir or json_config must be provided"
    ):
        mark_data_main(
            year_q_from="2020q1",
            year_q_to="2020q1",
            config_dir=None,
            json_config=None,
            dir_out=str(output_dir),
            threads=1,
            clean_on_failure=True,
        )


@pytest.mark.django_db
def test_report_main(outcome):
    """
    Test the report main function to ensure it runs without errors.
    This test assumes the config files exist in the specified directories.
    """
    year_q_from = f"{outcome.case.year}q{outcome.case.quarter}"
    year_q_to = f"{outcome.case.year}q{Quarter.increment(outcome.case).quarter}"

    report_main(
        dir_marked_data=f"{Path(__file__).resolve().parent}/output/mark_data",
        year_q_from=year_q_from,
        year_q_to=year_q_to,
        config_dir=f"{Path(__file__).resolve().parent}/output/config",
        dir_reports=f"{Path(__file__).resolve().parent}/output/reports",
        output_raw_exposure_data=False,
    )

    # If no exceptions are raised, the test passes
    assert True


@pytest.mark.django_db
def test_report_main_returns_plot_data(outcome):
    """
    Test that report_main returns plot data for each config and report type when return_plot_data=True.
    Verifies the structure and content types of the returned data.
    """
    year_q_from = f"{outcome.case.year}q{outcome.case.quarter}"
    year_q_to = f"{outcome.case.year}q{Quarter.increment(outcome.case).quarter}"

    results = report_main(
        dir_marked_data=f"{Path(__file__).resolve().parent}/output/mark_data",
        year_q_from=year_q_from,
        year_q_to=year_q_to,
        config_dir=f"{Path(__file__).resolve().parent}/output/config",
        dir_reports=f"{Path(__file__).resolve().parent}/output/reports",
        output_raw_exposure_data=False,
        return_plot_data_only=True,
    )

    # Test overall structure
    assert isinstance(results, dict), "Results should be a dictionary"
    assert len(results) > 0, "Should have at least one config"

    # Test structure for each config
    for config_name, config_data in results.items():
        assert isinstance(config_name, str), "Config key should be a string"
        assert isinstance(config_data, dict), "Config data should be a dictionary"

        # Verify all report types are present
        expected_reports = {"initial_data", "stratified_lr", "stratified_lr_no_weight"}
        assert set(config_data.keys()) == expected_reports, (
            f"Missing report types for config {config_name}"
        )

        # Test data structure for each report
        for report_type, plot_data in config_data.items():
            assert isinstance(plot_data, dict), (
                f"Plot data for {config_name}.{report_type} should be a dictionary"
            )
            ror_data = plot_data["ror_data"]

            # Verify required plot data fields
            required_fields = {
                "quarters",
                "ror_values",
                "ror_lower",
                "ror_upper",
                "log10_ror",
                "log10_ror_lower",
                "log10_ror_upper",
            }
            assert set(ror_data.keys()) == required_fields, (
                f"Missing data fields in {config_name}.{report_type}"
            )

            # Verify data types and consistency
            assert isinstance(ror_data["quarters"], list), "quarters should be a list"
            assert isinstance(ror_data["ror_values"], list), (
                "ror_values should be a list"
            )

            # All arrays should have the same length
            array_length = len(ror_data["quarters"])
            for key in required_fields - {"quarters"}:
                assert len(ror_data[key]) == array_length, (
                    f"Inconsistent array length in {key} for {config_name}.{report_type}"
                )
