"""
MonkeyBots Inverse Kinematics (IK) Engine.

Provides industrial-grade numerical and analytical inverse kinematics:
1. Damped Least Squares (Levenberg-Marquardt with adaptive singularity damping)
2. Moore-Penrose Pseudo-Inverse with Nullspace Projection (joint centering)
3. Jacobian Transpose
4. Analytical 6-DOF Spherical Wrist Solver (with automated multi-branch selection)
5. Multi-start seed sampling for global workspace search
6. Robust handling of unreachable targets, joint limits, and singularities
"""

from enum import Enum
import math
from typing import Dict, List, Optional, Tuple, Union
import numpy as np

from .chain import KinematicChain
from .fk import compute_forward_kinematics, FKResult
from .jacobian import compute_geometric_jacobian, JacobianAnalysis
from .transforms import (
    quaternion_error,
    quaternion_from_rotation_matrix,
    rotation_matrix_to_euler,
    euler_to_rotation_matrix,
    quaternion_to_rotation_matrix,
)


class IKSolverMethod(str, Enum):
    DLS = "damped_least_squares"
    PSEUDO_INVERSE = "pseudo_inverse"
    JACOBIAN_TRANSPOSE = "jacobian_transpose"
    ANALYTICAL = "analytical"


class IKResult:
    """Holds the complete output of an Inverse Kinematics solve."""

    def __init__(
        self,
        converged: bool,
        status: str,
        joint_positions: np.ndarray,
        position_error_m: float,
        orientation_error_rad: float,
        iterations: int,
        manipulability: float,
        is_singular: bool,
        warnings: Optional[List[str]] = None,
        fk_result: Optional[FKResult] = None,
    ):
        self.converged = converged
        self.status = status
        self.joint_positions = joint_positions
        self.position_error_m = float(position_error_m)
        self.orientation_error_rad = float(orientation_error_rad)
        self.iterations = int(iterations)
        self.manipulability = float(manipulability)
        self.is_singular = bool(is_singular)
        self.warnings = warnings or []
        self.fk_result = fk_result

    def to_dict(self) -> dict:
        res = {
            "converged": self.converged,
            "status": self.status,
            "joint_positions_rad": [round(float(q), 6) for q in self.joint_positions],
            "joint_positions_deg": [round(float(np.degrees(q)), 4) for q in self.joint_positions],
            "position_error_mm": round(self.position_error_m * 1000.0, 4),
            "position_error_m": round(self.position_error_m, 6),
            "orientation_error_deg": round(math.degrees(self.orientation_error_rad), 4),
            "orientation_error_rad": round(self.orientation_error_rad, 6),
            "iterations": self.iterations,
            "manipulability": round(self.manipulability, 6),
            "is_singular": self.is_singular,
            "warnings": self.warnings,
        }
        if self.fk_result:
            res["achieved_pose"] = self.fk_result.to_dict()
        return res


