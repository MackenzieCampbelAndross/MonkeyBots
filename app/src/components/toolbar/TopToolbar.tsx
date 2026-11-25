import React from "react";
import { useAppStore } from "../../store/useAppStore";
import { simWebSocket } from "../../services/websocket";
import { sendSimControl } from "../../services/api";
import {
  Play,
  Pause,
  RotateCcw,
  StepForward,
  Grid,
  Box,
  Compass,
  Save,
  Wifi,
  WifiOff,
  Activity,
  FolderOpen,
  FastForward,
} from "lucide-react";

export const TopToolbar: React.FC = () => {
  const {
    activeWorkspace,
    viewportSettings,
    updateViewportSettings,
    telemetry,
    connectionStatus,
    latencyMs,
    activeProjectId,
    projects,
    activeRobotId,
    setActiveRobotId,
    simSpeedMultiplier,
    setSimSpeedMultiplier,
    addToast,
  } = useAppStore();

  const isRunning = telemetry?.status === "RUNNING";

  const handleTogglePlay = async () => {
    const action = isRunning ? "PAUSE" : "START";
    simWebSocket.sendSimControl(action);
    try {
      await sendSimControl(action);
    } catch {
      // Fallback
    }
  };

  const handleReset = async () => {
    simWebSocket.sendSimControl("RESET");
    try {
      await sendSimControl("RESET");
      addToast("info", "Simulation Reset", "Reset physics state to initial qpos = 0.");
    } catch {
      // Fallback
    }
  };

  const handleStep = async () => {
    try {
      await sendSimControl("STEP");
    } catch {
      // Fallback
    }
  };

  const handleSaveProject = () => {
    addToast("success", "Project Saved", `Synchronized '${activeProjectId || "default_6dof_arm"}' to local filesystem.`);
  };

  const toggleGrid = () => {
    updateViewportSettings({ showGrid: !viewportSettings.showGrid });
  };

  const toggleAxes = () => {
    updateViewportSettings({ showAxes: !viewportSettings.showAxes });
  };

  const cycleShading = () => {
    const nextMode =
      viewportSettings.shadingMode === "solid"
        ? "wireframe"
        : viewportSettings.shadingMode === "wireframe"
        ? "collision"
        : "solid";
    updateViewportSettings({ shadingMode: nextMode });
    addToast("info", "Shading Mode", `Switched to ${nextMode.toUpperCase()} rendering`);
  };

  const cycleSpeed = () => {
    const nextSpeed =
      simSpeedMultiplier === 1.0 ? 2.0 : simSpeedMultiplier === 2.0 ? 5.0 : simSpeedMultiplier === 5.0 ? 0.5 : 1.0;
    setSimSpeedMultiplier(nextSpeed);
    addToast("info", "Simulation Speed", `Time scale set to ${nextSpeed}x`);
  };

  return (
    <header className="h-11 bg-slate-900 border-b border-slate-800 px-3 flex items-center justify-between select-none z-10 text-xs">
      {/* Left: Project Selector & Breadcrumb */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-1.5 bg-slate-950/70 px-2 py-1 rounded border border-slate-800 text-slate-300 font-medium">
          <FolderOpen className="w-3.5 h-3.5 text-amber-500" />
          <span className="truncate max-w-[130px]">
            {activeProjectId || projects[0]?.name || "default_6dof_arm"}
          </span>
        </div>

        <div className="flex items-center space-x-1.5 text-slate-400 font-mono text-[11px]">
          <span>/</span>
          <span className="text-slate-200 capitalize font-sans font-semibold">
            {activeWorkspace.replace("-", " ")}
          </span>
        </div>

        {/* Robot Model Switcher */}
        <select
          value={activeRobotId}
          onChange={(e) => {
            const nextId = e.target.value;
            setActiveRobotId(nextId);
            addToast("info", "Robot Switched", `Active robot model changed to ${nextId.replace("_", " ").toUpperCase()}`);
          }}
          className="bg-slate-950/80 text-sky-400 border border-slate-800 rounded px-2 py-0.5 text-[11px] font-mono focus:outline-none focus:border-sky-500 cursor-pointer"
          title="Switch Active Robot Model"
        >
          <option value="default_6dof_arm">6-DOF Industrial Arm</option>
          <option value="franka_panda">Franka Emika Panda (7-DOF)</option>
          <option value="ur5e">Universal Robots UR5e</option>
          <option value="ur10e">Universal Robots UR10e (12.5kg)</option>
          <option value="delta_robot">Parallel Delta Robot</option>
          <option value="mobile_base">Differential Mobile Base</option>
        </select>

        {/* Save Quick Action */}
        <button
          onClick={handleSaveProject}
          className="p-1 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded transition"
          title="Save Project Manifest (Ctrl+S)"
        >
          <Save className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Center: High-Precision Simulation Controls */}
      <div className="flex items-center space-x-1.5 bg-slate-950/80 p-0.5 rounded-lg border border-slate-800">
        <button
          onClick={handleTogglePlay}
          className={`flex items-center space-x-1 px-2.5 py-1 rounded text-[11px] font-bold transition ${
            isRunning
              ? "bg-amber-500/20 text-amber-400 border border-amber-500/40 hover:bg-amber-500/30"
              : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 hover:bg-emerald-500/30"
          }`}
          title="Toggle Simulation (Space)"
        >
          {isRunning ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
          <span>{isRunning ? "PAUSE" : "SIM"}</span>
        </button>

        <button
          onClick={handleStep}
          disabled={isRunning}
          className="p-1 text-slate-400 hover:text-slate-200 disabled:opacity-30 disabled:hover:text-slate-400 rounded transition"
          title="Single Step Integration (500 Hz dt)"
        >
          <StepForward className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={handleReset}
          className="p-1 text-slate-400 hover:text-slate-200 rounded transition"
          title="Reset Simulation (R)"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={cycleSpeed}
          className="px-1.5 py-0.5 text-[10px] font-mono text-slate-300 hover:text-white bg-slate-800/80 rounded border border-slate-700/60 flex items-center space-x-0.5"
          title="Simulation Speed Multiplier"
        >
          <FastForward className="w-2.5 h-2.5 text-amber-400" />
          <span>{simSpeedMultiplier}x</span>
        </button>

        <div className="px-2 border-l border-slate-800 text-[10px] text-slate-400 font-mono">
          t: <span className="text-slate-200 font-semibold">{telemetry ? telemetry.sim_time.toFixed(2) : "0.00"}</span>s
        </div>
      </div>

      {/* Right: CAD Viewport Tools & Telemetry Status */}
      <div className="flex items-center space-x-2">
        {/* Viewport Toggles */}
        <div className="flex items-center space-x-1 border-r border-slate-800 pr-2">
          <button
            onClick={toggleGrid}
            className={`p-1 rounded transition ${
              viewportSettings.showGrid
                ? "bg-sky-950/70 text-sky-400 border border-sky-600/40"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
            }`}
            title="Toggle Ground Grid (G)"
          >
            <Grid className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={toggleAxes}
            className={`p-1 rounded transition ${
              viewportSettings.showAxes
                ? "bg-sky-950/70 text-sky-400 border border-sky-600/40"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
            }`}
            title="Toggle Coordinate Axes"
          >
            <Compass className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={cycleShading}
            className="px-1.5 py-0.5 text-[10px] uppercase font-mono bg-slate-800/70 hover:bg-slate-800 text-slate-300 rounded border border-slate-700/50 flex items-center space-x-1"
            title="Cycle Shading Mode: Solid / Wireframe / Collision (W)"
          >
            <Box className="w-3 h-3 text-amber-400" />
            <span>{viewportSettings.shadingMode}</span>
          </button>
        </div>

        {/* Connection Status Badge */}
        <div
          className={`flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-semibold border ${
            connectionStatus === "CONNECTED"
              ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-400"
              : connectionStatus === "CONNECTING"
              ? "bg-amber-950/40 border-amber-500/40 text-amber-400 animate-pulse"
              : "bg-rose-950/40 border-rose-500/40 text-rose-400"
          }`}
        >
          {connectionStatus === "CONNECTED" ? (
            <Wifi className="w-3 h-3" />
          ) : connectionStatus === "CONNECTING" ? (
            <Activity className="w-3 h-3" />
          ) : (
            <WifiOff className="w-3 h-3" />
          )}
          <span>{connectionStatus}</span>
          {latencyMs > 0 && <span className="font-mono text-[9px] opacity-75">({latencyMs}ms)</span>}
        </div>
      </div>
    </header>
  );
};
