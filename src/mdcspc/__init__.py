from __future__ import annotations

# XmR engine
from .xmr import (
    MultiXmrResult,
    analyse_xmr,
    analyse_xmr_by_group,
    plot_xmr,
)

# Summary / per-series KPI table
from .summary import SummaryConfig, summarise_xmr_by_group

# Metric configuration + variation/assurance helpers
from .metric_config import (
    MetricConfig,
    VariationStatus,
    AssuranceStatus,
    VARIATION_ICON_FILES,
    ASSURANCE_ICON_FILES,
    load_metric_config,
    get_metric_config,
    classify_variation,
    classify_assurance,
    classify_assurance_from_key,
)

# Icon table builder + exporter
from .icon_table import build_icon_table, export_icon_table

# High-level pipelines
from .exporter import export_spc_from_csv
from .exporter_dataframe import export_spc_from_dataframe, export_spc_from_sqlite


__version__ = "0.1.0"

__all__ = [
    "__version__",
    # XmR engine
    "MultiXmrResult",
    "analyse_xmr",
    "analyse_xmr_by_group",
    "plot_xmr",
    # Summary
    "SummaryConfig",
    "summarise_xmr_by_group",
    # Metric config + statuses
    "MetricConfig",
    "VariationStatus",
    "AssuranceStatus",
    "VARIATION_ICON_FILES",
    "ASSURANCE_ICON_FILES",
    "load_metric_config",
    "get_metric_config",
    "classify_variation",
    "classify_assurance",
    "classify_assurance_from_key",
    # Icon table
    "build_icon_table",
    "export_icon_table",
    # High-level pipeline entry points
    "export_spc_from_csv",
    "export_spc_from_dataframe",
    "export_spc_from_sqlite",
]