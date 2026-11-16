# MonkeyBots | Robotics Kinematics, Planning & Control Algorithms

---

## 1. Forward Kinematics (FK)

The Forward Kinematics engine computes the exact position and orientation of every link and the tool flange in world coordinates:

### Homogeneous Transformations (SE(3))
Given joint coordinate $q_i$ for link $i$:
$$T_i(q_i) = T_{\text{origin}, i} \cdot T_{\text{joint}, i}(q_i)$$

For revolute joints rotating about unit axis $\hat{\mathbf{a}} = [a_x, a_y, a_z]^T$:
$$R(\hat{\mathbf{a}}, q_i) = \cos(q_i) I + \sin(q_i) [\hat{\mathbf{a}}]_\times + (1 - \cos(q_i)) (\hat{\mathbf{a}} \otimes \hat{\mathbf{a}})$$

The cumulative base-to-flange pose is given by:
$$T_{0}^{N}(\mathbf{q}) = \prod_{i=1}^{N} T_i(q_i) = \begin{bmatrix} R(\mathbf{q}) & \mathbf{p}(\mathbf{q}) \\ \mathbf{0}^T & 1 \end{bmatrix}$$

---

## 2. Inverse Kinematics (IK)

Given target pose $T_{\text{target}} = [\mathbf{p}_d, \mathbf{q}_d]$, solve for $\mathbf{q}^* \in \mathbb{R}^N$.

### Damped Least Squares (Levenberg-Marquardt with Singularity Avoidance)
To prevent extreme joint velocities near kinematic singularities ($\det(J J^T) \to 0$):
$$\Delta \mathbf{q} = J^T (J J^T + \lambda^2 I)^{-1} \mathbf{e}$$
where the adaptive damping factor is modulated by manipulability index $w = \sqrt{\det(J J^T)}$:
$$\lambda^2 = \begin{cases} 0 & w \ge w_0 \\ \lambda_0^2 \left(1 - \frac{w}{w_0}\right)^2 & w < w_0 \end{cases}$$

### Geodesic Orientation Error
Rotation error is evaluated via quaternion conjugate multiplication:
$$\Delta q = q_{\text{target}} \otimes q_{\text{current}}^{-1}$$
$$\mathbf{e}_{\text{rot}} = 2 \cdot \operatorname{sgn}(\Delta q_w) \cdot \Delta \mathbf{q}_{xyz}$$

---

## 3. Motion Planning: Multi-Segment Splines

### $C^2$ Continuous Quintic Polynomials
To prevent infinite actuator jerk, quintic trajectories guarantee continuity of position $q(t)$, velocity $\dot{q}(t)$, and acceleration $\ddot{q}(t)$:
$$q(t) = a_0 + a_1 t + a_2 t^2 + a_3 t^3 + a_4 t^4 + a_5 t^5$$
Boundary constraints:
$$q(0) = q_0, \quad \dot{q}(0) = v_0, \quad \ddot{q}(0) = a_0$$
$$q(T) = q_f, \quad \dot{q}(T) = v_f, \quad \ddot{q}(T) = a_f$$

---

## 4. Multi-Axis PID Control with Anti-Windup

Each independent actuator computes control torque $\tau(t)$:
$$\tau(t) = K_p e(t) + K_i \int_0^t e(\tau) d\tau + K_d \frac{d e_f(t)}{dt} + \tau_{\text{grav\_comp}}$$

- **Anti-Windup:** Integrator clamped to $[-\tau_{\text{clamp}}, \tau_{\text{clamp}}]$.
- **Derivative Filter:** First-order low-pass filter $\alpha$ eliminates quantization noise.
- **Feedforward Gravity Compensation:** $\tau_{\text{grav\_comp}} = \mathbf{g}(\mathbf{q})$ extracted from MuJoCo generalized forces (`qfrc_bias`).
