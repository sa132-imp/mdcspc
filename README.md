# mdcspc

Python package for generating NHS England Making Data Count style statistical process control (SPC) outputs.

`mdcspc` provides a practical Python workflow for analysts who want to create SPC XmR charts, apply consistent special cause detection rules, and generate repeatable outputs from analytical data.

The package is designed around long-format time-series data and supports:

* CSV workflows through the command line
* pandas DataFrame workflows through Python
* optional SQLite workflows for lightweight local database use
* XmR SPC calculations
* special cause detection rules
* SPC chart generation
* summary output files
* configuration-driven analysis

The intended users are NHS analysts and analytical teams who want to use SPC methods consistently without needing to build their own implementation.

SPC charts and detected signals should be treated as prompts for investigation and learning. They do not automatically prove that performance has improved or deteriorated.

---

## Quick start

If you are new to `mdcspc`, start with the Quick Start Guide:

`README_QUICKSTART.md`

The Quick Start Guide covers the first workflow:

1. Prepare data
2. Install the package
3. Generate SPC outputs
4. Review charts and summary files

This README provides the full technical reference, including supported workflows, configuration, commands, and advanced usage.

---

## Background

Statistical process control (SPC) is a method for understanding variation in processes over time.

Traditional reporting often compares measures against fixed thresholds, targets, or previous periods. While these approaches can be useful, they may not distinguish between:

* expected variation that is part of the normal process
* unusual variation that may indicate something has changed

The Making Data Count approach promotes the use of SPC methods to support better understanding of variation and improvement conversations.

`mdcspc` provides a Python implementation of this approach, allowing analysts to create consistent SPC outputs from existing analytical workflows.

The package is designed to support practical analytical use cases including:

* operational reporting
* quality improvement work
* recurring performance monitoring
* analytical pipelines producing multiple SPC charts

---

## Current scope

The first draft release of `mdcspc` currently focuses on XmR SPC analysis.

The package supports:

### Analysis

* XmR charts
* centre line calculation
* control limits
* special cause detection
* improvement direction handling

### Inputs

Supported input routes:

* CSV files
* pandas DataFrames
* SQLite queries

### Outputs

Generated outputs include:

* SPC charts as PNG images
* summary CSV files
* analysis results for review and further processing

### Configuration

Settings can be controlled through CSV configuration files.

Configuration supports:

* metric-level settings
* improvement direction
* phase recalculation points
* chart annotations
* target settings

---

## Who this package is for

### NHS analysts

The simplest workflow is usually:

1. Prepare data from an existing source
2. Save or export the data in a supported format
3. Run `mdcspc`
4. Review charts and summaries

Many NHS analytical workflows begin with data stored in:

* Excel workbooks
* reporting systems
* SQL databases
* analytical platforms

For command-line use, data should normally be exported to CSV first.

For more advanced workflows, data can be queried and prepared in Python before being passed to `mdcspc` as a pandas DataFrame.

---

### Analytical teams

Teams producing repeated SPC outputs can use configuration files to create consistent and reproducible workflows.

Examples include:

* standard chart settings
* different improvement directions for different measures
* predefined phase changes
* reusable production workflows

---

### Users learning SPC

`mdcspc` helps apply SPC calculations consistently, but it does not replace understanding of SPC principles.

Users should consider:

* what their measure represents
* what improvement means for that measure
* whether detected signals are meaningful in context

---

## Installation

### Requirements

`mdcspc` requires:

- Python 3.10 or later
- pip
- a working Python environment

The package has been developed and tested on Python 3.13.

Using a virtual environment is recommended, particularly when using the package alongside other analytical tools.

---

### Install from a local project folder

If the repository has already been downloaded:

```bash
pip install -e .
```

This installs the package in editable mode.

After installation, the command line interface is available:

```powershell
mdcspc --help
```

---

### Install from GitHub

Clone the repository:

```bash
git clone https://github.com/sa132-imp/mdcspc.git
```

Move into the project folder:

```bash
cd mdcspc
```

Install:

```bash
pip install -e .
```

---

### Verify installation

Run:

```powershell
mdcspc --help
```

The installed command is the recommended way to use the package.

A Python module fallback is also available:

```powershell
python -m mdcspc.cli --help
```

