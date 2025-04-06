import pandas as pd
import pytest
from typing import Callable, Type
from pathlib import Path
from django.db.models import F, Model


from analysis.models import Case, Demo, Drug, DrugName, Outcome, Reaction, ReactionName
from analysis.faers_analysis import constants as const
from analysis.faers_analysis.src.utils import normalize_dataframe


@pytest.mark.django_db
class TestCreateNewCases:
    def test_creates_new_cases_from_zipped_csv(
        self, create_zipped_csv: Path, tmp_path: Path, quarter, command
    ):
        """Test it creates new Case records from a zipped CSV file."""
        primary_ids = [101, 102, 103]
        case_ids = [201, 202, 203]
        data = pd.DataFrame(
            {
                "primaryid": primary_ids,
                "caseid": case_ids,
            }
        )
        zip_path = create_zipped_csv(data, "demo2020q1", tmp_path)
        # maps faers_primaryid to case.id
        cmd, _ = command
        result = cmd._create_new_cases(zip_path, quarter)

        assert Case.objects.count() == 3

        for primaryid in primary_ids:
            case = Case.objects.get(faers_primaryid=primaryid)
            assert result[primaryid] == case.id  # validate resule

            # validate case
            assert case.faers_caseid in case_ids
            assert case.year == quarter.year
            assert case.quarter == quarter.quarter

    def test_skips_existing_cases(
        self, create_zipped_csv: Path, tmp_path: Path, quarter, command
    ):
        """Test it does not create Case records for primaryids that already exist."""
        Case.objects.create(
            faers_primaryid=101,
            faers_caseid=201,
            year=quarter.year,
            quarter=quarter.quarter,
        )

        data = pd.DataFrame(
            {
                "primaryid": [101, 102],
                "caseid": [201, 202],
            }
        )
        zip_path = create_zipped_csv(data, "demo20202q1", tmp_path)
        cmd, _ = command
        result = cmd._create_new_cases(zip_path, quarter)

        assert Case.objects.count() == 2
        assert 101 not in result
        assert 102 in result

    def test_deduplicates_primaryids_in_csv(
        self,
        create_zipped_csv: Callable[[pd.DataFrame, str, Path], Path],
        tmp_path: Path,
        quarter,
        command,
    ):
        """Test it deduplicates primaryids in the input CSV file before creating Cases."""
        data = pd.DataFrame(
            {
                "primaryid": [101, 101, 102],
                "caseid": [201, 201, 202],
            }
        )
        zip_path = create_zipped_csv(data, "demo2020q1", tmp_path)
        cmd, _ = command
        result = cmd._create_new_cases(zip_path, quarter)

        assert Case.objects.count() == 2
        assert 101 in result and 102 in result

        case_101 = Case.objects.get(faers_primaryid=101)
        case_102 = Case.objects.get(faers_primaryid=102)

        assert case_101.faers_caseid == 201
        assert case_102.faers_caseid == 202


