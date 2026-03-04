from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_full_flow_from_csv_writes_summary_and_charts(tmp_path: Path) -> None:
    """
    End-to-end-ish library test (no CLI):

    - Load the golden input CSV
    - Run the exporter
    - Assert summary CSV is created
    - Assert at least one chart PNG is created

    This avoids any GUI operations and does not depend on working/.
    """
    project_root = Path(__file__).resolve().parent.parent
    input_csv = project_root / "tests" / "data" / "xmr_golden_input.csv"

    assert input_csv.exists(), f"Missing test input CSV: {input_csv}"

    # Import inside the test so failures are reported cleanly by pytest
    from mdcspc.exporter import export_spc_from_csv

    out_dir = tmp_path / "full_flow_out"

    export_spc_from_csv(
        input_csv=input_csv,
        working_dir=out_dir,
        config_dir=project_root / "config",
        chart_mode="x_only",  # default behaviour we want most of the time
        value_col="Value",
        index_col="Month",
        summary_filename="spc_summary_from_input.csv",
        quiet=True,
    )

    summary_path = out_dir / "spc_summary_from_input.csv"
    charts_dir = out_dir / "charts"

    assert summary_path.exists(), f"Expected summary CSV not found: {summary_path}"
    assert charts_dir.exists(), f"Expected charts directory not found: {charts_dir}"

    pngs = list(charts_dir.glob("*.png"))
    assert pngs, f"Expected at least one chart PNG in: {charts_dir}"

    # Optional sanity: summary has at least one row
    df = pd.read_csv(summary_path)
    assert len(df) > 0, "Summary CSV is empty."