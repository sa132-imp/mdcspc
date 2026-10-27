from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from matplotlib.axes import Axes

from mdcspc.dates import parse_uk_dates
from mdcspc.exporter import _load_target_config, export_spc_from_csv
from mdcspc.exporter_dataframe import _ensure_datetime_column

MAY_1 = pd.Timestamp("2025-05-01")


@pytest.mark.parametrize(
    "value",
    ["01/05/2025", "1/5/2025", "2025-05-01", "2025-05-01 00:00:00", " 01/05/2025 "],
)
def test_uk_and_iso_dates_parse_to_the_same_day(value):
    assert parse_uk_dates([value]).iloc[0] == MAY_1


def test_mixed_formats_missing_and_blank_values():
    parsed = parse_uk_dates(["2023-04-01", "13/10/2023", None, ""])

    assert parsed.iloc[0] == pd.Timestamp("2023-04-01")
    assert parsed.iloc[1] == pd.Timestamp("2023-10-13")
    assert parsed.iloc[2:].isna().all()


def test_unparseable_dates_raise():
    with pytest.raises(ValueError):
        parse_uk_dates(["32/01/2025"])


@pytest.mark.parametrize(
    "effective_from",
    [["2023-04-01", "2023-10-01"], ["01/04/2023", "01/10/2023"], ["2023-04-01", "01/10/2023"]],
)
def test_target_config_dates_are_not_day_month_swapped(tmp_path: Path, effective_from):
    rows = "".join(f"RKB,AE4hr,{d},95\n" for d in effective_from)
    (tmp_path / "spc_target_config.csv").write_text(
        "OrgCode,MetricName,EffectiveFrom,TargetValue\n" + rows
    )

    cfg = _load_target_config(tmp_path, tmp_path, ["OrgCode", "MetricName"], quiet=True)

    assert cfg["EffectiveFrom"].tolist() == [pd.Timestamp("2023-04-01"), pd.Timestamp("2023-10-01")]


def test_dataframe_api_parses_uk_string_dates_day_first():
    df = pd.DataFrame({"Month": ["01/01/2024", "01/02/2024", "01/03/2024"], "Value": [1, 2, 3]})

    out = _ensure_datetime_column(df, "Month")

    assert out["Month"].tolist() == list(pd.date_range("2024-01-01", periods=3, freq="MS"))


def _write_phase_series(root: Path, phase_cfg_dir: Path, phase_start: str) -> Path:
    months = pd.date_range("2024-01-01", periods=24, freq="MS")
    values = [50 + (i % 5) for i in range(16)] + [80 + (i % 5) for i in range(8)]
    input_csv = root / "input.csv"
    pd.DataFrame(
        {
            "MetricName": "Metric1",
            "OrgCode": "OrgA",
            "Month": months.strftime("%d/%m/%Y"),
            "Value": values,
        }
    ).to_csv(input_csv, index=False)

    phase_cfg_dir.mkdir(parents=True, exist_ok=True)
    (phase_cfg_dir / "spc_phase_config.csv").write_text(
        "OrgCode,MetricName,PhaseStart,Annotation,ShowOnChart,AnnotationPosition\n"
        f"OrgA,Metric1,{phase_start},New triage process,True,U\n"
    )
    return input_csv


def _record_chart_text(monkeypatch) -> list:
    drawn = []
    original_text = Axes.text

    def recording_text(self, x, y, s, *args, **kwargs):
        drawn.append(str(s))
        return original_text(self, x, y, s, *args, **kwargs)

    monkeypatch.setattr(Axes, "text", recording_text)
    return drawn


@pytest.mark.parametrize("phase_start", ["01/05/2025", "2025-05-01"])
def test_phase_annotation_is_drawn_for_uk_and_iso_phase_starts(tmp_path: Path, monkeypatch, phase_start):
    config_dir = tmp_path / "config"
    input_csv = _write_phase_series(tmp_path, config_dir, phase_start)
    drawn = _record_chart_text(monkeypatch)

    _, multi = export_spc_from_csv(input_csv, working_dir=tmp_path, config_dir=config_dir, quiet=True)

    data = next(iter(multi.by_group.values())).data
    assert data.loc[data["phase"] == 2, "Month"].min() == MAY_1
    assert any("triage" in text for text in drawn)


def test_phase_annotation_is_drawn_from_legacy_working_dir_config(tmp_path: Path, monkeypatch):
    input_csv = _write_phase_series(tmp_path, tmp_path, "01/05/2025")
    drawn = _record_chart_text(monkeypatch)

    export_spc_from_csv(
        input_csv,
        working_dir=tmp_path,
        config_dir=tmp_path / "empty_config",
        quiet=True,
    )

    assert any("triage" in text for text in drawn)
