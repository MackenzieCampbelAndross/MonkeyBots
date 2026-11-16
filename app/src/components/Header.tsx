import React from "react";
import { useAppStore } from "../store/useAppStore";
import { simWebSocket } from "../services/websocket";
import { sendSimControl } from "../services/api";
import {
  Activity,
  Play,
  Pause,
  RotateCcw,
  Cpu,
  FolderOpen,
  Wifi,
  WifiOff,
} from "lucide-react";

export const Header: React.FC = () => {
  const { connectionStatus, health, latencyMs, telemetry, activeProjectId, projects } =
    useAppStore();

  const isRunning = telemetry?.status === "RUNNING";

  const handleTogglePlay = async () => {
    const action = isRunning ? "PAUSE" : "START";
    simWebSocket.sendSimControl(action);
    try {
      await sendSimControl(action);
    } catch {
      // Handled
    }
  };

  const handleReset = async () => {
    simWebSocket.sendSimControl("RESET");
    try {
      await sendSimControl("RESET");
    } catch {
      // Handled
    }
  };

  return (
    <header className="h-14 bg-slate-900 border-b border-slate-800 px-4 flex items-center justify-between select-none z-10">
      {/* Brand & Identity */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2">
          <span className="text-xl">🐒🤖</span>
          <span className="font-bold text-lg text-slate-100 tracking-wide">
            MONKEY<span className="text-amber-500">BOTS</span>
          </span>
        </div>
        <div className="hidden md:flex items-center pl-3 border-l border-slate-800 text-xs text-slate-400">
          Precision Robotics Lab
        </div>
      </div>

      {/* Central Simulation Controls */}
      <div className="flex items-center space-x-2 bg-slate-950/60 p-1 rounded-lg border border-slate-800/80">
        <button
          onClick={handleTogglePlay}
          className={`flex items-center space-x-1.5 px-3 py-1.5 rounded text-xs font-semibold transition ${
            isRunning
              ? "bg-amber-500/20 text-amber-400 border border-amber-500/30 hover:bg-amber-500/30"
              : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/30"
          }`}
          title={isRunning ? "Pause Simulation" : "Start Simulation"}
        >
          {isRunning ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
          <span>{isRunning ? "PAUSE" : "SIMULATE"}</span>
        </button>

        <button
          onClick={handleReset}
          className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 rounded transition"
          title="Reset Simulation State"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>

        <div className="px-2 border-l border-slate-800 text-[11px] text-slate-400 font-mono">
          t: {telemetry ? telemetry.sim_time.toFixed(2) : "0.00"}s
        </div>
      </div>

      {/* Right System & Connection Status */}
      <div className="flex items-center space-x-4">
        {/* Project indicator */}
        <div className="hidden lg:flex items-center space-x-1.5 text-xs text-slate-300 bg-slate-800/50 px-2.5 py-1 rounded border border-slate-700/50">
          <FolderOpen className="w-3.5 h-3.5 text-amber-400" />
          <span className="truncate max-w-[140px]">
            {activeProjectId || projects[0]?.name || "No Project"}
          </span>
        </div>

        {/* Backend Host & Diagnostics */}
        {health && (
          <div className="hidden xl:flex items-center space-x-3 text-[11px] text-slate-400 border-r border-slate-800 pr-3">
            <span className="flex items-center space-x-1" title="Host CPU utilization">
              <Cpu className="w-3 h-3 text-sky-400" />
              <span>{health.cpu_percent.toFixed(0)}%</span>
            </span>
            <span title="Physics Engine Status">
              {health.mujoco_available ? (
                <span className="text-emerald-400 font-medium">MuJoCo Core</span>
              ) : (
                <span className="text-amber-400">MuJoCo Sim</span>
              )}
            </span>
          </div>
        )}

        {/* Connection Status Pill */}
        <div
          className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
            connectionStatus === "CONNECTED"
              ? "bg-emerald-950/50 border-emerald-500/40 text-emerald-400"
              : connectionStatus === "CONNECTING"
              ? "bg-amber-950/50 border-amber-500/40 text-amber-400 animate-pulse"
              : "bg-rose-950/50 border-rose-500/40 text-rose-400"
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
          {connectionStatus === "CONNECTED" && latencyMs > 0 && (
            <span className="text-[10px] opacity-75 font-mono">({latencyMs}ms)</span>
          )}
        </div>
      </div>
    </header>
  );
};
