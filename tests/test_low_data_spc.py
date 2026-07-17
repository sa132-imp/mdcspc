import pandas as pd

from mdcspc.xmr import analyse_xmr


def test_low_data_spc_triggers_fallback():
    # Arrange: only 5 points (below default threshold of 10)
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=5, freq="MS"),
        "value": [10, 12, 11, 13, 12],
    })

    # Act
    result = analyse_xmr(
        data=df,
        value_col="value",
        index_col="date",
        min_points_for_spc=10,
    )

    out = result.data

    # Assert: low data flag exists and is true
    assert "low_data_spc" in out.columns
    assert bool(out["low_data_spc"].iloc[0]) is True

    # Assert: user-visible warning text is included in the output
    assert "low_data_warning" in out.columns
    assert "SPC limits not calculated" in out["low_data_warning"].iloc[0]

    # Assert: limits are NaN
    assert out["mean"].isna().all()
    assert out["sigma"].isna().all()
    assert out["ucl"].isna().all()
    assert out["lcl"].isna().all()

    # Assert: rules disabled
    rule_cols = [c for c in out.columns if c.startswith("rule_")]
    for c in rule_cols:
        assert out[c].sum() == 0

    # Assert: special cause off
    assert out["special_cause"].sum() == 0


def test_missing_values_do_not_count_towards_minimum():
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=10, freq="MS"),
        "value": [10, 11, 12, 13, None, 15, 16, 17, 18, 19],
    })

    result = analyse_xmr(
        data=df,
        value_col="value",
        index_col="date",
        min_points_for_spc=10,
    )

    out = result.data

    assert "low_data_spc" in out.columns
    assert bool(out["low_data_spc"].iloc[0]) is True
    assert out["mean"].isna().all()
    assert out["ucl"].isna().all()
    assert out["lcl"].isna().all()


def test_zero_counts_as_valid_observation():
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=10, freq="MS"),
        "value": [10, 11, 12, 13, 0, 15, 16, 17, 18, 19],
    })

    result = analyse_xmr(
        data=df,
        value_col="value",
        index_col="date",
        min_points_for_spc=10,
    )

    out = result.data

    assert "low_data_spc" not in out.columns
    assert out["mean"].notna().all()
    assert out["ucl"].notna().all()
    assert out["lcl"].notna().all()
