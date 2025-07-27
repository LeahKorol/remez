from django.core.management.base import BaseCommand, CommandError

from analysis.faers_analysis.src.report import main as report_main


class Command(BaseCommand):
    help = (
        "Generate FAERS reports using the specified configuration and data directories."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dir-marked-data",
            type=str,
            required=True,
            help="Directory containing marked data (pickled files).",
        )
        parser.add_argument(
            "--year-q-from",
            type=str,
            required=True,
            help="Start quarter in format YYYYqQ (e.g., 2020q1).",
        )
        parser.add_argument(
            "--year-q-to",
            type=str,
            required=True,
            help="End quarter in format YYYYqQ (e.g., 2021q4).",
        )
        parser.add_argument(
            "--config-dir",
            type=str,
            required=True,
            help="Directory containing configuration files.",
        )
        parser.add_argument(
            "--dir-reports",
            type=str,
            required=True,
            help="Directory to write output reports.",
        )
        parser.add_argument(
            "--output-raw-exposure-data",
            action="store_true",
            help="Include raw table of exposure cases in the report.",
        )
        parser.add_argument(
            "--return-plot-data",
            action="store_true",
            help="Return graph data points instead of generating graphs.",
        )

    def handle(self, *args, **options):
        try:
            report_main(
                dir_marked_data=options["dir_marked_data"],
                year_q_from=options["year_q_from"],
                year_q_to=options["year_q_to"],
                config_dir=options["config_dir"],
                dir_reports=options["dir_reports"],
                output_raw_exposure_data=options["output_raw_exposure_data"],
                return_plot_data=options["return_plot_data"],
            )
            self.stdout.write(
                self.style.SUCCESS("Report generation completed successfully.")
            )
        except Exception as e:
            raise CommandError(f"Error in report: {e}")