Do not use:

```powershell
python -m src.mdcspc.cli
```

as normal package usage. This is only a repository development shortcut.

---
## How `mdcspc` works

The overall workflow is:

```
Input data
    |
    v
Identify metric series
    |
    v
Apply configuration settings
    |
    v
Calculate SPC statistics
    |
    v
Apply special cause rules
    |
    v
Generate charts and summary files
```

The package is designed around long-format analytical data.

Each row represents one observation for a metric at a point in time.

Example:

| Period     | Value | MetricName | Group          |
| ---------- | ----: | ---------- | -------------- |
| 2024-01-01 |  9578 | ED_Attends | Organisation A |
| 2024-02-01 |  9396 | ED_Attends | Organisation A |
| 2024-03-01 |  9955 | ED_Attends | Organisation A |

Rows with the same metric and grouping values are analysed as a single SPC series.

---

## Data model

### Long-format data

`mdcspc` expects data in long format.

Long format means each measurement is stored as a separate row rather than having separate columns for each month, week, or organisation.

Recommended structure:

| Column     | Purpose                                        |
| ---------- | ---------------------------------------------- |
| Period     | Date or reporting period                       |
| Value      | Numeric measure being analysed                 |
| MetricName | Name of the metric                             |
| Group      | Organisation, service, team, or other grouping |

Example:

```csv
Period,Value,MetricName,Group
2024-01-01,9578,ED_Attends,Organisation A
2024-02-01,9396,ED_Attends,Organisation A
2024-03-01,9955,ED_Attends,Organisation A
```

---

### Required data fields

#### Period

The date or reporting period for the observation.

Examples:

* day
* week
* month
* reporting period

Examples of valid values:

```
2024-01-01
2024-01
Jan-24
```

The field should represent when the measurement occurred.

---

#### Value

The numeric value being analysed.

Examples:

* counts
* rates
* percentages
* durations
* waiting times

Values must be stored as numbers.

For example:

Correct:

```
95
```

or:

```
0.95
```

Incorrect:

```
95%
```

---

#### MetricName

The name or identifier of the measure.

Examples:

```
ED_Attends
RTT_18_Week
Patient_Experience
```

When multiple metrics exist in the same dataset, each metric is treated as a separate SPC series.

---

#### Group

The organisation, service, team, site, or other grouping identifier.

Examples:

```
Trust A
Ward 5
Community Team North
```

When multiple groups exist, each metric/group combination is analysed separately.

#### OrgCode

`OrgCode` is an optional identifier used when data contains formal organisation codes.

It can be used alongside `Group`:

* OrgCode for formal organisational identifiers
* Group for wider categories such as teams, services, or other groupings

When present, OrgCode can be used as part of the series grouping behaviour.

---

## Grouping behaviour

`mdcspc` supports multiple series within the same dataset.

A series is identified using recognised grouping columns.

The package currently recognises:

1. `OrgCode`
2. `Group`
3. `MetricName`

These columns are detected automatically when present.

---

### Why only recognised grouping columns are used

Analytical datasets often contain additional fields that describe the data but should not create separate SPC charts.

Examples:

* source system identifiers
* extraction dates
* notes fields
* metadata columns

`mdcspc` does not automatically treat every additional column as a grouping variable.

Only recognised grouping columns are used for automatic series detection.

---

### Single-series fallback

If no recognised grouping columns are present, the package treats the dataset as a single series.

For example:

```csv
Month,Value
2024-01,100
2024-02,105
2024-03,102
```

can still be analysed as one SPC chart.

---

## Improvement direction

SPC signals can have different interpretations depending on the measure.

For example:

* higher values may represent improvement for one metric
* lower values may represent improvement for another

`mdcspc` supports three improvement direction settings:

| Direction | Meaning                                    |
| --------- | ------------------------------------------ |
| `higher`  | Higher values are considered improvement   |
| `lower`   | Lower values are considered improvement    |
| `neutral` | Direction is not automatically interpreted |

---

### Command-line direction

When using CSV export:

```powershell
mdcspc export-csv --input data.csv --out output --direction higher
```

The direction applies to every series in that CSV.

This works well when the dataset contains one metric or multiple metrics with the same interpretation.

---

### Different directions for different metrics

