import React from "react";
import { useAppStore } from "../store/useAppStore";
import { simWebSocket } from "../services/websocket";
import { Sliders, RotateCw, Gauge, ShieldAlert } from "lucide-react";

const JOINT_NAMES = [
  "Joint 1 (Base Yaw)",
  "Joint 2 (Shoulder Pitch)",
  "Joint 3 (Elbow Pitch)",
  "Joint 4 (Wrist 1 Roll)",
  "Joint 5 (Wrist 2 Pitch)",
  "Joint 6 (Flange Roll)",
];

const JOINT_LIMITS = [
  { min: -Math.PI, max: Math.PI },
  { min: -Math.PI / 2, max: Math.PI / 2 },
  { min: -Math.PI / 2, max: Math.PI / 2 },
  { min: -Math.PI, max: Math.PI },
  { min: -Math.PI, max: Math.PI },
  { min: -Math.PI, max: Math.PI },
];

export const JointInspector: React.FC = () => {
  const telemetry = useAppStore((state) => state.telemetry);
  const qpos = telemetry?.qpos || [0, -0.785, 1.57, 0, 0.785, 0];
  const qtorque = telemetry?.qtorque || [0, 0, 0, 0, 0, 0];

  const handleJointChange = (index: number, valueRad: number) => {
    const updated = [...qpos];
    updated[index] = valueRad;
    simWebSocket.sendJointPositions(updated);
  };

  const radToDeg = (rad: number) => ((rad * 180) / Math.PI).toFixed(1);

  return (
    <aside className="w-80 bg-slate-900 border-l border-slate-800 flex flex-col h-full select-none">
      <div className="p-3 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2 text-xs font-semibold text-slate-200">
          <Sliders className="w-4 h-4 text-amber-500" />
          <span>6-DOF JOINT CONTROLLER</span>
        </div>
        <button
          onClick={() => simWebSocket.sendJointPositions([0, 0, 0, 0, 0, 0])}
          className="text-[10px] text-slate-400 hover:text-amber-400 flex items-center space-x-1 transition"
          title="Zero all joint angles"
        >
          <RotateCw className="w-3 h-3" />
          <span>Zero</span>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {JOINT_NAMES.map((name, i) => {
          const val = qpos[i] ?? 0;
          const torque = qtorque[i] ?? 0;
          const limits = JOINT_LIMITS[i] || { min: -Math.PI, max: Math.PI };
          const minDeg = radToDeg(limits.min);
          const maxDeg = radToDeg(limits.max);

          return (
            <div key={i} className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-slate-300">{name}</span>
                <span className="font-mono text-amber-400 font-semibold">{radToDeg(val)}°</span>
              </div>

              {/* Angle Slider */}
              <input
                type="range"
                min={limits.min}
                max={limits.max}
                step={0.01}
                value={val}
                onChange={(e) => handleJointChange(i, parseFloat(e.target.value))}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
              />

              <div className="flex items-center justify-between text-[10px] text-slate-400">
                <span>{minDeg}°</span>
                <span className="font-mono">{val.toFixed(3)} rad</span>
                <span>{maxDeg}°</span>
              </div>

              {/* Joint Torque Meter */}
              <div className="flex items-center justify-between pt-1 border-t border-slate-800/60 text-[10px] text-slate-400">
                <span className="flex items-center space-x-1">
                  <Gauge className="w-3 h-3 text-sky-400" />
                  <span>Torque:</span>
                </span>
                <span className="font-mono text-slate-300">{torque.toFixed(1)} Nm</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Safety Notice Footer */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/40 text-[10px] text-slate-400 flex items-center space-x-2">
        <ShieldAlert className="w-3.5 h-3.5 text-amber-400 shrink-0" />
        <span>Hardware velocity & acceleration limits enforced in MuJoCo physics.</span>
      </div>
    </aside>
  );
};
