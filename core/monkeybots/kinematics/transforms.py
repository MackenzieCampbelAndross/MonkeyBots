"""
MonkeyBots Spatial Mathematics and Coordinate Transformations.

Provides rigorous SE(3) and SO(3) geometric operations:
- 4x4 Homogeneous transformation matrices
- 3x3 Rotation matrices (orthonormal SO(3))
- Quaternions [w, x, y, z] with Hamilton product, SLERP, and logarithmic maps
- Rodrigues rotation formula
- Euler RPY (Roll-Pitch-Yaw) angle conversions
"""

import math
from typing import List, Tuple, Union
import numpy as np


def normalize_vector(v: Union[List[float], np.ndarray]) -> np.ndarray:
    """Normalize a 3D vector to unit length. Handles zero vectors safely."""
    arr = np.asarray(v, dtype=np.float64)
    norm = np.linalg.norm(arr)
    if norm < 1e-12:
        return np.zeros_like(arr)
    return arr / norm


def euler_to_rotation_matrix(roll: float, pitch: float, yaw: float) -> np.ndarray:
    """
    Computes 3x3 rotation matrix from Roll-Pitch-Yaw angles (extrinsic XYZ / intrinsic Z-Y-X).
    Standard convention used in URDF and robotics:
    R = Rz(yaw) * Ry(pitch) * Rx(roll)
    """
    cr = math.cos(roll)
    sr = math.sin(roll)
    cp = math.cos(pitch)
    sp = math.sin(pitch)
    cy = math.cos(yaw)
    sy = math.sin(yaw)

    R = np.array([
        [cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
        [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
        [-sp, cp * sr, cp * cr]
    ], dtype=np.float64)
    return R


def rotation_matrix_to_euler(R: np.ndarray) -> Tuple[float, float, float]:
    """
    Extracts Roll, Pitch, Yaw angles from a 3x3 rotation matrix.
    Handles gimbal lock (pitch = +- pi/2) gracefully.
    Returns (roll, pitch, yaw) in radians.
    """
    R = np.asarray(R, dtype=np.float64)
    pitch = -math.asin(np.clip(R[2, 0], -1.0, 1.0))
    cp = math.cos(pitch)

    if abs(cp) > 1e-6:
        roll = math.atan2(R[2, 1], R[2, 2])
        yaw = math.atan2(R[1, 0], R[0, 0])
    else:
        # Gimbal lock: roll and yaw are coupled
        roll = 0.0
        yaw = math.atan2(-R[0, 1], R[1, 1])

    return float(roll), float(pitch), float(yaw)


def axis_angle_to_rotation_matrix(axis: Union[List[float], np.ndarray], angle: float) -> np.ndarray:
    """
    Rodrigues rotation formula: rotation matrix for rotation of 'angle' radians
    around an arbitrary 3D unit axis.
    R = I + sin(theta) * [k]_x + (1 - cos(theta)) * [k]_x^2
    """
    k = normalize_vector(axis)
    if np.linalg.norm(k) < 1e-9 or abs(angle) < 1e-12:
        return np.eye(3, dtype=np.float64)

    kx, ky, kz = k[0], k[1], k[2]
    K = np.array([
        [0.0, -kz, ky],
        [kz, 0.0, -kx],
        [-ky, kx, 0.0]
    ], dtype=np.float64)

    c = math.cos(angle)
    s = math.sin(angle)
    R = np.eye(3, dtype=np.float64) + s * K + (1.0 - c) * (K @ K)
    return R


def quaternion_from_rotation_matrix(R: np.ndarray) -> np.ndarray:
    """
    Converts 3x3 rotation matrix to unit quaternion [w, x, y, z].
    Uses Shepperd's algorithm for numerical stability.
    """
    R = np.asarray(R, dtype=np.float64)
    trace = R[0, 0] + R[1, 1] + R[2, 2]

    if trace > 0.0:
        s = 0.5 / math.sqrt(trace + 1.0)
        w = 0.25 / s
        x = (R[2, 1] - R[1, 2]) * s
        y = (R[0, 2] - R[2, 0]) * s
        z = (R[1, 0] - R[0, 1]) * s
    elif (R[0, 0] > R[1, 1]) and (R[0, 0] > R[2, 2]):
        s = 2.0 * math.sqrt(max(1e-12, 1.0 + R[0, 0] - R[1, 1] - R[2, 2]))
        w = (R[2, 1] - R[1, 2]) / s
        x = 0.25 * s
        y = (R[0, 1] + R[1, 0]) / s
        z = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = 2.0 * math.sqrt(max(1e-12, 1.0 + R[1, 1] - R[0, 0] - R[2, 2]))
        w = (R[0, 2] - R[2, 0]) / s
        x = (R[0, 1] + R[1, 0]) / s
        y = 0.25 * s
        z = (R[1, 2] + R[2, 1]) / s
    else:
        s = 2.0 * math.sqrt(max(1e-12, 1.0 + R[2, 2] - R[0, 0] - R[1, 1]))
        w = (R[1, 0] - R[0, 1]) / s
        x = (R[0, 2] + R[2, 0]) / s
        y = (R[1, 2] + R[2, 1]) / s
        z = 0.25 * s

    q = np.array([w, x, y, z], dtype=np.float64)
    return q / np.linalg.norm(q)


def quaternion_to_rotation_matrix(q: Union[List[float], np.ndarray]) -> np.ndarray:
    """
    Converts unit quaternion [w, x, y, z] to 3x3 orthonormal rotation matrix SO(3).
    """
    q_arr = np.asarray(q, dtype=np.float64)
    norm = np.linalg.norm(q_arr)
    if norm < 1e-12:
        return np.eye(3, dtype=np.float64)
    w, x, y, z = q_arr / norm

    return np.array([
        [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)],
        [2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)],
        [2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)]
    ], dtype=np.float64)


