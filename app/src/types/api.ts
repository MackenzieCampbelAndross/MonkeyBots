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
  robot_type?: string;
  author?: string;
  created_at?: string;
  updated_at?: string;
  path: string;
  dof: number;
  has_mjcf: boolean;
  has_urdf: boolean;
  size_bytes?: number;
  integrity_status?: "HEALTHY" | "WARNING" | "ERROR";
  missing_assets_count?: number;
  experiments_count?: number;
  trajectories_count?: number;
  reports_count?: number;
  snapshots_count?: number;
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
    id?: string;
    name: string;
    description: string;
    created_at: string;
    updated_at: string;
    author: string;
    robot_type?: string;
    tags?: string[];
    version_tag?: string;
  };
  robot: {
    model_file: string;
    urdf_file?: string;
    dof: number;
    end_effector_site: string;
    default_qpos: number[];
    base_link?: string;
    flange_link?: string;
  };
  physics: {
    timestep: number;
    integrator: string;
    gravity: [number, number, number];
    collision_tolerance: number;
    solver?: string;
    iterations?: number;
  };
  controllers: {
    default_mode: string;
    gains: JointGain[];
  };
  materials?: Record<string, {
    name: string;
    rgba: number[];
    friction: number[];
    density: number;
    roughness: number;
  }>;
  assets?: Array<{
    name: string;
    relative_path: string;
    format: string;
    scale: number[];
  }>;
  trajectories?: Array<{
    id: string;
    name: string;
    relative_path: string;
    interpolation: string;
    waypoints_count: number;
    duration_s: number;
  }>;
  experiments?: string[];
  reports?: string[];
}

export interface AssetVerificationResult {
  name: string;
  relative_path: string;
  exists: boolean;
  size_bytes: number;
  format: string;
  status: "VALID" | "MISSING" | "CORRUPT" | "ABSOLUTE_PATH_FORBIDDEN";
}

export interface ProjectIntegrityReport {
  project_id: string;
  is_valid: boolean;
  status: "HEALTHY" | "WARNING" | "ERROR";
  manifest_valid: boolean;
  model_mjcf_valid: boolean;
  model_urdf_valid: boolean;
  total_assets: number;
  missing_assets_count: number;
  assets: AssetVerificationResult[];
  experiments_count: number;
  trajectories_count: number;
  reports_count: number;
  snapshots_count: number;
  warnings: string[];
  errors: string[];
  file_inventory: Record<string, number>;
}

export interface CreateProjectPayload {
  name: string;
  description?: string;
  robot_preset?: "6dof_industrial" | "workcell" | "blank";
  author?: string;
  robot_type?: string;
  tags?: string[];
}