If a dataset contains multiple metrics with different improvement directions, use configuration files.

Example:

| Metric               | Direction |
| -------------------- | --------- |
| Patient satisfaction | higher    |
| Waiting time         | lower     |

Configuration files allow each metric to have its own behaviour.

---

## SPC calculations

`mdcspc` currently focuses on XmR charts.

XmR charts contain:

### Data points

The observed values over time.

### Centre line

The average level of the process.

### Control limits

Expected variation boundaries calculated from the process data.

These help distinguish between:

* normal variation
* unusual variation

---

## Special cause detection

The package applies special cause rules based on Making Data Count style SPC interpretation.

Detected signals include:

### Astronomical point

A single point outside the control limits.

This may indicate something unusual has occurred.

---

### Shift

A run of consecutive points consistently above or below the centre line.

A shift may suggest the process has changed.

---

### Trend

A sequence of consecutive points consistently increasing or decreasing.

A trend may indicate a sustained movement in the process.

---

### Two out of three near a limit

A pattern where two out of three consecutive points are close to a control limit.

This can indicate unusual process behaviour.

---

## Interpreting SPC outputs

SPC signals are not automatic conclusions.

A signal does not mean:

* performance has definitely improved
* performance has definitely worsened
* a specific cause has been identified

Instead, signals should prompt questions such as:

* What changed in the process?
* Was there an intervention?
* Was there a change in demand?
* Did data collection change?
* Does this represent meaningful improvement?

The context of the measure and process remains essential.

---

## Low-data behaviour

SPC limits require enough observations to estimate variation.

By default, `mdcspc` requires:

```
10 points
```

to calculate SPC limits.

Where a series has fewer than 10 observations:

* control limits are not calculated
* special cause rules are not applied
* outputs identify the series as having insufficient data

Users should generally aim for at least 15 data points where possible, following Making Data Count recommendations.

---
## Input workflows

`mdcspc` supports three main input routes:

1. CSV files through the command line
2. pandas DataFrames through Python
3. SQLite queries for lightweight local database workflows

The recommended route depends on where your data already exists.

---

## CSV workflow

The CSV workflow is the simplest and most accessible route.

Use this when:

* your data is already available as a spreadsheet
* you can export data from another system
* you want to run SPC analysis from the command line

A typical workflow is:

1. Prepare your data
2. Save or export it as CSV
3. Run `mdcspc export-csv`
4. Review charts and summaries

Example:

```powershell
mdcspc export-csv --input data.csv --out output
```

---

### CSV requirements

A CSV file should contain:

* one period/date column
* one numeric value column
* optional metric and grouping columns

Recommended structure:

```csv
Period,Value,MetricName,Group
2024-01-01,9578,ED_Attends,Organisation A
2024-02-01,9396,ED_Attends,Organisation A
2024-03-01,9955,ED_Attends,Organisation A
```

---

### CSV column detection

`mdcspc` attempts to identify columns automatically.

For more control, columns can be specified manually.

Example:

```powershell
mdcspc export-csv `
    --input data.csv `
    --out output `
    --index-col Month `
    --value-col Measure
```

Where:

* `--index-col` specifies the period/date column
* `--value-col` specifies the numeric measure column

---

## pandas DataFrame workflow

For more advanced analytical workflows, using a pandas DataFrame may be preferable.

This is likely to be the best approach when data has already been:

* extracted from a database
* joined with other datasets
* cleaned
* filtered
* transformed in Python

The general workflow is:

1. Query or prepare data using your normal analytical tools
2. Create a pandas DataFrame
3. Pass the DataFrame to `mdcspc`
4. Generate SPC outputs

This approach avoids unnecessary intermediate files and fits well into reproducible analytical pipelines.

### Example DataFrame

A DataFrame should follow the same long-format structure as CSV input.

```python
import pandas as pd

df = pd.DataFrame(
    {
        "Period": [
            "2024-01-01",
            "2024-02-01",
            "2024-03-01"
        ],
        "Value": [
            9578,
            9396,
            9955
        ],
        "MetricName": [
            "ED_Attends",
            "ED_Attends",
            "ED_Attends"
        ],
        "Group": [
            "Organisation A",
            "Organisation A",
            "Organisation A"
        ]
    }
)
```

