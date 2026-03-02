import os
import sys
import argparse
from pathlib import Path

# Make sure the project root (MDCpip) is on sys.path so "import mdcspc" works
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mdcspc.exporter import export_spc_from_csv  # noqa: E402


"""
CLI wrapper for mdcspc.exporter.export_spc_from_csv

Usage (from the MDCpip project root):

    # Use the default example CSV and X + mR charts
    python scripts/export_spc_from_csv.py

    # Run on a specific CSV, X + mR charts
    python scripts/export_spc_from_csv.py working/ae4hr_multi_org_example.csv

    # Run on a specific CSV, X-only charts (no mR panel)
    python scripts/export_spc_from_csv.py working/ae4hr_multi_org_example.csv --chart-mode x_only

Arguments
---------
input_csv (positional, optional)
    Path to the input CSV. If omitted, defaults to:
        PROJECT_ROOT / "working" / "ae4hr_multi_org_example.csv"

--chart-mode {xmr, x_only}
    xmr     : X + mR charts (default)
    x_only  : X chart only
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run MDC-style XmR analysis and export summary + charts from a CSV."
    )
    parser.add_argument(
        "input_csv",
        nargs="?",
        help=(
            "Path to the input CSV. If omitted, defaults to "
            "'working/ae4hr_multi_org_example.csv' under the project root."
        ),
    )
    parser.add_argument(
        "--chart-mode",
        choices=["xmr", "x_only"],
        default="xmr",
        help=(
            "Chart mode: 'xmr' for X + mR charts (default), "
            "'x_only' for X chart only."
        ),
    )

    args = parser.parse_args()

    # Work out the input path
    if args.input_csv:
        input_path = Path(args.input_csv)
        if not input_path.is_absolute():
            # Treat relative paths as relative to the project root
            input_path = PROJECT_ROOT / input_path
    else:
        # Default to the example CSV
        input_path = PROJECT_ROOT / "working" / "ae4hr_multi_org_example.csv"

    # Call the library-level exporter
    export_spc_from_csv(
        input_csv=input_path,
        chart_mode=args.chart_mode,
    )


if __name__ == "__main__":
    main()
