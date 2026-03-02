import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import pandas as pd
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.dates as mdates
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.ticker import FormatStrFormatter

from . import analyse_xmr_by_group, summarise_xmr_by_group
from .metric_config import load_metric_config, get_metric_config

"""
mdcspc.exporter

Public, library-level interface for exporting SPC charts and summaries
from a long-format CSV using the MDC SPC conventions.
"""

PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_PROJECT_ROOT = PACKAGE_ROOT.parent
DEFAULT_CONFIG_DIR = DEFAULT_PROJECT_ROOT / "config"
DEFAULT_WORKING_DIR = DEFAULT_PROJECT_ROOT / "working"
DEFAULT_ASSETS_DIR = DEFAULT_PROJECT_ROOT / "assets"


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


def _detect_group_cols(df: pd.DataFrame) -> List[str]:
    """Guess sensible group columns from the input DataFrame."""
    if "OrgCode" in df.columns and "MetricName" in df.columns:
        return ["OrgCode", "MetricName"]

    if "OrgCode" in df.columns:
        return ["OrgCode"]

    exclude = {"Month", "Date", "Value"}
    candidate: List[str] = []
    for col in df.columns:
        if col not in exclude:
            candidate.append(col)

    if not candidate:
        raise ValueError(
            "Could not detect group columns. "
            "Expected at least 'OrgCode' and/or 'MetricName', "
            "or some other non-date, non-value column."
        )

    return candidate


def _safe_filename(parts: Sequence[object]) -> str:
    """Build a filesystem-safe filename from a list/tuple of parts."""
    text = "__".join(str(p) for p in parts if p is not None)
    return re.sub(r"[^A-Za-z0-9._-]+", "_", text)


# -------------------------------------------------------------------
# Phase configuration loader
# -------------------------------------------------------------------


def _load_phase_config(
    working_dir: Path,
    group_cols: Sequence[str],
) -> Optional[Dict[Tuple, List[pd.Timestamp]]]:
    """
    Load optional phase configuration from working/spc_phase_config.csv.

    Expected columns:
        group_cols (e.g. OrgCode, MetricName)
        PhaseStart
    """
    config_path = working_dir / "spc_phase_config.csv"

    if not config_path.exists():
        print("[INFO] No spc_phase_config.csv found – running all series as single-phase.")
        return None

    print(f"[INFO] Loading phase configuration from: {config_path}")

    cfg = pd.read_csv(config_path)

    if "PhaseStart" not in cfg.columns:
        raise ValueError(
            "Phase config must contain a 'PhaseStart' column "
            "with the start date of each new phase."
        )

    # Parse deterministically: ISO dates (YYYY-MM-DD) with explicit format
    cfg["PhaseStart"] = pd.to_datetime(cfg["PhaseStart"], format="%Y-%m-%d", errors="raise")


    missing = [gc for gc in group_cols if gc not in cfg.columns]
    if missing:
        raise ValueError(
            f"Phase config is missing required group column(s): {missing}. "
            f"Expected at least these columns: {list(group_cols) + ['PhaseStart']}"
        )

    if "PhaseStart" not in cfg.columns:
        raise ValueError(
            "Phase config must contain a 'PhaseStart' column "
            "with the start date of each new phase."
        )

    phase_starts: Dict[Tuple, List[pd.Timestamp]] = {}

    grouped_cfg = cfg.groupby(list(group_cols), dropna=False)
    for key, group_df in grouped_cfg:
        if not isinstance(key, tuple):
            key_tuple = (key,)
        else:
            key_tuple = key

        starts = (
            group_df["PhaseStart"]
            .dropna()
            .sort_values()
            .unique()
        )

        if len(starts) == 0:
            continue

        phase_starts[key_tuple] = list(starts)

    if not phase_starts:
        print(
            "[INFO] Phase config loaded, but no valid PhaseStart values found; "
            "all series will be single-phase."
        )
        return None

    print(f"[INFO] Phase configuration loaded for {len(phase_starts)} series.")
    return phase_starts


# -------------------------------------------------------------------
# Direction configuration from central metric_config
# -------------------------------------------------------------------


