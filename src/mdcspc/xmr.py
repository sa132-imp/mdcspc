from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# --------------------------------------------------------------------
# Data classes
# --------------------------------------------------------------------


@dataclass
class XmrConfig:
    value_col: str
    index_col: Optional[str]
    group_cols: Optional[Sequence[str]]
    baseline_mode: str
    baseline_points: Optional[int]
    min_points_for_spc: int
    shift_length: int
    trend_length: int
    rules: Sequence[str]


@dataclass
class XmrResult:
    data: pd.DataFrame
    config: XmrConfig


@dataclass
class MultiXmrResult:
    data: pd.DataFrame
    by_group: Dict[Tuple, XmrResult]
    config: XmrConfig


# --------------------------------------------------------------------
# Internal helper functions (single-series)
# --------------------------------------------------------------------


def _prepare_series(
    data: pd.DataFrame,
    value_col: str,
    index_col: Optional[str],
) -> pd.DataFrame:
    """
    Return a working DataFrame for a single series:
    - sorted by index_col or index
    - indexed by index_col (if provided)
    - value column as float
    """
    if value_col not in data.columns:
        raise ValueError(f"value_col '{value_col}' not found in DataFrame")

    work = data.copy()

    if index_col is not None:
        if index_col not in work.columns:
            raise ValueError(f"index_col '{index_col}' not found in DataFrame")
        work = work.sort_values(index_col)
        work = work.set_index(index_col)
    else:
        work = work.sort_index()

    work = work[[value_col]].copy()
    work[value_col] = work[value_col].astype(float)

    return work


def _assign_phases(
    index: pd.Index,
    phase_starts: Optional[Sequence[Union[str, pd.Timestamp]]],
) -> pd.Series:
    """
    Assign phase numbers based on a list of phase start points.

    - If phase_starts is None or empty, all points are phase 1.
    - Otherwise, phase_starts is interpreted as a sorted list of index
      values at which a NEW phase begins.

      Example (dates):
        phase_starts = ["2023-07-01", "2024-01-01"]

      Interpretation:
        phase 1: index <  2023-07-01
        phase 2: 2023-07-01 <= index < 2024-01-01
        phase 3: index >= 2024-01-01
    """
    if not phase_starts:
        return pd.Series(1, index=index)

    # Try to coerce phase_starts into the same "kind" as the index.
    # For datetime-like indexes, use to_datetime; otherwise, just make an Index.
    if index.inferred_type in ("datetime64", "datetime64tz", "date", "period"):
        starts = pd.to_datetime(list(phase_starts))
    else:
        starts = pd.Index(list(phase_starts))

    # Ensure sorted unique starts
    starts = starts.sort_values().unique()

    # Use searchsorted to count how many boundaries each index value is >=
    # and then add 1 to make phases 1-based.
    # For each x in index:
    #   phase = 1 + number of starts <= x
    # We implement "starts <= x" using side="right".
    positions = starts.searchsorted(index, side="right")
    phases = 1 + positions

    return pd.Series(phases, index=index)


def _compute_baseline_mask(
    values: pd.Series,
    baseline_mode: str,
    baseline_points: Optional[int],
) -> pd.Series:
    """
    Return a boolean Series indicating which points are used for the baseline
    *within a phase*.

    baseline_mode='all':
        - all non-null points in the phase are used as baseline
    baseline_mode='first_n':
        - the first N non-null points in the phase are used
    """
    baseline_mode = baseline_mode.lower()

    if baseline_mode not in ("all", "first_n"):
        raise ValueError("baseline_mode must be 'all' or 'first_n'")

    mask = pd.Series(False, index=values.index)

    non_null_idx = values.dropna().index

    if baseline_mode == "all":
        mask.loc[non_null_idx] = True
        return mask

    # baseline_mode == "first_n"
    if baseline_points is None or baseline_points <= 0:
        raise ValueError("baseline_points must be a positive integer when baseline_mode='first_n'")

    baseline_idx = non_null_idx[:baseline_points]
    mask.loc[baseline_idx] = True
    return mask


