/**
 * MonkeyBots REST API Client
 */

import type {
  HealthResponse,
  ProjectSummary,
  ProjectManifest,
  SimStatus,
  ValidationSuiteReportData,
  ValidationTestCaseData,
  ExperimentConfigData,
  ExperimentResultData,
  ExperimentSummaryItem,
  ExperimentComparisonData,
} from "../types/api";

const BASE_URL = "http://127.0.0.1:8765/api/v1";

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${BASE_URL}/system/health`, { method: "GET" });
  if (!res.ok) {
    throw new Error(`Health check failed with status: ${res.status}`);
  }
  return res.json();
}

export async function fetchProjects(): Promise<ProjectSummary[]> {
  const res = await fetch(`${BASE_URL}/projects`, { method: "GET" });
  if (!res.ok) {
    throw new Error(`Failed to fetch projects: ${res.status}`);
  }
  return res.json();
}

export async function fetchProjectDetails(projectId: string): Promise<ProjectManifest> {
  const res = await fetch(`${BASE_URL}/projects/${projectId}`, { method: "GET" });
  if (!res.ok) {
    throw new Error(`Failed to load project '${projectId}': ${res.status}`);
  }
  return res.json();
}

export async function fetchSimStatus(): Promise<SimStatus> {
  const res = await fetch(`${BASE_URL}/simulation/status`, { method: "GET" });
  if (!res.ok) {
    throw new Error(`Failed to fetch simulation status: ${res.status}`);
  }
  return res.json();
}

export async function sendSimControl(action: "START" | "PAUSE" | "STEP" | "RESET"): Promise<void> {
  const res = await fetch(`${BASE_URL}/simulation/control`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action }),
  });
  if (!res.ok) {
    throw new Error(`Simulation control '${action}' failed: ${res.status}`);
  }
}

export async function triggerShutdown(): Promise<void> {
  await fetch(`${BASE_URL}/system/shutdown`, { method: "POST" });
}

// Robot Modelling & Mechanical Configuration APIs
export async function fetchSample6DofModel(): Promise<any> {
  const res = await fetch(`${BASE_URL}/models/sample-6dof`, { method: "GET" });
  if (!res.ok) throw new Error("Failed to load sample 6-DOF robot model");
  return res.json();
}

export async function validateRobotModel(model: any): Promise<{
  is_valid: boolean;
  errors: Array<{ code: string; message: string; element_id?: string; severity: string }>;
  warnings: Array<{ code: string; message: string; element_id?: string; severity: string }>;
  dof: number;
  link_count: number;
  joint_count: number;
}> {
  const res = await fetch(`${BASE_URL}/models/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(model),
  });
  if (!res.ok) throw new Error("Model validation request failed");
  return res.json();
}

export async function exportRobotURDF(model: any): Promise<{ format: string; content: string }> {
  const res = await fetch(`${BASE_URL}/models/export/urdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(model),
  });
  if (!res.ok) throw new Error("URDF export failed");
  return res.json();
}

export async function exportRobotMJCF(model: any): Promise<{
  format: string;
  content: string;
  mujoco_verified: boolean;
  verification_message: string;
}> {
  const res = await fetch(`${BASE_URL}/models/export/mjcf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(model),
  });
  if (!res.ok) throw new Error("MJCF export failed");
  return res.json();
}

// Kinematics APIs
export async function fetchKinematicChain(robotId: string = "default_6dof_arm"): Promise<any> {
  const res = await fetch(`${BASE_URL}/kinematics/chain?robot_id=${encodeURIComponent(robotId)}`, {
    method: "GET",
  });
  if (!res.ok) throw new Error("Failed to load kinematic chain");
  return res.json();
}

export async function calculateFK(
  jointPositions: number[],
  robotId: string = "default_6dof_arm"
): Promise<any> {
  const res = await fetch(`${BASE_URL}/kinematics/fk`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      robot_id: robotId,
      joint_positions: jointPositions,
    }),
  });
  if (!res.ok) throw new Error("Forward kinematics calculation failed");
  return res.json();
}

