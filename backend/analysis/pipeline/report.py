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
from typing import Dict, List, Optional, TypeAlias, Union
import json

import defopt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
import tqdm
from matplotlib import pylab as plt
from statsmodels.stats.outliers_influence import variance_inflation_factor
from utils import (
    ContingencyMatrix,
    QuestionConfig,
    html_from_fig,
)

# Add logger definition
logger = logging.getLogger(__name__)


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
        dir_raw_data: str,
        output_raw_exposure_data: bool,
        return_plot_data_only: bool = False,
    ) -> None:
        """Initialize the Reporter with configuration and mode settings.

        Args:
            config: Analysis configuration
            dir_out: Base output directory
            output_raw_exposure_data: Whether to include raw exposure data
            return_plot_data_only: If True, only process data without generating files
        """
        # Analysis configuration
        self.config = config
        self.dir_raw_data = dir_raw_data
        self.title = config.name

        # Output settings
        self.dir_out = os.path.join(dir_out, self.title)
        self.output_raw_exposure_data = output_raw_exposure_data
        self.return_plot_data_only = return_plot_data_only
        self.figure_count = 0

        # Setup output directories only if generating files
        if not self.return_plot_data_only:
            self._setup_directories()

    def _setup_directories(self) -> None:
        """Create output directories if not in plot-data-only mode."""
        for format_ in self.FORMATS:
            os.makedirs(os.path.join(self.dir_out, format_), exist_ok=True)
            logger.debug(f"Created directory: {os.path.join(self.dir_out, format_)}")

    def subplots(self, figsize=(8, 4), dpi=360):
        """Create matplotlib subplots with default settings."""
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
    ) -> PlotDataDict:
        """
        Process data and generate plot data.
        Optionally creating files - if return_plot_data_only=False
        """
        # Process data
        processed_data = self._process_data(data)

        # Generate plot data
        plot_data = self._calculate_ror_data(processed_data)
        plot_data_dict = {"ror_data": plot_data}

        # Generate report files
        if not self.return_plot_data_only:
            self._generate_report_files(
                processed_data, plot_data_dict, title, config, explanation, skip_lr
            )

        # return plot_data in a dictionary for optionally return other values (i.e. regression_data) in the future
        return plot_data_dict

    def _process_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Process and validate input data."""
        # Check for duplicate indices
        if len(set(data.index)) != len(data):
            logger.warning("Found duplicate indices in data. Resetting index.")
            data = data.reset_index(drop=False)

        # Apply data controls
        return self.handle_controls(data, self.config)

    def _generate_report_files(
        self,
        data: pd.DataFrame,
        plot_data: PlotDataDict,
        title: str,
        config: QuestionConfig,
        explanation: Optional[str],
        skip_lr: bool,
    ) -> None:
        """Generate HTML report and associated files."""
        lines = []

        # Title and explanation
        lines.append(f"<H1>{self.title}</H1>")
        if explanation is not None:
            lines.append(explanation)

        # Configuration summary
        config_summary = self.summarize_config(config)
        lines.append(config_summary)

        # Demographic tables
        demographic_html = self.demographic_summary(data)
        lines.append(demographic_html)

        # ROR visualization (using processed data)
        ror_html = self._generate_plot_html(plot_data["ror_data"])
        lines.append(ror_html)

        # Get regression data if needed, using processed data
        if not skip_lr:
            regression_data = self.regression_analysis(data)
            lines.append(regression_data)

        # True-True cases table (if enabled)
        if self.output_raw_exposure_data:
            true_true_html = self.true_true(data, config)
            lines.append(true_true_html)

        # Write report file
        fn = os.path.join(self.dir_out, f"report {self.config.name} {title}.html")
        with open(fn, "w") as f:
            f.write("\n".join(lines))
        logger.info(f"Saved report to {fn}")

    def handle_controls(self, data, config):
        if config.control is None:
            return data
        control_col = f"control {config.name}"
        col_exposure = f"exposed {config.name}"
        sel = data[control_col] | data[col_exposure]
        logger.info(
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

    def _calculate_regression_data(self, data_regression):
        """Process regression data.
        Returns:
            dict: Contains processed regression data and any error messages
        """
        config = self.config
        data_regression = data_regression.copy()
        col_exposure = f"exposed {config.name}"
        col_ouctome = f"reacted {config.name}"

        # Prepare data
        data_regression["exposure"] = data_regression[col_exposure].astype(int)
        data_regression["outcome"] = data_regression[col_ouctome].astype(int)
        data_regression["is_female"] = (data_regression["sex"] == "F").astype(int)
        data_regression["intercept"] = 1.0

        regression_cols = ["age", "is_female", "exposure", "intercept"]
        if "wt" in data_regression.columns:
            regression_cols.append("wt")
        outcome_col = "outcome"
        data_regression = data_regression[regression_cols + [outcome_col]]

        # Handle empty dataset
        if len(data_regression) == 0 or data_regression[regression_cols].empty:
            return {"error": "Empty dataset for regression analysis"}

        try:
            # Fit model
            logit = sm.Logit(
                data_regression[outcome_col], data_regression[regression_cols]
            )
            result = logit.fit()

            # Process results
            or_estimates = result.conf_int().rename(columns={0: "lower", 1: "upper"})
            or_estimates["OR"] = result.params
            or_estimates = np.round(np.exp(or_estimates)[["lower", "OR", "upper"]], 3)

            return {
                "result": result,
                "or_estimates": or_estimates,
                "data_regression": data_regression,
                "regression_cols": regression_cols,
                "error": None,
            }
        except Exception as e:
            logger.error(f"Error in regression analysis: {str(e)}")
            return {"error": str(e)}

    def regression_analysis(self, data_regression):
        """Combines data processing and visualization for regression analysis."""
        # Process data
        reg_data = self._calculate_regression_data(data_regression)

        # Handle errors
        if reg_data.get("error"):
            logger.error(f"Regression analysis error: {reg_data['error']}")
            return f"ERROR: {reg_data['error']}<br>"

        # Generate visualization
        result = reg_data["result"]
        or_estimates = reg_data["or_estimates"]

        # Build HTML
        result_summary = result.summary2(title=self.config.name).as_html()
        or_estimates_html = "OR estimates<br>" + or_estimates.to_html()

        colinearity_html = self.colinearity_analysis(
            data_regression=reg_data["data_regression"],
            regression_cols=reg_data["regression_cols"],
            name=None,
        )

        html_summary = (
            "<h3>Logistic regression</h3>\n"
            + result_summary
            + "\n<br>\n"
            + or_estimates_html
            + colinearity_html
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
        outcome_files = glob(os.path.join(self.dir_raw_data, "outc*.csv.zip"))
        serious_outcomes = set()
        for f in outcome_files:
            serious_outcomes.update(
                pd.read_csv(f, usecols=["caseid"], dtype=str).caseid.values
            )
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

    def _calculate_ror_data(self, data: pd.DataFrame) -> PlotDataDict:
        """Calculate ROR values and prepare plot data."""
        rors = []

        # Select relevant columns
        columns_to_keep = ["age", "sex", "event_date", "q"] + [
            c for c in data.columns if c.endswith(self.config.name)
        ]
        if "wt" in data.columns:
            columns_to_keep.append("wt")

        # Process data by quarter
        ror_data = pd.DataFrame()
        gr = data[columns_to_keep].groupby("q")

        for q, curr in sorted(gr):
            ror_data = pd.concat((ror_data, curr))
            contingency_matrix = ContingencyMatrix.from_results_table(
                ror_data, self.config
            )
            ror, (lower, upper) = contingency_matrix.ror()
            rors.append([q, lower, ror, upper])

        # Convert to DataFrame for data processing
        df_rors = pd.DataFrame(rors, columns=["q", "ROR_lower", "ROR", "ROR_upper"])

        return self.plot_ror_data(df_rors)

    def _generate_plot_html(self, plot_data: PlotDataDict) -> str:
        """Generate plot visualization and return HTML.

        This function has the single responsibility of visualization.
        Only called when return_plot_data_only=False.
        """
        lines = ["<H3>ROR data</H3>"]

        # Create visualization
        fig, ax = self.subplots()
        self.draw_ror_plot(plot_data, ax_ror=ax)
        lines.append(self.handle_fig(fig, "ROR dynamics"))

        return "\n".join(lines)

    @staticmethod
    def plot_ror_data(tbl_report: pd.DataFrame) -> PlotDataDict:
        """Calculate log10 ROR data values and return plot data points.

        Args:
            tbl_report: DataFrame with ROR data

        Returns:
            Dictionary containing all data needed for plotting:
            - quarters: List of quarter identifiers
            - ror_values: Linear ROR values
            - ror_lower/upper: Linear confidence bounds
            - log10_ror: Log10 of ROR values for plotting
            - log10_ror_lower/upper: Log10 of confidence bounds
        """
        # Extract and sort quarters
        quarters = list(sorted(tbl_report.q.unique()))

        # Calculate logarithmic values
        df = tbl_report.copy()
        df["l10_ROR"] = np.log10(df.ROR)
        df["l10_ROR_lower"] = np.log10(df.ROR_lower)
        df["l10_ROR_upper"] = np.log10(df.ROR_upper)

        # Create data dictionary
        return {
            "quarters": quarters,
            "ror_values": df.ROR.values.tolist(),
            "ror_lower": df.ROR_lower.values.tolist(),
            "ror_upper": df.ROR_upper.values.tolist(),
            "log10_ror": df.l10_ROR.values.tolist(),
            "log10_ror_lower": df.l10_ROR_lower.values.tolist(),
            "log10_ror_upper": df.l10_ROR_upper.values.tolist(),
        }

    def draw_ror_plot(
        self,
        plot_data: PlotDataDict,
        ax_ror: Optional[plt.Axes] = None,
        xticklabels: bool = True,
        figwidth: int = 8,
        dpi: int = 360,
    ) -> plt.Axes:
        """Draw ROR plot using prepared data.

        This function handles only visualization, using pre-calculated data.
        It's only called when return_plot_data_only=False.

        Args:
            plot_data: Dictionary with all required plotting data
            ax_ror: Optional matplotlib axis for plotting
            xticklabels: Whether to show x-axis labels
            figwidth: Width of the figure
            dpi: DPI for the figure

        Returns:
            Matplotlib axis with the plot
        """
        # Create axis if needed
        if ax_ror is None:
            figsize = (figwidth, figwidth * 0.5)
            _, ax_ror = plt.subplots(figsize=figsize, dpi=dpi)

        # Setup basic plot elements
        quarters = plot_data["quarters"]
        x = list(range(len(quarters)))

        # Plot main line
        ax_ror.plot(x, plot_data["log10_ror"], "-o", color="C0", zorder=99)

        # Plot confidence interval
        try:
            ax_ror.fill_between(
                x,
                plot_data["log10_ror_lower"],
                plot_data["log10_ror_upper"],
                color="C0",
                alpha=0.3,
            )
        except Exception as e:
            logger.warning(f"Error filling between curves: {str(e)}")
            return ax_ror

        # Style the plot
        ax_ror.set_ylim(-2.1, 2.1)
        tkx = [-1, 0, 1]
        ax_ror.set_yticks(tkx)
        ax_ror.set_yticklabels([f"$\\times {10**t}$" for t in tkx])

        # X-axis labels
        tkx = [i for i, q in enumerate(quarters) if q.endswith("1")]
        lbls = [quarters[i].split("q")[0] for i in tkx]
        ax_ror.set_xticks(tkx)
        if xticklabels:
            ax_ror.set_xticklabels(lbls)
        else:
            ax_ror.set_xticklabels([])

        # Additional styling
        sns.despine(ax=ax_ror)
        ax_ror.spines["bottom"].set_position("zero")
        ax_ror.set_ylabel("ROR", rotation=0, ha="right", y=0.9)
        ax_ror.set_xlim(0, max(x) + 1)

        # Add value labels
        ax_ror.text(
            x=max(x) + 0.15,
            y=plot_data["log10_ror"][-1],
            s=f"${plot_data['ror_values'][-1]:.2f}$",
            ha="left",
            va="center",
            color="gray",
        )
        ax_ror.text(
            x=max(x) + 0.1,
            y=plot_data["log10_ror_lower"][-1],
            s=f"${plot_data['ror_lower'][-1]:.2f}$",
            ha="left",
            va="top",
            size="small",
            color="gray",
        )
        ax_ror.text(
            x=max(x) + 0.1,
            y=plot_data["log10_ror_upper"][-1],
            s=f"${plot_data['ror_upper'][-1]:.2f}$",
            ha="left",
            va="bottom",
            size="small",
            color="gray",
        )

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
    config_dir: str,
    dir_raw_data: str,
    dir_reports: str,
    output_raw_exposure_data: bool = False,
    return_plot_data_only: bool = False,
) -> Dict[str, Dict[str, Reporter.PlotDataDict]]:
    """
    Generate reports and optionally return plot data

    :param str dir_marked_data:
        marked data directory
    :param str config_dir:
        config directory
    :param str dir_reports:
        output directory
    :param bool output_raw_exposure_data:
        whether to include raw table of exposure cases
    :param bool return_plot_data:
        If True, returns a dict containing plot data points instead of generating plots

    :return:
        If return_plot_data=False: None
        If return_plot_data=True: Dict containing plot data for each config, for example:

        {'saxenda_et_al - liraglutide_saxenda_victoza':
            {'initial_data': {'ror_data': {'quarters': ['2020q1'],
                'ror_values': [0.6726039259706947], 'ror_lower': [0.5633208387774181], 'ror_upper': [0.8030877079091061],
                'log10_ror': [-0.17224060204898844], 'log10_ror_lower': [-0.24924418272764398], 'log10_ror_upper': [-0.09523702137033288]}},
            'stratified_lr': {'ror_data': {'quarters': ['2020q1'],
                'ror_values': [0.7909182992810732], 'ror_lower': [0.5622737524599851], 'ror_upper': [1.1125394941535764],
                'log10_ror': [-0.10186837617863559],'log10_ror_lower': [-0.2500521893482361], 'log10_ror_upper': [0.046315436990964826]}},
            'stratified_lr_no_weight': {'ror_data': {'quarters': ['2020q1'],
                'ror_values': [0.8536837501490995], 'ror_lower': [0.616947607155467], 'ror_upper': [1.1812606724074433],
                'log10_ror': [-0.06870298528530162], 'log10_ror_lower': [-0.2097517158523444], 'log10_ror_upper': [0.07234574528174116]}}}}
    """

    config_items = QuestionConfig.load_config_items(config_dir)
    files = sorted(glob(os.path.join(dir_marked_data, "*.pkl")))
    data_all_configs = pd.concat([pickle.load(open(f, "rb")) for f in files])

    # Always create the plot data dictionary now
    plot_data_by_config = {}

    for config in tqdm.tqdm(config_items):
        logger.info(f"Processing config: {config.name}")

        # Data selection
        columns_to_keep = ["age", "sex", "wt", "event_date", "q"] + [
            c for c in data_all_configs.columns if c.endswith(config.name)
        ]
        data = data_all_configs[columns_to_keep]

        # Initialize reporter with plot data only mode
        reporter = Reporter(
            config,
            dir_reports,
            dir_raw_data,
            output_raw_exposure_data=output_raw_exposure_data,
            return_plot_data_only=return_plot_data_only,
        )

        # Initialize plot data structure for this config
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
        )
        plot_data_by_config[config.name]["initial_data"] = plot_data

        # Filter and process data
        data = filter_illegal_values(data)
        data_lr = filter_data_for_regression(data, config)

        # Report 2: Stratified for LR
        plot_data = reporter.report(
            data_lr,
            "02 Stratified for LR",
            config=config,
            explanation="After filtering out age and weight values that do not fit 99 percentile of the exposed population",
        )
        plot_data_by_config[config.name]["stratified_lr"] = plot_data

        # Report 3: Stratified for LR without weight
        data_lr = filter_data_for_regression(data, config, including_the_weight=False)
        plot_data = reporter.report(
            data_lr,
            "03 Stratified for LR ignoring weight",
            config=config,
            explanation="After filtering out age values that do not fit 99 percentile of the exposed population",
        )
        plot_data_by_config[config.name]["stratified_lr_no_weight"] = plot_data

    for config_name, config_data in plot_data_by_config.items():
        logger.debug(f"\nPlot data for {config_name}:")
        for report_type, plot_data in config_data.items():
            logger.debug(f"{report_type}:")
            # Log ROR data
            ror_data = plot_data["ror_data"]
            logger.debug("ROR Data:")
            logger.debug(f"Quarters: {ror_data.get('quarters', [])}")
            logger.debug(f"ROR values: {ror_data.get('ror_values', [])}")
            logger.debug(f"ROR lower bounds: {ror_data.get('ror_lower', [])}")
            logger.debug(f"ROR upper bounds: {ror_data.get('ror_upper', [])}")

    # Save ror results to file in json format
    try:
        with open(os.path.join(dir_reports, "results.json"), "w") as f:
            json.dump(plot_data_by_config, f, indent=2, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        logger.error(f"Failed to serialize data to JSON: {e}")
        raise

    return plot_data_by_config


if __name__ == "__main__":
    defopt.run(main)
