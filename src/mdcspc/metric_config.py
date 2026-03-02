"""
Metric configuration loader and helpers for the MDC SPC library.

Reads metric_config.csv and exposes a simple, typed interface
for looking up per-metric settings such as direction, target, unit etc.

Also defines helpers for mapping SPC results + metric config
into high-level variation/assurance statuses and icon filenames.

Config resolution priority (best-practice, install-safe):

1) If caller provides path=... -> use that file
2) Else if caller provides config_dir=... -> use <config_dir>/metric_config.csv
3) Else if DEFAULT_CONFIG_PATH (legacy) points to an existing file -> use that
4) Else if repo root config exists -> use <repo>/config/metric_config.csv (dev-friendly)
5) Else -> use packaged default resource:
      mdcspc/resources/config/metric_config.csv

This ensures "pip install mdcspc" works anywhere, while still allowing
easy development using the repo-root config/ folder.

Backward compatibility:
- DEFAULT_CONFIG_PATH is kept so tests (and any existing callers) can monkeypatch it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import os
import pandas as pd

# Python 3.9+ importlib.resources API (works on 3.13)
from importlib import resources


# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------

# Repo root is assumed to be the parent of the mdcspc package directory.
# In an installed wheel, this will point inside site-packages and will
# not contain a repo-level "config/" folder (which is fine).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO_CONFIG_PATH = PROJECT_ROOT / "config" / "metric_config.csv"

# Legacy / backwards compatible constant (tests monkeypatch this)
DEFAULT_CONFIG_PATH = str(DEFAULT_REPO_CONFIG_PATH)

PACKAGED_RESOURCE_REL_PATH = Path("resources") / "config" / "metric_config.csv"


# -------------------------------------------------------------------
# Data structures
# -------------------------------------------------------------------


@dataclass(frozen=True)
class MetricConfig:
    """
    Configuration for a single metric (v1 scope).

    Fields:

    - metric_name: key used in the data (e.g. "AE_4hr_Performance")
    - display_name: human-friendly label for charts/tables
    - direction: "higher", "lower" or "neutral"
    - has_target: whether the metric has a target at all
    - target_value: single current target value (None if no target)
    - unit: e.g. "percent", "rate", "count", "time", "other"
    - decimal_places: preferred display precision (None to use defaults)
    """

    metric_name: str
    display_name: str
    direction: str  # "higher" | "lower" | "neutral"
    has_target: bool
    target_value: Optional[float]
    unit: str
    decimal_places: Optional[int]


class VariationStatus(Enum):
    """
    High-level variation classification for the latest point / series.

    This is deliberately generic; mapping to colours/icons happens separately.
    """

    COMMON_CAUSE = "common_cause"
    IMPROVEMENT_HIGH = "improvement_high"
    IMPROVEMENT_LOW = "improvement_low"
    CONCERN_HIGH = "concern_high"
    CONCERN_LOW = "concern_low"
    NEITHER_HIGH = "neither_high"  # special cause, but directionally neutral
    NEITHER_LOW = "neither_low"


class AssuranceStatus(Enum):
    """
    Assurance classification relative to the target.

    For v1 we keep this simple and aligned to your icons:
      - PASSING: Blue P
      - HIT_OR_MISS: Grey P/F
      - FAILING: Orange F
      - NO_TARGET: Empty icon
    """

    PASSING = "passing"
    HIT_OR_MISS = "hit_or_miss"
    FAILING = "failing"
    NO_TARGET = "no_target"


# -------------------------------------------------------------------
# Icon filename mappings (centralised here)
# -------------------------------------------------------------------

VARIATION_ICON_FILES: Dict[VariationStatus, str] = {
    VariationStatus.COMMON_CAUSE: "VariationIconCommonCause.png",
    VariationStatus.IMPROVEMENT_HIGH: "VariationIconImprovementHigh.png",
    VariationStatus.IMPROVEMENT_LOW: "VariationIconImprovementLow.png",
    VariationStatus.CONCERN_HIGH: "VariationIconConcernHigh.png",
    VariationStatus.CONCERN_LOW: "VariationIconConcernLow.png",
    VariationStatus.NEITHER_HIGH: "VariationIconNeitherHigh.png",
    VariationStatus.NEITHER_LOW: "VariationIconNeitherLow.png",
}

ASSURANCE_ICON_FILES: Dict[AssuranceStatus, str] = {
    AssuranceStatus.FAILING: "AssuranceIconFail.png",
    AssuranceStatus.HIT_OR_MISS: "AssuranceIconHitOrMiss.png",
    AssuranceStatus.PASSING: "AssuranceIconPass.png",
    AssuranceStatus.NO_TARGET: "IconEmpty.png",
}


# -------------------------------------------------------------------
# Internal helpers
# -------------------------------------------------------------------


def _normalise_bool(value: object) -> bool:
    """
    Convert various truthy/falsy strings into a bool.

    Interprets "yes", "y", "true", "1" (case-insensitive) as True.
    Everything else is False.
    """
    if value is None:
        return False
    text = str(value).strip().lower()
    return text in {"yes", "y", "true", "1"}


def _safe_float(value: object, metric_name: str, field_name: str) -> Optional[float]:
    """
    Convert a value to float or return None if blank/NaN.
    Raise a clear error if conversion fails.
    """
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    if pd.isna(value):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"Invalid numeric value for {field_name!r} on metric {metric_name!r}: {value!r}"
        )


def _safe_int(value: object, metric_name: str, field_name: str) -> Optional[int]:
    """
    Convert a value to int or return None if blank/NaN.
    Raise a clear error if conversion fails.
    """
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    if pd.isna(value):
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"Invalid integer value for {field_name!r} on metric {metric_name!r}: {value!r}"
        )


def _resolve_metric_config_path(
    path: Optional[Union[str, os.PathLike]] = None,
    config_dir: Optional[Union[str, os.PathLike]] = None,
) -> Tuple[Optional[Path], str]:
    """
    Decide where to load metric_config.csv from.

    Returns:
        (resolved_path, source_label)

    resolved_path:
        A filesystem Path to load from, if available locally.
        If None, caller should load from packaged resources.

    source_label:
        Human label useful for error messages.
    """
    if path:
        p = Path(path).expanduser().resolve()
        return p, "explicit path"

    if config_dir:
        cd = Path(config_dir).expanduser().resolve()
        return cd / "metric_config.csv", "config_dir override"

    # Backwards compatible: allow tests/callers to monkeypatch DEFAULT_CONFIG_PATH
    try:
        legacy = Path(DEFAULT_CONFIG_PATH).expanduser()
        if legacy.exists():
            return legacy.resolve(), "DEFAULT_CONFIG_PATH (legacy/monkeypatched)"
    except Exception:
        # If someone monkeypatches it to something invalid, ignore and continue
        pass

    # Dev-friendly: if repo root config exists, use it
    if DEFAULT_REPO_CONFIG_PATH.exists():
        return DEFAULT_REPO_CONFIG_PATH, "repo root config/"

    # Otherwise fall back to packaged resources
    return None, "packaged default resource"


def _read_packaged_metric_config() -> pd.DataFrame:
    """
    Read metric_config.csv from packaged resources.

    Expects: mdcspc/resources/config/metric_config.csv
    """
    try:
        traversable = resources.files("mdcspc").joinpath(str(PACKAGED_RESOURCE_REL_PATH))
    except Exception as e:
        raise FileNotFoundError(
            "Unable to locate packaged metric_config.csv via importlib.resources.\n"
            "Expected it to be packaged at: mdcspc/resources/config/metric_config.csv\n"
            f"Underlying error: {e!r}"
        )

    # as_file handles cases where resources are inside a zip/wheel
    with resources.as_file(traversable) as p:
        if not Path(p).exists():
            raise FileNotFoundError(
                "Packaged metric_config.csv not found.\n"
                "Expected it to be packaged at: mdcspc/resources/config/metric_config.csv\n"
                "This usually means the file wasn't included in the wheel/sdist."
            )
        return pd.read_csv(p)


# -------------------------------------------------------------------
# Public API – config loading
# -------------------------------------------------------------------


def load_metric_config(
    path: Optional[str] = None,
    config_dir: Optional[Union[str, os.PathLike]] = None,
) -> Dict[str, MetricConfig]:
    """
    Load metric configuration from a CSV file.

    Expected columns (v1):

        MetricName,DisplayName,Direction,HasTarget,TargetValue,Unit,DecimalPlaces

    - MetricName: key that will match the metric in your data.
    - DisplayName: human label for charts/tables.
    - Direction: "higher", "lower", or "neutral".
    - HasTarget: "yes"/"no" (or similar truthy/falsy).
    - TargetValue: numeric (can be blank if HasTarget = no).
    - Unit: "percent", "rate", "count", "time", "other".
    - DecimalPlaces: integer (e.g. 0, 1, 2) or blank.

    Parameters
    ----------
    path:
        Explicit path to a metric_config.csv file. If provided, this wins.
    config_dir:
        Directory containing metric_config.csv. Used by CLI --config-dir.
        If provided (and path is not), we look for <config_dir>/metric_config.csv.

    Returns
    -------
    Dict[str, MetricConfig]
        A dict mapping MetricName -> MetricConfig.
    """
    resolved_path, source_label = _resolve_metric_config_path(path=path, config_dir=config_dir)

    if resolved_path is not None:
        if not resolved_path.exists():
            raise FileNotFoundError(
                "Metric config file not found.\n"
                f"Source: {source_label}\n"
                f"Looked for: {resolved_path}\n"
                "Fix options:\n"
                "  - Pass path=... to load_metric_config(), or\n"
                "  - Use config_dir=... (CLI: --config-dir), or\n"
                "  - Ensure packaged defaults are included (mdcspc/resources/config/metric_config.csv)."
            )
        df = pd.read_csv(resolved_path)
    else:
        # Packaged default
        df = _read_packaged_metric_config()

    required_cols = [
        "MetricName",
        "DisplayName",
        "Direction",
        "HasTarget",
        "TargetValue",
        "Unit",
        "DecimalPlaces",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            "Metric config CSV is missing required columns: "
            + ", ".join(missing)
            + f"\nFound columns: {list(df.columns)}"
        )

    configs: Dict[str, MetricConfig] = {}

    for _, row in df.iterrows():
        metric_name = str(row["MetricName"]).strip()
        if not metric_name:
            # Skip completely empty metric rows
            continue

        display_name_raw = row.get("DisplayName", metric_name)
        display_name = str(display_name_raw).strip() or metric_name

        direction_raw = row.get("Direction", "")
        direction = str(direction_raw).strip().lower()
        if direction not in {"higher", "lower", "neutral"}:
            raise ValueError(
                f"Invalid Direction {direction_raw!r} for metric {metric_name!r}. "
                "Expected one of: 'higher', 'lower', 'neutral'."
            )

        has_target = _normalise_bool(row.get("HasTarget", "no"))
        target_value = _safe_float(row.get("TargetValue", None), metric_name, "TargetValue")

        # If HasTarget is False, we ignore any TargetValue and force None
        if not has_target:
            target_value = None

        unit_raw = row.get("Unit", "other")
        unit = str(unit_raw).strip().lower() or "other"

        decimal_places = _safe_int(row.get("DecimalPlaces", None), metric_name, "DecimalPlaces")

        config = MetricConfig(
            metric_name=metric_name,
            display_name=display_name,
            direction=direction,
            has_target=has_target,
            target_value=target_value,
            unit=unit,
            decimal_places=decimal_places,
        )

        # Last one wins if there are duplicate MetricName rows
        configs[metric_name] = config

    return configs


def get_metric_config(
    metric_name: str,
    configs: Dict[str, MetricConfig],
    default: Optional[MetricConfig] = None,
) -> Optional[MetricConfig]:
    """
    Convenience helper to fetch a MetricConfig from a dict.

    If the metric is not found:
      - return 'default' if provided,
      - otherwise return None.
    """
    return configs.get(metric_name, default)


# -------------------------------------------------------------------
# Public API – variation / assurance helpers (logic only, no plotting)
# -------------------------------------------------------------------


def classify_variation(
    is_special_cause: bool,
    is_high: bool,
    metric_cfg: MetricConfig,
    treat_neutral_as_neither: bool = True,
) -> Tuple[VariationStatus, str]:
    """
    Decide the variation status + icon filename for the *latest* point
    given:
      - whether there is special cause at all (MDC rules),
      - whether the latest point is 'high' or 'low' relative to the mean,
      - the metric's direction of improvement.

    This does NOT run the rules itself – it just interprets the outcome
    in the context of metric direction.
    """
    # Common cause – always the same
    if not is_special_cause:
        status = VariationStatus.COMMON_CAUSE
        return status, VARIATION_ICON_FILES[status]

    direction = metric_cfg.direction

    # Neutral metrics – we don't say improvement/concern, just "special cause"
    if direction == "neutral" and treat_neutral_as_neither:
        if is_high:
            status = VariationStatus.NEITHER_HIGH
        else:
            status = VariationStatus.NEITHER_LOW
        return status, VARIATION_ICON_FILES[status]

    if direction == "higher":
        if is_high:
            status = VariationStatus.IMPROVEMENT_HIGH
        else:
            status = VariationStatus.CONCERN_LOW
    elif direction == "lower":
        if is_high:
            status = VariationStatus.CONCERN_HIGH
        else:
            status = VariationStatus.IMPROVEMENT_LOW
    else:
        if is_high:
            status = VariationStatus.NEITHER_HIGH
        else:
            status = VariationStatus.NEITHER_LOW

    return status, VARIATION_ICON_FILES[status]


def classify_assurance(
    latest_value: Optional[float],
    metric_cfg: MetricConfig,
    tolerance: float = 1e-12,
) -> Tuple[AssuranceStatus, str]:
    """
    Decide the assurance status + icon filename for the metric
    relative to its target, based on the latest value.
    """
    if not metric_cfg.has_target or metric_cfg.target_value is None:
        status = AssuranceStatus.NO_TARGET
        return status, ASSURANCE_ICON_FILES[status]

    if latest_value is None or pd.isna(latest_value):
        status = AssuranceStatus.HIT_OR_MISS
        return status, ASSURANCE_ICON_FILES[status]

    value = float(latest_value)
    target = float(metric_cfg.target_value)

    direction = metric_cfg.direction

    diff = value - target

    if abs(diff) <= tolerance:
        status = AssuranceStatus.HIT_OR_MISS
        return status, ASSURANCE_ICON_FILES[status]

    if direction == "higher":
        status = AssuranceStatus.PASSING if value > target else AssuranceStatus.FAILING
    elif direction == "lower":
        status = AssuranceStatus.PASSING if value < target else AssuranceStatus.FAILING
    else:
        status = AssuranceStatus.HIT_OR_MISS

    return status, ASSURANCE_ICON_FILES[status]


def classify_assurance_from_key(
    assurance_key: Optional[str],
    metric_cfg: Optional[MetricConfig] = None,
) -> Tuple[AssuranceStatus, str]:
    """
    Map an MDC-style assurance_key from the SPC layer to an
    AssuranceStatus + icon filename.
    """
    key = (assurance_key or "").strip().lower()

    if key == "pass":
        status = AssuranceStatus.PASSING
    elif key == "fail":
        status = AssuranceStatus.FAILING
    elif key == "no_strong_assurance":
        status = AssuranceStatus.HIT_OR_MISS
    elif key in {"", "no_data"}:
        status = AssuranceStatus.NO_TARGET
    else:
        status = AssuranceStatus.NO_TARGET

    return status, ASSURANCE_ICON_FILES[status]


__all__ = [
    "MetricConfig",
    "VariationStatus",
    "AssuranceStatus",
    "VARIATION_ICON_FILES",
    "ASSURANCE_ICON_FILES",
    "DEFAULT_CONFIG_PATH",
    "load_metric_config",
    "get_metric_config",
    "classify_variation",
    "classify_assurance",
    "classify_assurance_from_key",
]