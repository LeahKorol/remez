"""
Download FAERS quarterly CSV zip files for pipeline external data.

This is intentionally aligned with backend management command behavior.
"""

import argparse
import logging
import os
import shutil
import urllib.request
from multiprocessing.dummy import Pool as ThreadPool

import tqdm
from core.config import get_settings
from utils import Quarter, generate_quarters

logger = logging.getLogger("FAERS")


def _parse_bool(value: str) -> bool:
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean value: {value}")


def quarter_urls(quarter: Quarter) -> list[str]:
    ret = []
    year = quarter.year
    yearquarter = str(quarter)
    what = ["demo", "drug", "outc", "reac"]

    for w in what:
        if year <= 2018:
            tmplt = f"https://data.nber.org/fda/faers/{year}/{w}{yearquarter}.csv.zip"
        else:
            tmplt = (
                f"https://data.nber.org/fda/faers/{year}/csv/{w}{yearquarter}.csv.zip"
            )
        ret.append(tmplt)
    return ret


def download_url(url: str, dir_out: str, force: bool = False) -> None:
    fn_out = os.path.split(url)[-1]
    fn_out = os.path.join(dir_out, fn_out)
    if os.path.exists(fn_out):
        if force:
            os.remove(fn_out)
            logger.info(f"Deleted existing file {fn_out}")
        else:
            logger.debug(f"Skipping {url} because {fn_out} already exists")
            return
    try:
        urllib.request.urlretrieve(url, fn_out)
    except Exception as err:
        logger.error(f"Failed to download {url} to {fn_out} {err}")
    else:
        logger.info(f"Saved {fn_out}")
        assert os.path.exists(fn_out)


def run_download(
    year_q_from: str,
    year_q_to: str,
    dir_out: str,
    threads: int = 4,
    clean_on_failure: bool = True,
    force: bool = False,
) -> None:
    dir_out_abs = os.path.abspath(dir_out)
    os.makedirs(dir_out_abs, exist_ok=True)

    try:
        q_first = Quarter(year_q_from)
        q_last = Quarter(year_q_to)
        urls: list[str] = []
        for q in generate_quarters(q_first, q_last):
            urls.extend(quarter_urls(q))

        logger.info(f"will download {len(urls)} urls")
        with ThreadPool(threads) as pool:
            _ = list(
                tqdm.tqdm(
                    pool.imap(lambda url: download_url(url, dir_out_abs, force), urls),
                    total=len(urls),
                )
            )
    except Exception:
        if clean_on_failure:
            shutil.rmtree(dir_out_abs, ignore_errors=True)
        raise


def build_parser() -> argparse.ArgumentParser:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Download FAERS quarterly CSV files")
    parser.add_argument("year_q_from", type=str)
    parser.add_argument("year_q_to", type=str)
    parser.add_argument(
        "--dir_out",
        type=str,
        default=str(settings.get_external_data_path()),
        help="Output directory",
    )
    parser.add_argument("--threads", type=int, default=4, help="N of parallel threads")
    parser.add_argument(
        "--clean_on_failure",
        type=_parse_bool,
        default=True,
        help="Delete the output directory if the command fails",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete existing files before downloading",
    )
    return parser


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s",
    )
    args = build_parser().parse_args()
    run_download(
        year_q_from=args.year_q_from,
        year_q_to=args.year_q_to,
        dir_out=args.dir_out,
        threads=args.threads,
        clean_on_failure=args.clean_on_failure,
        force=args.force,
    )


if __name__ == "__main__":
    main()
