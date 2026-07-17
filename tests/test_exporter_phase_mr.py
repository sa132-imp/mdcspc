import pandas as pd
import pytest

from mdcspc.exporter import _calculate_phase_mr


def test_calculate_phase_mr_restarts_at_phase_boundaries():
    dates = pd.date_range("2025-01-01", periods=20, freq="MS")
    values = [
        10, 12, 11, 13, 12, 14, 13, 15, 14, 16,
        100, 102, 101, 103, 102, 104, 103, 105, 104, 106,
    ]
    phases = [1] * 10 + [2] * 10
    df = pd.DataFrame({"Value": values, "phase": phases}, index=dates)

    result = _calculate_phase_mr(df, value_col="Value")

    phase_1 = result[result["phase"] == 1]
    phase_2 = result[result["phase"] == 2]

    assert pd.isna(phase_1["moving_range"].iloc[0])
    assert pd.isna(phase_2["moving_range"].iloc[0])
    assert 84.0 not in result["moving_range"].dropna().tolist()

    expected_mr_bar = 14.0 / 9.0
    expected_mr_ucl = expected_mr_bar * 3.268

    assert phase_1["mr_bar"].dropna().unique().tolist() == pytest.approx([expected_mr_bar])
    assert phase_2["mr_bar"].dropna().unique().tolist() == pytest.approx([expected_mr_bar])
    assert phase_1["mr_ucl"].dropna().unique().tolist() == pytest.approx([expected_mr_ucl])
    assert phase_2["mr_ucl"].dropna().unique().tolist() == pytest.approx([expected_mr_ucl])
