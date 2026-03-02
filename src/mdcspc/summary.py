from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd

from .xmr import MultiXmrResult
from .metric_config import (
    load_metric_config,
    get_metric_config,
    classify_variation,
    classify_assurance_from_key,
)


@dataclass
class SummaryConfig:
    """
    Simple configuration holder for XmR summaries.

    This exists mainly to keep older code paths working and to provide
    a place for future options (e.g. toggling specific columns).
    """

    lookback_points: int = 12
    direction: str = "higher_is_better"


def _get_metric_name_from_key_tuple(
    key_tuple: Tuple,
    group_cols: List[str],
    metric_name_idx: Optional[int],
) -> Optional[str]:
    """
    Extract MetricName from the group key tuple if possible.
    """
    if metric_name_idx is None:
        return None

    if not group_cols or metric_name_idx >= len(group_cols):
        return None

    try:
        return str(key_tuple[metric_name_idx])
    except Exception:
        return None


def _direction_from_metric_cfg(
    metric_cfg: Any,
    default: str = "higher_is_better",
) -> str:
    """
    Infer the XmR direction argument from a MetricConfig row.

    metric_cfg.direction is expected to be one of:
      - "higher"
      - "lower"
      - "neutral"

    We map these to analyse_xmr_by_group's direction strings:
      - "higher_is_better"
      - "lower_is_better"
      - "neutral"
    """
    if metric_cfg is None:
        return default

    raw = getattr(metric_cfg, "direction", None) or getattr(metric_cfg, "Direction", None)
    if raw is None:
        return default

    raw = str(raw).strip().lower()
    if raw == "higher":
        return "higher_is_better"
    if raw == "lower":
        return "lower_is_better"
    if raw == "neutral":
        return "neutral"

    return default


def _get_decimal_places(metric_cfg: Any) -> Optional[int]:
    """
    Extract DecimalPlaces from a MetricConfig row, if present.
    """
    if metric_cfg is None:
        return None

    dp = getattr(metric_cfg, "decimal_places", None)
    if dp is None:
        dp = getattr(metric_cfg, "DecimalPlaces", None)

    if dp is None:
        return None

    try:
        return int(dp)
    except Exception:
        return None


def _get_default_target_from_metric(metric_cfg: Any) -> Optional[float]:
    """
    Extract the default (static) target value from a MetricConfig row, if present.
    """
    if metric_cfg is None:
        return None

    tv = getattr(metric_cfg, "target_value", None)
    if tv is None:
        tv = getattr(metric_cfg, "TargetValue", None)

    if tv is None or tv == "":
        return None

    try:
        return float(tv)
    except Exception:
        return None


def _apply_decimal_places(value: Any, decimal_places: Optional[int]) -> Any:
    """
    Apply a DecimalPlaces rule to a numeric value.

    If decimal_places is None, return value unchanged.
    If value is NaN or non-numeric, return as-is.
    """
    if decimal_places is None:
        return value

    if value is None or pd.isna(value):
        return value

    try:
        return round(float(value), decimal_places)
    except Exception:
        return value


def _classify_variation_for_last_point(
    df: pd.DataFrame,
    value_col: str,
    direction: str,
) -> Dict[str, Any]:
    """
    Inspect the last non-null point in the series and classify variation.

    This uses SPC-layer outputs (special_cause, special_cause_label, mean)
    to decide:

      - whether the last point is special cause,
      - which rule triggered (trend/shift/2-of-3/astronomical),
      - whether the point is "high" / "low" / "neutral" relative to the mean,
      - whether the special cause is improvement vs concern vs neutral.

    It returns a dictionary with keys including:

      - last_date
      - last_value
      - last_special_cause (True/False)
      - last_special_cause_rule (e.g. "trend")
      - variation_key: one of {"common_cause", "improvement", "concern", "neutral"}
      - variation_colour: e.g. "grey", "blue", "orange", "purple"
      - variation_side: "high" / "low" / "neutral" / "none"
    """
    non_null = df[df[value_col].notna()].copy()
    if non_null.empty:
        return {
            "last_date": pd.NaT,
            "last_value": float("nan"),
            "last_special_cause": False,
            "last_special_cause_rule": "",
            "variation_key": "common_cause",
            "variation_colour": "grey",
            "variation_side": "none",
        }

    last_row = non_null.iloc[-1]
    last_date = last_row.name
    last_value = last_row[value_col]

    sc = bool(last_row.get("special_cause", False))
    sc_label = str(last_row.get("special_cause_label", "") or "")

    mean = last_row.get("mean", float("nan"))

    if pd.isna(last_value) or pd.isna(mean):
        return {
            "last_date": last_date,
            "last_value": last_value,
            "last_special_cause": sc,
            "last_special_cause_rule": sc_label,
            "variation_key": "common_cause",
            "variation_colour": "grey",
            "variation_side": "none",
        }

    if sc:
        if last_value > mean:
            side = "high"
        elif last_value < mean:
            side = "low"
        else:
            side = "neutral"

        dir_norm = (direction or "").lower()
        if dir_norm == "higher_is_better":
            if side == "high":
                v_key = "improvement"
                colour = "blue"
            elif side == "low":
                v_key = "concern"
                colour = "orange"
            else:
                v_key = "neutral"
                colour = "purple"
        elif dir_norm == "lower_is_better":
            if side == "low":
                v_key = "improvement"
                colour = "blue"
            elif side == "high":
                v_key = "concern"
                colour = "orange"
            else:
                v_key = "neutral"
                colour = "purple"
        else:
            v_key = "neutral"
            colour = "purple"

        return {
            "last_date": last_date,
            "last_value": last_value,
            "last_special_cause": True,
            "last_special_cause_rule": sc_label,
            "variation_key": v_key,
            "variation_colour": colour,
            "variation_side": side,
        }

    return {
        "last_date": last_date,
        "last_value": last_value,
        "last_special_cause": False,
        "last_special_cause_rule": "",
        "variation_key": "common_cause",
        "variation_colour": "grey",
        "variation_side": "none",
    }


