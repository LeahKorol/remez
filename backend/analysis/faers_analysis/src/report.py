"""
This file was originally copied from: https://github.com/bgbg/faers_analysis/blob/main/src/report.py
Modifiefd to use FAERS data from a database instead of CSV files.
Added an option to return the graph data points instead of generating them.
"""

# We will use a class instead of a set of functions, mainly for figure management
import logging
import os
import pickle
from glob import glob
from typing import Dict, List, Optional, Tuple, TypeAlias, Union

import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
import tqdm
from matplotlib import pylab as plt
from statsmodels.stats.outliers_influence import variance_inflation_factor

from analysis.faers_analysis.src.utils import (
    ContingencyMatrix,
    Quarter,
    QuestionConfig,
    generate_quarters,
    html_from_fig,
)
from analysis.models import Outcome

logger = logging.getLogger("FAERS")


class Reporter:
    FORMATS: List[str] = ["png"]
    PlotDataDict: TypeAlias = Dict[str, List[Union[str, float]]]
    """Structure of PlotDataDict:
    {
        "quarters": List[str],       # Quarter identifiers (e.g., ["2021q1", "2021q2", ...])
        "ror_values": List[float],   # Reporting Odds Ratio values
        "ror_lower": List[float],    # Lower confidence bounds for ROR
        "ror_upper": List[float],    # Upper confidence bounds for ROR
        "log10_ror": List[float],    # Log10 of ROR values for plotting
        "log10_ror_lower": List[float], # Log10 of lower bounds
        "log10_ror_upper": List[float]  # Log10 of upper bounds
    }
    """

    def __init__(
        self,
        config: QuestionConfig,
        dir_out: str,
        q_from: Quarter,
        q_to: Quarter,
        output_raw_exposure_data: bool,
    ) -> None:
        self.config = config
        self.title = config.name
        self.dir_out = os.path.join(dir_out, self.title)
        self.q_from = q_from
        self.q_to = q_to
        for format_ in self.FORMATS:
            os.makedirs(os.path.join(self.dir_out, format_), exist_ok=True)
        self.figure_count = 0
        self.output_raw_exposure_data = output_raw_exposure_data

    def subplots(self, figsize=(8, 4), dpi=360):
        return plt.subplots(figsize=figsize, dpi=dpi)

    def handle_fig(self, fig, caption=None):
        self.figure_count += 1
        if caption is None:
            caption = ""
        else:
            caption = ": " + caption
        caption = f"Figure {self.figure_count}{caption}"
        html = html_from_fig(fig, caption=caption, width=600)
        for format_ in self.FORMATS:
            fn = os.path.join(
                self.dir_out, format_, f"figure_{self.figure_count:03d}.{format_}"
            )
            fig.savefig(fn, dpi=360)
        plt.close(fig)
        return html

    def report(
        self,
        data: pd.DataFrame,
        title: str,
        config: QuestionConfig,
        explanation: Optional[str] = None,
        skip_lr: bool = False,
        return_plot_data: bool = False,
    ) -> Optional[PlotDataDict]:
        # Check for duplicate indices and reset index if needed
        if len(set(data.index)) != len(data):
            logger.warning("Found duplicate indices in data. Resetting index.")
            data = data.reset_index(drop=False)

        lines = []
        lines.append(f"<H1>{self.title}</H1>")
        if explanation is not None:
            lines.append(explanation)
        data = self.handle_controls(data, config)
        config_summary = self.summarize_config(config)
        lines.append(config_summary)

        summary_result = self.summarize_data(
            data, title, config, skip_lr=skip_lr, return_plot_data=return_plot_data
        )
        if return_plot_data:
            summary_html, plot_data = summary_result
            lines.append(summary_html)
        else:
            lines.append(summary_result)

        fn = os.path.join(self.dir_out, f"report {self.config.name} {title}.html")
        open(fn, "w").write("\n".join(lines))
        print(f"Saved {fn}")

        if return_plot_data:
            return plot_data

    def handle_controls(self, data, config):
        if config.control is None:
            return data
        control_col = f"control {config.name}"
        col_exposure = f"exposed {config.name}"
        sel = data[control_col] | data[col_exposure]
        print(
            f"{config.name:40s}: Due to control handling, removing {(1 - sel.mean()) * 100:.1f}% of lines"
        )
        return data.loc[sel]

    def summarize_config(self, config: QuestionConfig):
        lines = ["<H2>%s</H2>" % config.name]
        str_drugs = ", ".join(sorted(config.drugs))
        str_reactions = ", ".join(sorted(config.reactions))
        lines.append(f"<strong>Drugs:</strong> {str_drugs}<br>")
        if config.control is not None:
            str_control = ", ".join(config.control)
            lines.append(f"<strong>Controls:</strong> {str_control}<br>")
        lines.append(f"<strong>Reactions:</strong> {str_reactions}<br>")
        return "\n".join(lines)

    def summarize_data(
        self,
        data: pd.DataFrame,
        title: str,
        config: QuestionConfig,
        skip_lr: bool = False,
        return_plot_data: bool = False,
    ) -> Union[str, Tuple[str, PlotDataDict]]:
        lines = ["<H2>%s</H2>" % title]
        lines.append(self.demographic_summary(data))

        ror_result = self.ror_dynamics(data, return_data=return_plot_data)
        if return_plot_data:
            ror_html, plot_data = ror_result
            lines.append(ror_html)
        else:
            lines.append(ror_result)

        if not skip_lr:
            lines.append(self.regression_analysis(data))
        if self.output_raw_exposure_data:
            lines.append(self.true_true(data, config))

        if return_plot_data:
            return "\n".join(lines), plot_data
        return "\n".join(lines)

    def true_true(self, data, config):
        lines = ["<h3> True-True cases </h3>"]
        col_exposure = f"exposed {config.name}"
        col_ouctome = f"reacted {config.name}"
        cols_data = [c for c in ["age", "wt", "sex", "event_date", "q"] if c in data]
        true_true_data = data.loc[data[col_exposure] & data[col_ouctome]][
            cols_data
        ].reset_index()
        for c in ["age", "wt"]:
            if c in true_true_data:
                true_true_data[c] = np.round(true_true_data[c], 1)
        true_true_data.index += 1
        lines.append(true_true_data.to_html())

        # lines.append('<h3>True-False cases</h3>')
        # true_false_data = data.loc[
        #     data[col_exposure] & (~data[col_ouctome])
        #     ][cols_data].reset_index()
        # for c in ['age', 'wt']:
        #     if c in true_false_data:
        #       true_false_data[c] = np.round(true_false_data[c], 1)
        # true_false_data.index += 1
        # lines.append(true_false_data.to_html())

        return "\n".join(lines)

    def regression_analysis(self, data_regression):
        config = self.config
        data_regression = data_regression.copy()
        col_exposure = f"exposed {config.name}"
        col_ouctome = f"reacted {config.name}"

        data_regression["exposure"] = data_regression[col_exposure].astype(int)
        data_regression["outcome"] = data_regression[col_ouctome].astype(int)
        data_regression["is_female"] = (data_regression["sex"] == "F").astype(int)
        data_regression["intercept"] = 1.0

        regression_cols = ["age", "is_female", "exposure", "intercept"]
        if "wt" in data_regression.columns:
            regression_cols.append("wt")
        outcome_col = "outcome"
        data_regression = data_regression[regression_cols + [outcome_col]]

        # Check if the dataset is empty before attempting regression
        if len(data_regression) == 0 or data_regression[regression_cols].empty:
            return "ERROR: Empty dataset for regression analysis<br>"

        try:
            logit = sm.Logit(
                data_regression[outcome_col], data_regression[regression_cols]
            )
        except Exception as e:
            logger.error(f"Error in Logit model creation: {str(e)}")
            return f"ERROR in regression: {str(e)}<br>"
        try:
            result = logit.fit()
        except Exception as e:
            logger.warning(f"Error fitting logistic regression: {str(e)}")
            result_summary = "ERROR. Most probably, singular matrix<br>"
            or_estimates = "<br>"
        else:
            result_summary = result.summary2(title=config.name).as_html()
            or_estimates = result.conf_int().rename(columns={0: "lower", 1: "upper"})
            or_estimates["OR"] = result.params
            or_estimates = np.round(np.exp(or_estimates)[["lower", "OR", "upper"]], 3)
            or_estimates = "OR estimates<br>" + or_estimates.to_html()

        html_summary = (
            "<h3>Logistic regression</h3>\n"
            + result_summary
            + "\n<br>\n"
            + or_estimates
            + self.colinearity_analysis(
                data_regression=data_regression,
                regression_cols=regression_cols,
                name=None,
            )
        )
        return html_summary

    @staticmethod
    def colinearity_analysis(data_regression, regression_cols, name=None):
        rows = []
        if name:
            row = f"{name}: "
        else:
            row = ""
        rows.append("<b> " + row + "variance inflation factors" + "</b>")
        rows.append("<table><tbody>")
        rows.append(
            """<tr>
    			<th>variable</th>
    			<th>VIF</th>
    		</tr>
        """
        )

        mat = data_regression[regression_cols].values
        for i in range(len(regression_cols)):
            colname = regression_cols[i]
            if colname == "intercept":
                continue
            vif = variance_inflation_factor(mat, i)
            rows.append(f"<tr><td>{colname:30s}</td><td>{vif:.3f}</td></tr>")
        rows.append("</tbody></table>")
        return "\n".join(rows)

    def demographic_summary(self, data):
        lines = []
        lines.append("<H3>Demographic data</H3>")
        lines.append(self.demographic_table(data))
        lines.append(self.contingency_table(data))
        return "\n".join(lines)

    def contingency_table(self, data):
        lines = []
        lines.append("<h4>Contingency-matrix</h4>")
        cm = ContingencyMatrix.from_results_table(data, self.config)
        lines.append(cm.crosstab().to_html())
        return "\n".join(lines)

    def count_serious_outcomes(self, outcome_cases):
        # We assume that if a case ID is listed in `outcome*.csv.zip` it is
        # a "serious" outcome
        quarters_to_process = list(generate_quarters(self.q_from, self.q_to))
        years = [q.year for q in quarters_to_process]
        quarters = [q.quarter for q in quarters_to_process]
        outcome_caseids = (
            Outcome.objects.all()
            .filter(case__year__in=years)
            .filter(case__quarter__in=quarters)
            .values_list("caseid", flat=True)
        )

        serious_outcomes = set(outcome_caseids)
        n_serious = np.sum([c in serious_outcomes for c in outcome_cases])
        return n_serious

    def demographic_table(self, data):
        config = self.config
        col_exposure = f"exposed {config.name}"
        col_ouctome = f"reacted {config.name}"
        table_rows = []
        for exposure in "all", True, False:
            if exposure == "all":
                data_exposure = data
            else:
                data_exposure = data.loc[data[col_exposure] == exposure]
            for outcome in "all", True, False:
                if (exposure == "all") and (outcome != "all"):
                    continue
                if outcome == "all":
                    data_outcome = data_exposure
                else:
                    data_outcome = data_exposure.loc[
                        data_exposure[col_ouctome] == outcome
                    ]
                for gender in ["all", "F", "M"]:
                    if gender == "all":
                        data_gender = data_outcome
                    else:
                        data_gender = data_outcome.loc[data_outcome.sex == gender]

                    data_row = data_gender
                    n = f"{len(data_row):,d}"
                    age_mean = data_row.age.mean()
                    age_std = data_row.age.std(ddof=1)
                    age_range = f"{data_row.age.min():.1f} - {data_row.age.max():.1f}"
                    if "wt" in data.columns:
                        weight_mean = data_row.wt.mean()
                        weight_std = data_row.wt.std(ddof=1)
                        str_weight = f"{weight_mean:.1f}({weight_std:.1f})"
                        weight_range = (
                            f"{data_row.wt.min():.1f} - {data_row.wt.max():.1f}"
                        )
                    else:
                        str_weight = ""
                        weight_range = ""
                    if gender == "all":
                        percent_female = 100 * (data_row.sex == "F").mean()
                        percent_male = 100 * (data_row.sex == "M").mean()
                        female_to_male = f"{percent_female:.1f} : {percent_male:.1f}"
                    else:
                        female_to_male = ""
                    table_rows.append(
                        [
                            str(exposure),
                            str(outcome),
                            gender,
                            n,
                            f"{age_mean:.1f}({age_std:.1f})",
                            age_range,
                            str_weight,
                            weight_range,
                            female_to_male,
                        ]
                    )
                table_rows.append(["--"] * len(table_rows[-1]))
        summary_table = pd.DataFrame(
            table_rows,
            columns=[
                "Exposure",
                "Outcome",
                "Gender",
                "N",
                "Age",
                "Age range",
                "Weight",
                "Weight range",
                "Female : Male",
            ],
        )
        html_table = summary_table.to_html(index=False)
        additional_rows = []
        cases_with_outcome = set(data.loc[data[col_ouctome]].index)
        additional_rows.append(
            f"Of {len(data):,d} cases, {len(cases_with_outcome):,d} had a reaction."
        )
        n_exposed = data[col_exposure].sum()
        reports_with_exposure = set(data.loc[data[col_exposure]].index)
        cases_with_outcome_and_exposure = cases_with_outcome.intersection(
            reports_with_exposure
        )
        n_serious = self.count_serious_outcomes(cases_with_outcome_and_exposure)
        p_serious = 100 * n_serious / n_exposed
        additional_rows.append(
            f"Number of people who were exposed to the drug: {n_exposed}. "
            f"Of them, {len(cases_with_outcome)} developed a reaction. "
            f"Of them, {n_serious} ({p_serious:.1f}%) had a serious reaction"
        )

        ret = (
            "<h4>Demographic summary</h4>\n"
            + html_table
            + "<br>\n".join(additional_rows)
        )

        return ret

    def ror_dynamics(
        self, data: pd.DataFrame, return_data: bool = False
    ) -> Union[str, Tuple[str, PlotDataDict]]:
        """Generate ROR dynamics report section and optionally return plot data

        Returns:
            If return_data=True: Tuple of (html_string, plot_data_dict)
            If return_data=False: html_string
        """
        config = self.config
        rors = []
        columns_to_keep = ["age", "sex", "event_date", "q"] + [
            c for c in data.columns if c.endswith(config.name)
        ]
        if "wt" in data.columns:
            columns_to_keep.append("wt")
        ror_data = pd.DataFrame()
        gr = data[columns_to_keep].groupby("q")
        for q, curr in sorted(gr):
            ror_data = pd.concat((ror_data, curr))
            contingency_matrix = ContingencyMatrix.from_results_table(ror_data, config)
            ror, (lower, upper) = contingency_matrix.ror()
            rors.append([q, lower, ror, upper])
        df_rors = pd.DataFrame(rors, columns=["q", "ROR_lower", "ROR", "ROR_upper"])

        # Generate HTML without plotting if return_data is True
        lines = []
        lines.append("<H3>ROR data</H3>")
        if return_data:
            plot_data = self.plot_ror(df_rors, return_data=True)
            return "\n".join(lines), plot_data
        else:
            fig, ax = self.subplots()
            self.plot_ror(df_rors, ax_ror=ax)
            lines.append(self.handle_fig(fig, "ROR dynamics"))
            return "\n".join(lines)

    @staticmethod
    def plot_ror(
        tbl_report: pd.DataFrame,
        ax_ror: Optional[plt.Axes] = None,
        xticklabels: bool = True,
        figwidth: int = 8,
        dpi: int = 360,
        return_data: bool = False,
    ) -> Union[plt.Axes, PlotDataDict]:
        """
        Plot ROR dynamics or return the plot data points.
        IMPORTANT: It plots log(10) values, but labels are back-converted to a linear form.

        Returns:
            If return_data=True: Dict with plot data points - both linear and log10 values.
            If return_data=False: Matplotlib axis object.
        """
        quarters = list(sorted(tbl_report.q.unique()))  # we assume no Q is missing
        x = list(range(len(quarters)))

        # Calculate log10 values as in original plotting code
        tbl_report["l10_ROR"] = np.log10(tbl_report.ROR)
        tbl_report["l10_ROR_lower"] = np.log10(tbl_report.ROR_lower)
        tbl_report["l10_ROR_upper"] = np.log10(tbl_report.ROR_upper)

        plot_data = {
            "quarters": quarters,
            "ror_values": tbl_report.ROR.values.tolist(),
            "ror_lower": tbl_report.ROR_lower.values.tolist(),
            "ror_upper": tbl_report.ROR_upper.values.tolist(),
            "log10_ror": tbl_report.l10_ROR.values.tolist(),
            "log10_ror_lower": tbl_report.l10_ROR_lower.values.tolist(),
            "log10_ror_upper": tbl_report.l10_ROR_upper.values.tolist(),
        }

        if return_data:
            return plot_data

        if ax_ror is None:
            figsize = (figwidth, figwidth * 0.5)
            fig_ror, ax_ror = plt.subplots(figsize=figsize, dpi=dpi)

        ax_ror.plot(x, tbl_report.l10_ROR, "-o", color="C0", zorder=99)
        try:
            ax_ror.fill_between(
                x,
                tbl_report.l10_ROR_lower,
                tbl_report.l10_ROR_upper,
                color="C0",
                alpha=0.3,
            )
        except Exception as e:
            logger.warning(f"Error filling between curves: {str(e)}")
            return ax_ror
        
        ax_ror.set_ylim(-2.1, 2.1)
        tkx = [-1, 0, 1]
        ax_ror.set_yticks(tkx)
        ax_ror.set_yticklabels([f"$\\times {10**t}$" for t in tkx])
        sns.despine(ax=ax_ror)
        ax_ror.spines["bottom"].set_position("zero")
        tkx = []
        lbls = []
        for i, q in enumerate(quarters):
            if q.endswith("1"):
                tkx.append(i)
                lbls.append(q.split("q")[0])

        ax_ror.set_xticks(tkx)
        if xticklabels:
            ax_ror.set_xticklabels(lbls)
        else:
            ax_ror.set_xticklabels([])
        ax_ror.text(
            x=max(x) + 0.15,
            y=tbl_report.l10_ROR.iloc[-1],
            s=f"${tbl_report.ROR.iloc[-1]:.2f}$",
            ha="left",
            va="center",
            color="gray",
        )

        ax_ror.text(
            x=max(x) + 0.1,
            y=tbl_report.l10_ROR_lower.iloc[-1],
            s=f"${tbl_report.ROR_lower.iloc[-1]:.2f}$",
            ha="left",
            va="top",
            size="small",
            color="gray",
        )

        ax_ror.text(
            x=max(x) + 0.1,
            y=tbl_report.l10_ROR_upper.iloc[-1],
            s=f"${tbl_report.ROR_upper.iloc[-1]:.2f}$",
            ha="left",
            va="bottom",
            size="small",
            color="gray",
        )
        ax_ror.set_ylabel("ROR", rotation=0, ha="right", y=0.9)
        ax_ror.set_xlim(0, max(x) + 1)
        return ax_ror


