"""
MonkeyBots Controlled Physics Verification Suite
Executes analytical benchmark experiments and records exact numerical errors,
conservation laws, and solver limits.
"""

import math
import numpy as np
from typing import Dict, Any
import mujoco


def run_free_fall_benchmark(duration: float = 1.0, dt: float = 0.001) -> Dict[str, Any]:
    """
    Test 1: Free fall of a rigid sphere under gravity.
    Analytical Equations:
      z(t) = z0 - 0.5 * g * t^2
      vz(t) = -g * t
    """
    g = 9.81
    z0 = 10.0
    mass = 2.5

    xml = f"""
    <mujoco model="free_fall_test">
      <option timestep="{dt}" gravity="0 0 {-g}" integrator="RK4"/>
      <worldbody>
        <body name="ball" pos="0 0 {z0}">
          <freejoint/>
          <inertial pos="0 0 0" mass="{mass}" diaginertia="0.01 0.01 0.01"/>
          <geom type="sphere" size="0.1"/>
        </body>
      </worldbody>
    </mujoco>
    """
    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)

    steps = int(duration / dt)
    for _ in range(steps):
        mujoco.mj_step(model, data)

    t_final = data.time
    z_sim = float(data.qpos[2])
    vz_sim = float(data.qvel[2])

    z_analytical = z0 - 0.5 * g * (t_final ** 2)
    vz_analytical = -g * t_final

    z_error = abs(z_sim - z_analytical)
    vz_error = abs(vz_sim - vz_analytical)

    passed = bool(z_error < 1e-4 and vz_error < 1e-4)

    return {
        "test_name": "Free Fall Rigid Body Under Gravity",
        "passed": passed,
        "sim_time": round(t_final, 4),
        "z_sim": round(z_sim, 6),
        "z_analytical": round(z_analytical, 6),
        "z_error_m": round(z_error, 8),
        "vz_sim": round(vz_sim, 6),
        "vz_analytical": round(vz_analytical, 6),
        "vz_error_mps": round(vz_error, 8),
        "tolerance": 1e-4,
    }


def run_pendulum_energy_conservation_benchmark(duration: float = 2.0, dt: float = 0.001) -> Dict[str, Any]:
    """
    Test 2: Undamped single revolute joint (simple pendulum).
    Verifies mechanical energy conservation: E(t) = T(t) + V(t) = constant.
    """
    g = 9.81
    L = 1.0
    m = 1.0
    theta_0 = 0.1  # rad

    xml = f"""
    <mujoco model="pendulum_test">
      <option timestep="{dt}" gravity="0 0 {-g}" integrator="RK4"/>
      <worldbody>
        <body name="pendulum" pos="0 0 1.5">
          <joint name="hinge" type="hinge" pos="0 0 0" axis="0 1 0" damping="0" armature="0"/>
          <inertial pos="0 0 {-L}" mass="{m}" diaginertia="0.001 0.001 0.001"/>
          <geom type="cylinder" size="0.02 {L/2}" pos="0 0 {-L/2}"/>
          <geom type="sphere" size="0.06" pos="0 0 {-L}"/>
        </body>
      </worldbody>
    </mujoco>
    """
    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)

    data.qpos[0] = theta_0
    mujoco.mj_forward(model, data)

    # Initial Energy
    mujoco.mj_energyPos(model, data)
    mujoco.mj_energyVel(model, data)
    e_initial = float(data.energy[0] + data.energy[1])

    steps = int(duration / dt)
    max_energy_drift = 0.0

    for _ in range(steps):
        mujoco.mj_step(model, data)
        mujoco.mj_energyPos(model, data)
        mujoco.mj_energyVel(model, data)
        e_current = float(data.energy[0] + data.energy[1])
        drift = abs(e_current - e_initial)
        if drift > max_energy_drift:
            max_energy_drift = drift

    rel_drift = max_energy_drift / abs(e_initial) if abs(e_initial) > 1e-6 else max_energy_drift
    passed = bool(rel_drift < 1e-3)

    return {
        "test_name": "Rotating Joint Mechanical Energy Conservation",
        "passed": passed,
        "initial_energy_joules": round(e_initial, 6),
        "max_energy_drift_joules": round(max_energy_drift, 8),
        "relative_drift": round(rel_drift, 6),
        "tolerance": 1e-3,
    }


def run_multi_joint_static_equilibrium_benchmark(dt: float = 0.002) -> Dict[str, Any]:
    """
    Test 3: Multi-joint 6-DOF arm under gravity.
    Verifies that applying analytical gravity compensation torques maintains static equilibrium.
    """
    from ..models.assets.sample_6dof_arm import create_sample_6dof_arm
    from ..models.mjcf_builder import export_mjcf

    arm = create_sample_6dof_arm()
    mjcf_xml = export_mjcf(arm)

    model = mujoco.MjModel.from_xml_string(mjcf_xml)
    data = mujoco.MjData(model)

    # Set non-zero test pose
    test_pose = [0.0, -0.5, 0.8, 0.0, 0.3, 0.0]
    data.qpos[:6] = test_pose
    mujoco.mj_forward(model, data)

    # Compute gravity compensation torques via inverse dynamics
    data.qacc.fill(0.0)
    data.qvel.fill(0.0)
    mujoco.mj_inverse(model, data)
    gravity_torques = np.copy(data.qfrc_inverse[:model.nu])

    # Apply computed gravity compensation torques as constant control inputs
    data.ctrl[:model.nu] = gravity_torques

    # Step for 1 second (500 steps)
    for _ in range(500):
        mujoco.mj_step(model, data)

    # Measure maximum position drift from equilibrium
    pos_drift = np.max(np.abs(data.qpos[:6] - test_pose))
    passed = bool(pos_drift < 0.02)  # Less than 0.02 rad drift with passive hold

    return {
        "test_name": "Multi-Joint Arm Gravity Compensation Equilibrium",
        "passed": passed,
        "max_position_drift_rad": round(float(pos_drift), 5),
        "gravity_torques_nm": [round(float(t), 2) for t in gravity_torques],
        "tolerance": 0.02,
    }


