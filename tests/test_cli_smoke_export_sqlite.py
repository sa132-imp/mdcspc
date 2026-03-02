from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

import pandas as pd


def test_cli_export_sqlite_smoke(tmp_path: Path) -> None:
    """
    Smoke test the CLI export-sqlite entrypoint end-to-end:
    - build a tiny SQLite DB from the golden input CSV
    - run `mdcspc export-sqlite` against it
    - assert it writes the summary and creates charts
    """
    project_root = Path(__file__).resolve().parent.parent
    input_csv = project_root / "tests" / "data" / "xmr_golden_input.csv"

    db_path = tmp_path / "golden.db"
    out_dir = tmp_path / "cli_sqlite_out"

    # Load the golden CSV WITHOUT parsing dates, so Month stays in the same string format
    df = pd.read_csv(input_csv)

    with sqlite3.connect(str(db_path)) as con:
        df.to_sql("spc_input", con, index=False, if_exists="replace")

    query = "SELECT Month, OrgCode, MetricName, Value FROM spc_input"

    cmd = [
        sys.executable,
        "-m",
        "mdcspc.cli",
        "export-sqlite",
        "--db",
        str(db_path),
        "--query",
        query,
        "--out",
        str(out_dir),
        "--chart-mode",
        "xmr",
    ]

    completed = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )

    if completed.returncode != 0:
        raise AssertionError(
            "CLI command failed.\n"
            f"Return code: {completed.returncode}\n"
            f"STDOUT:\n{completed.stdout}\n"
            f"STDERR:\n{completed.stderr}\n"
        )

    assert "[INFO] Done." in (completed.stdout or ""), (
        "Expected completion marker not found in CLI output.\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}\n"
    )

    summary_path = out_dir / "spc_summary_from_input.csv"
    charts_dir = out_dir / "charts"

    assert summary_path.exists(), f"Expected summary file not found: {summary_path}"
    assert charts_dir.exists(), f"Expected charts dir not found: {charts_dir}"

    chart_files = list(charts_dir.glob("*.png"))
    assert len(chart_files) > 0, "Expected at least one chart PNG to be generated."


def test_cli_export_sqlite_prints_config_dir_when_provided(tmp_path: Path) -> None:
    """
    Prove that --config-dir is wired through the CLI for export-sqlite by asserting the
    informational line appears in STDOUT.

    We intentionally supply an empty config dir: exporter should still run
    (metric config load is fail-soft; phase/target configs are optional).
    """
    project_root = Path(__file__).resolve().parent.parent
    input_csv = project_root / "tests" / "data" / "xmr_golden_input.csv"

    db_path = tmp_path / "golden_cfg.db"
    out_dir = tmp_path / "cli_sqlite_out_cfg"
    cfg_dir = tmp_path / "custom_config_dir"
    cfg_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_csv)
    with sqlite3.connect(str(db_path)) as con:
        df.to_sql("spc_input", con, index=False, if_exists="replace")

    query = "SELECT Month, OrgCode, MetricName, Value FROM spc_input"

    cmd = [
        sys.executable,
        "-m",
        "mdcspc.cli",
        "export-sqlite",
        "--db",
        str(db_path),
        "--query",
        query,
        "--out",
        str(out_dir),
        "--chart-mode",
        "xmr",
        "--config-dir",
        str(cfg_dir),
    ]

    completed = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )

    if completed.returncode != 0:
        raise AssertionError(
            "CLI command failed.\n"
            f"Return code: {completed.returncode}\n"
            f"STDOUT:\n{completed.stdout}\n"
            f"STDERR:\n{completed.stderr}\n"
        )

    assert "Using config_dir:" in (completed.stdout or ""), (
        "Expected CLI to print the selected config_dir.\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}\n"
    )
    assert str(cfg_dir) in (completed.stdout or ""), (
        "Expected CLI to include the provided config_dir path in STDOUT.\n"
        f"config_dir={cfg_dir}\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}\n"
    )

    # Still confirm outputs exist (keeps this as a real end-to-end run)
    summary_path = out_dir / "spc_summary_from_input.csv"
    charts_dir = out_dir / "charts"

    assert summary_path.exists(), f"Expected summary file not found: {summary_path}"
    assert charts_dir.exists(), f"Expected charts dir not found: {charts_dir}"

    chart_files = list(charts_dir.glob("*.png"))
    assert len(chart_files) > 0, "Expected at least one chart PNG to be generated."

def test_cli_export_sqlite_quiet_outputs_only_done(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parent.parent
    input_csv = project_root / "tests" / "data" / "xmr_golden_input.csv"

    db_path = tmp_path / "golden.db"
    out_dir = tmp_path / "cli_sqlite_out_quiet"

    df = pd.read_csv(input_csv)
    with sqlite3.connect(str(db_path)) as con:
        df.to_sql("spc_input", con, index=False, if_exists="replace")

    query = "SELECT Month, OrgCode, MetricName, Value FROM spc_input"

    cmd = [
        sys.executable,
        "-m",
        "mdcspc.cli",
        "export-sqlite",
        "--db",
        str(db_path),
        "--query",
        query,
        "--out",
        str(out_dir),
        "--chart-mode",
        "xmr",
        "--quiet",
    ]

    completed = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, (
        "CLI command failed.\n"
        f"Return code: {completed.returncode}\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}\n"
    )

    assert (completed.stdout or "").strip() == "[INFO] Done.", (
        "Quiet mode should print only '[INFO] Done.'\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}\n"
    )

    assert (completed.stderr or "").strip() == "", (
        "Quiet mode should not emit stderr.\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}\n"
    )
