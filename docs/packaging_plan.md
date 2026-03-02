# MDCpip – Packaging & Final Shape Plan

This document describes the intended “finished” shape of MDCpip as a **Python package** and **CLI tool**, and clarifies the role of config, examples, and Adam’s personal `working/` folder.

The aim is to make it easy for others to install and use MDC SPC tooling without inheriting local dev clutter.

---

## 1. High-level goals

When MDCpip is installed (e.g. via `pip install mdcspc`), users should have:

1. A reusable **Python API**:
   - `from mdcspc.exporter import export_spc_from_csv`
   - Possibly also: `from mdcspc import analyse_xmr_by_group, summarise_xmr_by_group`, etc.

2. A simple **command-line interface** (CLI), for example:
   ```bash
   mdcspc-export input.csv --output-dir outputs/
