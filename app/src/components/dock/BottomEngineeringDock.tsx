import React, { useState } from "react";
import { useAppStore } from "../../store/useAppStore";
import {
  Activity,
  Terminal,
  Trash2,
  Minimize2,
} from "lucide-react";

export const BottomEngineeringDock: React.FC = () => {
  const {
    telemetry,
    logs,
    clearLogs,
    bottomDockHeight,
    isBottomDockCollapsed,
    toggleBottomDock,
  } = useAppStore();

  const [activeTab, setActiveTab] = useState<"oscilloscope" | "logs">("oscilloscope");
  const [logFilter, setLogFilter] = useState<string>("ALL");

  if (isBottomDockCollapsed) return null;

  const filteredLogs = logs.filter((l) => (logFilter === "ALL" ? true : l.level === logFilter));

  const qpos = telemetry?.qpos || [0, 0, 0, 0, 0, 0];
  const qtorque = telemetry?.qtorque || [0, 0, 0, 0, 0, 0];

  return (
    <div
      style={{ height: `${bottomDockHeight}px` }}
      className="bg-slate-900 border-t border-slate-800 flex flex-col select-none z-20"
    >
      {/* Dock Header Tabs */}
      <div className="h-8 border-b border-slate-800 px-3 flex items-center justify-between text-xs">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setActiveTab("oscilloscope")}
            className={`flex items-center space-x-1.5 h-8 border-b-2 font-medium transition ${
              activeTab === "oscilloscope"
                ? "border-amber-500 text-amber-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>REAL-TIME OSCILLOSCOPE</span>
          </button>

          <button
            onClick={() => setActiveTab("logs")}
            className={`flex items-center space-x-1.5 h-8 border-b-2 font-medium transition ${
              activeTab === "logs"
                ? "border-amber-500 text-amber-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>ENGINE CONSOLE ({logs.length})</span>
          </button>
        </div>

        {/* Right Controls */}
        <div className="flex items-center space-x-2">
          {activeTab === "logs" && (
            <>
              <div className="flex items-center space-x-1 text-[10px] bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800">
                <span className="text-slate-400">Filter:</span>
                {(["ALL", "INFO", "WARNING", "ERROR"] as const).map((f) => (
                  <button
                    key={f}
                    onClick={() => setLogFilter(f)}
                    className={`px-1 rounded ${
                      logFilter === f ? "text-amber-400 font-bold" : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {f}
                  </button>
                ))}
              </div>

              <button
                onClick={clearLogs}
                className="text-[10px] text-slate-400 hover:text-slate-200 p-1 flex items-center space-x-1"
                title="Clear Logs"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            </>
          )}

          <button
            onClick={toggleBottomDock}
            className="p-1 text-slate-400 hover:text-slate-200 transition"
            title="Minimize Dock"
          >
            <Minimize2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Dock Content */}
      <div className="flex-1 overflow-auto p-3 text-xs font-mono">
        {activeTab === "oscilloscope" ? (
          <div className="grid grid-cols-2 md:grid-cols-6 gap-2 h-full">
            {qpos.map((pos, i) => {
              const torque = qtorque[i] || 0;
              const torquePercent = Math.min(100, Math.abs(torque / 150) * 100);

              return (
                <div key={i} className="bg-slate-950 p-2.5 rounded border border-slate-800 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-400 font-medium">J{i + 1}</span>
                    <span className="text-amber-400 font-bold font-mono">
                      {((pos * 180) / Math.PI).toFixed(1)}°
                    </span>
                  </div>

                  {/* Waveform / Level Meter */}
                  <div className="my-1.5">
                    <div className="text-[9px] text-slate-400 flex justify-between mb-0.5">
                      <span>Torque</span>
                      <span>{torque.toFixed(1)} Nm</span>
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div
                        className="bg-sky-400 h-full rounded-full transition-all duration-75"
                        style={{ width: `${torquePercent}%` }}
                      />
                    </div>
                  </div>

                  <div className="text-[10px] text-slate-400 flex justify-between">
                    <span>Pos (rad)</span>
                    <span className="text-slate-200 font-mono">{pos.toFixed(3)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* Logs Terminal */
          <div className="space-y-1">
            {filteredLogs.length === 0 ? (
              <div className="text-slate-400 text-xs">No matching engine events.</div>
            ) : (
              filteredLogs.map((log) => (
                <div key={log.id} className="flex items-start space-x-2 text-[11px] leading-tight">
                  <span className="text-slate-400 shrink-0 font-mono">[{log.timestamp}]</span>
                  <span
                    className={`shrink-0 font-semibold ${
                      log.level === "ERROR"
                        ? "text-rose-400"
                        : log.level === "WARNING"
                        ? "text-amber-400"
                        : log.level === "INFO"
                        ? "text-sky-400"
                        : "text-slate-400"
                    }`}
                  >
                    [{log.level}]
                  </span>
                  <span className="text-amber-400 shrink-0">[{log.source}]</span>
                  <span className="text-slate-300">{log.message}</span>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};
