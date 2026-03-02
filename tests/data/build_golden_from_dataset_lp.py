from pathlib import Path
import pandas as pd

from mdcspc.exporter import export_spc_from_csv

# -------------------------------------------------------------------
# Mappings
# -------------------------------------------------------------------

VARIATION_MAP = {
    "01. CC": "Common cause variation",
    "02. SCHI": "Special cause improving (higher)",
    "03. SCLI": "Special cause improving (lower)",
    "04. SCHD": "Special cause deterioration (higher)",
    "05. SCLD": "Special cause deterioration (lower)",
    "06. SCHC": "Special cause change (higher)",
    "07. SCLC": "Special cause change (lower)",
}

# Map the full RuleBreak code to a canonical label for the rule
RULE_LABEL_MAP = {
    "00. None": "",
    "01. Trend": "trend",
    "02. Shift": "shift",
    "03. 2of3": "2of3",
    "04. Astro": "astronomical",
}

# Icon -> VariationCode mapping
ICON_TO_VARIATION_CODE = {
    "VariationIconCommonCause.png": "01. CC",
    "VariationIconImprovementHigh.png": "02. SCHI",
    "VariationIconImprovementLow.png": "03. SCLI",
    "VariationIconConcernHigh.png": "04. SCHD",
    "VariationIconConcernLow.png": "05. SCLD",
    "VariationIconNeitherHigh.png": "06. SCHC",
    "VariationIconNeitherLow.png": "07. SCLC",
}


def _short_rule_name(rule_break: str) -> str:
    """
    Turn '01. Trend' -> 'Trend', '03. 2of3' -> '2of3', etc.
    """
    if not isinstance(rule_break, str):
        return ""
    rule_break = rule_break.strip()
    if ". " in rule_break:
        return rule_break.split(". ", 1)[1].strip()
    return rule_break


