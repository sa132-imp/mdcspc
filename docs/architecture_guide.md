# MDCSPC – Architecture Guide (Plain English)

## 1. What this system does

MDCSPC takes time-series healthcare (or similar operational) data and turns it into:

- SPC (Statistical Process Control) calculations
- control charts (X and moving range)
- rule-based signal detection
- summary outputs for reporting
- optional configuration-based adjustments (phases, targets, metrics)

Input → Output:

Raw time-series data → grouped SPC analysis → charts + summary tables


## 2. High-level system flow

Input CSV / SQLite
→ CLI (mdcspc)
→ exporter.py (orchestration layer)
→ xmr.py (core SPC calculations)
→ grouping logic (OrgCode / MetricName)
→ config application (phase + target)
→ outputs (CSV + PNG charts)


## 3. Core modules

### xmr.py (CORE ENGINE)

- analyse_xmr()
- SPC statistics:
  - mean
  - sigma
  - UCL / LCL
- SPC rules:
  - trend
  - shift
  - 2-of-3
  - astronomical points
- phase recalculation
- low-data fallback

THIS is the file to port to Polars / PySpark.


### exporter.py (ORCHESTRATOR)

- loads input data
- detects grouping columns
- splits dataset into series
- calls analyse_xmr per group
- merges results
- writes outputs


### cli.py (ENTRY POINT)

- argument parsing
- command routing
- calls exporter

NO calculations happen here.


### wizard.py (CONFIG BUILDER)

- builds metric config
- builds phase config
- builds target config


## 4. Config system

metric_config.csv
- MetricName
- Direction

spc_phase_config.csv
- OrgCode + MetricName
- PhaseStart

spc_target_config.csv
- time-varying targets


Config lookup order:

config/ → working/


## 5. Data model

Month | OrgCode | MetricName | Value

Grouped as:
OrgCode + MetricName


## 6. Outputs

Summary CSV:
- control limits
- rule flags
- phase labels

Charts:
- X chart (and optional mR)
- PNG output per group


## 7. What is NOT core logic

- CLI
- wizard tools
- scripts/
- tests
- logging wrappers


## 8. What matters for rewrite

MUST PORT:
- analyse_xmr
- SPC rules
- control limits
- phase logic

OPTIONAL:
- grouping logic
- exporter orchestration

DO NOT PORT:
- CLI
- file IO wrappers
- tests
- scripts


## 9. Mental model

CLI
→ exporter
→ xmr engine
→ config
→ outputs
