import React from 'react';

export interface TrajectoryRibbonProps {
  historyPoints: Array<{ pos: [number, number, number]; velocity: number }>;
  maxPoints?: number;
  ribbonWidth?: number;
}

export const TrajectoryRibbon: React.FC<TrajectoryRibbonProps> = ({
  historyPoints,
  maxPoints = 250,
  ribbonWidth: _ribbonWidth = 0.008,
}) => {
  return (
    <div className="absolute top-14 left-4 bg-slate-900/80 border border-slate-800 rounded px-2 py-1 text-[11px] font-mono text-slate-400">
      TRAIL POINTS: {Math.min(historyPoints.length, maxPoints)} / {maxPoints}
    </div>
  );
};
