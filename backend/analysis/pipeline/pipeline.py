import logging
import os
import shutil

import luigi
import mark_data
import report
import save_to_db

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
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Directory for the output of pipeline tasks
PIPELINE_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "pipeline_output")


class Faers_Pipeline(luigi.Task):
    year_q_from = luigi.Parameter(default="2013q1")
    year_q_to = luigi.Parameter(default="2023q1")
    query_id = luigi.OptionalParameter(default=None)
    save_results_to_db = luigi.BoolParameter(default=False)

    # Use absolute paths based on script location
    dir_data = os.path.join(SCRIPT_DIR, "data")
    dir_external = os.path.join(dir_data, "external/faers")
    config_dir = os.path.join(SCRIPT_DIR, "config")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.validate_parameters()

        # Use query_id for paths of tasks output if query_id was spesified
        self.dir_internal = (
            os.path.join(PIPELINE_OUTPUT_DIR, f"{self.query_id}")
            if self.query_id
            else PIPELINE_OUTPUT_DIR
        )
        self.dir_interim = os.path.join(self.dir_internal, "interim")
        self.dir_processed = os.path.join(self.dir_internal, "processed")

        # Clean up any existing directory for this query
        # This prevents parallel processing of same query_id
        if os.path.exists(self.dir_internal):
            logger.warning(
                f"Removing existing processing directory for query {self.query_id}"
            )
            shutil.rmtree(self.dir_internal)
            logger.info(f"Cleaned up existing directory: {self.dir_internal}")

    def validate_parameters(self):
        # Validation: can't save to DB without query_id
        if self.save_results_to_db and not self.query_id:
            raise luigi.parameter.ParameterException(
                "Cannot save results to database without query_id. "
                "Either provide --query-id or set --no-save-results-to-db"
            )

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
        report = Report(
            dir_marked_data=os.path.dirname(marked.output().path),
            dir_raw_data=self.dir_external,
            config_dir=self.config_dir,
            dir_reports=os.path.join(self.dir_processed, "reports"),
            output_raw_exposure_data=True,
            dependency_params={
                "mark_the_data": marked.param_kwargs,
            },
        )
        yield report

        # save results to db
        if self.save_results_to_db:
            saved_results = SaveToDB(
                dir_processed=self.dir_processed,
                dependency_params={
                    "report": report.param_kwargs,
                },
                query_id=self.query_id,
            )
            yield saved_results

    def output(self):
        return luigi.LocalTarget(self.dir_processed)


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
        return luigi.LocalTarget(os.path.join(self.dir_out, "_MARK_DATA"))

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
        return luigi.LocalTarget(os.path.join(self.dir_reports, "_REPORT"))

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


class SaveToDB(luigi.Task):
    dir_processed = luigi.Parameter(default="data/processed")
    dependency_params = luigi.DictParameter(default={})
    version = luigi.Parameter(default="v3")
    query_id = luigi.Parameter()

    def requires(self):
        return Report(**self.dependency_params.get("report", {}))

    def output(self):
        return luigi.LocalTarget(os.path.join(self.dir_processed, "_DB_SAVED"))

    def run(self):
        results_file = os.path.join(self.dir_processed, "reports", "results.json")

        save_to_db.save_ror_values(results_file=results_file, query_id=self.query_id)

        # Write marker to indicate success
        with self.output().open("w") as out_file:
            out_file.write(f"Results were saved to DB using data from:{results_file}")
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
