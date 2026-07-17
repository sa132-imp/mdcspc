import pandas as pd

from mdcspc.xmr import analyse_xmr


def test_short_phase_is_warned_but_limits_are_calculated():
    df = pd.DataFrame({
        "Month": pd.date_range("2025-01-01", periods=15, freq="MS"),
        "Value": range(10, 25),
    })

    result = analyse_xmr(
        df,
        value_col="Value",
        index_col="Month",
        phase_starts=["2025-11-01"],
        min_points_for_spc=10,
    )

    out = result.data
    phase_1 = out[out["phase"] == 1]
    phase_2 = out[out["phase"] == 2]

    assert phase_1["phase_low_data"].eq(False).all()
    assert phase_1["phase_low_data_warning"].eq("").all()

    assert phase_2["phase_low_data"].eq(True).all()
    assert phase_2["phase_low_data_warning"].str.contains("5 valid observations").all()
    assert phase_2["mean"].notna().all()
    assert phase_2["ucl"].notna().all()
    assert phase_2["lcl"].notna().all()
