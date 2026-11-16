/**
 * MonkeyBots Global Application Store
 */

import { create } from "zustand";
import type {
  HealthResponse,
  ProjectSummary,
  ProjectManifest,
  TelemetryFrame,
  ConnectionStatus,
  LogEntry,
} from "../types/api";

interface AppState {
  // Connection & Health
  connectionStatus: ConnectionStatus;
  health: HealthResponse | null;
  latencyMs: number;
  lastError: string | null;

  // Projects
  projects: ProjectSummary[];
  activeProject: ProjectManifest | null;
  activeProjectId: string | null;

  // Telemetry
  telemetry: TelemetryFrame | null;
  selectedJointIndex: number;

  // UI state
  activeTab: "inspector" | "telemetry" | "logs";
  logs: LogEntry[];

  // Actions
  setConnectionStatus: (status: ConnectionStatus) => void;
  setHealth: (health: HealthResponse | null) => void;
  setLatencyMs: (ms: number) => void;
  setLastError: (err: string | null) => void;
  setProjects: (projects: ProjectSummary[]) => void;
  setActiveProject: (manifest: ProjectManifest, id: string) => void;
  setTelemetry: (frame: TelemetryFrame) => void;
  setSelectedJointIndex: (index: number) => void;
  setActiveTab: (tab: "inspector" | "telemetry" | "logs") => void;
  addLog: (level: LogEntry["level"], source: string, message: string) => void;
  clearLogs: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  connectionStatus: "CONNECTING",
  health: null,
  latencyMs: 0,
  lastError: null,

  projects: [],
  activeProject: null,
  activeProjectId: null,

  telemetry: null,
  selectedJointIndex: 0,

  activeTab: "inspector",
  logs: [],

  setConnectionStatus: (status) => set({ connectionStatus: status }),
  setHealth: (health) => set({ health }),
  setLatencyMs: (latencyMs) => set({ latencyMs }),
  setLastError: (lastError) => set({ lastError }),
  setProjects: (projects) => set({ projects }),
  setActiveProject: (manifest, id) => set({ activeProject: manifest, activeProjectId: id }),
  setTelemetry: (frame) => set({ telemetry: frame }),
  setSelectedJointIndex: (index) => set({ selectedJointIndex: index }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  addLog: (level, source, message) =>
    set((state) => ({
      logs: [
        {
          id: Math.random().toString(36).substring(7),
          timestamp: new Date().toLocaleTimeString(),
          level,
          source,
          message,
        },
        ...state.logs.slice(0, 99), // Keep latest 100 entries
      ],
    })),
  clearLogs: () => set({ logs: [] }),
}));
