from pathlib import Path
import sys
import pandas as pd

# -------------------------------------------------------------------
# Make sure the project root (where the mdcspc package lives) is on sys.path
# -------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mdcspc.exporter import export_spc_from_csv


def test_golden_series_special_cause_patterns_match(tmp_path):
    """
    Use the handcrafted golden dataset to check that, for each series,
    the presence/absence and type of special-cause patterns match what
    we expect from the Excel tooling.

    Interpretation of the golden summary:

      - VariationCode == "01. CC"
          => the series should have NO special-cause points at all.

      - VariationCode != "01. CC"
          => the series should have AT LEAST ONE special-cause point,
             and that series should include the rule in RuleBreakRaw
             (Trend / Shift / 2of3 / Astro) somewhere in its points.

    Inputs (built by tests/data/build_golden_from_dataset.py):

      tests/data/xmr_golden_input.csv
        - Month, OrgCode, MetricName, Value

      tests/data/xmr_golden_expected_summary.csv
        - OrgCode, MetricName, VariationCode, VariationCategory,
          Expected_Special_Cause, Expected_Special_Cause_Label, RuleBreakRaw
    """
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"

    input_csv = data_dir / "xmr_golden_input.csv"
    expected_csv = data_dir / "xmr_golden_expected_summary.csv"

    assert input_csv.exists(), f"Golden input CSV not found: {input_csv}"
    assert expected_csv.exists(), f"Golden expected summary CSV not found: {expected_csv}"

    # Load expected per-series classifications
    expected = pd.read_csv(expected_csv)

    # Run the full exporter on the golden input
    summary, multi = export_spc_from_csv(
        input_csv,
        working_dir=tmp_path,
        config_dir=Path("config"),
        icons_dir=Path("assets") / "icons",
    )

    # Build a DataFrame of per-series special-cause patterns
    actual_rows = []

    for key, group_result in multi.by_group.items():
        # Keys come from group_cols; for golden data this should be (OrgCode, MetricName)
        if isinstance(key, tuple):
            if len(key) == 2:
                org_code, metric_name = key
            else:
                org_code = key[0]
                metric_name = key[1] if len(key) > 1 else ""
        else:
            org_code = key
            metric_name = ""

        df = group_result.data.copy()
        if df.empty:
            continue

        # Defensively handle missing columns, though they should exist
        if "special_cause" in df.columns:
            has_sc = df["special_cause"].astype(bool).any()
        else:
            has_sc = False

        if "special_cause_label" in df.columns:
            labels_present = {
                str(x).strip().lower()
                for x in df["special_cause_label"].tolist()
                if isinstance(x, str) and x.strip()
            }
        else:
            labels_present = set()

        actual_rows.append(
            {
                "OrgCode": str(org_code),
                "MetricName": str(metric_name),
                "Has_Special_Cause": has_sc,
                "Special_Cause_Labels": ";".join(sorted(labels_present)),
            }
        )

    actual = pd.DataFrame(actual_rows)

    # Join expected per-series summary to actual series-level patterns
    merged = expected.merge(
        actual,
        on=["OrgCode", "MetricName"],
        how="inner",
    )

    assert not merged.empty, "No overlap between expected golden series and actual results."

    # Normalise expected label to lower-case string (empty if NaN)
    merged["Expected_Special_Cause_Label"] = (
        merged["Expected_Special_Cause_Label"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    # Convert the semi-colon string back to a set for convenience
    def _labels_to_set(s: str) -> set:
        if not isinstance(s, str) or not s.strip():
            return set()
        return {part.strip().lower() for part in s.split(";") if part.strip()}

    merged["Actual_Label_Set"] = merged["Special_Cause_Labels"].apply(_labels_to_set)

    # -------------------------------
    # 1) Check presence/absence of ANY special cause
    # -------------------------------
    flag_equal = (
        merged["Expected_Special_Cause"].astype(bool)
        == merged["Has_Special_Cause"].astype(bool)
    )
    if not flag_equal.all():
        mismatches = merged.loc[~flag_equal, [
            "OrgCode",
            "MetricName",
            "VariationCode",
            "VariationCategory",
            "Expected_Special_Cause",
            "Has_Special_Cause",
            "Expected_Special_Cause_Label",
            "Special_Cause_Labels",
            "RuleBreakRaw",
        ]]
        print("\n[DEBUG] Special-cause PRESENCE mismatches (expected vs any actual):")
        print(mismatches.to_string(index=False))
        assert False, "Special-cause presence does not match for some golden series."

    # -------------------------------
    # 2) For series expected to have special cause, check the rule type appears
    # -------------------------------
    mask_sc = merged["Expected_Special_Cause"].astype(bool)
    labelled = merged[mask_sc].copy()

    # Only look at rows where we actually have a non-empty expected label
    labelled = labelled[labelled["Expected_Special_Cause_Label"] != ""]

    if not labelled.empty:
        def _label_matches(row) -> bool:
            exp_label = row["Expected_Special_Cause_Label"]
            label_set = row["Actual_Label_Set"]
            if not exp_label:
                return True  # nothing to check
            return exp_label in label_set

        label_match = labelled.apply(_label_matches, axis=1)

        if not label_match.all():
            mismatches = labelled.loc[~label_match, [
                "OrgCode",
                "MetricName",
                "VariationCode",
                "VariationCategory",
                "Expected_Special_Cause",
                "Has_Special_Cause",
                "Expected_Special_Cause_Label",
                "Special_Cause_Labels",
                "RuleBreakRaw",
            ]]
            print("\n[DEBUG] Special-cause RULE mismatches (expected label not found in series):")
            print(mismatches.to_string(index=False))
            assert False, (
                "Some golden series did not exhibit the expected special-cause rule "
                "(trend/shift/2of3/astronomical) anywhere in the series."
            )
