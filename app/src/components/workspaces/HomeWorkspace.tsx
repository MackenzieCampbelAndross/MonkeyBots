import React from "react";
import { useAppStore } from "../../store/useAppStore";
import {
  Cpu,
  ShieldCheck,
  ArrowRight,
  HardDrive,
  Activity,
  Zap,
} from "lucide-react";

export const HomeWorkspace: React.FC = () => {
  const { health, projects, setActiveWorkspace } = useAppStore();

  return (
    <div className="flex-1 overflow-y-auto p-8 bg-slate-950 text-slate-100 select-none space-y-8">
      {/* Hero Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 space-y-3 relative overflow-hidden">
        <div className="flex items-center space-x-3">
          <span className="text-3xl">🐒🤖</span>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-100">
              MONKEY<span className="text-amber-500">BOTS</span>
            </h1>
            <p className="text-sm text-slate-400 font-medium">
              Precision Robotics Engineering & High-Fidelity Physics Simulation Platform
            </p>
          </div>
        </div>
        <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
          Design robotic structures, configure degrees of freedom, simulate multi-body contact dynamics in
          MuJoCo, plan trajectory motions, and mathematically validate performance entirely on your local
          workstation.
        </p>

        <div className="pt-2 flex items-center space-x-3">
          <button
            onClick={() => setActiveWorkspace("simulation")}
            className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 rounded font-semibold text-xs flex items-center space-x-2 transition shadow"
          >
            <Activity className="w-4 h-4" />
            <span>Launch Simulation Workstation</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setActiveWorkspace("designer")}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded font-medium text-xs transition border border-slate-700"
          >
            Open Robot Designer
          </button>
        </div>
      </div>

      {/* Engineering Foundations Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5 space-y-2">
          <div className="flex items-center space-x-2 text-amber-400 font-semibold text-xs">
            <ShieldCheck className="w-4 h-4" />
            <span>LOCAL-FIRST & OFFLINE</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            100% self-contained. Operates completely without external AI APIs, cloud subscriptions, or databases.
            Your projects remain private on your local filesystem.
          </p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5 space-y-2">
          <div className="flex items-center space-x-2 text-sky-400 font-semibold text-xs">
            <Zap className="w-4 h-4" />
            <span>DETERMINISTIC MUJOCO</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Multi-body physics simulated at 500 Hz (dt = 0.002s) with exact inertia tensors, friction
            cones, and joint torque limits.
          </p>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-5 space-y-2">
          <div className="flex items-center space-x-2 text-emerald-400 font-semibold text-xs">
            <HardDrive className="w-4 h-4" />
            <span>STANDARD FORMATS</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Directly author, inspect, and export industry-standard URDF and native MuJoCo MJCF XML model files.
          </p>
        </div>
      </div>

      {/* Host System Verification Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 space-y-4">
        <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
          <Cpu className="w-4 h-4 text-sky-400" />
          <span>Workstation Hardware & Environment Status</span>
        </h2>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
          <div className="bg-slate-950 p-3 rounded border border-slate-800">
            <div className="text-[10px] text-slate-400 uppercase font-sans">Operating System</div>
            <div className="text-slate-200 mt-1">{health?.os || "win32 x64"}</div>
          </div>
          <div className="bg-slate-950 p-3 rounded border border-slate-800">
            <div className="text-[10px] text-slate-400 uppercase font-sans">Python Kernel</div>
            <div className="text-slate-200 mt-1">{health?.python_version || "3.11.9"}</div>
          </div>
          <div className="bg-slate-950 p-3 rounded border border-slate-800">
            <div className="text-[10px] text-slate-400 uppercase font-sans">Physics Backend</div>
            <div className="text-emerald-400 font-bold mt-1">MuJoCo Core</div>
          </div>
          <div className="bg-slate-950 p-3 rounded border border-slate-800">
            <div className="text-[10px] text-slate-400 uppercase font-sans">Local Projects Available</div>
            <div className="text-amber-400 font-bold mt-1">{projects.length} Found</div>
          </div>
        </div>
      </div>
    </div>
  );
};
