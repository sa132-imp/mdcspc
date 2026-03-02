import os
import sys
from typing import Dict, List, Optional, Tuple

import pandas as pd

# -------------------------------------------------------------------
# Ensure project root (MDCpip) is on sys.path (for consistency)
# -------------------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Icons live here (same as charts)
ICONS_DIR = os.path.join(PROJECT_ROOT, "assets", "icons")

# -------------------------------------------------------------------
# Metric config (central config/metric_config.csv)
# -------------------------------------------------------------------
from mdcspc.metric_config import load_metric_config, MetricConfig
from mdcspc.icon_table import build_icon_table


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _load_summary(
    working_dir: str,
    summary_filename: str = "spc_summary_from_input.csv",
) -> pd.DataFrame:
    """
    Load the summary CSV produced by export_spc_from_csv.py.
    """
    summary_path = os.path.join(working_dir, summary_filename)
    if not os.path.exists(summary_path):
        raise FileNotFoundError(
            f"Summary file not found: {summary_path}\n"
            "Make sure you have run scripts/export_spc_from_csv.py first."
        )

    print(f"[INFO] Loading summary from: {summary_path}")
    df = pd.read_csv(summary_path)

    # Basic clean-up: strip whitespace from any object columns
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip()

    print("[INFO] Summary columns detected:", list(df.columns))
    return df


# -------------------------------------------------------------------
# CSV export  (formatting unchanged)
# -------------------------------------------------------------------

def _export_csv(icon_table: pd.DataFrame, working_dir: str) -> str:
    """
    Save the icon table as CSV.
    Columns:
      KPI, Latest month, Measure, Target, Variation, Assurance,
      Mean, Lower process limit, Upper process limit
    """
    output_path = os.path.join(working_dir, "spc_icon_table.csv")
    icon_table.to_csv(output_path, index=False)
    print(f"[INFO] CSV icon table saved to: {output_path}")
    return output_path


# -------------------------------------------------------------------
# Excel export (formatting unchanged, with icons)
# -------------------------------------------------------------------