def _classify_assurance_for_last_point(
    df: pd.DataFrame,
    value_col: str,
    direction: str,
    target_series: Optional[pd.Series],
) -> Dict[str, Any]:
    """
    Assurance classification for the last point, using MDC-style logic:

      - Assurance is based on where the target lies relative to process
        limits (LCL/UCL) in the latest phase, not just the last dot.

      - If there's no valid target or direction is neutral, we return
        "no strong assurance" / "no target" so that the icon layer can
        choose the empty icon.

    Returns a dictionary including:

      - assurance_key: "pass" / "fail" / "no_strong_assurance" / "" / "no_data"
      - assurance_colour: "blue" / "orange" / "grey" / "" (for convenience)
      - target_value: the numeric target used for the classification
    """
    non_null = df[df[value_col].notna()].copy()
    if non_null.empty:
        return {
            "assurance_key": "no_data",
            "assurance_colour": "",
            "target_value": float("nan"),
        }

    dir_norm = (direction or "").lower()
    if dir_norm not in ("higher_is_better", "lower_is_better"):
        return {
            "assurance_key": "",
            "assurance_colour": "",
            "target_value": float("nan"),
        }

    last_row = non_null.iloc[-1]
    idx = last_row.name

    if target_series is None:
        return {
            "assurance_key": "",
            "assurance_colour": "",
            "target_value": float("nan"),
        }

    try:
        target_value = float(target_series.loc[idx])
    except Exception:
        target_value = float("nan")

    if pd.isna(target_value):
        return {
            "assurance_key": "",
            "assurance_colour": "",
            "target_value": float("nan"),
        }

    lcl = last_row.get("lcl", float("nan"))
    ucl = last_row.get("ucl", float("nan"))
    if pd.isna(lcl) or pd.isna(ucl):
        return {
            "assurance_key": "",
            "assurance_colour": "",
            "target_value": target_value,
        }

    key: str
    colour: str

    if dir_norm == "higher_is_better":
        if target_value <= lcl:
            key = "pass"
            colour = "blue"
        elif target_value >= ucl:
            key = "fail"
            colour = "orange"
        else:
            key = "no_strong_assurance"
            colour = "grey"
    else:
        if target_value >= ucl:
            key = "pass"
            colour = "blue"
        elif target_value <= lcl:
            key = "fail"
            colour = "orange"
        else:
            key = "no_strong_assurance"
            colour = "grey"

    return {
        "assurance_key": key,
        "assurance_colour": colour,
        "target_value": target_value,
    }


VARIATION_ICON_COMMON = "VariationIconCommonCause.png"
VARIATION_ICON_IMPROVEMENT_HIGH = "VariationIconImprovementHigh.png"
VARIATION_ICON_IMPROVEMENT_LOW = "VariationIconImprovementLow.png"
VARIATION_ICON_CONCERN_HIGH = "VariationIconConcernHigh.png"
VARIATION_ICON_CONCERN_LOW = "VariationIconConcernLow.png"
VARIATION_ICON_NEUTRAL_HIGH = "VariationIconNeitherHigh.png"
VARIATION_ICON_NEUTRAL_LOW = "VariationIconNeitherLow.png"


