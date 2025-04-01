import pandas as pd
import pytest
from typing import Callable
from pathlib import Path

from analysis.models import Case
from analysis.faers_analysis.src.utils import Quarter
from analysis.management.commands.load_faers_data import Command


@pytest.mark.django_db
class TestCreateNewCases:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.quarter = Quarter(2025, 1)
        self.command = Command()

    def test_creates_new_cases_from_zipped_csv(
        self, create_zipped_csv: Path, tmp_path: Path
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
        result = self.command._create_new_cases(zip_path, self.quarter)

        assert Case.objects.count() == 3

        for primaryid in primary_ids:
            case = Case.objects.get(faers_primaryid=primaryid)
            assert result[primaryid] == case.id  # validate resule

            # validate case
            assert case.faers_caseid in case_ids
            assert case.year == self.quarter.year
            assert case.quarter == self.quarter.quarter

    def test_skips_existing_cases(self, create_zipped_csv: Path, tmp_path: Path):
        """Test it does not create Case records for primaryids that already exist."""
        Case.objects.create(
            faers_primaryid=101,
            faers_caseid=201,
            year=self.quarter.year,
            quarter=self.quarter.quarter,
        )

        data = pd.DataFrame(
            {
                "primaryid": [101, 102],
                "caseid": [201, 202],
            }
        )
        zip_path = create_zipped_csv(data, "demo20202q1", tmp_path)

        result = self.command._create_new_cases(zip_path, self.quarter)

        assert Case.objects.count() == 2
        assert 101 not in result
        assert 102 in result

    def test_deduplicates_primaryids_in_csv(
        self,
        create_zipped_csv: Callable[[pd.DataFrame, str, Path], Path],
        tmp_path: Path,
    ):
        """Test it deduplicates primaryids in the input CSV file before creating Cases."""
        data = pd.DataFrame(
            {
                "primaryid": [101, 101, 102],
                "caseid": [201, 201, 202],
            }
        )
        zip_path = create_zipped_csv(data, "demo2020q1", tmp_path)

        result = self.command._create_new_cases(zip_path, self.quarter)

        assert Case.objects.count() == 2
        assert 101 in result and 102 in result

        case_101 = Case.objects.get(faers_primaryid=101)
        case_102 = Case.objects.get(faers_primaryid=102)

        assert case_101.faers_caseid == 201
        assert case_102.faers_caseid == 202
