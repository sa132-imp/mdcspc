# MDCSPC User Workflow

## Purpose

This document defines the intended plain-English user workflow for the `mdcspc` package.

Its purpose is to keep the project anchored to the real user journey and avoid drift in future design or coding discussions.

The core principle is:

> `mdcspc` is a config-driven SPC tool with optional guided helpers.

It is **not** a wizard-only product, and it is **not** a tool that should force all users through one rigid path.

---

## Core workflow

### 1. User brings data

The user starts with a dataset.

This input may come from:
- a CSV file, or
- a pandas DataFrame created from another process such as SQL, SQLite, or other database-linked workflows.

Both routes are first-class inputs and should be treated as part of the normal workflow.

---

### 2. Tool helps identify what is in the data

Early in the workflow, the tool should help the user understand what is present in the input.

In particular, it should be able to identify the distinct metric names available in the dataset.

This can support the next step, where the user decides how they want to configure the run.

From the user point of view, the expected behaviour is:

> "Show me the metrics in my data so I know what I am configuring."

This metric discovery may happen inside a wizard or as a helper step before a wizard. The exact implementation can vary, but the workflow expectation should remain the same.

---

### 3. User chooses a guided or manual config route

Once the available metrics are known, the user should be able to choose how they want to configure the run.

There are two valid routes:

#### A. Guided route
The user runs a config wizard.

This is most useful when:
- they are working with a small number of charts
- they want help stepping through the setup
- they are less comfortable editing config files directly

The wizard should work through the identified metrics and help the user create the relevant config.

#### B. Manual route
The user edits the config CSV files directly.

This is most useful when:
- there are large numbers of metrics
- they want speed and full control
- they are a bulk or power-user
- they simply prefer working directly in config files

Both routes are valid. The package should support both without implying that one is the only proper way to work.

---

### 4. Tool generates outputs

Once the relevant config is in place, the tool runs and produces outputs.

These outputs include:
- SPC charts
- summary tables

This is the first main output stage.

---

### 5. User reviews outputs

The user reviews the generated charts and summaries.

This is an important part of the workflow, not an optional extra.

At this stage, the user decides whether additional refinement is needed, especially:
- recalculation points / phase changes
- annotations
- targets
- other chart-specific adjustments that may be added later

The charts are not just an end product. They are also part of the review loop.

---

### 6. User adds recalcs if needed

If recalculation points are needed, the user should again have two valid routes:

#### A. Recalc wizard
The user runs a small dedicated recalc wizard.

This is useful when they want guided help adding a recalculation point.

#### B. Manual config editing
The user edits the phase/recalc config CSV directly.

This is useful for bulk or power-users, or anyone who prefers direct control.

Again, both routes are valid and should remain supported.

---

### 7. Tool reruns outputs

After recalcs are added or changed, the user reruns the charts and summary outputs.

This ensures the outputs reflect the updated phase/recalculation settings.

---

### 8. Recalcs persist until changed or removed

Recalculation settings are part of the project configuration.

Once added, they should continue to affect the outputs unless the user explicitly changes or removes them.

Expected behaviour:

> Recalcs remain in the charts until removed by the user.

This persistence is an important part of making the tool reliable and predictable.

---

## Design principles implied by this workflow

### 1. Config-driven first
The package should remain config-driven.

Wizards are helpers, not the core identity of the tool.

### 2. Optional guided helpers
Wizards should help users where useful, but should not be required for all workflows.

### 3. Support both light and heavy use
The package should work for:
- smaller guided jobs
- larger bulk or power-user jobs

### 4. Review is part of the workflow
Generating charts is not the final stop. Reviewing and refining outputs is part of the normal cycle.

### 5. Modular helper tools are preferred
It is better to have small, focused helper wizards than one large wizard that tries to do everything.

---

## Preferred modular helper pattern

The preferred direction for helper workflows is:

- **Config wizard** for initial setup
- **Recalc wizard** for phase/recalculation updates
- potentially later:
  - **Annotation wizard**
  - **Target wizard**

This modular pattern is preferred over a single large all-in-one wizard.

Reasons:
- simpler for users
- easier to maintain
- easier to reason about
- avoids forcing wizard-based behaviour on users who prefer direct config editing

---

## Non-goals / anti-drift notes

To avoid future confusion, the project should not drift into these assumptions:

- The wizard is **not** the whole product.
- Users should **not** be forced into a wizard-only workflow.
- Manual config editing is a valid first-class workflow, especially for bulk or power-users.
- Recalc editing is only one part of the overall user journey, not the whole workflow.
- Setup, output review, and refinement should all be treated as distinct stages.

---

## Short reference version

If a short version is needed, use this:

> A user brings in data from CSV or DataFrame. The tool helps identify available metrics. The user then either uses a wizard or edits config files directly to define what should be charted. The tool generates charts and summaries. The user reviews those outputs and, if needed, adds recalculation points through a wizard or direct config editing. The outputs are rerun, and those recalculation settings persist until changed or removed.

---

## Status of this document

This document records the intended workflow agreed during project discussion.

It should be treated as a reference point for future design, CLI decisions, wizard design, and documentation, so that the project stays aligned with the real user journey.

### Recalc annotation position

`AnnotationPosition` in `spc_phase_config.csv` controls whether a phase annotation is drawn near the upper control limit (`U`) or lower control limit (`L`).

This has been tested end-to-end with:
- `recalc-wizard`
- `export-csv`
- a matching long-format input dataset