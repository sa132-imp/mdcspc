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


def test_full_flow_from_csv_applies_phase_config_to_summary(tmp_path: Path) -> None:
    """
    End-to-end-ish library test for phased recalculation via canonical phase config.

    - Load the sample input CSV
    - Write a temporary spc_phase_config.csv
    - Run the exporter
    - Assert summary latest mean/LCL/UCL reflect the latest phase, not whole-series limits
    """
    project_root = Path(__file__).resolve().parent.parent
    input_csv = project_root / "tests" / "data" / "sample_input.csv"

    assert input_csv.exists(), f"Missing test input CSV: {input_csv}"

    from mdcspc.exporter import export_spc_from_csv

    out_dir = tmp_path / "phase_flow_out"
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    phase_cfg = config_dir / "spc_phase_config.csv"
    phase_cfg.write_text(
        "OrgCode,MetricName,PhaseStart\n"
        "OrgA,Metric1,2025-05-01\n"
        "OrgA,Metric2,2025-05-01\n",
        encoding="utf-8",
    )

    summary, _multi = export_spc_from_csv(
        input_csv=input_csv,
        working_dir=out_dir,
        config_dir=config_dir,
        chart_mode="x_only",
        value_col="Value",
        index_col="Month",
        summary_filename="spc_summary_from_input.csv",
        quiet=True,
    )

    assert len(summary) == 2, f"Expected 2 summary rows, got {len(summary)}"

    metric1 = summary.loc[
        (summary["OrgCode"] == "OrgA") & (summary["MetricName"] == "Metric1")
    ].iloc[0]
    metric2 = summary.loc[
        (summary["OrgCode"] == "OrgA") & (summary["MetricName"] == "Metric2")
    ].iloc[0]

    assert metric1["mean_latest"] == 32.166666666666664
    assert metric1["lcl_latest"] == 13.549645390070918
    assert metric1["ucl_latest"] == 50.78368794326241

    assert metric2["mean_latest"] == 1.6225000000000003
    assert metric2["lcl_latest"] == 1.3565425531914896
    assert metric2["ucl_latest"] == 1.888457446808511