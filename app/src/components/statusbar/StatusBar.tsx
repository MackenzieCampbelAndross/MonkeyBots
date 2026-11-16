import React from "react";
import { useAppStore } from "../../store/useAppStore";
import { Terminal } from "lucide-react";

export const StatusBar: React.FC = () => {
  const {
    telemetry,
    worldCursorCoords,
    selectedLinkId,
    isBottomDockCollapsed,
    toggleBottomDock,
    activeWorkspace,
  } = useAppStore();

  const isRunning = telemetry?.status === "RUNNING";

  return (
    <footer className="h-6 bg-slate-900 border-t border-slate-800 px-3 flex items-center justify-between text-[11px] font-mono text-slate-400 select-none z-30">
      {/* Left: Execution Status */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-1.5">
          <div
            className={`w-2 h-2 rounded-full ${
              isRunning ? "bg-emerald-500 animate-pulse" : "bg-amber-500"
            }`}
          />
          <span className="font-semibold text-slate-200">
            {isRunning ? "SIMULATING (500 Hz)" : "SOLVER READY"}
          </span>
        </div>

        <button
          onClick={toggleBottomDock}
          className="flex items-center space-x-1 text-slate-400 hover:text-slate-200 transition"
          title="Toggle Engineering Oscilloscope & Logs"
        >
          <Terminal className="w-3 h-3" />
          <span>{isBottomDockCollapsed ? "Show Dock" : "Hide Dock"}</span>
        </button>

        <span className="text-slate-400 hidden sm:inline">|</span>
        <span className="text-slate-400 hidden sm:inline">
          Workspace: <span className="text-amber-400 capitalize">{activeWorkspace}</span>
        </span>
      </div>

      {/* Center: Cursor World Coordinates HUD */}
      <div className="hidden md:flex items-center space-x-3">
        <span>
          World Cursor: X:{" "}
          <span className="text-slate-200">{worldCursorCoords.x.toFixed(3)}</span>m Y:{" "}
          <span className="text-slate-200">{worldCursorCoords.y.toFixed(3)}</span>m Z:{" "}
          <span className="text-slate-200">{worldCursorCoords.z.toFixed(3)}</span>m
        </span>
        {selectedLinkId && (
          <span className="text-slate-400">
            Selected: <span className="text-sky-400">{selectedLinkId}</span>
          </span>
        )}
      </div>

      {/* Right: Physics Stepper & Local Verification */}
      <div className="flex items-center space-x-3">
        <span>dt: 0.002s (RK4)</span>
        <span className="text-slate-400">|</span>
        <span className="text-emerald-400 font-medium">Local-First</span>
      </div>
    </footer>
  );
};
