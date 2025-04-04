"""
Deduplication Approach

1. At the CSV Files Level:
   Currently, no deduplication is performed, FAERS data is supposed to be deduplicated.

2. At the Database Level:
   1. Parse the CSV to extract all primaryids.
   2. Remove rows from the CSV whose primaryids already exist in the database (effectively skipping duplicates).
   3. Load the remaining rows into the database.

   This process currently allows adding new cases only, without updating existing ones.
   Since FAERS data from previous years does not change frequently, this method is fine for now.

Optional: Allowing Updates
--------------------------
If we decide to replace or update old data for existing cases rather than skipping them, we can do so by:

1. Introducing a "--do_update" flag (e.g., an optional command-line argument).
   - If this flag is set, we can proceed with the replace/update logic below.

2. In one transaction, delete existing rows:
       DELETE FROM Case
       WHERE primaryid IN (list_of_ids_from_csv);

   All child rows in DemoCase, ReactionCase, etc., are removed automatically
   because of using ON DELETE CASCADE is enabled in their models.

3. Bulk insert the new rows from the CSV into the Case table.

This approach is useful as we want an absolute overwrite of data and do it infrequently,
ensuring the CSV holds the latest “truth.” However, deleting and reinserting
large volumes of data can be expensive, so it is not recommended to do this too often.
"""

from django.core.management.base import BaseCommand, CommandError
from pathlib import Path
from typing import List, Dict
import pandas as pd

from analysis.faers_analysis.src.utils import (
    Quarter,
    generate_quarters,
    validate_event_dt_num,
    empty_to_none,
    normalize_string,
)
from ..cli_utils import QuarterRangeArgMixin
from analysis.faers_analysis.constants import (
    FaersTerms,
    DEMO_COLUMNS,
    DEMO_COLUMN_TYPES,
)
from analysis.models import Case, Demo, Drug, Outcome, Reaction


