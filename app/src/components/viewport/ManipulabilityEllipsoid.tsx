import React from 'react';

export interface ManipulabilityEllipsoidProps {
  visible: boolean;
  radii?: [number, number, number];
  volume?: number;
  isSingular?: boolean;
}

export const ManipulabilityEllipsoid: React.FC<ManipulabilityEllipsoidProps> = ({
  visible,
  radii = [0.1, 0.1, 0.1],
  volume = 0.001,
  isSingular = false,
}) => {
  if (!visible) return null;

  return (
    <div className="absolute top-36 left-4 bg-slate-900/90 border border-slate-800 rounded px-2.5 py-1.5 text-[11px] font-mono shadow-md">
      <div className="flex items-center space-x-2">
        <span className={`w-2 h-2 rounded-full ${isSingular ? 'bg-rose-500 animate-pulse' : 'bg-emerald-400'}`} />
        <span className="text-slate-300 font-semibold uppercase">3D SVD Ellipsoid</span>
      </div>
      <div className="text-[10px] text-slate-400 mt-1">
        Radii: [{radii.map((r) => r.toFixed(2)).join(', ')}]
      </div>
      <div className="text-[10px] text-sky-400 font-bold">
        Vol: {volume.toFixed(5)} m&sup3;
      </div>
    </div>
  );
};
