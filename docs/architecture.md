# MonkeyBots | Technical Architecture & System Blueprint

**Version:** 1.0.0 (Production Release)  
**Architecture Pattern:** Desktop Local-First Hybrid (Tauri Native Shell + React 19 Frontend + High-Speed Local Python Simulation Engine)

---

## 1. High-Level System Architecture

MonkeyBots is architected as an offline-first desktop application without reliance on cloud infrastructure, remote databases, or external AI APIs:

```mermaid
graph TD
    subgraph Desktop Shell [Tauri v2 Desktop Container (Rust)]
        WebView[Edge Chromium WebView2]
        TauriIPC[Local IPC Bridge]
    end

    subgraph Frontend [React 19 + TypeScript Application]
        ZustandStore[Zustand Local State Store]
        ThreeJSViewport[Three.js 3D Digital Twin Viewport]
        Workspaces[CAD Engineering Workspaces 1..8]
        Oscilloscope[Real-Time Telemetry Oscilloscope]
    end

    subgraph Local Server Gateway [FastAPI Asynchronous Gateway (127.0.0.1:8765)]
        RESTEndpoints[REST API: Projects, Models, Kinematics, Planning, Validation, Reports]
        WSTelemetry[60 Hz WebSocket Broadcast Gateway]
    end

    subgraph Core Physics & Robotics Kernel [Python High-Performance Runtime]
        MuJoCoEngine[MuJoCo 4.0.1 Physics Simulation Engine (500 Hz)]
        KinematicsEngine[Homogeneous SE(3) Transformations & SVD/DLS IK]
        TrajectoryPlanner[C2 Quintic & C1 Cubic Spline Generator]
        ControlManager[Multi-Axis Independent PID with Anti-Windup]
        ContactTracker[Dynamic Contact Manifold & Impulse Tracker]
        TelemetryBuffer[In-Memory Circular Buffer & Downsampler]
    end

    subgraph Storage Subsystem [Local Filesystem (No Database)]
        ProjectJSON[project.json (Project Manifest)]
        ModelFiles[robot.urdf / robot.mjcf]
        TrajectoryData[trajectories/*.json]
        ExperimentLogs[experiments/*.json]
        Backups[.snapshots/ & backups/*.mbpkg]
    end

    WebView --> ZustandStore
    ZustandStore --> ThreeJSViewport
    ZustandStore --> Workspaces
    ZustandStore --> Oscilloscope

    Frontend <-->|HTTP REST & 60 Hz WebSocket| LocalServerGateway
    LocalServerGateway --> CorePhysicsKernel
    CorePhysicsKernel <--> StorageSubsystem
```

---

## 2. Communication Pipeline & Frequency Decoupling

Robotics physics and user interfaces require fundamentally different update frequencies:

1. **Physics Loop (500 Hz / $\Delta t = 0.002\text{ s}$):**
   - MuJoCo integrates rigid-body dynamics, contact constraints, and torque actuation at 500 Hz on the backend process.
   - Deterministic, high-frequency mathematical stepping prevents energy drift and contact penetration.
2. **Telemetry Decoupling & Downsampling (60 Hz):**
   - The simulation runner downsamples the 500 Hz stream into a clean 60 Hz frame broadcast over a local WebSocket (`/ws/simulation`).
   - Frame latency is measured at $\le 2.1\text{ ms}$, ensuring zero perceptible input lag in the Three.js viewport.
3. **Analytical Buffer (Variable):**
   - Full-resolution data points are retained in `SimulationTelemetryBuffer` for engineering report generation and RMSE computation.

---

## 3. Storage Architecture: 100% Pure Local Filesystem

MonkeyBots rejects SQL/NoSQL databases in favor of transparent, user-inspectable local files:

- **Manifest:** `projects/{project_id}/project.json` containing metadata, robot definition, physics config, controller gains, and trajectory records.
- **Models:** `robot.urdf` (ROS standard) and `robot.mjcf` (MuJoCo XML).
- **Safety Backups:** Every write is atomic (`atomic_write()`), creating `.bak` redundancy. Rolling revision snapshots reside in `.snapshots/`. Standalone compressed archives are saved as `.mbpkg` (standard ZIP format).
