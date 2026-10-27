"""
mdcspc.dates

converts all user-supplied dates into ISO format, else forces dd-mm-yyyy day-first to avoid US ambiguity.

Rule:
- ISO-looking values (YYYY-MM-DD, optionally with a time) are parsed as ISO.
- Everything else is parsed day-first (dd/mm/yyyy).

"""

from __future__ import annotations

from typing import Any

import pandas as pd

ISO_DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?)?$"


def parse_uk_dates(values: Any) -> pd.Series:
    series = values if isinstance(values, pd.Series) else pd.Series(values)

    if pd.api.types.is_datetime64_any_dtype(series):
        return series.dt.normalize()

    text = series.astype(str).str.strip()
    missing = series.isna() | text.eq("")
    iso_mask = ~missing & text.str.match(ISO_DATE_PATTERN)
    other_mask = ~missing & ~iso_mask

    parsed = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    if iso_mask.any():
        parsed.loc[iso_mask] = pd.to_datetime(text.loc[iso_mask], format="ISO8601")
    if other_mask.any():
        parsed.loc[other_mask] = pd.to_datetime(text.loc[other_mask], dayfirst=True)

    return parsed.dt.normalize()
