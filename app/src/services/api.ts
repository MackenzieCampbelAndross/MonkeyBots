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
  ProjectIntegrityReport,
  CreateProjectPayload,
  BackupItem,
  AnalyticsRunResponse,
  MultiRunComparisonReportData,
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

// Stage 11: Local Project Management APIs
export async function createProject(payload: CreateProjectPayload): Promise<ProjectManifest> {
  const res = await fetch(`${BASE_URL}/projects/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Project creation failed" }));
    throw new Error(err.detail || `Failed to create project: ${res.status}`);
  }
  return res.json();
}

export async function saveProject(projectId: string, manifest: ProjectManifest): Promise<ProjectManifest> {
  const res = await fetch(`${BASE_URL}/projects/${projectId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(manifest),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Save failed" }));
    throw new Error(err.detail || `Failed to save project: ${res.status}`);
  }
  return res.json();
}

export async function saveProjectAs(projectId: string, newName: string, newId?: string): Promise<ProjectManifest> {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/save-as`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ new_name: newName, new_id: newId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Save-as failed" }));
    throw new Error(err.detail || `Save As failed: ${res.status}`);
  }
  return res.json();
}

export async function duplicateProject(projectId: string, newName?: string): Promise<ProjectManifest> {
  const url = newName
    ? `${BASE_URL}/projects/${projectId}/duplicate?new_name=${encodeURIComponent(newName)}`
    : `${BASE_URL}/projects/${projectId}/duplicate`;
  const res = await fetch(url, { method: "POST" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Duplicate failed" }));
    throw new Error(err.detail || `Duplicate failed: ${res.status}`);
  }
  return res.json();
}

export async function renameProject(projectId: string, newName: string): Promise<ProjectManifest> {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/rename`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ new_name: newName }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Rename failed" }));
    throw new Error(err.detail || `Rename failed: ${res.status}`);
  }
  return res.json();
}

export async function deleteProject(projectId: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/projects/${projectId}?confirm=true`, { method: "DELETE" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Delete failed" }));
    throw new Error(err.detail || `Failed to delete project: ${res.status}`);
  }
}

export async function validateProject(projectId: string): Promise<ProjectIntegrityReport> {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/validate`, { method: "GET" });
  if (!res.ok) {
    throw new Error(`Failed to validate project: ${res.status}`);
  }
  return res.json();
}

export async function createProjectBackup(projectId: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/backup`, { method: "POST" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Backup failed" }));
    throw new Error(err.detail || `Backup failed: ${res.status}`);
  }
  return res.json();
}

export async function fetchProjectBackups(projectId?: string): Promise<{ backups: BackupItem[] }> {
  const url = projectId
    ? `${BASE_URL}/projects/backups?project_id=${encodeURIComponent(projectId)}`
    : `${BASE_URL}/projects/backups`;
  const res = await fetch(url, { method: "GET" });
  if (!res.ok) throw new Error("Failed to fetch backups");
  return res.json();
}

export async function restoreProjectBackup(backupFile: string, newProjectId?: string): Promise<ProjectManifest> {
  const res = await fetch(`${BASE_URL}/projects/restore-backup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ backup_file: backupFile, new_project_id: newProjectId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Restore failed" }));
    throw new Error(err.detail || `Restore failed: ${res.status}`);
  }
  return res.json();
}

export async function importProjectModel(
  projectId: string,
  sourceModelPath: string,
  destinationFilename?: string
): Promise<ProjectManifest> {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/import-model`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source_model_path: sourceModelPath, destination_filename: destinationFilename }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Import model failed" }));
    throw new Error(err.detail || `Import failed: ${res.status}`);
  }
  return res.json();
}

export async function exportProjectModel(
  projectId: string,
  exportDir: string,
  formatType: string = "bundle"
): Promise<any> {
  const res = await fetch(`${BASE_URL}/projects/${projectId}/export-model`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ export_dir: exportDir, format_type: formatType }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Export model failed" }));
    throw new Error(err.detail || `Export failed: ${res.status}`);
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

// Stage 12: Analytics, Visualization & Engineering Reporting APIs
export async function recordSimulationRun(config: {
  project_id?: string;
  duration?: number;
  timestep?: number;
  interpolation?: string;
  kp_gains?: number[];
  kd_gains?: number[];
  ki_gains?: number[];
  waypoints?: number[][];
  v_max?: number;
  a_max?: number;
}): Promise<AnalyticsRunResponse> {
  const res = await fetch(`${BASE_URL}/analytics/record`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Run failed" }));
    throw new Error(err.detail || `Failed to record simulation run: ${res.status}`);
  }
  return res.json();
}

export async function fetchLatestAnalytics(): Promise<AnalyticsRunResponse> {
  const res = await fetch(`${BASE_URL}/analytics/latest`, { method: "GET" });
  if (!res.ok) throw new Error(`Failed to fetch latest analytics: ${res.status}`);
  return res.json();
}

export async function compareAnalyticsRuns(experimentIds: string[]): Promise<MultiRunComparisonReportData> {
  const res = await fetch(`${BASE_URL}/analytics/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ experiment_ids: experimentIds }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Comparison failed" }));
    throw new Error(err.detail || `Failed to compare runs: ${res.status}`);
  }
  return res.json();
}

export async function fetchAnalyticsCSV(): Promise<string> {
  const res = await fetch(`${BASE_URL}/analytics/export/csv`, { method: "GET" });
  if (!res.ok) throw new Error(`CSV export failed: ${res.status}`);
  return res.text();
}

export async function fetchAnalyticsJSON(): Promise<any> {
  const res = await fetch(`${BASE_URL}/analytics/export/json`, { method: "GET" });
  if (!res.ok) throw new Error(`JSON export failed: ${res.status}`);
  return res.json();
}

export async function fetchAnalyticsMarkdown(): Promise<string> {
  const res = await fetch(`${BASE_URL}/analytics/export/markdown`, { method: "GET" });
  if (!res.ok) throw new Error(`Markdown export failed: ${res.status}`);
  return res.text();
}

export async function fetchAnalyticsHTML(): Promise<string> {
  const res = await fetch(`${BASE_URL}/analytics/export/html`, { method: "GET" });
  if (!res.ok) throw new Error(`HTML report export failed: ${res.status}`);
  return res.text();
}