class Command(QuarterRangeArgMixin, BaseCommand):
    TERMS = FaersTerms.values()
    CHUNK_SIZE = 1000

    def add_arguments(self, parser):
        # Add year_q_from and year_q_to
        super().add_arguments(parser)

        parser.add_argument(
            "--dir_in",
            type=str,
            help="Input directory",
        )

    def handle(self, *args, **options):
        dir_in = Path(options["dir_in"] or "analysis/management/commands/output")
        if not dir_in.exists():
            raise CommandError(f"Input directory {dir_in} does not exist")

        year_q_from = options["year_q_from"]
        year_q_to = options["year_q_to"]

        try:
            q_first = Quarter(year_q_from)
            q_last = Quarter(year_q_to)
        except RuntimeError as err:
            raise CommandError(f"Invalid quarter format: {err}")

        for q in generate_quarters(q_first, q_last):
            self.stdout.write(f"Processing quarter: {q}")
            self.load_quarter_data(dir_in, q)

    def load_quarter_data(self, dir_in: str, quarter: Quarter) -> None:
        """
        Load FAERS data for a specific quarter into the database.
        """
        term_file_paths = self._get_quarter_files(dir_in, quarter)
        demo_file_path = self._get_demo_file(term_file_paths)

        cases_ids: Dict[int, int] = self._create_new_cases(demo_file_path, quarter)

        for file_path in term_file_paths:
            if FaersTerms.DEMO.value in file_path.name:
                self._load_demo_data(file_path, cases_ids)
            elif FaersTerms.DRUG.value in file_path.name:
                self._load_drug_data(file_path)
            elif FaersTerms.REACTION.value in file_path.name:
                self._load_reaction_data(file_path)
            elif FaersTerms.OUTCOME.value in file_path.name:
                self._load_outcome_data(file_path)

    def _get_quarter_files(self, dir_in: str, quarter: Quarter) -> None:
        """
        Generate FAERS file paths for a spesific quarter.
        """
        quarteryear = str(quarter)  # YYYYqQ format
        term_file_paths = []

        for term in self.TERMS:
            file_name = f"{term}{quarteryear}.csv.zip"
            file_path = Path(dir_in) / file_name

            if not file_path.exists():
                raise CommandError(f"Required file not found: {file_path}")
            term_file_paths.append(file_path)

        return term_file_paths

    @staticmethod
    def _get_demo_file(terms_files_paths: List[Path]) -> Path:
        """Return the file whose name contains 'demo' (case-insensitive)."""
        for file in terms_files_paths:
            if FaersTerms.DEMO.value in file.name:
                print(f"File {str(file)} was found")
                return file
        raise CommandError("No file containing 'demo' found in the provided paths.")

    def _create_new_cases(
        self, demo_file_path: Path, quarter: Quarter
    ) -> Dict[int, int]:
        """
        Create new Case objects in the database for a spesific quarter
        Return a dictionary maps the faers primartids to the new cases ids
        """

        self.stdout.write(f"Build the cases of {str(quarter)}")

        # Use set for quick lookups
        existing_primaryids = set(
            Case.objects.filter(year=quarter.year, quarter=quarter.quarter).values_list(
                "faers_primaryid", flat=True
            )
        )
        new_cases = []

        # Read the whole file in one chunk to remove duplicates.
        demo_df = pd.read_csv(
            demo_file_path,
            usecols=["primaryid", "caseid"],
            dtype={"primaryid": int, "caseid": int},
        )

        # remove duplicate reports of the same case
        demo_df.drop_duplicates(subset="primaryid", inplace=True)

        for row in demo_df.itertuples(index=False):
            if row.primaryid not in existing_primaryids:
                new_cases.append(
                    Case(
                        faers_primaryid=row.primaryid,
                        faers_caseid=row.caseid,
                        year=quarter.year,
                        quarter=quarter.quarter,
                    )
                )
        created_cases = Case.objects.bulk_create(new_cases, batch_size=1000)

        return {case.faers_primaryid: case.id for case in created_cases}

    def _load_demo_data(self, file_path: Path, cases_ids: Dict[int, int]) -> None:
        """
        Load demographic data from the CSV file into the database.
        To ensure consistency, it loads only cases appear in cases_ids.
        """
        self.stdout.write(f"Loading demographic data from {file_path}...")
        new_demos = []
        num_demos = 0

        for chunk in pd.read_csv(
            file_path,
            usecols=DEMO_COLUMNS,
            dtype=DEMO_COLUMN_TYPES,
            chunksize=self.CHUNK_SIZE,
        ):
            for row in chunk.itertuples(index=False):
                case_id = cases_ids.get(row.primaryid, None)
                if case_id is None:
                    continue

                clean_row = self._clean_row(row=row, lower=False)

                demo = Demo(
                    case_id=case_id,
                    event_dt_num=self._get_event_dt_num(clean_row),
                    age=clean_row["age"],
                    age_cod=clean_row["age_cod"],
                    sex=clean_row["sex"],
                    wt=clean_row["wt"],
                    wt_cod=clean_row["wt_cod"],
                )
                new_demos.append(demo)

            Demo.objects.bulk_create(new_demos)
            num_demos += len(new_demos)
            new_demos = []

        self.stdout.write(
            f"Loaded {num_demos} demographic records from file {file_path}"
        )

    def _load_drug_data(self, file_path: Path) -> None:
        """
        Load drug data from the CSV file into the database.
        """
        self.stdout.write(f"Loading drug data from {file_path}...")

    def _load_outcome_data(self, file_path: Path) -> None:
        """
        Load outcome data from the CSV file into the database.
        """
        self.stdout.write(f"Loading outcome data from {file_path}...")

    def _load_reaction_data(self, file_path: Path) -> None:
        """
        Load reaction data from the CSV file into the database.
        """
        self.stdout.write(f"Loading reaction data from {file_path}...")

    @staticmethod
    def _clean_row(row: tuple, lower=True) -> dict:
        """
        Takes a row from itertuples and returns a cleaned dictionary:
        - Strips and lowercases/uppercase string values
        - Converts empty strings or NaNs to None
        """
        clean = {}
        for key in row._fields:
            val = getattr(row, key)
            if isinstance(val, str):
                val = normalize_string(val, lower)
            val = empty_to_none(val)
            clean[key] = val
        return clean

    @staticmethod
    def _get_event_dt_num(row):
        return (
            row["event_dt_num"] if validate_event_dt_num(row["event_dt_num"]) else None
        )