export async function calculateIK(params: {
  robotId?: string;
  targetPosition: [number, number, number];
  targetRpyDeg?: [number, number, number];
  targetRpyRad?: [number, number, number];
  targetQuaternion?: [number, number, number, number];
  initialSeed?: number[];
  method?: string;
  posToleranceM?: number;
  rotToleranceRad?: number;
  maxIterations?: number;
}): Promise<any> {
  const res = await fetch(`${BASE_URL}/kinematics/ik`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      robot_id: params.robotId || "default_6dof_arm",
      target_position: params.targetPosition,
      target_rpy_deg: params.targetRpyDeg,
      target_rpy_rad: params.targetRpyRad,
      target_quaternion: params.targetQuaternion,
      initial_seed: params.initialSeed,
      method: params.method || "damped_least_squares",
      pos_tolerance_m: params.posToleranceM ?? 1e-4,
      rot_tolerance_rad: params.rotToleranceRad ?? 1e-3,
      max_iterations: params.maxIterations ?? 150,
    }),
  });
  if (!res.ok) throw new Error("Inverse kinematics calculation failed");
  return res.json();
}

export async function fetchPosePresets(robotId: string = "default_6dof_arm"): Promise<any> {
  const res = await fetch(`${BASE_URL}/kinematics/presets?robot_id=${encodeURIComponent(robotId)}`, {
    method: "GET",
  });
  if (!res.ok) throw new Error("Failed to load pose presets");
  return res.json();
}

// Motion Planning & Control APIs
export async function planTrajectory(params: {
  waypoints: number[][];
  interpolation?: string;
  vMax?: number;
  aMax?: number;
  sampleDt?: number;
}): Promise<any> {
  const res = await fetch(`${BASE_URL}/motion/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      waypoints: params.waypoints,
      interpolation: params.interpolation || "quintic",
      v_max: params.vMax ?? 2.5,
      a_max: params.aMax ?? 5.0,
      sample_dt: params.sampleDt ?? 0.02,
    }),
  });
  if (!res.ok) throw new Error("Trajectory planning failed");
  return res.json();
}

export async function executeTrajectory(params: {
  waypoints: number[][];
  interpolation?: string;
  vMax?: number;
  aMax?: number;
}): Promise<any> {
  const res = await fetch(`${BASE_URL}/motion/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      waypoints: params.waypoints,
      interpolation: params.interpolation || "quintic",
      v_max: params.vMax ?? 2.5,
      a_max: params.aMax ?? 5.0,
    }),
  });
  if (!res.ok) throw new Error("Trajectory execution failed");
  return res.json();
}

export async function runStepResponseTest(params: {
  jointIndex: number;
  stepAmplitudeRad?: number;
  testDuration?: number;
  kp?: number;
  ki?: number;
  kd?: number;
}): Promise<any> {
  const res = await fetch(`${BASE_URL}/motion/step_response`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      joint_index: params.jointIndex,
      step_amplitude_rad: params.stepAmplitudeRad ?? 0.35,
      test_duration: params.testDuration ?? 2.0,
      kp: params.kp ?? 280.0,
      ki: params.ki ?? 2.0,
      kd: params.kd ?? 50.0,
    }),
  });
  if (!res.ok) throw new Error("Step response evaluation failed");
  return res.json();
}

export async function fetchTrajectoryPresets(): Promise<any> {
  const res = await fetch(`${BASE_URL}/motion/presets`, { method: "GET" });
  if (!res.ok) throw new Error("Failed to load trajectory presets");
  return res.json();
}

// Stage 09: Collision Detection, Contact Physics & Object Manipulation APIs
export async function sendGripperCommand(action: "OPEN" | "CLOSE" | "SET_FORCE", forceN: number = 16.0): Promise<any> {
  const res = await fetch(`${BASE_URL}/simulation/gripper/command`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, force_n: forceN }),
  });
  if (!res.ok) throw new Error("Gripper command failed");
  return res.json();
}

export async function fetchGripperStatus(): Promise<{
  width: number;
  left_force: number;
  right_force: number;
  is_grasping: boolean;
}> {
  const res = await fetch(`${BASE_URL}/simulation/gripper/status`, { method: "GET" });
  if (!res.ok) throw new Error("Failed to load gripper status");
  return res.json();
}

