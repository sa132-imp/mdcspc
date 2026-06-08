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


def test_cli_wizard_writes_starter_configs(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parent.parent

    input_csv = project_root / "tests" / "data" / "sample_input.csv"
    out_cfg = tmp_path / "wizard_config"

    cmd = [
        sys.executable,
        "-m",
        "mdcspc.cli",
        "wizard",
        "--input",
        str(input_csv),
        "--out-config",
        str(out_cfg),
        "--defaults", # NEW LINE added
    ]

    completed = subprocess.run(
        cmd,
        cwd=str(tmp_path),
        input="\n".join(["higher", "count", "0", "no", "lower", "rate", "1", "no"]),
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

    metric_cfg = out_cfg / "metric_config.csv"
    target_cfg = out_cfg / "spc_target_config.csv"

    assert metric_cfg.exists(), "Expected metric_config.csv to be written by wizard."
    assert target_cfg.exists(), "Expected spc_target_config.csv to be written by wizard."

    metric_df = pd.read_csv(metric_cfg)
    assert "MetricName" in metric_df.columns
    assert "DisplayName" in metric_df.columns
    assert "Direction" in metric_df.columns
    assert "HasTarget" in metric_df.columns
    assert "TargetValue" in metric_df.columns
    assert "Unit" in metric_df.columns
    assert "DecimalPlaces" in metric_df.columns
    assert len(metric_df) > 0, "metric_config.csv should contain at least one metric row."

    target_df = pd.read_csv(target_cfg)
    assert list(target_df.columns) == ["OrgCode", "MetricName", "EffectiveFrom", "TargetValue"]

    assert "Configuration for" in (completed.stdout or "")

def test_cli_wizard_missing_metric_name_shows_plain_english_error(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parent.parent

    input_csv = tmp_path / "missing_metric_name.csv"
    input_csv.write_text(
        "date,value\n"
        "11/01/2026,0.08858\n"
        "18/01/2026,0.08549\n",
        encoding="utf-8",
    )

    out_cfg = tmp_path / "wizard_config"

    cmd = [
        sys.executable,
        "-m",
        "mdcspc.cli",
        "wizard",
        "--input",
        str(input_csv),
        "--out-config",
        str(out_cfg),
        "--defaults",
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
    assert "ERROR MDCSPC001: Missing MetricName column" in combined_output
    assert "The wizard needs a MetricName column to build the metric configuration." in combined_output
    assert "Traceback" not in combined_output