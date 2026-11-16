/**
 * MonkeyBots Type Definitions
 * Typed contracts matching the FastAPI backend and WebSocket schemas.
 */

export interface HealthResponse {
  status: "HEALTHY" | "UNHEALTHY" | "DEGRADED";
  app: string;
  version: string;
  uptime_seconds: number;
  python_version: string;
  os: string;
  cpu_percent: number;
  memory_percent: number;
  mujoco_available: boolean;
}

export interface ProjectSummary {
  id: string;
  name: string;
  description: string;
  path: string;
  dof: number;
  has_mjcf: boolean;
  has_urdf: boolean;
}

export interface JointGain {
  joint: string;
  kp: number;
  ki: number;
  kd: number;
  max_torque: number;
}

export interface ProjectManifest {
  version: string;
  metadata: {
    name: string;
    description: string;
    created_at: string;
    updated_at: string;
    author: string;
  };
  robot: {
    model_file: string;
    urdf_file?: string;
    dof: number;
    end_effector_site: string;
    default_qpos: number[];
  };
  physics: {
    timestep: number;
    integrator: string;
    gravity: [number, number, number];
    collision_tolerance: number;
  };
  controllers: {
    default_mode: string;
    gains: JointGain[];
  };
}

export interface SimStatus {
  is_active: boolean;
  status: "RUNNING" | "PAUSED" | "STOPPED";
  model_name: string;
  timestep: number;
  sim_time: number;
  step_count: number;
}

export interface Pose3D {
  position: [number, number, number];
  quaternion: [number, number, number, number];
}

export interface ContactInfo {
  geom1: string;
  geom2: string;
  force: number;
  distance: number;
  position?: [number, number, number];
}

export interface TelemetryFrame {
  type: "telemetry";
  sim_time: number;
  real_time_factor: number;
  step_count: number;
  joint_names: string[];
  qpos: number[];
  qvel: number[];
  qtorque: number[];
  end_effector?: Pose3D;
  contacts: ContactInfo[];
  status: "RUNNING" | "PAUSED" | "ERROR";
}

export type ConnectionStatus = "CONNECTED" | "CONNECTING" | "DISCONNECTED" | "ERROR";

export interface LogEntry {
  id: string;
  timestamp: string;
  level: "INFO" | "WARNING" | "ERROR" | "DEBUG";
  source: string;
  message: string;
}
