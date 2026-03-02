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

from mdcspc import analyse_xmr, plot_xmr


# -------------------------------------------------------------------
# CONFIG: this uses your xmr_phase_test_1.csv + two re-calcs
# -------------------------------------------------------------------

# Path to your test CSV (exported from Excel)
CSV_PATH = os.path.join(PROJECT_ROOT, "working", "xmr_phase_test_1.csv")

# Your chosen re-baseline dates:
# Phase 1: before 2023-03-01
# Phase 2: 2023-03-01 to before 2024-07-01
# Phase 3: 2024-07-01 onwards
PHASE_STARTS = ["2023-03-01", "2024-07-01"]

# Rule settings – keep these matched to your Excel template
SHIFT_LENGTH = 6
TREND_LENGTH = 6
MIN_POINTS_FOR_SPC = 10


def main():
    # 1) Load your dataset
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    df = pd.read_csv(
        CSV_PATH,
        parse_dates=["Month"],
        dayfirst=True,
    )

    if "Value" not in df.columns:
        raise ValueError("Expected a 'Value' column in xmr_phase_test_1.csv")

    # 2) Run single-series XmR analysis with phases
    result = analyse_xmr(
        data=df,
        value_col="Value",
        index_col="Month",
        phase_starts=PHASE_STARTS,
        baseline_mode="all",      # per-phase baseline: all points in that phase
        baseline_points=None,
        min_points_for_spc=MIN_POINTS_FOR_SPC,
        shift_length=SHIFT_LENGTH,
        trend_length=TREND_LENGTH,
        rules=("trend", "shift", "2of3", "astronomical"),
    )

    data = result.data

    # 3) Print a compact view so you can compare with Excel
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

    print("\n=== Phase test – single-series XmR with manual phase starts ===\n")
    print(f"Using phase_starts = {PHASE_STARTS}\n")
    print(data[cols_to_show])

    # 4) Plot the chart so you can eyeball the phase behaviour vs Excel
    plot_xmr(
        result,
        value_label="Value",
        title="XmR with manual phase(s) – xmr_phase_test_1.csv",
        figsize=(10, 5),
        show=True,
    )


if __name__ == "__main__":
    main()
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

from mdcspc import analyse_xmr, plot_xmr


# -------------------------------------------------------------------
# CONFIG: this uses your xmr_phase_test_1.csv + two re-calcs
# -------------------------------------------------------------------

# Path to your test CSV (exported from Excel)
CSV_PATH = os.path.join(PROJECT_ROOT, "working", "xmr_phase_test_1.csv")

# Your chosen re-baseline dates:
# Phase 1: before 2023-03-01
# Phase 2: 2023-03-01 to before 2024-07-01
# Phase 3: 2024-07-01 onwards
PHASE_STARTS = ["2023-03-01", "2024-07-01"]

# Rule settings – keep these matched to your Excel template
SHIFT_LENGTH = 6
TREND_LENGTH = 6
MIN_POINTS_FOR_SPC = 10


def main():
    # 1) Load your dataset
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    df = pd.read_csv(
        CSV_PATH,
        parse_dates=["Month"],
        dayfirst=True,
    )

    if "Value" not in df.columns:
        raise ValueError("Expected a 'Value' column in xmr_phase_test_1.csv")

    # 2) Run single-series XmR analysis with phases
    result = analyse_xmr(
        data=df,
        value_col="Value",
        index_col="Month",
        phase_starts=PHASE_STARTS,
        baseline_mode="all",      # per-phase baseline: all points in that phase
        baseline_points=None,
        min_points_for_spc=MIN_POINTS_FOR_SPC,
        shift_length=SHIFT_LENGTH,
        trend_length=TREND_LENGTH,
        rules=("trend", "shift", "2of3", "astronomical"),
    )

    data = result.data

    # 3) Print a compact view so you can compare with Excel
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

    print("\n=== Phase test – single-series XmR with manual phase starts ===\n")
    print(f"Using phase_starts = {PHASE_STARTS}\n")
    print(data[cols_to_show])

    # 4) Plot the chart so you can eyeball the phase behaviour vs Excel
    plot_xmr(
        result,
        value_label="Value",
        title="XmR with manual phase(s) – xmr_phase_test_1.csv",
        figsize=(10, 5),
        show=True,
    )


if __name__ == "__main__":
    main()