def _build_directions_by_group_from_metric_config(
    multi: Any,
    group_cols: Sequence[str],
    metric_configs: Optional[Dict[str, Any]],
) -> Optional[Dict[Tuple, str]]:
    """
    Build directions_by_group mapping from central metric_config.

    Keys: group tuples from multi.by_group
    Values: direction string ("higher_is_better", "lower_is_better", "neutral")
    """
    if not metric_configs:
        print(
            "[INFO] metric_config: no central metric config available for directions; "
            "using global default direction only."
        )
        return None

    if "MetricName" not in group_cols:
        print(
            "[INFO] metric_config: 'MetricName' not in group_cols; "
            "directions_by_group will not use central config."
        )
        return None

    metric_idx = group_cols.index("MetricName")

    directions_by_group: Dict[Tuple, str] = {}
    missing_metrics = set()
    used_metrics = set()

    for key in multi.by_group.keys():
        if not isinstance(key, tuple):
            key_tuple = (key,)
        else:
            key_tuple = key

        if metric_idx >= len(key_tuple):
            continue

        metric_name = str(key_tuple[metric_idx])
        metric_cfg = get_metric_config(metric_name, metric_configs, default=None)
        if metric_cfg is None:
            missing_metrics.add(metric_name)
            continue

        dir_raw = getattr(metric_cfg, "direction", None)
        if dir_raw is None:
            dir_raw = getattr(metric_cfg, "Direction", None)

        if not dir_raw:
            missing_metrics.add(metric_name)
            continue

        dir_norm = str(dir_raw).strip().lower()
        if dir_norm in ("higher", "higher_is_better", "up"):
            dir_norm = "higher_is_better"
        elif dir_norm in ("lower", "lower_is_better", "down"):
            dir_norm = "lower_is_better"
        elif dir_norm in ("neutral", "two_sided", "two-sided"):
            dir_norm = "neutral"

        directions_by_group[key_tuple] = dir_norm
        used_metrics.add(metric_name)

    if used_metrics:
        print(
            "[INFO] metric_config: directions_by_group built from central config "
            f"for {len(directions_by_group)} series ({len(used_metrics)} MetricName(s))."
        )
    else:
        print(
            "[INFO] metric_config: no usable Direction found in central config "
            "for any MetricName; using global default direction only."
        )
        return None

    if missing_metrics:
        print(
            "[INFO] metric_config: no Direction in central config for MetricName(s) "
            f"in this dataset (using global default for them): {sorted(missing_metrics)}"
        )

    return directions_by_group


# -------------------------------------------------------------------
# Target configuration loader
# -------------------------------------------------------------------


def _load_target_config(
    config_dir: Path,
    working_dir: Path,
    group_cols: Sequence[str],
) -> Optional[pd.DataFrame]:
    """
    Load optional target configuration, preferring:

        config/spc_target_config.csv

    and falling back to:

        working/spc_target_config.csv
    """
    canonical_path = config_dir / "spc_target_config.csv"
    legacy_path = working_dir / "spc_target_config.csv"

    if canonical_path.exists():
        config_path = canonical_path
        print(f"[INFO] Loading target configuration from central config: {config_path}")
    elif legacy_path.exists():
        config_path = legacy_path
        print(
            "[INFO] Loading target configuration from working directory "
            f"(legacy/demo): {config_path}"
        )
    else:
        print(
            "[INFO] No spc_target_config.csv found in config/ or working/ – "
            "no time-varying targets will be used."
        )
        return None

    cfg = pd.read_csv(
        config_path,
        parse_dates=["EffectiveFrom"],
        dayfirst=True,
    )

    required = ["MetricName", "EffectiveFrom", "TargetValue"]
    if "OrgCode" in group_cols:
        required.append("OrgCode")

    missing = [c for c in required if c not in cfg.columns]
    if missing:
        raise ValueError(
            f"Target config is missing required column(s): {missing}. "
            "Expected at least: MetricName, EffectiveFrom, TargetValue, "
            "and OrgCode if using per-org targets."
        )

    cfg["MetricName"] = cfg["MetricName"].astype(str).str.strip()
    if "OrgCode" in cfg.columns:
        cfg["OrgCode"] = cfg["OrgCode"].astype(str).str.strip()

    return cfg


