/**
 * MonkeyBots REST API Client
 */

import type { HealthResponse, ProjectSummary, ProjectManifest, SimStatus } from "../types/api";

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
