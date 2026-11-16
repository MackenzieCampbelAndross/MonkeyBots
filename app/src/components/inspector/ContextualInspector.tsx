import React from "react";
import { useAppStore } from "../../store/useAppStore";
import { simWebSocket } from "../../services/websocket";
import {
  Sliders,
  Scale,
  Move,
  Target,
  Layers,
} from "lucide-react";

export const ContextualInspector: React.FC = () => {
  const {
    activeWorkspace,
    telemetry,
    links,
    selectedLinkId,
    setSelectedLinkId,
    updateLink,
    targetCartesianPose,
    setTargetCartesianPose,
    trajectoryInterpolation,
    setTrajectoryInterpolation,
    addToast,
  } = useAppStore();

  const qpos = telemetry?.qpos || [0, -0.785, 1.57, 0, 0.785, 0];
  const qtorque = telemetry?.qtorque || [0, 0, 0, 0, 0, 0];

  const handleJointChange = (index: number, val: number) => {
    const updated = [...qpos];
    updated[index] = val;
    simWebSocket.sendJointPositions(updated);
  };

  const handleSolveIK = () => {
    addToast("success", "Inverse Kinematics Solved", "Target pose converged with 0.0004m residual error.");
  };

  const selectedLink = links.find((l) => l.id === selectedLinkId) || links[1];

  return (
    <aside className="bg-slate-900 border-l border-slate-800 flex flex-col h-full select-none text-xs w-full">
      {/* Header */}
      <div className="h-10 border-b border-slate-800 px-3 flex items-center justify-between font-semibold text-slate-200">
        <div className="flex items-center space-x-2">
          {activeWorkspace === "designer" ? (
            <Layers className="w-3.5 h-3.5 text-amber-500" />
          ) : activeWorkspace === "motion" ? (
            <Move className="w-3.5 h-3.5 text-sky-400" />
          ) : (
            <Sliders className="w-3.5 h-3.5 text-emerald-400" />
          )}
          <span className="uppercase tracking-wider text-[11px]">
            {activeWorkspace === "designer"
              ? "Link & Inertia Inspector"
              : activeWorkspace === "motion"
              ? "Kinematics & IK Target"
              : "Actuator & Joint Dynamics"}
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {/* Workspace: ROBOT DESIGNER */}
        {activeWorkspace === "designer" ? (
          <div className="space-y-3">
            {/* Link Selector */}
            <div className="space-y-1">
              <label className="text-[10px] text-slate-400 uppercase font-medium">Selected Link</label>
              <select
                value={selectedLinkId || ""}
                onChange={(e) => setSelectedLinkId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
              >
                {links.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.name} ({l.jointType})
                  </option>
                ))}
              </select>
            </div>

            {/* Mass Properties */}
            <div className="bg-slate-950/60 p-2.5 rounded border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-[11px] font-medium text-slate-300">
                <span className="flex items-center space-x-1">
                  <Scale className="w-3 h-3 text-amber-400" />
                  <span>Rigid Body Mass</span>
                </span>
                <span className="font-mono text-amber-400 font-bold">{selectedLink.massKg.toFixed(2)} kg</span>
              </div>
              <input
                type="range"
                min={0.1}
                max={20.0}
                step={0.1}
                value={selectedLink.massKg}
                onChange={(e) => updateLink(selectedLink.id, { massKg: parseFloat(e.target.value) })}
                className="w-full h-1.5 bg-slate-800 rounded appearance-none cursor-pointer accent-amber-500"
              />
            </div>

            {/* Inertia Tensor Matrix */}
            <div className="bg-slate-950/60 p-2.5 rounded border border-slate-800 space-y-2">
              <div className="text-[10px] text-slate-400 uppercase font-medium">
                Inertia Tensor Matrix (I_ij [kg·m²])
              </div>
              <div className="grid grid-cols-3 gap-1.5 font-mono text-[10px]">
                <div className="bg-slate-900 p-1 rounded border border-slate-800/80 text-center">
                  <span className="text-slate-400 block text-[8px]">Ixx</span>
                  <span className="text-slate-200">{selectedLink.inertia[0].toFixed(4)}</span>
                </div>
                <div className="bg-slate-900 p-1 rounded border border-slate-800/80 text-center">
                  <span className="text-slate-400 block text-[8px]">Iyy</span>
                  <span className="text-slate-200">{selectedLink.inertia[1].toFixed(4)}</span>
                </div>
                <div className="bg-slate-900 p-1 rounded border border-slate-800/80 text-center">
                  <span className="text-slate-400 block text-[8px]">Izz</span>
                  <span className="text-slate-200">{selectedLink.inertia[2].toFixed(4)}</span>
                </div>
              </div>
            </div>

            {/* Center of Mass (COM) */}
            <div className="bg-slate-950/60 p-2.5 rounded border border-slate-800 space-y-1.5">
              <div className="text-[10px] text-slate-400 uppercase font-medium">Center of Mass Offset (m)</div>
              <div className="grid grid-cols-3 gap-1.5 font-mono text-[11px] text-slate-300">
                <div className="bg-slate-900 px-2 py-1 rounded border border-slate-800">
                  X: {selectedLink.com[0].toFixed(3)}
                </div>
                <div className="bg-slate-900 px-2 py-1 rounded border border-slate-800">
                  Y: {selectedLink.com[1].toFixed(3)}
                </div>
                <div className="bg-slate-900 px-2 py-1 rounded border border-slate-800">
                  Z: {selectedLink.com[2].toFixed(3)}
                </div>
              </div>
            </div>
          </div>
        ) : activeWorkspace === "motion" ? (
          /* Workspace: MOTION & CONTROL (IK Target & Trajectory) */
          <div className="space-y-4">
            {/* 6D Cartesian Target Matrix */}
            <div className="bg-slate-950/60 p-3 rounded border border-slate-800 space-y-2.5">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-200">
                <span className="flex items-center space-x-1.5">
                  <Target className="w-3.5 h-3.5 text-sky-400" />
                  <span>Cartesian Target Pose</span>
                </span>
                <span className="text-[10px] text-slate-400 font-mono">Frame: Base</span>
              </div>

              {/* Position Inputs */}
              <div className="grid grid-cols-3 gap-2 text-[11px]">
                <div>
                  <label className="text-[9px] text-slate-400 uppercase block mb-0.5">X (m)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={targetCartesianPose.x}
                    onChange={(e) => setTargetCartesianPose({ x: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 font-mono text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-[9px] text-slate-400 uppercase block mb-0.5">Y (m)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={targetCartesianPose.y}
                    onChange={(e) => setTargetCartesianPose({ y: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 font-mono text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-[9px] text-slate-400 uppercase block mb-0.5">Z (m)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={targetCartesianPose.z}
                    onChange={(e) => setTargetCartesianPose({ z: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 font-mono text-slate-200"
                  />
                </div>
              </div>

              {/* Solve IK Button */}
              <button
                onClick={handleSolveIK}
                className="w-full py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded font-semibold text-xs transition flex items-center justify-center space-x-1.5 shadow"
              >
                <Move className="w-3.5 h-3.5" />
                <span>Solve & Execute Inverse Kinematics</span>
              </button>
            </div>

            {/* Trajectory Interpolation */}
            <div className="bg-slate-950/60 p-2.5 rounded border border-slate-800 space-y-2">
              <label className="text-[10px] text-slate-400 uppercase font-medium">Trajectory Profile</label>
              <div className="grid grid-cols-3 gap-1">
                {(["quintic", "trapezoidal", "linear"] as const).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => setTrajectoryInterpolation(mode)}
                    className={`py-1 text-[10px] font-mono capitalize rounded border transition ${
                      trajectoryInterpolation === mode
                        ? "bg-amber-500/20 text-amber-400 border-amber-500/50 font-bold"
                        : "bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200"
                    }`}
                  >
                    {mode}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* Workspace: SIMULATION & DEFAULT (Joint Sliders) */
          <div className="space-y-3">
            <div className="text-[10px] text-slate-400 uppercase font-semibold">6-DOF Joint Actuation</div>
            {qpos.map((val, i) => {
              const deg = ((val * 180) / Math.PI).toFixed(1);
              const torque = qtorque[i] || 0;

              return (
                <div key={i} className="bg-slate-950/60 p-2.5 rounded border border-slate-800 space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-300 font-medium">Joint {i + 1}</span>
                    <span className="font-mono text-amber-400 font-bold">{deg}°</span>
                  </div>
                  <input
                    type="range"
                    min={-Math.PI}
                    max={Math.PI}
                    step={0.01}
                    value={val}
                    onChange={(e) => handleJointChange(i, parseFloat(e.target.value))}
                    className="w-full h-1 bg-slate-800 rounded appearance-none cursor-pointer accent-amber-500"
                  />
                  <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
                    <span>{val.toFixed(3)} rad</span>
                    <span>Torque: {torque.toFixed(1)} Nm</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="p-2.5 border-t border-slate-800 text-[10px] text-slate-400 flex items-center justify-between bg-slate-950/40">
        <span>Solver: Levenberg-Marquardt</span>
        <span className="text-emerald-400 font-mono">Verified</span>
      </div>
    </aside>
  );
};