def _build_targets_by_group(
    multi: Any,
    group_cols: Sequence[str],
    target_cfg: Optional[pd.DataFrame],
) -> Optional[Dict[Tuple, pd.Series]]:
    """
    Build targets_by_group mapping for summarise_xmr_by_group.

    Keys: group key tuples
    Values: Series of target values indexed as group_result.data.index
    """
    if target_cfg is None:
        return None

    if "MetricName" not in group_cols:
        print(
            "[INFO] Target config found but 'MetricName' is not in group_cols; "
            "targets_by_group will not be used."
        )
        return None

    use_org = "OrgCode" in group_cols and "OrgCode" in target_cfg.columns

    target_key_cols = ["MetricName"]
    if use_org:
        target_key_cols.insert(0, "OrgCode")

    temp_map: Dict[Tuple, List[Tuple[pd.Timestamp, float]]] = {}

    grouped_cfg = target_cfg.groupby(target_key_cols, dropna=False)
    for key, group_df in grouped_cfg:
        if not isinstance(key, tuple):
            key_tuple = (key,)
        else:
            key_tuple = key

        g_sorted = group_df.sort_values("EffectiveFrom")
        effs = g_sorted["EffectiveFrom"].tolist()
        vals = g_sorted["TargetValue"].astype(float).tolist()

        pairs = [(eff, val) for eff, val in zip(effs, vals) if pd.notna(eff)]
        if pairs:
            temp_map[key_tuple] = pairs

    if not temp_map:
        print(
            "[INFO] Target config loaded, but no valid EffectiveFrom/TargetValue pairs found."
        )
        return None

    targets_by_group: Dict[Tuple, pd.Series] = {}

    group_cols_list = list(group_cols)

    for key, group_result in multi.by_group.items():
        if not isinstance(key, tuple):
            key_tuple = (key,)
        else:
            key_tuple = key

        metric_name = None
        org_code = None

        if "MetricName" in group_cols_list:
            metric_idx = group_cols_list.index("MetricName")
            if metric_idx < len(key_tuple):
                metric_name = str(key_tuple[metric_idx])

        if use_org and "OrgCode" in group_cols_list:
            org_idx = group_cols_list.index("OrgCode")
            if org_idx < len(key_tuple):
                org_code = str(key_tuple[org_idx])

        if metric_name is None:
            continue

        if use_org:
            target_key = (org_code, metric_name)
        else:
            target_key = (metric_name,)

        if target_key not in temp_map:
            continue

        pairs = temp_map[target_key]
        dates = list(group_result.data.index)

        values: List[float] = []
        for d in dates:
            chosen = float("nan")
            for eff, val in pairs:
                if eff <= d:
                    chosen = val
                else:
                    break
            values.append(chosen)

        target_series = pd.Series(values, index=group_result.data.index)
        targets_by_group[key_tuple] = target_series

    if not targets_by_group:
        print(
            "[INFO] Target config loaded, but no matching series found; "
            "targets_by_group will be empty."
        )
        return None

    print(f"[INFO] targets_by_group built for {len(targets_by_group)} series.")
    return targets_by_group


# -------------------------------------------------------------------
# Plotting helpers
# -------------------------------------------------------------------


def _classify_point_colour(
    value: float,
    mean: float,
    special_cause: bool,
    direction: str,
    special_cause_label: str = "",
    trend_direction: Optional[str] = None,
) -> str:
    """
    Return a matplotlib colour for a single point based on MDC rules.
    """
    if (not special_cause) or pd.isna(value):
        return "#A6A6A6"

    label = (special_cause_label or "").strip().lower()
    direction = (direction or "").strip().lower()

    if label == "trend" and trend_direction in {"up", "down"}:
        if direction == "neutral":
            return "#490092"
        if direction == "higher_is_better":
            return "#00B0F0" if trend_direction == "up" else "#E46C0A"
        if direction == "lower_is_better":
            return "#00B0F0" if trend_direction == "down" else "#E46C0A"
        return "#490092"

    if direction == "neutral":
        return "#490092"

    if pd.isna(mean):
        return "#A6A6A6"

    if value > mean:
        side = "high"
    elif value < mean:
        side = "low"
    else:
        return "#A6A6A6"

    if direction == "higher_is_better":
        return "#00B0F0" if side == "high" else "#E46C0A"
    if direction == "lower_is_better":
        return "#E46C0A" if side == "high" else "#00B0F0"

    return "#A6A6A6"


