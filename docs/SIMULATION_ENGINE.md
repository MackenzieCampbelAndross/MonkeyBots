# MonkeyBots | High-Fidelity Physics Simulation Engine Guide

**Physics Kernel:** DeepMind MuJoCo 4.0.1  
**Integration Rate:** 500 Hz ($\Delta t = 0.002\text{ s}$)  
**Execution:** Native C-accelerated rigid-body dynamics

---

## 1. Physics Engine Architecture

MonkeyBots embeds MuJoCo for deterministic, accurate physical simulation:
1. **Equations of Motion (Lagrangian Dynamics):**
   $$M(\mathbf{q}) \ddot{\mathbf{q}} + \mathbf{c}(\mathbf{q}, \dot{\mathbf{q}}) + \mathbf{g}(\mathbf{q}) = \boldsymbol{\tau} + J_c^T \mathbf{f}_c$$
   where $M(\mathbf{q})$ is the symmetric positive-definite inertia matrix, $\mathbf{c}$ encompasses Coriolis and centrifugal forces, $\mathbf{g}$ is the gravitational vector, $\boldsymbol{\tau}$ is the commanded motor torque vector, and $J_c^T \mathbf{f}_c$ captures contact forces.
2. **Contact & Collision Physics:**
   - Soft and rigid contact dynamics via convex optimization.
   - Coulomb friction cones approximated with polyhedral friction pyramids for real-time compliance.
   - Contact manifold tracking with normal force calculation $F_n$, tangential friction forces $F_t$, and restitution impulses.
3. **Numerical Integrators Supported:**
   - **RK4 (Runge-Kutta 4th Order):** Recommended for dynamic multi-joint arm trajectories.
   - **Euler (Semi-Implicit):** High-speed integration for rapid preview.
   - **Implicit Fast:** Recommended for stiff contact systems and multi-finger grasping.

---

## 2. Manipulation & Grasp Mechanics

The manipulation controller handles bilateral finger grasping through physics constraints:
- **Coulomb Friction Grasping:** Grasp security is governed by normal force $F_n$ and friction coefficient $\mu$:
  $$F_t \le \mu F_n$$
- **Pick-and-Place State Machine:**
  1. *Approach Pose:* IK target positioned $10\text{ cm}$ above the target object.
  2. *Descend:* Lower flange along Cartesian $Z$ to align gripper jaws.
  3. *Close Gripper:* Actuate left and right finger joints with commanded squeeze force (e.g., $15\text{ N}$).
  4. *Lift:* Elevate flange along $Z$; monitor contact normals to confirm object mass support.
  5. *Transport & Release:* Move to destination coordinates and release gripper force to $0\text{ N}$.