def run_elastic_collision_benchmark(duration: float = 0.5, dt: float = 0.0005) -> Dict[str, Any]:
    """
    Test 4: Elastic collision between two identical spheres.
    Verifies linear momentum conservation: P_initial = P_final.
    """
    m1 = 1.5
    m2 = 1.5
    v1_init = 2.0
    v2_init = 0.0

    xml = f"""
    <mujoco model="collision_test">
      <option timestep="{dt}" gravity="0 0 0" integrator="RK4"/>
      <worldbody>
        <body name="ball1" pos="-0.5 0 0">
          <freejoint/>
          <inertial pos="0 0 0" mass="{m1}" diaginertia="0.01 0.01 0.01"/>
          <geom type="sphere" size="0.1" friction="0 0 0" margin="0.0001"/>
        </body>
        <body name="ball2" pos="0.5 0 0">
          <freejoint/>
          <inertial pos="0 0 0" mass="{m2}" diaginertia="0.01 0.01 0.01"/>
          <geom type="sphere" size="0.1" friction="0 0 0" margin="0.0001"/>
        </body>
      </worldbody>
    </mujoco>
    """
    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)

    # Set initial velocities
    data.qvel[0] = v1_init  # ball1 vx
    data.qvel[6] = v2_init  # ball2 vx

    p_initial = m1 * v1_init + m2 * v2_init

    steps = int(duration / dt)
    for _ in range(steps):
        mujoco.mj_step(model, data)

    v1_final = float(data.qvel[0])
    v2_final = float(data.qvel[6])
    p_final = m1 * v1_final + m2 * v2_final

    momentum_error = abs(p_final - p_initial)
    rel_error = momentum_error / p_initial
    passed = bool(rel_error < 0.01)

    return {
        "test_name": "Object Collision Linear Momentum Conservation",
        "passed": passed,
        "initial_momentum_kg_mps": round(p_initial, 4),
        "final_momentum_kg_mps": round(p_final, 4),
        "momentum_error": round(momentum_error, 6),
        "relative_error": round(rel_error, 6),
        "tolerance": 0.01,
    }


def run_sliding_friction_benchmark(duration: float = 2.0, dt: float = 0.001) -> Dict[str, Any]:
    """
    Test 5: Frictional contact scenario (Block sliding on a flat horizontal plane).
    Analytical:
      a = -mu * g
      d_stop = v0^2 / (2 * mu * g)
    """
    g = 9.81
    mu = 0.25
    m = 2.0
    v0 = 2.0

    xml = f"""
    <mujoco model="friction_test">
      <option timestep="{dt}" gravity="0 0 {-g}" integrator="RK4"/>
      <worldbody>
        <geom name="ground" type="plane" size="5 5 0.1" friction="{mu} 0.005 0.0001"/>
        <body name="box" pos="0 0 0.05">
          <freejoint/>
          <inertial pos="0 0 0" mass="{m}" diaginertia="0.005 0.005 0.005"/>
          <geom type="box" size="0.05 0.05 0.05" friction="{mu} 0.005 0.0001"/>
        </body>
      </worldbody>
    </mujoco>
    """
    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)

    data.qvel[0] = v0

    analytical_stop_dist = (v0 ** 2) / (2.0 * mu * g)

    steps = int(duration / dt)
    for _ in range(steps):
        mujoco.mj_step(model, data)

    x_sim = float(data.qpos[0])
    dist_error = abs(x_sim - analytical_stop_dist)
    rel_error = dist_error / analytical_stop_dist

    # In MuJoCo soft-contact dynamics, error is typically under 3%
    passed = bool(rel_error < 0.05)

    return {
        "test_name": "Coulomb Sliding Friction Deceleration",
        "passed": passed,
        "initial_velocity_mps": v0,
        "stopping_distance_sim_m": round(x_sim, 4),
        "stopping_distance_analytical_m": round(analytical_stop_dist, 4),
        "distance_error_m": round(dist_error, 4),
        "relative_error": round(rel_error, 4),
        "tolerance": 0.05,
    }


def run_all_physics_benchmarks() -> Dict[str, Any]:
    """Executes all 5 controlled physics benchmarks and aggregates validation report."""
    results = [
        run_free_fall_benchmark(),
        run_pendulum_energy_conservation_benchmark(),
        run_multi_joint_static_equilibrium_benchmark(),
        run_elastic_collision_benchmark(),
        run_sliding_friction_benchmark(),
    ]
    all_passed = all(r["passed"] for r in results)
    return {
        "all_passed": all_passed,
        "suite_count": len(results),
        "passed_count": sum(1 for r in results if r["passed"]),
        "results": results,
    }
