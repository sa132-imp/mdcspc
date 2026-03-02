# tests/test_golden_summary_icons.py

from pathlib import Path
import sys

import pandas as pd
import matplotlib

# Use a non-GUI backend so tests don't require Tk
matplotlib.use("Agg")

# -------------------------------------------------------------------
# Make sure the project root (where the mdcspc package lives) is on sys.path
# -------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mdcspc.exporter import export_spc_from_csv
from mdcspc.metric_config import VARIATION_ICON_FILES, VariationStatus


def _expected_status_from_variation_code(code: object) -> VariationStatus:
    """
    Map your MDC-style VariationCode to the internal VariationStatus enum.

    Expected codes (from dataset.csv / xmr_golden_expected_summary.csv):

        01. CC   -> Common cause
        02. SCHI -> Special cause improving (higher)
        03. SCLI -> Special cause improving (lower)
        04. SCHD -> Special cause deterioration (higher)
        05. SCLD -> Special cause deterioration (lower)
        06. SCHC -> Special cause change (higher)
        07. SCLC -> Special cause change (lower)
    """
    text = str(code or "").strip()
    if not text:
        raise ValueError(f"Empty VariationCode in golden summary: {code!r}")

    # Take leading digits, e.g. "02. SCHI" -> "02"
    numeric = ""
    for ch in text:
        if ch.isdigit():
            numeric += ch
        else:
            break

    if not numeric:
        raise ValueError(f"Could not parse numeric part of VariationCode: {text!r}")

    # Normalise leading zero, e.g. "01" -> "1"
    numeric = numeric.lstrip("0") or "0"

    mapping = {
        "1": VariationStatus.COMMON_CAUSE,
        "2": VariationStatus.IMPROVEMENT_HIGH,
        "3": VariationStatus.IMPROVEMENT_LOW,
        "4": VariationStatus.CONCERN_HIGH,
        "5": VariationStatus.CONCERN_LOW,
        "6": VariationStatus.NEITHER_HIGH,
        "7": VariationStatus.NEITHER_LOW,
    }

    if numeric not in mapping:
        raise ValueError(f"Unknown VariationCode numeric '{numeric}' from {text!r}")

    return mapping[numeric]


def test_golden_series_variation_icons_match(tmp_path):
    """
    For each golden series, check that the variation icon in the
    summary table matches the expected VariationCode (01..07).

    Uses:
      - tests/data/xmr_golden_input.csv
      - tests/data/xmr_golden_expected_summary.csv

    The expectation is:

      VariationCode -> VariationStatus -> VARIATION_ICON_FILES[status]
                      == summary['variation_icon']
    """
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"

    input_csv = data_dir / "xmr_golden_input.csv"
    expected_csv = data_dir / "xmr_golden_expected_summary.csv"

    assert input_csv.exists(), f"Golden input CSV not found: {input_csv}"
    assert expected_csv.exists(), f"Golden expected summary CSV not found: {expected_csv}"

    # Load the golden per-series expectations
    expected = pd.read_csv(expected_csv)

    # Normalise keys
    expected["OrgCode"] = expected["OrgCode"].astype(str).str.strip()
    expected["MetricName"] = expected["MetricName"].astype(str).str.strip()

    # Derive expected VariationStatus + icon filename from VariationCode
    statuses = []
    icons = []

    for _, row in expected.iterrows():
        status = _expected_status_from_variation_code(row["VariationCode"])
        icon = VARIATION_ICON_FILES[status]
        statuses.append(status.value)
        icons.append(icon)

    expected["ExpectedVariationStatus"] = statuses
    expected["ExpectedVariationIcon"] = icons

    # Run the full exporter on the golden input
    summary, _multi = export_spc_from_csv(
        input_csv,
        working_dir=tmp_path,
        config_dir=Path("config"),
        icons_dir=Path("assets") / "icons",
    )

    # Sanity checks on summary structure
    for col in ("OrgCode", "MetricName", "variation_icon"):
        assert col in summary.columns, (
            f"Summary output missing expected column {col!r}. "
            f"Columns present: {list(summary.columns)}"
        )

    actual = summary[["OrgCode", "MetricName", "variation_icon"]].copy()

    # Normalise keys / filenames
    actual["OrgCode"] = actual["OrgCode"].astype(str).str.strip()
    actual["MetricName"] = actual["MetricName"].astype(str).str.strip()
    actual["variation_icon"] = actual["variation_icon"].astype(str).str.strip()

    # Join expected -> actual by (OrgCode, MetricName)
    merged = expected.merge(
        actual,
        on=["OrgCode", "MetricName"],
        how="inner",
        suffixes=("_exp", "_act"),
    )

    assert not merged.empty, (
        "No overlap between expected golden series and summary output. "
        "Check that group columns (OrgCode, MetricName) match in both CSVs."
    )

    # We expect a 1:1 match of series
    assert len(merged) == len(expected), (
        f"Golden series count != merged series count: "
        f"expected {len(expected)}, merged {len(merged)}. "
        "Some golden series may be missing from the summary."
    )

    # Compare expected vs actual icon filenames
    mismatches = merged[
        merged["ExpectedVariationIcon"].astype(str).str.strip()
        != merged["variation_icon"].astype(str).str.strip()
    ]

    if not mismatches.empty:
        # Helpful debug output if this ever fails
        print("\n[DEBUG] Variation icon mismatches:")
        cols_to_show = [
            "OrgCode",
            "MetricName",
            "VariationCode",
            "VariationCategory",
            "ExpectedVariationStatus",
            "ExpectedVariationIcon",
            "variation_icon",
        ]
        cols_to_show = [c for c in cols_to_show if c in mismatches.columns]
        print(mismatches[cols_to_show].to_string(index=False))

    assert mismatches.empty, (
        "Variation icons do not match expected values for some golden series. "
        "See [DEBUG] output above for details."
    )
