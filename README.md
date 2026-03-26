# MDCpip / mdcspc

Python package for generating NHS England Making Data Count style SPC outputs (currently focused on XmR charts).

---

## Overview

`mdcspc` is a Python package for producing SPC outputs from long-format time-series data.

Current Draft 1 scope includes:

- XmR charts
- long-format CSV input
- pandas DataFrame input
- SQLite input
- SPC logic and special-cause rules
- PNG chart outputs
- per-series summary CSV output
- config-driven behaviour via CSV files
- helper commands for config setup and recalculation workflows

---

## Installation

Typical editable install during development:

```bash
pip install -e .
```

After installation, the main CLI entry point is:

```powershell
mdcspc --help
```

Fallback module-style command:

```powershell
python -m mdcspc.cli --help
```

Do not use `python -m src.mdcspc.cli` as normal package usage. That is a repo-root development shortcut, not the intended installed command.

---

## Main commands

- `init-config` — write editable config templates (`metric_config.csv`, `spc_phase_config.csv`, `spc_target_config.csv`) to a folder
- `explain-config` — explain where configs will be loaded from (user `--config-dir` overrides vs packaged defaults)
- `wizard` — generate starter config files from an input CSV
- `recalc-wizard` — interactive helper to add a phased recalculation date to a metric
- `export-csv` — export SPC outputs from a long-format CSV
- `export-sqlite` — export SPC outputs from a SQLite query

---

## Config files

The package uses these config files:

- `metric_config.csv` — metric-level behaviour and chart settings
- `spc_phase_config.csv` — phased recalculation points and annotations
- `spc_target_config.csv` — target settings

You can either:

- generate starter versions with `init-config` or `wizard`, or
- edit config CSVs manually if you are doing bulk / power-user setup

---

## Proven guided workflow (tested)

### 1. Create starter config from CSV

```powershell
mdcspc wizard --input tests/data/xmr_golden_input.csv --out-config working/wizard_real_test_2 --defaults
```

### 2. Add a recalculation / phase change

```powershell
mdcspc recalc-wizard --config-dir working/wizard_real_test_2 --metric "Decimal+None+CC" --org "ORG_GOLD"
```

Example answers at prompt:

- `PhaseStart`: `2025-05-01`
- `Annotation`: `test upper`
- `ShowOnChart`: `y`
- `Position`: `U`

### 3. Rebuild outputs

```powershell
mdcspc export-csv --input tests/data/xmr_golden_input.csv --out working/wizard_real_test_2_out --config-dir working/wizard_real_test_2
```

### 4. Review outputs

- Check charts in `working/wizard_real_test_2_out/charts`
- Confirm phase annotations appear at the correct position (top / bottom)
- Check CSV summaries for consistency

---

## Typical usage patterns

### Export from CSV

```powershell
mdcspc export-csv --input path/to/input.csv --out path/to/output
```

### Export from SQLite

```powershell
mdcspc export-sqlite --db path/to/data.db --sql path/to/query.sql --out path/to/output
```

### Write starter config templates

```powershell
mdcspc init-config --out-config path/to/config
```

### Explain config resolution

```powershell
mdcspc explain-config
```

---

## Workflow notes

- Wizard usage is optional
- Manual config editing is fully supported, especially for bulk / power-user workflows
- Recalcs persist until changed or removed in config
- Typical pattern is: generate → review → refine → rerun

---

## Current status

This repository is currently at Draft 1 stage.

Recent verification completed:

- full pytest suite passing
- CSV / DataFrame / SQLite export routes working
- CLI smoke tests passing
- phase config flow tested
- headless plotting fixed for test and server environments

---

## Notes

This package is being developed primarily as a practical Python implementation of Making Data Count style SPC workflows. Documentation and packaging may continue to be refined, but the current Draft 1 package has a passing test suite and working CLI routes.
