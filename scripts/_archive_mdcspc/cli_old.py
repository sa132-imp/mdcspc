from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional


def _try_import_export_spc_from_csv():
    try:
        # canonical location in this repo
        from .exporter import export_spc_from_csv  # type: ignore
        return export_spc_from_csv
    except Exception:
        return None


def _try_import_export_spc_from_sqlite():
    """
    Be flexible about where export_spc_from_sqlite lives.

    We try a couple of plausible module paths so the CLI doesn't break
    just because we reorganised internals.
    """
    # 1) Most likely: alongside export_spc_from_csv
    try:
        from .exporter import export_spc_from_sqlite  # type: ignore
        return export_spc_from_sqlite
    except Exception:
        pass

    # 2) Current location (dataframe-backed exporters)
    try:
        from .exporter_dataframe import export_spc_from_sqlite  # type: ignore
        return export_spc_from_sqlite
    except Exception:
        pass

    # 3) Alternate: dedicated module
    try:
        from .exporter_sqlite import export_spc_from_sqlite  # type: ignore
        return export_spc_from_sqlite
    except Exception:
        pass

    # 4) Alternate: db/sql helper module
    try:
        from .sqlite import export_spc_from_sqlite  # type: ignore
        return export_spc_from_sqlite
    except Exception:
        pass

    return None


def _build_parser(has_sqlite: bool) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mdcspc",
        description="MDC-style SPC exporter (XmR for now). Produces charts + summary from CSV or SQLite.",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # -------------------------
    # export-csv
    # -------------------------
    p_csv = sub.add_parser(
        "export-csv",
        help="Export SPC outputs from a long-format CSV.",
    )
    p_csv.add_argument("--input", required=True, help="Path to input CSV")
    p_csv.add_argument("--out", required=True, help="Output directory")
    p_csv.add_argument(
        "--config-dir",
        default=None,
        help="Directory containing config files (metric_config.csv, spc_phase_config.csv, spc_target_config.csv, etc.).",
    )
    p_csv.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce CLI output (suppresses final Done message; exporter may still print its own info).",
    )
    p_csv.add_argument("--chart-mode", default="xmr", choices=["xmr", "x_only"], help="Chart mode")
    p_csv.add_argument("--value-col", default="Value", help="Value column name in the input")
    p_csv.add_argument("--index-col", default="Month", help="Date/index column name in the input")
    p_csv.add_argument(
        "--summary-filename",
        default="spc_summary_from_input.csv",
        help="Summary CSV filename",
    )

    # -------------------------
    # export-sqlite
    # -------------------------
    p_sql = sub.add_parser(
        "export-sqlite",
        help="Export SPC outputs from a SQLite query.",
    )
    p_sql.add_argument("--db", required=True, help="Path to SQLite database file")
    p_sql.add_argument("--query", required=True, help="SQL query returning long-format data")
    p_sql.add_argument("--out", required=True, help="Output directory")
    p_sql.add_argument(
        "--config-dir",
        default=None,
        help="Directory containing config files (metric_config.csv, spc_phase_config.csv, spc_target_config.csv, etc.).",
    )
    p_sql.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce CLI output (suppresses final Done message; exporter may still print its own info).",
    )
    p_sql.add_argument("--chart-mode", default="xmr", choices=["xmr", "x_only"], help="Chart mode")
    p_sql.add_argument("--value-col", default="Value", help="Value column name in the query result")
    p_sql.add_argument("--index-col", default="Month", help="Date/index column name in the query result")
    p_sql.add_argument(
        "--summary-filename",
        default="spc_summary_from_input.csv",
        help="Summary CSV filename",
    )

    # If export-sqlite isn't actually available, we still keep the subcommand
    # (for discoverability) but we fail with a clear message at runtime.
    # That behaviour is implemented in main().
    _ = has_sqlite

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    export_spc_from_csv = _try_import_export_spc_from_csv()
    export_spc_from_sqlite = _try_import_export_spc_from_sqlite()

    parser = _build_parser(has_sqlite=export_spc_from_sqlite is not None)
    args = parser.parse_args(argv)

    # Shared CLI behaviour
    config_dir_path = Path(args.config_dir) if getattr(args, "config_dir", None) else None
    quiet = bool(getattr(args, "quiet", False))

    if not quiet:
        if config_dir_path is None:
            print("[INFO] Using config_dir: (default)")
        else:
            print(f"[INFO] Using config_dir: {config_dir_path}")

    if args.command == "export-csv":
        if export_spc_from_csv is None:
            print(
                "[ERROR] export-csv is not available because export_spc_from_csv could not be imported.",
                file=sys.stderr,
            )
            return 1

        export_spc_from_csv(
            input_csv=Path(args.input),
            working_dir=Path(args.out),
            config_dir=config_dir_path,
            chart_mode=args.chart_mode,
            value_col=args.value_col,
            index_col=args.index_col,
            summary_filename=args.summary_filename,
        )
        if not quiet:
            print("[INFO] Done.")  # Only the CLI should print this final "Done" message
        return 0

    if args.command == "export-sqlite":
        if export_spc_from_sqlite is None:
            print(
                "[ERROR] export-sqlite is not available because export_spc_from_sqlite could not be imported.",
                file=sys.stderr,
            )
            return 1

        export_spc_from_sqlite(
            db_path=Path(args.db),
            sql=str(args.query),
            working_dir=Path(args.out),
            config_dir=config_dir_path,
            chart_mode=args.chart_mode,
            value_col=args.value_col,
            index_col=args.index_col,
            summary_filename=args.summary_filename,
        )
        if not quiet:
            print("[INFO] Done.")  # Only the CLI should print this final "Done" message
        return 0

    print(f"[ERROR] Unknown command: {args.command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
