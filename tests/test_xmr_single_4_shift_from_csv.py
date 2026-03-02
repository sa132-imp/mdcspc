import os
import sys
import pandas as pd

# -------------------------------------------------------------------
# Ensure project root (MDCpip) is on sys.path so "import mdcspc" works
# regardless of where this script is launched from.
# -------------------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from mdcspc import analyse_xmr


def main():
    # Path to the shift dataset CSV
    csv_path = os.path.join(PROJECT_ROOT, "working", "xmr_test_single_4_shift.csv")

    # Load CSV, parse Month as UK-style dates
    df = pd.read_csv(
        csv_path,
        parse_dates=["Month"],
        dayfirst=True,
    )

    # Run single-series XmR analysis with same settings as your Excel template
    result = analyse_xmr(
        data=df,
        value_col="Value",
        index_col="Month",
        baseline_mode="all",      # use all points as baseline
        baseline_points=None,
        min_points_for_spc=10,
        shift_length=6,
        trend_length=6,
        rules=("trend", "shift", "2of3", "astronomical"),
    )

    # Core stats
    first_row = result.data.iloc[0]

    print("\n=== Core XmR statistics for test dataset 4 (shift pattern) ===\n")
    print(f"Mean:                    {first_row['mean']:.5f}")
    print(f"Sigma (MR-bar/1.128):    {first_row['sigma']:.9f}")
    print(f'Three sigma (3σ):        {3 * first_row["sigma"]:.5f}')
    print(f"Upper process limit UPL: {first_row['ucl']:.5f}")
    print(f"Lower process limit LPL: {first_row['lcl']:.5f}")

    # Per-point rule behaviour – we expect shift to dominate, not trend
    cols_to_show = [
        "Value",
        "phase",
        "mean",
        "ucl",
        "lcl",
        "rule_trend",
        "rule_shift",
        "rule_2of3",
        "rule_astronomical",
        "special_cause",
        "special_cause_label",
    ]

    print("\n=== Per-point output for dataset 4 (expected: shift, no trend) ===\n")
    print(result.data[cols_to_show])


if __name__ == "__main__":
    main()