### Run SPC analysis from a DataFrame

Once your data has been prepared as a pandas DataFrame, pass it to `mdcspc` using `export_spc_from_dataframe`.

```python
from mdcspc.exporter_dataframe import export_spc_from_dataframe

summary, results = export_spc_from_dataframe(
    df,
    working_dir="output",
    index_col="Period",
    value_col="Value"
)
```

This writes the same style of outputs as the CSV workflow:

```text
output/
|
├── charts/
|
└── spc_summary_from_input.csv
```

The function returns:

* `summary` — a pandas DataFrame containing the per-series summary results
* `results` — the SPC analysis results object

Useful optional arguments include:

| Argument           | Purpose                                        |
| ------------------ | ---------------------------------------------- |
| `working_dir`      | Output folder                                  |
| `config_dir`       | Optional folder containing configuration files |
| `value_col`        | Name of the numeric value column               |
| `index_col`        | Name of the period/date column                 |
| `summary_filename` | Name of the summary CSV file                   |
| `charts_subdir`    | Name of the chart output subfolder             |
| `chart_mode`       | Chart mode, such as `x_only` or `xmr`          |
| `quiet`            | Suppress normal console output                 |

For example, to use a configuration folder:

```python
summary, results = export_spc_from_dataframe(
    df,
    working_dir="output",
    config_dir="config",
    index_col="Period",
    value_col="Value"
)
```

## SQLite workflow

SQLite input is available for lightweight local database workflows.

It can be useful for:

* reproducible local extracts
* testing
* small analytical databases

It is not intended to represent the typical NHS enterprise database workflow.

For larger database environments, the recommended approach is usually:

1. Query data using existing database tools
2. Prepare the dataset
3. Pass the resulting CSV or DataFrame to `mdcspc`

---

### SQLite export example

```powershell
mdcspc export-sqlite `
    --db path/to/data.db `
    --query "SELECT Period, Value, MetricName FROM measures" `
    --out output
```

The query should return data in a structure suitable for SPC analysis.

---

## Command line reference

The main CLI commands are:

| Command          | Purpose                                 |
| ---------------- | --------------------------------------- |
| `export-csv`     | Generate SPC outputs from CSV           |
| `export-sqlite`  | Generate SPC outputs from SQLite        |
| `wizard`         | Create starter configuration files      |
| `init-config`    | Create empty configuration templates    |
| `explain-config` | Explain configuration loading behaviour |
| `recalc-wizard`  | Add phase recalculation settings        |

---

## `export-csv`

Generates SPC outputs from a CSV file.

Basic usage:

```powershell
mdcspc export-csv --input data.csv --out output
```

---

### Options

#### `--input`

Path to the input CSV file.

Example:

```powershell
--input "C:\data\metrics.csv"
```

---

#### `--out`

Folder where outputs will be created.

Example:

```powershell
--out "C:\outputs\spc"
```

---

#### `--config-dir`

Optional folder containing configuration files.

Example:

```powershell
--config-dir config
```

Configuration allows more control over:

* metric settings
* improvement direction
* phases
* targets
* annotations

---

#### `--direction`

Sets the improvement direction.

If `--direction` is not provided, the default is `neutral`.

Options:

```text
higher
lower
neutral
```

Example:

```powershell
--direction lower
```

Meaning:

* `higher`: increasing values are interpreted as improvement
* `lower`: decreasing values are interpreted as improvement
* `neutral`: no automatic improvement interpretation

This setting applies to all series in the CSV.

For datasets containing metrics with different directions, use configuration files.

---

#### `--index-col`

Specifies the period/date column.

Example:

```powershell
--index-col Month
```

---

#### `--value-col`

Specifies the measure column.

Example:

```powershell
--value-col Number
```

---

#### `--chart-mode`

Controls chart generation mode.

If `--chart-mode` is not provided, the default is `x_only`. The default produces the X chart only; use `--chart-mode xmr` to generate the full XmR chart pair including the moving range chart.

Available options:

```text
xmr
x_only
```

`xmr` generates the full XmR chart.

`x_only` generates only the X chart.

---

#### `--quiet`

Suppresses normal command output.

Useful for automated workflows.

Example:

```powershell
--quiet
```

---

## `export-sqlite`

Generates SPC outputs from a SQLite database query.

Example:

```powershell
mdcspc export-sqlite `
    --db data.db `
    --query "SELECT Period, Value FROM measures" `
    --out output
```

