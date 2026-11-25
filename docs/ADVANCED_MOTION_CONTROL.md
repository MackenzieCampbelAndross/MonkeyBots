# Advanced Motion Control & Kinematic Dexterity

This document outlines the theoretical formulations and practical implementations of the advanced motion control subsystem in MonkeyBots.

## 1. Cartesian Impedance Control

Compliant interaction with the environment is governed by task-space impedance:

$$\\tau = J^T (K_p \\tilde{x} + D_p \\tilde{v}) + (I - J^T J^{\\dagger T}) \\tau_0 + g(q)$$

Where:
* $K_p \\in \\mathbb{R}^{6 \\times 6}$ is positive-definite task-space stiffness.
* $D_p \\in \\mathbb{R}^{6 \\times 6}$ is damping designed to satisfy passivity constraints ($D_p = 2 \\sqrt{K_p}$).
* $(I - J^T J^{\\dagger T})$ projects secondary posture optimization torques into the kinematic null-space.

## 2. Time-Optimal Path Parameterization (TOPP-RA)

Geometric paths $q(s)$ parameterized by arc-length $s \\in [0, 1]$ are time-scaled to maximize speed under actuator velocity and torque bounds:

$$\\min_{s(t)} T = \\int_0^1 \\frac{1}{\\dot{s}} ds$$

Subject to:
* $\\dot{q}_{min} \\le q'(s) \\dot{s} \\le \\dot{q}_{max}$
* $\\tau_{min} \\le M(q) (q'' \\dot{s}^2 + q' \\ddot{s}) + C(q, q') \\dot{s}^2 + g(q) \\le \\tau_{max}$

## 3. Real-Time 3D SVD Ellipsoid Inspection

The manipulability ellipsoid visualizes directional dexterity at the tool center point:

$$v^T (J J^T)^{-1} v \\le 1$$

Decomposition via Singular Value Decomposition ($J = U \\Sigma V^T$) yields principal semi-axes $u_i \\sigma_i$.
