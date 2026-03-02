import os
import sys
from typing import List

import pandas as pd

# -------------------------------------------------------------------
# Ensure project root (MDCpip) is on sys.path if we ever need it.
# Not strictly required for this helper, but keeps things consistent.
# -------------------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def _detect_metric_column(df: pd.DataFrame) -> str:
    """
    Try to detect the metric identifier column.

    For now we expect 'MetricName' to exist. If not, we raise a clear error.
    """
    if "MetricName" in df.columns:
        return "MetricName"

    raise ValueError(
        "Could not find a 'MetricName' column in the input CSV. "
        "This helper expects a column called 'MetricName' to identify metrics."
    )


def build_metric_config_from_csv(input_path: str, working_dir: str) -> None:
    """
    Build or update working/spc_metric_config.csv based on the metrics
    present in the given input CSV.

    Behaviour:
    - Load the CSV.
    - Detect the MetricName column.
    - Get unique MetricName values.
    - If spc_metric_config.csv does not exist:
        * Create it with columns: MetricName, Direction
        * Direction is left blank for all metrics.
    - If it does exist:
        * Load it.
        * Add any new metrics that are not already present, with blank Direction.
        * Keep existing Direction values unchanged.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    print(f"[INFO] Loading input CSV: {input_path}")
    df = pd.read_csv(input_path)

    metric_col = _detect_metric_column(df)
    metrics: List[str] = (
        df[metric_col]
        .astype(str)
        .str.strip()
        .dropna()
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    if not metrics:
        print("[WARN] No MetricName values found in the input CSV.")
        return

    config_path = os.path.join(working_dir, "spc_metric_config.csv")
    os.makedirs(working_dir, exist_ok=True)

    if os.path.exists(config_path):
        print(f"[INFO] Existing metric config found: {config_path}")
        existing = pd.read_csv(config_path)

        if "MetricName" not in existing.columns:
            raise ValueError(
                "Existing spc_metric_config.csv does not contain a 'MetricName' column."
            )

        if "Direction" not in existing.columns:
            # Add Direction column if missing
            existing["Direction"] = ""

        # Normalise MetricName for matching
        existing["MetricName"] = (
            existing["MetricName"].astype(str).str.strip()
        )

        existing_metrics = set(existing["MetricName"].tolist())
        new_metrics = [m for m in metrics if m not in existing_metrics]

        if new_metrics:
            print(
                f"[INFO] Adding {len(new_metrics)} new metric(s) to spc_metric_config.csv:"
            )
            for m in new_metrics:
                print(f"       - {m}")

            new_rows = pd.DataFrame(
                {"MetricName": new_metrics, "Direction": [""] * len(new_metrics)}
            )

            updated = pd.concat([existing, new_rows], ignore_index=True)
        else:
            print("[INFO] No new metrics to add; spc_metric_config.csv already up to date.")
            updated = existing

        # Sort by MetricName for neatness
        updated = updated.sort_values("MetricName").reset_index(drop=True)
        updated.to_csv(config_path, index=False)
        print(f"[INFO] Updated metric config saved to: {config_path}")

    else:
        print(f"[INFO] No existing metric config found. Creating new file at: {config_path}")
        cfg = pd.DataFrame(
            {
                "MetricName": metrics,
                "Direction": ["" for _ in metrics],  # to be filled: higher_is_better / lower_is_better / neutral
            }
        )
        cfg.to_csv(config_path, index=False)
        print(f"[INFO] New metric config created with {len(metrics)} metric(s).")


def main():
    # Decide which CSV to inspect
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
        if not os.path.isabs(input_path):
            input_path = os.path.join(PROJECT_ROOT, input_path)
    else:
        # Default to the same example CSV as export_spc_from_csv.py
        input_path = os.path.join(PROJECT_ROOT, "working", "ae4hr_multi_org_example.csv")

    working_dir = os.path.join(PROJECT_ROOT, "working")

    build_metric_config_from_csv(input_path=input_path, working_dir=working_dir)


if __name__ == "__main__":
    main()
