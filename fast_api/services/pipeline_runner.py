import os
import defopt
from mark_data_runner import mark_data
from report import main as report_main

def run_pipeline(
    dir_raw_data,
    dir_config,
    dir_marked_data,
    dir_reports,
    output_raw_exposure_data=False,
):
    """
    רץ את כל הצינור:
    1. סימון הנתונים
    2. הפקת הדוחות
    """
    os.makedirs(dir_marked_data, exist_ok=True)
    os.makedirs(dir_reports, exist_ok=True)

    # שלב 1: סימון הנתונים
    mark_data(
        dir_raw_data=dir_raw_data,
        dir_config=dir_config,
        dir_marked_data=dir_marked_data,
    )

    # שלב 2: הפקת דוחות
    report_main(
        dir_marked_data=dir_marked_data,
        dir_raw_data=dir_raw_data,
        config_dir=dir_config,
        dir_reports=dir_reports,
        output_raw_exposure_data=output_raw_exposure_data,
    )


if __name__ == "__main__":
    defopt.run(run_pipeline)
