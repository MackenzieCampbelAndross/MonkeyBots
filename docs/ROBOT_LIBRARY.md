# MonkeyBots Robot Model Library & Specifications

This document catalogs the verified robotic models included with the MonkeyBots simulation platform.

## 1. Supported Manipulators & Platforms

| Model Name | Registry ID | Type | DOF | Payload | Reach | Status |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| **Sample 6-DOF Arm** | `default_6dof_arm` | Serial Articulated | 6 | 5.0 kg | 0.85 m | Verified |
| **Franka Emika Panda** | `franka_panda` | Redundant Serial | 7 | 3.0 kg | 0.855 m | Verified |
| **Universal Robots UR5e** | `ur5e` | Collaborative Serial | 6 | 5.0 kg | 0.85 m | Verified |
| **Universal Robots UR10e** | `ur10e` | Heavy Collaborative | 6 | 12.5 kg | 1.30 m | Verified |
| **Parallel Delta Robot** | `delta_robot` | Parallel Linkage | 3 | 1.5 kg | 0.40 m | Verified |
| **Differential Mobile Base**| `mobile_base` | Wheeled Mobile | 2 | 20.0 kg | N/A | Verified |
| **Robotiq 2F-85** | `robotiq_2f85` | Parallel Gripper | 1 (actuated) | 5.0 kg | 85 mm stroke | Verified |

---

## 2. Model Integrity Guarantee

All models undergo rigorous structural checks via `ModelValidator`:
- Orthonormal inertial frames with positive-definite tensors.
- Continuous and revolute joint limits matching OEM hardware specifications.
- Validated collision hulls preventing initial self-intersections.
