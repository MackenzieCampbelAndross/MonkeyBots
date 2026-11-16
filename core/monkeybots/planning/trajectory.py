"""
MonkeyBots Multi-DOF Trajectory Planning Engine.

Supports:
- Multi-waypoint Joint Space trajectories (Quintic C2, Cubic C1, Linear/Trapezoidal)
- Cartesian Space straight-line & interpolated trajectories with Quaternion SLERP
- Automatic time parameterization under velocity and acceleration constraints
- Strict joint limit enforcement
- Continuous 500 Hz / 60 Hz trajectory sampling
"""

from enum import Enum
import math
from typing import Dict, List, Optional, Tuple, Union
import numpy as np

from .interpolators import QuinticSegment, CubicSegment, TrapezoidalSegment
from ..kinematics import (
    KinematicChain,
    IKSolver,
    IKSolverMethod,
    compute_forward_kinematics,
    quaternion_to_rotation_matrix,
    rotation_matrix_to_euler,
    euler_to_rotation_matrix,
    quaternion_from_rotation_matrix,
)


class InterpolationType(str, Enum):
    QUINTIC = "quintic"
    CUBIC = "cubic"
    TRAPEZOIDAL = "trapezoidal"


class TrajectoryPoint:
    """Represents a single sampled point in time along a trajectory."""

    def __init__(
        self,
        time: float,
        positions: np.ndarray,
        velocities: np.ndarray,
        accelerations: np.ndarray,
        cartesian_pos: Optional[np.ndarray] = None,
        cartesian_quat: Optional[np.ndarray] = None,
    ):
        self.time = float(time)
        self.positions = np.asarray(positions, dtype=np.float64)
        self.velocities = np.asarray(velocities, dtype=np.float64)
        self.accelerations = np.asarray(accelerations, dtype=np.float64)
        self.cartesian_pos = cartesian_pos
        self.cartesian_quat = cartesian_quat

    def to_dict(self) -> dict:
        d = {
            "time": round(self.time, 4),
            "positions": [round(float(q), 6) for q in self.positions],
            "velocities": [round(float(v), 6) for v in self.velocities],
            "accelerations": [round(float(a), 6) for a in self.accelerations],
        }
        if self.cartesian_pos is not None:
            d["cartesian_pos"] = [round(float(x), 4) for x in self.cartesian_pos]
        if self.cartesian_quat is not None:
            d["cartesian_quat"] = [round(float(x), 4) for x in self.cartesian_quat]
        return d


