"""
Manipulability Analysis and Ellipsoid Metric Engine
Implements Yoshikawa manipulability index, Jacobian SVD decomposition,
and spatial velocity ellipsoid extraction.
"""

import numpy as np
from typing import Dict, Any, Tuple


def compute_yoshikawa_index(J: np.ndarray) -> float:
    """Calculates Yoshikawa manipulability index w = sqrt(det(J * J^T))."""
    JJT = J @ J.T
    det = np.linalg.det(JJT)
    return float(np.sqrt(max(0.0, det)))


def decompose_manipulability_ellipsoid(J: np.ndarray) -> Dict[str, Any]:
    """
    Performs Singular Value Decomposition (SVD) on the spatial Jacobian
    to extract velocity ellipsoid principal axes, radii, and condition numbers.
    """
    # Decompose into translational (top 3 rows) and rotational (bottom 3 rows)
    J_trans = J[:3, :]
    J_rot = J[3:, :]

    # SVD for translational ellipsoid
    U_t, S_t, _ = np.linalg.svd(J_trans)
    # SVD for rotational ellipsoid
    U_r, S_r, _ = np.linalg.svd(J_rot)

    # Full 6D SVD
    _, S_full, _ = np.linalg.svd(J)

    cond_num = min(100000.0, float(S_full[0] / S_full[-1])) if S_full[-1] > 1e-9 else 100000.0

    return {
        "yoshikawa_index": compute_yoshikawa_index(J),
        "condition_number": round(cond_num, 4),
        "translational": {
            "radii": [round(float(s), 5) for s in S_t],
            "axes": [[round(float(v), 5) for v in row] for row in U_t],
            "volume": float(np.prod(S_t)),
        },
        "rotational": {
            "radii": [round(float(s), 5) for s in S_r],
            "axes": [[round(float(v), 5) for v in row] for row in U_r],
            "volume": float(np.prod(S_r)),
        },
    }
