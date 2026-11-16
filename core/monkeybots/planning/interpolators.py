"""
MonkeyBots Trajectory Interpolation Algorithms.

Provides mathematically rigorous, boundary-constrained polynomial interpolators:
1. Linear with parabolic blends (Trapezoidal velocity)
2. Cubic Polynomial Splines (C1 continuity: position & velocity continuous)
3. Quintic Polynomial Splines (C2 continuity: position, velocity, and acceleration continuous, bounded jerk)
"""

import math
from typing import Tuple
import numpy as np


class CubicSegment:
    """
    Cubic polynomial trajectory segment for single degree of freedom:
    s(t) = a0 + a1*t + a2*t^2 + a3*t^3
    Satisfies boundary conditions:
    s(0) = q0, s(T) = qf, s_dot(0) = v0, s_dot(T) = vf
    """

    def __init__(self, q0: float, qf: float, v0: float, vf: float, duration: float):
        self.q0 = float(q0)
        self.qf = float(qf)
        self.v0 = float(v0)
        self.vf = float(vf)
        self.T = max(1e-6, float(duration))

        # Solve boundary constraints
        delta_q = self.qf - self.q0
        T2 = self.T * self.T
        T3 = T2 * self.T

        self.a0 = self.q0
        self.a1 = self.v0
        self.a2 = (3.0 * delta_q - (2.0 * self.v0 + self.vf) * self.T) / T2
        self.a3 = (-2.0 * delta_q + (self.v0 + self.vf) * self.T) / T3

    def evaluate(self, t: float) -> Tuple[float, float, float]:
        """Returns (position, velocity, acceleration) at time t in [0, T]."""
        t = np.clip(t, 0.0, self.T)
        t2 = t * t
        t3 = t2 * t

        pos = self.a0 + self.a1 * t + self.a2 * t2 + self.a3 * t3
        vel = self.a1 + 2.0 * self.a2 * t + 3.0 * self.a3 * t2
        acc = 2.0 * self.a2 + 6.0 * self.a3 * t
        return float(pos), float(vel), float(acc)


class QuinticSegment:
    """
    Quintic polynomial trajectory segment for single degree of freedom:
    s(t) = c0 + c1*t + c2*t^2 + c3*t^3 + c4*t^4 + c5*t^5
    Satisfies boundary conditions:
    s(0) = q0, s(T) = qf
    s_dot(0) = v0, s_dot(T) = vf
    s_ddot(0) = a0, s_ddot(T) = af
    Ensures C2 continuity with smooth, zero-discontinuity jerk profiles.
    """

    def __init__(
        self,
        q0: float,
        qf: float,
        v0: float = 0.0,
        vf: float = 0.0,
        a0: float = 0.0,
        af: float = 0.0,
        duration: float = 1.0,
    ):
        self.q0 = float(q0)
        self.qf = float(qf)
        self.v0 = float(v0)
        self.vf = float(vf)
        self.a0 = float(a0)
        self.af = float(af)
        self.T = max(1e-6, float(duration))

        delta_q = self.qf - self.q0
        T = self.T
        T2 = T * T
        T3 = T2 * T
        T4 = T3 * T
        T5 = T4 * T

        self.c0 = self.q0
        self.c1 = self.v0
        self.c2 = 0.5 * self.a0
        self.c3 = (20.0 * delta_q - (8.0 * self.vf + 12.0 * self.v0) * T - (3.0 * self.a0 - self.af) * T2) / (2.0 * T3)
        self.c4 = (-30.0 * delta_q + (14.0 * self.vf + 16.0 * self.v0) * T + (3.0 * self.a0 - 2.0 * self.af) * T2) / (2.0 * T4)
        self.c5 = (12.0 * delta_q - 6.0 * (self.vf + self.v0) * T - (self.a0 - self.af) * T2) / (2.0 * T5)

    def evaluate(self, t: float) -> Tuple[float, float, float]:
        """Returns (position, velocity, acceleration) at time t in [0, T]."""
        t = np.clip(t, 0.0, self.T)
        t2 = t * t
        t3 = t2 * t
        t4 = t3 * t
        t5 = t4 * t

        pos = self.c0 + self.c1 * t + self.c2 * t2 + self.c3 * t3 + self.c4 * t4 + self.c5 * t5
        vel = self.c1 + 2.0 * self.c2 * t + 3.0 * self.c3 * t2 + 4.0 * self.c4 * t3 + 5.0 * self.c5 * t4
        acc = 2.0 * self.c2 + 6.0 * self.c3 * t + 12.0 * self.c4 * t2 + 20.0 * self.c5 * t3
        return float(pos), float(vel), float(acc)


class TrapezoidalSegment:
    """
    Linear trajectory with parabolic blend (trapezoidal velocity).
    Provides constant-velocity cruising with constant acceleration/deceleration phases.
    """

    def __init__(self, q0: float, qf: float, v_max: float, a_max: float):
        self.q0 = float(q0)
        self.qf = float(qf)
        delta_q = self.qf - self.q0
        self.sign = 1.0 if delta_q >= 0.0 else -1.0
        h = abs(delta_q)

        v_max = max(1e-4, abs(v_max))
        a_max = max(1e-4, abs(a_max))

        # Check if triangular profile is required (distance too short to reach v_max)
        if v_max * v_max / a_max > h:
            # Triangular profile
            self.v_cruise = math.sqrt(h * a_max)
            self.t_acc = self.v_cruise / a_max
            self.t_flat = 0.0
            self.t_dec = self.t_acc
            self.T = 2.0 * self.t_acc
        else:
            # Full trapezoidal profile
            self.v_cruise = v_max
            self.t_acc = self.v_cruise / a_max
            self.t_flat = (h - (self.v_cruise * self.v_cruise / a_max)) / self.v_cruise
            self.t_dec = self.t_acc
            self.T = 2.0 * self.t_acc + self.t_flat

        self.a_acc = a_max

    def evaluate(self, t: float) -> Tuple[float, float, float]:
        """Returns (position, velocity, acceleration) at time t in [0, T]."""
        t = np.clip(t, 0.0, self.T)
        t_acc = self.t_acc
        t_flat = self.t_flat

        if t <= t_acc:
            # Acceleration phase: s(t) = 0.5 * a * t^2
            p = 0.5 * self.a_acc * t * t
            v = self.a_acc * t
            a = self.a_acc
        elif t <= (t_acc + t_flat):
            # Constant velocity cruise phase
            dt = t - t_acc
            p = 0.5 * self.a_acc * t_acc * t_acc + self.v_cruise * dt
            v = self.v_cruise
            a = 0.0
        else:
            # Deceleration phase
            dt = self.T - t
            p = abs(self.qf - self.q0) - 0.5 * self.a_acc * dt * dt
            v = self.a_acc * dt
            a = -self.a_acc

        pos = self.q0 + self.sign * p
        vel = self.sign * v
        acc = self.sign * a
        return float(pos), float(vel), float(acc)
