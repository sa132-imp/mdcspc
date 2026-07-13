# mdcspc — Quick Start Guide

This guide explains how to use `mdcspc` in simple terms.

It is written for analysts who want to turn data into SPC charts without having to understand the technical details first.

This package uses the NHS England Making Data Count approach, which supports better use of statistical process control instead of RAG reporting. You can find more about the programme on the [Making Data Count FutureNHS workspace](https://future.nhs.uk/connect.ti/MDC/groupHome).

---

# What this tool does

`mdcspc` helps you:

* turn your data into SPC XmR charts
* spot unusual changes in data over time
* generate simple summaries of patterns
* apply consistent NHS Making Data Count rules

You give it data. It gives you charts and summaries.

---

# What you need first

For this quickstart, you need a CSV file with data in it.

A lot of data might be in Excel spreadsheets. That is fine, but for this quickstart you need to save or export the Excel sheet as a `.csv` file first. This package does not read Excel workbook files such as `.xlsx` directly from the command line.

However, `mdcspc` can also be used in more advanced Python workflows, where data has already been queried, cleaned, and prepared as a pandas DataFrame. This is likely to be the best route when your source data comes from a larger database or data warehouse. Other input methods and more advanced workflows are covered in the full README, but this guide starts with CSV because it is the simplest first workflow.

For the recommended workflow, your CSV should have these columns:

* `Period` — the date or reporting period being measured, such as a day, week, or month.
* `Value` — the number you want to chart
* `MetricName` — the name of what is being measured
* `Group` — the ward, site, service, specialty, team, organisation, or other group being charted

Rows with the same `MetricName` and `Group` are treated as one series and produce one chart. Different `MetricName` or `Group` values produce separate charts.

Each series needs at least 10 data points to calculate SPC limits but should aim for 15+ data points as per MDC programme recommendation.

Data should be in these formats:

* `Period` should be a date or date-like value, for example `2024-01-01`
* `Value` should be numeric, such as an integer, decimal, percentage, rate, or time value
* `MetricName` should be text
* `Group` should be text

Percentages, rates, and time values should still be stored as numbers in the CSV. For example, use `0.95` or `95`, not `95%`.

For example:
```csv
Period,Value,MetricName,Group
2024-01-01,9578,ED_Attends,Org A
2024-02-01,9396,ED_Attends,Org A
2024-03-01,9955,ED_Attends,Org A
2024-04-01,9453,ED_Attends,Org A
2024-05-01,9069,ED_Attends,Org A
2024-06-01,9453,ED_Attends,Org A
2024-07-01,9791,ED_Attends,Org A
2024-08-01,9181,ED_Attends,Org A
2024-09-01,9711,ED_Attends,Org A
2024-10-01,9678,ED_Attends,Org A
2024-11-01,9725,ED_Attends,Org A
2024-12-01,9888,ED_Attends,Org A
```

In this example:

* `Period` is the month date
* `Value` is the number of attends
* `MetricName` is ED attends
* `Group` says which organisation the data belongs to

This four-column structure is the recommended starting point because it makes the output easier to understand and reuse.

For the simplest possible first test, `mdcspc` can also run on a CSV with just a date column and a value column. In that case, it treats the file as one series.

---

# Step 1 — Install `mdcspc`

You usually only need to do this once.

To use `mdcspc`, the package must be installed in the Python environment you are using. This makes the `mdcspc` command available.

You need to run the install command in a terminal. This could be:

* Windows PowerShell
* Command Prompt
* The terminal inside VS Code, RStudio, Positron, PyCharm, or another coding tool

The important thing is that the terminal is using the Python environment where you want `mdcspc` to be installed.

There are two common ways to install it.

---

## Option A — You have been given the project folder

Use this option if someone has already given you the `mdcspc` project folder.

Open your terminal and move into the project folder.

The project folder is the folder that contains files such as:

    README.md
    pyproject.toml
    src

You should run the install command from inside that folder.

Then run:

    pip install -e .

Here is what this means:

* `pip` is Python’s package installer
* `install` tells Python to install something
* `-e` means editable mode, which is useful when working from a project folder
* `.` means “install the project in the current folder”

After this has finished, the `mdcspc` command should be available.

---

## Option B — You are using Git

Use this option if you need to download the project from GitHub.

Open your terminal in the folder where you want the project folder to be created.

First, clone the repository:

    git clone https://github.com/sa132-imp/mdcspc.git

This downloads the project into a new folder called:

    mdcspc

Move into that folder:

    cd mdcspc

Then install the package:

    pip install -e .

After this has finished, the `mdcspc` command should be available.

---

## Check the install worked

Run:

    mdcspc --help

If the install worked, you should see a help message showing the available `mdcspc` commands.

Each command also has its own help page. For example:

    mdcspc export-csv --help

This shows the options available when creating SPC charts from a CSV file.

If you get an error saying that `mdcspc` is not recognised, the package has not been installed correctly or your terminal is not using the right Python environment.

---

# Step 2 — Run a simple chart

Now run `mdcspc` on a CSV file.

The command below tells `mdcspc` to read a CSV file, analyse it, and save the results in an output folder.

    mdcspc export-csv --input your_data.csv --out output_folder --direction neutral

Here is what each part means:

* `mdcspc` is the command-line tool installed with this package.
* `export-csv` tells `mdcspc` that your input data is in a CSV file.
* `--input` tells `mdcspc` where your CSV file is.
* `your_data.csv` is the CSV file you want to analyse. Replace this with your actual file name or file path.
* `--direction` tells `mdcspc` how to interpret unusual changes.
  * Use `higher` when higher values are better.
  * Use `lower` when lower values are better.
  * Use `neutral` when neither higher nor lower values should automatically be treated as better.
  * The setting applies to every series in the CSV. If different metrics need different directions, use configuration files instead.
* `--out` tells `mdcspc` where to save the results.
* `output_folder` is the folder where charts and summary files will be created. Replace this with the folder name you want to use.

---

## Example 1 — Your CSV file is in the current folder

If your CSV file is called `sample_spc.csv` and it is in the folder you are currently working in, run:

    mdcspc export-csv --input sample_spc.csv --out outputs --direction neutral

This will read:

    sample_spc.csv

and save the results in a folder called:

    outputs

Because `outputs` is a relative folder name, it will be created in the folder where you run the command.

---

## Example 2 — Your CSV file is in a different folder

If your CSV file is somewhere else, give the full path to the file.

For example:

    mdcspc export-csv --input "C:\Users\your.name\Documents\sample_spc.csv" --out outputs --direction neutral

The quote marks are useful when a file path contains spaces.

This will read the CSV file from your `Documents` folder and save the results in a folder called `outputs`.

Because `outputs` is a relative folder name, the output folder will be created in the folder where you run the command, not necessarily in the same folder as the CSV file.

---

## Example 3 — Save the outputs somewhere specific

You can also give a full path for the output folder.

For example:

    mdcspc export-csv --input "C:\Users\your.name\Documents\sample_spc.csv" --out "C:\Users\your.name\Documents\mdcspc_outputs" --direction neutral

This will:

* read the CSV file from your `Documents` folder
* analyse the data
* create SPC charts
* create summary files
* save the results in `mdcspc_outputs`

After the command finishes, open the output folder and check that files have been created.

---

# Step 3 — Find your results

Look in the output folder you chose.

For example, if you used:

```powershell
mdcspc export-csv --input sample_spc.csv --out outputs --direction neutral
```

then look for a folder called:

```text
outputs
```

Inside the output folder, you should see files such as:

* chart images
* summary CSV files

The chart images are saved as PNG files. You can open these like normal image files.

The summary CSV files can be opened in Excel.

---

# Step 4 — Understand the chart

Each SPC chart shows your data over time.

It usually includes:

* the data points
* a centre line, which is the mean average
* an upper control limit
* a lower control limit
* signals showing if something unusual may have happened

You do not need to understand all the statistics to start using the chart.

The main idea is that there are two types of variation:

* common cause variation — the usual variation you would expect from a process when there is no clear signal of unusual change
* special cause variation — variation that may suggest something unusual has happened

`mdcspc` looks for four types of special-cause signal:

* an astronomical point — a point outside the control limits
* a shift — a run of points all above or all below the centre line
* a trend — a run of points all increasing or all decreasing
* two out of three points close to a control limit

`mdcspc` uses different coloured dots to show common cause variation and special-cause signals:

* grey dots show common cause variation
* blue dots show special-cause improvement
* orange dots show special-cause concern
* purple dots show special-cause change where the direction is neutral or depends on context

These signals are prompts for investigation. They do not automatically prove that performance has got better or worse.

---

# Optional — Use the setup wizard

The setup wizard is optional.

You do not need it for a simple first chart.

Use the wizard when you want help creating configuration files for more controlled or repeatable chart production.

The wizard reads the metrics in your CSV file and creates editable CSV configuration files. You can review or update these files before using them with future `mdcspc` runs.

A configuration folder contains CSV files that tell `mdcspc` how to handle your charts. These files can control things such as:

* which metrics are included
* how metrics are named in outputs
* whether higher or lower values are better
* where recalculation points or phase changes start
* whether targets are used

Configuration files are particularly useful when you are producing several charts, rerunning the same analysis later, or when different metrics need different settings. For example, one metric may improve when values increase, while another improves when values decrease.

The command is:

    mdcspc wizard --input your_data.csv --out-config config_folder

Here is what each part means:

* `mdcspc` is the command-line tool.
* `wizard` starts the setup wizard.
* `--input` tells the wizard where your CSV file is.
* `your_data.csv` is the CSV file you want to use.
* `--out-config` tells the wizard where to save the configuration files.
* `config_folder` is the folder where the configuration files will be created.

For example:

    mdcspc wizard --input sample_spc.csv --out-config config

This creates configuration files in a folder called:

    config

The configuration folder will contain files such as:

* `metric_config.csv`
* `spc_phase_config.csv`
* `spc_target_config.csv`

You can open these files in Excel or another spreadsheet tool, edit them if needed, save them as CSV files, and then use them when running `mdcspc`.

Most new users can ignore this at first and use `export-csv` directly. Move to configuration files when you need repeatable settings or different options for different metrics.

---

# Common mistakes

## “My chart looks blank or strange”

This usually means one of these things:

* there is not enough data
* the value column does not contain usable numbers
* the date/period column is not being read correctly
* the wrong column has been selected

Check that your CSV has:

* one date/period  column
* one numeric value column
* enough rows to calculate SPC limits
* valid metric and grouping columns if you are using multiple series

---

## “I get an error about columns”

This usually means `mdcspc` could not work out which columns to use.

Check your CSV file.

You need:

* a column containing dates or date-like periods (for example day, week, or month)
* a column containing the numbers you want to chart
* `MetricName` and grouping columns if you are producing multiple series

If your column names are unusual, you may need to tell `mdcspc` which columns to use.

For example:

```powershell
mdcspc export-csv --input sample_spc.csv --out outputs --index-col Month --value-col Value --direction neutral
```

Here:

* `--index-col Month` tells `mdcspc` to use the `Month` column as the date/period column
* `--value-col Value` tells `mdcspc` to use the `Value` column for the numbers

Change `Month` and `Value` to match the column names in your own CSV file.

---

## “Nothing appears in the output folder”

Check:

* the command finished without an error
* the output folder path is correct
* you have permission to write files into that folder
* the folder has not been created somewhere else because of where the terminal was opened
* you are looking in the output folder created by the `--out` option

If you used a relative folder name such as:

```text
outputs
```

then the folder will be created inside the folder where you ran the command.

---

## “The command says the file cannot be found”

Check the input path.

If the file is not in your current folder, use the full path.

For example:

```powershell
mdcspc export-csv --input "C:\Users\your.name\Documents\sample_spc.csv" --out outputs --direction neutral
```

Use quote marks around paths that contain spaces.

---

# Key idea

You do not need to understand statistics to start using `mdcspc`.

The basic workflow is:

1. prepare a CSV file
2. run `mdcspc export-csv` with the options you need
3. open the output folder
4. review the chart and summary files

Start simple. Once that works, you can move on to configuration and more advanced options.

---

# Support

`mdcspc` is currently a first draft release.

If something fails, please report it using:

england.makingdatacount@nhs.net

When reporting a problem, include:

* the command you ran
* the error message
* the first few rows of your CSV file
* the column names in your CSV file

This information will help diagnose problems and improve future versions of the package.