"""
This file was originally copied from: https://github.com/bgbg/faers_analysis/blob/main/src/mark_data.py
Modifiefd to use FAERS data from a database instead of CSV files.
"""

import os
import pickle
import shutil
from functools import partial
from multiprocessing import Pool

import numpy as np
import pandas as pd
import tqdm

from ...django_setup import setup_django_environemnt
from . import utils
from .utils import Quarter, QuestionConfig, generate_quarters

setup_django_environemnt()

import logging

from django.db.models import F

from analysis.faers_analysis import constants as const
from analysis.faers_analysis.src.utils import normalize_dataframe
from analysis.models import Demo, Drug, Outcome, Reaction

logger = logging.getLogger("FAERS")


def mark_drug_data(df, drug_names):
    df.drugname = df.drugname.apply(QuestionConfig.normalize_drug_name)
    for drug in sorted(drug_names):
        df[f"drug {drug}"] = df.drugname == drug
    drug_columns = [f"drug {drug}" for drug in drug_names]
    ret = df.groupby("caseid")[drug_columns].any()
    return ret


def mark_reaction_data(df, reaction_types):
    df.pt = df.pt.apply(QuestionConfig.normalize_reaction_name)

    # Create a dict of new columns
    new_cols = {
        f"reaction {reaction}": df.pt == reaction for reaction in sorted(reaction_types)
    }

    # Concatenate in a single operation to avoid fragmentation
    df = pd.concat([df, pd.DataFrame(new_cols, index=df.index)], axis=1)

    reaction_columns = list(new_cols.keys())
    ret = df.groupby("caseid")[reaction_columns].any()

    return ret


def handle_duplicates_within_case(df, cols_boolean, cols_rest):
    if df.shape[0] == 1:
        return df.iloc[0]
    ret = df[cols_rest].iloc[-1]  # take the last available data
    ret["q"] = df["q"].iloc[0]  # take the earliest timepoint
    ret = pd.concat([ret, df[cols_boolean].any(axis=0)])
    return ret


def handle_duplicates(df):
    cols_boolean = [c for c in df.columns if df.dtypes[c] == np.dtype(bool)]
    cols_rest = [c for c in df.columns if (c not in cols_boolean) and (c != "q")]
    rows_per_caseid = pd.value_counts(df["caseid"])
    df["rows_per_caseid"] = rows_per_caseid.reindex(df.caseid).values
    sel = df.rows_per_caseid == 1
    already_good = df.loc[sel]
    logger.info(f"{sel.sum():,d} rows are already good")
    need_to_fix = df.loc[~sel]
    logger.info(f"{len(need_to_fix):,d} rows need some fixing")
    fixed = need_to_fix.groupby("caseid").apply(
        lambda d: handle_duplicates_within_case(d, cols_boolean, cols_rest)
    )
    logger.info("Done fixing, combining the results")
    ret = pd.concat([already_good, fixed], sort=False)
    uniqueness = utils.compute_df_uniqueness(ret, ["caseid"], do_print=False)
    assert uniqueness == 1.0
    return ret.set_index("caseid")


def mark_data(df_drug, df_reac, df_demo, config_items):
    logger.info("Marking the data")
    cols_to_collect = list(df_demo.columns)
    df_merged = df_demo.join(df_reac).join(df_drug)
    for config in config_items:
        logger.info(f"Config {config.name[0:40]}....")
        drugs_curr = set(config.drugs)
        drug_columns = [f"drug {drug}" for drug in drugs_curr]
        exposed = f"exposed {config.name}"
        df_merged[exposed] = df_merged[drug_columns].any(axis=1)
        cols_to_collect.append(exposed)
        if config.control is not None:
            control_columns = [f"drug {drug}" for drug in config.control]
            control = f"control {config.name}"
            df_merged[control] = df_merged[control_columns].any(axis=1)
            cols_to_collect.append(control)
        reaction_columns = [f"reaction {reaction}" for reaction in config.reactions]
        reacted = f"reacted {config.name}"
        df_merged[reacted] = df_merged[reaction_columns].any(axis=1)
        cols_to_collect.append(reacted)
    df_merged = df_merged[cols_to_collect].reset_index().sort_values(["caseid", "q"])
    logger.info(f"Handling duplicates of {len(df_merged):,d} rows")
    ret = handle_duplicates(df_merged)
    return ret


def load_quarder_files(model, quarters, **kwargs) -> pd.DataFrame:
    if model not in [Demo, Drug, Outcome, Reaction]:
        raise ValueError(
            f"Invalid model: {model}. Must be one of [Demo, Drug, Outcome, Reaction]"
        )

    # Check if quarters is iterable but not a string
    if hasattr(quarters, "__iter__") and not isinstance(quarters, (str, bytes)):
        quarters_to_process = quarters
    else:
        # Handle the case where a single quarter is passed
        quarters_to_process = [quarters]

    years = [q.year for q in quarters_to_process]
    quarters = [q.quarter for q in quarters_to_process]

    if model == Demo:
        data = (
            Demo.objects.all()
            .filter(case__year__in=years)
            .filter(case__quarter__in=quarters)
            .values(*const.DEMO_COLUMNS)
        )
    elif model == Drug:
        data = (
            Drug.objects.all()
            .annotate(drugname=F("drug__name"))
            .filter(case__year__in=years)
            .filter(case__quarter__in=quarters)
            .values(*const.DRUG_COLUMNS)
        )
    elif model == Outcome:
        data = (
            Outcome.objects.all()
            .filter(case__year__in=years)
            .filter(case__quarter__in=quarters)
            .values(*const.OUTCOME_COLUMNS)
        )
    elif model == Reaction:
        data = (
            Reaction.objects.all()
            .annotate(pt=F("reaction__name"))
            .filter(case__year__in=years)
            .filter(case__quarter__in=quarters)
            .values(*const.REACTION_COLUMNS)
        )

    model_name = model.__name__.upper()
    column_types = getattr(const, f"{model_name}_COLUMN_TYPES")
    columns = getattr(const, f"{model_name}_COLUMNS")

    data = pd.DataFrame.from_records(data=data, columns=columns)
    normalised_data = normalize_dataframe(data, column_types)
    return normalised_data


