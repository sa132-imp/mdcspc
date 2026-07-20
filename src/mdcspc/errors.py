from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MdcSpcError(ValueError):
    """Plain-English user-facing MDCSPC error."""

    code: str
    title: str
    detail: str
    fix: Optional[str] = None
    docs: Optional[str] = None

    def __str__(self) -> str:
        parts = [f"{self.code}: {self.title}"]

        if self.detail:
            parts.append(self.detail)

        if self.fix:
            parts.append(f"How to fix it:\n{self.fix}")

        if self.docs:
            parts.append(f"More help: {self.docs}")

        return "\n\n".join(parts)


def missing_metric_name_for_wizard() -> MdcSpcError:
    return MdcSpcError(
        code="MDCSPC001",
        title="Missing MetricName column",
        detail=(
            "The wizard needs a MetricName column to build the metric configuration.\n\n"
            "MetricName identifies what each row is measuring and is used to create "
            "chart settings such as display name, improvement direction, unit, target "
            "and decimal places.\n\n"
            "Your input data should include:\n"
            "- a date/index column\n"
            "- a value column\n"
            "- a MetricName column"
        ),
        fix=(
            "If your file contains one metric, repeat the same MetricName on each row.\n"
            "If your file contains several metrics, use MetricName to show which metric each row belongs to."
        ),
    )


def blank_metric_name_for_wizard() -> MdcSpcError:
    return MdcSpcError(
        code="MDCSPC001",
        title="MetricName column is blank",
        detail=(
            "The wizard found a MetricName column, but it does not contain any usable values.\n\n"
            "MetricName identifies what each row is measuring and is used to create "
            "chart settings such as display name, improvement direction, unit, target "
            "and decimal places."
        ),
        fix=(
            "If your file contains one metric, repeat the same MetricName on each row.\n"
            "If your file contains several metrics, use MetricName to show which metric each row belongs to."
        ),
    )

def no_metric_or_grouping_column_for_export(
    index_col: str,
    value_col: str,
) -> MdcSpcError:
    return MdcSpcError(
        code="MDCSPC002",
        title="No metric or grouping column found",
        detail=(
            "MDCSPC could not find a metric or grouping column.\n\n"
            "Your input data needs:\n"
            f"- a date/index column, currently set as: {index_col}\n"
            f"- a value column, currently set as: {value_col}\n"
            "- at least one column that identifies the chart or series, usually MetricName"
        ),
        fix=(
            "Recommended: add a MetricName column.\n\n"
            "MetricName links your data to metric_config.csv, including display name, "
            "improvement direction, unit, target and decimal places.\n\n"
            "If your file contains one metric, repeat the same MetricName on each row.\n"
            "If your file contains several metrics, use MetricName to identify each metric."
        ),
    )

def missing_index_column_for_export(index_col: str) -> MdcSpcError:
    return MdcSpcError(
        code="MDCSPC003",
        title="Missing date/index column",
        detail=(
            f"Your CSV is missing the date/index column currently set as: {index_col}\n\n"
            "MDCSPC needs a date or time column so it can put the data points "
            "in the right order on the chart."
        ),
        fix=(
            "If your date column has a different name, use --index-col.\n"
            "If your CSV does not have a date or time column yet, add one for each data point."
        ),
    )


def missing_value_column_for_export(value_col: str) -> MdcSpcError:
    return MdcSpcError(
        code="MDCSPC004",
        title="Missing value column",
        detail=(
            f"Your CSV is missing the value column currently set as: {value_col}\n\n"
            "MDCSPC needs a value column containing the numbers to plot on the chart."
        ),
        fix=(
            "If your value column has a different name, use --value-col.\n"
            "If your CSV does not have a value column yet, add one containing the metric value for each data point."
        ),
    )

def could_not_parse_index_dates_for_export(
    index_col: str,
    bad_values: list[str],
) -> MdcSpcError:
    shown_values = bad_values[:5]
    values_text = "\n".join(f"- {value}" for value in shown_values)

    return MdcSpcError(
        code="MDCSPC005",
        title="Could not read date/index values",
        detail=(
            f"MDCSPC could not read some values in the date/index column currently set as: {index_col}\n\n"
            "Example problem values:\n"
            f"{values_text}"
        ),
        fix=(
            "Check that the date/index column contains real dates.\n"
            "Common formats include:\n"
            "- 11/01/2026\n"
            "- 2026-01-11\n"
            "- Jan 2026"
        ),
    )

def could_not_parse_numeric_values_for_export(
    value_col: str,
    bad_values: list[str],
) -> MdcSpcError:
    shown_values = bad_values[:5]
    values_text = "\n".join(f"- {value}" for value in shown_values)

    return MdcSpcError(
        code="MDCSPC006",
        title="Could not read numeric values",
        detail=(
            "MDCSPC could not convert some values in the value column to numbers.\n\n"
            f"Value column currently set as: {value_col}\n\n"
            "Example problem values:\n"
            f"{values_text}"
        ),
        fix=(
            "Check that the value column contains numbers only.\n"
            "Remove text, symbols or notes from the value column before running the export.\n\n"
            "Examples of valid values:\n"
            "- 12\n"
            "- 12.5\n"
            "- 0.08858"
        ),
    )


def duplicate_period_values_for_series(
    index_col: str,
    duplicate_values: list[str],
) -> MdcSpcError:
    shown_values = duplicate_values[:5]
    values_text = "\n".join(f"- {value}" for value in shown_values)

    return MdcSpcError(
        code="MDCSPC007",
        title="Duplicate period values within a series",
        detail=(
            "MDCSPC found more than one row for the same period within a single series.\n\n"
            f"Date/index column: {index_col}\n\n"
            "Example duplicate periods:\n"
            f"{values_text}"
        ),
        fix=(
            "Keep only one value for each period within each series.\n"
            "Do not simply remove a row unless you have confirmed which value is correct.\n"
            "The same period may appear in different series."
        ),
    )


def invalid_phase_starts(
    problem: str,
    values: list[str],
) -> MdcSpcError:
    shown_values = values[:5]
    values_text = "\n".join(f"- {value}" for value in shown_values)

    return MdcSpcError(
        code="MDCSPC008",
        title="Invalid phase start values",
        detail=(
            f"{problem}\n\n"
            "Example phase start values:\n"
            f"{values_text}"
        ),
        fix=(
            "Each phase start must match an actual observation in the series.\n"
            "Do not use the first observation as a phase start, because that would create an empty first phase.\n"
            "Remove duplicate phase starts."
        ),
    )



def invalid_infinite_values(
    value_col: str,
    invalid_values: list[str],
) -> MdcSpcError:
    shown_values = invalid_values[:5]
    values_text = "\n".join(f"- {value}" for value in shown_values)

    return MdcSpcError(
        code="MDCSPC009",
        title="Infinite values are not allowed",
        detail=(
            "MDCSPC found infinite values in the data.\n\n"
            f"Value column: {value_col}\n\n"
            "Example problem values:\n"
            f"{values_text}"
        ),
        fix=(
            "Replace infinite values with a valid numeric value or a missing value "
            "if appropriate.\n"
            "Do not use infinity as a measurement."
        ),
    )
