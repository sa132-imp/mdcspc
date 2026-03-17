from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Any, Callable, Dict, Tuple

from importlib import resources

from .wizard import run_wizard
from mdcspc.wizard import recalc_wizard


def _try_import_export_spc_from_csv():
    try:
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


def _call_with_optional_kwargs(func: Callable[..., Any], kwargs: Dict[str, Any]) -> Any:
    """
    Call func(**kwargs), but if it errors due to an unexpected keyword argument
    (e.g. older exporter doesn't accept quiet/config_dir), retry without it.

    This keeps the CLI robust while internals move around.
    """
    try:
        return func(**kwargs)
    except TypeError as e:
        msg = str(e)

        # Retry stripping known optional kwargs one-by-one if they are rejected
        for opt in [
            "quiet",
            "config_dir",
            "icons_dir",
            "title_template",
            "y_label",
            "y_min",
            "y_max",
            "x_label_rotate",
            "x_label_fontsize",
            "x_label_format",
            "annotate_last_point",
            "annotate_special_cause",
        ]:
            if opt in kwargs and ("unexpected keyword argument" in msg) and (f"'{opt}'" in msg):
                new_kwargs = dict(kwargs)
                new_kwargs.pop(opt, None)
                return _call_with_optional_kwargs(func, new_kwargs)

        raise


# -------------------------
# Config helpers (init/explain)
# -------------------------

_PACKAGED_CONFIG_FILES = (
    "metric_config.csv",
    "spc_target_config.csv",
)


def _packaged_config_traversable(filename: str):
    """
    Return a Traversable for a packaged config file inside the installed package.

    Expected location in the package:
      mdcspc/resources/config/<filename>
    """
    return resources.files("mdcspc").joinpath("resources", "config", filename)


def _resolve_config_sources(config_dir: Optional[Path]) -> Dict[str, Tuple[str, Optional[Path]]]:
    """
    For each known config filename, decide where it will be loaded from.

    Returns a mapping:
      filename -> (source_label, filesystem_path_if_applicable)

    Rules:
      - If config_dir is provided and contains the file -> use that path
      - Else -> packaged default (we return a temporary extracted path via as_file when needed)
    """
    out: Dict[str, Tuple[str, Optional[Path]]] = {}

    for fname in _PACKAGED_CONFIG_FILES:
        if config_dir is not None:
            candidate = config_dir / fname
            if candidate.exists():
                out[fname] = ("config_dir override", candidate)
                continue
            else:
                out[fname] = ("config_dir override (missing -> fallback to packaged default)", None)
                continue

        out[fname] = ("packaged default", None)

    return out


