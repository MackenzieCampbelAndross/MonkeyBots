import React from 'react';

export type CameraPreset = 'TOP' | 'FRONT' | 'SIDE' | 'ISOMETRIC' | 'FOLLOW';

export interface CameraPresetsProps {
  currentPreset: CameraPreset;
  onSelectPreset: (preset: CameraPreset) => void;
}

export const CameraPresets: React.FC<CameraPresetsProps> = ({
  currentPreset,
  onSelectPreset,
}) => {
  const presets: CameraPreset[] = ['TOP', 'FRONT', 'SIDE', 'ISOMETRIC', 'FOLLOW'];
  return (
    <div className="flex space-x-1 bg-slate-900/90 border border-slate-800 rounded p-1">
      {presets.map((p) => (
        <button
          key={p}
          onClick={() => onSelectPreset(p)}
          className={`px-2 py-0.5 text-[10px] font-mono rounded ${
            currentPreset === p
              ? 'bg-sky-600 text-white font-bold'
              : 'text-slate-400 hover:bg-slate-800'
          }`}
        >
          {p}
        </button>
      ))}
    </div>
  );
};
