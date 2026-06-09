from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


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

def test_cli_export_csv_without_grouping_column_shows_plain_english_error(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parent.parent

    input_csv = tmp_path / "missing_grouping_column.csv"
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

    assert completed.returncode == 1
    assert "ERROR MDCSPC002: No metric or grouping column found" in combined_output
    assert "MDCSPC could not find a metric or grouping column." in combined_output
    assert "Phase config is missing required group column" not in combined_output
    assert "Traceback" not in combined_output

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


