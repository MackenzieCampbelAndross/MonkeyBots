import React from 'react';

export interface CoordinateTriadsProps {
  visibleJoints: string[];
  axisLength?: number;
}

export const CoordinateTriads: React.FC<CoordinateTriadsProps> = ({
  visibleJoints,
  axisLength: _axisLength = 0.08,
}) => {
  return (
    <div className="absolute top-24 left-4 bg-slate-900/80 border border-slate-800 rounded px-2 py-1 text-[11px] font-mono text-slate-400">
      TRIADS: {visibleJoints.length} ACTIVE (RGB=XYZ)
    </div>
  );
};
