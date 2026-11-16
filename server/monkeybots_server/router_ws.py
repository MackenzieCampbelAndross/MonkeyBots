"""
WebSocket Real-Time Simulation Gateway
Streams live 60 Hz physics telemetry from MuJoCo and receives real-time control packets.
"""

import asyncio
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from server.monkeybots_server.schemas.telemetry import TelemetryFrame
from server.monkeybots_server.schemas.commands import JointPositionCommand, SimControlAction
from server.monkeybots_server.router_simulation import live_engine
from server.monkeybots_server.utils.logger import get_logger

router = APIRouter(tags=["WebSocket Gateway"])
logger = get_logger("router_ws")

active_connections: Set[WebSocket] = set()


@router.websocket("/ws/simulation")
async def simulation_websocket_endpoint(websocket: WebSocket):
    """Real-time bi-directional telemetry and command streaming."""
    await websocket.accept()
    active_connections.add(websocket)
    client_ip = websocket.client.host if websocket.client else "unknown"
    logger.info(f"UI WebSocket client connected from {client_ip}. Active connections: {len(active_connections)}")

    telemetry_fps = 60
    telemetry_dt = 1.0 / telemetry_fps

    try:
        # Background task for stepping physics and broadcasting telemetry
        async def telemetry_loop():
            # If engine hasn't started yet, set it to RUNNING
            if live_engine.status in ("IDLE", "PAUSED"):
                live_engine.start()

            while True:
                t0 = asyncio.get_event_loop().time()

                # If running, step physics
                if live_engine.status == "RUNNING":
                    # Step 500 Hz physics within this 60 Hz frame (approx 8 steps of 0.002s = 0.016s)
                    dt = live_engine.config.timestep
                    steps_per_frame = max(1, int(telemetry_dt / dt))
                    live_engine.step(steps_per_frame)

                # Get exact state from MuJoCo
                frame: TelemetryFrame = live_engine.get_telemetry_frame()
                await websocket.send_text(frame.model_dump_json())

                elapsed = asyncio.get_event_loop().time() - t0
                sleep_time = max(0.001, telemetry_dt - elapsed)
                await asyncio.sleep(sleep_time)

        broadcaster_task = asyncio.create_task(telemetry_loop())

        # Main receiver loop for incoming commands
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "command":
                mode = data.get("mode")
                if mode == "joint_position":
                    cmd = JointPositionCommand.model_validate(data)
                    live_engine.set_target_joint_positions(cmd.targets)
                    logger.debug(f"Target joint positions applied: {cmd.targets}")

            elif msg_type == "control":
                ctrl = SimControlAction.model_validate(data)
                act = ctrl.action.upper()
                if act == "PAUSE":
                    live_engine.pause()
                elif act in ("START", "RESUME"):
                    live_engine.start()
                elif act == "RESET":
                    live_engine.reset()
                logger.info(f"Applied simulation control via WS: {act}")

    except WebSocketDisconnect:
        logger.info(f"UI WebSocket client disconnected ({client_ip}).")
    except Exception as e:
        logger.warning(f"WebSocket session terminated: {e}")
    finally:
        broadcaster_task.cancel()
        active_connections.discard(websocket)
        logger.info(f"Cleaned up WebSocket connection. Remaining: {len(active_connections)}")
