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

from mdcspc import analyse_xmr_by_group


def main():
    # Build a simple multi-org dummy dataset:
    # - Two orgs: ORG1 and ORG2
    # - Same 20-month pattern for both (reusing the first test case)
    months = pd.date_range("2023-01-01", periods=20, freq="M")
    values = [
        100, 102, 98, 101, 99, 100, 101, 99, 100, 102,   # fairly stable
        103, 104, 105, 106, 107, 108, 109, 110, 111, 112  # upward trend
    ]

    df_org1 = pd.DataFrame({"Month": months, "OrgCode": "ORG1", "Value": values})
    df_org2 = pd.DataFrame({"Month": months, "OrgCode": "ORG2", "Value": values})

    df = pd.concat([df_org1, df_org2], axis=0, ignore_index=True)

    # Run multi-series analysis grouped by OrgCode
    multi = analyse_xmr_by_group(
        data=df,
        value_col="Value",
        index_col="Month",
        group_cols="OrgCode",     # could also be ["OrgCode"] or ["OrgCode", "MetricName"] later
        baseline_mode="all",
        baseline_points=None,
        min_points_for_spc=10,
        shift_length=6,
        trend_length=6,
        rules=("trend", "shift", "2of3", "astronomical"),
    )

    print("\n=== MultiXmrResult.config ===\n")
    print(multi.config)

    print("\n=== Combined data (first 15 rows) ===\n")
    cols_to_show = [
        "OrgCode",
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
    print(multi.data[cols_to_show].head(15))

    print("\n=== Available groups in by_group ===\n")
    for key in multi.by_group.keys():
        print("Group key:", key)

    # Show a snippet for ORG1 only
    org1_result = multi.by_group[("ORG1",)]
    print("\n=== ORG1 per-point output (first 10 rows) ===\n")
    print(org1_result.data[cols_to_show].head(10))


if __name__ == "__main__":
    main()