def process_quarters(quarters, dir_out, config_items, drug_names, reaction_types):
    DEBUG = None
    df_drug = load_quarder_files(Drug, quarters, nrows=DEBUG).dropna()
    df_drug = mark_drug_data(df_drug, drug_names)

    df_reac = load_quarder_files(Reaction, quarters, nrows=DEBUG)
    df_reac = mark_reaction_data(df_reac, reaction_types)

    df_demo = []
    for q in quarters:
        fn_demo = load_quarder_files(Demo, quarters, nrows=DEBUG)
        tmp = utils.process_demo_data(fn_demo, nrows=DEBUG).set_index("caseid")
        tmp["q"] = str(q)
        df_demo.append(tmp)
    df_demo = pd.concat(df_demo)

    df_marked = mark_data(
        df_drug=df_drug, df_reac=df_reac, df_demo=df_demo, config_items=config_items
    )
    logger.info("Marked the data, dumping the file")

    # Save the combined file
    pickle.dump(df_marked, open(os.path.join(dir_out, "marked_data.pkl"), "wb"))

    # Save individual quarterly files
    for q in quarters:
        df_q = df_marked[df_marked.q == str(q)]
        if not df_q.empty:
            pickle.dump(df_q, open(os.path.join(dir_out, f"{q}.pkl"), "wb"))
            logger.info(f"Saved quarterly file for {q}")

    return df_marked


def process_quarter_wrapper(q, dir_out, config_items, drug_names, reaction_types):
    """Wrapper function for process_quarter to use with multiprocessing"""
    output_file = os.path.join(dir_out, f"{q}.pkl")
    if os.path.exists(output_file):
        logger.debug(f"Skipping {q} because {output_file} already exists")
        return

    # Ensure the environment is set up for Django, as this function runs in a separate process
    from django.conf import settings

    settings.DATABASES["default"]["NAME"] = os.environ.get("DB_NAME", "test_postgres")

    # Process the single quarter
    df_drug = load_quarder_files(Drug, [q]).dropna()
    df_drug = mark_drug_data(df_drug, drug_names)

    df_reac = load_quarder_files(Reaction, [q])
    df_reac = mark_reaction_data(df_reac, reaction_types)

    fn_demo = load_quarder_files(Demo, [q])
    df_demo = utils.process_demo_data(fn_demo).set_index("caseid")
    df_demo["q"] = str(q)

    df_marked = mark_data(
        df_drug=df_drug, df_reac=df_reac, df_demo=df_demo, config_items=config_items
    )

    # Only save the quarterly file for this quarter
    logger.info(f"Saving quarterly file {output_file}")
    pickle.dump(df_marked, open(output_file, "wb"))

    return df_marked


def main(
    *,
    year_q_from,
    year_q_to,
    config_dir=None,  # save config_dir for backwards compatibility
    json_config=None,
    dir_out,
    threads=1,
    clean_on_failure=True,
):
    # --skip-if-exists --year-q-from=$(QUARTER_FROM) --year-q-to=$(QUARTER_TO) --dir-in=$(DIR_FAERS_DEDUPLICATED) --config-dir=$(CONFIG_DIR) --dir-out=$(DIR_MARKED_FILES) -t $(N_THREADS) --no-clean-on-failure
    """

    :param str year_q_from:
        XXXXqQ, where XXXX is the year, q is the literal "q" and Q is 1, 2, 3 or 4
    :param str year_q_to:
        XXXXqQ, where XXXX is the year, q is the literal "q" and Q is 1, 2, 3 or 4
    :param str config_dir:
        Directory with config files
    :param str json_config:
        JSON object with configuration for queries
    :param str dir_out:
        Output directory
    :param int threads:
        Threads in parallel processing
    :param bool clean_on_failure:
        ???

    :return: None

    """

    dir_out = os.path.abspath(dir_out)
    os.makedirs(dir_out, exist_ok=True)

    if not config_dir and not json_config:
        raise ValueError(
            "Either config_dir or json_config must be provided. "
            "Use --config-dir or --json-config options."
        )
    try:
        q_from = Quarter(year_q_from)
        q_to = Quarter(year_q_to)
        config_items = []
        if config_dir:
            config_items = QuestionConfig.load_config_items(config_dir)
        if json_config:
            config_items.append(QuestionConfig.config_from_json_object(json_config))
        drug_names = set()
        reaction_types = set()
        for config in config_items:
            drug_names.update(set(config.drugs))
            if config.control is not None:
                drug_names.update(set(config.control))
            reaction_types.update(set(config.reactions))
        print(
            f"Will analyze {len(drug_names)} drugs and {len(reaction_types)} reactions"
        )
        quarters = list(generate_quarters(q_from, q_to))
        process_quarters(
            quarters,
            dir_out=dir_out,
            config_items=config_items,
            drug_names=drug_names,
            reaction_types=reaction_types,
        )

        with Pool(threads) as pool:
            wrapper_func = partial(
                process_quarter_wrapper,
                dir_out=dir_out,
                config_items=config_items,
                drug_names=drug_names,
                reaction_types=reaction_types,
            )
            _ = list(tqdm.tqdm(pool.imap(wrapper_func, quarters), total=len(quarters)))
    except Exception as err:
        if clean_on_failure:
            shutil.rmtree(dir_out)
        raise err
