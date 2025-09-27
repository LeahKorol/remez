from django.core.management.base import BaseCommand, CommandError
from pathlib import Path
import pandas as pd
from typing import Type
from django.db.models import Model

from analysis.models import DrugName, ReactionName
from analysis.faers_analysis.src.utils import (
    Quarter,
    generate_quarters,
    normalize_string,
)
from ..cli_utils import QuarterRangeArgMixin


class Command(QuarterRangeArgMixin, BaseCommand):
    """
    Loads unique drug and reaction terms from FAERS source files into the database,
    ensuring no duplicates are created.
    """

    def add_arguments(self, parser):
        # Add year_q_from and year_q_to
        super().add_arguments(parser)

        parser.add_argument(
            "--no_reactions",
            action="store_true",
            help="Skip loading reaction terms",
        )
        parser.add_argument(
            "--no_drugs",
            action="store_true",
            help="Skip loading drug terms",
        )
        parser.add_argument(
            "--dir_in",
            type=str,
            help="Input directory",
        )

    def handle(self, *args, **options):
        input_dir = Path(options["dir_in"] or "analysis/management/commands/output")
        if not input_dir.exists():
            raise CommandError(f"Input directory {input_dir} does not exist")

        year_q_from = options["year_q_from"]
        year_q_to = options["year_q_to"]

        try:
            q_first = Quarter(year_q_from)
            q_last = Quarter(year_q_to)
        except RuntimeError as err:
            raise CommandError(f"Invalid quarter format: {err}")

        if not options["no_drugs"]:
            self.load_terms(input_dir, q_first, q_last, "drug")

        if not options["no_reactions"]:
            self.load_terms(input_dir, q_first, q_last, "reaction")

    def load_terms(
        self, input_dir: str, q_first: Quarter, q_last: Quarter, term: str
    ) -> None:
        if term == "drug":
            prefix, column, model = "drug", "drugname", DrugName
        elif term == "reaction":
            prefix, column, model = "reac", "pt", ReactionName
        else:
            raise CommandError(f"Invalid term '{term}'")

        files = self._get_term_files(input_dir, q_first, q_last, prefix)
        new_terms = self._collect_new_terms(files, column, model, term)

        # ignore_conflicts=True so inserting terms that already exist won't throw errors.
        # That enables inserting identdied terms from multiple files.
        model.objects.bulk_create(
            [model(name=name) for name in new_terms],
            batch_size=1000,
            ignore_conflicts=True,
        )
        self.stdout.write(
            self.style.SUCCESS(f"Inserted {len(new_terms)} new {term} terms.")
        )

    @staticmethod
    def _get_term_files(
        input_dir: str, q_first: Quarter, q_last: Quarter, term: str
    ) -> None:
        """
        Generate FAERS file paths for a spesific term.
        """
        term_file_paths = []

        for quarter in generate_quarters(q_first, q_last):
            yearquarter = str(quarter)  # YYYYqQ format

            file_name = f"{term}{yearquarter}.csv.zip"
            file_path = Path(input_dir) / file_name

            if not file_path.exists():
                raise CommandError(f"Required file not found: {file_path}")
            term_file_paths.append(file_path)

        return term_file_paths

    def _collect_new_terms(
        self,
        files: list[Path],
        column: str,
        model: Type[Model],
        term_label: str,
    ) -> set[str]:
        """
        Extracts and deduplicates new terms from CSV files based on the given column.
        """
        # Use set to ensure uniqueness across values from different files
        new_terms = set()

        self.stdout.write(f"Loading {term_label} terms from {len(files)} files...")

        for file in files:
            df = pd.read_csv(file, usecols=[column], dtype=str)

            for name in df[column].dropna().astype(str):
                name = normalize_string(name)
                if name:
                    new_terms.add(name)

            self.stdout.write(f"Loaded new terms from file {file.name}.")

        return new_terms
