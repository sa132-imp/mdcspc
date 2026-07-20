from pathlib import Path

import pandas as pd

from mdcspc.exporter_dataframe import export_spc_from_dataframe


def test_missing_group_identifier_warns_but_exports(tmp_path, capsys):
    df = pd.DataFrame(
        {
            "Month": pd.date_range("2026-01-01", periods=10, freq="MS"),
            "Value": range(1, 11),
            "OrgCode": [
                "ORG001",
                "ORG001",
                "ORG001",
                "ORG001",
                "ORG001",
                "",
                "",
                "",
                "",
                "",
            ],
            "MetricName": ["Test"] * 10,
        }
    )

    export_spc_from_dataframe(
        df,
        working_dir=tmp_path,
        quiet=False,
    )

    captured = capsys.readouterr()

    assert "Group column 'OrgCode' contains" in captured.out

    summary = pd.read_csv(
        tmp_path / "spc_summary_from_input.csv"
    )

    assert len(summary) > 0
