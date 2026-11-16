"""
MonkeyBots Background Simulation Runner
Executes fixed-timestep physics stepping at 500 Hz in a high-resolution worker thread.
"""

import time
import threading
from typing import Optional, Callable
from .engine import SimulationEngine
from server.monkeybots_server.schemas.telemetry import TelemetryFrame
from server.monkeybots_server.utils.logger import get_logger

logger = get_logger("sim_runner")


class SimulationRunner:
    """Threaded runner that executes the 500 Hz physics loop and broadcasts 60 Hz telemetry."""

    def __init__(self, engine: SimulationEngine):
        self.engine = engine
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._telemetry_callback: Optional[Callable[[TelemetryFrame], None]] = None
        self.telemetry_hz = 60
        self.physics_hz = 500

    def set_telemetry_callback(self, cb: Callable[[TelemetryFrame], None]):
        self._telemetry_callback = cb

    def start(self):
        """Launches the background simulation thread."""
        if self._thread is not None and self._thread.is_alive():
            self._pause_event.clear()
            self.engine.resume()
            return

        self._stop_event.clear()
        self._pause_event.clear()
        self.engine.start()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="MuJoCoPhysicsThread")
        self._thread.start()
        logger.info("MuJoCo 500 Hz physics runner thread started.")

    def pause(self):
        """Pauses the physics loop."""
        self._pause_event.set()
        self.engine.pause()
        logger.info("MuJoCo physics loop paused.")

    def resume(self):
        """Resumes the physics loop."""
        self._pause_event.clear()
        self.engine.resume()
        logger.info("MuJoCo physics loop resumed.")

    def stop(self):
        """Terminates the physics thread."""
        self._stop_event.set()
        self._pause_event.clear()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None
        self.engine.stop()
        logger.info("MuJoCo physics runner thread stopped.")

    def _run_loop(self):
        """Main fixed-rate integration loop."""
        dt = self.engine.model.opt.timestep if self.engine.model else 0.002
        physics_period = dt
        decimation = max(1, int(self.physics_hz / self.telemetry_hz))
        step_counter = 0

        while not self._stop_event.is_set():
            if self._pause_event.is_set() or self.engine.status != "RUNNING":
                time.sleep(0.01)
                continue

            t_start = time.perf_counter()

            # Execute single physics step
            success = self.engine.step(1)
            if not success:
                logger.error("Physics step failed or diverged. Pausing runner.")
                self._pause_event.set()
                continue

            step_counter += 1

            # Telemetry decimation broadcast (~60 Hz)
            if step_counter % decimation == 0 and self._telemetry_callback:
                frame = self.engine.get_telemetry_frame()
                try:
                    self._telemetry_callback(frame)
                except Exception:
                    pass

            # Sleep to match simulation speed multiplier
            t_elapsed = time.perf_counter() - t_start
            effective_period = physics_period / max(0.1, self.engine.config.speed_multiplier)
            t_sleep = effective_period - t_elapsed
            if t_sleep > 0.0001:
                time.sleep(t_sleep)
