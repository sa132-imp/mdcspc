import os
import sys

# Ensure project root is on sys.path so we can import mdcspc
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from mdcspc.metric_config import load_metric_config  # noqa: E402


def main() -> None:
    """
    Simple helper script to inspect the metric configuration.

    Usage (from project root, with venv activated):

        python scripts/inspect_metric_config.py
    """
    print("[INFO] Loading metric configuration...\n")

    try:
        configs = load_metric_config()
    except FileNotFoundError as e:
        print("[ERROR] Could not find metric_config.csv:")
        print(f"       {e}")
        return
    except Exception as e:  # pragma: no cover - debug helper
        print("[ERROR] Failed to load metric configuration:")
        print(f"       {type(e).__name__}: {e}")
        return

    if not configs:
        print("[WARN] No metrics found in the config file.")
        return

    print(f"[INFO] Loaded {len(configs)} metric configuration(s):\n")

    # Nice, readable dump
    for name, cfg in sorted(configs.items()):
        print(f"MetricName    : {cfg.metric_name}")
        print(f"  DisplayName : {cfg.display_name}")
        print(f"  Direction   : {cfg.direction}")
        print(f"  HasTarget   : {cfg.has_target}")
        print(f"  TargetValue : {cfg.target_value}")
        print(f"  Unit        : {cfg.unit}")
        print(f"  Decimals    : {cfg.decimal_places}")
        print("-" * 60)


if __name__ == "__main__":
    main()
