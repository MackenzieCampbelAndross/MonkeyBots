import React from "react";
import { useAppStore } from "../store/useAppStore";
import { Terminal, Activity, Trash2 } from "lucide-react";

export const TelemetryPanel: React.FC = () => {
  const { telemetry, logs, clearLogs, activeTab, setActiveTab } = useAppStore();

  return (
    <div className="h-44 bg-slate-900 border-t border-slate-800 flex flex-col select-none">
      {/* Tab Navigation */}
      <div className="h-8 border-b border-slate-800 px-3 flex items-center justify-between text-xs">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setActiveTab("inspector")}
            className={`flex items-center space-x-1.5 h-8 border-b-2 font-medium transition ${
              activeTab === "inspector"
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
            <span>ENGINE LOGS ({logs.length})</span>
          </button>
        </div>

        {activeTab === "logs" && (
          <button
            onClick={clearLogs}
            className="text-[10px] text-slate-400 hover:text-slate-200 flex items-center space-x-1"
          >
            <Trash2 className="w-3 h-3" />
            <span>Clear</span>
          </button>
        )}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-auto p-3 text-xs font-mono">
        {activeTab === "inspector" && telemetry ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-slate-950/60 p-2.5 rounded border border-slate-800/80">
              <div className="text-[10px] text-slate-400 uppercase font-sans">Physics Step Count</div>
              <div className="text-sm font-bold text-sky-400 mt-1">{telemetry.step_count.toLocaleString()}</div>
              <div className="text-[10px] text-slate-400 mt-0.5">dt: 0.002s (500 Hz)</div>
            </div>

            <div className="bg-slate-950/60 p-2.5 rounded border border-slate-800/80">
              <div className="text-[10px] text-slate-400 uppercase font-sans">Real-Time Factor</div>
              <div className="text-sm font-bold text-emerald-400 mt-1">{telemetry.real_time_factor.toFixed(2)}x</div>
              <div className="text-[10px] text-slate-400 mt-0.5">Sim Time: {telemetry.sim_time.toFixed(2)}s</div>
            </div>

            <div className="bg-slate-950/60 p-2.5 rounded border border-slate-800/80">
              <div className="text-[10px] text-slate-400 uppercase font-sans">Active Contacts</div>
              <div className="text-sm font-bold text-amber-400 mt-1">{telemetry.contacts.length}</div>
              <div className="text-[10px] text-slate-400 mt-0.5">Friction Cones Solved</div>
            </div>

            <div className="bg-slate-950/60 p-2.5 rounded border border-slate-800/80">
              <div className="text-[10px] text-slate-400 uppercase font-sans">Engine Status</div>
              <div className="text-sm font-bold text-slate-200 mt-1">{telemetry.status}</div>
              <div className="text-[10px] text-slate-400 mt-0.5">Deterministic MuJoCo</div>
            </div>
          </div>
        ) : activeTab === "logs" ? (
          <div className="space-y-1">
            {logs.length === 0 ? (
              <div className="text-slate-400">No events logged yet.</div>
            ) : (
              logs.map((log) => (
                <div key={log.id} className="flex items-start space-x-2 text-[11px] leading-tight">
                  <span className="text-slate-400 shrink-0">[{log.timestamp}]</span>
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
        ) : (
          <div className="text-slate-400">Waiting for simulation telemetry frame...</div>
        )}
      </div>
    </div>
  );
};
