# MonkeyBots Communication Protocol Specification
**Protocol Version:** 1.0.0  
**Transport:** WebSocket (Binary/JSON) & HTTP REST (JSON)

---

## 1. Transport Architecture

MonkeyBots decouples the user interface from the physics and kinematics engine using two communication channels:

1. **High-Frequency WebSocket Channel (`/ws/simulation`):**
   - Streams live physics state updates from MuJoCo to the frontend at 60 Hz.
   - Accepts high-frequency real-time jog inputs and trajectory target streams from the frontend.
2. **REST API Channel (`/api/v1`):**
   - Synchronous lifecycle commands: project loading, saving, resetting, static kinematic evaluations, and report generation.

---

## 2. WebSocket Protocol (`/ws/simulation`)

### 2.1 Server-to-Client Messages

#### A. Telemetry Frame (`telemetry`)
Emitted by the physics engine at a downsampled rate (typically 60 Hz or 120 Hz) from the internal 500 Hz integration loop:

```json
{
  "type": "telemetry",
  "sim_time": 1.482000,
  "real_time_factor": 1.001,
  "step_count": 741,
  "joint_names": [
    "joint_1",
    "joint_2",
    "joint_3",
    "joint_4",
    "joint_5",
    "joint_6"
  ],
  "qpos": [0.0, -0.785398, 1.570796, 0.0, 0.785398, 0.0],
  "qvel": [0.0, 0.002, -0.001, 0.0, 0.0, 0.0],
  "qtorque": [0.0, -38.4, 18.2, 0.0, 0.9, 0.0],
  "end_effector": {
    "name": "tool0",
    "position": [0.485, 0.0, 0.521],
    "quaternion": [1.0, 0.0, 0.0, 0.0]
  },
  "contacts": [
    {
      "geom1": "gripper_left_pad",
      "geom2": "target_cube",
      "distance": 0.0,
      "force": 12.8,
      "position": [0.485, 0.015, 0.521]
    }
  ],
  "status": "RUNNING"
}
```

#### B. Error / Warning Frame (`error`)
Emitted when numerical divergence, singularity, or constraint violations occur:

```json
{
  "type": "error",
  "code": "KINEMATIC_SINGULARITY_APPROACH",
  "message": "Manipulability index fell below threshold (0.015). Damped least-squares fallback active.",
  "severity": "WARNING",
  "timestamp": 1731769800.123
}
```

---

### 2.2 Client-to-Server Messages

#### A. Direct Joint Position Command (`joint_position`)
Used when user drags joint angle sliders:

```json
{
  "type": "command",
  "mode": "joint_position",
  "targets": [0.1, -0.5, 1.2, 0.0, 0.5, 0.0],
  "gripper": 0.035
}
```

#### B. Cartesian Pose Target Command (`cartesian_target`)
Used when user drags the 3D transform gizmo in the Three.js viewport:

```json
{
  "type": "command",
  "mode": "cartesian_target",
  "target_pose": {
    "position": [0.45, 0.1, 0.6],
    "quaternion": [0.7071, 0.0, 0.7071, 0.0]
  },
  "ik_tolerance": 0.001
}
```

#### C. Simulation State Control (`sim_control`)
```json
{
  "type": "control",
  "action": "PAUSE"
}
```
*Valid actions:* `START`, `PAUSE`, `STEP`, `RESET`.

---

## 3. REST API Endpoints (`/api/v1`)

| Endpoint | Method | Description |
|---|---|---|
| `/health` | `GET` | Verifies engine status, active physics backend, and version. |
| `/projects` | `GET` | Returns list of local project directories found in the workspace. |
| `/projects/load` | `POST` | Loads a specified `project.json` into the active simulation memory. |
| `/kinematics/fk` | `POST` | Computes Forward Kinematics for arbitrary 6-DOF joint angles. |
| `/kinematics/ik` | `POST` | Solves Inverse Kinematics for a 6D target pose. |
| `/trajectory/plan`| `POST` | Computes a smooth trajectory (quintic / trapezoidal) between waypoints. |
| `/reports/export` | `POST` | Exports validation laboratory test benchmarks to Markdown/CSV. |