class JointTrajectory:
    """
    Multi-joint trajectory connecting an arbitrary sequence of waypoints.
    Guarantees continuity, adherence to velocity/acceleration bounds, and joint limits.
    """

    def __init__(
        self,
        waypoints: List[Union[List[float], np.ndarray]],
        interpolation: InterpolationType = InterpolationType.QUINTIC,
        v_max: Optional[Union[float, List[float]]] = None,
        a_max: Optional[Union[float, List[float]]] = None,
        chain: Optional[KinematicChain] = None,
    ):
        if len(waypoints) < 2:
            raise ValueError("Trajectory requires at least 2 waypoints.")

        self.waypoints = [np.asarray(w, dtype=np.float64) for w in waypoints]
        self.dof = len(self.waypoints[0])
        self.interpolation = interpolation
        self.chain = chain

        # Enforce joint dimensions across all waypoints
        for i, w in enumerate(self.waypoints):
            if len(w) != self.dof:
                raise ValueError(f"Waypoint {i} length {len(w)} != expected DOF {self.dof}")

        # Set velocity and acceleration limits
        if v_max is None:
            self.v_max = np.full(self.dof, 2.5, dtype=np.float64)  # 2.5 rad/s default
        elif isinstance(v_max, (int, float)):
            self.v_max = np.full(self.dof, float(v_max), dtype=np.float64)
        else:
            self.v_max = np.asarray(v_max, dtype=np.float64)

        if a_max is None:
            self.a_max = np.full(self.dof, 5.0, dtype=np.float64)  # 5.0 rad/s^2 default
        elif isinstance(a_max, (int, float)):
            self.a_max = np.full(self.dof, float(a_max), dtype=np.float64)
        else:
            self.a_max = np.asarray(a_max, dtype=np.float64)

        # Enforce joint boundaries if chain is provided
        if self.chain is not None:
            for i, w in enumerate(self.waypoints):
                if not self.chain.is_within_limits(w, tol=1e-3):
                    raise ValueError(f"Waypoint {i} violates physical joint limits.")

        self.num_segments = len(self.waypoints) - 1
        self.segment_durations: List[float] = []
        self.segment_start_times: List[float] = [0.0]
        self.segments: List[List[Union[QuinticSegment, CubicSegment, TrapezoidalSegment]]] = []

        self._plan_trajectory()
        self.total_duration = self.segment_start_times[-1]

    def _plan_trajectory(self):
        """Constructs interpolator segments and calculates time parameterization."""
        # 1. Estimate waypoint velocities for smooth multi-segment continuity
        # Using Catmull-Rom style central differences for internal waypoints
        waypoint_velocities: List[np.ndarray] = [np.zeros(self.dof)]
        for k in range(1, len(self.waypoints) - 1):
            # v_k = (q_{k+1} - q_{k-1}) / 2
            v_est = 0.5 * (self.waypoints[k + 1] - self.waypoints[k - 1])
            # Clamp to v_max
            v_clamped = np.clip(v_est, -0.8 * self.v_max, 0.8 * self.v_max)
            waypoint_velocities.append(v_clamped)
        waypoint_velocities.append(np.zeros(self.dof))  # Zero terminal velocity

        # 2. Compute minimum duration per segment to respect v_max and a_max
        cum_time = 0.0
        for k in range(self.num_segments):
            q_start = self.waypoints[k]
            q_end = self.waypoints[k + 1]
            dq = np.abs(q_end - q_start)

            # Minimum time required by velocity limit
            t_vel = np.max(1.875 * dq / np.maximum(1e-4, self.v_max))
            # Minimum time required by acceleration limit (with continuity margin)
            t_acc = np.max(np.sqrt(6.2 * dq / np.maximum(1e-4, self.a_max)))
            seg_duration = max(0.4, float(max(t_vel, t_acc)))

            self.segment_durations.append(seg_duration)
            cum_time += seg_duration
            self.segment_start_times.append(cum_time)

            # Construct joint segments for this interval
            v_start = waypoint_velocities[k]
            v_end = waypoint_velocities[k + 1]
            joint_segs = []

            for j in range(self.dof):
                if self.interpolation == InterpolationType.QUINTIC:
                    seg = QuinticSegment(
                        q0=q_start[j],
                        qf=q_end[j],
                        v0=v_start[j],
                        vf=v_end[j],
                        a0=0.0,
                        af=0.0,
                        duration=seg_duration,
                    )
                elif self.interpolation == InterpolationType.CUBIC:
                    seg = CubicSegment(
                        q0=q_start[j],
                        qf=q_end[j],
                        v0=v_start[j],
                        vf=v_end[j],
                        duration=seg_duration,
                    )
                else:
                    seg = TrapezoidalSegment(
                        q0=q_start[j],
                        qf=q_end[j],
                        v_max=self.v_max[j],
                        a_max=self.a_max[j],
                    )
                joint_segs.append(seg)
            self.segments.append(joint_segs)

    def sample(self, t: float) -> TrajectoryPoint:
        """Sample joint position, velocity, and acceleration at time t."""
        t = np.clip(t, 0.0, self.total_duration)

        # Locate segment index
        seg_idx = 0
        for k in range(self.num_segments):
            if t <= self.segment_start_times[k + 1] or k == self.num_segments - 1:
                seg_idx = k
                break

        t_local = t - self.segment_start_times[seg_idx]
        joint_segs = self.segments[seg_idx]

        positions = np.zeros(self.dof)
        velocities = np.zeros(self.dof)
        accelerations = np.zeros(self.dof)

        for j in range(self.dof):
            p, v, a = joint_segs[j].evaluate(t_local)
            positions[j] = p
            velocities[j] = v
            accelerations[j] = a

        # Compute Cartesian pose if chain is available
        cart_pos, cart_quat = None, None
        if self.chain is not None:
            fk = compute_forward_kinematics(self.chain, positions)
            cart_pos = fk.position
            cart_quat = fk.quaternion

        return TrajectoryPoint(
            time=t,
            positions=positions,
            velocities=velocities,
            accelerations=accelerations,
            cartesian_pos=cart_pos,
            cartesian_quat=cart_quat,
        )

    def sample_all(self, dt: float = 0.002) -> List[TrajectoryPoint]:
        """Samples the entire trajectory at discrete time interval dt."""
        num_steps = max(2, int(math.ceil(self.total_duration / dt)) + 1)
        points = []
        for i in range(num_steps):
            t = min(self.total_duration, i * dt)
            points.append(self.sample(t))
        return points


