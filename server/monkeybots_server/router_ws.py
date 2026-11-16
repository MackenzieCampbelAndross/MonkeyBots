"""
WebSocket Real-Time Simulation Gateway
Streams 60 Hz telemetry to UI and accepts real-time control packets.
"""

import math
import time
import asyncio
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from server.monkeybots_server.schemas.telemetry import TelemetryFrame, Pose3D, ContactInfo
from server.monkeybots_server.schemas.commands import JointPositionCommand, SimControlAction
from server.monkeybots_server.utils.logger import get_logger

router = APIRouter(tags=["WebSocket Gateway"])
logger = get_logger("router_ws")

# Connected UI clients
active_connections: Set[WebSocket] = set()

# Shared simulation jog state for Stage 02 demonstration
joint_positions = [0.0, -0.785398, 1.570796, 0.0, 0.785398, 0.0]
sim_status = "RUNNING"


@router.websocket("/ws/simulation")
async def simulation_websocket_endpoint(websocket: WebSocket):
    """Real-time bi-directional telemetry and command streaming."""
    await websocket.accept()
    active_connections.add(websocket)
    client_ip = websocket.client.host if websocket.client else "unknown"
    logger.info(f"UI WebSocket client connected from {client_ip}. Active connections: {len(active_connections)}")

    # Start independent streaming loop for this client
    sim_time = 0.0
    step_count = 0
    dt = 1.0 / 60.0  # 60 FPS telemetry

    try:
        # Background task for sending telemetry
        async def telemetry_broadcaster():
            nonlocal sim_time, step_count
            while True:
                if sim_status == "RUNNING":
                    sim_time += dt
                    step_count += 1

                # Calculate smooth forward kinematics end-effector demo pose
                # (Demonstrating continuous 60Hz state stream)
                t = sim_time
                ee_x = 0.45 + 0.05 * math.cos(t * 0.8)
                ee_y = 0.05 * math.sin(t * 0.8)
                ee_z = 0.55 + 0.03 * math.sin(t * 1.6)

                frame = TelemetryFrame(
                    sim_time=round(sim_time, 4),
                    real_time_factor=1.0,
                    step_count=step_count,
                    joint_names=[f"joint_{i+1}" for i in range(6)],
                    qpos=[round(q, 4) for q in joint_positions],
                    qvel=[round(0.02 * math.cos(t + i), 4) for i in range(6)],
                    qtorque=[round(15.0 * math.sin(t + i * 0.5), 2) for i in range(6)],
                    end_effector=Pose3D(
                        position=[round(ee_x, 4), round(ee_y, 4), round(ee_z, 4)],
                        quaternion=[1.0, 0.0, 0.0, 0.0],
                    ),
                    contacts=[],
                    status=sim_status,
                )

                await websocket.send_text(frame.model_dump_json())
                await asyncio.sleep(dt)

        broadcaster_task = asyncio.create_task(telemetry_broadcaster())

        # Main receiver loop for incoming commands
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "command":
                mode = data.get("mode")
                if mode == "joint_position":
                    cmd = JointPositionCommand.model_validate(data)
                    for i, val in enumerate(cmd.targets[:6]):
                        joint_positions[i] = val
                    logger.debug(f"Applied joint position command: {joint_positions}")

            elif msg_type == "control":
                ctrl = SimControlAction.model_validate(data)
                global sim_status
                if ctrl.action == "PAUSE":
                    sim_status = "PAUSED"
                elif ctrl.action in ("START", "RESET"):
                    sim_status = "RUNNING"
                logger.info(f"Applied simulation control via WS: {ctrl.action}")

    except WebSocketDisconnect:
        logger.info(f"UI WebSocket client disconnected ({client_ip}).")
    except Exception as e:
        logger.warning(f"WebSocket session terminated: {e}")
    finally:
        broadcaster_task.cancel()
        active_connections.discard(websocket)
        logger.info(f"Cleaned up WebSocket connection. Remaining: {len(active_connections)}")
