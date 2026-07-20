from __future__ import annotations

import pandas as pd
import pytest

from mdcspc.xmr import analyse_xmr, analyse_xmr_by_group


def test_analyse_xmr_rejects_duplicate_periods():
    df = pd.DataFrame(
        {
            "Period": pd.to_datetime([
                "2026-01-01",
                "2026-02-01",
                "2026-02-01",
            ]),
            "Value": [10, 11, 12],
        }
    )

    with pytest.raises(ValueError, match="duplicate period"):
        analyse_xmr(
            df,
            value_col="Value",
            index_col="Period",
            min_points_for_spc=1,
        )


def test_analyse_xmr_by_group_allows_same_period_in_different_series():
    df = pd.DataFrame(
        {
            "Period": pd.to_datetime([
                "2026-01-01",
                "2026-01-01",
            ]),
            "MetricName": ["Metric A", "Metric B"],
            "Value": [10, 20],
        }
    )

    result = analyse_xmr_by_group(
        df,
        value_col="Value",
        index_col="Period",
        group_cols=["MetricName"],
        min_points_for_spc=1,
    )

    assert len(result.by_group) == 2


def test_analyse_xmr_by_group_rejects_duplicate_period_within_series():
    df = pd.DataFrame(
        {
            "Period": pd.to_datetime([
                "2026-01-01",
                "2026-02-01",
                "2026-02-01",
            ]),
            "MetricName": ["Metric A", "Metric A", "Metric A"],
            "Value": [10, 11, 12],
        }
    )

    with pytest.raises(ValueError, match="duplicate period"):
        analyse_xmr_by_group(
            df,
            value_col="Value",
            index_col="Period",
            group_cols=["MetricName"],
            min_points_for_spc=1,
        )
