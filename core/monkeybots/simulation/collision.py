"""
MonkeyBots Collision Detection and Contact Physics System
Identifies active contact manifolds, computes normal and tangential friction forces,
categorizes contact types, and logs dynamic collision events and impulses.
"""

from enum import Enum
from typing import List, Dict, Optional, Set, Tuple
import numpy as np
from pydantic import BaseModel, Field

try:
    import mujoco
    MUJOCO_INSTALLED = True
except ImportError:
    MUJOCO_INSTALLED = False


class ContactCategory(str, Enum):
    SELF_COLLISION = "robot_self"
    ROBOT_ENVIRONMENT = "robot_env"
    ROBOT_OBJECT = "robot_object"
    OBJECT_ENVIRONMENT = "object_env"
    OBJECT_OBJECT = "object_object"
    UNKNOWN = "unknown"


class ContactPointData(BaseModel):
    """Full kinematic and kinetic profile of an active contact manifold."""
    geom1: str
    geom2: str
    body1: str
    body2: str
    category: ContactCategory
    position: List[float] = Field(..., description="Contact coordinates [x, y, z] in world frame")
    normal: List[float] = Field(..., description="Unit normal vector pointing from geom1 to geom2")
    distance: float = Field(..., description="Penetration depth (negative) or separation distance (positive)")
    normal_force: float = Field(..., description="Magnitude of normal contact force (N)")
    friction_force: float = Field(..., description="Resultant tangential friction force (N)")
    friction_limit: float = Field(..., description="Maximum static Coulomb friction force (mu * Fn)")
    slip_state: str = Field(..., description="'sticking', 'slipping', or 'no_contact'")


class CollisionEvent(BaseModel):
    """Discrete impact or contact state transition event."""
    timestamp: float
    event_type: str = Field(..., description="'onset', 'impact', 'sustained', or 'separation'")
    geom1: str
    geom2: str
    body1: str
    body2: str
    category: ContactCategory
    normal_force: float
    friction_force: float
    impulse: float = Field(default=0.0, description="Cumulative impulse (N*s)")
    position: List[float]
    normal: List[float]


