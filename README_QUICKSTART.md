# mdcspc — Quick Start Guide

This guide explains how to use mdcspc in simple terms.

It assumes you are an NHS analyst who just wants results, not a technical setup guide.

---

# What this tool does

mdcspc helps you:

- turn your data into SPC (XmR) charts
- spot unusual changes in data over time
- generate simple summaries of patterns
- apply consistent NHS Making Data Count rules

You give it data → it gives you charts and summaries.

---

# What you need first

You need:

- A CSV file with data (Excel export is fine)
- At least:
  - a date column
  - a numeric value column

Example:

Month,Value
2024-01,10
2024-02,12

---

## Step 1 — Install (usually done once)

To use MDCSPC, you must first get the project onto your machine.

This can be done in one of two ways:

### Option A — If you have been given the project folder directly

Open a terminal in the project folder and run:

    pip install -e .

This installs the tool locally so the `mdcspc` command becomes available.

---

### Option B — If you are using Git

Clone the repository first:

    git clone https://github.com/sa132-imp/mdcspc.git
    cd mdcspc

Then install:

    pip install -e .

# Step 2 — Run a simple chart

mdcspc export-csv --input your_data.csv --out output_folder

This will:

- analyse your data
- build SPC charts
- create summary files

---

# Step 3 — Find your results

Look in the output folder you chose.

You will see:

- charts (PNG images)
- summary CSV files

---

# Step 4 — Understand the chart

Each chart shows:

- your data over time
- a centre line (average)
- upper and lower control limits
- signals when something unusual happens

---

# Optional: using setup wizard (advanced)

mdcspc wizard --input your_data.csv --out-config config_folder

This is optional and only needed for advanced configuration.

---

# Common mistakes

My chart looks blank or weird:
- usually not enough data
- or wrong column format

I get an error about columns:
- you need a date column
- and a numeric value column

Nothing appears in output folder:
- check file path
- check write permissions

---

# Key idea

You do NOT need to understand statistics to use this tool.

Just:
1. give it data
2. run command
3. read chart

---

# Support

If something fails, copy the error message and send it to your analytics support team.