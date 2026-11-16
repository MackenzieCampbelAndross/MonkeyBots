import React from "react";
import { useAppStore } from "../../store/useAppStore";
import {
  Settings,
  Cpu,
  Monitor,
} from "lucide-react";

export const SettingsWorkspace: React.FC = () => {
  const { addToast } = useAppStore();

  const handleSaveSettings = () => {
    addToast("success", "Settings Saved", "Saved engineering preferences to local config.");
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 bg-slate-950 text-slate-100 select-none space-y-6">
      {/* Workspace Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
            <Settings className="w-5 h-5 text-amber-500" />
            <span>Platform Configuration & Preferences</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Configure MuJoCo physics numerical parameters, Three.js 3D rendering quality, and local storage.
          </p>
        </div>

        <button
          onClick={handleSaveSettings}
          className="px-4 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 rounded font-semibold text-xs transition shadow"
        >
          Save Preferences
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Physics Solver Parameters */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-2 text-xs font-semibold text-slate-200">
            <Cpu className="w-4 h-4 text-sky-400" />
            <span>MuJoCo Physics Solver Settings</span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="space-y-1">
              <label className="text-[10px] text-slate-400 uppercase font-medium">Integration Timestep</label>
              <select className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 font-mono">
                <option value="0.001">0.001 s (1000 Hz - Ultra High Precision)</option>
                <option value="0.002" selected>0.002 s (500 Hz - Standard Engineering Default)</option>
                <option value="0.005">0.005 s (200 Hz - Low Compute)</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-[10px] text-slate-400 uppercase font-medium">Numerical Integrator</label>
              <select className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 font-mono">
                <option value="RK4" selected>Runge-Kutta 4th Order (RK4)</option>
                <option value="Euler">Semi-implicit Euler</option>
                <option value="Implicit">Implicit Fast (Newton-Raphson)</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-[10px] text-slate-400 uppercase font-medium">Gravity Acceleration Vector</label>
              <div className="grid grid-cols-3 gap-2 font-mono text-[11px]">
                <input
                  type="text"
                  value="0.0"
                  readOnly
                  className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-400"
                />
                <input
                  type="text"
                  value="0.0"
                  readOnly
                  className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-400"
                />
                <input
                  type="text"
                  value="-9.81"
                  readOnly
                  className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 font-bold"
                />
              </div>
            </div>
          </div>
        </div>

        {/* 3D Viewport Graphics Settings */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-2 text-xs font-semibold text-slate-200">
            <Monitor className="w-4 h-4 text-emerald-400" />
            <span>Three.js Viewport & Graphics</span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-2.5 bg-slate-950 rounded border border-slate-800">
              <div>
                <div className="font-medium text-slate-200">Hardware Antialiasing (MSAA)</div>
                <div className="text-[10px] text-slate-400">Smooth CAD mesh geometry edges</div>
              </div>
              <input type="checkbox" defaultChecked className="accent-amber-500 w-4 h-4 cursor-pointer" />
            </div>

            <div className="flex items-center justify-between p-2.5 bg-slate-950 rounded border border-slate-800">
              <div>
                <div className="font-medium text-slate-200">Dynamic Contact Shadows</div>
                <div className="text-[10px] text-slate-400">Soft shadow maps on ground plane</div>
              </div>
              <input type="checkbox" defaultChecked className="accent-amber-500 w-4 h-4 cursor-pointer" />
            </div>

            <div className="flex items-center justify-between p-2.5 bg-slate-950 rounded border border-slate-800">
              <div>
                <div className="font-medium text-slate-200">Frame Rate Cap</div>
                <div className="text-[10px] text-slate-400">Sync with monitor refresh rate</div>
              </div>
              <span className="font-mono text-amber-400 font-bold">60 / 120 Hz</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