export async function fetchActiveContacts(): Promise<{
  count: number;
  contacts: Array<{
    geom1: string;
    geom2: string;
    force: number;
    distance: number;
    position?: [number, number, number];
    normal?: [number, number, number];
    friction_force?: number;
    category?: string;
    slip_state?: string;
  }>;
}> {
  const res = await fetch(`${BASE_URL}/simulation/contacts`, { method: "GET" });
  if (!res.ok) throw new Error("Failed to fetch active contacts");
  return res.json();
}

export async function fetchCollisionEvents(limit: number = 50): Promise<{
  count: number;
  events: Array<{
    timestamp: number;
    event_type: string;
    geom1: string;
    geom2: string;
    body1: string;
    body2: string;
    category: string;
    normal_force: number;
    friction_force: number;
    impulse: number;
    position: [number, number, number];
    normal: [number, number, number];
  }>;
}> {
  const res = await fetch(`${BASE_URL}/simulation/collision_events?limit=${limit}`, { method: "GET" });
  if (!res.ok) throw new Error("Failed to fetch collision events");
  return res.json();
}

export async function executePickAndPlace(plan?: {
  pick_pos?: [number, number, number];
  place_pos?: [number, number, number];
  lift_height?: number;
  grip_force?: number;
}): Promise<any> {
  const res = await fetch(`${BASE_URL}/simulation/manipulation/pick_and_place`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(plan || {}),
  });
  if (!res.ok) throw new Error("Pick and place execution failed");
  return res.json();
}

export async function runManipulationBenchmarks(): Promise<any> {
  const res = await fetch(`${BASE_URL}/simulation/manipulation_benchmarks`, { method: "GET" });
  if (!res.ok) throw new Error("Failed to run manipulation benchmarks");
  return res.json();
}

// Stage 10: Validation Laboratory & Repeatable Experiments APIs
export async function fetchValidationSuite(): Promise<ValidationSuiteReportData> {
  const res = await fetch(`${BASE_URL}/validation/suite`, { method: "GET" });
  if (!res.ok) throw new Error(`Validation suite failed: ${res.status}`);
  return res.json();
}

export async function fetchValidationCapabilities(): Promise<{ capabilities: any[] }> {
  const res = await fetch(`${BASE_URL}/validation/capabilities`, { method: "GET" });
  if (!res.ok) throw new Error(`Failed to fetch capabilities: ${res.status}`);
  return res.json();
}

export async function fetchValidationCapability(capabilityId: string): Promise<ValidationTestCaseData> {
  const res = await fetch(`${BASE_URL}/validation/capability/${capabilityId}`, { method: "GET" });
  if (!res.ok) throw new Error(`Failed to run capability '${capabilityId}': ${res.status}`);
  return res.json();
}

export async function fetchValidationReportMarkdown(): Promise<string> {
  const res = await fetch(`${BASE_URL}/validation/report/markdown`, { method: "GET" });
  if (!res.ok) throw new Error(`Failed to fetch Markdown validation report: ${res.status}`);
  return res.text();
}

export async function fetchValidationExperiments(): Promise<{ experiments: ExperimentSummaryItem[] }> {
  const res = await fetch(`${BASE_URL}/validation/experiments`, { method: "GET" });
  if (!res.ok) throw new Error(`Failed to fetch experiments: ${res.status}`);
  return res.json();
}

export async function runValidationExperiment(config: ExperimentConfigData): Promise<ExperimentResultData> {
  const res = await fetch(`${BASE_URL}/validation/experiments/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Experiment execution failed" }));
    throw new Error(err.detail || `Experiment failed: ${res.status}`);
  }
  return res.json();
}

export async function fetchValidationExperimentDetails(experimentId: string): Promise<ExperimentResultData> {
  const res = await fetch(`${BASE_URL}/validation/experiments/${experimentId}`, { method: "GET" });
  if (!res.ok) throw new Error(`Failed to load experiment '${experimentId}': ${res.status}`);
  return res.json();
}

export async function compareValidationExperiments(experimentIds: string[]): Promise<ExperimentComparisonData> {
  const res = await fetch(`${BASE_URL}/validation/experiments/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ experiment_ids: experimentIds }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Comparison failed" }));
    throw new Error(err.detail || `Comparison failed: ${res.status}`);
  }
  return res.json();
}
