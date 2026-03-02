import os
import sys

# Ensure project root is on sys.path so we can import mdcspc
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from mdcspc.metric_config import (  # noqa: E402
    load_metric_config,
    classify_variation,
    classify_assurance,
    VariationStatus,
    AssuranceStatus,
)


def demo_for_metric(metric_name: str, latest_value: float, is_special_cause: bool, is_high: bool):
    """
    Run a little demo for one metric:
      - variation classification (with icon)
      - assurance classification (with icon)
    """
    configs = load_metric_config()
    cfg = configs.get(metric_name)

    if cfg is None:
        print(f"[WARN] No config found for metric {metric_name!r}")
        return

    print(f"\n=== Demo for metric: {cfg.metric_name} ({cfg.display_name}) ===")
    print(f"Direction     : {cfg.direction}")
    print(f"Has target    : {cfg.has_target}")
    print(f"Target value  : {cfg.target_value}")
    print(f"Latest value  : {latest_value}")
    print(f"Special cause : {is_special_cause}")
    print(f"Is high side  : {is_high}")

    # Variation
    var_status, var_icon = classify_variation(
        is_special_cause=is_special_cause,
        is_high=is_high,
        metric_cfg=cfg,
    )

    # Assurance
    ass_status, ass_icon = classify_assurance(
        latest_value=latest_value,
        metric_cfg=cfg,
    )

    print("\nVariation result:")
    print(f"  Status      : {var_status.value}")
    print(f"  Icon file   : {var_icon}")

    print("\nAssurance result:")
    print(f"  Status      : {ass_status.value}")
    print(f"  Icon file   : {ass_icon}")
    print("-" * 70)


def main() -> None:
    """
    Simple demo to sanity-check variation/assurance logic against the
    metric configuration file.

    It runs a few scenarios for each of the example metrics in
    config/metric_config.csv so you can eyeball whether the logic
    matches how you think about improvement/concern/passing/failing.
    """
    configs = load_metric_config()
    if not configs:
        print("[WARN] No metric configs found.")
        return

    print("[INFO] Loaded metric configs:")
    for name, cfg in sorted(configs.items()):
        print(f"  - {name} (direction={cfg.direction}, has_target={cfg.has_target}, target={cfg.target_value})")

    # Pick some of the example metrics from your starter CSV.
    # Adjust these metric names & values to match your real config if needed.

    # 1) A&E 4-hour performance: higher is better, has target (e.g. 95)
    if "AE_4hr_Performance" in configs:
        # Below target, high special cause (bad)
        demo_for_metric(
            metric_name="AE_4hr_Performance",
            latest_value=90.0,
            is_special_cause=True,
            is_high=False,  # lower side
        )
        # Above target, high special cause (good)
        demo_for_metric(
            metric_name="AE_4hr_Performance",
            latest_value=97.0,
            is_special_cause=True,
            is_high=True,  # higher side
        )

    # 2) RTT 18-week performance: higher is better, has target
    if "RTT_18w_Performance" in configs:
        demo_for_metric(
            metric_name="RTT_18w_Performance",
            latest_value=93.0,
            is_special_cause=True,
            is_high=True,
        )

    # 3) ED attendances: neutral, no target
    if "ED_Attendances" in configs:
        # Special cause on high side
        demo_for_metric(
            metric_name="ED_Attendances",
            latest_value=1200,
            is_special_cause=True,
            is_high=True,
        )
        # Common cause case
        demo_for_metric(
            metric_name="ED_Attendances",
            latest_value=950,
            is_special_cause=False,
            is_high=True,
        )

    # 4) Complaints rate: lower is better, no target
    if "Complaints_Rate" in configs:
        # High special cause (bad)
        demo_for_metric(
            metric_name="Complaints_Rate",
            latest_value=7.5,
            is_special_cause=True,
            is_high=True,
        )
        # Low special cause (good)
        demo_for_metric(
            metric_name="Complaints_Rate",
            latest_value=1.2,
            is_special_cause=True,
            is_high=False,
        )


if __name__ == "__main__":
    main()
