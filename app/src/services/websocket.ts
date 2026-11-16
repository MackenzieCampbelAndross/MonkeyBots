/**
 * MonkeyBots Real-Time WebSocket Manager
 * Manages 60 Hz telemetry streaming and command packet dispatch with auto-reconnection.
 */

import type { TelemetryFrame, ConnectionStatus } from "../types/api";

type TelemetryListener = (frame: TelemetryFrame) => void;
type StatusListener = (status: ConnectionStatus) => void;

class SimulationWebSocketClient {
  private ws: WebSocket | null = null;
  private url: string = "ws://127.0.0.1:8765/ws/simulation";
  private telemetryListeners: Set<TelemetryListener> = new Set();
  private statusListeners: Set<StatusListener> = new Set();
  private reconnectTimer: number | null = null;
  private status: ConnectionStatus = "DISCONNECTED";
  private shouldReconnect: boolean = true;
  private reconnectInterval: number = 2000;

  public connect(customUrl?: string) {
    if (customUrl) this.url = customUrl;
    this.shouldReconnect = true;
    this.initSocket();
  }

  private setStatus(newStatus: ConnectionStatus) {
    if (this.status !== newStatus) {
      this.status = newStatus;
      this.statusListeners.forEach((fn) => fn(newStatus));
    }
  }

  public getStatus(): ConnectionStatus {
    return this.status;
  }

  private initSocket() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.setStatus("CONNECTING");

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.setStatus("CONNECTED");
        if (this.reconnectTimer) {
          clearTimeout(this.reconnectTimer);
          this.reconnectTimer = null;
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "telemetry") {
            this.telemetryListeners.forEach((fn) => fn(data as TelemetryFrame));
          }
        } catch {
          // Ignore malformed packet
        }
      };

      this.ws.onclose = () => {
        this.setStatus("DISCONNECTED");
        this.scheduleReconnect();
      };

      this.ws.onerror = () => {
        this.setStatus("ERROR");
        this.ws?.close();
      };
    } catch {
      this.setStatus("ERROR");
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect() {
    if (!this.shouldReconnect || this.reconnectTimer) return;
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      if (this.shouldReconnect) {
        this.initSocket();
      }
    }, this.reconnectInterval);
  }

  public sendJointPositions(targets: number[], gripper?: number) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          type: "command",
          mode: "joint_position",
          targets,
          gripper,
        })
      );
    }
  }

  public sendSimControl(action: "START" | "PAUSE" | "RESET") {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          type: "control",
          action,
        })
      );
    }
  }

  public onTelemetry(listener: TelemetryListener): () => void {
    this.telemetryListeners.add(listener);
    return () => this.telemetryListeners.delete(listener);
  }

  public onStatus(listener: StatusListener): () => void {
    this.statusListeners.add(listener);
    listener(this.status);
    return () => this.statusListeners.delete(listener);
  }

  public disconnect() {
    this.shouldReconnect = false;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.setStatus("DISCONNECTED");
  }
}

export const simWebSocket = new SimulationWebSocketClient();
