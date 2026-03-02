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
    # Create a simple dummy series:
    # - First 10 points wobble around 100 (stable system)
    # - Next 10 points steadily increase (to trigger a trend)
    data = {
        "Month": pd.date_range("2023-01-01", periods=20, freq="M"),
        "Value": [
            100, 102, 98, 101, 99, 100, 101, 99, 100, 102,   # fairly stable
            103, 104, 105, 106, 107, 108, 109, 110, 111, 112  # clear upward trend
        ],
    }

    df = pd.DataFrame(data)

    # Run single-series XmR analysis
    result = analyse_xmr(
        data=df,
        value_col="Value",
        index_col="Month",
        baseline_mode="all",      # use all points as baseline for now
        baseline_points=None,     # not used with 'all'
        min_points_for_spc=10,    # we have 20 points, so rules will be applied
        shift_length=6,           # match your Excel config
        trend_length=6,           # match your Excel config
        rules=("trend", "shift", "2of3", "astronomical"),
    )

    # Show the key columns so we can see what's happening
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

    print("\n=== XmR analysis output (dummy in-memory test) ===\n")
    print(result.data[cols_to_show])


if __name__ == "__main__":
    main()
