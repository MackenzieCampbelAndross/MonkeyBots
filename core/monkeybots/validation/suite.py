"""
MonkeyBots Validation Suite Orchestrator & Markdown Report Generator
Orchestrates all 10 engineering validation capabilities, computes overall suite compliance,
and generates formal engineering validation reports in Markdown and structured formats.
"""

import time
import platform
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional, Callable

from .standards import (
    ValidationStatus,
    ValidationMetric,
    ValidationTestCase,
    ValidationSuiteReport,
)
from .capabilities import (
    validate_robot_model_integrity,
    validate_joint_limits,
    validate_kinematics,
    validate_physics_engine,
    validate_trajectory_planning,
    validate_collision_and_contact,
    validate_numerical_stability,
    validate_repeatability_and_determinism,
    validate_controller_performance,
    validate_numerical_error_analysis,
)

try:
    import mujoco
    MUJOCO_VERSION = mujoco.__version__
except Exception:
    MUJOCO_VERSION = "Unavailable"


CAPABILITY_RUNNERS: Dict[str, Callable[[], ValidationTestCase]] = {
    "VAL_CAP_01": validate_robot_model_integrity,
    "VAL_CAP_02": validate_joint_limits,
    "VAL_CAP_03": validate_kinematics,
    "VAL_CAP_04": validate_physics_engine,
    "VAL_CAP_05": validate_trajectory_planning,
    "VAL_CAP_06": validate_collision_and_contact,
    "VAL_CAP_07": validate_numerical_stability,
    "VAL_CAP_08": validate_repeatability_and_determinism,
    "VAL_CAP_09": validate_controller_performance,
    "VAL_CAP_10": validate_numerical_error_analysis,
}

# Alias mapping for friendly lookup
CAPABILITY_ALIASES: Dict[str, str] = {
    "model": "VAL_CAP_01",
    "joint_limits": "VAL_CAP_02",
    "kinematics": "VAL_CAP_03",
    "physics": "VAL_CAP_04",
    "trajectory": "VAL_CAP_05",
    "collision": "VAL_CAP_06",
    "stability": "VAL_CAP_07",
    "repeatability": "VAL_CAP_08",
    "controller": "VAL_CAP_09",
    "numerical_error": "VAL_CAP_10",
}


