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
  status: "STOPPED" | "RUNNING" | "PAUSED" | "DIVERGED";
  model_name?: string;
  timestep: number;
  sim_time: number;
  step_count: number;
  real_time_factor?: number;
  dof?: number;
  energy?: {
    kinetic_joules: number;
    potential_joules: number;
    total_joules: number;
  };
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


export interface KinematicChainJoint {
  name: string;
  type: string;
  parent_link: string;
  child_link: string;
  lower_limit_rad: number;
  upper_limit_rad: number;
  lower_limit_deg: number;
  upper_limit_deg: number;
  axis: [number, number, number];
  origin_xyz: [number, number, number];
}

export interface KinematicChainInfo {
  robot_id: string;
  base_link: string;
  end_effector_link: string;
  dof: number;
  joints: KinematicChainJoint[];
  links: string[];
}

export interface JacobianAnalysisData {
  jacobian: number[][];
  singular_values: number[];
  manipulability: number;
  condition_number: number;
  is_singular: boolean;
  sigma_min: number;
  sigma_max: number;
}

export interface FKResultData {
  position: [number, number, number];
  quaternion: [number, number, number, number];
  rpy_rad: [number, number, number];
  rpy_deg: [number, number, number];
  transform_matrix: number[][];
  link_transforms: Record<string, number[][]>;
  jacobian_analysis?: JacobianAnalysisData;
  warnings?: string[];
  dof?: number;
}

export interface IKResultData {
  converged: boolean;
  status: string;
  joint_positions_rad: number[];
  joint_positions_deg: number[];
  position_error_mm: number;
  position_error_m: number;
  orientation_error_deg: number;
  orientation_error_rad: number;
  iterations: number;
  manipulability: number;
  is_singular: boolean;
  warnings: string[];
  achieved_pose?: FKResultData;
}

export interface PosePreset {
  name: string;
  description: string;
  joints_rad: number[];
  target_pos: [number, number, number];
}

export interface TrajectorySamplePoint {
  time: number;
  positions: number[];
  velocities: number[];
  accelerations: number[];
  cartesian_pos?: [number, number, number];
  cartesian_quat?: [number, number, number, number];
}

export interface PlanTrajectoryResponse {
  total_duration: number;
  num_segments: number;
  num_samples: number;
  interpolation: string;
  samples: TrajectorySamplePoint[];
}

export interface ExecuteTrajectoryResponse {
  duration: number;
  step_count: number;
  overall_position_rmse_rad: number;
  max_tracking_error_rad: number;
  joint_rmse_rad: number[];
  joint_max_error_rad: number[];
  timestamps: number[];
  target_positions: number[][];
  actual_positions: number[][];
  tracking_errors: number[][];
  applied_torques: number[][];
}

export interface StepResponseData {
  joint_index: number;
  initial_position_rad: number;
  target_position_rad: number;
  steady_state_error_rad: number;
  overshoot_percent: number;
  rise_time_seconds: number;
  settling_time_seconds: number;
  stability: string;
  is_stable: boolean;
  timestamps: number[];
  positions: number[];
  velocities: number[];
  torques: number[];
}

export interface TrajectoryPreset {
  name: string;
  description: string;
  waypoints: number[][];
}