def _overlay_icon(ax, icon_path: Path, xy: Tuple[float, float], zoom: float = 0.18) -> None:
    """Overlay a PNG icon at a given axes-fraction coordinate."""
    if not icon_path or not icon_path.exists():
        return

    try:
        arr = mpimg.imread(str(icon_path))
    except Exception:
        return

    imagebox = OffsetImage(arr, zoom=zoom)
    ab = AnnotationBbox(
        imagebox,
        xy,
        xycoords="axes fraction",
        frameon=False,
        box_alignment=(1, 1),
    )
    ax.add_artist(ab)


def _draw_target_line(
    ax,
    x_index: pd.Index,
    target_series: pd.Series,
) -> None:
    """Draw time-varying target line in red across the dataset."""
    if target_series is None:
        return

    ts = target_series.copy()
    if ts.dropna().empty:
        return

    current_val = None
    current_start = None
    last_date = None

    for date, val in ts.items():
        if pd.isna(val):
            if current_val is not None and current_start is not None and last_date is not None:
                ax.hlines(
                    current_val,
                    xmin=current_start,
                    xmax=last_date,
                    colors="#FF0000",
                    linestyles="-",
                    linewidth=1.8,
                    zorder=0.7,
                )
            current_val = None
            current_start = None
            last_date = None
            continue

        if current_val is None:
            current_val = val
            current_start = date
            last_date = date
        else:
            if val == current_val:
                last_date = date
            else:
                if current_start is not None and last_date is not None:
                    ax.hlines(
                        current_val,
                        xmin=current_start,
                        xmax=last_date,
                        colors="#FF0000",
                        linestyles="-",
                        linewidth=1.8,
                        zorder=0.7,
                    )
                current_val = val
                current_start = date
                last_date = date

    if current_val is not None and current_start is not None and last_date is not None:
        ax.hlines(
            current_val,
            xmin=current_start,
            xmax=last_date,
            colors="#FF0000",
            linestyles="-",
            linewidth=1.8,
            zorder=0.7,
        )


# -------------------------------------------------------------------
# Chart plotting
# -------------------------------------------------------------------


