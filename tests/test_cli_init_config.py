from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _env_with_project_on_path(project_root: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    return env


def test_cli_init_config_writes_templates(tmp_path: Path) -> None:
    """
    init-config should write editable config templates into the requested folder.

    We force PYTHONPATH=project_root so the subprocess imports the repo copy
    of mdcspc (not any installed version in site-packages).
    """
    project_root = Path(__file__).resolve().parent.parent

    out_cfg = tmp_path / "mdcspc_config"

    cmd = [
        sys.executable,
        "-m",
        "mdcspc.cli",
        "init-config",
        "--out",
        str(out_cfg),
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

    metric_cfg = out_cfg / "metric_config.csv"
    target_cfg = out_cfg / "spc_target_config.csv"

    assert metric_cfg.exists(), (
        "Expected metric_config.csv not written by init-config.\n"
        f"Expected: {metric_cfg}\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}\n"
    )
    assert target_cfg.exists(), (
        "Expected spc_target_config.csv not written by init-config.\n"
        f"Expected: {target_cfg}\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}\n"
    )

    # Very light sanity check: non-empty files
    assert metric_cfg.stat().st_size > 0, "metric_config.csv is empty."
    assert target_cfg.stat().st_size > 0, "spc_target_config.csv is empty."

    # Helpful confirmation line
    assert f"[INFO] Wrote config templates to: {out_cfg}" in (completed.stdout or ""), (
        "Expected init-config success message not found.\n"
        f"Expected to include: [INFO] Wrote config templates to: {out_cfg}\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}\n"
    )


def test_cli_init_config_refuses_overwrite_without_force(tmp_path: Path) -> None:
    """
    If files already exist, init-config should refuse to overwrite unless --force is passed.
    """
    project_root = Path(__file__).resolve().parent.parent
    out_cfg = tmp_path / "mdcspc_config"
    out_cfg.mkdir(parents=True, exist_ok=True)

    # Create a dummy existing file that init-config would write
    existing = out_cfg / "metric_config.csv"
    existing.write_text("DUMMY", encoding="utf-8")

    cmd = [
        sys.executable,
        "-m",
        "mdcspc.cli",
        "init-config",
        "--out",
        str(out_cfg),
    ]

    completed = subprocess.run(
        cmd,
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env=_env_with_project_on_path(project_root),
    )

    assert completed.returncode != 0, (
        "Expected init-config to fail when files exist and --force is not provided.\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}\n"
    )

    # Should complain about already exists
    combined = "\n".join([completed.stdout or "", completed.stderr or ""])
    assert "already exists" in combined, (
        "Expected an 'already exists' message when refusing to overwrite.\n"
        f"STDOUT:\n{completed.stdout}\n"
        f"STDERR:\n{completed.stderr}\n"
    )