import os
import sys
import pandas as pd

# Ensure project root is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from mdcspc import analyse_xmr_by_group, summarise_xmr_by_group


def main():
    # Simple multi-org dummy dataset:
    # - Two orgs: ORG1 and ORG2
    # - Same 20-month pattern for both
    months = pd.date_range("2023-01-01", periods=20, freq="M")
    values = [
        100, 102, 98, 101, 99, 100, 101, 99, 100, 102,   # relatively stable
        103, 104, 105, 106, 107, 108, 109, 110, 111, 112  # clear upward trend
    ]

    df_org1 = pd.DataFrame({"Month": months, "OrgCode": "ORG1", "MetricName": "AE4hr", "Value": values})
    df_org2 = pd.DataFrame({"Month": months, "OrgCode": "ORG2", "MetricName": "AE4hr", "Value": values})

    df = pd.concat([df_org1, df_org2], axis=0, ignore_index=True)

    # Run multi-series analysis grouped by OrgCode + MetricName
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

    # Build summary (placeholder logic for variation/assurance)
    summary = summarise_xmr_by_group(
        multi,
        direction="higher_is_better",
        lookback_points=12,
    )

    print("\n=== Summary table (basic placeholder logic) ===\n")
    print(summary)


if __name__ == "__main__":
    main()