def filter_illegal_values(data: pd.DataFrame) -> pd.DataFrame:
    """Filter out rows with illegal values for weight, age, and sex."""
    sel = (
        ((data.wt > 0) & (data.wt < 360))
        & ((data.age > 0) & (data.age < 120))
        & (data.sex.isin({"M", "F"}))
    )
    return data.loc[sel]


def filter_data_for_regression(
    data: pd.DataFrame, config: QuestionConfig, including_the_weight: bool = True
) -> pd.DataFrame:
    """Filter data for regression analysis based on percentiles."""
    percentile_ = 99.0
    percentile_lower = (100 - percentile_) / 2
    percentile_upper = 100 - percentile_lower

    col_exposure = f"exposed {config.name}"
    if data.loc[data[col_exposure]].empty:
        return data.head(0)
    else:
        age_from, age_to = np.nanpercentile(
            data.age, [percentile_lower, percentile_upper]
        )
        sel = (data.sex.isin({"M", "F"})) & (data.age > age_from) & (data.age < age_to)
        if including_the_weight:
            weight_from, weight_to = np.nanpercentile(
                data.wt, [percentile_lower, percentile_upper]
            )
            sel = sel & ((data.wt > weight_from) & (data.wt < weight_to))
        else:
            data.drop("wt", axis=1, inplace=True)
        assert sel.any()
        return data.loc[sel]


