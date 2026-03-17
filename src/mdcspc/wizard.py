from __future__ import annotations
from pathlib import Path
from typing import List, Optional
import pandas as pd
from datetime import datetime

METRIC_CONFIG_COLUMNS: List[str] = [
    "MetricName",
    "DisplayName",
    "Direction",
    "HasTarget",
    "TargetValue",
    "Unit",
    "DecimalPlaces",
    "ChartMode",
    "UseBaseline",
    "BaselinePoints",
]

TARGET_CONFIG_COLUMNS: List[str] = [
    "OrgCode",
    "MetricName",
    "EffectiveFrom",
    "TargetValue",
]

VALID_DIRECTIONS = {"higher", "lower", "neutral"}


def _load_or_init_metric_config(path: Path) -> pd.DataFrame:
    if path.exists():
        df = pd.read_csv(path)
        for col in METRIC_CONFIG_COLUMNS:
            if col not in df.columns:
                df[col] = pd.NA
        return df[METRIC_CONFIG_COLUMNS].copy()
    return pd.DataFrame(columns=METRIC_CONFIG_COLUMNS)


def _load_or_init_target_config(path: Path) -> pd.DataFrame:
    if path.exists():
        df = pd.read_csv(path)
        for col in TARGET_CONFIG_COLUMNS:
            if col not in df.columns:
                df[col] = pd.NA
        return df[TARGET_CONFIG_COLUMNS].copy()
    return pd.DataFrame(columns=TARGET_CONFIG_COLUMNS)


def _coerce_decimal_places(raw: object, default: int = 1) -> int:
    try:
        return int(raw)
    except Exception:
        return default


def _normalise_target_value(raw: object) -> Optional[float]:
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return float(raw)
    except Exception:
        return None


def _prompt_or_default(prompt_text: str, default: str, interactive: bool) -> str:
    if not interactive:
        return default
    entered = input(f"{prompt_text} [{default}]: ").strip()
    return entered or default


def run_wizard(input_csv: Path, out_config: Path, defaults: bool = False) -> int:
    interactive = not defaults

    input_csv = Path(input_csv)
    out_config = Path(out_config)

    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    input_df = pd.read_csv(input_csv)
    if "MetricName" not in input_df.columns:
        raise ValueError("Wizard input CSV must contain a 'MetricName' column.")

    metrics = [str(m).strip() for m in input_df["MetricName"].dropna().unique() if str(m).strip()]
    if not metrics:
        raise ValueError("Wizard input CSV contains no usable MetricName values.")

    out_config.mkdir(parents=True, exist_ok=True)

    metric_config_path = out_config / "metric_config.csv"
    target_config_path = out_config / "spc_target_config.csv"
    phase_config_path = out_config / "spc_phase_config.csv"

    metric_df = _load_or_init_metric_config(metric_config_path)
    target_df = _load_or_init_target_config(target_config_path)

    phase_columns = [
        "OrgCode",
        "MetricName",
        "PhaseStart",
        "Annotation",
        "ShowOnChart",
        "AnnotationPosition",
    ]

    if phase_config_path.exists():
        phase_df = pd.read_csv(phase_config_path)
        for col in phase_columns:
            if col not in phase_df.columns:
                phase_df[col] = pd.NA
        phase_df = phase_df[phase_columns].copy()
    else:
        phase_df = pd.DataFrame(columns=phase_columns)

    existing_metrics = set(metric_df["MetricName"].astype(str).str.strip()) if not metric_df.empty else set()
    added_count = 0
    skipped_count = 0

    for metric in metrics:
        if metric in existing_metrics:
            skipped_count += 1
            print(f"[INFO] Metric already present in metric_config.csv, leaving as-is: {metric}")
            continue

        print(f"Configuring metric: {metric}")

        direction = _prompt_or_default(
            f"Direction for {metric} (higher/lower/neutral)",
            default="higher",
            interactive=interactive,
        ).strip().lower()
        if direction not in VALID_DIRECTIONS:
            direction = "higher"

        unit = _prompt_or_default(
            f"Unit for {metric} (percent/rate/count/time/other)",
            default="count",
            interactive=interactive,
        ).strip().lower() or "count"

        decimal_places_raw = _prompt_or_default(
            f"Decimal places for {metric}",
            default="1",
            interactive=interactive,
        )
        decimal_places = _coerce_decimal_places(decimal_places_raw, default=1)

        has_target_raw = _prompt_or_default(
            f"Does {metric} have a static target? (yes/no)",
            default="no",
            interactive=interactive,
        ).strip().lower()
        has_target = has_target_raw in {"y", "yes", "true", "1"}

        target_value: Optional[float] = None
        if has_target:
            target_value_raw = _prompt_or_default(
                f"Static target value for {metric}",
                default="",
                interactive=interactive,
            )
            target_value = _normalise_target_value(target_value_raw)
            if target_value is None:
                has_target = False

        # Chart type prompt
        chart_mode = _prompt_or_default(
            f"Chart type for {metric} (x_only/xmr)",
            default="x_only",
            interactive=interactive,
        ).strip().lower()
        if chart_mode not in {"x_only", "xmr"}:
            chart_mode = "x_only"

        # Baseline yes/no prompt
        use_baseline_raw = _prompt_or_default(
            f"Use baseline for {metric}? (y/N) [No] - advised only for improvement projects",
            default="no",
            interactive=interactive,
        ).strip().lower()
        use_baseline = use_baseline_raw in {"y", "yes"}

        baseline_points = 12
        if use_baseline:
            while True:
                baseline_points_raw = _prompt_or_default(
                    f"Number of points to use for baseline for {metric} [12]",
                    default="12",
                    interactive=interactive,
                )
                try:
                    baseline_points = int(baseline_points_raw)
                except Exception:
                    baseline_points = 12

                if not 6 <= baseline_points <= 24:
                    print(f"Warning: You entered {baseline_points} points. It is strongly recommended that baseline points are between 6 and 24.")
                    change = _prompt_or_default(
                        "Do you want to change it? (y/N)",
                        default="n",
                        interactive=interactive,
                    ).strip().lower()
                    if change not in {"y", "yes"}:
                        break
                else:
                    break

        new_row = {
            "MetricName": metric,
            "DisplayName": metric,
            "Direction": direction,
            "HasTarget": "yes" if has_target else "no",
            "TargetValue": target_value,
            "Unit": unit,
            "DecimalPlaces": decimal_places,
            "ChartMode": chart_mode,
            "UseBaseline": use_baseline,
            "BaselinePoints": baseline_points,
        }

        new_row_df = pd.DataFrame([new_row])
        if not new_row_df.dropna(how="all").empty:
            metric_df = pd.concat([metric_df, new_row_df], ignore_index=True)
        existing_metrics.add(metric)
        added_count += 1

    metric_df = metric_df[METRIC_CONFIG_COLUMNS].copy()
    target_df = target_df[TARGET_CONFIG_COLUMNS].copy()

    metric_df.to_csv(metric_config_path, index=False)
    target_df.to_csv(target_config_path, index=False)
    phase_df.to_csv(phase_config_path, index=False)

    print(
        f"Configuration for {len(metrics)} metrics saved to {out_config}. Added {added_count}, skipped {skipped_count} existing. Created/updated metric_config.csv, spc_target_config.csv, and spc_phase_config.csv."
    )
    return 0

