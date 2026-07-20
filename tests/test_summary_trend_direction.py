from __future__ import annotations

import pandas as pd

from mdcspc.summary import _classify_variation_for_last_point


def test_downward_trend_above_mean_is_improvement_when_lower_is_better():
    df = pd.DataFrame(
        {
            "Value": [30, 29, 28, 27, 26, 25],
            "mean": [20, 20, 20, 20, 20, 20],
            "special_cause": [True, True, True, True, True, True],
            "special_cause_label": ["trend"] * 6,
        },
        index=pd.date_range("2026-01-01", periods=6, freq="MS"),
    )

    result = _classify_variation_for_last_point(
        df=df,
        value_col="Value",
        direction="lower_is_better",
    )

    assert result["variation_key"] == "improvement"
    assert result["variation_colour"] == "blue"
    assert result["variation_side"] == "high"


def test_upward_trend_below_mean_is_improvement_when_higher_is_better():
    df = pd.DataFrame(
        {
            "Value": [10, 11, 12, 13, 14, 15],
            "mean": [20, 20, 20, 20, 20, 20],
            "special_cause": [True, True, True, True, True, True],
            "special_cause_label": ["trend"] * 6,
        },
        index=pd.date_range("2026-01-01", periods=6, freq="MS"),
    )

    result = _classify_variation_for_last_point(
        df=df,
        value_col="Value",
        direction="higher_is_better",
    )

    assert result["variation_key"] == "improvement"
    assert result["variation_colour"] == "blue"
    assert result["variation_side"] == "low"


def test_upward_trend_is_concern_when_lower_is_better():
    df = pd.DataFrame(
        {
            "Value": [10, 11, 12, 13, 14, 15],
            "mean": [20, 20, 20, 20, 20, 20],
            "special_cause": [True, True, True, True, True, True],
            "special_cause_label": ["trend"] * 6,
        },
        index=pd.date_range("2026-01-01", periods=6, freq="MS"),
    )

    result = _classify_variation_for_last_point(
        df=df,
        value_col="Value",
        direction="lower_is_better",
    )

    assert result["variation_key"] == "concern"
    assert result["variation_colour"] == "orange"


def test_downward_trend_is_concern_when_higher_is_better():
    df = pd.DataFrame(
        {
            "Value": [30, 29, 28, 27, 26, 25],
            "mean": [20, 20, 20, 20, 20, 20],
            "special_cause": [True, True, True, True, True, True],
            "special_cause_label": ["trend"] * 6,
        },
        index=pd.date_range("2026-01-01", periods=6, freq="MS"),
    )

    result = _classify_variation_for_last_point(
        df=df,
        value_col="Value",
        direction="higher_is_better",
    )

    assert result["variation_key"] == "concern"
    assert result["variation_colour"] == "orange"
