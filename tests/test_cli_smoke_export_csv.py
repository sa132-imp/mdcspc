from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pandas as pd


def _env_with_project_on_path(project_root: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    return env


def test_cli_export_csv_smoke(tmp_path: Path) -> None:
    """
    Smoke test the CLI entrypoint end-to-end.

    We force PYTHONPATH=project_root so the subprocess imports the repo copy
    of mdcspc (not any installed version in site-packages).
    """
    project_root = Path(__file__).resolve().parent.parent
    input_csv = project_root / "tests" / "data" / "xmr_golden_input.csv"

    out_dir = tmp_path / "cli_smoke_out"

    cmd = [
        sys.executable,
        "-m",
        "mdcspc.cli",
        "export-csv",
        "--input",
        str(input_csv),
        "--out",
        str(out_dir),
        "--chart-mode",
        "xmr",
    ]

    completed = subprocess.run(
        cmd,
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env=_env_with_project_on_path(project_root),
    )

    if completed.returncode != 0:
        raise AssertionError(
            "CLI command failed.\n"
            f"Return code: {completed.returncode}\n"
            f"STDOUT:\n{completed.stdout}\n"
            f"STDERR:\n{completed.stderr}\n"
        )

    summary_path = out_dir / "spc_summary_from_input.csv"
    charts_dir = out_dir / "charts"

    assert summary_path.exists(), (
        "Expected summary file not found.\n"
        f"Expected: {summary_path}\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}\n"
    )
    assert charts_dir.exists(), (
        "Expected charts dir not found.\n"
        f"Expected: {charts_dir}\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}\n"
    )

    pngs = list(charts_dir.glob("*.png"))
    assert pngs, (
        "No chart PNGs found after running CLI.\n"
        f"charts_dir={charts_dir}\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}\n"
    )


def test_cli_export_csv_prints_config_dir_when_provided(tmp_path: Path) -> None:
    """
    When --config-dir is provided, CLI should print a single line indicating
    which config_dir it is using (in non-quiet mode).
    """
    project_root = Path(__file__).resolve().parent.parent
    input_csv = project_root / "tests" / "data" / "xmr_golden_input.csv"
    out_dir = tmp_path / "cli_smoke_out"
    config_dir = project_root / "config"

    cmd = [
        sys.executable,
        "-m",
        "mdcspc.cli",
        "export-csv",
        "--input",
        str(input_csv),
        "--out",
        str(out_dir),
        "--config-dir",
        str(config_dir),
        "--chart-mode",
        "xmr",
    ]

    completed = subprocess.run(
        cmd,
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env=_env_with_project_on_path(project_root),
    )

    if completed.returncode != 0:
        raise AssertionError(
            "CLI command failed.\n"
            f"Return code: {completed.returncode}\n"
            f"STDOUT:\n{completed.stdout}\n"
            f"STDERR:\n{completed.stderr}\n"
        )

    assert f"[INFO] Using config_dir: {config_dir}" in (completed.stdout or ""), (
        "Expected config_dir line not found in CLI output.\n"
        f"Expected to include: [INFO] Using config_dir: {config_dir}\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}\n"
    )


def test_cli_export_csv_quiet_outputs_only_done(tmp_path: Path) -> None:
    """
    Quiet mode should suppress chatter.

    Contract:
    - Export succeeds and writes outputs
    - If any text is emitted to stdout/stderr, it must be ONLY: [INFO] Done.
    (Some Windows subprocess pipe setups can yield empty stdout even when the process succeeds.)
    """
    project_root = Path(__file__).resolve().parent.parent
    input_csv = project_root / "tests" / "data" / "xmr_golden_input.csv"
    out_dir = tmp_path / "cli_smoke_out"

    cmd = [
        sys.executable,
        "-m",
        "mdcspc.cli",
        "export-csv",
        "--input",
        str(input_csv),
        "--out",
        str(out_dir),
        "--chart-mode",
        "xmr",
        "--quiet",
    ]

    completed = subprocess.run(
        cmd,
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env=_env_with_project_on_path(project_root),
    )

    if completed.returncode != 0:
        raise AssertionError(
            "CLI command failed.\n"
            f"Return code: {completed.returncode}\n"
            f"STDOUT:\n{completed.stdout}\n"
            f"STDERR:\n{completed.stderr}\n"
        )

    # Outputs must exist
    summary_path = out_dir / "spc_summary_from_input.csv"
    charts_dir = out_dir / "charts"
    assert summary_path.exists(), f"Expected summary file not found: {summary_path}"
    assert charts_dir.exists(), f"Expected charts dir not found: {charts_dir}"
    assert list(charts_dir.glob("*.png")), "Expected at least one chart PNG."

    # If anything is printed, it must be only Done (stdout OR stderr)
    combined = "\n".join([completed.stdout or "", completed.stderr or ""]).strip()

    if combined:
        lines = [ln.strip() for ln in combined.splitlines() if ln.strip()]
        if lines != ["[INFO] Done."]:
            debug_path = tmp_path / "quiet_mode_output_debug.txt"
            debug_path.write_text("\n".join(lines), encoding="utf-8")
            raise AssertionError(
                "Quiet mode should emit no chatter; if it emits anything, it must be only '[INFO] Done.'\n"
                f"LINES FOUND ({len(lines)}). Saved to: {debug_path}\n"
            )

def test_cli_export_csv_without_grouping_column_uses_single_series_fallback(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parent.parent

    input_csv = tmp_path / "single_series_no_grouping_column.csv"
    input_csv.write_text(
        "date,value\n"
        "11/01/2026,0.08858\n"
        "18/01/2026,0.08549\n",
        encoding="utf-8",
    )

    out_dir = tmp_path / "export_out"

    cmd = [
        sys.executable,
        "-m",
        "mdcspc.cli",
        "export-csv",
        "--input",
        str(input_csv),
        "--out",
        str(out_dir),
        "--value-col",
        "value",
        "--index-col",
        "date",
    ]

    completed = subprocess.run(
        cmd,
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env=_env_with_project_on_path(project_root),
    )

    combined_output = f"{completed.stdout}\n{completed.stderr}"

    assert completed.returncode == 0
    assert "Using group columns: ['MetricName']" in combined_output
    assert "Series1" in combined_output
    assert "ERROR MDCSPC002" not in combined_output
    assert "Phase config is missing required group column" not in combined_output
    assert "Traceback" not in combined_output

    summary_path = out_dir / "spc_summary_from_input.csv"
    charts_dir = out_dir / "charts"
    chart_path = charts_dir / "Series1.png"

    assert summary_path.exists(), f"Expected summary file not found: {summary_path}"
    assert charts_dir.exists(), f"Expected charts dir not found: {charts_dir}"
    assert chart_path.exists(), f"Expected fallback single-series chart not found: {chart_path}"


def test_cli_export_csv_with_group_column_auto_detects_group(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parent.parent

    input_csv = tmp_path / "group_column_input.csv"
    input_csv.write_text(
        "date,MetricName,Group,value\n"
        "11/01/2026,Falls,Ward_A,10\n"
        "18/01/2026,Falls,Ward_A,12\n"
        "25/01/2026,Falls,Ward_A,11\n"
        "01/02/2026,Falls,Ward_A,13\n"
        "08/02/2026,Falls,Ward_A,15\n"
        "15/02/2026,Falls,Ward_A,14\n"
        "22/02/2026,Falls,Ward_A,16\n"
        "01/03/2026,Falls,Ward_A,15\n"
        "08/03/2026,Falls,Ward_A,17\n"
        "15/03/2026,Falls,Ward_A,18\n"
        "11/01/2026,Falls,Ward_B,8\n"
        "18/01/2026,Falls,Ward_B,9\n"
        "25/01/2026,Falls,Ward_B,10\n"
        "01/02/2026,Falls,Ward_B,9\n"
        "08/02/2026,Falls,Ward_B,11\n"
        "15/02/2026,Falls,Ward_B,12\n"
        "22/02/2026,Falls,Ward_B,11\n"
        "01/03/2026,Falls,Ward_B,13\n"
        "08/03/2026,Falls,Ward_B,12\n"
        "15/03/2026,Falls,Ward_B,14\n",
        encoding="utf-8",
    )

    out_dir = tmp_path / "export_out"

    cmd = [
        sys.executable,
        "-m",
        "mdcspc.cli",
        "export-csv",
        "--input",
        str(input_csv),
        "--out",
        str(out_dir),
        "--value-col",
        "value",
        "--index-col",
        "date",
    ]

    completed = subprocess.run(
        cmd,
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env=_env_with_project_on_path(project_root),
    )

    combined_output = f"{completed.stdout}\n{completed.stderr}"

    assert completed.returncode == 0
    assert "Using group columns: ['Group', 'MetricName']" in combined_output
    assert "Ward_A__Falls" in combined_output
    assert "Ward_B__Falls" in combined_output
    assert "Traceback" not in combined_output

    summary_path = out_dir / "spc_summary_from_input.csv"
    charts_dir = out_dir / "charts"

    assert summary_path.exists(), f"Expected summary file not found: {summary_path}"
    assert charts_dir.exists(), f"Expected charts dir not found: {charts_dir}"
    assert (charts_dir / "Ward_A__Falls.png").exists()
    assert (charts_dir / "Ward_B__Falls.png").exists()

    summary = pd.read_csv(summary_path)

    assert "Group" in summary.columns
    assert "MetricName" in summary.columns
    assert set(summary["Group"].astype(str)) == {"Ward_A", "Ward_B"}

def test_cli_export_csv_missing_index_column_shows_plain_english_error(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parent.parent

    input_csv = tmp_path / "missing_index_column.csv"
    input_csv.write_text(
        "MetricName,value\n"
        "My_Metric,0.08858\n"
        "My_Metric,0.08549\n",
        encoding="utf-8",
    )

    out_dir = tmp_path / "export_out"

    cmd = [
        sys.executable,
        "-m",
        "mdcspc.cli",
        "export-csv",
        "--input",
        str(input_csv),
        "--out",
        str(out_dir),
        "--value-col",
        "value",
        "--index-col",
        "date",
    ]

    completed = subprocess.run(
        cmd,
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env=_env_with_project_on_path(project_root),
    )

    combined_output = f"{completed.stdout}\n{completed.stderr}"

    assert completed.returncode == 1
    assert "ERROR MDCSPC003: Missing date/index column" in combined_output
    assert "currently set as: date" in combined_output
    assert "Traceback" not in combined_output


def test_cli_export_csv_missing_value_column_shows_plain_english_error(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parent.parent

    input_csv = tmp_path / "missing_value_column.csv"
    input_csv.write_text(
        "date,MetricName\n"
        "11/01/2026,My_Metric\n"
        "18/01/2026,My_Metric\n",
        encoding="utf-8",
    )

    out_dir = tmp_path / "export_out"

    cmd = [
        sys.executable,
        "-m",
        "mdcspc.cli",
        "export-csv",
        "--input",
        str(input_csv),
        "--out",
        str(out_dir),
        "--value-col",
        "value",
        "--index-col",
        "date",
    ]

    completed = subprocess.run(
        cmd,
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env=_env_with_project_on_path(project_root),
    )

    combined_output = f"{completed.stdout}\n{completed.stderr}"

    assert completed.returncode == 1
    assert "ERROR MDCSPC004: Missing value column" in combined_output
    assert "currently set as: value" in combined_output
    assert "Traceback" not in combined_output

def test_cli_export_csv_bad_index_dates_shows_plain_english_error(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parent.parent

    input_csv = tmp_path / "bad_index_dates.csv"
    input_csv.write_text(
        "date,MetricName,value\n"
        "not-a-date,My_Metric,0.08858\n"
        "also-bad,My_Metric,0.08549\n",
        encoding="utf-8",
    )

    out_dir = tmp_path / "export_out"

    cmd = [
        sys.executable,
        "-m",
        "mdcspc.cli",
        "export-csv",
        "--input",
        str(input_csv),
        "--out",
        str(out_dir),
        "--value-col",
        "value",
        "--index-col",
        "date",
    ]

    completed = subprocess.run(
        cmd,
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env=_env_with_project_on_path(project_root),
    )

    combined_output = f"{completed.stdout}\n{completed.stderr}"

    assert completed.returncode == 1
    assert "ERROR MDCSPC005: Could not read date/index values" in combined_output
    assert "not-a-date" in combined_output
    assert "also-bad" in combined_output
    assert "UserWarning" not in combined_output
    assert "Traceback" not in combined_output

def test_cli_export_csv_bad_numeric_values_shows_plain_english_error(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parent.parent

    input_csv = tmp_path / "bad_numeric_values.csv"
    input_csv.write_text(
        "date,MetricName,value\n"
        "11/01/2026,My_Metric,0.08858\n"
        "18/01/2026,My_Metric,not-a-number\n",
        encoding="utf-8",
    )

    out_dir = tmp_path / "export_out"

    cmd = [
        sys.executable,
        "-m",
        "mdcspc.cli",
        "export-csv",
        "--input",
        str(input_csv),
        "--out",
        str(out_dir),
        "--value-col",
        "value",
        "--index-col",
        "date",
    ]

    completed = subprocess.run(
        cmd,
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env=_env_with_project_on_path(project_root),
    )

    combined_output = f"{completed.stdout}\n{completed.stderr}"

    assert completed.returncode == 1
    assert "ERROR MDCSPC006: Could not read numeric values" in combined_output
    assert "not-a-number" in combined_output
    assert "could not convert string to float" not in combined_output
    assert "Traceback" not in combined_output


def test_cli_export_csv_direction_lower_sets_lower_is_better(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parent.parent

    input_csv = tmp_path / "lower_direction_input.csv"
    input_csv.write_text(
        "date,MetricName,value\n"
        "01/01/2025,Waiting_Time,10\n"
        "01/02/2025,Waiting_Time,11\n"
        "01/03/2025,Waiting_Time,12\n"
        "01/04/2025,Waiting_Time,13\n"
        "01/05/2025,Waiting_Time,14\n"
        "01/06/2025,Waiting_Time,15\n"
        "01/07/2025,Waiting_Time,16\n"
        "01/08/2025,Waiting_Time,17\n"
        "01/09/2025,Waiting_Time,18\n"
        "01/10/2025,Waiting_Time,19\n",
        encoding="utf-8",
    )

    out_dir = tmp_path / "export_out"

    cmd = [
        sys.executable,
        "-m",
        "mdcspc.cli",
        "export-csv",
        "--input",
        str(input_csv),
        "--out",
        str(out_dir),
        "--value-col",
        "value",
        "--index-col",
        "date",
        "--direction",
        "lower",
    ]

    completed = subprocess.run(
        cmd,
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env=_env_with_project_on_path(project_root),
    )

    if completed.returncode != 0:
        raise AssertionError(
            "CLI command failed.\n"
            f"Return code: {completed.returncode}\n"
            f"STDOUT:\n{completed.stdout}\n"
            f"STDERR:\n{completed.stderr}\n"
        )

    summary_path = out_dir / "spc_summary_from_input.csv"

    assert summary_path.exists(), f"Expected summary file not found: {summary_path}"

    summary = pd.read_csv(summary_path)

    assert "direction" in summary.columns
    assert set(summary["direction"].astype(str)) == {"lower_is_better"}

def test_cli_export_csv_direction_defaults_to_neutral() -> None:
    from mdcspc.cli import _build_parser

    parser = _build_parser(has_sqlite=True)
    args = parser.parse_args(["export-csv", "--input", "data.csv", "--out", "output"])

    assert args.direction == "neutral"
