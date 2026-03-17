from __future__ import annotations

from pathlib import Path

import pandas as pd

TARGET_CONFIG_COLUMNS = [
    "OrgCode",
    "MetricName",
    "EffectiveFrom",
    "TargetValue",
]


def load_spc_target_config(config_path: Path) -> pd.DataFrame:
    """
    Load spc_target_config.csv.

    If the file does not exist, return an empty DataFrame with the expected
    columns so callers can safely append/write without special casing.
    """
    config_path = Path(config_path)

    if not config_path.exists():
        return pd.DataFrame(columns=TARGET_CONFIG_COLUMNS)

    df = pd.read_csv(config_path)
    for col in TARGET_CONFIG_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    return df[TARGET_CONFIG_COLUMNS].copy()


def write_spc_target_config(df: pd.DataFrame, config_path: Path) -> None:
    """
    Write spc_target_config.csv with a stable column order.
    """
    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    out = df.copy() if df is not None else pd.DataFrame(columns=TARGET_CONFIG_COLUMNS)
    for col in TARGET_CONFIG_COLUMNS:
        if col not in out.columns:
            out[col] = pd.NA

    out = out[TARGET_CONFIG_COLUMNS].copy()
    out.to_csv(config_path, index=False)