def _compute_limits_from_baseline(
    values: pd.Series,
    baseline_mask: pd.Series,
) -> Tuple[float, float, float, float]:
    """
    Compute mean, sigma, UCL, LCL from baseline points using MR-bar / 1.128.
    """
    baseline_values = values[baseline_mask].dropna()

    if len(baseline_values) < 2:
        return np.nan, np.nan, np.nan, np.nan

    mean = float(baseline_values.mean())

    mr = baseline_values.diff().abs().dropna()
    if len(mr) == 0:
        sigma = 0.0
    else:
        sigma = float(mr.mean() / 1.128)  # Wheeler constant for XmR

    ucl = mean + 3.0 * sigma
    lcl = mean - 3.0 * sigma

    return mean, sigma, ucl, lcl


def _rule_astronomical(values: pd.Series, mean: float, sigma: float) -> pd.Series:
    """
    Astronomical rule: any point beyond ±3 sigma (outside control limits).
    """
    if np.isnan(mean) or np.isnan(sigma) or sigma <= 0:
        return pd.Series(False, index=values.index)

    ucl = mean + 3.0 * sigma
    lcl = mean - 3.0 * sigma
    return (values > ucl) | (values < lcl)


def _rule_2of3(
    values: pd.Series,
    mean: float,
    sigma: float,
) -> pd.Series:
    """
    2-of-3 rule:

    In any 3 consecutive points, if at least 2 points are at or beyond ±2 sigma
    from the mean (|x - mean| >= 2*sigma) and on the same side of the mean,
    those points are flagged.

    NOTE: this includes points beyond 3 sigma as part of the 2-of-3 pattern.
    """
    if np.isnan(mean) or np.isnan(sigma) or sigma <= 0:
        return pd.Series(False, index=values.index)

    index = values.index
    n = len(values)
    flag = pd.Series(False, index=index)

    # Precompute deviation and side
    dev = values - mean
    high_band = dev >= 2.0 * sigma
    low_band = dev <= -2.0 * sigma

    for i in range(2, n):
        window_index = index[i - 2 : i + 1]

        hb = high_band.iloc[i - 2 : i + 1]
        lb = low_band.iloc[i - 2 : i + 1]

        # High side 2-of-3
        if hb.sum() >= 2:
            flag.loc[window_index[hb]] = True

        # Low side 2-of-3
        if lb.sum() >= 2:
            flag.loc[window_index[lb]] = True

    return flag.fillna(False)


def _rule_shift(
    values: pd.Series,
    mean: float,
    shift_length: int,
) -> pd.Series:
    """
    Shift rule:

    A run of 'shift_length' or more consecutive points all above the mean
    or all below the mean.

    Points exactly equal to the mean break the run.
    """
    if np.isnan(mean) or shift_length <= 1:
        return pd.Series(False, index=values.index)

    index = values.index
    n = len(values)
    flag = pd.Series(False, index=index)

    run_len = 0
    last_side: Optional[str] = None  # "above" or "below"

    for pos in range(n):
        x = values.iloc[pos]

        if np.isnan(x):
            run_len = 0
            last_side = None
            continue

        if x > mean:
            side = "above"
        elif x < mean:
            side = "below"
        else:
            # Exactly on the mean breaks the run
            run_len = 0
            last_side = None
            continue

        if side == last_side:
            run_len += 1
        else:
            run_len = 1
            last_side = side

        if run_len >= shift_length:
            start_pos = pos - run_len + 1
            for j in range(start_pos, pos + 1):
                flag.iloc[j] = True

    return flag.fillna(False)


