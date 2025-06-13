from django.core.management.base import BaseCommand, CommandError
from analysis.faers_analysis.src.mark_data import main as mark_data_main


class Command(BaseCommand):
    help = "Mark FAERS data using the specified configuration and output directory."

    def add_arguments(self, parser):
        parser.add_argument(
            "--year-q-from",
            type=str,
            required=True,
            help="Start quarter in format YYYYqQ (e.g., 2020q1)",
        )
        parser.add_argument(
            "--year-q-to",
            type=str,
            required=True,
            help="End quarter in format YYYYqQ (e.g., 2021q4)",
        )
        parser.add_argument(
            "--config-dir",
            type=str,
            required=True,
            help="Directory containing configuration files.",
        )
        parser.add_argument(
            "--dir-out",
            type=str,
            required=True,
            help="Directory to write output files.",
        )
        parser.add_argument(
            "-t",
            "--threads",
            type=int,
            default=1,
            help="Number of parallel threads to use (default: 1).",
        )
        parser.add_argument(
            "--no-clean-on-failure",
            action="store_true",
            help="Do not clean output directory on failure.",
        )

    def handle(self, *args, **options):
        try:
            mark_data_main(
                year_q_from=options["year_q_from"],
                year_q_to=options["year_q_to"],
                config_dir=options["config_dir"],
                dir_out=options["dir_out"],
                threads=options["threads"],
                clean_on_failure=not options["no_clean_on_failure"],
            )
            self.stdout.write(
                self.style.SUCCESS("Marking data completed successfully.")
            )
        except Exception as e:
            raise CommandError(f"Error in mark_data: {e}")
