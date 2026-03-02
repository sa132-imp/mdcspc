import os
import sys
import pandas as pd

# Ensure project root is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from mdcspc import analyse_xmr, plot_xmr


def main():
    csv_path = os.path.join(PROJECT_ROOT, "working", "xmr_test_single_3.csv")

    df = pd.read_csv(
        csv_path,
        parse_dates=["Month"],
        dayfirst=True,
    )

    result = analyse_xmr(
        data=df,
        value_col="Value",
        index_col="Month",
        baseline_mode="all",
        baseline_points=None,
        min_points_for_spc=10,
        shift_length=6,
        trend_length=6,
        rules=("trend", "shift", "2of3", "astronomical"),
    )

    # Basic plot – should show a stable system with no highlighted points
    plot_xmr(
        result,
        value_label="Value",
        title="Test XmR – stable system (dataset 3)",
        figsize=(10, 5),
        show=True,
    )


if __name__ == "__main__":
    main()
