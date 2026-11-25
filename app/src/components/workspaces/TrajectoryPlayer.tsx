import React, { useState, useEffect } from 'react';
import { Play, Pause, RotateCcw, FastForward } from 'lucide-react';

export interface TrajectoryPlayerProps {
  durationS: number;
  totalWaypoints: number;
  onTimeUpdate?: (t: number) => void;
}

export const TrajectoryPlayer: React.FC<TrajectoryPlayerProps> = ({
  durationS,
  totalWaypoints,
  onTimeUpdate,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0);

  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => {
        setProgress((prev) => {
          const next = prev + (0.05 * playbackSpeed) / durationS;
          if (next >= 1.0) {
            setIsPlaying(false);
            return 1.0;
          }
          if (onTimeUpdate) onTimeUpdate(next * durationS);
          return next;
        });
      }, 50);
    }
    return () => clearInterval(interval);
  }, [isPlaying, playbackSpeed, durationS, onTimeUpdate]);

  const handleReset = () => {
    setIsPlaying(false);
    setProgress(0);
    if (onTimeUpdate) onTimeUpdate(0);
  };

  return (
    <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 space-y-2 font-sans">
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-slate-400 font-semibold uppercase">Trajectory Playback</span>
        <span className="text-xs font-mono text-sky-400">
          {(progress * durationS).toFixed(2)}s / {durationS.toFixed(2)}s
        </span>
      </div>

      <input
        type="range"
        min={0}
        max={1}
        step={0.005}
        value={progress}
        onChange={(e) => {
          const val = parseFloat(e.target.value);
          setProgress(val);
          if (onTimeUpdate) onTimeUpdate(val * durationS);
        }}
        className="w-full accent-sky-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg"
      />

      <div className="flex items-center justify-between text-xs pt-1">
        <div className="flex items-center space-x-1.5">
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="p-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded transition flex items-center space-x-1"
          >
            {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={handleReset}
            className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded transition"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="flex items-center space-x-1 text-[10px] font-mono text-slate-400">
          <FastForward className="w-3 h-3 text-slate-500" />
          {[0.5, 1.0, 2.0].map((spd) => (
            <button
              key={spd}
              onClick={() => setPlaybackSpeed(spd)}
              className={`px-1.5 py-0.5 rounded ${playbackSpeed === spd ? 'bg-sky-500/20 text-sky-300 font-bold' : 'text-slate-500 hover:text-slate-300'}`}
            >
              {spd}x
            </button>
          ))}
          <span className="text-slate-600 pl-1">({totalWaypoints} pts)</span>
        </div>
      </div>
    </div>
  );
};
