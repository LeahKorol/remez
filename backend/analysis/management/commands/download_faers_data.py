"""
This file is adapted from:
https://github.com/bgbg/faers_analysis/blob/main/src/download_faers_data.py
It has been modified to work with Django management commands instead of defopt.
"""

import logging
import os
import shutil
import urllib.request
from multiprocessing.dummy import Pool as ThreadPool

import tqdm
from django.core.management.base import BaseCommand, CommandError

from analysis.faers_analysis.src.utils import Quarter, generate_quarters

from ..cli_utils import QuarterRangeArgMixin

logger = logging.getLogger("FAERS")


class Command(QuarterRangeArgMixin, BaseCommand):
    help = "Download FAERS quarterly CSV files"

    def add_arguments(self, parser):
        # Add year_q_from and year_q_to
        super().add_arguments(parser)

        parser.add_argument(
            "--dir_out",
            type=str,
            help="Output directory",
        )
        parser.add_argument("--threads", type=int, help="N of parallel threads")

        parser.add_argument(
            "--clean_on_failure",
            type=bool,
            help="Delete the output directory if the command fails",
        )

    def handle(self, *args, **options):
        year_q_from = options["year_q_from"]
        year_q_to = options["year_q_to"]
        dir_out = os.path.abspath(
            options["dir_out"] or "analysis/management/commands/output"
        )
        threads = options.get("threads", 4)
        clean_on_failure = options.get("clean_on_failure", True)

        dir_out = os.path.abspath(dir_out)
        os.makedirs(dir_out, exist_ok=True)
        try:
            q_first = Quarter(year_q_from)
            q_last = Quarter(year_q_to)
            urls = []
            for q in generate_quarters(q_first, q_last):
                urls.extend(Command.quarter_urls(q))

            logger.info(f"will download {len(urls)} urls")
            with ThreadPool(threads) as pool:
                _ = list(
                    tqdm.tqdm(
                        pool.imap(lambda url: Command.download_url(url, dir_out), urls),
                        total=len(urls),
                    )
                )
        except Exception as err:
            if clean_on_failure:
                shutil.rmtree(dir_out)
            raise CommandError(str(err))

    @staticmethod
    def quarter_urls(quarter):
        ret = []
        year = quarter.year
        yearquarter = str(quarter)
        what = [
            "demo",
            "drug",
            "reac",
            "outc",
            # "indi",
            # "ther",
        ]

        for w in what:
            if year <= 2018:
                tmplt = (
                    f"https://data.nber.org/fda/faers/{year}/{w}{yearquarter}.csv.zip"
                )
            else:
                tmplt = f"https://data.nber.org/fda/faers/{year}/csv/{w}{yearquarter}.csv.zip"
            ret.append(tmplt)
        return ret

    @staticmethod
    def download_url(url, dir_out):
        fn_out = os.path.split(url)[-1]
        fn_out = os.path.join(dir_out, fn_out)
        if os.path.exists(fn_out):
            logger.debug(f"Skipping {url} because {fn_out} already exists")
            return
        try:
            urllib.request.urlretrieve(url, fn_out)
        except Exception as err:
            logger.error(f"Failed to download {url} to {fn_out} {err}")
        else:
            logger.info(f"Saved {fn_out}")
            assert os.path.exists(fn_out)
