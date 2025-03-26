from django.core.management.base import BaseCommand, CommandError
from pathlib import Path
import pandas as pd

from analysis.models import Drug, Reaction


class Command(BaseCommand):
    """Loads unique drug and reaction terms from FAERS source files into the database,
    ensuring no duplicates are created."""

    def add_arguments(self, parser):
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

        if not options["no_drugs"]:
            self.load_terms(input_dir, "drug")

        if not options["no_reactions"]:
            self.load_terms(input_dir, "reaction")

    def load_terms(self, input_dir: str, term: str) -> None:
        if term == "drug":
            term_file_name = "drug"
            term_field_name = "drugname"
            model = Drug
        elif term == "reaction":
            term_file_name = "reac"
            term_field_name = "pt"
            model = Reaction
        else:
            raise CommandError(f"Invalid term {term}")

        # Load files starting with the term_file_name
        term_files = list(Path(input_dir).glob(f"{term_file_name}*.csv"))

        # Use set for efficient lookups
        existed_terms = set(model.objects.values_list("name", flat=True))

        # Use set for to prevent duplicates
        unique_term_names = set()

        self.stdout.write(f"Loading {term} terms from {len(term_files)} files...")

        for file in term_files:
            term_df = pd.read_csv(file)

            if term_field_name not in term_df.columns:
                raise CommandError(f"Column {term_field_name} not found in {file.name}")

            term_names = term_df[term_field_name].dropna().astype(str)

            for term_name in term_names:
                if term_name not in existed_terms:
                    unique_term_names.add(term_name)

            self.stdout.write(f"Loaded new terms from file {file.name}.")

        model.objects.bulk_create(
            [model(name=term_name) for term_name in unique_term_names], batch_size=1000
        )
        self.stdout.write(
            self.style.SUCCESS(f"Inserted {len(unique_term_names)} new {term} terms.")
        )
