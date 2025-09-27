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

import concurrent
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Model
from pathlib import Path
from typing import List, Dict, Type
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
    DRUG_COLUMNS,
    DRUG_COLUMN_TYPES,
    OUTCOME_COLUMNS,
    OUTCOME_COLUMN_TYPES,
    REACTION_COLUMNS,
    REACTION_COLUMN_TYPES,
)
from analysis.models import Case, Demo, Drug, DrugName, Outcome, Reaction, ReactionName


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

            # get the drug and reaction names for creating the drug and reaction
        # instances quickly without querying the database for each row
        drug_names = dict(DrugName.objects.values_list("name", "id"))
        reaction_names = dict(ReactionName.objects.values_list("name", "id"))

        for q in generate_quarters(q_first, q_last):
            self.stdout.write(f"Processing quarter: {q}")
            self.load_quarter_data(dir_in, q, drug_names, reaction_names)
            self.stdout.write(f"Finished processing quarter: {q}")

    def load_quarter_data(
        self,
        dir_in: str,
        quarter: Quarter,
        drug_names: Dict[str, int],
        reaction_names: Dict[str, int],
    ) -> None:
        """
        Load FAERS data for a specific quarter into the database.
        The term files are prcessed concurrently after the cases are created
        """
        term_file_paths = self._get_quarter_files(dir_in, quarter)
        demo_file_path = self._get_demo_file(term_file_paths)

        cases_ids: Dict[int, int] = self._create_new_cases(demo_file_path, quarter)
        # Use exsisting cases if they are already in the database
        # cases_ids = dict(
        #     Case.objects.values_list("faers_primaryid", "id").filter(
        #         year=quarter.year, quarter=quarter.quarter
        #     )
        # )

        # Process files concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_file = {}
            for file_path in term_file_paths:
                if FaersTerms.DEMO.value in file_path.name:
                    future_to_file[
                        executor.submit(
                            self._load_term_data,
                            file_path,
                            cases_ids,
                            Demo,
                            DEMO_COLUMNS,
                            DEMO_COLUMN_TYPES,
                            False,
                        )
                    ] = file_path
                elif FaersTerms.DRUG.value in file_path.name:
                    future_to_file[
                        executor.submit(
                            self._load_term_data,
                            file_path,
                            cases_ids,
                            Drug,
                            DRUG_COLUMNS,
                            DRUG_COLUMN_TYPES,
                            True,
                            drug_names,
                        )
                    ]
                elif FaersTerms.OUTCOME.value in file_path.name:
                    future_to_file[
                        executor.submit(
                            self._load_term_data,
                            file_path,
                            cases_ids,
                            Outcome,
                            OUTCOME_COLUMNS,
                            OUTCOME_COLUMN_TYPES,
                            False,
                        )
                    ] = file_path
                elif FaersTerms.REACTION.value in file_path.name:
                    future_to_file[
                        executor.submit(
                            self._load_term_data,
                            file_path,
                            cases_ids,
                            Reaction,
                            REACTION_COLUMNS,
                            REACTION_COLUMN_TYPES,
                            True,
                            reaction_names,
                        )
                    ] = file_path
                else:
                    raise CommandError(f"Unknown file type: {file_path}")
            for future in concurrent.futures.as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    num_terms = future.result()
                    self.stdout.write(
                        f"Loaded {num_terms} terms from file {file}. Thread exited sucessfully!"
                    )
                except Exception as exc:
                    print(f"{file} generated an exception: {exc}")

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
        self.stdout.write(
            f"Loaded {len(created_cases)} new cases from file {demo_file_path}"
        )

        return {case.faers_primaryid: case.id for case in created_cases}

    def _load_term_data(
        self,
        file_path: Path,
        cases_ids: Dict[int, int],
        term: Type[Model],
        columns: List[str],
        column_types: Dict,
        lower: bool = True,
        term_ids: Dict[str, int] = None,
    ) -> None:
        """
        Load term data from the CSV file into the database.
        To ensure consistency, it loads only cases appear in cases_ids.
        """
        if term not in [Demo, Drug, Outcome, Reaction]:
            raise CommandError(f"Invalid term type: {term}")

        self.stdout.write(f"Loading {term.__name__} data from {file_path}...")

        new_terms = []
        num_terms = 0
        for chunk in pd.read_csv(
            file_path,
            usecols=columns,
            dtype=column_types,
            chunksize=self.CHUNK_SIZE,
        ):
            for row in chunk.itertuples(index=False):
                case_id = cases_ids.get(row.primaryid, None)
                if case_id is None:
                    self.stdout.write(
                        f"Term {term} with primaryid {row.primaryid} doesn't have a matched case_id. Skipping..."
                    )
                    continue

                clean_row = self._clean_row(row=row, lower=lower)

                # Create a new instance of the term model with the cleaned data.
                if term == Demo:
                    term_instance = self._create_demo_instance(case_id, clean_row)
                elif term == Drug:
                    term_instance = self._create_drug_instance(
                        case_id, clean_row, term_ids
                    )
                elif term == Outcome:
                    term_instance = self._create_outcome_instance(case_id, clean_row)
                elif term == Reaction:
                    term_instance = self._create_reaction_instance(
                        case_id, clean_row, term_ids
                    )

                # Uncomment the following lines to validate the instance before saving.
                # Pay attention this will slow down the process significantly.
                # # try:
                # #     term_instance.full_clean()
                # # except ValidationError as e:
                # #     self.stdout.write(self.style.ERROR(
                # #             f"Validation error for term {term.__name__} in {clean_row}\n"
                # #             f"Error: {str(e)}"
                # #         )
                # #     )
                # #     continue
                if term_instance:
                    new_terms.append(term_instance)

            term.objects.bulk_create(new_terms, batch_size=1000)
            num_terms += len(new_terms)
            new_terms = []

        self.stdout.write(
            f"Loaded {num_terms} {term.__name__} records from file {file_path}"
        )
        return num_terms

    @staticmethod
    def _create_demo_instance(case_id: int, clean_row: dict) -> Demo:
        demo = Demo(
            case_id=case_id,
            event_dt_num=Command._get_event_dt_num(clean_row),
            age=clean_row["age"],
            age_cod=clean_row["age_cod"],
            sex=clean_row["sex"],
            wt=clean_row["wt"],
            wt_cod=clean_row["wt_cod"],
        )
        return demo

    def _create_drug_instance(
        self, case_id: int, clean_row: dict, drug_names: dict
    ) -> Drug:
        drug_id = drug_names.get(clean_row["drugname"])
        if drug_id is None:
            self.stdout.write(
                f"Drug name #{clean_row['primaryid']} not found in database. Skipping..."
            )
            return None

        drug = Drug(
            case_id=case_id,
            drug_id=drug_id,
        )
        return drug

    @staticmethod
    def _create_outcome_instance(case_id: int, clean_row: dict) -> Outcome:
        outcome = Outcome(
            case_id=case_id,
            outc_cod=clean_row["outc_cod"],
        )
        return outcome

    @staticmethod
    def _create_reaction_instance(
        case_id: int, clean_row: dict, reaction_names: dict
    ) -> Reaction:
        reaction_id = reaction_names.get(clean_row["pt"])
        if reaction_id is None:
            print(f"Reaction name {clean_row['pt']} not found in database. Skipping...")
            return None
        reaction = Reaction(
            case_id=case_id,
            reaction_id=reaction_id,
        )
        return reaction

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