def recalc_wizard(config_dir: Path, metric: str | None = None, org: str | None = None):
    """
    CLI wizard for adding a phase recalculation point to a metric.

    Prompts for:
    - Metric / Org if not provided
    - Recalculation start date
    - Annotation (required)
    - Show on chart (default No)
    - Annotation vertical placement (above UCL / below LCL)
    """

    # TODO: replace with actual metric/org selection if None
    metric_name = metric or input("Enter metric name: ").strip()
    org_code = org or input("Enter OrgCode: ").strip()

    # Step 1: Phase start date
    while True:
        date_str = input("Enter recalculation start date (YYYY-MM-DD): ").strip()
        try:
            phase_start = pd.to_datetime(date_str, format="%Y-%m-%d", errors="raise").normalize()
            break
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")

    # Step 2: Annotation
    while True:
        annotation = input("Enter a short annotation/comment (required): ").strip()
        if annotation:
            break
        print("Annotation cannot be empty.")

    # Step 3: Show annotation on graph
    show_on_chart_input = input("Show annotation on chart? (y/N): ").strip().lower()
    show_on_chart = True if show_on_chart_input == "y" else False

    # Step 4: Annotation vertical placement (only if shown on chart)
    if show_on_chart:
        while True:
            position_input = input("Should the annotation appear above the UCL or below the LCL? [U/L] (default L): ").strip().upper()
            if position_input in ("U", "L", ""):
                annotation_position = position_input if position_input else "L"
                break
            print("Invalid input. Enter 'U' for above UCL or 'L' for below LCL.")

    else:
        annotation_position = "L"  # default if not shown

    # Prepare canonical phase config path
    phase_cfg_path = config_dir / "spc_phase_config.csv"
    if phase_cfg_path.exists():
        df_phase = pd.read_csv(phase_cfg_path)
    else:
        df_phase = pd.DataFrame(columns=[
            "OrgCode",
            "MetricName",
            "PhaseStart",
            "Annotation",
            "ShowOnChart",
            "AnnotationPosition"
        ])

    # Append new phase row
    new_row = {
        "OrgCode": org_code,
        "MetricName": metric_name,
        "PhaseStart": phase_start.date(),
        "Annotation": annotation,
        "ShowOnChart": show_on_chart,
        "AnnotationPosition": annotation_position
    }

    df_phase = pd.concat([df_phase, pd.DataFrame([new_row])], ignore_index=True)

    # Save back to canonical CSV
    df_phase.to_csv(phase_cfg_path, index=False)

    print(f"\nPhase recalculation saved to {phase_cfg_path}")
    print(f"OrgCode: {org_code}, MetricName: {metric_name}, PhaseStart: {phase_start.date()}")
    print(f"Annotation: {annotation}, ShowOnChart: {show_on_chart}, Position: {annotation_position}")