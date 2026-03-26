"""
Basic sanity tests for the MDCpip / mdcspc pipeline.

These tests are intentionally simple and high-level. They check that:

- We can run the full pipeline on a stable sample CSV under tests/data
- The summary includes the new variation_status and assurance_status columns
- Any non-null variation / assurance values are known values
- Icon table builds without blowing up and has the expected columns

Run with:
    pytest tests/test_summary_and_icons.py

or:
    python -m pytest
from the project root.
"""

import os
import sys
from pathlib import Path

import pandas as pd

# Use a non-GUI backend for matplotlib so tests don't need Tk
os.environ.setdefault("MPLBACKEND", "Agg")

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import mdcspc as mdc


# Stable test input that lives inside the repo
DEFAULT_INPUT = PROJECT_ROOT / "tests" / "data" / "sample_input.csv"


def _pick_input_csv() -> Path:
    """
    Pick a stable CSV to test against.

    Uses a canonical sample file stored under tests/data so the test suite
    does not depend on personal scratch folders such as working/.
    """
    if DEFAULT_INPUT.exists():
        return DEFAULT_INPUT

    raise FileNotFoundError(
        f"No test input CSV found. Expected:\n"
        f"  - {DEFAULT_INPUT}"
    )


def test_export_spc_from_csv_runs_and_returns_summary(tmp_path):
    """
    Basic: export_spc_from_csv runs on a real CSV and returns a non-empty summary.
    """
    input_csv = _pick_input_csv()

    summary, multi = mdc.export_spc_from_csv(
        str(input_csv),
        working_dir=tmp_path,
        chart_mode="xmr",
        quiet=True,
    )

    # Summary should not be empty
    assert isinstance(summary, pd.DataFrame)
    assert not summary.empty

    # MultiXmrResult should have groups
    assert hasattr(multi, "by_group")
    assert len(multi.by_group) > 0

    # New columns should be present
    assert "variation_status" in summary.columns
    assert "assurance_status" in summary.columns


def test_variation_and_assurance_status_values_are_known(tmp_path):
    """
    Check that variation_status and assurance_status columns
    only contain known / non-weird non-null values for a test run.

    This test does not require the sample dataset to trigger non-null statuses;
    it only checks that if statuses are present, they are valid.
    """
    input_csv = _pick_input_csv()

    summary, _ = mdc.export_spc_from_csv(
        str(input_csv),
        working_dir=tmp_path,
        chart_mode="xmr",
        quiet=True,
    )

    allowed_variation_statuses = {
        "common_cause",
        "improvement_high",
        "improvement_low",
        "concern_high",
        "concern_low",
        "neither_high",
        "neither_low",
    }

    allowed_assurance_statuses = {
        "passing",
        "failing",
        "hit_or_miss",
        "no_target",
        "no_data",
    }

    assert "variation_status" in summary.columns
    assert "assurance_status" in summary.columns

    v_status_unique = set(summary["variation_status"].dropna().unique())
    a_status_unique = set(summary["assurance_status"].dropna().unique())

    # If any non-null values are present, they should be recognised.
    assert v_status_unique.issubset(allowed_variation_statuses)
    assert a_status_unique.issubset(allowed_assurance_statuses)


def test_export_icon_table_builds_files(tmp_path):
    """
    Build the icon table via the library API and check:

    - icon_table is non-empty
    - expected columns exist
    - CSV and XLSX files are created
    """
    input_csv = _pick_input_csv()

    summary, _multi = mdc.export_spc_from_csv(
        str(input_csv),
        working_dir=tmp_path,
        chart_mode="xmr",
        quiet=True,
    )

    metric_cfg = mdc.load_metric_config()

    icon_table, csv_path, xlsx_path = mdc.export_icon_table(
        summary=summary,
        metric_configs=metric_cfg,
        working_dir=tmp_path,
    )

    # Basic checks
    assert isinstance(icon_table, pd.DataFrame)
    assert not icon_table.empty

    expected_cols = {
        "KPI",
        "Latest month",
        "Measure",
        "Target",
        "Variation",
        "Assurance",
        "Mean",
        "Lower process limit",
        "Upper process limit",
    }
    assert expected_cols.issubset(set(icon_table.columns))

    # Files should exist
    assert os.path.isfile(csv_path)

    # XLSX may be empty string if XlsxWriter isn't installed; handle that
    if xlsx_path:
        assert os.path.isfile(xlsx_path)