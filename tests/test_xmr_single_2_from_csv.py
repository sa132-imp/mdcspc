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
    # Path to dataset 2 (2-of-3 + astronomical test)
    csv_path = os.path.join(PROJECT_ROOT, "working", "xmr_test_single_2.csv")

    # Load CSV, parse Month as UK-style dates
    df = pd.read_csv(
        csv_path,
        parse_dates=["Month"],
        dayfirst=True,
    )

    # For this test we ONLY care about:
    # - 2-of-3 rule
    # - astronomical rule
    # So we switch off trend and shift by not listing them in `rules`.
    result = analyse_xmr(
        data=df,
        value_col="Value",
        index_col="Month",
        baseline_mode="all",      # use all points as baseline
        baseline_points=None,
        min_points_for_spc=10,
        shift_length=6,           # irrelevant here (rule_shift is off)
        trend_length=6,           # irrelevant here (rule_trend is off)
        rules=("2of3", "astronomical"),
    )

    # Show the core stats (mean / sigma / limits)
    first_row = result.data.iloc[0]

    print("\n=== Core XmR statistics for test dataset 2 ===\n")
    print(f"Mean:                    {first_row['mean']:.5f}")
    print(f"Sigma (MR-bar/1.128):    {first_row['sigma']:.9f}")
    print(f'Three sigma (3σ):        {3 * first_row["sigma"]:.5f}')
    print(f"Upper process limit UPL: {first_row['ucl']:.5f}")
    print(f"Lower process limit LPL: {first_row['lcl']:.5f}")

    # Show per-point rule behaviour
    cols_to_show = [
        "Value",
        "phase",
        "mean",
        "ucl",
        "lcl",
        "rule_2of3",
        "rule_astronomical",
        "special_cause",
        "special_cause_label",
    ]

    print("\n=== Per-point output for dataset 2 (2-of-3 + astronomical only) ===\n")
    print(result.data[cols_to_show])


if __name__ == "__main__":
    main()