def build_golden_from_dataset_lp():
    """
    Use tests/data/dataset_lp.csv (wide, easy-to-edit format) to build:

      - xmr_golden_input.csv
          Columns: Month, OrgCode, MetricName, Value
          (long format for export_spc_from_csv)

      - xmr_golden_expected_summary.csv
          Columns:
            OrgCode
            MetricName
            VariationCode
            VariationCategory
            Expected_Special_Cause
            Expected_Special_Cause_Label
            RuleBreakRaw

        where:
          * Expected_* fields come from RuleBreak (last point behaviour)
          * VariationCode/Category come from the exporter’s variation_icon,
            so the icon test checks the mapping logic, not our guesswork.
    """
    base_dir = Path(__file__).resolve().parent

    source_csv = base_dir / "dataset_lp.csv"
    if not source_csv.exists():
        raise FileNotFoundError(
            f"Cannot find {source_csv}. Put dataset_lp.csv next to this script "
            "or update source_csv in build_golden_from_dataset_lp.py."
        )

    print(f"[INFO] Loading source dataset: {source_csv}")
    df = pd.read_csv(source_csv)

    # Expect these meta columns, everything else is a date column
    meta_cols = ["Org", "RuleBreak", "Variation", "combination"]
    missing = [c for c in meta_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"Source CSV is missing required columns: {missing}. "
            f"Found columns: {list(df.columns)}"
        )

    date_cols = [c for c in df.columns if c not in meta_cols]
    if not date_cols:
        raise ValueError(
            "No date columns found in dataset_lp.csv. "
            "Expected columns like '01/01/2024', '01/02/2024', etc."
        )

    # ----------------------------------------------------------------
    # 1) Build xmr_golden_input.csv (long format)
    # ----------------------------------------------------------------
    long_rows = []

    for _, row in df.iterrows():
        org_code = str(row["Org"]).strip()
        metric_name = str(row["combination"]).strip()

        for month_col in date_cols:
            value = row[month_col]
            if pd.isna(value):
                continue

            try:
                val_float = float(value)
            except (TypeError, ValueError):
                # Skip any non-numeric oddities rather than explode
                continue

            long_rows.append(
                {
                    "Month": month_col,
                    "OrgCode": org_code,
                    "MetricName": metric_name,
                    "Value": val_float,
                }
            )

    if not long_rows:
        raise ValueError(
            "No usable data values found when building long-format input "
            "from dataset_lp.csv."
        )

    input_df = pd.DataFrame(long_rows)
    input_df.sort_values(["OrgCode", "MetricName", "Month"], inplace=True)

    xmr_input_path = base_dir / "xmr_golden_input.csv"
    input_df.to_csv(xmr_input_path, index=False)
    print(f"[INFO] Wrote long-format golden input to: {xmr_input_path}")

    # ----------------------------------------------------------------
    # 2) Run exporter to get actual variation_icon per series
    # ----------------------------------------------------------------
    working_dir = base_dir / "_build_tmp"
    working_dir.mkdir(exist_ok=True)

    print("[INFO] Running exporter on golden input to capture variation_icon...")
    summary, _multi = export_spc_from_csv(
        xmr_input_path,
        working_dir=working_dir,
        config_dir=Path("config"),
        icons_dir=Path("assets") / "icons",
    )

    if "variation_icon" not in summary.columns:
        raise ValueError(
            "Summary output from export_spc_from_csv is missing 'variation_icon' "
            f"column. Columns present: {list(summary.columns)}"
        )

    # Normalise join keys
    summary["OrgCode"] = summary["OrgCode"].astype(str).str.strip()
    summary["MetricName"] = summary["MetricName"].astype(str).str.strip()
    summary["variation_icon"] = summary["variation_icon"].astype(str).str.strip()

    icon_lookup = (
        summary[["OrgCode", "MetricName", "variation_icon"]]
        .drop_duplicates()
        .set_index(["OrgCode", "MetricName"])["variation_icon"]
        .to_dict()
    )

    # ----------------------------------------------------------------
    # 3) Build xmr_golden_expected_summary.csv
    # ----------------------------------------------------------------
    summary_rows = []
    missing_icon_keys = []

    for _, row in df.iterrows():
        org_code = str(row["Org"]).strip()
        metric_name = str(row["combination"]).strip()

        key = (org_code, metric_name)
        icon = icon_lookup.get(key)

        if icon is None:
            # Shouldn't happen, but fail soft and treat as common cause
            missing_icon_keys.append(key)
            icon = "VariationIconCommonCause.png"

        variation_code = ICON_TO_VARIATION_CODE.get(icon, "01. CC")
        variation_category = VARIATION_MAP.get(variation_code, "")

        rule_break_full = str(row["RuleBreak"]).strip()
        rule_label = RULE_LABEL_MAP.get(rule_break_full, "").strip()
        rule_short = _short_rule_name(rule_break_full)

        # Last-point expected special cause flag from RuleBreak
        expected_sc = rule_break_full != "00. None"

        summary_rows.append(
            {
                "OrgCode": org_code,
                "MetricName": metric_name,
                "VariationCode": variation_code,
                "VariationCategory": variation_category,
                "Expected_Special_Cause": expected_sc,
                "Expected_Special_Cause_Label": rule_label,
                "RuleBreakRaw": rule_short,
            }
        )

    if missing_icon_keys:
        print(
            "[WARN] No variation_icon found in summary for some series; "
            "they were defaulted to common cause. Keys:\n"
            + "\n".join(f"  {k}" for k in sorted(set(missing_icon_keys)))
        )

    expected_df = pd.DataFrame(summary_rows)
    expected_df.sort_values(["OrgCode", "MetricName"], inplace=True)

    expected_path = base_dir / "xmr_golden_expected_summary.csv"
    expected_df.to_csv(expected_path, index=False)
    print(f"[INFO] Wrote golden expected summary to: {expected_path}")

    print("[INFO] Done. You can now run the pytest golden tests against this dataset.")


if __name__ == "__main__":
    build_golden_from_dataset_lp()