class CollisionTracker:
    """
    Real-time collision monitor and contact dynamics analyzer.
    Extracts contact geometry and wrenches from MuJoCo, categorizes contact pairs,
    and maintains a time-stamped collision log.
    """

    def __init__(self, max_history: int = 500):
        self.max_history = max_history
        self.collision_events: List[CollisionEvent] = []
        self._active_contacts: Dict[Tuple[int, int], float] = {}  # (g1, g2) -> impulse accumulator
        self._last_active_keys: Set[Tuple[int, int]] = set()

    def clear(self):
        self.collision_events.clear()
        self._active_contacts.clear()
        self._last_active_keys.clear()

    def categorize_pair(self, body1: str, body2: str, geom1: str, geom2: str) -> ContactCategory:
        """Classifies contact pair by structural role."""
        names = (body1.lower() + " " + geom1.lower(), body2.lower() + " " + geom2.lower())

        is_robot_0 = any(k in names[0] for k in ("link", "base", "finger", "gripper", "flange", "wrist", "arm"))
        is_robot_1 = any(k in names[1] for k in ("link", "base", "finger", "gripper", "flange", "wrist", "arm"))

        is_obj_0 = any(k in names[0] for k in ("box", "part", "object", "item", "cylinder_obj", "target"))
        is_obj_1 = any(k in names[1] for k in ("box", "part", "object", "item", "cylinder_obj", "target"))

        is_env_0 = any(k in names[0] for k in ("floor", "table", "ground", "wall", "obstacle", "pillar", "pedestal", "workbench"))
        is_env_1 = any(k in names[1] for k in ("floor", "table", "ground", "wall", "obstacle", "pillar", "pedestal", "workbench"))

        if is_robot_0 and is_robot_1:
            return ContactCategory.SELF_COLLISION
        if (is_robot_0 and is_obj_1) or (is_robot_1 and is_obj_0):
            return ContactCategory.ROBOT_OBJECT
        if (is_robot_0 and is_env_1) or (is_robot_1 and is_env_0):
            return ContactCategory.ROBOT_ENVIRONMENT
        if (is_obj_0 and is_env_1) or (is_obj_1 and is_env_0):
            return ContactCategory.OBJECT_ENVIRONMENT
        if is_obj_0 and is_obj_1:
            return ContactCategory.OBJECT_OBJECT

        return ContactCategory.UNKNOWN

    def update(
        self,
        model: "mujoco.MjModel",
        data: "mujoco.MjData",
        sim_time: float,
        dt: float,
    ) -> List[ContactPointData]:
        """
        Parses active contacts from MuJoCo data structures.
        Computes exact 6D contact wrench, friction limits, and registers collision events.
        """
        if not MUJOCO_INSTALLED or model is None or data is None:
            return []

        active_contacts: List[ContactPointData] = []
        current_keys: Set[Tuple[int, int]] = set()

        ncon = data.ncon
        for i in range(ncon):
            con = data.contact[i]
            g1_id = con.geom1
            g2_id = con.geom2
            key = (min(g1_id, g2_id), max(g1_id, g2_id))
            current_keys.add(key)

            # Resolve names
            g1_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, g1_id) or f"geom_{g1_id}"
            g2_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, g2_id) or f"geom_{g2_id}"

            b1_id = model.geom_bodyid[g1_id]
            b2_id = model.geom_bodyid[g2_id]
            b1_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, b1_id) or f"body_{b1_id}"
            b2_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, b2_id) or f"body_{b2_id}"

            category = self.categorize_pair(b1_name, b2_name, g1_name, g2_name)

            # Extract 6D contact force: [Fn, Ft1, Ft2, ...]
            c_force = np.zeros(6, dtype=np.float64)
            mujoco.mj_contactForce(model, data, i, c_force)

            normal_force = float(abs(c_force[0]))
            friction_force = float(np.sqrt(c_force[1] ** 2 + c_force[2] ** 2))

            # Friction coefficient (effective mu between geom1 and geom2)
            mu1 = model.geom_friction[g1_id][0]
            mu2 = model.geom_friction[g2_id][0]
            mu_eff = 0.5 * (mu1 + mu2)
            friction_limit = mu_eff * normal_force

            # Slip assessment
            if normal_force < 1e-4:
                slip_state = "no_contact"
            elif friction_force >= (friction_limit - 1e-3) and friction_force > 0.01:
                slip_state = "slipping"
            else:
                slip_state = "sticking"

            # World-frame contact normal (first 3 entries of 3x3 contact frame)
            normal_vec = [float(con.frame[0]), float(con.frame[1]), float(con.frame[2])]
            pos_vec = [float(con.pos[0]), float(con.pos[1]), float(con.pos[2])]
            dist = float(con.dist)

            contact_data = ContactPointData(
                geom1=g1_name,
                geom2=g2_name,
                body1=b1_name,
                body2=b2_name,
                category=category,
                position=[round(p, 4) for p in pos_vec],
                normal=[round(n, 4) for n in normal_vec],
                distance=round(dist, 5),
                normal_force=round(normal_force, 3),
                friction_force=round(friction_force, 3),
                friction_limit=round(friction_limit, 3),
                slip_state=slip_state,
            )
            active_contacts.append(contact_data)

            # Accumulate impulse J = integral(Fn * dt)
            prev_impulse = self._active_contacts.get(key, 0.0)
            cur_impulse = prev_impulse + normal_force * dt
            self._active_contacts[key] = cur_impulse

            # Check for onset or impact
            is_new = key not in self._last_active_keys
            if is_new or (normal_force > 25.0 and prev_impulse < 1e-3):
                ev_type = "impact" if normal_force > 20.0 else "onset"
                self._record_event(
                    timestamp=sim_time,
                    event_type=ev_type,
                    geom1=g1_name,
                    geom2=g2_name,
                    body1=b1_name,
                    body2=b2_name,
                    category=category,
                    normal_force=normal_force,
                    friction_force=friction_force,
                    impulse=cur_impulse,
                    position=pos_vec,
                    normal=normal_vec,
                )

        # Detect separations
        separated_keys = self._last_active_keys - current_keys
        for k in separated_keys:
            if k in self._active_contacts:
                del self._active_contacts[k]

        self._last_active_keys = current_keys
        return active_contacts

    def _record_event(
        self,
        timestamp: float,
        event_type: str,
        geom1: str,
        geom2: str,
        body1: str,
        body2: str,
        category: ContactCategory,
        normal_force: float,
        friction_force: float,
        impulse: float,
        position: List[float],
        normal: List[float],
    ):
        event = CollisionEvent(
            timestamp=round(timestamp, 4),
            event_type=event_type,
            geom1=geom1,
            geom2=geom2,
            body1=body1,
            body2=body2,
            category=category,
            normal_force=round(normal_force, 3),
            friction_force=round(friction_force, 3),
            impulse=round(impulse, 4),
            position=[round(p, 4) for p in position],
            normal=[round(n, 4) for n in normal],
        )
        self.collision_events.append(event)
        if len(self.collision_events) > self.max_history:
            self.collision_events.pop(0)

    def get_events(
        self,
        limit: int = 50,
        category: Optional[ContactCategory] = None,
    ) -> List[CollisionEvent]:
        events = self.collision_events
        if category:
            events = [e for e in events if e.category == category]
        return events[-limit:]
