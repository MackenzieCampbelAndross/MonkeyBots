import React from 'react';

export interface TransformGizmoProps {
  mode: 'translate' | 'rotate';
  position: [number, number, number];
  orientation: [number, number, number, number];
  snapStepMm?: number;
  snapStepDeg?: number;
  onTransformChange?: (pos: [number, number, number], rot: [number, number, number, number]) => void;
}

export const TransformGizmo: React.FC<TransformGizmoProps> = ({
  mode,
  position,
  orientation,
  snapStepMm = 10,
  snapStepDeg = 5,
  onTransformChange,
}) => {
  return (
    <div className="absolute bottom-4 right-4 bg-slate-900/90 border border-slate-700 rounded p-2 text-xs text-slate-300 font-mono shadow-lg">
      <div className="flex items-center space-x-2 border-b border-slate-800 pb-1 mb-1">
        <span className="font-bold text-sky-400">GIZMO [{mode.toUpperCase()}]</span>
        <span className="text-[10px] text-slate-500">SNAP: {mode === 'translate' ? `${snapStepMm}mm` : `${snapStepDeg}°`}</span>
      </div>
      <div>XYZ: {position.map((v) => v.toFixed(3)).join(', ')}</div>
    </div>
  );
};
