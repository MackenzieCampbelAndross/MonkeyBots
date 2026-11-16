# MonkeyBots 🐒🤖
> **Local-First Robotics Engineering & Simulation Platform**  
> *Build. Simulate. Perfect.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()
[![Simulation](https://img.shields.io/badge/Physics-MuJoCo-orange.svg)](https://mujoco.org/)

---

## 1. Product Overview

**MonkeyBots** is a local-first robotics engineering and simulation platform that enables engineers to design robots, simulate their physical behaviour, test their movements, and validate their performance in a realistic virtual environment before building them physically.

Think of MonkeyBots as a complete virtual robotics laboratory.

Our goal is to create a highly accurate, reliable, and realistic robotics engineering environment where physical correctness takes precedence over visual approximations.

---

## 2. Core Capabilities

* **01. Robot Design**
  * Create and configure robotic structures and kinematic chains.
  * Define mechanical components, dimensions, and visual/collision geometries.
  * Configure joints, degrees of freedom (DOF), and joint limits.
  * Define mass, density, inertia tensors, and material properties.
  * Import and export standard **URDF** and **MJCF** robot models.

* **02. Physics Simulation**
  * Realistic gravity, mass distribution, and inertia dynamics.
  * Precise collision detection and multi-body contact responses.
  * Friction models (dry friction, viscous damping, contact friction).
  * Actuator dynamics, joint torque calculations, and transmission ratios.
  * Stable, deterministic, and repeatable simulation behavior powered by **MuJoCo**.

* **03. Digital Twin**
  * Interactive 3D robot visualization powered by **Three.js**.
  * Accurate geometric representation and coordinate frame transformations.
  * Real-time 60 Hz+ simulation visualization and state synchronization.
  * Environment interactions, obstacles, and manipulable objects.
  * Robot state monitoring (joint positions, velocities, torques, temperatures).

* **04. Motion and Control**
  * Analytical and numerical Forward Kinematics (FK).
  * Robust Inverse Kinematics (IK) with joint limit avoidance and singularity dampening.
  * Joint-space and Cartesian trajectory planning (trapezoidal velocity, quintic polynomials, S-curve profiles).
  * Joint controllers: PID, computed torque control, gravity compensation.
  * Motion execution profiling and control analysis.

* **05. Validation Laboratory**
  * Rigorous simulation experiments and benchmark suites.
  * Trajectory tracking accuracy (RMS error, overshoot, settling time).
  * Stability analysis and payload limit testing.
  * Collision impulse and safety testing.
  * Exportable engineering reports and simulation telemetry logs.

---

## 3. Initial Development Target: 6-DOF Industrial Robotic Arm

Our first major milestone is a high-precision **six degree of freedom (6 DOF) industrial robotic arm** with an integrated parallel-jaw gripper.

Features:
1. **Mechanical configuration**: Articulated 6-axis arm with customizable link lengths and mass distributions.
2. **Kinematics**: Full analytical/numerical FK & IK solvers with interactive 3D end-effector gizmos.
3. **Physics**: Native MuJoCo simulation model with exact inertia matrices, motor limits, and joint friction.
4. **Motion Planning**: Trapezoidal and quintic trajectory generator with collision avoidance.
5. **Manipulation**: Object pick-and-place with contact force dynamics.
6. **Validation**: Automated benchmark suite with performance metrics and engineering report generation.

---

## 4. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Desktop Application** | **Tauri** (Rust) | Lightweight, native desktop shell with zero electron bloat |
| **Frontend** | **React** + **TypeScript** + **Tailwind CSS** | Clean, modular CAD-grade user interface |
| **3D Rendering** | **Three.js** | Interactive WebGL digital twin viewport |
| **Physics Kernel** | **MuJoCo** | High-fidelity multi-joint contact and rigid-body dynamics |
| **Backend & IPC** | **Python** + **FastAPI** + **WebSockets** | Real-time simulation daemon, kinematics solver, and telemetry gateway |
| **Control & Kinematics** | **Python** / **NumPy** / **SciPy** | Trajectory generators, PID loops, IK solvers |
| **Robot Description** | **URDF** & **MJCF** (XML) | Industry-standard interchange formats |

---

## 5. Architectural Constraints (Non-Negotiable)

- **No database required**: All project data is stored cleanly on the local filesystem.
- **No external AI API keys or paid APIs**: 100% self-sufficient engineering tool.
- **No mandatory cloud infrastructure or user accounts**: Privacy-first, offline-capable.
- **Local filesystem project storage**: Projects are simple directories with readable manifests and robot descriptions.
- **Local simulation execution**: Real-time physics runs completely on the user's hardware.
- **Open-source & permissively licensed**: Built on proven, peer-reviewed engineering foundations.

---

## 6. Engineering Philosophy

MonkeyBots prioritizes:
- **Physical accuracy over visual appearance**
- **Realistic simulation over exaggerated animations**
- **Reliable results over excessive features**
- **Measurable performance over subjective claims**
- **Engineering correctness over shortcuts**
- **Reproducibility over approximate results**

---

## 7. Project Structure

```
MonkeyBots/
├── core/                   # Python robotics & simulation kernel
│   ├── simulation/         # MuJoCo physics engine wrappers & steppers
│   ├── kinematics/         # FK, IK, Jacobian, and coordinate transformations
│   ├── planning/           # Trajectory generators (joint-space & Cartesian)
│   ├── control/            # PID, computed torque, and gravity compensation
│   └── models/             # Standard robot descriptions (URDF/MJCF models & meshes)
├── server/                 # FastAPI WebSocket & REST API service
├── app/                    # Tauri desktop shell & React frontend
│   ├── src/
│   │   ├── components/     # UI panels, tree view, inspector, telemetry
│   │   ├── viewport/       # Three.js 3D robotics scene & gizmos
│   │   └── hooks/          # Real-time WebSocket state synchronizer
│   └── src-tauri/          # Rust Tauri desktop application config
└── tests/                  # Validation laboratory test suites & benchmarks
```

---

## License

This project is licensed under the [MIT License](LICENSE).
