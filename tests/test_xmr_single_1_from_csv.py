import os
import sys
import pandas as pd

# -------------------------------------------------------------------
# Make sure the project root (MDCpip) is on sys.path so that
# "import mdcspc" works whether this script is run:
# - from the project root:  python tests/test_xmr_single_1_from_csv.py
# - from inside the tests folder (e.g. VS Code "Run Python File")
# -------------------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from mdcspc import analyse_xmr


def main():
    # Load the CSV you saved in the working folder
    # Explicitly parse Month as a date and treat the format as day-first (UK style)
    csv_path = os.path.join(PROJECT_ROOT, "working", "xmr_test_single_1.csv")
    df = pd.read_csv(
        csv_path,
        parse_dates=["Month"],
        dayfirst=True,
    )

    # Run single-series XmR analysis
    # NOTE: trend_length=6 and shift_length=6 to match your Excel settings
    result = analyse_xmr(
        data=df,
        value_col="Value",
        index_col="Month",
        baseline_mode="all",      # use all points as baseline (matches your Excel run)
        baseline_points=None,     # not used with 'all'
        min_points_for_spc=10,
        shift_length=6,           # match Excel
        trend_length=6,           # match Excel
        rules=("trend", "shift", "2of3", "astronomical"),
    )

    # Pull out one row (they're all the same for mean/UCL/LCL) to show the core stats
    first_row = result.data.iloc[0]

    print("\n=== Core XmR statistics from Python ===\n")
    print(f"Mean:                    {first_row['mean']:.5f}")
    print(f"Sigma (MR-bar/1.128):    {first_row['sigma']:.9f}")
    print(f'Three sigma (3σ):        {3 * first_row["sigma"]:.5f}')
    print(f"Upper process limit UPL: {first_row['ucl']:.5f}")
    print(f"Lower process limit LPL: {first_row['lcl']:.5f}")

    # And show the full table of key columns so we can eyeball rule behaviour
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

    print("\n=== Full per-point output (key columns) ===\n")
    print(result.data[cols_to_show])


if __name__ == "__main__":
    main()
