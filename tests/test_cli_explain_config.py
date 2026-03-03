from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _env_with_project_on_path(project_root: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    return env


def test_cli_explain_config_runs_without_config_dir(tmp_path: Path) -> None:
    """
    explain-config should run successfully without --config-dir and report packaged defaults.
    """
    project_root = Path(__file__).resolve().parent.parent

    cmd = [
        sys.executable,
        "-m",
        "mdcspc.cli",
        "explain-config",
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

    out = completed.stdout or ""
    assert "[INFO] mdcspc config resolution" in out, (
        "Expected header line not found.\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}\n"
    )
    # Should mention packaged defaults in some form
    assert "packaged default" in out, (
        "Expected output to mention packaged defaults.\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}\n"
    )
    # Should mention the known config file names
    assert "metric_config.csv" in out, "Expected metric_config.csv to be mentioned."
    assert "spc_target_config.csv" in out, "Expected spc_target_config.csv to be mentioned."


def test_cli_explain_config_with_config_dir_reports_missing_and_fallback(tmp_path: Path) -> None:
    """
    If --config-dir is provided but files are missing, explain-config should report missing
    and indicate fallback to packaged defaults.
    """
    project_root = Path(__file__).resolve().parent.parent

    empty_cfg = tmp_path / "empty_cfg"
    empty_cfg.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "mdcspc.cli",
        "explain-config",
        "--config-dir",
        str(empty_cfg),
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

    out = completed.stdout or ""
    assert f"[INFO] --config-dir provided: {empty_cfg}" in out, (
        "Expected config-dir line not found.\n"
        f"Expected: [INFO] --config-dir provided: {empty_cfg}\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}\n"
    )
    assert "MISSING in config_dir" in out, (
        "Expected missing-file messaging when config_dir is empty.\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}\n"
    )
    assert "fallback: packaged default" in out, (
        "Expected fallback messaging when config_dir is missing files.\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}\n"
    )