def _rule_trend(
    values: pd.Series,
    trend_length: int,
) -> pd.Series:
    """
    Trend rule:

    A run of 'trend_length' or more consecutive points strictly increasing
    or strictly decreasing.

    Ties (equal values) break the trend.
    """
    if trend_length <= 1:
        return pd.Series(False, index=values.index)

    index = values.index
    n = len(values)
    flag = pd.Series(False, index=index)

    if n == 0:
        return flag

    up_run = 1
    down_run = 1

    prev = values.iloc[0]

    for pos in range(1, n):
        x = values.iloc[pos]

        if np.isnan(x) or np.isnan(prev):
            up_run = 1
            down_run = 1
            prev = x
            continue

        if x > prev:
            up_run += 1
            down_run = 1
        elif x < prev:
            down_run += 1
            up_run = 1
        else:
            # tie
            up_run = 1
            down_run = 1

        # Flag upward trend
        if up_run >= trend_length:
            start_pos = pos - up_run + 1
            for j in range(start_pos, pos + 1):
                idx_j = index[j]
                flag.loc[idx_j] = True

        # Flag downward trend
        if down_run >= trend_length:
            start_pos = pos - down_run + 1
            for j in range(start_pos, pos + 1):
                idx_j = index[j]
                flag.loc[idx_j] = True

        prev = x

    return flag.fillna(False)


# --------------------------------------------------------------------
# Public API: single-series analysis (with phases)
# --------------------------------------------------------------------


