import os
import sys
from typing import List, Sequence, Tuple, Any

import pandas as pd

# -------------------------------------------------------------------
# Ensure project root (MDCpip) is on sys.path so "import mdcspc" works
# regardless of where this script is launched from.
# -------------------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from mdcspc import analyse_xmr_by_group  # type: ignore


def _detect_group_cols(df: pd.DataFrame) -> List[str]:
    """
    Same group-col detection as the main exporter.

    Priority:
    - If both OrgCode and MetricName exist, use both.
    - Else if OrgCode exists, use OrgCode only.
    - Else fall back to any non-date, non-value columns.
    """
    candidate: List[str] = []

    if "OrgCode" in df.columns and "MetricName" in df.columns:
        return ["OrgCode", "MetricName"]

    if "OrgCode" in df.columns:
        return ["OrgCode"]

    exclude = {"Month", "Date", "Value"}
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


def main():
    """
    Debug helper:

    Run the same XmR analysis as the exporter, but dump the full SPC
    table for a single series (e.g. OrgCode + MetricName) to CSV so
    we can compare *per-point* mean/LCL/UCL with the Excel template.
    """

    # ----------------------------------------------------------------
    # 1) Parse CLI args
    # ----------------------------------------------------------------
    # Usage:
    #   python scripts/debug_dump_series.py [input_csv] ORGCODE METRICNAME
    #
    # Example:
    #   python scripts/debug_dump_series.py RKB AE4hr
    #   python scripts/debug_dump_series.py working/ae4hr_multi_org_example.csv RKB AE4hr
    #
    args = sys.argv[1:]

    if len(args) == 2:
        # No explicit CSV path, use the same default as exporter
        input_csv = os.path.join(PROJECT_ROOT, "working", "ae4hr_multi_org_example.csv")
        org_code = args[0]
        metric_name = args[1]
    elif len(args) == 3:
        input_arg = args[0]
        if not os.path.isabs(input_arg):
            input_csv = os.path.join(PROJECT_ROOT, input_arg)
        else:
            input_csv = input_arg
        org_code = args[1]
        metric_name = args[2]
    else:
        print(
            "Usage:\n"
            "  python scripts/debug_dump_series.py ORGCODE METRICNAME\n"
            "  python scripts/debug_dump_series.py input_csv ORGCODE METRICNAME\n"
        )
        sys.exit(1)

    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    print(f"[DEBUG] Loading input CSV: {input_csv}")
    print(f"[DEBUG] Target series: OrgCode={org_code!r}, MetricName={metric_name!r}")

    # ----------------------------------------------------------------
    # 2) Load CSV
    # ----------------------------------------------------------------
    df = pd.read_csv(
        input_csv,
        parse_dates=["Month"],
        dayfirst=True,
    )

    if "Value" not in df.columns:
        raise ValueError("Expected a 'Value' column in the input CSV.")

    if "Month" not in df.columns:
        raise ValueError("Expected a 'Month' column in the input CSV for the index.")

    group_cols = _detect_group_cols(df)
    print(f"[DEBUG] Using group columns: {group_cols}")

    working_dir = os.path.join(PROJECT_ROOT, "working")
    os.makedirs(working_dir, exist_ok=True)

    # ----------------------------------------------------------------
    # 3) Load phase config (same as exporter)
    # ----------------------------------------------------------------
    phase_config_path = os.path.join(working_dir, "spc_phase_config.csv")
    phase_starts = None
    if os.path.exists(phase_config_path):
        print(f"[DEBUG] Loading phase configuration from: {phase_config_path}")
        cfg = pd.read_csv(
            phase_config_path,
            parse_dates=["PhaseStart"],
            dayfirst=True,
        )

        # Basic validation
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

        phase_starts = {}
        grouped_cfg = cfg.groupby(list(group_cols), dropna=False)
        for key, g in grouped_cfg:
            if not isinstance(key, tuple):
                key_tuple: Tuple[Any, ...] = (key,)
            else:
                key_tuple = key
            starts = (
                g["PhaseStart"]
                .dropna()
                .sort_values()
                .unique()
            )
            if len(starts) > 0:
                phase_starts[key_tuple] = list(starts)

        print(f"[DEBUG] Phase configuration loaded for {len(phase_starts or {})} series.")
    else:
        print("[DEBUG] No spc_phase_config.csv found – running all series as single-phase.")

    # ----------------------------------------------------------------
    # 4) Run multi-series XmR analysis (same parameters as exporter)
    # ----------------------------------------------------------------
    multi = analyse_xmr_by_group(
        data=df,
        value_col="Value",
        index_col="Month",
        group_cols=group_cols,
        phase_starts=phase_starts,
        baseline_mode="all",
        baseline_points=None,
        min_points_for_spc=10,
        shift_length=6,
        trend_length=6,
        rules=("trend", "shift", "2of3", "astronomical"),
    )

    # ----------------------------------------------------------------
    # 5) Locate the specific series we care about
    # ----------------------------------------------------------------
    # For group_cols ['OrgCode', 'MetricName'], keys in multi.by_group
    # will be tuples like ('RKB', 'AE4hr').
    target_key: Tuple[Any, ...]
    if "OrgCode" in group_cols and "MetricName" in group_cols:
        # Build key tuple in the same order as group_cols
        key_parts: List[Any] = []
        for col in group_cols:
            if col == "OrgCode":
                key_parts.append(str(org_code))
            elif col == "MetricName":
                key_parts.append(str(metric_name))
            else:
                key_parts.append(None)
        target_key = tuple(key_parts)
    else:
        # Fallback – very unlikely for your use case
        raise ValueError(
            "This debug script currently assumes group_cols include "
            "'OrgCode' and 'MetricName'."
        )

    if target_key not in multi.by_group:
        available_keys = list(multi.by_group.keys())
        raise KeyError(
            f"Target key {target_key!r} not found in multi.by_group.\n"
            f"Available keys: {available_keys}"
        )

    group_result = multi.by_group[target_key]
    series_df = group_result.data.copy()

    # ----------------------------------------------------------------
    # 6) Dump the full SPC table for this series to CSV
    # ----------------------------------------------------------------
    safe_org = str(org_code).replace(" ", "_")
    safe_metric = str(metric_name).replace(" ", "_")
    out_path = os.path.join(
        working_dir,
        f"debug_spc_table_{safe_org}__{safe_metric}.csv",
    )

    series_df.to_csv(out_path, index=True)
    print(f"[DEBUG] SPC table for {target_key} written to: {out_path}")


if __name__ == "__main__":
    main()
