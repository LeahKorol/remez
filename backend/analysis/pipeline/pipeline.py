import logging
import os

import luigi
import mark_data
import report

# Ensure logging is configured
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FAERS")
logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "%(levelname)s: %(message)s"}},
    "handlers": {
        "stdout": {"class": "logger.StreamHandler", "stream": "ext://sys.stdout"}
    },
}


# Get the directory where this script is located
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# Go up one level to project root
# PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)


class Faers_Pipeline(luigi.Task):
    print("Starting FAERS Pipeline...")

    # Use absolute paths based on script location
    dir_data = os.path.join(PROJECT_ROOT, "data")
    dir_external = os.path.join(dir_data, "external/faers")
    dir_interim = os.path.join(dir_data, "interim")
    dir_processed = os.path.join(dir_data, "processed")
    config_dir = os.path.join(PROJECT_ROOT, "config")

    dir_out_report = dir_processed

    year_q_from = luigi.Parameter(default="2013q1")
    year_q_to = luigi.Parameter(default="2023q1")

    def requires(self):
        # mark the data
        marked = MarkTheData(
            year_q_from=self.year_q_from,
            year_q_to=self.year_q_to,
            dir_in=self.dir_external,
            config_dir=self.config_dir,
            dir_out=os.path.join(self.dir_interim, "marked_data_v2"),
        )
        yield marked

        # generate reports
        yielded_report = Report(
            dir_marked_data=os.path.dirname(marked.output().path),
            dir_raw_data=self.dir_external,
            config_dir=self.config_dir,
            dir_reports=self.output().path,
            output_raw_exposure_data=True,
            dependency_params={
                "mark_the_data": marked.param_kwargs,
            },
        )
        yield yielded_report

    def output(self):
        return luigi.LocalTarget(os.path.join(self.dir_processed, "reports"))


class MarkTheData(luigi.Task):
    year_q_from = luigi.Parameter()
    year_q_to = luigi.Parameter()
    dir_in = luigi.Parameter(default="data/interim/faers")
    config_dir = luigi.Parameter(default="config")
    dir_out = luigi.Parameter(default="data/interim/marked_data_v2")
    threads = luigi.IntParameter(default=7)
    dependency_params = luigi.DictParameter(default={})
    version = luigi.Parameter(default="v3")

    def output(self):
        return luigi.LocalTarget(os.path.join(self.dir_out, "_SUCCESS"))

    def run(self):
        os.makedirs(self.dir_out, exist_ok=True)
        mark_data.main(
            year_q_from=self.year_q_from,
            year_q_to=self.year_q_to,
            dir_in=self.dir_in,
            config_dir=self.config_dir,
            dir_out=self.dir_out,
            threads=self.threads,
            clean_on_failure=True,
        )
        with self.output().open("w") as out_file:
            out_file.write(
                f"Processed quarters from {self.year_q_from} to {self.year_q_to}"
            )
            out_file.write("\n")
            out_file.write(f"Version: {self.version}")


class Report(luigi.Task):
    dir_marked_data = luigi.Parameter(default="data/interim/marked_data_v2")
    dir_raw_data = luigi.Parameter(default="data/external/faers")
    config_dir = luigi.Parameter(default="config")
    dir_reports = luigi.Parameter(default="data/processed/reports")
    output_raw_exposure_data = luigi.BoolParameter(default=True)
    dependency_params = luigi.DictParameter(default={})
    version = luigi.Parameter(default="v3")

    def requires(self):
        return MarkTheData(**self.dependency_params.get("mark_the_data", {}))

    def output(self):
        return luigi.LocalTarget(os.path.join(self.dir_reports, "output.txt"))

    def run(self):
        os.makedirs(self.dir_reports, exist_ok=True)
        report.main(
            dir_marked_data=self.dir_marked_data,
            dir_raw_data=self.dir_raw_data,
            config_dir=self.config_dir,
            dir_reports=self.dir_reports,
            output_raw_exposure_data=self.output_raw_exposure_data,
        )
        with self.output().open("w") as out_file:
            out_file.write(f"Reports generated using data from {self.dir_marked_data}")
            out_file.write("\n")
            out_file.write(f"Version: {self.version}")


if __name__ == "__main__":
    # Luigi reads sys.argv - the command line arguments passed to the script
    luigi.run()

    # Command to run the pipeline directly
    # luigi.run(
    #     [
    #         "--local-scheduler",
    #         "--Faers-Pipeline-year-q-from",
    #         "2020q1",
    #         "--Faers-Pipeline-year-q-to",
    #         "2020q2",
    #     ],
    #     main_task_cls=Faers_Pipeline,
    # )