def _map_variation_icon_legacy(variation_key: str, variation_side: str) -> str:
    """
    Legacy mapping from variation classification + side to a specific icon filename.

    This is now a fallback only. The primary icon choice comes from
    metric_config.classify_variation where possible.
    """
    if variation_key == "common_cause":
        return VARIATION_ICON_COMMON

    if variation_key == "improvement":
        if variation_side == "high":
            return VARIATION_ICON_IMPROVEMENT_HIGH
        if variation_side == "low":
            return VARIATION_ICON_IMPROVEMENT_LOW
        return VARIATION_ICON_IMPROVEMENT_HIGH

    if variation_key == "concern":
        if variation_side == "high":
            return VARIATION_ICON_CONCERN_HIGH
        if variation_side == "low":
            return VARIATION_ICON_CONCERN_LOW
        return VARIATION_ICON_CONCERN_HIGH

    if variation_key == "neutral":
        if variation_side == "high":
            return VARIATION_ICON_NEUTRAL_HIGH
        if variation_side == "low":
            return VARIATION_ICON_NEUTRAL_LOW
        return VARIATION_ICON_NEUTRAL_HIGH

    return VARIATION_ICON_COMMON


def summarise_xmr_by_group(
    multi: MultiXmrResult,
    direction: str = "higher_is_better",
    lookback_points: int = 12,
    directions_by_group: Optional[Dict[Tuple, str]] = None,
    targets_by_group: Optional[Dict[Tuple, pd.Series]] = None,
) -> pd.DataFrame:
    """
    Build a per-series summary table from a MultiXmrResult, with MDC-style
    variation and assurance classifications.

    Returns a DataFrame where each row corresponds to one series (group),
    including:

      - group columns (e.g. OrgCode, MetricName)
      - n_points
      - last_date, last_value
      - mean_latest, lcl_latest, ucl_latest (latest phase limits)
      - direction (effective direction for this series)
      - target_value (effective target at last point)
      - variation_key, variation_colour, variation_side
      - variation_icon
      - variation_status  (central VariationStatus / string)
      - last_special_cause, last_special_cause_rule
      - assurance_key, assurance_colour
      - assurance_icon
      - assurance_status  (central AssuranceStatus / string)
      - any_special_cause_in_lookback
    """
    if multi.data.empty or not multi.by_group:
        return pd.DataFrame()

    group_cols = multi.config.group_cols or []
    value_col = multi.config.value_col

    try:
        metric_configs = load_metric_config()
        if metric_configs is not None:
            print(f"[INFO] metric_config: loaded {len(metric_configs)} metric config(s).")
    except Exception as e:
        print(
            "[INFO] metric_config: failed to load central metric config in summary; "
            f"using defaults only. Error: {e}"
        )
        metric_configs = None

    metric_name_idx: Optional[int] = None
    if "MetricName" in group_cols:
        metric_name_idx = group_cols.index("MetricName")

    rows: List[Dict[str, object]] = []

    for key_tuple, xmr_result in multi.by_group.items():
        # xmr_result is an XmrResult; grab its underlying DataFrame
        df = xmr_result.data

        if isinstance(key_tuple, tuple):
            key_for_directions = key_tuple
        else:
            key_for_directions = (key_tuple,)

        metric_name_for_group: Optional[str] = None
        if metric_configs:
            metric_name_for_group = _get_metric_name_from_key_tuple(
                key_for_directions,
                group_cols,
                metric_name_idx,
            )

        metric_cfg = None
        decimal_places = None
        default_target_from_metric = None
        if metric_configs:
            if metric_name_for_group:
                try:
                    metric_cfg = get_metric_config(metric_name_for_group, metric_configs)
                except KeyError:
                    metric_cfg = None

        decimal_places = _get_decimal_places(metric_cfg)
        default_target_from_metric = _get_default_target_from_metric(metric_cfg)

        dir_for_group = direction
        if metric_cfg is not None:
            dir_for_group = _direction_from_metric_cfg(metric_cfg, dir_for_group)
        elif directions_by_group is not None and key_tuple in directions_by_group:
            dir_for_group = directions_by_group[key_tuple]

        target_series = None
        if targets_by_group is not None and key_tuple in targets_by_group:
            target_series = targets_by_group[key_tuple]

        n_points = int(df[value_col].notna().sum())

        if n_points == 0:
            row: Dict[str, object] = {}

            last_row = df.iloc[-1] if not df.empty else None
            if last_row is not None and group_cols:
                for gc in group_cols:
                    row[gc] = last_row.get(gc, None)

            row.update(
                {
                    "n_points": 0,
                    "last_date": pd.NaT,
                    "last_value": float("nan"),
                    "mean_latest": float("nan"),
                    "lcl_latest": float("nan"),
                    "ucl_latest": float("nan"),
                    "direction": dir_for_group,
                    "target_value": (
                        _apply_decimal_places(default_target_from_metric, decimal_places)
                        if default_target_from_metric is not None
                        else float("nan")
                    ),
                    "variation_key": "common_cause",
                    "variation_colour": "grey",
                    "variation_side": "none",
                    "variation_icon": VARIATION_ICON_COMMON,
                    "variation_status": None,
                    "last_special_cause": False,
                    "last_special_cause_rule": "",
                    "assurance_key": "no_data",
                    "assurance_colour": "",
                    "assurance_icon": "",
                    "assurance_status": None,
                    "any_special_cause_in_lookback": False,
                }
            )

            rows.append(row)
            continue

        non_null_idx = df[df[value_col].notna()].index
        last_idx = non_null_idx[-1]
        last_row = df.loc[last_idx]

        last_date = last_idx
        mean_latest = last_row.get("mean", float("nan"))
        lcl_latest = last_row.get("lcl", float("nan"))
        ucl_latest = last_row.get("ucl", float("nan"))

        if len(non_null_idx) <= lookback_points:
            idx_window = non_null_idx
        else:
            idx_window = non_null_idx[-lookback_points:]

        window_df = df.loc[idx_window]
        any_sc_in_window = bool(window_df.get("special_cause", False).astype(bool).any())

        var_info = _classify_variation_for_last_point(
            df=df,
            value_col=value_col,
            direction=dir_for_group,
        )

        target_series_for_assurance = target_series
        if (
            (target_series_for_assurance is None)
            or (not target_series_for_assurance.dropna().any())
        ) and default_target_from_metric is not None:
            target_series_for_assurance = pd.Series(
                [default_target_from_metric] * len(df.index),
                index=df.index,
            )

        ass_info = _classify_assurance_for_last_point(
            df=df,
            value_col=value_col,
            direction=dir_for_group,
            target_series=target_series_for_assurance,
        )

        target_value = ass_info["target_value"]
        if (pd.isna(target_value) or target_value is None) and default_target_from_metric is not None:
            target_value = default_target_from_metric

        last_value_fmt = _apply_decimal_places(var_info["last_value"], decimal_places)
        mean_latest_fmt = _apply_decimal_places(mean_latest, decimal_places)
        lcl_latest_fmt = _apply_decimal_places(lcl_latest, decimal_places)
        ucl_latest_fmt = _apply_decimal_places(ucl_latest, decimal_places)
        target_value_fmt = _apply_decimal_places(target_value, decimal_places)

        # Track centralised variation/assurance statuses for the summary output.
        variation_status = None  # type: ignore[assignment]
        assurance_status = None  # type: ignore[assignment]

        # Primary variation icon: use metric_config.classify_variation if possible
        variation_icon: str
        if metric_cfg is not None:
            try:
                is_special = bool(var_info["last_special_cause"])
                side = var_info["variation_side"]
                if side == "high":
                    is_high = True
                elif side == "low":
                    is_high = False
                else:
                    is_high = False

                status, variation_icon_from_cfg = classify_variation(
                    is_special_cause=is_special,
                    is_high=is_high,
                    metric_cfg=metric_cfg,
                )
                variation_icon = variation_icon_from_cfg
                try:
                    variation_status = getattr(status, "value", str(status))
                except Exception:
                    variation_status = str(status)
            except Exception:
                variation_icon = _map_variation_icon_legacy(
                    variation_key=var_info["variation_key"],
                    variation_side=var_info["variation_side"],
                )
        else:
            variation_icon = _map_variation_icon_legacy(
                variation_key=var_info["variation_key"],
                variation_side=var_info["variation_side"],
            )

        # Assurance icon: map the SPC assurance_key via central metric_config mapping.
        ass_status, assurance_icon = classify_assurance_from_key(
            assurance_key=ass_info["assurance_key"],
            metric_cfg=metric_cfg,
        )
        try:
            assurance_status = getattr(ass_status, "value", str(ass_status))
        except Exception:
            assurance_status = str(ass_status)

        row = {}

        if group_cols:
            for gc in group_cols:
                row[gc] = last_row.get(gc, None)

        row.update(
            {
                "n_points": n_points,
                "last_date": var_info["last_date"],
                "last_value": last_value_fmt,
                "mean_latest": mean_latest_fmt,
                "lcl_latest": lcl_latest_fmt,
                "ucl_latest": ucl_latest_fmt,
                "direction": dir_for_group,
                "target_value": target_value_fmt,
                "variation_key": var_info["variation_key"],
                "variation_colour": var_info["variation_colour"],
                "variation_side": var_info["variation_side"],
                "variation_icon": variation_icon,
                "variation_status": variation_status,
                "last_special_cause": var_info["last_special_cause"],
                "last_special_cause_rule": var_info["last_special_cause_rule"],
                "assurance_key": ass_info["assurance_key"],
                "assurance_colour": ass_info["assurance_colour"],
                "assurance_icon": assurance_icon,
                "assurance_status": assurance_status,
                "any_special_cause_in_lookback": any_sc_in_window,
            }
        )

        rows.append(row)

    summary = pd.DataFrame(rows)

    if group_cols:
        summary = summary.sort_values(group_cols)

    return summary
