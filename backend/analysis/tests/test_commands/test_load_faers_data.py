import pandas as pd
import pytest
from typing import Callable
from pathlib import Path
from collections import namedtuple
from django.db.models import F


from analysis.models import Case, Demo, Drug, DrugName
from analysis.faers_analysis.constants import DEMO_COLUMN_TYPES, DRUG_COLUMN_TYPES
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


@pytest.mark.django_db
class TestDemo:
    @pytest.fixture
    def demo_data(self):
        """Provides sample demographic data as a DataFrame."""
        data = {
            "primaryid": [1, 2, 3, 4, 5],
            "caseid": [1, 2, 3, 4, 5],
            "event_dt_num": [
                "8/01/2020",
                "1/01/2020",
                "9/01/2020",
                "04/06/2020",
                "3/2/2020",
            ],
            "age": [25, 30, 35, 40, 45],
            "age_cod": ["YR", "YR", "YR", "YR", "YR"],
            "sex": ["M", "F", "M", "F", "M"],
            "wt": [70, 60, 80, 75, 85],
            "wt_cod": ["KG", "KG", "KG", "KG", "KG"],
        }
        return pd.DataFrame(data)

    def test_load_demo_data_stdout_messages(
        self, demo_data, cases_ids, create_zipped_csv, tmp_path, command
    ):
        zip_path = create_zipped_csv(demo_data, "demo2020q1", tmp_path)
        custom_cases_ids = cases_ids(demo_data)

        cmd, output = command
        cmd._load_demo_data(zip_path, custom_cases_ids)

        assert (
            output.getvalue()
            == f"Loading demographic data from {zip_path}...\nLoaded 5 demographic records from file {zip_path}\n"
        )

    def test_load_demo_data_correct_demo_objects(
        self, demo_data, create_zipped_csv, tmp_path, cases_ids, command
    ):
        zip_path = create_zipped_csv(demo_data, "demo2020q1", tmp_path)
        custom_cases_ids = cases_ids(demo_data)

        cmd, _ = command
        cmd._load_demo_data(zip_path, custom_cases_ids)

        # get all the values as dictionaries. Each dict represents a row from the database
        stored_values = Demo.objects.all().values()
        stored_data = pd.DataFrame.from_records(stored_values)

        for col, dtype in DEMO_COLUMN_TYPES.items():
            stored_data[col] = stored_data[col].astype(dtype)
            demo_data[col] = demo_data[col].astype(dtype)
            assert stored_data[col].equals(demo_data[col])

    def test_load_demo_data_strips_whitespace(
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
        cmd._load_demo_data(zip_path, custom_cases_ids)

        # Get stored values and reconstruct DataFrame
        stored_values = Demo.objects.all().values()
        stored_data = pd.DataFrame.from_records(stored_values)

        # Strip demo_data manually for expected comparison
        str_cols = [
            col for col, dtype in DEMO_COLUMN_TYPES.items() if dtype == "string"
        ]
        for col in str_cols:
            demo_data[col] = demo_data[col].str.strip()

        # Normalise stored data for expected comparison
        normalize_dataframe(stored_data, DEMO_COLUMN_TYPES)

        # Match dtypes before comparing
        for col, dtype in DEMO_COLUMN_TYPES.items():
            demo_data[col] = demo_data[col].astype(dtype)
            assert stored_data[col].equals(
                demo_data[col]
            ), f"Mismatch in column '{col}, {demo_data[col].to_string()}, {stored_data[col].to_string()}'"

    def test_demo_fields_are_uppercased(self, command):
        """
        Ensure that clean_row applies uppercasing to all string fields.
        """
        # Create a named tuple as ittertuples would yield
        Row = namedtuple(
            "Row",
            [
                "primaryid",
                "caseid",
                "age",
                "age_cod",
                "sex",
                "wt",
                "wt_cod",
                "event_dt_num",
            ],
        )
        row = Row(1, 1, 30, "  yr ", " m ", 70, " kg ", "1/2/2020")

        cmd, _ = command
        cleaned = cmd._clean_row(row=row, lower=False)

        assert cleaned["age_cod"] == "YR"
        assert cleaned["sex"] == "M"
        assert cleaned["wt_cod"] == "KG"

    def test_demo_fields_accept_nulls(self, cases_ids, demo_data):
        """
        Ensure all nullable fields correctly store None in the database.
        """
        custom_cases_ids = cases_ids(demo_data)
        _, case_id = next(iter(custom_cases_ids.items()))

        demo = Demo.objects.create(
            case_id=case_id,
            event_dt_num=None,
            age=None,
            age_cod=None,
            sex=None,
            wt=None,
            wt_cod=None,
        )

        fetched = Demo.objects.get(id=demo.id)

        assert fetched.event_dt_num is None
        assert fetched.age is None
        assert fetched.age_cod is None
        assert fetched.sex is None
        assert fetched.wt is None
        assert fetched.wt_cod is None


@pytest.mark.django_db
class TestDrug:
    @pytest.fixture
    def drug_data(self):
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

    def test_load_drug_data_stdout_messages(
        self, drug_data, cases_ids, create_zipped_csv, tmp_path, command
    ):
        """Test stdout messages during drug data loading."""
        zip_path = create_zipped_csv(drug_data, "drug2020q1", tmp_path)
        custom_cases_ids = cases_ids(drug_data)

        cmd, output = command
        cmd._load_drug_data(zip_path, custom_cases_ids)

        assert (
            output.getvalue()
            == f"Loading drug data from {zip_path}...\nLoaded 2 drug records from file {zip_path}\n"
        )

    def test_load_drug_data_correct_drug_objects(
        self, drug_data, create_zipped_csv, tmp_path, cases_ids, command
    ):
        """Test that drug objects are created correctly."""
        zip_path = create_zipped_csv(drug_data, "drug2020q1", tmp_path)
        custom_cases_ids = cases_ids(drug_data)

        cmd, _ = command
        cmd._load_drug_data(zip_path, custom_cases_ids)

        # Get stored values, rename 'drug__name' to 'drugname' and reconstruct DataFrame
        stored_values = (
            Drug.objects.all()
            .annotate(drugname=F("drug__name"))
            .values("primaryid", "caseid", "drugname")
        )
        stored_data = pd.DataFrame.from_records(stored_values)

        # Normalise stored data for expected comparison
        normalize_dataframe(stored_data, DRUG_COLUMN_TYPES)

        # Match dtypes before comparing
        for col, dtype in DRUG_COLUMN_TYPES.items():
            drug_data[col] = drug_data[col].astype(dtype)
            assert stored_data[col].equals(
                drug_data[col]
            ), f"Mismatch in column '{col}, {drug_data[col].to_string()}, {stored_data[col].to_string()}'"

    def test_load_drug_data_strips_whitespace(
        self, drug_data, create_zipped_csv, tmp_path, cases_ids, command
    ):
        """Test that whitespace is stripped from drug names, so the drug name can be found in the DrugName table"""
        # Add whitespace to drug names
        drug_data["drugname"] = drug_data["drugname"].apply(lambda x: f" {x} \n")

        zip_path = create_zipped_csv(drug_data, "drug2020q1", tmp_path)
        custom_cases_ids = cases_ids(drug_data)

        cmd, _ = command
        cmd._load_drug_data(zip_path, custom_cases_ids)

        # Check that 2 drugs were created - the whitespace was striped
        assert Drug.objects.count() == 2

    def test_load_drug_data_skips_non_existing_cases(
        self, drug_data, create_zipped_csv, tmp_path, command
    ):
        """Test that drugs for non-existing cases are skipped."""
        zip_path = create_zipped_csv(drug_data, "drug2020q1", tmp_path)
        # Empty cases_ids dictionary - should skip all records
        custom_cases_ids = {}

        cmd, _ = command
        cmd._load_drug_data(zip_path, custom_cases_ids)

        assert Drug.objects.count() == 0
