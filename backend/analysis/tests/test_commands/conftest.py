import pytest
from pathlib import Path
import zipfile
import pandas as pd
from typing import Callable, Dict
import io

from analysis.faers_analysis.src.utils import Quarter
from analysis.management.commands.load_faers_data import Command
from analysis.models import Case


@pytest.fixture
def create_zipped_csv() -> Callable[[pd.DataFrame, str, Path], Path]:
    def _create_zipped_csv(dataframe: pd.DataFrame, filename: str, path: Path) -> Path:
        """
        Create a temporary zipped CSV file from the given DataFrame.
        Yields the path to the zipped file.
        """
        csv_filename = f"{filename}.csv"
        csv_path = path / csv_filename
        zip_path = path / f"{csv_filename}.zip"

        dataframe.to_csv(csv_path, index=False)  # write the CSV file

        # Zip the CSV file
        with zipfile.ZipFile(zip_path, "w") as zipf:
            zipf.write(csv_path, arcname=csv_filename)

        csv_path.unlink()  # Delete the unzipped CSV

        return zip_path

    return _create_zipped_csv


# Ensure clean test output by redirecting the command outputs to a buffer
@pytest.fixture
def command():
    output = io.StringIO()
    cmd = Command(stdout=output)
    return cmd, output


@pytest.fixture
def quarter():
    return Quarter(2025, 1)


@pytest.fixture
def cases_ids(quarter: Quarter) -> Callable[[pd.DataFrame], Dict[int, int]]:
    def _cases_ids(sample_data: pd.DataFrame):
        """
        Creates sample Case objects in the database, matching primaryids of the sample data
        It intialises faers_case_id with the primary_id as well, enable consistency between models.
        """
        cases_ids = {}
        for primary_id in sample_data["primaryid"]:
            case = Case.objects.create(
                faers_primaryid=primary_id,
                faers_caseid=primary_id,
                quarter=quarter.quarter,
                year=quarter.year,
            )
            cases_ids[primary_id] = case.id
        return cases_ids

    return _cases_ids
