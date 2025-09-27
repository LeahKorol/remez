from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command


class Command(BaseCommand):
    help = "Run the full FAERS import pipeline"

    def add_arguments(self, parser):
        parser.add_argument(
            "year_q_from",
            type=str,
            help='XXXXqQ, where XXXX is the year, q is the literal "q" and Q is 1, 2, 3 or 4',
        )
        parser.add_argument(
            "year_q_to",
            type=str,
            help='XXXXqQ, where XXXX is the year, q is the literal "q" and Q is 1, 2, 3 or 4',
        )

    def handle(self, *args, **options):
        # Add process and save_to_db stages
        steps = [
            ("download_faers_data", [options["year_q_from"], options["year_q_to"]]),
            ("load_faers_terms", [options["year_q_from"], options["year_q_to"]]),
            ("load_faers_data", [options["year_q_from"], options["year_q_to"]]),
        ]

        self.stdout.write(self.style.MIGRATE_HEADING("Starting FAERS pipeline"))

        for name, cmd_opts in steps:
            try:
                self.stdout.write(self.style.NOTICE(f"Running `{name}`..."))
                self.stdout.write(f"Calling `{name}` with {cmd_opts}")
                call_command(name, *cmd_opts)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Step `{name}` failed: {e}"))
                raise CommandError("Pipeline stopped due to error.")

        self.stdout.write(self.style.SUCCESS("All pipeline steps completed."))