SQLite support is intended for lightweight local workflows rather than replacing enterprise database connections.

---

## `wizard`

The wizard creates starter configuration files from an input CSV.

Example:

```powershell
mdcspc wizard `
    --input data.csv `
    --out-config config
```

The wizard is optional.

Simple workflows can use:

```powershell
mdcspc export-csv
```

without configuration.

Use the wizard when you need:

* repeatable settings
* multiple metrics
* different directions
* phase changes
* targets

---

## `init-config`

Creates empty configuration templates.

Example:

```powershell
mdcspc init-config --out config
```

Generated files include:

* `metric_config.csv`
* `spc_phase_config.csv`
* `spc_target_config.csv`

These can be edited manually.

---

## `explain-config`

Shows where configuration files are loaded from.

Example:

```powershell
mdcspc explain-config
```

This is useful when troubleshooting configuration behaviour.

---

## `recalc-wizard`

Provides a guided way to add a recalculation point to a metric.

Recalculation points are used when a process has changed and SPC limits need to be recalculated from a defined point.

Examples:

* implementation of a new process
* service redesign
* major change in measurement method

The settings created by this workflow are stored in phase configuration.

---
## Configuration system

Configuration files allow users to control how `mdcspc` handles individual metrics and analytical workflows.

Configuration is optional.

A simple CSV workflow can generate SPC outputs without any configuration files.

Configuration becomes useful when you need:

* repeatable production workflows
* multiple metrics with different settings
* different improvement directions
* phase recalculation points
* chart annotations
* target information

The recommended workflow is:

1. Generate starter configuration
2. Review the configuration files
3. Edit settings as required
4. Rerun the analysis using the configuration

---

## Configuration files

`mdcspc` uses three main configuration files:

| File                    | Purpose                                |
| ----------------------- | -------------------------------------- |
| `metric_config.csv`     | Metric-level settings                  |
| `spc_phase_config.csv`  | Phase changes and recalculation points |
| `spc_target_config.csv` | Target settings                        |

Configuration files are CSV files so they can be edited using:

* Excel
* text editors
* other spreadsheet software

---

## Configuration directory

A configuration directory contains the CSV files used during analysis.

Example:

```text
config/
|
├── metric_config.csv
├── spc_phase_config.csv
└── spc_target_config.csv
```

Pass a configuration directory using:

```powershell
mdcspc export-csv `
    --input data.csv `
    --out output `
    --config-dir config
```

---

## Creating configuration files

There are two main approaches.

### Using the wizard

The wizard creates starter configuration based on an input dataset.

Example:

```powershell
mdcspc wizard `
    --input data.csv `
    --out-config config
