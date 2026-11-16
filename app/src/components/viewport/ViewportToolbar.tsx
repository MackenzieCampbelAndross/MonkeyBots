/**
 * MonkeyBots 3D Viewport Engineering Toolbar
 */

import React, { useState } from "react";
import {
  Eye,
  Grid,
  Box,
  Compass,
  Sun,
  Camera,
  Plus,
  Sliders,
} from "lucide-react";

interface ViewportToolbarProps {
  onCameraPreset: (preset: "iso" | "front" | "top" | "side") => void;
  isOrthographic: boolean;
  onToggleProjection: () => void;
  showGrid: boolean;
  onToggleGrid: () => void;
  showFrames: boolean;
  onToggleFrames: () => void;
  showCollisions: boolean;
  onToggleCollisions: () => void;
  showJointAxes: boolean;
  onToggleJointAxes: () => void;
  showShadows: boolean;
  onToggleShadows: () => void;
  shadingMode: "solid" | "wireframe" | "xray";
  onChangeShading: (mode: "solid" | "wireframe" | "xray") => void;
  onAddObstacle: (type: "table" | "box" | "cylinder" | "target") => void;
}

export const ViewportToolbar: React.FC<ViewportToolbarProps> = ({
  onCameraPreset,
  isOrthographic,
  onToggleProjection,
  showGrid,
  onToggleGrid,
  showFrames,
  onToggleFrames,
  showCollisions,
  onToggleCollisions,
  showJointAxes,
  onToggleJointAxes,
  showShadows,
  onToggleShadows,
  shadingMode,
  onChangeShading,
  onAddObstacle,
}) => {
  const [showEnvMenu, setShowEnvMenu] = useState<boolean>(false);
  const [showShadingMenu, setShowShadingMenu] = useState<boolean>(false);

  return (
    <div className="absolute top-3 left-3 z-10 flex items-center space-x-1.5 bg-slate-900/90 backdrop-blur-md p-1 rounded-lg border border-slate-800 text-xs text-slate-300 shadow-xl select-none">
      {/* Camera Presets */}
      <div className="flex items-center space-x-0.5 border-r border-slate-800 pr-1.5">
        {(["iso", "front", "top", "side"] as const).map((preset) => (
          <button
            key={preset}
            onClick={() => onCameraPreset(preset)}
            className="px-2 py-1 rounded hover:bg-slate-800 hover:text-white transition font-mono uppercase text-[10px]"
          >
            {preset}
          </button>
        ))}
      </div>

      {/* Perspective / Orthographic Toggle */}
      <button
        onClick={onToggleProjection}
        title={isOrthographic ? "Switch to Perspective Projection" : "Switch to Orthographic Projection"}
        className={`px-2 py-1 rounded text-[10px] font-mono flex items-center space-x-1 transition ${
          isOrthographic ? "bg-amber-500/20 text-amber-400 border border-amber-600/40" : "hover:bg-slate-800"
        }`}
      >
        <Camera className="w-3 h-3" />
        <span>{isOrthographic ? "ORTHO" : "PERSP"}</span>
      </button>

      {/* Shading Mode Dropdown */}
      <div className="relative">
        <button
          onClick={() => setShowShadingMenu(!showShadingMenu)}
          className="px-2 py-1 rounded hover:bg-slate-800 flex items-center space-x-1 text-[10px] uppercase font-mono"
        >
          <Sliders className="w-3 h-3 text-sky-400" />
          <span>{shadingMode}</span>
        </button>

        {showShadingMenu && (
          <div className="absolute top-full left-0 mt-1 w-28 bg-slate-900 border border-slate-800 rounded shadow-xl py-1 z-20 font-mono text-[10px]">
            {(["solid", "wireframe", "xray"] as const).map((m) => (
              <button
                key={m}
                onClick={() => {
                  onChangeShading(m);
                  setShowShadingMenu(false);
                }}
                className={`w-full text-left px-2.5 py-1 hover:bg-slate-800 uppercase ${
                  shadingMode === m ? "text-amber-400 font-bold" : "text-slate-300"
                }`}
              >
                {m}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Visibility Toggles */}
      <div className="flex items-center space-x-0.5 border-l border-r border-slate-800 px-1.5">
        <button
          onClick={onToggleGrid}
          title="Toggle Grid"
          className={`p-1 rounded ${showGrid ? "text-sky-400 bg-sky-950/40" : "text-slate-500 hover:text-slate-300"}`}
        >
          <Grid className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={onToggleFrames}
          title="Toggle Coordinate Frames (RGB Triads)"
          className={`p-1 rounded ${showFrames ? "text-emerald-400 bg-emerald-950/40" : "text-slate-500 hover:text-slate-300"}`}
        >
          <Compass className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={onToggleCollisions}
          title="Toggle Collision Geometry (Orange Hulls)"
          className={`p-1 rounded ${showCollisions ? "text-amber-400 bg-amber-950/40" : "text-slate-500 hover:text-slate-300"}`}
        >
          <Box className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={onToggleJointAxes}
          title="Toggle Joint Rotation Direction Rings"
          className={`p-1 rounded ${showJointAxes ? "text-purple-400 bg-purple-950/40" : "text-slate-500 hover:text-slate-300"}`}
        >
          <Eye className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={onToggleShadows}
          title="Toggle Real-Time Shadows"
          className={`p-1 rounded ${showShadows ? "text-amber-300 bg-amber-950/40" : "text-slate-500 hover:text-slate-300"}`}
        >
          <Sun className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Add Environment Object Menu */}
      <div className="relative">
        <button
          onClick={() => setShowEnvMenu(!showEnvMenu)}
          className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-sky-300 rounded flex items-center space-x-1 text-[10px] font-semibold transition"
        >
          <Plus className="w-3 h-3" />
          <span>Add Object</span>
        </button>

        {showEnvMenu && (
          <div className="absolute top-full left-0 mt-1 w-36 bg-slate-900 border border-slate-800 rounded shadow-2xl py-1 z-20 font-sans text-[11px]">
            <button
              onClick={() => {
                onAddObstacle("table");
                setShowEnvMenu(false);
              }}
              className="w-full text-left px-2.5 py-1.5 hover:bg-slate-800 text-slate-200"
            >
              + Work Table
            </button>
            <button
              onClick={() => {
                onAddObstacle("box");
                setShowEnvMenu(false);
              }}
              className="w-full text-left px-2.5 py-1.5 hover:bg-slate-800 text-slate-200"
            >
              + Box Obstacle
            </button>
            <button
              onClick={() => {
                onAddObstacle("cylinder");
                setShowEnvMenu(false);
              }}
              className="w-full text-left px-2.5 py-1.5 hover:bg-slate-800 text-slate-200"
            >
              + Cylinder Obstacle
            </button>
            <button
              onClick={() => {
                onAddObstacle("target");
                setShowEnvMenu(false);
              }}
              className="w-full text-left px-2.5 py-1.5 hover:bg-slate-800 text-slate-200"
            >
              + Target Marker
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
