"""
MonkeyBots Multi-Run Simulation Comparator
Performs rigorous side-by-side analysis of multiple simulation experiments.
Compares trajectory tracking, energy dissipation, torque expenditures, and control stability.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from .metrics import SimulationRunMetrics


class RunComparisonItem(BaseModel):
    run_id: str
    run_name: str
    timestep: float
    duration: float
    cartesian_rmse_mm: float
    max_cartesian_error_mm: float
    joint_rmse_mrad: float
    peak_torque_nm: float
    rms_torque_nm: float
    settling_time_s: float
    overshoot_percent: float
    energy_drift_j: float
    real_time_factor: float
    mean_latency_us: float


class CrossRunMetricDelta(BaseModel):
    target_id: str
    baseline_id: str
    delta_rmse_mm: float
    rmse_improvement_pct: float
    delta_peak_torque_nm: float
    delta_settling_time_s: float
    delta_energy_drift_j: float
    rtf_ratio: float
    trade_off_summary: str


class MultiRunComparisonReport(BaseModel):
    baseline_run_id: str
    compared_runs: List[RunComparisonItem]
    deltas: Dict[str, CrossRunMetricDelta]
    key_findings: List[str]


def compare_simulation_runs(
    runs_data: List[Dict[str, Any]],
) -> MultiRunComparisonReport:
    """
    Compares two or more simulation runs.
    runs_data must contain 'run_id', 'name', 'metrics' (SimulationRunMetrics dict), and optional time-series.
    """
    if len(runs_data) < 2:
        raise ValueError("Multi-run comparison requires at least 2 simulation runs.")

    items: List[RunComparisonItem] = []
    for r in runs_data:
        m = r.get("metrics")
        if not m:
            continue
        if isinstance(m, dict):
            pass
        elif hasattr(m, "model_dump"):
            m = m.model_dump()

        items.append(
            RunComparisonItem(
                run_id=r.get("run_id", "run"),
                run_name=r.get("name", "Simulation Run"),
                timestep=m.get("timestep_s", 0.002),
                duration=m.get("total_duration_s", 2.5),
                cartesian_rmse_mm=round(m.get("overall_position_rmse_m", 0.0) * 1000.0, 3),
                max_cartesian_error_mm=round(m.get("max_cartesian_error_m", 0.0) * 1000.0, 3),
                joint_rmse_mrad=round(m.get("overall_joint_rmse_rad", 0.0) * 1000.0, 3),
                peak_torque_nm=round(m.get("peak_applied_torque_nm", 0.0), 2),
                rms_torque_nm=round(float(np.mean([j.get("rms_torque_nm", 0.0) for j in m.get("joints", [])])) if m.get("joints") else 0.0, 2),
                settling_time_s=round(m.get("step_response", {}).get("settling_time_s", 0.0), 3),
                overshoot_percent=round(m.get("step_response", {}).get("overshoot_percent", 0.0), 2),
                energy_drift_j=round(m.get("energy_drift_j", 0.0), 3),
                real_time_factor=round(m.get("real_time_factor", 1.0), 2),
                mean_latency_us=round(m.get("mean_step_latency_us", 0.0), 1),
            )
        )

    if len(items) < 2:
        raise ValueError("Could not parse valid metrics for at least 2 runs.")

    baseline = items[0]
    deltas: Dict[str, CrossRunMetricDelta] = {}
    findings: List[str] = []

    for other in items[1:]:
        d_rmse = round(other.cartesian_rmse_mm - baseline.cartesian_rmse_mm, 3)
        rmse_impr = round(
            ((baseline.cartesian_rmse_mm - other.cartesian_rmse_mm) / max(1e-4, baseline.cartesian_rmse_mm)) * 100.0,
            2,
        )
        d_torque = round(other.peak_torque_nm - baseline.peak_torque_nm, 2)
        d_ts = round(other.settling_time_s - baseline.settling_time_s, 3)
        d_energy = round(other.energy_drift_j - baseline.energy_drift_j, 3)
        rtf_ratio = round(other.real_time_factor / max(1e-4, baseline.real_time_factor), 2)

        # Trade-off synthesis
        if rmse_impr > 5.0 and d_torque > 5.0:
            trade_off = f"Improves tracking accuracy by {rmse_impr}% at the expense of +{d_torque} Nm higher peak actuator torque."
        elif rmse_impr > 5.0 and d_torque <= 5.0:
            trade_off = f"Optimal configuration: {rmse_impr}% tracking error reduction with minimal torque impact ({d_torque} Nm)."
        elif rmse_impr < -5.0:
            trade_off = f"Tracking degradation by {abs(rmse_impr)}% compared to baseline."
        else:
            trade_off = f"Comparable trajectory tracking (Δ RMSE: {d_rmse} mm, Δ Peak Torque: {d_torque} Nm)."

        deltas[f"{other.run_id}_vs_{baseline.run_id}"] = CrossRunMetricDelta(
            target_id=other.run_id,
            baseline_id=baseline.run_id,
            delta_rmse_mm=d_rmse,
            rmse_improvement_pct=rmse_impr,
            delta_peak_torque_nm=d_torque,
            delta_settling_time_s=d_ts,
            delta_energy_drift_j=d_energy,
            rtf_ratio=rtf_ratio,
            trade_off_summary=trade_off,
        )

        findings.append(f"[{other.run_name} vs {baseline.run_name}]: {trade_off}")

    return MultiRunComparisonReport(
        baseline_run_id=baseline.run_id,
        compared_runs=items,
        deltas=deltas,
        key_findings=findings,
    )


import numpy as np  # Required for np.mean inside comparator