def _cmd_init_config(out_dir: Path, force: bool) -> int:
    """
    Copy packaged default config CSVs into out_dir.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    for fname in _PACKAGED_CONFIG_FILES:
        dest = out_dir / fname
        if dest.exists() and not force:
            print(
                f"[ERROR] {dest} already exists. Use --force to overwrite.",
                file=sys.stderr,
            )
            return 1

    # Copy each packaged file
    for fname in _PACKAGED_CONFIG_FILES:
        dest = out_dir / fname
        traversable = _packaged_config_traversable(fname)
        # as_file handles wheels/zip installs
        with resources.as_file(traversable) as src_path:
            src_p = Path(src_path)
            if not src_p.exists():
                print(
                    "[ERROR] Packaged config file missing from installation: "
                    f"mdcspc/resources/config/{fname}",
                    file=sys.stderr,
                )
                return 1
            dest.write_bytes(src_p.read_bytes())

    print(f"[INFO] Wrote config templates to: {out_dir}")
    print("[INFO] Next steps:")
    print(f"  1) Edit the CSVs in: {out_dir}")
    print("  2) Run exports using: --config-dir <that folder>")
    return 0


def _cmd_explain_config(config_dir: Optional[Path]) -> int:
    """
    Print where configs will be loaded from and what exists/missing.
    """
    print("[INFO] mdcspc config resolution")
    if config_dir is None:
        print("[INFO] --config-dir not provided: using packaged defaults (unless you pass overrides).")
    else:
        print(f"[INFO] --config-dir provided: {config_dir}")

    resolved = _resolve_config_sources(config_dir)

    for fname in _PACKAGED_CONFIG_FILES:
        label, path = resolved[fname]
        if path is not None:
            print(f"  - {fname}: {label} -> {path}")
        else:
            # Either packaged default, or missing in config_dir and will fall back
            if label.startswith("config_dir override (missing"):
                missing_path = (config_dir / fname) if config_dir is not None else None
                print(f"  - {fname}: MISSING in config_dir -> {missing_path}")
                print(f"           fallback: packaged default -> mdcspc/resources/config/{fname}")
            else:
                print(f"  - {fname}: packaged default -> mdcspc/resources/config/{fname}")

    print("[INFO] Tip:")
    print("  Run `mdcspc init-config --out ./mdcspc_config` to create editable templates,")
    print("  then use `--config-dir ./mdcspc_config` when exporting.")
    return 0


def _build_parser(has_sqlite: bool) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mdcspc",
        description="MDC-style SPC exporter (XmR for now). Produces charts + summary from CSV or SQLite.",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # -------------------------
    # init-config
    # -------------------------
    p_init = sub.add_parser(
        "init-config",
        help="Write editable config templates (metric_config.csv, spc_target_config.csv) to a folder.",
    )
    p_init.add_argument("--out", required=True, help="Output directory to write config templates into")
    p_init.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files if present",
    )

    # -------------------------
    # explain-config
    # -------------------------
    p_explain = sub.add_parser(
        "explain-config",
        help="Explain where configs will be loaded from (config_dir overrides vs packaged defaults).",
    )
    p_explain.add_argument(
        "--config-dir",
        default=None,
        help="Directory containing config files (metric_config.csv, spc_phase_config.csv, spc_target_config.csv, etc.).",
    )


    # -------------------------
    # wizard
    # -------------------------
    p_wizard = sub.add_parser(
        "wizard",
        help="Generate starter config files from an input CSV.",
    )
    p_wizard.add_argument(
        "--input",
        "--input-csv",
        dest="input",
        required=True,
        help="Path to input CSV containing a MetricName column.",
    )
    p_wizard.add_argument(
        "--defaults",
        action="store_true",
        help="Use default values, non-interactive",
    )
    p_wizard.add_argument(
        "--out-config",
        "--out",
        dest="out_config",
        required=True,
        help="Directory to write metric_config.csv and spc_target_config.csv into.",
    )

    # -------------------------
    # recalc-wizard
    # -------------------------
    p_recalc = sub.add_parser(
        "recalc-wizard",
        help="Interactive wizard to add a phased recalculation date to a metric.",
    )
    p_recalc.add_argument(
        "--metric",
        type=str,
        default=None,
        help="MetricName to apply recalculation (optional; prompt if missing).",
    )
    p_recalc.add_argument(
        "--org",
        type=str,
        default=None,
        help="OrgCode to apply recalculation (optional; prompt if missing).",
    )
    p_recalc.add_argument(
        "--config-dir",
        type=Path,
        default=Path("config"),
        help="Directory containing spc_phase_config.csv",
    )

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
        help="Suppress chatter; still prints final '[INFO] Done.' only.",
    )
    p_csv.add_argument("--chart-mode", default="x_only", choices=["xmr", "x_only"], help="Chart mode")
    p_csv.add_argument("--value-col", default="Value", help="Value column name in the input")
    p_csv.add_argument("--index-col", default="Month", help="Date/index column name in the input")
    p_csv.add_argument(
        "--summary-filename",
        default="spc_summary_from_input.csv",
        help="Summary CSV filename",
    )

    p_csv.add_argument(
        "--title-template",
        default="{MetricName}",
        help="Chart title template using group column names, e.g. '{OrgCode} – {MetricName}'.",
    )
    p_csv.add_argument(
        "--y-label",
        default=None,
        help="Y-axis label override (defaults to value column name, with units where known).",
    )
    p_csv.add_argument("--y-min", type=float, default=None, help="Y-axis minimum (optional)")
    p_csv.add_argument("--y-max", type=float, default=None, help="Y-axis maximum (optional)")
    p_csv.add_argument(
        "--x-label-rotate",
        type=int,
        default=90,
        help="Rotation angle for x-axis tick labels (default: 90).",
    )
    p_csv.add_argument(
        "--x-label-fontsize",
        type=int,
        default=8,
        help="Font size for x-axis tick labels (default: 8).",
    )
    p_csv.add_argument(
        "--x-label-format",
        default=None,
        help="Optional strftime format for x-axis labels (e.g. '%d/%m/%y'). If omitted, mdcspc chooses a sensible default.",
    )
    p_csv.add_argument(
        "--annotate-last-point",
        action="store_true",
        help="Annotate the last point value on the chart.",
    )
    p_csv.add_argument(
        "--annotate-special-cause",
        action="store_true",
        help="Annotate special-cause points with the rule label (can be busy on dense charts).",
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
        help="Suppress chatter; still prints final '[INFO] Done.' only.",
    )
    p_sql.add_argument("--chart-mode", default="x_only", choices=["xmr", "x_only"], help="Chart mode")
    p_sql.add_argument("--value-col", default="Value", help="Value column name in the query result")
    p_sql.add_argument("--index-col", default="Month", help="Date/index column name in the query result")
    p_sql.add_argument(
        "--summary-filename",
        default="spc_summary_from_input.csv",
        help="Summary CSV filename",
    )

    p_sql.add_argument(
        "--title-template",
        default="{MetricName}",
        help="Chart title template using group column names, e.g. '{OrgCode} – {MetricName}'.",
    )
    p_sql.add_argument(
        "--y-label",
        default=None,
        help="Y-axis label override (defaults to value column name, with units where known).",
    )
    p_sql.add_argument("--y-min", type=float, default=None, help="Y-axis minimum (optional)")
    p_sql.add_argument("--y-max", type=float, default=None, help="Y-axis maximum (optional)")
    p_sql.add_argument(
        "--x-label-rotate",
        type=int,
        default=90,
        help="Rotation angle for x-axis tick labels (default: 90).",
    )
    p_sql.add_argument(
        "--x-label-fontsize",
        type=int,
        default=8,
        help="Font size for x-axis tick labels (default: 8).",
    )
    p_sql.add_argument(
        "--x-label-format",
        default=None,
        help="Optional strftime format for x-axis labels (e.g. '%d/%m/%y'). If omitted, mdcspc chooses a sensible default.",
    )
    p_sql.add_argument(
        "--annotate-last-point",
        action="store_true",
        help="Annotate the last point value on the chart.",
    )
    p_sql.add_argument(
        "--annotate-special-cause",
        action="store_true",
        help="Annotate special-cause points with the rule label (can be busy on dense charts).",
    )

    _ = has_sqlite
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    export_spc_from_csv = _try_import_export_spc_from_csv()
    export_spc_from_sqlite = _try_import_export_spc_from_sqlite()

    parser = _build_parser(has_sqlite=export_spc_from_sqlite is not None)
    args = parser.parse_args(argv)

    # Commands that don't need exporter imports
    if args.command == "init-config":
        return _cmd_init_config(out_dir=Path(args.out), force=bool(args.force))

    if args.command == "explain-config":
        config_dir_path = Path(args.config_dir) if getattr(args, "config_dir", None) else None
        return _cmd_explain_config(config_dir=config_dir_path)

    if args.command == "wizard":
        return run_wizard(
            input_csv=Path(args.input),
            out_config=Path(args.out_config),
            defaults=args.defaults,  # added to pass the CLI flag into wizard
        )

    if args.command == "recalc-wizard":
        return recalc_wizard(
            config_dir=args.config_dir,
            metric=args.metric,
            org=args.org,
        )

    # Export commands below
    config_dir_path = Path(args.config_dir) if getattr(args, "config_dir", None) else None
    quiet = bool(getattr(args, "quiet", False))

    # NOTE:
    # In quiet mode we must not print chatter (tests enforce this),
    # but we DO still print the final "[INFO] Done." line.
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

        call_kwargs = dict(
            input_csv=Path(args.input),
            working_dir=Path(args.out),
            config_dir=config_dir_path,
            chart_mode=args.chart_mode,
            value_col=args.value_col,
            index_col=args.index_col,
            summary_filename=args.summary_filename,
            title_template=args.title_template,
            y_label=args.y_label,
            y_min=args.y_min,
            y_max=args.y_max,
            x_label_rotate=args.x_label_rotate,
            x_label_fontsize=args.x_label_fontsize,
            x_label_format=args.x_label_format,
            annotate_last_point=args.annotate_last_point,
            annotate_special_cause=args.annotate_special_cause,
            quiet=quiet,
        )
        _call_with_optional_kwargs(export_spc_from_csv, call_kwargs)

        # Always print Done, even in quiet mode (tests require it).
        print("[INFO] Done.")
        return 0

    if args.command == "export-sqlite":
        if export_spc_from_sqlite is None:
            print(
                "[ERROR] export-sqlite is not available because export_spc_from_sqlite could not be imported.",
                file=sys.stderr,
            )
            return 1

        call_kwargs = dict(
            db_path=Path(args.db),
            sql=str(args.query),
            working_dir=Path(args.out),
            config_dir=config_dir_path,
            chart_mode=args.chart_mode,
            value_col=args.value_col,
            index_col=args.index_col,
            summary_filename=args.summary_filename,
            title_template=args.title_template,
            y_label=args.y_label,
            y_min=args.y_min,
            y_max=args.y_max,
            x_label_rotate=args.x_label_rotate,
            x_label_fontsize=args.x_label_fontsize,
            x_label_format=args.x_label_format,
            annotate_last_point=args.annotate_last_point,
            annotate_special_cause=args.annotate_special_cause,
            quiet=quiet,
        )
        _call_with_optional_kwargs(export_spc_from_sqlite, call_kwargs)

        # Always print Done, even in quiet mode (tests require it).
        print("[INFO] Done.")
        return 0

    print(f"[ERROR] Unknown command: {args.command}", file=sys.stderr)
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