```

This is useful when:

* starting a new analytical workflow
* working with multiple metrics
* wanting a guided setup

---

### Creating templates manually

Templates can also be created:

```powershell
mdcspc init-config --out config
```

This creates blank configuration files that can be edited manually.

This approach may be preferable for experienced users managing larger analytical processes.

---

## metric_config.csv

The metric configuration file controls metric-level behaviour.

Typical uses include:

* identifying metrics
* setting improvement direction
* controlling metric-specific options

This is particularly useful where different metrics in the same dataset behave differently.

For example:

| Metric               | Direction |
| -------------------- | --------- |
| Patient satisfaction | higher    |
| Waiting time         | lower     |

A command-line `--direction` option applies one setting to all series.

Metric configuration allows more detailed control.

---

## spc_phase_config.csv

The phase configuration file controls recalculation points and chart annotations.

A phase change is used when the process itself has changed and historical variation may no longer represent the current process.

Examples:

* introduction of a new pathway
* service redesign
* major operational change
* change in data collection method

A phase configuration entry defines where recalculation begins.

Current structure:

```csv
OrgCode,Group,MetricName,PhaseStart,Annotation,ShowOnChart,AnnotationPosition
```

Fields:

| Field                | Purpose                          |
| -------------------- | -------------------------------- |
| `OrgCode`            | Optional organisation identifier |
| `Group`              | Optional grouping identifier     |
| `MetricName`         | Metric being affected            |
| `PhaseStart`         | Date where the new phase begins  |
| `Annotation`         | Text shown on the chart          |
| `ShowOnChart`        | Whether annotation is displayed  |
| `AnnotationPosition` | Chart annotation position        |

---

## spc_target_config.csv

The target configuration file stores target-related information.

Targets can provide additional context alongside SPC analysis.

A target should not be confused with a control limit.

A target represents an externally defined goal or expectation.

Control limits represent expected process variation.

They answer different questions:

| Target                        | Control limits                                  |
| ----------------------------- | ----------------------------------------------- |
| What level are we aiming for? | What variation does this process normally show? |
| External expectation          | Process behaviour                               |
| Improvement goal              | Statistical signal                              |

---

## Configuration precedence

When configuration is supplied, it overrides default behaviour.

The general approach is:

1. User-provided configuration directory
2. Package default configuration resources
3. Built-in defaults

This allows:

* local customisation
* reusable team configurations
* consistent analytical workflows

Use:

```powershell
mdcspc explain-config
```

to understand configuration loading behaviour.

---

## Output structure

`mdcspc` generates output files in the folder provided through `--out`.

A typical output structure is:

```text
output/
|
├── charts/
|
└── spc_summary_from_input.csv
```

---

## Charts

SPC charts are generated as PNG image files.

Charts include:

* plotted observations
* centre line
* control limits
* special cause signals
* optional annotations and targets

Charts are designed for:

* reporting
* review
* discussion
* investigation

---

## Summary files

The summary CSV file provides structured outputs from the analysis.

They can be used for:

* further analysis
* checking results
* reporting workflows
* automated processing

Summary outputs allow users to work with the analytical results without needing to extract information manually from chart images.

---

## Advanced workflows

### Multiple metrics

A single dataset can contain multiple metrics.

Example:

```csv
Period,Value,MetricName,Group
2024-01-01,100,Admissions,Organisation A
2024-01-01,20,Readmissions,Organisation A
2024-02-01,105,Admissions,Organisation A
2024-02-01,18,Readmissions,Organisation A
```

Each metric/group combination is analysed separately.

---

### Multiple organisations

The same metric can be analysed across multiple organisations.

`OrgCode` can be used when organisations have a formal identifier. `Group` can be used for wider grouping needs such as services, teams, or other categories.

Example:

```csv
Period,Value,MetricName,OrgCode,Group
2024-01-01,100,Admissions,ORG001,Organisation A
2024-02-01,105,Admissions,ORG001,Organisation A
2024-01-01,120,Admissions,ORG002,Organisation B
2024-02-01,118,Admissions,ORG002,Organisation B
```

Each organisation/metric combination produces its own SPC series.

---

### Different improvement directions

Where multiple measures exist:

Example:

| Metric             | Direction         |
| ------------------ | ----------------- |
| Patient experience | Higher is better  |
| Waiting time       | Lower is better   |
| Incident count     | Context dependent |

Use configuration files when different metrics require different interpretations.

---

## Python API workflows

The Python workflow is intended for users who already prepare data programmatically.

Typical pattern:

```text
Data source
    |
    v
Python preparation
    |
    v
pandas DataFrame
    |
    v
mdcspc analysis
    |
    v
Outputs
```

This approach is useful when:

* data comes from a database
* complex transformations are required
* analysis forms part of a wider Python pipeline

---

## Development and testing

The repository includes automated tests covering core functionality.

Development installation:

```bash
pip install -e .
```

Run tests:

```bash
pytest
```

Current first draft verification includes:

* CSV workflows
* DataFrame workflows
* SQLite workflows
* CLI commands
* configuration workflows
* plotting behaviour

---

## Current status

`mdcspc` is currently a first draft release.

The package currently provides:

* working XmR SPC analysis
* CLI workflows
* CSV, DataFrame and SQLite inputs
* configuration-driven behaviour
* automated testing

Documentation and features may continue to evolve as the package develops.

---

## Troubleshooting

This section covers common issues and checks when using `mdcspc`.

---

## Installation problems

### `mdcspc` command is not recognised

If the terminal reports that `mdcspc` is not recognised, check:

* the package installation completed successfully
* the terminal is using the correct Python environment
* your virtual environment is activated if you are using one

Check the installation:

```powershell
mdcspc --help
```

If this fails, try:

```powershell
python -m mdcspc.cli --help
```

If the Python module command works but `mdcspc` does not, the issue is likely related to the Python environment path.

---

## Input data problems

### The package cannot identify columns

`mdcspc` attempts to detect the required columns automatically.

If your columns have different names, specify them manually.

Example:

```powershell
mdcspc export-csv `
    --input data.csv `
    --out output `
    --index-col ReportingMonth `
    --value-col MeasureValue
