"""
MonkeyBots Analytics & Reporting Module
Provides ground-truth simulation telemetry buffers, dynamic performance metrics,
multi-run comparative analytics, and multi-format engineering report generators.
"""

from .telemetry_buffer import (
    TelemetryPoint,
    SimulationTelemetryBuffer,
    execute_and_record_run,
    compute_quaternion_error,
)
from .metrics import (
    JointPerformanceMetrics,
    StepResponseMetrics,
    SimulationRunMetrics,
    compute_analytics_metrics,
)
from .comparator import (
    RunComparisonItem,
    CrossRunMetricDelta,
    MultiRunComparisonReport,
    compare_simulation_runs,
)
from .report_generator import (
    generate_svg_chart,
    generate_markdown_report,
    generate_html_report,
)

__all__ = [
    "TelemetryPoint",
    "SimulationTelemetryBuffer",
    "execute_and_record_run",
    "compute_quaternion_error",
    "JointPerformanceMetrics",
    "StepResponseMetrics",
    "SimulationRunMetrics",
    "compute_analytics_metrics",
    "RunComparisonItem",
    "CrossRunMetricDelta",
    "MultiRunComparisonReport",
    "compare_simulation_runs",
    "generate_svg_chart",
    "generate_markdown_report",
    "generate_html_report",
]