def _plot_mdc_chart_for_series(
    key_tuple: Tuple,
    group_result: Any,
    group_values: Sequence[object],
    group_cols: Sequence[str],
    value_col: str,
    charts_dir: Path,
    summary: pd.DataFrame,
    icons_dir: Path,
    targets_by_group: Optional[Dict[Tuple, pd.Series]],
    metric_configs: Optional[Dict[str, Any]],
    chart_mode: str = "xmr",
) -> None:
    """
    Create an MDC-style chart for a single series.

    chart_mode:
        - "x_only" : X chart only.
        - "xmr"    : Combined X (top) + mR (bottom) chart.
    """
    df = group_result.data.copy()
    if df.empty:
        return

    chart_mode = (chart_mode or "xmr").lower()
    if chart_mode not in ("x_only", "xmr"):
        chart_mode = "xmr"

    title_parts = [str(v) for v in group_values]
    title = " – ".join(title_parts + ["XmR chart"])

    filename_base = _safe_filename(group_values)
    filename = f"{filename_base}.png"
    filepath = charts_dir / filename

    summary_row = None
    if not summary.empty and group_cols:
        mask = pd.Series(True, index=summary.index)
        for col, val in zip(group_cols, group_values):
            mask &= summary[col].astype(str) == str(val)
        matches = summary[mask]
        if not matches.empty:
            summary_row = matches.iloc[0]

    if summary_row is not None:
        direction = str(summary_row.get("direction", "higher_is_better"))
        variation_icon_name = summary_row.get("variation_icon", "")
        assurance_icon_name = summary_row.get("assurance_icon", "")
        target_value_static = float(summary_row.get("target_value", float("nan")))
    else:
        direction = "higher_is_better"
        variation_icon_name = ""
        assurance_icon_name = ""
        target_value_static = float("nan")

    variation_icon_path = (
        icons_dir / str(variation_icon_name)
        if variation_icon_name
        else Path()
    )
    assurance_icon_path = (
        icons_dir / str(assurance_icon_name)
        if assurance_icon_name
        else Path()
    )

    target_series = None
    if targets_by_group is not None and key_tuple in targets_by_group:
        target_series = targets_by_group[key_tuple]

    metric_cfg = None
    metric_name = None
    if metric_configs and "MetricName" in group_cols:
        metric_idx = group_cols.index("MetricName")
        if metric_idx < len(group_values):
            metric_name = str(group_values[metric_idx])
            metric_cfg = get_metric_config(metric_name, metric_configs, default=None)

    # Unit + decimal places from metric config
    scale_factor = 1.0
    unit = None
    decimal_places: Optional[int] = None

    if metric_cfg is not None:
        unit = getattr(metric_cfg, "unit", None) or getattr(metric_cfg, "Unit", None)
        # IMPORTANT: don't use "or" here because 0 is a valid value
        decimal_places = getattr(metric_cfg, "decimal_places", None)
        if decimal_places is None:
            decimal_places = getattr(metric_cfg, "DecimalPlaces", None)

    unit_norm = (unit or "").strip().lower()

    # If DecimalPlaces is not configured, choose a sensible default:
    # - Unit == "count"   -> 0 dp (whole people/episodes)
    # - Unit == "percent" -> 1 dp
    # - everything else   -> 1 dp
    if decimal_places is None:
        if unit_norm == "count":
            decimal_places = 0
        elif unit_norm == "percent":
            decimal_places = 1
        else:
            decimal_places = 1

    # Percent scaling logic
    if unit_norm == "percent":
        candidate_vals: List[float] = []
        if value_col in df.columns:
            candidate_vals.extend(
                [float(v) for v in df[value_col].dropna().tolist()]
            )
        for col in ("mean", "ucl", "lcl"):
            if col in df.columns:
                candidate_vals.extend(
                    [float(v) for v in df[col].dropna().tolist()]
                )
        if target_series is not None:
            candidate_vals.extend(
                [float(v) for v in target_series.dropna().tolist()]
            )
        if not pd.isna(target_value_static):
            candidate_vals.append(float(target_value_static))

        if candidate_vals:
            v_min = min(candidate_vals)
            v_max = max(candidate_vals)
            if 0.0 <= v_min and v_max <= 1.2:
                scale_factor = 100.0

    if scale_factor != 1.0:
        df[value_col] = df[value_col] * scale_factor
        for col in ("mean", "ucl", "lcl"):
            if col in df.columns:
                df[col] = df[col] * scale_factor
        if target_series is not None:
            target_series = target_series * scale_factor
        if not pd.isna(target_value_static):
            target_value_static = target_value_static * scale_factor

    x = df.index

    if chart_mode == "xmr":
        fig, (ax_x, ax_mr) = plt.subplots(
            nrows=2,
            ncols=1,
            sharex=True,
            figsize=(10, 8),
            gridspec_kw={"height_ratios": [2, 1]},
        )
    else:
        fig, ax_x = plt.subplots(figsize=(10, 5))
        ax_mr = None

    # -----------------------
    # X chart
    # -----------------------
    y = df[value_col]

    ax_x.plot(
        x,
        y,
        linestyle="-",
        linewidth=2.0,
        color="#A6A6A6",
        zorder=1,
    )

    if "phase" in df.columns:
        for _, g in df.groupby("phase"):
            mean_val = g["mean"].dropna().iloc[0] if g["mean"].notna().any() else None
            ucl_val = g["ucl"].dropna().iloc[0] if g["ucl"].notna().any() else None
            lcl_val = g["lcl"].dropna().iloc[0] if g["lcl"].notna().any() else None

            if mean_val is not None:
                ax_x.hlines(
                    mean_val,
                    xmin=g.index.min(),
                    xmax=g.index.max(),
                    colors="#000000",
                    linestyles="-",
                    linewidth=2.0,
                    zorder=0,
                )
            if ucl_val is not None:
                ax_x.hlines(
                    ucl_val,
                    xmin=g.index.min(),
                    xmax=g.index.max(),
                    colors="#777777",
                    linestyles="dashed",
                    linewidth=1.5,
                    zorder=0,
                )
            if lcl_val is not None:
                ax_x.hlines(
                    lcl_val,
                    xmin=g.index.min(),
                    xmax=g.index.max(),
                    colors="#777777",
                    linestyles="dashed",
                    linewidth=1.5,
                    zorder=0,
                )
    else:
        if "mean" in df.columns and df["mean"].notna().any():
            mean_val = df["mean"].dropna().iloc[0]
            ax_x.hlines(
                mean_val,
                xmin=x.min(),
                xmax=x.max(),
                colors="#000000",
                linestyles="-",
                linewidth=2.0,
                zorder=0,
            )
        if "ucl" in df.columns and df["ucl"].notna().any():
            ucl_val = df["ucl"].dropna().iloc[0]
            ax_x.hlines(
                ucl_val,
                xmin=x.min(),
                xmax=x.max(),
                colors="#777777",
                linestyles="dashed",
                linewidth=1.5,
                zorder=0,
            )
        if "lcl" in df.columns and df["lcl"].notna().any():
            lcl_val = df["lcl"].dropna().iloc[0]
            ax_x.hlines(
                lcl_val,
                xmin=x.min(),
                xmax=x.max(),
                colors="#777777",
                linestyles="dashed",
                linewidth=1.5,
                zorder=0,
            )

    if target_series is not None:
        _draw_target_line(ax_x, x_index=df.index, target_series=target_series)
    else:
        if not pd.isna(target_value_static):
            ax_x.hlines(
                target_value_static,
                xmin=x.min(),
                xmax=x.max(),
                colors="#FF0000",
                linestyles="-",
                linewidth=1.8,
                zorder=0.7,
            )

    specials = (
        df.get("special_cause", False).astype(bool)
        if "special_cause" in df.columns
        else pd.Series(False, index=df.index)
    )

    trend_directions: Dict[Any, str] = {}
    if "special_cause_label" in df.columns and value_col in df.columns:
        labels_list = df["special_cause_label"].astype(str).fillna("").tolist()
        values_list = df[value_col].tolist()
        idx_list = list(df.index)
        n = len(idx_list)
        i = 0
        while i < n:
            if labels_list[i].strip().lower() != "trend":
                i += 1
                continue
            run_indices = [i]
            j = i + 1
            while j < n and labels_list[j].strip().lower() == "trend":
                run_indices.append(j)
                j += 1

            start_val = values_list[run_indices[0]]
            end_val = values_list[run_indices[-1]]
            trend_dir: Optional[str] = None

            if pd.notna(start_val) and pd.notna(end_val):
                if end_val > start_val:
                    trend_dir = "up"
                elif end_val < start_val:
                    trend_dir = "down"

            if trend_dir is None:
                for k in range(run_indices[0] + 1, run_indices[-1] + 1):
                    v_prev = values_list[k - 1]
                    v_cur = values_list[k]
                    if pd.notna(v_prev) and pd.notna(v_cur):
                        if v_cur > v_prev:
                            trend_dir = "up"
                            break
                        elif v_cur < v_prev:
                            trend_dir = "down"
                            break

            if trend_dir is None:
                trend_dir = "up"

            for k in run_indices:
                trend_directions[idx_list[k]] = trend_dir

            i = j

    colours: List[str] = []
    for idx, row in df.iterrows():
        val = row[value_col]
        mean_val = row.get("mean", float("nan"))
        sc = bool(specials.loc[idx])
        label = str(row.get("special_cause_label", "") or "")
        trend_dir = trend_directions.get(idx)
        colour = _classify_point_colour(
            value=val,
            mean=mean_val,
            special_cause=sc,
            direction=direction,
            special_cause_label=label,
            trend_direction=trend_dir,
        )
        colours.append(colour)

    ax_x.scatter(
        x,
        y,
        c=colours,
        s=50,
        zorder=2,
    )

    ax_x.set_title(title)
    ax_x.set_xlabel("Month")
    ylabel = value_col
    if unit_norm == "percent":
        ylabel = f"{ylabel} (%)"
    ax_x.set_ylabel(ylabel)

    ymin, ymax = ax_x.get_ylim()
    span = ymax - ymin if ymax > ymin else 1.0
    ax_x.set_ylim(ymin, ymax + 0.20 * span)

    # -----------------------
    # mR chart
    # -----------------------
    if chart_mode == "xmr" and ax_mr is not None:
        mr = df[value_col].diff().abs()

        ax_mr.plot(
            x,
            mr,
            linestyle="-",
            linewidth=1.5,
            color="#A6A6A6",
            zorder=1,
        )

        mr_valid = mr.dropna()
        ucl_mr = None
        mr_bar = None

        if not mr_valid.empty:
            mr_bar = mr_valid.mean()
            ucl_mr = mr_bar * 3.268  # Wheeler constant for XmR

            ax_mr.hlines(
                mr_bar,
                xmin=x.min(),
                xmax=x.max(),
                colors="#000000",
                linestyles="-",
                linewidth=1.5,
                zorder=0,
            )
            ax_mr.hlines(
                ucl_mr,
                xmin=x.min(),
                xmax=x.max(),
                colors="#777777",
                linestyles="dashed",
                linewidth=1.2,
                zorder=0,
            )

        ax_mr.scatter(
            x,
            mr,
            s=30,
            color="#A6A6A6",
            zorder=2,
        )

        if ucl_mr is not None:
            above = mr > ucl_mr
            if above.any():
                ax_mr.scatter(
                    x[above],
                    mr[above],
                    s=40,
                    color="#E46C0A",
                    marker="D",
                    zorder=3,
                )

        ax_mr.set_ylabel("Moving range")
        ax_mr.set_xlabel("Month")

    # -----------------------
    # Shared axis formatting
    # -----------------------
    if isinstance(x, pd.DatetimeIndex):
        ax_x.xaxis.set_major_locator(mdates.MonthLocator())
        ax_x.xaxis.set_major_formatter(mdates.DateFormatter("%b-%y"))
        for lbl in ax_x.get_xticklabels():
            lbl.set_rotation(90)
            lbl.set_ha("right")
            lbl.set_fontsize(8)
    else:
        ax_x.set_xticks(range(len(x)))
        ax_x.set_xticklabels([str(v) for v in x])
        for lbl in ax_x.get_xticklabels():
            lbl.set_rotation(90)
            lbl.set_ha("right")
            lbl.set_fontsize(8)

    # decimal_places should always be set by now, but guard anyway
    if decimal_places is None:
        decimal_places = 1

    try:
        dp_int = int(decimal_places)
        if unit_norm == "percent":
            fmt_str = f"%.{dp_int}f%%"
        else:
            fmt_str = f"%.{dp_int}f"
        ax_x.yaxis.set_major_formatter(FormatStrFormatter(fmt_str))
        if chart_mode == "xmr" and ax_mr is not None:
            ax_mr.yaxis.set_major_formatter(FormatStrFormatter(fmt_str))
    except Exception:
        pass

    _overlay_icon(ax_x, assurance_icon_path, xy=(0.88, 0.98), zoom=0.18)
    _overlay_icon(ax_x, variation_icon_path, xy=(0.98, 0.98), zoom=0.18)

    fig.tight_layout()
    fig.savefig(str(filepath), dpi=150)
    plt.close(fig)

    print(f"    [OK] {title} -> {filepath}")


