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


# -------------------------------------------------------------------
# CONFIG: match this to your existing phase test
# -------------------------------------------------------------------

CSV_PATH = os.path.join(PROJECT_ROOT, "working", "xmr_phase_test_1.csv")

# IMPORTANT:
# Use the SAME phase start dates here that you used in
# test_xmr_phase_single_from_csv.py
PHASE_STARTS = [
    "2023-03-01"
    ,"2024-07-01"
    # Example:
    # "2021-10-31",
    # "2023-04-30",
]

SHIFT_LENGTH = 6
TREND_LENGTH = 6
MIN_POINTS_FOR_SPC = 10


def main():
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    df = pd.read_csv(
        CSV_PATH,
        parse_dates=["Month"],
        dayfirst=True,
    )

    if "Value" not in df.columns:
        raise ValueError("Expected a 'Value' column in xmr_phase_test_1.csv")

    # 1) Run XmR with phases
    result = analyse_xmr(
        data=df,
        value_col="Value",
        index_col="Month",
        phase_starts=PHASE_STARTS,
        baseline_mode="all",
        baseline_points=None,
        min_points_for_spc=MIN_POINTS_FOR_SPC,
        shift_length=SHIFT_LENGTH,
        trend_length=TREND_LENGTH,
        rules=("trend", "shift", "2of3", "astronomical"),
    )

    res = result.data.copy()

    # Restore Month as a normal column for clarity
    res = res.reset_index().rename(columns={"index": "Month"})

    # 2) Compute Moving Range per phase:
    #    MR = |Value_t - Value_(t-1)|, within each phase
    mr_col = "MR = |Value_t - Value_(t-1)| (within phase)"
    res[mr_col] = res.groupby("phase")[result.config.value_col].diff().abs()

    # 3) MR-bar per phase = AVERAGE(MR) within that phase
    mrbar_col = "MR_bar (per phase) = AVERAGE(MR within phase)"
    res[mrbar_col] = res.groupby("phase")[mr_col].transform("mean")

    # 4) Sigma = MR_bar / 1.128
    sigma_col = "Sigma = MR_bar / 1.128"
    res[sigma_col] = res[mrbar_col] / 1.128

    # 5) 3σ = 3 * Sigma
    three_sigma_col = "3sigma = 3 * Sigma"
    res[three_sigma_col] = 3.0 * res[sigma_col]

    # 6) Mean (per phase) – taken from engine, but label with formula
    mean_col = "Mean (per phase) = AVERAGE(Value within phase)"
    res[mean_col] = res["mean"]

    # 7) UPL / LPL = Mean ± 3 * Sigma
    upl_col = "UPL = Mean + 3 * Sigma"
    lpl_col = "LPL = Mean - 3 * Sigma"
    res[upl_col] = res[mean_col] + res[three_sigma_col]
    res[lpl_col] = res[mean_col] - res[three_sigma_col]

    # 8) Include rule flags and labels so you can see what’s firing
    rule_cols = [
        "rule_trend",
        "rule_shift",
        "rule_2of3",
        "rule_astronomical",
        "special_cause",
        "special_cause_label",
    ]

    # 9) Build a tidy column order
    cols_order = [
        "Month",
        "Value",
        "phase",
        mr_col,
        mrbar_col,
        sigma_col,
        three_sigma_col,
        mean_col,
        upl_col,
        lpl_col,
    ] + rule_cols

    debug_table = res[cols_order]

    # 10) Save to CSV for side-by-side comparison with Excel
    output_path = os.path.join(PROJECT_ROOT, "working", "xmr_phase_test_1_debug_table.csv")
    debug_table.to_csv(output_path, index=False)

    print("\n=== Debug table written ===")
    print(f"Path: {output_path}\n")
    print("First 15 rows:\n")
    print(debug_table.head(15))


if __name__ == "__main__":
    main()
