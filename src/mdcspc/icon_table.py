from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import os

import pandas as pd
from .metric_config import MetricConfig


# -------------------------------------------------------------------
# DESCRIPTIONS – wording for Variation / Assurance columns
# -------------------------------------------------------------------

VARIATION_DESCRIPTIONS = {
    "VariationIconCommonCause.png": "Common cause",
    "VariationIconConcernHigh.png": "Concern (high)",
    "VariationIconConcernLow.png": "Concern (low)",
    "VariationIconImprovementHigh.png": "Improvement (high)",
    "VariationIconImprovementLow.png": "Improvement (low)",
    "VariationIconNeitherHigh.png": "Change (high)",
    "VariationIconNeitherLow.png": "Change (low)",
}

ASSURANCE_DESCRIPTIONS = {
    "AssuranceIconFail.png": "Failing",
    "AssuranceIconHitOrMiss.png": "Hit or miss",
    "AssuranceIconPass.png": "Passing",
    "IconEmpty.png": "No target",
}


# -------------------------------------------------------------------
# Internal helpers – same logic as before
# -------------------------------------------------------------------

def _choose_column(
    summary: pd.DataFrame,
    exact_candidates: List[str],
    substr_keywords: Optional[List[str]] = None,
) -> pd.Series:
    """
    Pick a column from the summary DataFrame.

    1) Try exact column-name matches in order.
    2) If none found, try case-insensitive substring matches
       using substr_keywords.
    3) If still nothing, return a column of <NA>.
    """
    for col in exact_candidates:
        if col in summary.columns:
            return summary[col]

    if substr_keywords:
        for col in summary.columns:
            name = col.lower()
            for kw in substr_keywords:
                if kw.lower() in name:
                    return summary[col]

    return pd.Series([pd.NA] * len(summary), index=summary.index)


def _build_kpi_column(summary: pd.DataFrame) -> pd.Series:
    """
    Build a human-readable 'KPI' label for the left-most column.
    """
    if {"OrgCode", "MetricName"}.issubset(summary.columns):
        return summary["OrgCode"].astype(str) + " - " + summary["MetricName"].astype(str)

    if "MetricName" in summary.columns:
        return summary["MetricName"].astype(str)

    if "OrgName" in summary.columns:
        return summary["OrgName"].astype(str)

    first_col = summary.columns[0]
    return summary[first_col].astype(str)


def _describe_variation(filename: str) -> str:
    if not filename:
        return ""
    return VARIATION_DESCRIPTIONS.get(filename, f"Unknown ({filename})")


def _describe_assurance(filename: str) -> str:
    if not filename:
        return ""
    return ASSURANCE_DESCRIPTIONS.get(filename, f"Unknown ({filename})")


def _apply_percent_scaling_for_percent_metrics(
    icon_table: pd.DataFrame,
    summary: pd.DataFrame,
    metric_configs: Dict[str, MetricConfig],
) -> None:
    """
    For metrics whose Unit is 'percent' in metric_config, convert
    Measure/Target/Mean/LPL/UPL from decimals (0.9687) to percentages
    (e.g. 96.9), using DecimalPlaces as the rounding rule.
    """
    if "MetricName" not in summary.columns:
        print(
            "[INFO] MetricName column not found in summary; "
            "cannot apply percent scaling based on metric_config."
        )
        return

    numeric_cols = [
        "Measure",
        "Target",
        "Mean",
        "Lower process limit",
        "Upper process limit",
    ]

    for idx in icon_table.index:
        if idx not in summary.index:
            continue

        raw_name = summary.loc[idx, "MetricName"]
        metric_name = str(raw_name).strip()
        cfg = metric_configs.get(metric_name)
        if cfg is None:
            continue

        unit = getattr(cfg, "unit", None) or getattr(cfg, "Unit", None)
        if unit is None or str(unit).strip().lower() != "percent":
            continue

        decimal_places = getattr(cfg, "decimal_places", None) or getattr(
            cfg, "DecimalPlaces", None
        )

        for col in numeric_cols:
            if col not in icon_table.columns:
                continue
            value = icon_table.at[idx, col]

            if isinstance(value, str):
                try:
                    float(value)
                except ValueError:
                    continue

            if pd.isna(value):
                continue

            try:
                val = float(value) * 100.0
            except (TypeError, ValueError):
                continue

            if decimal_places is not None:
                try:
                    dp = int(decimal_places)
                    val = round(val, dp)
                except Exception:
                    pass

            icon_table.at[idx, col] = val


# -------------------------------------------------------------------
# Core builder – as before
# -------------------------------------------------------------------

