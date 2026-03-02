import mdcspc as mdc


def main():
    # 1. Run XmR via the library on your real CAN data
    #    (this also writes charts + summary CSV as a side-effect)
    summary, multi = mdc.export_spc_from_csv(
        "working/can_as_sample.csv",  # you can also use r"working\can_as_sample.csv"
        chart_mode="xmr",             # or "x_only" if you want, but "xmr" is fine
    )

    print(f"[INFO] Summary rows: {len(summary)}")
    print(f"[INFO] Groups in MultiXmrResult: {len(multi.by_group)}")

    # 2. Build icon table and export CSV + XLSX via the *library*
    icon_table, csv_path, xlsx_path = mdc.export_icon_table(
        summary=summary,
        metric_configs=mdc.load_metric_config(),
        working_dir="working",  # same working dir you’ve been using
    )

    print(f"[INFO] Icon table rows: {len(icon_table)}")
    print(f"[INFO] Icon table CSV: {csv_path}")
    print(f"[INFO] Icon table XLSX: {xlsx_path}")


if __name__ == "__main__":
    main()
