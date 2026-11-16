# MonkeyBots | Comprehensive Engineering User Manual

**Product:** MonkeyBots Robotics Engineering Workstation  
**Version:** 1.0.0  
**Interface Style:** Precision Engineering Desktop (inspired by ANSYS, SolidWorks, and Siemens NX)

---

## 1. Overview of the Workstation Interface

The MonkeyBots desktop environment is designed for maximum clarity, spatial awareness, and analytical depth.

```
+---------------------------------------------------------------------------------------------------------+
| [MonkeyBots]  File  Edit  View  Simulation  Kinematics  Tools  Help           ● ONLINE | 500 Hz | 1.0x RTF |
+----+-----------------------------------------+-----------------------------------+----------------------+
|    |                                         |                                   |                      |
| N  |                                         |                                   | CONTEXTUAL           |
| A  |        CENTRAL 3D VIEWPORT              |     ENGINEERING INSPECTOR         | PROPERTIES           |
| V  |                                         |                                   | INSPECTOR            |
| I  |        (Three.js Digital Twin)          |   - Physical Link Parameters      |                      |
| G  |   - Multi-body robot hierarchy          |   - Inertia Tensors (Ixx..Izz)    |   - Joint Angles     |
| A  |   - Dynamic collision hulls             |   - Coulomb Friction & Restitution|   - Actuator Torques |
| T  |   - World & joint coordinate triads     |   - Joint Velocity/Effort Limits  |   - Contact Points   |
| I  |   - Interactive camera orbit/pan/zoom   |                                   |   - RTF / Step Time  |
| O  |                                         |                                   |                      |
| N  +-----------------------------------------+-----------------------------------+----------------------+
|    |                      SIMULATION TIMELINE & TELEMETRY OSCILLOSCOPE                                  |
|    |   [► Start] [❚❚ Pause] [■ Reset] [►| Step]  Time: 2.450s | Steps: 1225 | Contacts: 2              |
+----+----------------------------------------------------------------------------------------------------+
```

---

## 2. Main Navigation Workspaces

The left navigation sidebar enables instantaneous switching between specialized engineering workstations:

### 1. Home (`Alt+1`)
- **System Dashboard:** Live telemetry summary, engine status indicators, and quick-start actions.
- **Recent Projects:** Instant access to recently edited robotics project folders.
- **Hardware Telemetry:** Real-time CPU, RAM, and simulation loop frequency metrics.

### 2. Projects (`Alt+2`)
- **Filesystem Project Explorer:** Create, open, rename, duplicate, and delete local robotics projects.
- **Integrity Auditor:** Real-time health status of project manifests (`project.json`), URDF, MJCF, and CAD assets.
- **Backup & Restore (.mbpkg):** Standalone zero-database compressed archive creation and one-click restoration.

### 3. Robot Designer (`Alt+3`)
- **Hierarchical Robot Tree:** Inspect kinematic chain from `base_link` down to the end-effector.
- **Link & Joint Editor:** Configure link masses, centers of mass ($[x, y, z]$), and $3 \times 3$ positive-definite inertia tensors.
- **URDF / MJCF Exporter:** Live bi-directional translation between ROS URDF XML and native MuJoCo MJCF.
- **Analytical Validator:** Real-time checking of triangular inequalities ($I_{xx} + I_{yy} \ge I_{zz}$), cycle detection, and joint limit consistency.

### 4. Simulation (`Alt+4`)
- **MuJoCo Dynamics Control:** Start, pause, resume, step forward, and reset the 500 Hz physics loop.
- **Environment Configuration:** Adjust numerical integration timesteps ($\Delta t = 0.001\text{ s} - 0.005\text{ s}$), gravity vector $\mathbf{g}$, and solver algorithms (Newton, CG, PGS).
- **Physical Verification Benchmarks:** Run 5 verified physics benchmarks (Free Fall, Pendulum Energy Conservation, Static Equilibrium, Elastic Impulse, Sliding Friction).

### 5. Motion and Control (`Alt+5`)
- **Forward Kinematics (FK):** Real-time joint sliders with sub-millimeter flange pose display $[x, y, z]$ and unit quaternions $[w, x, y, z]$.
- **Inverse Kinematics (IK):** Numerical target position and orientation solver utilizing Damped Least Squares (DLS) with singularity avoidance.
- **Trajectory Generator:** Generate smooth $C^2$ quintic polynomial or $C^1$ cubic spline trajectories under velocity ($v_{\max}$) and acceleration ($a_{\max}$) constraints.
- **Multi-Axis PID Tuning:** Configure independent axis gains ($K_p, K_i, K_d$) with anti-windup clamping and automated step-response analysis.

### 6. Validation Lab (`Alt+6`)
- **ISO 9283 Verification Laboratory:** Execute 10 rigorous engineering benchmark suites:
  1. Structural & mass integrity
  2. Joint limit enforcement
  3. Kinematic accuracy
  4. Dynamic physics conservation
  5. Trajectory path adherence
  6. Collision manifold dynamics
  7. Numerical stability
  8. Repeatability & determinism
  9. Controller transient response
  10. Numerical truncation analysis
- **Compliance Matrix:** Certified compliance percentage and explicit documentation of known physical limitations.

### 7. Reports & Analytics (`Alt+7`)
- **10 Ground-Truth Telemetry Streams:** Joint coordinates, velocities, accelerations, torques, spatial trajectories, tracking errors, orientation errors, step responses, contacts, and RTF.
- **Multi-Run Comparative Engine:** Overlay trajectories between multiple simulation experiments; evaluate $\Delta\text{RMSE}$ and torque expenditure trade-offs.
- **Publication-Grade Export:** Export raw CSV datasets, structured JSON, executive Markdown, and vector-sharp SVG HTML reports printable directly to PDF.

### 8. Settings (`Alt+8`)
- **Theme & Display:** Dark CAD / SolidWorks aesthetic with configurable viewport frame rate caps.
- **System Diagnostics:** Deep local environment audit (Python, MuJoCo, RAM, storage permissions).

---

## 3. Viewport 3D Interaction Guide

| Mouse / Keyboard Input | Action |
| :--- | :--- |
| **Left Click + Drag** | Orbit camera around center of interest |
| **Right Click + Drag** (or **Middle Drag**) | Pan camera along the viewport plane |
| **Scroll Wheel** | Continuous zoom in / zoom out |
| **Left Click (Object)** | Select robot link or environment object to inspect properties |
| **Key `G`** | Toggle CAD ground grid on/off |
| **Key `W`** | Cycle shading modes: Solid $\to$ Wireframe $\to$ Collision Hulls |
| **Spacebar** | Toggle simulation Start / Pause |
| **Key `R`** | Reset simulation to initial state ($t=0.0\text{ s}$) |
| **Keys `1` – `8`** | Instantly switch active engineering workspace |
