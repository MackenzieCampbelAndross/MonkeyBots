import React from 'react';

export interface KeyboardShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const KeyboardShortcutsModal: React.FC<KeyboardShortcutsModalProps> = ({
  isOpen,
  onClose,
}) => {
  if (!isOpen) return null;
  const shortcuts = [
    { key: 'Space', desc: 'Toggle Simulation Play/Pause' },
    { key: 'R', desc: 'Reset Simulation & State' },
    { key: 'G', desc: 'Toggle Ground Reference Grid' },
    { key: '1 - 8', desc: 'Switch CAD Workspace Tabs' },
    { key: 'Esc', desc: 'Deselect / Close Modal' },
  ];
  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-slate-900 border border-slate-700 rounded-lg p-5 w-96 shadow-2xl">
        <h3 className="text-sm font-bold text-white mb-3 flex justify-between">
          <span>KEYBOARD SHORTCUTS</span>
          <button onClick={onClose} className="text-slate-400 hover:text-white">&times;</button>
        </h3>
        <div className="space-y-2">
          {shortcuts.map((s) => (
            <div key={s.key} className="flex justify-between text-xs py-1 border-b border-slate-800">
              <span className="font-mono bg-slate-800 px-1.5 py-0.5 rounded text-sky-400">{s.key}</span>
              <span className="text-slate-300">{s.desc}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
