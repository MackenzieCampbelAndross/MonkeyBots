import React from "react";
import { useAppStore } from "../store/useAppStore";
import { simWebSocket } from "../services/websocket";
import { AlertCircle, RefreshCw, X } from "lucide-react";

export const ErrorBanner: React.FC = () => {
  const { lastError, setLastError, connectionStatus } = useAppStore();

  if (!lastError && connectionStatus !== "DISCONNECTED" && connectionStatus !== "ERROR") {
    return null;
  }

  const message =
    lastError ||
    (connectionStatus === "DISCONNECTED"
      ? "Backend connection lost. Ensure the Python FastAPI daemon is running on port 8765."
      : "Connection error encountered communicating with the robotics engine.");

  const handleRetry = () => {
    setLastError(null);
    simWebSocket.connect();
  };

  return (
    <div className="bg-rose-950/90 border-b border-rose-500/50 px-4 py-2 flex items-center justify-between text-xs text-rose-200 backdrop-blur z-20">
      <div className="flex items-center space-x-2">
        <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
        <span className="font-medium">{message}</span>
      </div>

      <div className="flex items-center space-x-3">
        <button
          onClick={handleRetry}
          className="flex items-center space-x-1 px-2.5 py-1 bg-rose-900/60 hover:bg-rose-800/80 rounded border border-rose-500/40 text-[11px] font-semibold transition"
        >
          <RefreshCw className="w-3 h-3" />
          <span>RECONNECT</span>
        </button>

        {lastError && (
          <button
            onClick={() => setLastError(null)}
            className="text-rose-400 hover:text-rose-200 transition"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};
