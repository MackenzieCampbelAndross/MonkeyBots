import React from 'react';

export interface CollisionOverlayProps {
  showWireframe: boolean;
  onToggle: (show: boolean) => void;
}

export const CollisionOverlay: React.FC<CollisionOverlayProps> = ({
  showWireframe,
  onToggle,
}) => {
  return (
    <button
      onClick={() => onToggle(!showWireframe)}
      className={`px-2 py-1 text-xs rounded border font-mono transition-colors ${
        showWireframe
          ? 'bg-amber-950/80 text-amber-400 border-amber-800'
          : 'bg-slate-800 text-slate-400 border-slate-700'
      }`}
    >
      COLLISION HULLS: {showWireframe ? 'ON' : 'OFF'}
    </button>
  );
};
