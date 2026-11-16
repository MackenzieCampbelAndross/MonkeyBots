# MonkeyBots Local Project Format Specification
**Format Version:** 1.0.0  
**Storage Paradigm:** Pure Local Filesystem (No Database)

---

## 1. Directory Structure

A MonkeyBots project is a standard folder on the local file system. It can be initialized, edited with any text editor, and version-controlled using Git:

```
<ProjectDirectoryName>/
├── project.json              # Primary project manifest & configuration
├── robot.mjcf                # Native MuJoCo XML model description
├── robot.urdf                # Standard URDF description (interchange)
├── assets/                   # 3D meshes (STL, OBJ) and textures
│   ├── base.stl
│   ├── shoulder.stl
│   ├── upperarm.stl
│   ├── forearm.stl
│   ├── wrist1.stl
│   ├── wrist2.stl
│   └── wrist3.stl
├── trajectories/             # User-defined trajectories and waypoints
│   ├── default_home.json
│   └── pick_and_place.json
└── runs/                     # Experiment recordings, telemetry logs & reports
    └── run_sample/
        ├── run_meta.json
        ├── telemetry.csv
        └── report.md
```

---

## 2. Project Manifest Specification (`project.json`)

The manifest contains metadata, model entry references, physics solver parameters, and joint control gains:

```json
{
  "$schema": "https://raw.githubusercontent.com/MackenzieCampbelAndross/MonkeyBots/main/schemas/project.schema.json",
  "version": "1.0.0",
  "metadata": {
    "name": "Industrial 6-DOF Robotic Arm",
    "description": "Standard 6-axis industrial manipulator with parallel-jaw gripper",
    "created_at": "2026-11-16T20:20:00Z",
    "updated_at": "2026-11-16T20:25:00Z",
    "author": "MonkeyBots Robotics Lab"
  },
  "robot": {
    "model_file": "robot.mjcf",
    "urdf_file": "robot.urdf",
    "dof": 6,
    "end_effector_site": "flange_site",
    "default_qpos": [0.0, -0.785398, 1.570796, 0.0, 0.785398, 0.0]
  },
  "physics": {
    "timestep": 0.002,
    "integrator": "RK4",
    "gravity": [0.0, 0.0, -9.81],
    "collision_tolerance": 0.001
  },
  "controllers": {
    "default_mode": "position",
    "gains": [
      { "joint": "joint_1", "kp": 350.0, "ki": 0.5, "kd": 25.0, "max_torque": 150.0 },
      { "joint": "joint_2", "kp": 450.0, "ki": 1.0, "kd": 40.0, "max_torque": 150.0 },
      { "joint": "joint_3", "kp": 300.0, "ki": 0.5, "kd": 20.0, "max_torque": 150.0 },
      { "joint": "joint_4", "kp": 150.0, "ki": 0.1, "kd": 10.0, "max_torque": 28.0 },
      { "joint": "joint_5", "kp": 150.0, "ki": 0.1, "kd": 10.0, "max_torque": 28.0 },
      { "joint": "joint_6", "kp": 80.0,  "ki": 0.05, "kd": 5.0,  "max_torque": 28.0 }
    ]
  }
}
```

---

## 3. Zero-Database Guarantee
- MonkeyBots never instantiates SQLite, LevelDB, or any background database daemon.
- Scanning for projects is performed via fast local filesystem discovery of folders containing a valid `project.json`.
- All telemetry logs are written as append-only CSV or JSON Lines (`.jsonl`) files directly into the project's `runs/` subfolder.
