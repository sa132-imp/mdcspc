# MDCpip / mdcspc

Python package replicating NHS England Making Data Count SPC outputs (XmR charts).

---

## Overview

- Generates XmR charts from long-format time series
- Supports CSV and SQLite input
- Applies SPC logic and special-cause rules
- Produces MDC-style charts as PNGs and summary CSVs
- Config-driven behaviour via CSV files
- Optional wizard helpers for setup and recalcs

---

## Installation

Installation instructions can be expanded once packaging is stabilised.

Typical editable install during development:

\\\ash
pip install -e .
\\\

You can then run commands from the project root using:

\\\powershell
python -m src.mdcspc.cli --help
\\\

---

## Main commands

- init-config — write editable config templates (metric_config.csv, spc_phase_config.csv, spc_target_config.csv) to a folder
- explain-config — explain where configs will be loaded from (config_dir overrides vs packaged defaults)
- wizard — generate starter config files from an input CSV
- recalc-wizard — interactive wizard to add a phased recalculation date to a metric
- export-csv — export SPC outputs from a long-format CSV
- export-sqlite — export SPC outputs from a SQLite query

---

## Config files

- metric_config.csv — metric-level behaviour and chart settings
- spc_phase_config.csv — phased recalculation points and annotations
- spc_target_config.csv — target settings

---

## Proven guided workflow (tested)

### 1. Create starter config from CSV

\\\powershell
python -m src.mdcspc.cli wizard --input tests\data\xmr_golden_input.csv --out-config working\wizard_real_test_2 --defaults
\\\

### 2. Add a recalculation / phase change

\\\powershell
python -m src.mdcspc.cli recalc-wizard --config-dir working\wizard_real_test_2 --metric "Decimal+None+CC" --org "ORG_GOLD"
\\\

Example answers at prompt:

- PhaseStart: 2025-05-01
- Annotation: test upper
- ShowOnChart: y
- Position: U

### 3. Rebuild outputs

\\\powershell
python -m src.mdcspc.cli export-csv --input tests\data\xmr_golden_input.csv --out working\wizard_real_test_2_out --config-dir working\wizard_real_test_2
\\\

### 4. Review outputs

- Check charts in working\wizard_real_test_2_out\charts
- Confirm phase annotations appear at the correct position (top / bottom)
- Check CSV summaries for consistency

---

## Notes

- Wizard usage is optional; manual config editing is fully supported
- Recalcs persist until changed or removed in config
- Workflow pattern: generate → review → refine → rerun
