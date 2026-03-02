"""
DataFrame / SQLite entry points for MDC SPC export.

Design goal:
- Keep the SPC pipeline single-sourced.
- Reuse the existing, battle-tested CSV exporter path initially.
- Provide a clean API for DB-backed workflows (SQL/SQLite -> DataFrame -> export).

NOTE:
- For now, export_spc_from_dataframe writes a temporary CSV and calls
  export_spc_from_csv(...) to avoid duplicating logic.
- We can refactor later so CSV/SQL both call a shared "core" function
  without the temp CSV step.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Tuple, Union, Sequence, Mapping
import tempfile
import os
import sqlite3

import pandas as pd

from .exporter import export_spc_from_csv


def _ensure_datetime_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """
    Ensure df[col] is datetime64, parsing deterministically.

    IMPORTANT: Use dayfirst=False to match CSV exporter behaviour and tests.
    """
    if col not in df.columns:
        raise ValueError(f"Expected an '{col}' column in the input DataFrame.")

    out = df.copy()

    if not pd.api.types.is_datetime64_any_dtype(out[col]):
        try:
            out[col] = pd.to_datetime(out[col], dayfirst=False, errors="raise")
        except Exception:
            s = out[col].astype(str)
            bad_sample = s.head(10).tolist()
            raise ValueError(
                f"Could not parse '{col}' values as dates using dayfirst=False. "
                f"Sample values (first 10): {bad_sample}"
            )

    out[col] = out[col].dt.normalize()
    return out


def export_spc_from_dataframe(
    df: pd.DataFrame,
    working_dir: Optional[Union[str, Path]] = None,
    config_dir: Optional[Union[str, Path]] = None,
    icons_dir: Optional[Union[str, Path]] = None,
    value_col: str = "Value",
    index_col: str = "Month",
    summary_filename: str = "spc_summary_from_input.csv",
    charts_subdir: str = "charts",
    chart_mode: str = "xmr",
) -> Tuple[pd.DataFrame, Any]:
    """
    Run XmR analysis and export SPC outputs from an in-memory DataFrame.

    For now, this function writes a temporary long-format CSV and calls
    export_spc_from_csv(...) so the core pipeline behaviour is identical.
    """
    if df is None or not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame.")

    if value_col not in df.columns:
        raise ValueError(f"Expected a '{value_col}' column in the input DataFrame.")

    df2 = _ensure_datetime_column(df, index_col)

    sort_cols = [c for c in [index_col, "OrgCode", "MetricName"] if c in df2.columns]
    if sort_cols:
        df2 = df2.sort_values(by=sort_cols).reset_index(drop=True)

    tmp_path: Optional[Path] = None
    try:
        tmp_dir = Path(working_dir) if working_dir is not None else Path(tempfile.gettempdir())
        tmp_dir.mkdir(parents=True, exist_ok=True)

        fd, name = tempfile.mkstemp(prefix="mdcspc_df_", suffix=".csv", dir=str(tmp_dir))
        os.close(fd)
        tmp_path = Path(name)

        df_to_write = df2.copy()
        df_to_write[index_col] = df_to_write[index_col].dt.strftime("%Y-%m-%d")
        df_to_write.to_csv(tmp_path, index=False)

        return export_spc_from_csv(
            input_csv=tmp_path,
            working_dir=working_dir,
            config_dir=config_dir,
            icons_dir=icons_dir,
            value_col=value_col,
            index_col=index_col,
            summary_filename=summary_filename,
            charts_subdir=charts_subdir,
            chart_mode=chart_mode,
        )

    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass


def export_spc_from_sqlite(
    db_path: Union[str, Path],
    sql: str,
    params: Optional[Union[Sequence[Any], Mapping[str, Any]]] = None,
    working_dir: Optional[Union[str, Path]] = None,
    config_dir: Optional[Union[str, Path]] = None,
    icons_dir: Optional[Union[str, Path]] = None,
    value_col: str = "Value",
    index_col: str = "Month",
    summary_filename: str = "spc_summary_from_input.csv",
    charts_subdir: str = "charts",
    chart_mode: str = "xmr",
) -> Tuple[pd.DataFrame, Any]:
    """
    Query a SQLite database into a DataFrame, then run the standard export pipeline.
    """
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite DB not found: {db_path}")

    if not sql or not str(sql).strip():
        raise ValueError("sql must be a non-empty SQL query string.")

    with sqlite3.connect(str(db_path)) as conn:
        df = pd.read_sql_query(sql, conn, params=params)

    return export_spc_from_dataframe(
        df=df,
        working_dir=working_dir,
        config_dir=config_dir,
        icons_dir=icons_dir,
        value_col=value_col,
        index_col=index_col,
        summary_filename=summary_filename,
        charts_subdir=charts_subdir,
        chart_mode=chart_mode,
    )


__all__ = [
    "export_spc_from_dataframe",
    "export_spc_from_sqlite",
]
