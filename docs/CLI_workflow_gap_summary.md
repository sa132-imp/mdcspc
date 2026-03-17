# CLI Workflow Gap Summary

This note compares the agreed user workflow for `mdcspc` against the current CLI and wizard surface.

Its purpose is to separate:
- what already works as intended
- what only needs clearer documentation
- what may need a small future code change

---

## Already works as intended

### 1. Modular helpers already exist
The current structure already supports the preferred modular pattern:
- `wizard` for starter config generation
- `recalc-wizard` for recalculation / phase updates

This is already much closer to the intended workflow than a single giant wizard.

### 2. Manual config editing is already first-class
The package already supports direct config editing:
- config CSVs are real first-class project inputs
- export commands work from config files
- users are not forced through wizard-led flows

This matches the agreed design for bulk or power-users.

### 3. Rebuild loop already exists
The workflow:
- change config
- rerun export
- inspect outputs

already exists in the current structure through export commands such as:
- `export-csv`
- `export-sqlite`

### 4. Recalcs already persist
Recalc entries are written into `spc_phase_config.csv`, so recalculation settings persist until changed or removed.

This matches the agreed intended behaviour.

---

## Needs documentation clarification only

### 1. `wizard` vs `recalc-wizard`
These command names are easy to muddle unless explained clearly.

They do different jobs:

- `wizard` = initial setup / starter config generation
- `recalc-wizard` = later refinement of phase / recalc config

This distinction should be made explicit in user-facing docs.

### 2. `init-config` vs `wizard`
These are both setup-related, but serve different needs:

- `init-config` = write blank/default config templates
- `wizard` = inspect input data and help generate starter config

This is not necessarily a code problem, but it is a likely source of user confusion unless documented clearly.

### 3. Metric discovery exists, but is not clearly surfaced
The current setup wizard already identifies metric names from the dataset.

That capability exists, but it is not yet described clearly enough as part of the early workflow.

The docs should make this explicit:
> the setup wizard helps identify the available metrics in the data

---

## Likely future small code changes

### 1. Dedicated metric-discovery helper
At the moment, metric discovery is bundled inside the setup wizard.

A future improvement could be a small helper command or reusable helper step that simply:
- inspects the data
- lists the metric names found
- helps the user decide whether to use a wizard or edit config manually

This would align more neatly with the agreed workflow.

### 2. Improved metric/org selection in recalc wizard
The recalc wizard currently relies on user prompts rather than a more guided selection flow.

A future improvement could make this more structured, especially when suitable project config already exists.

### 3. Clearer DataFrame story in user-facing workflow
The intended workflow includes CSV and DataFrame inputs.

The current user-facing CLI story appears clearer for CSV and SQLite than for DataFrame.

This may already be supported elsewhere in the package, but it is not yet clearly represented in the CLI/workflow surface and may need tidying later.

---

## Recommendation

The current project is not fundamentally off-track.

The main issue is not that the code structure is wrong, but that the user-facing workflow and command meanings are not yet documented clearly enough.

The best immediate priority is:

1. clarify the command meanings in docs
2. keep the workflow anchored to the agreed user journey
3. only then decide whether any command names or helper commands need code changes

This is lower-risk than redesigning code before the user-facing workflow is fully settled.