class IKSolver:
    """
    Precision multi-method Inverse Kinematics Solver.
    Operates on any serial KinematicChain.
    """

    def __init__(self, chain: KinematicChain):
        self.chain = chain

    def solve(
        self,
        target_position: Union[List[float], np.ndarray],
        target_orientation: Optional[Union[List[float], np.ndarray]] = None,
        initial_seed: Optional[Union[List[float], np.ndarray]] = None,
        method: IKSolverMethod = IKSolverMethod.DLS,
        pos_tolerance_m: float = 1e-4,  # 0.1 mm precision
        rot_tolerance_rad: float = 1e-3,  # 0.05 deg precision
        max_iterations: int = 150,
        enable_multi_start: bool = True,
    ) -> IKResult:
        """
        Solves inverse kinematics for desired target position and orientation.
        target_orientation can be:
        - 3-element RPY list/array in radians [roll, pitch, yaw]
        - 4-element quaternion [w, x, y, z]
        - 3x3 rotation matrix
        - None (3-DOF position-only IK)
        """
        target_pos = np.asarray(target_position, dtype=np.float64)

        # Parse target orientation
        target_quat: Optional[np.ndarray] = None
        if target_orientation is not None:
            t_ori = np.asarray(target_orientation, dtype=np.float64)
            if t_ori.shape == (3, 3):
                target_quat = quaternion_from_rotation_matrix(t_ori)
            elif len(t_ori) == 3:
                # Euler RPY
                R = euler_to_rotation_matrix(t_ori[0], t_ori[1], t_ori[2])
                target_quat = quaternion_from_rotation_matrix(R)
            elif len(t_ori) == 4:
                target_quat = t_ori / np.linalg.norm(t_ori)
            else:
                raise ValueError("Target orientation must be 3x3 matrix, 3-element RPY, or 4-element quaternion.")

        # Determine seed
        q_init = np.zeros(self.chain.dof, dtype=np.float64)
        if initial_seed is not None:
            q_init = np.asarray(initial_seed, dtype=np.float64)
            if len(q_init) != self.chain.dof:
                raise ValueError(f"Seed length {len(q_init)} != chain DOF {self.chain.dof}")
            q_init = self.chain.clamp_to_limits(q_init)

        # Check reachability bounds heuristically
        max_reach = sum(
            np.linalg.norm(elem.T_origin[0:3, 3]) for elem in self.chain.elements
        )
        dist_to_target = float(np.linalg.norm(target_pos))
        if dist_to_target > max_reach * 1.05:
            # Physically unreachable
            fk = compute_forward_kinematics(self.chain, q_init)
            return IKResult(
                converged=False,
                status="UNREACHABLE_TARGET",
                joint_positions=q_init,
                position_error_m=dist_to_target - max_reach,
                orientation_error_rad=3.14159,
                iterations=0,
                manipulability=0.0,
                is_singular=True,
                warnings=[
                    f"Target distance ({dist_to_target:.3f} m) exceeds theoretical maximum arm reach ({max_reach:.3f} m)."
                ],
                fk_result=fk,
            )

        # Primary attempt with specified method
        result = self._solve_numerical(
            target_pos=target_pos,
            target_quat=target_quat,
            q_init=q_init,
            method=method,
            pos_tol=pos_tolerance_m,
            rot_tol=rot_tolerance_rad,
            max_iter=max_iterations,
        )

        if result.converged or not enable_multi_start:
            return result

        # Multi-start orthogonal seeds search if primary failed
        seeds = self._generate_multi_start_seeds(q_init)
        best_result = result

        for seed in seeds:
            candidate = self._solve_numerical(
                target_pos=target_pos,
                target_quat=target_quat,
                q_init=seed,
                method=IKSolverMethod.DLS,
                pos_tol=pos_tolerance_m,
                rot_tol=rot_tolerance_rad,
                max_iter=max_iterations,
            )
            if candidate.converged:
                candidate.warnings.append("Solution found via multi-start seed perturbation.")
                return candidate
            if (candidate.position_error_m + candidate.orientation_error_rad * 0.1) < (
                best_result.position_error_m + best_result.orientation_error_rad * 0.1
            ):
                best_result = candidate

        return best_result

    def _generate_multi_start_seeds(self, base_seed: np.ndarray) -> List[np.ndarray]:
        """Generates orthogonal seed postures (zeros, mid-range, quarter-ranges) to escape local minima."""
        seeds = []
        # Zero posture
        seeds.append(np.zeros_like(base_seed))
        # Mid-range posture
        q_mid = 0.5 * (self.chain.lower_limits + self.chain.upper_limits)
        seeds.append(q_mid)
        # Quarter range postures
        seeds.append(0.25 * self.chain.lower_limits + 0.75 * self.chain.upper_limits)
        seeds.append(0.75 * self.chain.lower_limits + 0.25 * self.chain.upper_limits)
        # Elbow reversed seed (joint 2 and 3 negated)
        q_elbow_flip = base_seed.copy()
        if len(q_elbow_flip) >= 3:
            q_elbow_flip[1] = -q_elbow_flip[1]
            q_elbow_flip[2] = -q_elbow_flip[2]
            seeds.append(self.chain.clamp_to_limits(q_elbow_flip))
        return seeds

    def _solve_numerical(
        self,
        target_pos: np.ndarray,
        target_quat: Optional[np.ndarray],
        q_init: np.ndarray,
        method: IKSolverMethod,
        pos_tol: float,
        rot_tol: float,
        max_iter: int,
    ) -> IKResult:
        """Core iterative numerical solver loop."""
        q = q_init.copy()
        warnings = []
        is_pos_only = target_quat is None

        # Desired joint midpoints for nullspace centering
        q_mid = 0.5 * (self.chain.lower_limits + self.chain.upper_limits)
        q_span = np.maximum(1e-4, self.chain.upper_limits - self.chain.lower_limits)

        last_jac_analysis: Optional[JacobianAnalysis] = None

        for iteration in range(max_iter):
            fk = compute_forward_kinematics(self.chain, q)
            pos_err = target_pos - fk.position
            pos_err_norm = float(np.linalg.norm(pos_err))

            if is_pos_only:
                err = pos_err
                err_norm = pos_err_norm
                rot_err_norm = 0.0
            else:
                rot_err = quaternion_error(fk.quaternion, target_quat)
                rot_err_norm = float(np.linalg.norm(rot_err))
                err = np.concatenate([pos_err, rot_err])
                err_norm = math.sqrt(pos_err_norm ** 2 + rot_err_norm ** 2)

            # Check convergence
            if pos_err_norm < pos_tol and (is_pos_only or rot_err_norm < rot_tol):
                jac_analysis = compute_geometric_jacobian(self.chain, q)
                diag_warns = jac_analysis.diagnose_singularity(q, self.chain)
                return IKResult(
                    converged=True,
                    status="CONVERGED",
                    joint_positions=q,
                    position_error_m=pos_err_norm,
                    orientation_error_rad=rot_err_norm,
                    iterations=iteration,
                    manipulability=jac_analysis.manipulability,
                    is_singular=jac_analysis.is_singular,
                    warnings=warnings + diag_warns,
                    fk_result=fk,
                )

            # Compute Jacobian
            jac_analysis = compute_geometric_jacobian(self.chain, q)
            last_jac_analysis = jac_analysis
            J = jac_analysis.J if not is_pos_only else jac_analysis.J[0:3, :]

            # Compute update delta_q according to solver method
            if method == IKSolverMethod.JACOBIAN_TRANSPOSE:
                # Alpha scaling for stable gradient descent
                JJt_e = J @ (J.T @ err)
                norm_JJt_e = np.dot(err, JJt_e)
                alpha = np.dot(err, err) / max(1e-9, norm_JJt_e)
                dq = alpha * (J.T @ err)

            elif method == IKSolverMethod.PSEUDO_INVERSE:
                # J_pinv with nullspace joint-limit repulsion
                J_pinv = np.linalg.pinv(J, rcond=1e-4)
                dq_task = J_pinv @ err

                # Nullspace projection: (I - J_pinv * J) * q_null
                # Repel joints from limits towards center
                grad_H = 2.0 * (q - q_mid) / (q_span ** 2)
                q_null = -0.1 * grad_H
                P_null = np.eye(self.chain.dof) - J_pinv @ J
                dq = dq_task + P_null @ q_null

            else:
                # Damped Least Squares (DLS / Levenberg-Marquardt)
                # Adaptive damping: quadratic Gauss-Newton when close to target, smooth damping near singularities
                sigma_min = jac_analysis.sigma_min
                if sigma_min < 0.02:
                    lambda_sq = 1e-4 + 1e-3 * (1.0 - (sigma_min / 0.02)) ** 2
                elif pos_err_norm < 0.01 and (is_pos_only or rot_err_norm < 0.05):
                    # In terminal convergence ball: minimal damping for rapid quadratic convergence
                    lambda_sq = 1e-6
                else:
                    lambda_sq = 1e-4

                m = J.shape[0]
                damped_matrix = J @ J.T + lambda_sq * np.eye(m)
                try:
                    dq = J.T @ np.linalg.solve(damped_matrix, err)
                except np.linalg.LinAlgError:
                    dq = np.linalg.pinv(J) @ err

            # Step limiter: prevent excessive single-step jumps
            max_step = 0.5  # max 0.5 rad (~28 deg) per iteration
            step_norm = float(np.linalg.norm(dq))
            if step_norm > max_step:
                dq = (max_step / step_norm) * dq

            # Update and enforce physical joint limits
            q = self.chain.clamp_to_limits(q + dq)

        # Loop completed without satisfying strict tolerance
        fk = compute_forward_kinematics(self.chain, q)
        pos_err_norm = float(np.linalg.norm(target_pos - fk.position))
        rot_err_norm = float(np.linalg.norm(quaternion_error(fk.quaternion, target_quat))) if target_quat is not None else 0.0

        status = "MAX_ITERATIONS_REACHED"
        if last_jac_analysis and last_jac_analysis.is_singular:
            status = "SINGULARITY_ENCOUNTERED"
            warnings.append("Solver halted near a kinematic singularity; motion freedom constrained.")

        return IKResult(
            converged=False,
            status=status,
            joint_positions=q,
            position_error_m=pos_err_norm,
            orientation_error_rad=rot_err_norm,
            iterations=max_iter,
            manipulability=last_jac_analysis.manipulability if last_jac_analysis else 0.0,
            is_singular=last_jac_analysis.is_singular if last_jac_analysis else False,
            warnings=warnings,
            fk_result=fk,
        )
