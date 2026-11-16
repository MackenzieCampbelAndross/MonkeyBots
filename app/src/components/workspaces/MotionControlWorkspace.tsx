import React from "react";
import { Viewport3D } from "../Viewport3D";
import { ContextualInspector } from "../inspector/ContextualInspector";
import { useAppStore } from "../../store/useAppStore";
import { simWebSocket } from "../../services/websocket";
import { Move3d, Play, RotateCcw } from "lucide-react";

export const MotionControlWorkspace: React.FC = () => {
  const { addToast } = useAppStore();

  const handleExecuteTrajectory = () => {
    // Send standard pick & place waypoint sweep
    simWebSocket.sendJointPositions([0.5, -0.4, 1.2, 0.0, 0.6, 0.2], 0.02);
    addToast("info", "Executing Trajectory", "Dispatching quintic joint-space trajectory to MuJoCo PID loop.");
  };

  const handleReturnHome = () => {
    simWebSocket.sendJointPositions([0, -0.785, 1.57, 0, 0.785, 0], 0.04);
    addToast("info", "Motion Planning", "Returning arm to nominal calibration home pose.");
  };

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* Motion Planning Left Dock */}
      <div className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col p-3 space-y-3 select-none text-xs">
        <div className="flex items-center space-x-2 font-semibold text-slate-200 border-b border-slate-800 pb-2">
          <Move3d className="w-4 h-4 text-sky-400" />
          <span>TRAJECTORY PLANNER</span>
        </div>

        <div className="space-y-2">
          <button
            onClick={handleExecuteTrajectory}
            className="w-full py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded flex items-center justify-center space-x-1.5 transition shadow"
          >
            <Play className="w-3.5 h-3.5" />
            <span>Execute Pick & Place Path</span>
          </button>

          <button
            onClick={handleReturnHome}
            className="w-full py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium rounded border border-slate-700 flex items-center justify-center space-x-1.5 transition"
          >
            <RotateCcw className="w-3.5 h-3.5 text-amber-400" />
            <span>Return to Home Pose</span>
          </button>
        </div>

        {/* Waypoints List */}
        <div className="flex-1 bg-slate-950/60 p-2.5 rounded border border-slate-800 space-y-2 overflow-y-auto">
          <div className="text-[10px] text-slate-400 uppercase font-semibold">Planned Waypoints</div>
          <div className="space-y-1 font-mono text-[11px]">
            <div className="p-1.5 bg-slate-900 rounded border border-slate-800/80 text-emerald-400">
              WP1: [0.0, -0.78, 1.57] (Home)
            </div>
            <div className="p-1.5 bg-slate-900 rounded border border-slate-800/80 text-sky-400">
              WP2: [0.45, 0.10, 0.25] (Grasp Approach)
            </div>
            <div className="p-1.5 bg-slate-900 rounded border border-slate-800/80 text-amber-400">
              WP3: [0.45, 0.10, 0.15] (Contact Closure)
            </div>
            <div className="p-1.5 bg-slate-900 rounded border border-slate-800/80 text-slate-300">
              WP4: [0.20, -0.35, 0.40] (Target Placement)
            </div>
          </div>
        </div>
      </div>

      {/* Central 3D Kinematics Viewport */}
      <div className="flex-1 relative">
        <Viewport3D />
      </div>

      {/* Right Contextual Inspector */}
      <div className="w-80 border-l border-slate-800">
        <ContextualInspector />
      </div>
    </div>
  );
};
