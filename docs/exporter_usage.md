# SPC Exporter – Usage & Configuration

This document explains how to run `mdcspc` to generate MDC-style SPC outputs (currently **XmR**, with a default of **X-only** charts), how configuration works, and what files you get out the other end.

---

## What you get

Given long-format time-series data, `mdcspc` will:

- run XmR analysis per series (special-cause rules)
- classify variation/assurance and pick MDC-style icons
- write:
  - a **summary CSV** (one row per series)
  - one **PNG chart per series** in a `charts/` folder

---

## Inputs

### CSV input (export-csv)

A typical input file has these columns:

- `MetricName` (required)
- `Month` (required; despite the name it can be any date frequency)
- `Value` (required)
- optional extra grouping columns (recommended), e.g. `OrgCode`, `Region`, etc.

Example (long format):

```text
MetricName,OrgCode,Month,Value
4hr A&E,ABC,2024-01-01,71.2
4hr A&E,ABC,2024-02-01,69.8
4hr A&E,XYZ,2024-01-01,75.1
...