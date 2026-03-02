from __future__ import annotations

from pathlib import Path

import pandas as pd

from mdcspc.exporter import export_spc_from_csv
from mdcspc.exporter_dataframe import export_spc_from_dataframe


def _stable_sort_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Make summaries comparable across runs by sorting rows/cols deterministically
    and avoiding dtype noise where possible.
    """
    out = df.copy()

    # Sort rows by the typical grouping keys if present
    sort_cols = [c for c in ["OrgCode", "MetricName"] if c in out.columns]
    if sort_cols:
        out = out.sort_values(sort_cols).reset_index(drop=True)
    else:
        out = out.reset_index(drop=True)

    # Sort columns for stable equality checks
    out = out.reindex(sorted(out.columns), axis=1)

    return out


def test_export_from_dataframe_matches_csv_summary(tmp_path: Path):
    """
    End-to-end equivalence test:
    - Load the golden XmR CSV input
    - Run exporter via CSV path
    - Load into DataFrame and run exporter via DataFrame path
    - Assert the summary outputs match exactly (after stable sorting)
    """
    project_root = Path(__file__).resolve().parent.parent
    input_csv = project_root / "tests" / "data" / "xmr_golden_input.csv"
    assert input_csv.exists(), f"Missing test input: {input_csv}"

    # 1) CSV path
    out_csv_dir = tmp_path / "csv_path"
    summary_csv, _ = export_spc_from_csv(
        input_csv=input_csv,
        working_dir=out_csv_dir,
    )

    # 2) DataFrame path
    df = pd.read_csv(input_csv, parse_dates=["Month"], dayfirst=True)
    out_df_dir = tmp_path / "df_path"
    summary_df, _ = export_spc_from_dataframe(
        df=df,
        working_dir=out_df_dir,
        index_col="Month",
        value_col="Value",
    )

    # Compare
    s1 = _stable_sort_summary(summary_csv)
    s2 = _stable_sort_summary(summary_df)

    pd.testing.assert_frame_equal(s1, s2, check_dtype=False)
