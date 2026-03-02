from __future__ import annotations

from pathlib import Path

import pandas as pd

import mdcspc.metric_config as mc
from mdcspc.exporter import export_spc_from_csv


def test_golden_series_assurance_icons_match(tmp_path: Path, monkeypatch):
    """
    End-to-end assurance icon test:
      - Uses a test-only metric_config (to control direction-of-good)
      - Uses a test-only spc_target_config.csv via exporter(config_dir=...)
      - Runs the real exporter and asserts assurance_icon per MetricName

    This does NOT touch the existing variation goldens.
    """

    project_root = Path(__file__).resolve().parent.parent
    input_csv = project_root / "tests" / "data" / "assurance_golden_input.csv"
    cfg_dir = project_root / "tests" / "config_assurance"

    test_metric_cfg_path = cfg_dir / "metric_config.csv"
    assert input_csv.exists(), f"Missing test input: {input_csv}"
    assert test_metric_cfg_path.exists(), f"Missing test metric config: {test_metric_cfg_path}"
    assert (cfg_dir / "spc_target_config.csv").exists(), "Missing test target config"

    # Force the library's central metric_config loader to use our test config.
    monkeypatch.setattr(mc, "DEFAULT_CONFIG_PATH", str(test_metric_cfg_path))

    summary, _ = export_spc_from_csv(
        input_csv=input_csv,
        working_dir=tmp_path,
        config_dir=cfg_dir,
    )

    # Build MetricName -> assurance_icon mapping
    got = dict(zip(summary["MetricName"].astype(str), summary["assurance_icon"].astype(str)))

    expected = {
        "ASSUR_NO_TARGET_HIGH": "IconEmpty.png",
        "ASSUR_HIT_MISS_HIGH": "AssuranceIconHitOrMiss.png",
        "ASSUR_FAIL_HIGH": "AssuranceIconFail.png",
        "ASSUR_PASS_HIGH": "AssuranceIconPass.png",
        "ASSUR_PASS_LOW": "AssuranceIconPass.png",
        "ASSUR_FAIL_LOW": "AssuranceIconFail.png",
        "ASSUR_STEP_TARGET_HIGH": "AssuranceIconHitOrMiss.png",
    }

    # Make debugging pleasant if something goes sideways
    assert set(expected.keys()).issubset(set(got.keys())), (
        "Summary missing expected MetricName(s).\n"
        f"Expected keys: {sorted(expected.keys())}\n"
        f"Got keys: {sorted(got.keys())}"
    )

    for metric, exp_icon in expected.items():
        assert got[metric] == exp_icon, f"{metric}: expected {exp_icon} but got {got[metric]}"

    # Extra check: step target should use the LATEST target value (0.80)
    step_row = summary.loc[summary["MetricName"] == "ASSUR_STEP_TARGET_HIGH"].iloc[0]
    target_value = step_row.get("target_value", None)
    assert target_value is not None
    assert abs(float(target_value) - 0.80) < 1e-9
