# Running mdcspc

This guide explains how to run the MDCpip / mdcspc package from terminal.

---

## Overview

The package generates XmR charts and summary outputs from CSV or SQLite input.  
Config-driven workflow with optional helper wizards for setup and recalcs.

---

## Before you start

Open a terminal in the project root folder:

\\\powershell
cd ""C:\Users\adam.smith9\OneDrive - NHS\Projects\MDCpip""
\\\

All commands use the Python module entry point:

\\\powershell
python -m src.mdcspc.cli <command>
\\\

---

## Main commands

- init-config — write editable config templates (metric_config.csv, spc_phase_config.csv, spc_target_config.csv)
- explain-config — show where configs will be loaded from (config_dir overrides vs packaged defaults)
- wizard — generate starter config files from an input CSV
- recalc-wizard — add a phased recalculation date interactively
- export-csv — generate charts and summary from CSV
- export-sqlite — generate charts and summary from SQLite

---

## Config files

- metric_config.csv — metric-level settings and chart behaviour
- spc_phase_config.csv — phased recalculation points and annotations
- spc_target_config.csv — target settings

---

## Guided setup route

Use this route if starting with a CSV and want starter config:

### 1. Create starter config

\\\powershell
python -m src.mdcspc.cli wizard --input tests\data\xmr_golden_input.csv --out-config working\wizard_real_test_2 --defaults
\\\

- Detects available metrics  
- Writes starter config: metric_config.csv, spc_phase_config.csv, spc_target_config.csv

### 2. Add a recalculation / phase change

\\\powershell
python -m src.mdcspc.cli recalc-wizard --config-dir working\wizard_real_test_2 --metric ""Decimal+None+CC"" --org ""ORG_GOLD""
\\\

Example answers:

- PhaseStart: 2025-05-01  
- Annotation: test upper  
- ShowOnChart: y  
- Position: U  

Updates spc_phase_config.csv.

### 3. Rebuild outputs

\\\powershell
python -m src.mdcspc.cli export-csv --input tests\data\xmr_golden_input.csv --out working\wizard_real_test_2_out --config-dir working\wizard_real_test_2
\\\

### 4. Review outputs

- Check charts in working\wizard_real_test_2_out\charts  
- Confirm phase annotations appear top/bottom correctly  
- Check CSV summaries

---

## Manual setup route

1. Create blank templates:

\\\powershell
python -m src.mdcspc.cli init-config --out working\init_config_test --force
\\\

2. Edit config files manually as needed  
3. Run export commands (CSV or SQLite)  
4. Review outputs  
5. Add recalcs if needed and rerun export

---

## Notes

- Both wizard and manual workflows are supported  
- Recalcs persist until changed or removed  
- Workflow pattern: generate → review → refine → rerun
