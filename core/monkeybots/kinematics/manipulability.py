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
