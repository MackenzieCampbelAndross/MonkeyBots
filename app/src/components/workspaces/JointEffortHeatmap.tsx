import React from 'react';

export interface JointEffortHeatmapProps {
  effortsNm: number[];
  maxEffortsNm?: number[];
}

export const JointEffortHeatmap: React.FC<JointEffortHeatmapProps> = ({
  effortsNm,
  maxEffortsNm = [150, 150, 150, 28, 28, 28],
}) => {
  return (
    <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 space-y-2 font-sans">
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-slate-400 font-semibold uppercase">Actuator Torque Load</span>
        <span className="text-[10px] text-emerald-400 font-mono font-bold">NOMINAL THERMALS</span>
      </div>

      <div className="space-y-1.5 font-mono text-[10px]">
        {effortsNm.map((val, idx) => {
          const maxE = maxEffortsNm[idx] || 100;
          const ratio = Math.min(Math.abs(val) / maxE, 1.0);
          const pct = (ratio * 100).toFixed(0);
          const barColor = ratio > 0.85 ? 'bg-rose-500' : ratio > 0.65 ? 'bg-amber-400' : 'bg-emerald-500';

          return (
            <div key={idx} className="space-y-0.5">
              <div className="flex justify-between text-slate-400">
                <span>Joint {idx + 1}</span>
                <span>{Math.abs(val).toFixed(1)} / {maxE} Nm ({pct}%)</span>
              </div>
              <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                <div
                  className={`h-full ${barColor} transition-all duration-300`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
