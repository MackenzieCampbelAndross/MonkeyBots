import React, { useEffect } from "react";
import { SidebarRail } from "./components/navigation/SidebarRail";
import { TopToolbar } from "./components/toolbar/TopToolbar";
import { StatusBar } from "./components/statusbar/StatusBar";
import { ToastContainer } from "./components/common/ToastContainer";
import { ErrorBanner } from "./components/ErrorBanner";
import { HomeWorkspace } from "./components/workspaces/HomeWorkspace";
import { ProjectsWorkspace } from "./components/workspaces/ProjectsWorkspace";
import { RobotDesignerWorkspace } from "./components/workspaces/RobotDesignerWorkspace";
import { SimulationWorkspace } from "./components/workspaces/SimulationWorkspace";
import { MotionControlWorkspace } from "./components/workspaces/MotionControlWorkspace";
import { ValidationLabWorkspace } from "./components/workspaces/ValidationLabWorkspace";
import { ReportsWorkspace } from "./components/workspaces/ReportsWorkspace";
import { SettingsWorkspace } from "./components/workspaces/SettingsWorkspace";
import { useAppStore } from "./store/useAppStore";
import { simWebSocket } from "./services/websocket";
import { fetchHealth, fetchProjects, fetchProjectDetails, sendSimControl } from "./services/api";
import type { WorkspaceId } from "./types/engineering";

export const App: React.FC = () => {
  const {
    activeWorkspace,
    setActiveWorkspace,
    setConnectionStatus,
    setHealth,
    setLatencyMs,
    setProjects,
    setActiveProject,
    setTelemetry,
    addLog,
    addToast,
    viewportSettings,
    updateViewportSettings,
    telemetry,
  } = useAppStore();

  useEffect(() => {
    addLog("INFO", "App", "MonkeyBots Professional Robotics Workstation initialized.");

    // 1. Establish Real-time WebSocket connection (60 Hz telemetry)
    simWebSocket.connect();

    const unsubTelemetry = simWebSocket.onTelemetry((frame) => {
      setTelemetry(frame);
    });

    const unsubStatus = simWebSocket.onStatus((status) => {
      setConnectionStatus(status);
      addLog("INFO", "WebSocket", `Telemetry gateway status: ${status}`);
    });

    // 2. Discover local projects and health check
    const initApp = async () => {
      const t0 = performance.now();
      try {
        const h = await fetchHealth();
        setHealth(h);
        setLatencyMs(Math.round(performance.now() - t0));

        const pList = await fetchProjects();
        setProjects(pList);

        if (pList.length > 0) {
          const defaultProj = await fetchProjectDetails(pList[0].id);
          setActiveProject(defaultProj, pList[0].id);
        }
      } catch {
        // Backend startup pending
      }
    };
    initApp();

    // 3. Periodic health polling & latency measurement
    const timer = setInterval(async () => {
      const t0 = performance.now();
      try {
        const h = await fetchHealth();
        setHealth(h);
        setLatencyMs(Math.round(performance.now() - t0));
      } catch {
        // Handled
      }
    }, 3000);

    return () => {
      clearInterval(timer);
      unsubTelemetry();
      unsubStatus();
      simWebSocket.disconnect();
    };
  }, []);

  // Global Engineering Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if user is typing in an input
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      // Space: Toggle Play/Pause
      if (e.code === "Space") {
        e.preventDefault();
        const isRunning = telemetry?.status === "RUNNING";
        const action = isRunning ? "PAUSE" : "START";
        simWebSocket.sendSimControl(action);
        sendSimControl(action).catch(() => {});
      }

      // R: Reset simulation
      if (e.key === "r" || e.key === "R") {
        e.preventDefault();
        simWebSocket.sendSimControl("RESET");
        sendSimControl("RESET").catch(() => {});
        addToast("info", "Simulation Reset", "Reset physics state to initial conditions.");
      }

      // G: Toggle ground grid
      if (e.key === "g" || e.key === "G") {
        updateViewportSettings({ showGrid: !viewportSettings.showGrid });
      }

      // W: Cycle shading mode
      if (e.key === "w" || e.key === "W") {
        const next =
          viewportSettings.shadingMode === "solid"
            ? "wireframe"
            : viewportSettings.shadingMode === "wireframe"
            ? "collision"
            : "solid";
        updateViewportSettings({ shadingMode: next });
      }

      // 1 - 8: Switch workspaces
      const workspaceMap: Record<string, WorkspaceId> = {
        "1": "home",
        "2": "projects",
        "3": "designer",
        "4": "simulation",
        "5": "motion",
        "6": "validation",
        "7": "reports",
        "8": "settings",
      };
      if (workspaceMap[e.key]) {
        setActiveWorkspace(workspaceMap[e.key]);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [telemetry, viewportSettings]);

  // Render Active Workspace Component
  const renderWorkspace = () => {
    switch (activeWorkspace) {
      case "home":
        return <HomeWorkspace />;
      case "projects":
        return <ProjectsWorkspace />;
      case "designer":
        return <RobotDesignerWorkspace />;
      case "simulation":
        return <SimulationWorkspace />;
      case "motion":
        return <MotionControlWorkspace />;
      case "validation":
        return <ValidationLabWorkspace />;
      case "reports":
        return <ReportsWorkspace />;
      case "settings":
        return <SettingsWorkspace />;
      default:
        return <SimulationWorkspace />;
    }
  };

  return (
    <div className="flex h-screen w-screen bg-slate-950 text-slate-100 overflow-hidden font-sans select-none">
      {/* 1. Left Navigation Sidebar Rail */}
      <SidebarRail />

      {/* 2. Main Workstation Body */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        <TopToolbar />
        <ErrorBanner />

        {/* Dynamic Workspace Container */}
        <main className="flex-1 flex overflow-hidden relative min-h-0">
          {renderWorkspace()}
        </main>

        <StatusBar />
      </div>

      {/* Floating Notifications */}
      <ToastContainer />
    </div>
  );
};

export default App;