export interface BackupItem {
  filename: string;
  path: string;
  size_bytes: number;
  created_at: string;
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
  normal?: [number, number, number];
  friction_force?: number;
  category?: string;
  slip_state?: string;
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

// Stage 10: Validation Laboratory & Repeatable Experiments Types
export type ValidationStatus = "VERIFIED" | "FAILED" | "NOT_IMPLEMENTED" | "KNOWN_LIMITATION";

export interface ValidationMetricData {
  name: string;
  expected_value: number;
  actual_value: number;
  difference: number;
  relative_error?: number;
  tolerance: number;
  unit: string;
  status: ValidationStatus;
  notes?: string;
}

export interface ValidationTestCaseData {
  id: string;
  category: string;
  name: string;
  description: string;
  standard_reference: string;
  status: ValidationStatus;
  metrics: ValidationMetricData[];
  execution_time_ms: number;
  failure_reason?: string;
}

export interface ValidationSuiteReportData {
  suite_name: string;
  version: string;
  timestamp: string;
  overall_status: ValidationStatus;
  total_tests: number;
  verified_count: number;
  failed_count: number;
  known_limitations_count: number;
  not_implemented_count: number;
  compliance_percentage: number;
  test_cases: ValidationTestCaseData[];
  system_info: Record<string, any>;
}

export interface ExperimentConfigData {
  id: string;
  name: string;
  description?: string;
  robot_id?: string;
  timestep: number;
  duration: number;
  controller_type?: string;
  kp: number[];
  ki: number[];
  kd: number[];
  trajectory_type: string;
  waypoints: number[][];
  v_max: number;
  a_max: number;
}

export interface ExperimentMetricsData {
  position_rmse_rad: number;
  max_position_error_rad: number;
  joint_rmse_rad: number[];
  max_velocity_rad_s: number;
  max_acceleration_rad_s2: number;
  max_applied_torque_nm: number;
  rms_torque_nm: number;
  energy_initial_j: number;
  energy_final_j: number;
  energy_drift_j: number;
  collision_events_count: number;
  simulation_execution_time_s: number;
  real_time_factor: number;
  solver_iterations_avg: number;
}

export interface ExperimentResultData {
  id: string;
  config: ExperimentConfigData;
  timestamp: string;
  metrics: ExperimentMetricsData;
  time_series: {
    timestamps: number[];
    q_actual: number[][];
    q_target: number[][];
    torques: number[][];
    position_errors: number[][];
    energies: number[];
  };
  summary: string;
}

export interface ExperimentSummaryItem {
  id: string;
  name: string;
  timestamp: string;
  duration: number;
  position_rmse_mrad: number;
  max_torque_nm: number;
  energy_drift_j: number;
}

export interface ExperimentComparisonData {
  experiment_ids: string[];
  experiments: Array<{
    id: string;
    name: string;
    timestamp: string;
    timestep: number;
    duration: number;
    position_rmse_mrad: number;
    max_position_error_mrad: number;
    max_torque_nm: number;
    rms_torque_nm: number;
    energy_drift_j: number;
    execution_time_s: number;
    real_time_factor: number;
  }>;
  comparative_analysis: Record<string, {
    delta_rmse_mrad: number;
    delta_max_torque_nm: number;
    delta_energy_drift_j: number;
    rmse_improvement_percent: number;
  }>;
}

// Stage 12: Analytics, Visualization & Engineering Reporting Types
export interface JointPerformanceMetricsData {
  joint_index: number;
  name: string;
  position_rmse_rad: number;
  max_position_error_rad: number;
  max_velocity_rad_s: number;
  max_acceleration_rad_s2: number;
  peak_torque_nm: number;
  rms_torque_nm: number;
}

export interface StepResponseMetricsData {
  rise_time_s: number;
  settling_time_s: number;
  overshoot_percent: number;
  steady_state_error_rad: number;
  is_stable: boolean;
}

export interface SimulationRunMetricsData {
  total_duration_s: number;
  total_steps: number;
  timestep_s: number;
  overall_position_rmse_m: number;
  max_cartesian_error_m: number;
  overall_joint_rmse_rad: number;
  max_orientation_error_rad: number;
  max_orientation_error_deg: number;
  joints: JointPerformanceMetricsData[];
  step_response: StepResponseMetricsData;
  peak_applied_torque_nm: number;
  total_energy_initial_j: number;
  total_energy_final_j: number;
  energy_drift_j: number;
  collision_events_count: number;
  peak_contact_force_n: number;
  real_time_factor: number;
  mean_step_latency_us: number;
  max_step_latency_us: number;
  avg_solver_iterations: number;
}

export interface TelemetryTimeSeriesData {
  timestamps: number[];
  q_actual: number[][];
  q_target: number[][];
  qvel_actual: number[][];
  qacc_actual: number[][];
  torques: number[][];
  ee_pos_actual: number[][];
  ee_pos_target: number[][];
  pos_error_norm: number[];
  rot_error_rad: number[];
  energy_total: number[];
  contacts_count: number[];
  max_normal_force: number[];
  solver_niter: number[];
}

export interface AnalyticsRunResponse {
  status: string;
  metrics: SimulationRunMetricsData;
  telemetry: TelemetryTimeSeriesData;
  total_points: number;
}

export interface RunComparisonItemData {
  run_id: string;
  run_name: string;
  timestep: number;
  duration: number;
  cartesian_rmse_mm: number;
  max_cartesian_error_mm: number;
  joint_rmse_mrad: number;
  peak_torque_nm: number;
  rms_torque_nm: number;
  settling_time_s: number;
  overshoot_percent: number;
  energy_drift_j: number;
  real_time_factor: number;
  mean_latency_us: number;
}

export interface CrossRunMetricDeltaData {
  target_id: string;
  baseline_id: string;
  delta_rmse_mm: number;
  rmse_improvement_pct: number;
  delta_peak_torque_nm: number;
  delta_settling_time_s: number;
  delta_energy_drift_j: number;
  rtf_ratio: number;
  trade_off_summary: string;
}

export interface MultiRunComparisonReportData {
  baseline_run_id: string;
  compared_runs: RunComparisonItemData[];
  deltas: Record<string, CrossRunMetricDeltaData>;
  key_findings: string[];
}
