import pytest
import pandas as pd
from pathlib import Path

from analysis.models import Case, Demo, Drug, Outcome, Reaction, DrugName, ReactionName
import analysis.faers_analysis.constants as const
from analysis.faers_analysis.src.utils import Quarter
from analysis.faers_analysis.src.mark_data import load_quarder_files, main


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
def test_main(demo, drug, outcome, reaction, quarter, django_db_setup):
    """
    Test the main function to ensure it runs without errors.
    This test assumes the config files exist in the spesified directory.
    """
    year_q_from = f"{quarter.year}q{quarter.quarter}"
    year_q_to = f"{quarter.year}q{Quarter.increment(quarter).quarter}"

    main(
        year_q_from=year_q_from,
        year_q_to=year_q_to,
        config_dir=f"{Path(__file__).resolve().parent}/config",
        dir_out=f"{Path(__file__).resolve().parent}/output",
    )

    # If no exceptions are raised, the test passes
    assert True
