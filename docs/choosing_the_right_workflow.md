# Choosing the Right Workflow

`mdcspc` is a config-driven SPC tool with optional guided helpers.

That means there is not one single mandatory route through the package. Users can either use helper wizards or work directly in the config CSV files, depending on the size and complexity of the job.

## The overall workflow

The intended user journey is:

1. Bring in data from CSV or DataFrame
2. Identify which metrics exist in the input
3. Choose either:
   - a guided config route using a wizard, or
   - a manual config route by editing config CSVs directly
4. Run the tool to generate charts and summary tables
5. Review the outputs
6. If needed, add recalculation points
7. Rerun the outputs
8. Recalcs persist until changed or removed

## Which route should I use?

### Use the setup wizard when:
- you are starting with a new dataset
- you want help creating starter config
- you only have a small number of metrics
- you want the tool to step through the metrics it finds

This is the guided route.

### Edit config CSVs directly when:
- you already know what you want to chart
- you have lots of metrics
- you want speed and full control
- you are a bulk or power-user

This is the manual route.

Both are valid. Neither should be treated as the only proper way to use the package.

## What each command is for

### `wizard`
Use this for initial setup from an input CSV.

Purpose:
- inspect the input data
- identify available metrics
- help create starter config files

Think of this as:

> Help me set up config for a new piece of work.

### `init-config`
Use this when you want blank/default config templates written out.

Purpose:
- create the standard config files
- let you fill them in manually

Think of this as:

> Give me the config structure and I will edit it myself.

### `recalc-wizard`
Use this after outputs have been generated and reviewed, when you want to add a recalculation point.

Purpose:
- add or update entries in the phase/recalc config
- support chart refinement after review

Think of this as:

> I have reviewed the chart and I now want to add a phase change.

### `export-csv` / `export-sqlite`
Use these to generate or regenerate outputs.

Purpose:
- produce charts
- produce summary tables
- rerun outputs after config changes

Think of this as:

> Build the outputs using the current config.

## Recommended mental model

Use this simple model:

- **Setup stage**: `wizard` or manual config creation
- **Build stage**: `export-*`
- **Review stage**: inspect charts and summaries
- **Refine stage**: `recalc-wizard` or manual recalc config editing
- **Rebuild stage**: `export-*` again

## Important note

The package should be treated as a **config-driven tool first**.

Wizards are there to help users, especially on smaller or guided tasks, but they are not the whole product and should not be required for all workflows.