```

Check that:

* the period column contains dates or date-like values
* the value column contains numeric data
* column names match the options provided

---

### Charts contain no SPC limits

This usually means there is insufficient data.

SPC limits require enough observations to estimate variation.

By default:

* fewer than 10 points → no SPC limits calculated
* special cause rules are not applied

Where possible, use longer time series to provide enough information about the process.

---

### Values are not being interpreted correctly

Check that numeric fields contain numbers only.

Correct:

```csv
Period,Value
2024-01-01,95
```

Incorrect:

```csv
Period,Value
2024-01-01,95%
```

Percentages, rates and durations should be stored as numeric values.

---

## Grouping problems

### Too many charts are created

Check whether your dataset contains recognised grouping columns.

`mdcspc` uses:

* `OrgCode`
* `Group`
* `MetricName`

to identify separate series.

It does not automatically use every column in the dataset as a grouping variable.

If unexpected charts are created, check these fields.

---

### I expected multiple charts but only got one

Check that your dataset contains the grouping fields required.

For example:

```csv
Period,Value,MetricName,Group
2024-01-01,100,Admissions,Organisation A
2024-01-01,120,Admissions,Organisation B
```

creates separate series because the groups differ.

If the dataset only contains:

```csv
Period,Value
2024-01-01,100
2024-02-01,120
```

it will be treated as a single series.

---

## Configuration problems

### My configuration changes are not being applied

Check:

1. The correct folder is supplied:

```powershell
--config-dir config
```

2. The CSV files have the expected names:

```text
metric_config.csv
spc_phase_config.csv
spc_target_config.csv
```

3. The configuration values match the metric and grouping values in your data.

Use:

```powershell
mdcspc explain-config
```

to review configuration behaviour.

---

### Different metrics need different improvement directions

Do not use:

```powershell
--direction
```

for this situation.

The command-line option applies one direction to all series.

Instead, use metric configuration.

Example:

| Metric               | Direction |
| -------------------- | --------- |
| Patient satisfaction | higher    |
| Waiting time         | lower     |

---

## Output problems

### Output folder is empty

Check:

* the command completed successfully
* the output path is correct
* you have write permission
* you are checking the folder specified by `--out`

Relative paths are created from the folder where the command was run.

Example:

```powershell
--out outputs
```

creates:

```text
current-folder/
└── outputs/
```

---

## Support

For support queries, provide:

* the command used
* the error message
* sample input data structure
* column names
* configuration files if relevant

Support contact:

[england.makingdatacount@nhs.net](mailto:england.makingdatacount@nhs.net)

When reporting issues, include enough information to reproduce the problem where possible.

---
## Reproducibility recommendations

For repeatable analytical workflows:

* store input datasets with clear versions
* keep configuration files under version control
* record the package version used
* retain generated outputs where appropriate
* document any phase changes or analytical decisions

A reproducible SPC workflow should make it clear:

* what data was analysed
* what settings were used
* when the analysis was produced

---

## Limitations and considerations

`mdcspc` is designed as a practical analytical tool, but users should consider:

### SPC is not automated judgement

Signals indicate patterns that may require investigation.

They do not identify causes automatically.

---

### Context remains essential

A statistical signal may be caused by:

* genuine process change
* seasonal effects
* data quality issues
* recording changes
* temporary operational events

Analysts should interpret outputs alongside operational knowledge.

---

### First draft scope

Current scope focuses on XmR charts.

Future development may expand functionality, but users should treat the current package as a first draft implementation.

---

## Project information

Repository:

`https://github.com/sa132-imp/mdcspc`

Current release:

`0.2.0`

Development status:

First draft release

---

## Licence

See the repository licence for current licensing information.