# -------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------

def export_spc_from_csv(
    input_csv: Union[str, Path],
    working_dir: Optional[Union[str, Path]] = None,
    config_dir: Optional[Union[str, Path]] = None,
    icons_dir: Optional[Union[str, Path]] = None,
    value_col: str = "Value",
    index_col: str = "Month",
    summary_filename: str = "spc_summary_from_input.csv",
    charts_subdir: str = "charts",
    chart_mode: str = "xmr",
    quiet: bool = False,
) -> Tuple[pd.DataFrame, Any]:
    """
    Run XmR analysis and export SPC outputs from a long-format CSV.
    """
    input_path = Path(input_csv)
    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    if working_dir is None:
        working_dir_path = DEFAULT_WORKING_DIR
    else:
        working_dir_path = Path(working_dir)

    if config_dir is None:
        config_dir_path = DEFAULT_CONFIG_DIR
    else:
        config_dir_path = Path(config_dir)

    if icons_dir is None:
        icons_dir_path = DEFAULT_ASSETS_DIR / "icons"
    else:
        icons_dir_path = Path(icons_dir)

    charts_dir = working_dir_path / charts_subdir

    os.makedirs(working_dir_path, exist_ok=True)
    os.makedirs(charts_dir, exist_ok=True)

    def _log(msg: str) -> None:
        if not quiet:
            print(msg)

    _log(f"\n[INFO] Loading input CSV: {input_path}")
    _log(f"[INFO] chart_mode passed to exporter: {chart_mode}")

    # Read raw first, then parse dates explicitly and consistently.
    # We do NOT use pandas 'date_parser' (deprecated).
    df = pd.read_csv(input_path)

    if value_col not in df.columns:
        raise ValueError(f"Expected a '{value_col}' column in the input CSV.")

    if index_col not in df.columns:
        raise ValueError(f"Expected an '{index_col}' column in the input CSV for the index.")

    # Deterministic date parsing:
    # - If values are ISO (YYYY-MM-DD), parse with an explicit format (no ambiguity).
    # - Otherwise parse with dayfirst=True to match existing DataFrame/test behaviour.
    s = df[index_col].astype(str).str.strip()

    iso_mask = s.str.match(r"^\d{4}-\d{2}-\d{2}$", na=False)
    if iso_mask.any():
        parsed = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
        # ISO rows
        parsed.loc[iso_mask] = pd.to_datetime(s.loc[iso_mask], format="%Y-%m-%d", errors="raise")
        # Non-ISO rows (potentially ambiguous)
        if (~iso_mask).any():
            parsed.loc[~iso_mask] = pd.to_datetime(s.loc[~iso_mask], dayfirst=True, errors="raise")
        df[index_col] = parsed
    else:
        df[index_col] = pd.to_datetime(df[index_col], dayfirst=True, errors="raise")

    # Normalise to midnight for stable outputs/comparisons
    df[index_col] = df[index_col].dt.normalize()

    group_cols = _detect_group_cols(df)
    _log(f"[INFO] Using group columns: {group_cols}")

    try:
        metric_configs = load_metric_config()
        _log(f"[INFO] metric_config: loaded {len(metric_configs)} metric config(s).")
    except Exception as e:
        _log(
            "[INFO] metric_config: failed to load central metric config; "
            "directions/units/targets will use defaults only. "
            f"Error: {e}"
        )
        metric_configs = None

    phase_starts = _load_phase_config(working_dir=working_dir_path, group_cols=group_cols)

    multi = analyse_xmr_by_group(
        data=df,
        value_col=value_col,
        index_col=index_col,
        group_cols=group_cols,
        phase_starts=phase_starts,
        baseline_mode="all",
        baseline_points=None,
        min_points_for_spc=10,
        shift_length=6,
        trend_length=6,
        rules=("trend", "shift", "2of3", "astronomical"),
    )

    directions_by_group = _build_directions_by_group_from_metric_config(
        multi=multi,
        group_cols=group_cols,
        metric_configs=metric_configs,
    )

    target_cfg = _load_target_config(
        config_dir=config_dir_path,
        working_dir=working_dir_path,
        group_cols=group_cols,
    )
    targets_by_group = _build_targets_by_group(
        multi=multi,
        group_cols=group_cols,
        target_cfg=target_cfg,
    )

    summary = summarise_xmr_by_group(
        multi,
        direction="higher_is_better",
        lookback_points=12,
        directions_by_group=directions_by_group,
        targets_by_group=targets_by_group,
    )

    summary_path = working_dir_path / summary_filename
    summary.to_csv(summary_path, index=False)
    _log(f"[INFO] Summary table saved to: {summary_path}")

    _log("[INFO] Generating MDC-style charts for each series.")

    value_col_final = multi.config.value_col
    n_series = 0

    for key, group_result in multi.by_group.items():
        n_series += 1
        group_values = list(key)
        _plot_mdc_chart_for_series(
            key_tuple=key,
            group_result=group_result,
            group_values=group_values,
            group_cols=group_cols,
            value_col=value_col_final,
            charts_dir=charts_dir,
            summary=summary,
            icons_dir=icons_dir_path,
            targets_by_group=targets_by_group,
            metric_configs=metric_configs,
            chart_mode=chart_mode,
        )

    _log(f"[INFO] Generated {n_series} chart file(s) in: {charts_dir}\n")

    return summary, multi
