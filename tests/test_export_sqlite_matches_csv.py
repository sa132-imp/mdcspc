from __future__ import annotations

from pathlib import Path
import sqlite3

import pandas as pd

from mdcspc.exporter import export_spc_from_csv
from mdcspc.exporter_dataframe import export_spc_from_sqlite


def _stable_sort_summary(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    sort_cols = [c for c in ["OrgCode", "MetricName"] if c in out.columns]
    if sort_cols:
        out = out.sort_values(sort_cols).reset_index(drop=True)
    else:
        out = out.reset_index(drop=True)

    out = out.reindex(sorted(out.columns), axis=1)
    return out


def test_export_from_sqlite_matches_csv_summary(tmp_path: Path):
    """
    End-to-end equivalence test:
    - Run exporter via CSV path
    - Load same rows into a temp SQLite DB table
    - Run exporter via SQLite path (SQL -> DataFrame -> pipeline)
    - Assert summaries match exactly (after stable sorting)
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

    # 2) SQLite path: create DB + insert table
    df = pd.read_csv(input_csv, parse_dates=["Month"], dayfirst=True)
    db_path = tmp_path / "test.db"

    with sqlite3.connect(db_path) as conn:
        df.to_sql("spc_input", conn, index=False, if_exists="replace")

    out_sql_dir = tmp_path / "sqlite_path"
    summary_sql, _ = export_spc_from_sqlite(
        db_path=db_path,
        sql="SELECT * FROM spc_input",
        working_dir=out_sql_dir,
        index_col="Month",
        value_col="Value",
    )

    s1 = _stable_sort_summary(summary_csv)
    s2 = _stable_sort_summary(summary_sql)

    pd.testing.assert_frame_equal(s1, s2, check_dtype=False)
