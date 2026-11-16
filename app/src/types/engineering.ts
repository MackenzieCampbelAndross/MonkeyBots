/**
 * MonkeyBots Engineering Workstation Types
 * Defines data structures for CAD tools, kinematics, designer, and validation lab.
 */

export type WorkspaceId =
  | "home"
  | "projects"
  | "designer"
  | "simulation"
  | "motion"
  | "validation"
  | "reports"
  | "settings";

export type ShadingMode = "solid" | "wireframe" | "collision";
export type CameraPreset = "iso" | "top" | "front" | "side";

export interface ViewportSettings {
  showGrid: boolean;
  showAxes: boolean;
  showShadows: boolean;
  shadingMode: ShadingMode;
  cameraPreset: CameraPreset;
  orthographic: boolean;
}

export interface DHParameter {
  jointIndex: number;
  name: string;
  theta: number; // Joint angle (rad)
  d: number;     // Link offset (m)
  a: number;     // Link length (m)
  alpha: number; // Link twist (rad)
}

export interface RobotLink {
  id: string;
  name: string;
  parent: string | null;
  jointType: "revolute" | "prismatic" | "fixed";
  massKg: number;
  com: [number, number, number]; // Center of mass
  inertia: [number, number, number, number, number, number]; // Ixx, Iyy, Izz, Ixy, Ixz, Iyz
  limits: { min: number; max: number }; // rad or m
  maxTorqueNm: number;
}

export interface CartesianPose {
  x: number;
  y: number;
  z: number;
  roll: number;
  pitch: number;
  yaw: number;
}

export interface ValidationTest {
  id: string;
  name: string;
  category: "KINEMATICS" | "DYNAMICS" | "CONTROL" | "SAFETY";
  status: "IDLE" | "RUNNING" | "PASSED" | "FAILED";
  metricName: string;
  metricValue: string;
  tolerance: string;
  description: string;
}

export interface ToastMessage {
  id: string;
  type: "info" | "success" | "warning" | "error";
  title: string;
  message: string;
  timestamp: string;
}
