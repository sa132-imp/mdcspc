import pandas as pd
import pytest

from mdcspc.xmr import analyse_xmr


def test_positive_infinity_is_rejected():
    df = pd.DataFrame(
        {
            "Month": pd.date_range("2026-01-01", periods=10, freq="MS"),
            "Value": [1, 2, 3, 4, 5, 6, 7, 8, float("inf"), 10],
        }
    )

    with pytest.raises(ValueError, match="infinite"):
        analyse_xmr(df, value_col="Value", index_col="Month")


def test_negative_infinity_is_rejected():
    df = pd.DataFrame(
        {
            "Month": pd.date_range("2026-01-01", periods=10, freq="MS"),
            "Value": [1, 2, 3, 4, 5, 6, 7, 8, float("-inf"), 10],
        }
    )

    with pytest.raises(ValueError, match="infinite"):
        analyse_xmr(df, value_col="Value", index_col="Month")


def test_missing_values_remain_allowed():
    df = pd.DataFrame(
        {
            "Month": pd.date_range("2026-01-01", periods=10, freq="MS"),
            "Value": [1, 2, None, 4, 5, 6, 7, 8, 9, 10],
        }
    )

    result = analyse_xmr(df, value_col="Value", index_col="Month")

    assert result.data["Value"].isna().sum() == 1
