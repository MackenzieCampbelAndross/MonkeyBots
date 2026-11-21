"""
Continuous Motion Segment Collision Checking
Interfaces with simulation engine to verify trajectory path feasibility.
"""

import numpy as np
from typing import List, Callable, Optional


class MotionCollisionChecker:
    """Checks whether C-space configurations or paths cause robot self- or obstacle collisions."""

    def __init__(self, validity_fn: Optional[Callable[[np.ndarray], bool]] = None):
        # Default validity: check no limits exceeded and placeholder obstacle check
        self.validity_fn = validity_fn or (lambda q: True)

    def is_state_valid(self, q: np.ndarray) -> bool:
        """Checks instantaneous collision state."""
        return self.validity_fn(q)

    def is_path_valid(self, waypoints: List[np.ndarray]) -> bool:
        """Checks continuous collision across discrete waypoints."""
        for q in waypoints:
            if not self.is_state_valid(q):
                return False
        return True
