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