def analyse_xmr(
    data: pd.DataFrame,
    value_col: str,
    index_col: Optional[str] = None,
    phase_starts: Optional[Sequence[Union[str, pd.Timestamp]]] = None,
    baseline_mode: str = "all",
    baseline_points: Optional[int] = None,
    min_points_for_spc: int = 10,
    shift_length: int = 8,
    trend_length: int = 6,
    rules: Sequence[str] = ("trend", "shift", "2of3", "astronomical"),
) -> XmrResult:
    """
    Analyse a single time series using Making Data Count XmR rules.

    Phase behaviour
    ---------------
    - If phase_starts is None or empty:
        * Treat the whole series as a single phase (phase=1 for all points).
    - If phase_starts is provided:
        * It should be a sequence of index values (e.g. dates) at which a new
          phase starts.
        * For example: ["2023-07-01", "2024-01-01"] means:
              phase 1: index <  2023-07-01
              phase 2: 2023-07-01 <= index < 2024-01-01
              phase 3: index >= 2024-01-01

    For each phase:
    - Baseline is computed independently within that phase:
        * baseline_mode='all'   -> all points in the phase
        * baseline_mode='first_n' -> first N non-null points in that phase
    - Mean, sigma, UCL, LCL are constant within a phase.
    - Rules are applied within each phase independently.

    Special-cause aggregation:
    - For each point, the combined special_cause flag and label are still
      computed with priority:
          trend > shift > 2of3 > astronomical
    """
    # Prepare working DataFrame
    work = _prepare_series(data, value_col=value_col, index_col=index_col)
    values = work[value_col]
    n_points = len(values)

    # Minimal structure when not enough points overall
    if n_points < min_points_for_spc:
        work = work.copy()
        # Even if phase_starts provided, for very short series we keep it simple
        work["phase"] = 1
        work["mean"] = np.nan
        work["sigma"] = np.nan
        work["ucl"] = np.nan
        work["lcl"] = np.nan

        for r in ("trend", "shift", "2of3", "astronomical"):
            work[f"rule_{r}"] = False

        work["special_cause"] = False
        work["special_cause_label"] = ""

        config = XmrConfig(
            value_col=value_col,
            index_col=index_col,
            group_cols=None,
            baseline_mode=baseline_mode,
            baseline_points=baseline_points,
            min_points_for_spc=min_points_for_spc,
            shift_length=shift_length,
            trend_length=trend_length,
            rules=rules,
        )

        return XmrResult(data=work, config=config)

    # Assign phases (may be all 1 if phase_starts is None/empty)
    phases = _assign_phases(values.index, phase_starts)
    work = work.copy()
    work["phase"] = phases

    # Prepare containers for statistics and rules
    work["mean"] = np.nan
    work["sigma"] = np.nan
    work["ucl"] = np.nan
    work["lcl"] = np.nan

    for r in ("trend", "shift", "2of3", "astronomical"):
        work[f"rule_{r}"] = False

    rules_set = set(rules)
    rule_flags: Dict[str, pd.Series] = {
        "trend": pd.Series(False, index=work.index),
        "shift": pd.Series(False, index=work.index),
        "2of3": pd.Series(False, index=work.index),
        "astronomical": pd.Series(False, index=work.index),
    }

    # Apply baseline and rules within each phase
    for phase_value in sorted(work["phase"].unique()):
        phase_mask = work["phase"] == phase_value
        phase_values = values[phase_mask]

        # Compute baseline for this phase
        baseline_mask_phase = _compute_baseline_mask(
            values=phase_values,
            baseline_mode=baseline_mode,
            baseline_points=baseline_points,
        )

        mean, sigma, ucl, lcl = _compute_limits_from_baseline(
            values=phase_values,
            baseline_mask=baseline_mask_phase,
        )

        # Assign stats
        work.loc[phase_mask, "mean"] = mean
        work.loc[phase_mask, "sigma"] = sigma
        work.loc[phase_mask, "ucl"] = ucl
        work.loc[phase_mask, "lcl"] = lcl

        # If we cannot compute sigma properly, skip rules for this phase
        if np.isnan(mean) or np.isnan(sigma) or sigma <= 0:
            continue

        # Apply rules for this phase only
        phase_index = phase_values.index

        if "astronomical" in rules_set:
            astro = _rule_astronomical(phase_values, mean=mean, sigma=sigma)
            rule_flags["astronomical"].loc[phase_index] = astro
        if "2of3" in rules_set:
            twoof3 = _rule_2of3(phase_values, mean=mean, sigma=sigma)
            rule_flags["2of3"].loc[phase_index] = twoof3
        if "shift" in rules_set:
            shift_flag = _rule_shift(phase_values, mean=mean, shift_length=shift_length)
            rule_flags["shift"].loc[phase_index] = shift_flag
        if "trend" in rules_set:
            trend_flag = _rule_trend(phase_values, trend_length=trend_length)
            rule_flags["trend"].loc[phase_index] = trend_flag

    # Attach individual rule columns
    for name, series in rule_flags.items():
        work[f"rule_{name}"] = series.reindex(work.index).fillna(False)

    # Aggregate to special_cause + label with priority:
    # trend > shift > 2of3 > astronomical
    priority_order: List[str] = ["trend", "shift", "2of3", "astronomical"]

    special_cause = pd.Series(False, index=work.index)
    labels = pd.Series("", index=work.index, dtype=object)

    for idx in work.index:
        label = ""
        for rule_name in priority_order:
            if rule_flags[rule_name].get(idx, False):
                label = rule_name
                break
        if label:
            special_cause.loc[idx] = True
            labels.loc[idx] = label

    work["special_cause"] = special_cause
    work["special_cause_label"] = labels

    # Build config and result
    config = XmrConfig(
        value_col=value_col,
        index_col=index_col,
        group_cols=None,
        baseline_mode=baseline_mode,
        baseline_points=baseline_points,
        min_points_for_spc=min_points_for_spc,
        shift_length=shift_length,
        trend_length=trend_length,
        rules=rules,
    )

    return XmrResult(data=work, config=config)


# --------------------------------------------------------------------
# Public API: multi-series analysis
# --------------------------------------------------------------------