def main(
    *,
    dir_marked_data: str,
    year_q_from: str,
    year_q_to: str,
    config_dir: str,
    dir_reports: str,
    output_raw_exposure_data: bool = False,
    return_plot_data: bool = False,
) -> Optional[Dict[str, Dict[str, Reporter.PlotDataDict]]]:
    """
    Generate reports and optionally return plot data

    :param str dir_marked_data:
        marked data directory
    :param str year_q_from:
        XXXXqQ, where XXXX is the year, q is the literal "q" and Q is 1, 2, 3 or 4
    :param str year_q_to:
        XXXXqQ, where XXXX is the year, q is the literal "q" and Q is 1, 2, 3 or 4
    :param str config_dir:
        config directory
    :param str dir_reports:
        output directory
    :param bool output_raw_exposure_data:
        whether to include raw table of exposure cases
    :param bool return_plot_data:
        If True, returns a dict containing plot data points instead of generating plots

    :return:
        If return_plot_data=True: Dict containing plot data for each config
        If return_plot_data=False: None
    """

    config_items = QuestionConfig.load_config_items(config_dir)
    files = sorted(glob(os.path.join(dir_marked_data, "*.pkl")))
    data_all_configs = pd.concat([pickle.load(open(f, "rb")) for f in files])

    if return_plot_data:
        plot_data_by_config = {}

    for config in tqdm.tqdm(config_items):
        print(f"DEBUG {config.name}")
        columns_to_keep = ["age", "sex", "wt", "event_date", "q"] + [
            c for c in data_all_configs.columns if c.endswith(config.name)
        ]
        data = data_all_configs[columns_to_keep]
        reporter = Reporter(
            config,
            dir_reports,
            q_from=Quarter(year_q_from),
            q_to=Quarter(year_q_to),
            output_raw_exposure_data=output_raw_exposure_data,
        )

        # Initialize plot data structure for this config
        if return_plot_data:
            plot_data_by_config[config.name] = {
                "initial_data": None,
                "stratified_lr": None,
                "stratified_lr_no_weight": None,
            }

        # Report 1: Initial data
        plot_data = reporter.report(
            data,
            "01 Initial data",
            explanation="Raw data",
            skip_lr=True,
            config=config,
            return_plot_data=return_plot_data,
        )
        if return_plot_data:
            plot_data_by_config[config.name]["initial_data"] = plot_data

        data = filter_illegal_values(data)
        data_lr = filter_data_for_regression(data, config)

        # Report 2: Stratified for LR
        plot_data = reporter.report(
            data_lr,
            "02 Stratified for LR",
            config=config,
            explanation="After filtering out age and weight values that do not fit 99 percentile of the exposed population",
            return_plot_data=return_plot_data,
        )
        if return_plot_data:
            plot_data_by_config[config.name]["stratified_lr"] = plot_data

        # Report 3: Stratified for LR without weight
        data_lr = filter_data_for_regression(data, config, including_the_weight=False)
        plot_data = reporter.report(
            data_lr,
            "03 Stratified for LR ignoring weight",
            config=config,
            explanation="After filtering out age values that do not fit 99 percentile of the exposed population",
            return_plot_data=return_plot_data,
        )
        if return_plot_data:
            plot_data_by_config[config.name]["stratified_lr_no_weight"] = plot_data

    if return_plot_data:
        # Log data for each config item and report type
        for config_name, config_data in plot_data_by_config.items():
            logger.debug(f"\nPlot data for {config_name}:")
            for report_type, plot_data in config_data.items():
                logger.debug(f"{report_type}:")
                logger.debug(f"Quarters: {plot_data['quarters']}")
                logger.debug(f"ROR values: {plot_data['ror_values']}")
                logger.debug(f"ROR lower bounds: {plot_data['ror_lower']}")
                logger.debug(f"ROR upper bounds: {plot_data['ror_upper']}")

        return plot_data_by_config
