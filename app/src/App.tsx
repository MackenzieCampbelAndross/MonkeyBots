import React, { useEffect } from "react";
import { Header } from "./components/Header";
import { Viewport3D } from "./components/Viewport3D";
import { JointInspector } from "./components/JointInspector";
import { ProjectExplorer } from "./components/ProjectExplorer";
import { TelemetryPanel } from "./components/TelemetryPanel";
import { ErrorBanner } from "./components/ErrorBanner";
import { useAppStore } from "./store/useAppStore";
import { simWebSocket } from "./services/websocket";
import { fetchHealth, fetchProjects, fetchProjectDetails } from "./services/api";

export const App: React.FC = () => {
  const {
    setConnectionStatus,
    setHealth,
    setLatencyMs,
    setProjects,
    setActiveProject,
    setTelemetry,
    addLog,
  } = useAppStore();

  useEffect(() => {
    addLog("INFO", "App", "MonkeyBots Desktop Application Initialized.");

    // 1. Establish Real-time WebSocket connection
    simWebSocket.connect();

    const unsubTelemetry = simWebSocket.onTelemetry((frame) => {
      setTelemetry(frame);
    });

    const unsubStatus = simWebSocket.onStatus((status) => {
      setConnectionStatus(status);
      addLog("INFO", "WebSocket", `Connection status changed to ${status}`);
    });

    // 2. Initial Health Check & Projects Discovery
    const checkHealthAndProjects = async () => {
      const startTime = performance.now();
      try {
        const healthData = await fetchHealth();
        const latency = Math.round(performance.now() - startTime);
        setHealth(healthData);
        setLatencyMs(latency);

        const projectList = await fetchProjects();
        setProjects(projectList);

        if (projectList.length > 0) {
          const defaultProj = await fetchProjectDetails(projectList[0].id);
          setActiveProject(defaultProj, projectList[0].id);
        }
      } catch (err: any) {
        // Backend not online or reconnecting
      }
    };

    checkHealthAndProjects();

    // 3. Periodic health polling & latency ping (every 3 seconds)
    const healthInterval = setInterval(async () => {
      const t0 = performance.now();
      try {
        const h = await fetchHealth();
        setHealth(h);
        setLatencyMs(Math.round(performance.now() - t0));
      } catch {
        // Handled by connection status
      }
    }, 3000);

    return () => {
      clearInterval(healthInterval);
      unsubTelemetry();
      unsubStatus();
      simWebSocket.disconnect();
    };
  }, []);

  return (
    <div className="flex flex-col h-screen w-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      <Header />
      <ErrorBanner />

      {/* Main 3-Column CAD Workstation Layout */}
      <div className="flex flex-1 overflow-hidden">
        <ProjectExplorer />
        <main className="flex-1 relative flex flex-col min-w-0">
          <div className="flex-1 relative">
            <Viewport3D />
          </div>
          <TelemetryPanel />
        </main>
        <JointInspector />
      </div>
    </div>
  );
};

export default App;
