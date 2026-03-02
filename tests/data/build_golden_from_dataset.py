import pandas as pd
from pathlib import Path

# Work relative to this script's folder (tests/data), not the CWD
SCRIPT_DIR = Path(__file__).resolve().parent

# --- config: everything lives next to this script ---
SOURCE_CSV = SCRIPT_DIR / "dataset.csv"  # your current wide file
OUTPUT_INPUT_CSV = SCRIPT_DIR / "xmr_golden_input.csv"
OUTPUT_SUMMARY_CSV = SCRIPT_DIR / "xmr_golden_expected_summary.csv"


def main():
    source_path = SOURCE_CSV
    if not source_path.exists():
        raise FileNotFoundError(
            f"Cannot find {source_path}. Put dataset.csv next to this script "
            f"({SCRIPT_DIR}) or update SOURCE_CSV."
        )

    print(f"[INFO] Loading source dataset: {source_path}")
    df = pd.read_csv(source_path)

    # ----------------------------------------------------------------
    # 1) Build long-format input file for MDCpip
    # ----------------------------------------------------------------
    # Non-date columns in your file:
    meta_cols = ["Org", "RuleBreak", "Variation", "Metric"]
    for col in meta_cols:
        if col not in df.columns:
            raise ValueError(f"Expected column '{col}' in source CSV but did not find it.")

    # Treat everything else as a date/month column
    date_cols = [c for c in df.columns if c not in meta_cols]
    if not date_cols:
        raise ValueError("No date columns found – expected columns like '01/01/2024', '01/02/2024', ...")

    print(f"[INFO] Detected {len(date_cols)} date columns: {date_cols[0]} ... {date_cols[-1]}")

    # Melt to long format
    long_input = df.melt(
        id_vars=["Org", "Metric"],
        value_vars=date_cols,
        var_name="Month",
        value_name="Value",
    )

    # Rename to match MDCpip expectations
    long_input.rename(
        columns={
            "Org": "OrgCode",
            "Metric": "MetricName",
        },
        inplace=True,
    )

    # Optional: sort nicely
    long_input.sort_values(["OrgCode", "MetricName", "Month"], inplace=True)

    # Ensure output dir exists (script dir)
    OUTPUT_INPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    long_input.to_csv(OUTPUT_INPUT_CSV, index=False)
    print(f"[INFO] Wrote long-format input to: {OUTPUT_INPUT_CSV} (rows: {len(long_input)})")

    # ----------------------------------------------------------------
    # 2) Build expected summary variation file
    # ----------------------------------------------------------------
    summary_df = df[["Org", "Metric", "Variation", "RuleBreak"]].copy()

    summary_df.rename(
        columns={
            "Org": "OrgCode",
            "Metric": "MetricName",
            "Variation": "VariationCode",
            "RuleBreak": "RuleBreakRaw",
        },
        inplace=True,
    )

    # Map variation codes to readable categories
    variation_desc_map = {
        "01. CC": "Common cause variation",
        "02. SCHI": "Special cause improving (higher)",
        "03. SCLI": "Special cause improving (lower)",
        "04. SCHD": "Special cause deterioration (higher)",
        "05. SCLD": "Special cause deterioration (lower)",
        "06. SCHC": "Special cause change (higher)",
        "07. SCLC": "Special cause change (lower)",
    }
    summary_df["VariationCategory"] = summary_df["VariationCode"].map(variation_desc_map)

    # Anything that is not common cause is special cause
    summary_df["Expected_Special_Cause"] = summary_df["VariationCode"] != "01. CC"

    # Map the rule-break label to a canonical lower-case form
    label_map = {
        "Trend": "trend",
        "Shift": "shift",
        "2of3": "2of3",
        "Astro": "astronomical",
    }
    summary_df["Expected_Special_Cause_Label"] = (
        summary_df["RuleBreakRaw"].map(label_map).fillna("")
    )

    # Reorder columns for readability
    summary_df = summary_df[
        [
            "OrgCode",
            "MetricName",
            "VariationCode",
            "VariationCategory",
            "Expected_Special_Cause",
            "Expected_Special_Cause_Label",
            "RuleBreakRaw",
        ]
    ]

    OUTPUT_SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(OUTPUT_SUMMARY_CSV, index=False)
    print(f"[INFO] Wrote expected summary file to: {OUTPUT_SUMMARY_CSV} (rows: {len(summary_df)})")


if __name__ == "__main__":
    main()
