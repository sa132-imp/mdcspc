# mdcspc — Quick Start Guide

This guide explains how to use `mdcspc` in simple terms.

It is written for NHS analysts who want to turn data into SPC charts without having to understand the technical details first.

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

You need a CSV file with data in it.

A CSV file is a simple data file. You can create one by saving or exporting data from Excel as a `.csv` file.

Your data should have at least:

* one column for time, such as month, week, date, or period
* one column containing the numbers you want to chart

For example:

```csv
Month,Value
2024-01,10
2024-02,12
2024-03,11
2024-04,14
```

In this example:

* `Month` is the time column
* `Value` is the number column

Your CSV can contain extra columns, but the simplest first test is to start with just the time column and value column. Once that works, you can try a larger file.

The tool needs enough data points to calculate SPC limits.

---

# Step 1 — Install `mdcspc`

You usually only need to do this once.

To use `mdcspc`, the package must be installed on your machine so that the `mdcspc` command is available.

There are two common ways to do this.

---

## Option A — You have been given the project folder

Use this option if someone has already given you the `mdcspc` project folder.

Open a terminal in the project folder.

The project folder is the folder that contains files such as:

```text
README.md
pyproject.toml
src
```

Then run:

```powershell
pip install -e .
```

Here is what this means:

* `pip` is Python’s package installer
* `install` tells Python to install something
* `-e` means editable mode, which is useful when working from a project folder
* `.` means “install the project in the current folder”

After this has finished, the `mdcspc` command should be available.

---

## Option B — You are using Git

Use this option if you need to download the project from GitHub.

First, clone the repository:

```powershell
git clone https://github.com/sa132-imp/mdcspc.git
```

This downloads the project into a new folder called:

```text
mdcspc
```

Move into that folder:

```powershell
cd mdcspc
```

Then install the package:

```powershell
pip install -e .
```

After this has finished, the `mdcspc` command should be available.

---

## Check the install worked

Run:

```powershell
mdcspc --help
```

If the install worked, you should see a help message showing the available `mdcspc` commands.

If you get an error saying that `mdcspc` is not recognised, the package has not been installed correctly or your terminal is not using the right Python environment.

---

# Step 2 — Run a simple chart

Now run `mdcspc` on a CSV file.

The command below tells `mdcspc` to read a CSV file, analyse it, and save the results in an output folder.

```powershell
mdcspc export-csv --input your_data.csv --out output_folder
```

Here is what each part means:

* `mdcspc` is the command-line tool installed with this package.
* `export-csv` tells `mdcspc` that your input data is in a CSV file.
* `--input` tells `mdcspc` where your CSV file is.
* `your_data.csv` is the CSV file you want to analyse. Replace this with your actual file name or file path.
* `--out` tells `mdcspc` where to save the results.
* `output_folder` is the folder where charts and summary files will be created. Replace this with the folder name you want to use.

---

## Example 1 — Your CSV file is in the current folder

If your CSV file is called `sample_spc.csv` and it is in the folder you are currently working in, run:

```powershell
mdcspc export-csv --input sample_spc.csv --out outputs
```

This will read:

```text
sample_spc.csv
```

and save the results in a folder called:

```text
outputs
```

---

## Example 2 — Your CSV file is in a different folder

If your CSV file is somewhere else, give the full path to the file.

For example:

```powershell
mdcspc export-csv --input "C:\Users\your.name\Documents\sample_spc.csv" --out outputs
```

The quote marks are useful when a file path contains spaces.

---

## Example 3 — Save the outputs somewhere specific

You can also give a full path for the output folder.

For example:

```powershell
mdcspc export-csv --input "C:\Users\your.name\Documents\sample_spc.csv" --out "C:\Users\your.name\Documents\mdcspc_outputs"
```

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
mdcspc export-csv --input sample_spc.csv --out outputs
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
* a centre line, which is the average
* an upper control limit
* a lower control limit
* signals showing when something unusual may have happened

You do not need to understand all the statistics to start using the chart.

The main idea is:

* points inside the limits usually show normal variation
* points or patterns outside the expected range may suggest something unusual has happened
* unusual signals are worth investigating, not automatically treating as good or bad

---

# Optional — Use the setup wizard

The setup wizard is optional.

You do not need it for a simple first chart.

Use the wizard when you want help creating a configuration folder for more controlled or repeatable chart production.

The command is:

```powershell
mdcspc wizard --input your_data.csv --out-config config_folder
```

Here is what each part means:

* `mdcspc` is the command-line tool
* `wizard` starts the setup wizard
* `--input` tells the wizard where your CSV file is
* `your_data.csv` is the CSV file you want to use
* `--out-config` tells the wizard where to save the configuration files
* `config_folder` is the folder where the configuration files will be created

For example:

```powershell
mdcspc wizard --input sample_spc.csv --out-config config
```

This creates configuration files in a folder called:

```text
config
```

Most new users can ignore this at first and just use `export-csv`.

---

# Common mistakes

## “My chart looks blank or strange”

This usually means one of these things:

* there is not enough data
* the value column does not contain usable numbers
* the time column is not being read correctly
* the wrong column has been selected

Check that your CSV has:

* one time column
* one numeric value column
* enough rows to calculate SPC limits

---

## “I get an error about columns”

This usually means `mdcspc` could not work out which columns to use.

Check your CSV file.

You need:

* a column for time, date, month, week, or period
* a column containing the numbers you want to chart

If your column names are unusual, you may need to tell `mdcspc` which columns to use.

For example:

```powershell
mdcspc export-csv --input sample_spc.csv --out outputs --index-col Month --value-col Value
```

Here:

* `--index-col Month` tells `mdcspc` to use the `Month` column for time
* `--value-col Value` tells `mdcspc` to use the `Value` column for the numbers

Change `Month` and `Value` to match the column names in your own CSV file.

---

## “Nothing appears in the output folder”

Check:

* the command finished without an error
* the output folder path is correct
* you have permission to write files into that folder
* the folder has not been created somewhere else because of where the terminal was opened

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
mdcspc export-csv --input "C:\Users\your.name\Documents\sample_spc.csv" --out outputs
```

Use quote marks around paths that contain spaces.

---

# Key idea

You do not need to understand statistics to start using `mdcspc`.

The basic workflow is:

1. prepare a CSV file
2. run `mdcspc export-csv`
3. open the output folder
4. review the chart and summary files

Start simple. Once that works, you can move on to configuration and more advanced options.

---

# Support

If something fails, copy:

* the command you ran
* the error message
* the first few rows of your CSV file
* the column names in your CSV file

Send these to your analytics support team or whoever supports your local use of `mdcspc`.