def quaternion_multiply(q1: Union[List[float], np.ndarray], q2: Union[List[float], np.ndarray]) -> np.ndarray:
    """
    Hamilton quaternion product q = q1 * q2, both in [w, x, y, z] format.
    Represents sequential rotation: first q2, then q1.
    """
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2

    return np.array([
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2
    ], dtype=np.float64)


def quaternion_conjugate(q: Union[List[float], np.ndarray]) -> np.ndarray:
    """Returns quaternion conjugate [w, -x, -y, -z]."""
    w, x, y, z = q
    return np.array([w, -x, -y, -z], dtype=np.float64)


def quaternion_error(q_current: np.ndarray, q_target: np.ndarray) -> np.ndarray:
    """
    Computes 3D angular orientation error vector e_omega in radians.
    Given current orientation qc and desired target qt, error is:
    q_err = qt * qc^-1
    For small errors, e_omega = 2 * sgn(q_err[0]) * q_err[1:4].
    """
    qc = q_current / np.linalg.norm(q_current)
    qt = q_target / np.linalg.norm(q_target)

    # Shortest path check: if dot product is negative, negate target quaternion
    if np.dot(qc, qt) < 0.0:
        qt = -qt

    q_err = quaternion_multiply(qt, quaternion_conjugate(qc))
    # Vector part scaled by angle
    w = np.clip(q_err[0], -1.0, 1.0)
    angle = 2.0 * math.acos(w)
    sin_half = math.sin(angle / 2.0)

    if abs(sin_half) < 1e-7:
        return np.zeros(3, dtype=np.float64)

    axis = q_err[1:4] / sin_half
    return axis * angle


def homogeneous_transform(R: np.ndarray, p: Union[List[float], np.ndarray]) -> np.ndarray:
    """Constructs 4x4 homogeneous transformation matrix SE(3) from 3x3 R and 3x1 p."""
    T = np.eye(4, dtype=np.float64)
    T[0:3, 0:3] = R
    T[0:3, 3] = np.asarray(p, dtype=np.float64)
    return T


def transform_inverse(T: np.ndarray) -> np.ndarray:
    """
    Computes exact analytical inverse of 4x4 SE(3) transformation:
    T^-1 = [[R^T, -R^T * p], [0, 1]]
    """
    R = T[0:3, 0:3]
    p = T[0:3, 3]
    T_inv = np.eye(4, dtype=np.float64)
    T_inv[0:3, 0:3] = R.T
    T_inv[0:3, 3] = -R.T @ p
    return T_inv
