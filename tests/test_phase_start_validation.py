from __future__ import annotations

import pandas as pd
import pytest

from mdcspc.xmr import analyse_xmr


def _data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Period": pd.to_datetime([
                "2026-01-01",
                "2026-02-01",
                "2026-03-01",
                "2026-04-01",
            ]),
            "Value": [10, 11, 12, 13],
        }
    )


def test_phase_start_must_match_an_observation():
    with pytest.raises(ValueError, match="match an actual observation"):
        analyse_xmr(
            _data(),
            value_col="Value",
            index_col="Period",
            phase_starts=["2026-02-15"],
            min_points_for_spc=1,
        )


def test_phase_start_cannot_be_first_observation():
    with pytest.raises(ValueError, match="empty phase"):
        analyse_xmr(
            _data(),
            value_col="Value",
            index_col="Period",
            phase_starts=["2026-01-01"],
            min_points_for_spc=1,
        )


def test_phase_start_after_final_observation_is_rejected():
    with pytest.raises(ValueError, match="match an actual observation"):
        analyse_xmr(
            _data(),
            value_col="Value",
            index_col="Period",
            phase_starts=["2026-05-01"],
            min_points_for_spc=1,
        )


def test_duplicate_phase_starts_are_rejected():
    with pytest.raises(ValueError, match="duplicate phase start"):
        analyse_xmr(
            _data(),
            value_col="Value",
            index_col="Period",
            phase_starts=["2026-03-01", "2026-03-01"],
            min_points_for_spc=1,
        )


def test_valid_phase_start_creates_two_non_empty_phases():
    result = analyse_xmr(
        _data(),
        value_col="Value",
        index_col="Period",
        phase_starts=["2026-03-01"],
        min_points_for_spc=1,
    )

    assert result.data["phase"].tolist() == [1, 1, 2, 2]