def analyse_xmr_by_group(
    data: pd.DataFrame,
    value_col: str,
    index_col: str,
    group_cols: Union[str, Sequence[str]],
    phase_starts: Optional[Dict[Tuple, Sequence[Union[str, pd.Timestamp]]]] = None,
    baseline_mode: str = "all",
    baseline_points: Optional[int] = None,
    min_points_for_spc: int = 10,
    shift_length: int = 8,
    trend_length: int = 6,
    rules: Sequence[str] = ("trend", "shift", "2of3", "astronomical"),
) -> MultiXmrResult:
    """
    Analyse many time series (e.g. one per trust) using Making Data Count XmR rules.

    - data: a DataFrame containing at least value_col, index_col, and group_cols.
    - group_cols: a column name or list of column names that define a series
      (e.g. 'OrgCode' or ['OrgCode', 'MetricName']).

    For each distinct combination of group_cols:
    - The rows are extracted as a subset.
    - analyse_xmr is called on that subset with the same configuration.
    - The resulting per-point data is returned with the group_cols attached.

    phase_starts for multi-series:
    - May be None (no manual phases).
    - Or a dict keyed by group tuple -> sequence of phase start labels.
      Example key shapes:
        {('RKB',): [...]} if group_cols=('OrgCode',)
        {('RKB', 'AE4hr'): [...]} if group_cols=('OrgCode', 'MetricName')
    """
    if value_col not in data.columns:
        raise ValueError(f"value_col '{value_col}' not found in DataFrame")
    if index_col not in data.columns:
        raise ValueError(f"index_col '{index_col}' not found in DataFrame")

    # Normalise group_cols to a list of strings
    if isinstance(group_cols, str):
        group_cols_list: List[str] = [group_cols]
    else:
        group_cols_list = list(group_cols)

    for gc in group_cols_list:
        if gc not in data.columns:
            raise ValueError(f"group_col '{gc}' not found in DataFrame")

    # Normalise phase_starts dict (may be None for now)
    phase_starts = phase_starts or {}

    all_result_frames: List[pd.DataFrame] = []
    by_group: Dict[Tuple, XmrResult] = {}

    # Group the data by the requested columns
    grouped = data.groupby(group_cols_list, dropna=False)

    for key, group_df in grouped:
        # Normalise group key to a tuple
        if not isinstance(key, tuple):
            key_tuple = (key,)
        else:
            key_tuple = key

        # Look up any phase starts for this group
        group_phase_starts = phase_starts.get(key_tuple)
        if group_phase_starts is None and len(key_tuple) == 1:
            # Also allow using the scalar key in the dict, for convenience
            group_phase_starts = phase_starts.get(key_tuple[0])

        # Run single-series analysis for this group
        group_result = analyse_xmr(
            data=group_df,
            value_col=value_col,
            index_col=index_col,
            phase_starts=group_phase_starts,
            baseline_mode=baseline_mode,
            baseline_points=baseline_points,
            min_points_for_spc=min_points_for_spc,
            shift_length=shift_length,
            trend_length=trend_length,
            rules=rules,
        )

        # Attach group columns back onto the result.data
        result_df = group_result.data.copy()

        # Build a small meta frame with index_col + group_cols to align on index
        meta_cols = [index_col] + group_cols_list
        meta = group_df[meta_cols].drop_duplicates(subset=[index_col]).set_index(index_col)
        # Reindex meta to match result_df's index (which is set to index_col in analyse_xmr)
        meta = meta.reindex(result_df.index)

        for gc in group_cols_list:
            result_df[gc] = meta[gc].values

        # Wrap back into an XmrResult
        group_result_with_groups = XmrResult(data=result_df, config=group_result.config)

        all_result_frames.append(result_df)
        by_group[key_tuple] = group_result_with_groups

    if not all_result_frames:
        # No data
        combined = pd.DataFrame()
    else:
        combined = pd.concat(all_result_frames, axis=0)

        # Sort by group_cols + index_col for tidy output
        sort_cols = list(group_cols_list) + [index_col]
        combined = combined.sort_values(sort_cols)

    # Build a config that reflects the multi-group setup
    multi_config = XmrConfig(
        value_col=value_col,
        index_col=index_col,
        group_cols=group_cols_list,
        baseline_mode=baseline_mode,
        baseline_points=baseline_points,
        min_points_for_spc=min_points_for_spc,
        shift_length=shift_length,
        trend_length=trend_length,
        rules=rules,
    )

    return MultiXmrResult(data=combined, by_group=by_group, config=multi_config)


# --------------------------------------------------------------------
# Public API: plotting
# --------------------------------------------------------------------