def build_icon_table(
    summary: pd.DataFrame,
    metric_configs: Dict[str, MetricConfig],
) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Build an MDC-style 'summary icon table' from a summary DataFrame.

    Returns
    -------
    icon_table:
        DataFrame with columns:
            KPI,
            Latest month,
            Measure,
            Target,
            Variation,
            Assurance,
            Mean,
            Lower process limit,
            Upper process limit

    variation_filenames:
        Series of variation icon filenames aligned to icon_table rows.

    assurance_filenames:
        Series of assurance icon filenames aligned to icon_table rows.
    """
    kpi = _build_kpi_column(summary)

    latest_month = _choose_column(
        summary,
        ["last_month", "latest_month", "last_date", "last_point_date", "last_index"],
        ["month", "date"],
    )

    measure = _choose_column(
        summary,
        ["last_value", "latest_value", "value_last", "last_measure"],
        ["value", "measure"],
    )

    target = _choose_column(
        summary,
        ["latest_target", "target", "target_value", "target_latest"],
        ["target"],
    )

    mean = _choose_column(
        summary,
        ["mean", "mean_latest_phase", "mean_phase", "cl"],
        ["mean", "centre", "center"],
    )

    lpl = _choose_column(
        summary,
        ["lcl", "lpl", "lower_limit", "lower_process_limit"],
        ["lcl", "lpl", "lower"],
    )

    upl = _choose_column(
        summary,
        ["ucl", "upl", "upper_limit", "upper_process_limit"],
        ["ucl", "upl", "upper"],
    )

    variation_files = _choose_column(
        summary,
        ["variation_icon", "variation_icon_file", "variation_icon_filename"],
        ["variation_icon"],
    ).fillna("")

    assurance_files = _choose_column(
        summary,
        ["assurance_icon", "assurance_icon_file", "assurance_icon_filename"],
        ["assurance_icon"],
    ).fillna("")

    var_desc = [_describe_variation(str(v) if isinstance(v, str) else "") for v in variation_files]
    ass_desc = [_describe_assurance(str(a) if isinstance(a, str) else "") for a in assurance_files]

    icon_table = pd.DataFrame(
        {
            "KPI": kpi,
            "Latest month": latest_month,
            "Measure": measure,
            "Target": target,
            "Variation": var_desc,
            "Assurance": ass_desc,
            "Mean": mean,
            "Lower process limit": lpl,
            "Upper process limit": upl,
        }
    )

    _apply_percent_scaling_for_percent_metrics(
        icon_table=icon_table,
        summary=summary,
        metric_configs=metric_configs,
    )

    icon_table["Target"] = icon_table["Target"].where(
        icon_table["Target"].notna(), "No Target"
    )

    icon_table = icon_table.sort_values("KPI").reset_index(drop=True)

    variation_files = variation_files.reindex(icon_table.index)
    assurance_files = assurance_files.reindex(icon_table.index)

    return icon_table, variation_files, assurance_files


# -------------------------------------------------------------------
# Library-level export: CSV + Excel (with icons)
# -------------------------------------------------------------------

def export_icon_table(
    summary: pd.DataFrame,
    metric_configs: Dict[str, MetricConfig],
    working_dir: Union[str, Path],
    icons_dir: Optional[Union[str, Path]] = None,
    csv_filename: str = "spc_icon_table.csv",
    xlsx_filename: str = "spc_icon_table.xlsx",
) -> Tuple[pd.DataFrame, str, str]:
    """
    High-level helper to:
      1) Build the MDC icon table from a summary DataFrame.
      2) Save CSV and styled Excel (with embedded icons) into working_dir.

    Returns
    -------
    icon_table : DataFrame
        The icon-table data.
    csv_path : str
        Full path to the CSV file.
    xlsx_path : str
        Full path to the XLSX file ('' if XlsxWriter not installed).
    """
    working_dir = Path(working_dir)
    working_dir.mkdir(parents=True, exist_ok=True)

    if icons_dir is None:
        # Default: project_root/assets/icons
        package_root = Path(__file__).resolve().parent
        project_root = package_root.parent
        icons_dir = project_root / "assets" / "icons"
    else:
        icons_dir = Path(icons_dir)

    icon_table, variation_files, assurance_files = build_icon_table(
        summary=summary,
        metric_configs=metric_configs,
    )

    # ---- CSV ----
    csv_path = working_dir / csv_filename
    icon_table.to_csv(csv_path, index=False)
    print(f"[INFO] CSV icon table saved to: {csv_path}")

    # ---- Excel ----
    try:
        import xlsxwriter  # noqa: F401
    except ImportError:
        print(
            "[WARN] XlsxWriter is not installed. "
            "Skipping Excel export.\n"
            "To enable styled Excel with icons, run:\n"
            "    pip install XlsxWriter\n"
        )
        return icon_table, str(csv_path), ""

    xlsx_path = working_dir / xlsx_filename

    excel_table = pd.DataFrame(
        {
            "KPI": icon_table["KPI"],
            "Latest date": icon_table["Latest month"],
            "Measure": icon_table["Measure"],
            "Variation": icon_table["Variation"],
            "Variation icon": "",
            "Assurance": icon_table["Assurance"],
            "Assurance icon": "",
            "Target": icon_table["Target"],
            "Mean": icon_table["Mean"],
            "Lower process limit": icon_table["Lower process limit"],
            "Upper process limit": icon_table["Upper process limit"],
        }
    )

    with pd.ExcelWriter(xlsx_path, engine="xlsxwriter") as writer:
        excel_table.to_excel(writer, index=False, sheet_name="SPC Icon Table")
        workbook = writer.book
        worksheet = writer.sheets["SPC Icon Table"]

        header_format = workbook.add_format(
            {
                "bold": True,
                "bg_color": "#DAE3F3",
                "border": 1,
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
            }
        )

        display_headers = [
            "KPI",
            "Latest date",
            "Measure",
            "Variation",
            "Icon",
            "Assurance",
            "Icon",
            "Target",
            "Mean",
            "Lower\nprocess\nlimit",
            "Upper\nprocess\nlimit",
        ]

        for col_num, value in enumerate(display_headers):
            worksheet.write(0, col_num, value, header_format)

        # Column formats
        kpi_fmt = workbook.add_format({
            "border": 1,
            "align": "left",
            "indent": 0.2,
        })

        latest_date_fmt = workbook.add_format({
            "border": 1,
            "align": "center",
            "num_format": "dd/mm/yyyy",
        })

        measure_fmt = workbook.add_format({
            "border": 1,
            "align": "center",
            "num_format": "0.00",
        })

        variation_desc_fmt = workbook.add_format({
            "border": 1,
            "align": "left",
            "indent": 0.2,
        })

        variation_icon_fmt = workbook.add_format({
            "border": 1,
            "align": "center",
        })

        assurance_desc_fmt = workbook.add_format({
            "border": 1,
            "align": "left",
            "indent": 0.2,
        })

        assurance_icon_fmt = workbook.add_format({
            "border": 1,
            "align": "center",
        })

        target_fmt = workbook.add_format({
            "border": 1,
            "align": "center",
            "num_format": "0.00",
        })

        mean_fmt = workbook.add_format({
            "border": 1,
            "align": "center",
            "num_format": "0.00",
        })

        lpl_fmt = workbook.add_format({
            "border": 1,
            "align": "center",
            "num_format": "0.00",
        })

        upl_fmt = workbook.add_format({
            "border": 1,
            "align": "center",
            "num_format": "0.00",
        })

        # Column widths + default formats
        worksheet.set_column(0, 0, 30, kpi_fmt)
        worksheet.set_column(1, 1, 12, latest_date_fmt)
        worksheet.set_column(2, 2, 10, measure_fmt)
        worksheet.set_column(3, 3, 18, variation_desc_fmt)
        worksheet.set_column(4, 4, 4.8, variation_icon_fmt)
        worksheet.set_column(5, 5, 18, assurance_desc_fmt)
        worksheet.set_column(6, 6, 4.8, assurance_icon_fmt)
        worksheet.set_column(7, 7, 10, target_fmt)
        worksheet.set_column(8, 8, 10, mean_fmt)
        worksheet.set_column(9, 9, 10, lpl_fmt)
        worksheet.set_column(10, 10, 10, upl_fmt)

        # Row heights
        worksheet.set_row(0, 42)
        for r in range(1, len(excel_table) + 1):
            worksheet.set_row(r, 26)

        # Write dates properly
        latest_col = excel_table["Latest date"]
        for row_idx, value in enumerate(latest_col, start=1):
            if pd.isna(value):
                worksheet.write(row_idx, 1, "", latest_date_fmt)
                continue

            try:
                dt = pd.to_datetime(value, dayfirst=True)
            except Exception:
                worksheet.write(row_idx, 1, str(value), latest_date_fmt)
                continue

            worksheet.write_datetime(row_idx, 1, dt, latest_date_fmt)

        # Insert icons
        for row_idx in range(len(excel_table)):
            excel_row = row_idx + 1

            v_name = str(variation_files.iloc[row_idx]) if not pd.isna(
                variation_files.iloc[row_idx]
            ) else ""
            a_name = str(assurance_files.iloc[row_idx]) if not pd.isna(
                assurance_files.iloc[row_idx]
            ) else ""

            if v_name:
                v_path = icons_dir / v_name
                if v_path.exists():
                    worksheet.insert_image(
                        excel_row,
                        4,
                        str(v_path),
                        {
                            "x_scale": 0.13,
                            "y_scale": 0.13,
                            "x_offset": 5.5,
                            "y_offset": 2,
                        },
                    )

            if a_name:
                a_path = icons_dir / a_name
                if a_path.exists():
                    worksheet.insert_image(
                        excel_row,
                        6,
                        str(a_path),
                        {
                            "x_scale": 0.13,
                            "y_scale": 0.13,
                            "x_offset": 5.5,
                            "y_offset": 2,
                        },
                    )

    print(f"[INFO] Excel icon table saved to: {xlsx_path}")
    return icon_table, str(csv_path), str(xlsx_path)