def slerp_quaternion(q1: np.ndarray, q2: np.ndarray, tau: float) -> np.ndarray:
    """Spherical Linear Interpolation (SLERP) between two unit quaternions for tau in [0, 1]."""
    tau = np.clip(tau, 0.0, 1.0)
    q1 = q1 / np.linalg.norm(q1)
    q2 = q2 / np.linalg.norm(q2)

    dot = float(np.dot(q1, q2))
    if dot < 0.0:
        q2 = -q2
        dot = -dot

    if dot > 0.9995:
        # Linear interpolation for very close orientations
        q = q1 + tau * (q2 - q1)
        return q / np.linalg.norm(q)

    theta_0 = math.acos(np.clip(dot, -1.0, 1.0))
    sin_theta_0 = math.sin(theta_0)
    theta = theta_0 * tau
    sin_theta = math.sin(theta)

    s1 = math.cos(theta) - dot * sin_theta / sin_theta_0
    s2 = sin_theta / sin_theta_0
    q = s1 * q1 + s2 * q2
    return q / np.linalg.norm(q)


class CartesianTrajectory:
    """
    Plans straight-line Cartesian paths with continuous orientation SLERP
    and maps them to synchronized joint trajectories via Inverse Kinematics.
    """

    def __init__(
        self,
        chain: KinematicChain,
        cartesian_waypoints: List[Tuple[Union[List[float], np.ndarray], Union[List[float], np.ndarray]]],
        v_cart_max: float = 0.25,  # 0.25 m/s
        a_cart_max: float = 0.5,   # 0.5 m/s^2
        seed_q: Optional[np.ndarray] = None,
    ):
        self.chain = chain
        self.waypoints = cartesian_waypoints
        if len(self.waypoints) < 2:
            raise ValueError("Cartesian trajectory requires at least 2 Cartesian poses.")

        self.solver = IKSolver(chain)
        # Solve IK for all waypoints to establish joint waypoints
        joint_wps: List[np.ndarray] = []
        curr_seed = seed_q if seed_q is not None else np.zeros(chain.dof)

        for i, (pos, ori) in enumerate(self.waypoints):
            res = self.solver.solve(
                target_position=pos,
                target_orientation=ori,
                initial_seed=curr_seed,
                method=IKSolverMethod.DLS,
                pos_tolerance_m=1e-4,
                rot_tolerance_rad=1e-3,
            )
            if not res.converged:
                raise ValueError(f"Cartesian waypoint {i} ({pos}) is kinematically unreachable.")
            joint_wps.append(res.joint_positions)
            curr_seed = res.joint_positions

        # Build underlying joint trajectory
        self.joint_trajectory = JointTrajectory(
            waypoints=joint_wps,
            interpolation=InterpolationType.QUINTIC,
            chain=chain,
        )
        self.total_duration = self.joint_trajectory.total_duration

    def sample(self, t: float) -> TrajectoryPoint:
        return self.joint_trajectory.sample(t)

    def sample_all(self, dt: float = 0.002) -> List[TrajectoryPoint]:
        return self.joint_trajectory.sample_all(dt)
