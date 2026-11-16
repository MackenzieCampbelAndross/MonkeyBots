"""
MonkeyBots Controller Performance and Step Response Analysis.

Calculates classical control systems metrics from simulation step response:
- Rise Time (10% to 90%)
- Overshoot percentage (Mp)
- Settling Time (within 2% tolerance band)
- Steady-State Error (ess)
- Control stability and damping ratio classification
"""

import math
from typing import Dict, List, Tuple
import numpy as np

from ..simulation.engine import SimulationEngine
from .controllers import RobotMotionController


def evaluate_step_response(
    sim: SimulationEngine,
    joint_idx: int = 1,
    step_amplitude: float = 0.35,  # 0.35 rad (~20 deg)
    test_duration: float = 2.0,     # 2 seconds
    kp: float = 250.0,
    ki: float = 2.0,
    kd: float = 25.0,
) -> Dict[str, any]:
    """
    Executes a controlled closed-loop step response test in live MuJoCo simulation.
    Analyzes overshoot, rise time, settling time, and steady-state error.
    """
    if sim.model is None or sim.data is None:
        raise RuntimeError("Simulation engine is not initialized.")

    sim.reset()
    dof = min(6, sim.model.nq)
    q0 = np.array(sim.data.qpos[:dof])
    q_target = q0.copy()
    q_target[joint_idx] += step_amplitude

    controller = RobotMotionController(sim, dof=dof)
    controller.set_gains(joint_idx, kp, ki, kd)

    dt = sim.config.timestep
    num_steps = int(math.ceil(test_duration / dt))

    timestamps = []
    positions = []
    velocities = []
    torques = []

    # Execute simulation
    for step in range(num_steps):
        t = step * dt
        tau = controller.compute_torques(q_target)
        for i in range(min(dof, sim.model.nu)):
            ctrl_limit = sim.model.actuator_ctrlrange[i]
            if ctrl_limit[0] < ctrl_limit[1]:
                sim.data.ctrl[i] = np.clip(tau[i], ctrl_limit[0], ctrl_limit[1])
            else:
                sim.data.ctrl[i] = tau[i]
        sim.step(1, apply_internal_controllers=False)

        q_curr = float(sim.data.qpos[joint_idx])
        v_curr = float(sim.data.qvel[joint_idx])

        if step % 5 == 0 or step == num_steps - 1:
            timestamps.append(round(t, 4))
            positions.append(round(q_curr, 5))
            velocities.append(round(v_curr, 5))
            torques.append(round(float(tau[joint_idx]), 3))

    # Classical Control Analysis
    y0 = float(q0[joint_idx])
    yf = float(q_target[joint_idx])
    delta_y = yf - y0
    t_arr = np.array(timestamps)
    y_arr = np.array(positions)

    # 1. Steady-state error
    y_final = float(np.mean(y_arr[-20:]))  # Average over final 20 samples
    ess = abs(yf - y_final)

    # 2. Overshoot
    peak_y = float(np.max(y_arr)) if delta_y > 0 else float(np.min(y_arr))
    overshoot_abs = max(0.0, (peak_y - yf) if delta_y > 0 else (yf - peak_y))
    overshoot_percent = (overshoot_abs / abs(delta_y)) * 100.0

    # 3. Rise time (10% to 90%)
    val_10 = y0 + 0.10 * delta_y
    val_90 = y0 + 0.90 * delta_y
    t_10, t_90 = None, None
    for t_val, pos_val in zip(t_arr, y_arr):
        if delta_y > 0:
            if t_10 is None and pos_val >= val_10:
                t_10 = t_val
            if t_90 is None and pos_val >= val_90:
                t_90 = t_val
        else:
            if t_10 is None and pos_val <= val_10:
                t_10 = t_val
            if t_90 is None and pos_val <= val_90:
                t_90 = t_val

    rise_time = round(float(t_90 - t_10), 4) if (t_10 is not None and t_90 is not None) else 0.0

    # 4. Settling time (2% band)
    band_2pct = 0.02 * abs(delta_y)
    settling_time = test_duration
    for idx in range(len(y_arr) - 1, -1, -1):
        if abs(y_arr[idx] - yf) > band_2pct:
            settling_time = round(float(t_arr[min(len(t_arr) - 1, idx + 1)]), 4)
            break

    # 5. Stability & Damping classification
    if ess > 0.10 * abs(delta_y) or np.any(np.isnan(y_arr)):
        stability = "UNSTABLE"
    elif overshoot_percent > 15.0:
        stability = "UNDERDAMPED"
    elif overshoot_percent > 1.0:
        stability = "SLIGHTLY_UNDERDAMPED"
    else:
        stability = "CRITICALLY_DAMPED"

    return {
        "joint_index": joint_idx,
        "initial_position_rad": round(y0, 5),
        "target_position_rad": round(yf, 5),
        "steady_state_error_rad": round(ess, 6),
        "overshoot_percent": round(overshoot_percent, 2),
        "rise_time_seconds": rise_time,
        "settling_time_seconds": settling_time,
        "stability": stability,
        "is_stable": stability != "UNSTABLE",
        "timestamps": timestamps,
        "positions": positions,
        "velocities": velocities,
        "torques": torques,
    }
