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
