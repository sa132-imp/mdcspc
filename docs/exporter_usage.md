# SPC Exporter – Usage & Configuration

This document explains how to use the SPC exporter in this repo, how the config files fit together, and what the inputs/outputs look like.

The exporter is implemented in:

- `mdcspc/exporter.py` (library API)
- `scripts/export_spc_from_csv.py` (CLI wrapper)

---

## 1. What the exporter does

Given a long-format CSV of metric data, the exporter will:

1. Run multi-series XmR analysis (one chart per series).
2. Apply MDC-style colouring and classification:
   - Common cause vs special cause
   - Improvement vs concern vs neutral
   - Assurance based on target vs limits
3. Save:
   - A **summary CSV** (one row per series) with MDC-friendly fields.
   - One **PNG XmR chart** per series with coloured dots and icons.

---

## 2. Input data (the main CSV)

By default, the script uses:

```text
working/ae4hr_multi_org_example.csv
