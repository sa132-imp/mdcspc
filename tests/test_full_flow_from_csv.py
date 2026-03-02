import os
import sys
import pandas as pd

# Ensure project root is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from mdcspc import analyse_xmr_by_group, summarise_xmr_by_group, plot_xmr


def main():
    # 1) Load the multi-org AE4hr example CSV
    csv_path = os.path.join(PROJECT_ROOT, "working", "ae4hr_multi_org_example.csv")

    df = pd.read_csv(
        csv_path,
        parse_dates=["Month"],
        dayfirst=True,
    )

    # 2) Run multi-series XmR analysis grouped by OrgCode + MetricName
    multi = analyse_xmr_by_group(
        data=df,
        value_col="Value",
        index_col="Month",
        group_cols=["OrgCode", "MetricName"],
        baseline_mode="all",
        baseline_points=None,
        min_points_for_spc=10,
        shift_length=6,
        trend_length=6,
        rules=("trend", "shift", "2of3", "astronomical"),
    )

    # 3) Build the summary table (placeholder variation/assurance logic)
    summary = summarise_xmr_by_group(
        multi,
        direction="higher_is_better",
        lookback_points=12,
    )

    print("\n=== Full-flow summary table from ae4hr_multi_org_example.csv ===\n")
    print(summary)

    # 4) Plot one org's chart (e.g. RKB AE4hr) so you can eyeball it
    # Find the group key for OrgCode='RKB', MetricName='AE4hr'
    key = ("RKB", "AE4hr")
    if key in multi.by_group:
        rkb_result = multi.by_group[key]
        plot_xmr(
            rkb_result,
            value_label="AE 4hr %",
            title="RKB AE 4hr – XmR chart (example full flow)",
            figsize=(10, 5),
            show=True,
        )
    else:
        print("\n[Warning] Could not find group ('RKB', 'AE4hr') in multi.by_group.\n")


if __name__ == "__main__":
    main()