class ValidationLaboratory:
    """
    Central validation orchestrator for MonkeyBots.
    Executes analytical verification suites, tracks compliance metrics,
    and produces deterministic verification artifacts without databases or cloud APIs.
    """

    def __init__(self):
        self._last_report: Optional[ValidationSuiteReport] = None

    def run_capability(self, identifier: str) -> ValidationTestCase:
        """Runs a single validation capability benchmark by ID or alias."""
        target_id = identifier.upper()
        if target_id not in CAPABILITY_RUNNERS:
            alias_key = identifier.lower().replace("-", "_").replace(" ", "_")
            if alias_key in CAPABILITY_ALIASES:
                target_id = CAPABILITY_ALIASES[alias_key]
            else:
                raise ValueError(
                    f"Unknown validation capability '{identifier}'. Available IDs: {list(CAPABILITY_RUNNERS.keys())}"
                )

        runner = CAPABILITY_RUNNERS[target_id]
        return runner()

    def run_suite(self) -> ValidationSuiteReport:
        """
        Executes all 10 engineering validation capabilities sequentially.
        Aggregates results, calculates pass/fail counts and compliance percentage.
        """
        iso_now = datetime.now(timezone.utc).isoformat()
        test_cases: List[ValidationTestCase] = []

        verified_count = 0
        failed_count = 0
        known_limitations_count = 0
        not_implemented_count = 0

        for cap_id, runner in CAPABILITY_RUNNERS.items():
            try:
                tc = runner()
            except Exception as e:
                tc = ValidationTestCase(
                    id=cap_id,
                    category="System Exception",
                    name=f"Execution Fault in {cap_id}",
                    description="Benchmark encountered an unhandled exception during execution.",
                    standard_reference="IEEE 1044 / ISO 26262 Fault Handling",
                    status=ValidationStatus.FAILED,
                    metrics=[],
                    execution_time_ms=0.0,
                    failure_reason=str(e),
                )

            test_cases.append(tc)

            if tc.status == ValidationStatus.VERIFIED:
                verified_count += 1
            elif tc.status == ValidationStatus.FAILED:
                failed_count += 1
            elif tc.status == ValidationStatus.KNOWN_LIMITATION:
                known_limitations_count += 1
            elif tc.status == ValidationStatus.NOT_IMPLEMENTED:
                not_implemented_count += 1

        total_tests = len(test_cases)
        # Compliance counts VERIFIED as fully compliant, and KNOWN_LIMITATION as partial (50%)
        effective_score = verified_count + (0.5 * known_limitations_count)
        compliance_pct = round((effective_score / max(1, total_tests)) * 100.0, 1)

        if failed_count > 0:
            overall_status = ValidationStatus.FAILED
        elif compliance_pct >= 90.0:
            overall_status = ValidationStatus.VERIFIED
        else:
            overall_status = ValidationStatus.KNOWN_LIMITATION

        system_info = {
            "os": platform.system(),
            "os_release": platform.release(),
            "architecture": platform.machine(),
            "python_version": sys.version.split()[0],
            "mujoco_version": MUJOCO_VERSION,
            "validation_standard": "ISO 9283 / IEEE 754 / Classical Rigid Body Dynamics",
        }

        report = ValidationSuiteReport(
            suite_name="MonkeyBots Comprehensive Engineering Validation Laboratory",
            version="1.0.0",
            timestamp=iso_now,
            overall_status=overall_status,
            total_tests=total_tests,
            verified_count=verified_count,
            failed_count=failed_count,
            known_limitations_count=known_limitations_count,
            not_implemented_count=not_implemented_count,
            compliance_percentage=compliance_pct,
            test_cases=test_cases,
            system_info=system_info,
        )

        self._last_report = report
        return report

    def generate_markdown_report(self, report: Optional[ValidationSuiteReport] = None) -> str:
        """
        Generates a rigorous engineering Markdown report for the validation suite.
        Includes executive summary, methodology, per-capability analytical findings,
        tolerances, differences, and standard citations.
        """
        rep = report or self._last_report
        if rep is None:
            rep = self.run_suite()

        lines: List[str] = []
        lines.append("# MONKEYBOTS | ENGINEERING VALIDATION & BENCHMARKING REPORT")
        lines.append(f"**Suite:** {rep.suite_name} (v{rep.version})  ")
        lines.append(f"**Generated:** {rep.timestamp}  ")
        lines.append(f"**Overall Status:** `{rep.overall_status.value}` | **Compliance:** {rep.compliance_percentage}%  ")
        lines.append("")

        # System Architecture & Environment
        lines.append("## 1. System Environment & Execution Context")
        lines.append("| Parameter | Value |")
        lines.append("| :--- | :--- |")
        lines.append(f"| Operating System | {rep.system_info.get('os')} {rep.system_info.get('os_release')} ({rep.system_info.get('architecture')}) |")
        lines.append(f"| Python Runtime | v{rep.system_info.get('python_version')} |")
        lines.append(f"| Physics Engine | MuJoCo v{rep.system_info.get('mujoco_version')} |")
        lines.append(f"| Standards Reference | {rep.system_info.get('validation_standard')} |")
        lines.append(f"| Persistence Architecture | Local-First JSON (Zero Cloud / Zero Database) |")
        lines.append("")

        # Executive Summary
        lines.append("## 2. Executive Validation Summary")
        lines.append(f"- **Total Capabilities Benchmarked:** {rep.total_tests}")
        lines.append(f"- **Formally Verified (`VERIFIED`):** {rep.verified_count}")
        lines.append(f"- **Failed (`FAILED`):** {rep.failed_count}")
        lines.append(f"- **Documented Limitations (`KNOWN_LIMITATION`):** {rep.known_limitations_count}")
        lines.append(f"- **Pending Implementation (`NOT_IMPLEMENTED`):** {rep.not_implemented_count}")
        lines.append(f"- **Analytical Compliance Ratio:** `{rep.compliance_percentage}%`")
        lines.append("")

        # Benchmark Matrix Table
        lines.append("## 3. Capability Compliance Matrix")
        lines.append("| ID | Capability / Benchmark | Category | Standard Reference | Exec Time | Status |")
        lines.append("| :--- | :--- | :--- | :--- | :---: | :---: |")
        for tc in rep.test_cases:
            badge = "✅ PASS" if tc.status == ValidationStatus.VERIFIED else ("⚠️ LIMITATION" if tc.status == ValidationStatus.KNOWN_LIMITATION else "❌ FAIL")
            lines.append(f"| `{tc.id}` | **{tc.name}** | {tc.category} | {tc.standard_reference} | {tc.execution_time_ms:.1f}ms | `{tc.status.value}` {badge} |")
        lines.append("")

        # Detailed Capability Breakdown
        lines.append("## 4. Analytical Metric Deep-Dives")
        for tc in rep.test_cases:
            status_indicator = "✅ VERIFIED" if tc.status == ValidationStatus.VERIFIED else f"⚠️ {tc.status.value}"
            lines.append(f"### {tc.id}: {tc.name} [{status_indicator}]")
            lines.append(f"**Category:** {tc.category} | **Reference:** *{tc.standard_reference}*  ")
            lines.append(f"**Description:** {tc.description}  ")
            if tc.failure_reason:
                lines.append(f"> **Notice:** {tc.failure_reason}  ")

            if tc.metrics:
                lines.append("")
                lines.append("| Metric | Expected Reference | Simulated / Computed | Absolute Difference | Tolerance | Unit | Status |")
                lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
                for m in tc.metrics:
                    m_status = "PASS" if m.status == ValidationStatus.VERIFIED else m.status.value
                    lines.append(
                        f"| {m.name} | `{m.expected_value:.6g}` | `{m.actual_value:.6g}` | `{m.difference:.6g}` | `{m.tolerance:.6g}` | {m.unit or '-'} | `{m_status}` |"
                    )
                lines.append("")

        # Engineering Methodology and Standards
        lines.append("## 5. Engineering Principles & Validation Methodology")
        lines.append("1. **Absolute Truth Baselines:** MonkeyBots validation relies strictly on closed-form analytical equations (e.g., $z(t) = z_0 - \\frac{1}{2}gt^2$, Hamiltonian energy invariants $E = T + V$, DLS residual convergence, and finite-difference Jacobians).")
        lines.append("2. **Zero Fabricated Precision:** Metrics reflect exact floating-point differences ($|\\text{actual} - \\text{expected}|$) against physical tolerances. No speculative scores or fabricated accuracy percentages are accepted.")
        lines.append("3. **Bit-Level Determinism:** Simulation state trajectories across identical initial conditions and seeds must exhibit variance $\\sigma^2 \\le 10^{-12}$ to qualify for safety-critical robotics engineering.")
        lines.append("4. **Classification Rigor:** Every benchmark result is categorized as `VERIFIED`, `FAILED`, `NOT_IMPLEMENTED`, or `KNOWN_LIMITATION`.")
        lines.append("")

        return "\n".join(lines)