def _export_excel(
    icon_table: pd.DataFrame,
    variation_filenames: pd.Series,
    assurance_filenames: pd.Series,
    working_dir: str,
) -> str:
    """
    Save the icon table as a styled Excel sheet, with PNG icons inserted.

    - Header row centred & word-wrapped, taller.
    - All data cells left-aligned by default, but each column has its own format.
    - Columns (Excel view):

        0: KPI
        1: Latest date
        2: Measure
        3: Variation
        4: Variation icon
        5: Assurance
        6: Assurance icon
        7: Target
        8: Mean
        9: Lower process limit
        10: Upper process limit

    - Dates: for now, everything is shown as DD/MM/YYYY.

    If XlsxWriter is not installed, we SKIP Excel export completely.
    """
    try:
        import xlsxwriter  # noqa: F401
    except ImportError:
        print(
            "[WARN] XlsxWriter is not installed. "
            "Skipping Excel export.\n"
            "To enable styled Excel with icons, run:\n"
            "    pip install XlsxWriter\n"
        )
        return ""

    output_path = os.path.join(working_dir, "spc_icon_table.xlsx")

    excel_table = pd.DataFrame(
        {
            "KPI": icon_table["KPI"],
            "Latest date": icon_table["Latest month"],  # renamed just for Excel
            "Measure": icon_table["Measure"],
            "Variation": icon_table["Variation"],
            "Variation icon": "",  # images only
            "Assurance": icon_table["Assurance"],
            "Assurance icon": "",  # images only
            "Target": icon_table["Target"],
            "Mean": icon_table["Mean"],
            "Lower process limit": icon_table["Lower process limit"],
            "Upper process limit": icon_table["Upper process limit"],
        }
    )

    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        excel_table.to_excel(writer, index=False, sheet_name="SPC Icon Table")
        workbook = writer.book
        worksheet = writer.sheets["SPC Icon Table"]

        # Header format (light blue background, bold, centred, border, wrap)
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

        # === COLUMN FORMATS (ONE PER COLUMN) ===

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

        # === COLUMN WIDTHS (ONE PER COLUMN) ===
        worksheet.set_column(0, 0, 30, kpi_fmt)         # KPI
        worksheet.set_column(1, 1, 12, latest_date_fmt) # Latest date
        worksheet.set_column(2, 2, 10, measure_fmt)     # Measure
        worksheet.set_column(3, 3, 18, variation_desc_fmt)  # Variation
        worksheet.set_column(4, 4, 4.8, variation_icon_fmt)  # Variation icon
        worksheet.set_column(5, 5, 18, assurance_desc_fmt)   # Assurance
        worksheet.set_column(6, 6, 4.8, assurance_icon_fmt)  # Assurance icon
        worksheet.set_column(7, 7, 10, target_fmt)      # Target
        worksheet.set_column(8, 8, 10, mean_fmt)        # Mean
        worksheet.set_column(9, 9, 10, lpl_fmt)         # LPL
        worksheet.set_column(10, 10, 10, upl_fmt)       # UPL

        # Header row height
        worksheet.set_row(0, 42)
        # Data rows
        for r in range(1, len(excel_table) + 1):
            worksheet.set_row(r, 26)

        # === PER-ROW DATE WRITING ===
        latest_col = excel_table["Latest date"]
        for row_idx, value in enumerate(latest_col, start=1):  # +1 for header
            if pd.isna(value):
                worksheet.write(row_idx, 1, "", latest_date_fmt)
                continue

            try:
                dt = pd.to_datetime(value, dayfirst=True)
            except Exception:
                worksheet.write(row_idx, 1, str(value), latest_date_fmt)
                continue

            worksheet.write_datetime(row_idx, 1, dt, latest_date_fmt)

        # Insert icons into Variation icon (col 4) and Assurance icon (col 6)
        for row_idx in range(len(excel_table)):
            excel_row = row_idx + 1  # offset for header

            v_name = str(variation_filenames.iloc[row_idx]) if not pd.isna(
                variation_filenames.iloc[row_idx]
            ) else ""
            a_name = str(assurance_filenames.iloc[row_idx]) if not pd.isna(
                assurance_filenames.iloc[row_idx]
            ) else ""

            if v_name:
                v_path = os.path.join(ICONS_DIR, v_name)
                if os.path.exists(v_path):
                    worksheet.insert_image(
                        excel_row,
                        4,
                        v_path,
                        {
                            "x_scale": 0.13,
                            "y_scale": 0.13,
                            "x_offset": 5.5,
                            "y_offset": 2,
                        },
                    )

            if a_name:
                a_path = os.path.join(ICONS_DIR, a_name)
                if os.path.exists(a_path):
                    worksheet.insert_image(
                        excel_row,
                        6,
                        a_path,
                        {
                            "x_scale": 0.13,
                            "y_scale": 0.13,
                            "x_offset": 5.5,
                            "y_offset": 2,
                        },
                    )

    print(f"[INFO] Excel icon table saved to: {output_path}")
    return output_path


# -------------------------------------------------------------------
# Main entry point
# -------------------------------------------------------------------

def build_summary_icon_table():
    """
    Main entry point:
    - Load working/spc_summary_from_input.csv
    - Load central metric_config (for units/decimal places)
    - Build MDC-style icon table via mdcspc.icon_table.build_icon_table
    - Save to:
        * working/spc_icon_table.csv
        * working/spc_icon_table.xlsx
    """
    working_dir = os.path.join(PROJECT_ROOT, "working")
    os.makedirs(working_dir, exist_ok=True)

    summary = _load_summary(working_dir=working_dir)

    metric_configs = load_metric_config()
    print(f"[INFO] Loaded {len(metric_configs)} metric config row(s) from config/metric_config.csv.")

    icon_table, variation_filenames, assurance_filenames = build_icon_table(
        summary=summary,
        metric_configs=metric_configs,
    )

    print("[INFO] Building outputs...")
    _export_csv(icon_table, working_dir=working_dir)
    _export_excel(
        icon_table,
        variation_filenames=variation_filenames,
        assurance_filenames=assurance_filenames,
        working_dir=working_dir,
    )

    print("[INFO] All icon table outputs generated.")


def main():
    build_summary_icon_table()


if __name__ == "__main__":
    main()