def plot_xmr(
    result: XmrResult,
    value_label: Optional[str] = None,
    title: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 5),
    show: bool = True,
):
    """
    Make an XmR chart from an XmrResult.

    - Plots the value series over time (or index order).
    - Draws horizontal lines for mean, UCL and LCL per phase.
    - Highlights special-cause points (using the combined special_cause flag).

    Parameters
    ----------
    result : XmrResult
        Output of analyse_xmr for a single series.
    value_label : str, optional
        Y-axis label. Defaults to the value column name from result.config.
    title : str, optional
        Plot title. If None, a basic title is generated.
    figsize : (int, int), optional
        Figure size passed to matplotlib.
    show : bool, optional
        If True (default), calls plt.show() at the end.
        If False, returns (fig, ax) so the caller can manage display.
    """
    df = result.data.copy()
    cfg = result.config

    if df.empty:
        raise ValueError("XmrResult.data is empty; nothing to plot.")

    # X-axis: use the DataFrame index (this is the index_col if provided)
    x = df.index
    y = df[cfg.value_col]

    fig, ax = plt.subplots(figsize=figsize)

    # Plot the main series
    ax.plot(x, y, marker="o", linestyle="-", label="Values")

    # Phase-aware mean and limits
    if "phase" in df.columns and df["phase"].nunique() > 1:
        phases = sorted(df["phase"].unique())
        first_phase = phases[0]

        for phase_value in phases:
            phase_mask = df["phase"] == phase_value
            if not phase_mask.any():
                continue

            x_phase = x[phase_mask]
            mean = df.loc[phase_mask, "mean"].iloc[0]
            ucl = df.loc[phase_mask, "ucl"].iloc[0]
            lcl = df.loc[phase_mask, "lcl"].iloc[0]

            xmin = x_phase.min()
            xmax = x_phase.max()

            label_mean = "Mean" if phase_value == first_phase else None
            label_ucl = "UCL" if phase_value == first_phase else None
            label_lcl = "LCL" if phase_value == first_phase else None

            if np.isfinite(mean):
                ax.hlines(mean, xmin, xmax, linestyles="--", linewidth=1, label=label_mean)
            if np.isfinite(ucl):
                ax.hlines(ucl, xmin, xmax, linestyles=":", linewidth=1, label=label_ucl)
            if np.isfinite(lcl):
                ax.hlines(lcl, xmin, xmax, linestyles=":", linewidth=1, label=label_lcl)

        # Optional: draw vertical lines at phase boundaries (except before phase 1)
        for phase_value in phases[1:]:
            boundary_mask = df["phase"] == phase_value
            if not boundary_mask.any():
                continue
            x_boundary = x[boundary_mask].min()
            ax.axvline(x_boundary, linestyle="--", linewidth=0.7)
    else:
        # Single phase (or no phase column) – use the first row's stats
        mean = df["mean"].iloc[0]
        ucl = df["ucl"].iloc[0]
        lcl = df["lcl"].iloc[0]

        if np.isfinite(mean):
            ax.axhline(mean, linestyle="--", linewidth=1, label="Mean")
        if np.isfinite(ucl):
            ax.axhline(ucl, linestyle=":", linewidth=1, label="UCL")
        if np.isfinite(lcl):
            ax.axhline(lcl, linestyle=":", linewidth=1, label="LCL")

    # Highlight special-cause points, if present
    if "special_cause" in df.columns:
        sc_mask = df["special_cause"].astype(bool)
        if sc_mask.any():
            ax.scatter(
                x[sc_mask],
                y[sc_mask],
                s=80,
                edgecolors="red",
                facecolors="none",
                linewidths=1.5,
                label="Special cause",
            )

    # Axis labels and title
    ax.set_ylabel(value_label or cfg.value_col)
    ax.set_xlabel(cfg.index_col or "Index")

    if title is None:
        title = "XmR chart"
    ax.set_title(title)

    # Improve x-axis formatting a bit
    fig.autofmt_xdate(rotation=45)

    # Show legend only if there are labelled artists
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend()

    fig.tight_layout()

    if show:
        plt.show()
        return None, ax
    else:
        return fig, ax
