import React from 'react';

export interface CenterOfMassMarkerProps {
  comPosition: [number, number, number];
  totalMassKg: number;
}

export const CenterOfMassMarker: React.FC<CenterOfMassMarkerProps> = ({
  comPosition,
  totalMassKg,
}) => {
  return (
    <div className="absolute bottom-4 left-4 bg-slate-900/80 border border-slate-800 rounded px-2 py-1 text-[11px] font-mono text-slate-300">
      CoM: [{comPosition.map((v) => v.toFixed(3)).join(', ')}] ({totalMassKg.toFixed(2)} kg)
    </div>
  );
};
