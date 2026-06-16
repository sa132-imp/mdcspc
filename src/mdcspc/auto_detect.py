from dataclasses import dataclass
from typing import List, Optional
import warnings

import pandas as pd


@dataclass
class DetectionResult:
    index_col: Optional[str]
    value_col: Optional[str]
    group_cols: List[str]
    confidence: str  # HIGH / MEDIUM / LOW
    warnings: List[str]


def _try_parse_dates(series: pd.Series) -> pd.Series:
    """
    Try to parse a Series as dates for auto-detection scoring.

    This is deliberately quiet because auto-detection probes every column,
    including columns that are not meant to be dates. Any real validation
    errors should be raised later by the exporter/analysis path.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Could not infer format.*",
            category=UserWarning,
        )
        return pd.to_datetime(series, errors="coerce")


def _score_date_col(series: pd.Series, name: str) -> int:
    score = 0

    # name hints
    if any(x in name.lower() for x in ["date", "time", "month", "week"]):
        score += 2

    # parseability
    parsed = _try_parse_dates(series)
    if parsed.notna().mean() > 0.8:
        score += 3

    # uniqueness (dates usually high but not unique like IDs)
    if len(series) > 0 and series.nunique() / len(series) > 0.7:
        score += 1

    # penalise numeric-like
    if pd.to_numeric(series, errors="coerce").notna().mean() > 0.8:
        score -= 2

    return score


def _score_value_col(series: pd.Series, name: str) -> int:
    score = 0

    # must be numeric-ish
    numeric_ratio = pd.to_numeric(series, errors="coerce").notna().mean()
    score += int(numeric_ratio * 4)

    if any(x in name.lower() for x in ["value", "count", "score", "rate", "metric"]):
        score += 2

    # not date-like
    date_ratio = _try_parse_dates(series).notna().mean()
    if date_ratio < 0.2:
        score += 1

    return score


def _score_group_col(series: pd.Series) -> int:
    # grouping columns tend to have lower cardinality
    if len(series) == 0:
        return 0

    uniq_ratio = series.nunique() / len(series)

    if uniq_ratio < 0.1:
        return 3
    elif uniq_ratio < 0.3:
        return 2
    else:
        return 0


def detect_columns(df: pd.DataFrame) -> DetectionResult:
    date_scores = {}
    value_scores = {}
    group_scores = {}

    cols = df.columns

    for col in cols:
        s = df[col]

        date_scores[col] = _score_date_col(s, col)
        value_scores[col] = _score_value_col(s, col)
        group_scores[col] = _score_group_col(s)

    index_col = max(date_scores, key=date_scores.get)
    value_col = max(value_scores, key=value_scores.get)

    group_cols = [
        col for col in cols
        if col != index_col and col != value_col and group_scores[col] > 0
    ]

    # confidence rules
    detection_warnings = []
    confidence = "HIGH"

    if date_scores[index_col] < 3:
        confidence = "MEDIUM"
        detection_warnings.append(f"Date column guess is uncertain: {index_col}")

    if value_scores[value_col] < 3:
        confidence = "MEDIUM"
        detection_warnings.append(f"Value column guess is uncertain: {value_col}")

    # collision case
    if index_col == value_col:
        confidence = "LOW"
        detection_warnings.append("Could not clearly separate date and value columns")

    return DetectionResult(
        index_col=index_col,
        value_col=value_col,
        group_cols=group_cols,
        confidence=confidence,
        warnings=detection_warnings,
    )