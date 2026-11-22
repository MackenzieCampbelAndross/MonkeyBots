import React from 'react';

export interface ChartZoomControlsProps {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetZoom: () => void;
  onExportSvg: () => void;
  onExportCsv: () => void;
}

export const ChartZoomControls: React.FC<ChartZoomControlsProps> = ({
  onZoomIn,
  onZoomOut,
  onResetZoom,
  onExportSvg,
  onExportCsv,
}) => {
  return (
    <div className="flex items-center space-x-1 text-xs">
      <button onClick={onZoomIn} className="px-2 py-0.5 bg-slate-800 rounded hover:bg-slate-700 text-slate-300">+</button>
      <button onClick={onZoomOut} className="px-2 py-0.5 bg-slate-800 rounded hover:bg-slate-700 text-slate-300">-</button>
      <button onClick={onResetZoom} className="px-2 py-0.5 bg-slate-800 rounded hover:bg-slate-700 text-slate-300">Reset</button>
      <button onClick={onExportSvg} className="px-2 py-0.5 bg-sky-900/60 rounded text-sky-400 hover:bg-sky-800">SVG</button>
      <button onClick={onExportCsv} className="px-2 py-0.5 bg-emerald-900/60 rounded text-emerald-400 hover:bg-emerald-800">CSV</button>
    </div>
  );
};
