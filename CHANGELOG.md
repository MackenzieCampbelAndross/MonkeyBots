# Changelog

All notable changes to the MonkeyBots Robotics Simulation & Digital Twin platform.

## [v0.9.0-rc1] - 2026-11-25

### Added
- **Cartesian Impedance Controller:** Compliant 6-DOF spring-damper dynamics with null-space posture stabilization and passivity damping.
- **TOPP-RA Time-Optimal Path Parameterization:** Minimum-time trajectory time-scaling under joint velocity and acceleration bounds.
- **URDF & MuJoCo MJCF Exporters:** Automated export pipeline and API for Franka Panda, UR5e, UR10e, Delta, and custom arms.
- **3D SVD Manipulability Ellipsoid Visualizer:** Live Three.js rendering of velocity ellipsoid principal radii and volume at end-effector.
- **Interactive Trajectory Scrubber:** Play/pause/step timeline player with adjustable speed presets.
- **Actuator Torque Load Heatmap:** Live thermal & torque utilization monitor with nominal safety margins.
- **System Diagnostics API:** `/api/v1/diagnostics/system` health monitoring, hardware profiling, and engine benchmarks.
- **Kinematic Solver Micro-Benchmark:** Microsecond-resolution latency profiling comparing DLS, Transpose, and Analytical IK.
- **Command-Line Exporters:** `monkeybots export <robot> --format <urdf|mjcf>` CLI tool.

## [v0.8.0] - 2026-11-24
- 5-Day engineering sprint completed with 122 production commits across robot libraries, redundant IK, sampling motion planners (RRT/PRM), and Three.js digital twin viewport tooling.