@pytest.fixture
def demo_data():
    """Provides sample demographic data as a DataFrame."""
    data = {
        "primaryid": [1, 2],
        "caseid": [1, 2],
        "event_dt_num": ["8/01/2020", "1/01/2020"],
        "age": [25, 30],
        "age_cod": ["YR", "YR"],
        "sex": ["M", "F"],
        "wt": [70, 60],
        "wt_cod": ["KG", "KG"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def drug_data():
    """Provides sample drug data as a DataFrame."""
    drugnames = ["aspirin", "tylenol"]
    for drug in drugnames:
        DrugName.objects.create(name=drug)

    data = {
        "primaryid": [1, 2],
        "caseid": [1, 2],
        "drugname": drugnames,
    }
    return pd.DataFrame(data)


@pytest.fixture
def outcome_data():
    """Provides sample outcome data as a DataFrame."""
    data = {
        "primaryid": [1, 2],
        "caseid": [1, 2],
        "outc_cod": ["DE", "LT"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def reaction_data():
    """Provides sample reaction data as a DataFrame."""
    reactions = ["reaction1", "reaction2"]
    for reaction in reactions:
        ReactionName.objects.create(name=reaction)

    data = {
        "primaryid": [1, 2],
        "caseid": [1, 2],
        "pt": reactions,
    }
    return pd.DataFrame(data)


@pytest.fixture
def term_data(request):
    """
    Return the right <term>_data fixture for function test_load_term_data_correct_objects
    """
    return request.getfixturevalue(request.param)


def get_stored_values(model: Type[Model]):
    """
    Return all the stored values of the model as dictionaries.
    Each dict represents a row from the database
    """
    if model == Drug:
        # Get stored values, rename 'drug__name' to 'drugname' and reconstruct DataFrame
        stored_values = (
            Drug.objects.all()
            .annotate(drugname=F("drug__name"))
            .values("primaryid", "caseid", "drugname")
        )
    elif model == Reaction:
        # Get stored values, rename 'reaction__name' to 'pt' and reconstruct DataFrame
        stored_values = (
            Reaction.objects.all()
            .annotate(pt=F("reaction__name"))
            .values("primaryid", "caseid", "pt")
        )
    else:
        stored_values = model.objects.all().values()
    return stored_values


@pytest.mark.parametrize(
    "term_name, model, columns, column_types, term_data, to_lower",
    [
        (
            "demo",
            Demo,
            const.DEMO_COLUMNS,
            const.DEMO_COLUMN_TYPES,
            "demo_data",
            False,
        ),
        (
            "drug",
            Drug,
            const.DRUG_COLUMNS,
            const.DRUG_COLUMN_TYPES,
            "drug_data",
            True,
        ),
        (
            "outcome",
            Outcome,
            const.OUTCOME_COLUMNS,
            const.OUTCOME_COLUMN_TYPES,
            "outcome_data",
            False,
        ),
        (
            "reaction",
            Reaction,
            const.RECTION_COLUMNS,
            const.REACTION_COLUMN_TYPES,
            "reaction_data",
            True,
        ),
    ],
    indirect=["term_data"],
)
@pytest.mark.django_db
def test_load_term_data_correct_objects(
    term_name,
    model,
    columns,
    column_types,
    term_data,
    to_lower,
    create_zipped_csv,
    tmp_path,
    cases_ids,
    command,
):
    """
    Test that term objects are created correctly
    """
    zip_path = create_zipped_csv(term_data, f"{term_name}2020q1", tmp_path)
    custom_case_ids = cases_ids(term_data)

    cmd, _ = command
    cmd._load_term_data(
        zip_path, custom_case_ids, model, columns, column_types, to_lower
    )

    stored_values = get_stored_values(model)
    stored_data = pd.DataFrame.from_records(stored_values)

    # Normalize and compare
    stored_data = normalize_dataframe(stored_data, column_types)

    for col, dtype in column_types.items():
        term_data[col] = term_data[col].astype(dtype)
        assert stored_data[col].equals(
            term_data[col]
        ), f"Mismatch in column '{col}':\nExpected:\n{term_data[col].to_string()}\nGot:\n{stored_data[col].to_string()}"


@pytest.mark.django_db
class TestDemo:
    def test_load_term_data_stdout_messages(
        self, demo_data, cases_ids, create_zipped_csv, tmp_path, command
    ):
        zip_path = create_zipped_csv(demo_data, "demo2020q1", tmp_path)
        custom_cases_ids = cases_ids(demo_data)

        cmd, output = command
        cmd._load_term_data(
            zip_path,
            custom_cases_ids,
            Demo,
            const.DEMO_COLUMNS,
            const.DEMO_COLUMN_TYPES,
            False,
        )

        assert (
            output.getvalue()
            == f"Loading Demo data from {zip_path}...\nLoaded 2 Demo records from file {zip_path}\n"
        )

    def test_load_term_data_strips_whitespace(
        self, demo_data, create_zipped_csv, tmp_path, cases_ids, command
    ):
        # Add leading/trailing spaces to text fields
        demo_data["age_cod"] = demo_data["age_cod"].apply(lambda x: f" {x} ")
        demo_data["event_dt_num"] = demo_data["event_dt_num"].apply(lambda x: f" {x} ")
        demo_data["sex"] = demo_data["sex"].apply(lambda x: f"\t{x} \n")
        demo_data["wt_cod"] = demo_data["wt_cod"].apply(lambda x: f"{x}  ")

        zip_path = create_zipped_csv(demo_data, "demo2020q1", tmp_path)
        custom_cases_ids = cases_ids(demo_data)

        cmd, _ = command
        cmd._load_term_data(
            zip_path,
            custom_cases_ids,
            Demo,
            const.DEMO_COLUMNS,
            const.DEMO_COLUMN_TYPES,
            False,
        )

        # Get stored values and reconstruct DataFrame
        stored_values = Demo.objects.all().values()
        stored_data = pd.DataFrame.from_records(stored_values)

        # Strip demo_data manually for expected comparison
        str_cols = [
            col for col, dtype in const.DEMO_COLUMN_TYPES.items() if dtype == "string"
        ]
        for col in str_cols:
            demo_data[col] = demo_data[col].str.strip()

        # Normalise stored data for expected comparison
        stored_data = normalize_dataframe(stored_data, const.DEMO_COLUMN_TYPES)

        # Match dtypes before comparing
        for col, dtype in const.DEMO_COLUMN_TYPES.items():
            demo_data[col] = demo_data[col].astype(dtype)
            assert stored_data[col].equals(
                demo_data[col]
            ), f"Mismatch in column '{col}, {demo_data[col].to_string()}, {stored_data[col].to_string()}'"

    def test_demo_fields_are_uppercased(
        self, demo_data, create_zipped_csv, tmp_path, cases_ids, command
    ):
        """
        Ensure that clean_row applies uppercasing to all string fields.
        """
        demo_data["sex"] = "f"
        demo_data["age_cod"] = "yr"
        demo_data["wt_cod"] = "kg"

        zip_path = create_zipped_csv(demo_data, "demo2020q1", tmp_path)
        custom_cases_ids = cases_ids(demo_data)

        cmd, _ = command
        cmd._load_term_data(
            zip_path,
            custom_cases_ids,
            Demo,
            const.DEMO_COLUMNS,
            const.DEMO_COLUMN_TYPES,
            False,
        )

        demos = Demo.objects.all()

        for demo in demos:
            assert demo.sex == "F"
            assert demo.age_cod == "YR"
            assert demo.wt_cod == "KG"

    def test_demo_fields_accept_nulls(
        self, demo_data, create_zipped_csv, tmp_path, cases_ids, command
    ):
        """
        Ensure all nullable fields correctly store None in the database.
        """
        custom_cases_ids = cases_ids(demo_data)
        # Get the first custom case ID from the dictionary
        custom_case_id = next(iter(custom_cases_ids.items()))

        # Create a demo object with None values for nullable fields
        demo_data["event_dt_num"] = None
        demo_data["age"] = None
        demo_data["age_cod"] = None
        demo_data["sex"] = None
        demo_data["wt"] = None
        demo_data["wt_cod"] = None

        zip_path = create_zipped_csv(demo_data.iloc[[0]], "demo2020q1", tmp_path)
        cmd, _ = command
        cmd._load_term_data(
            zip_path,
            {custom_case_id[0]: custom_case_id[1]},
            Demo,
            const.DEMO_COLUMNS,
            const.DEMO_COLUMN_TYPES,
            False,
        )

        fetched = Demo.objects.get(case_id=custom_case_id[1])

        assert fetched.event_dt_num is None
        assert fetched.age is None
        assert fetched.age_cod is None
        assert fetched.sex is None
        assert fetched.wt is None
        assert fetched.wt_cod is None


@pytest.mark.django_db
class TestDrug:
    def test_load_term_data_stdout_messages(
        self, drug_data, cases_ids, create_zipped_csv, tmp_path, command
    ):
        """Test stdout messages during drug data loading."""
        zip_path = create_zipped_csv(drug_data, "drug2020q1", tmp_path)
        custom_cases_ids = cases_ids(drug_data)

        cmd, output = command
        cmd._load_term_data(
            zip_path,
            custom_cases_ids,
            Drug,
            const.DRUG_COLUMNS,
            const.DRUG_COLUMN_TYPES,
            True,
        )

        assert (
            output.getvalue()
            == f"Loading Drug data from {zip_path}...\nLoaded 2 Drug records from file {zip_path}\n"
        )

    def test_load_term_data_strips_whitespace(
        self, drug_data, create_zipped_csv, tmp_path, cases_ids, command
    ):
        """Test that whitespace is stripped from drug names, so the drug name can be found in the DrugName table"""
        # Add whitespace to drug names
        drug_data["drugname"] = drug_data["drugname"].apply(lambda x: f" {x} \n")

        zip_path = create_zipped_csv(drug_data, "drug2020q1", tmp_path)
        custom_cases_ids = cases_ids(drug_data)

        cmd, _ = command
        cmd._load_term_data(
            zip_path,
            custom_cases_ids,
            Drug,
            const.DRUG_COLUMNS,
            const.DRUG_COLUMN_TYPES,
            True,
        )

        # Check that 2 drugs were created - the whitespace was striped
        assert Drug.objects.count() == 2

    def test_load_term_data_skips_non_existing_cases(
        self, drug_data, create_zipped_csv, tmp_path, command
    ):
        """Test that drugs for non-existing cases are skipped."""
        zip_path = create_zipped_csv(drug_data, "drug2020q1", tmp_path)
        # Empty cases_ids dictionary - should skip all records
        custom_cases_ids = {}

        cmd, _ = command
        cmd._load_term_data(
            zip_path,
            custom_cases_ids,
            Drug,
            const.DRUG_COLUMNS,
            const.DRUG_COLUMN_TYPES,
            True,
        )

        assert Drug.objects.count() == 0
