"""
MonkeyBots Centralized Robot Model Registry
Provides unified discovery and instantiation of all supported robotic models.
"""

from typing import Dict, List, Callable
from .robot import RobotModel
from .assets.sample_6dof_arm import create_sample_6dof_arm
from .assets.franka_panda import create_franka_panda
from .assets.ur5e_robot import create_ur5e_robot
from .assets.ur10e_robot import create_ur10e_robot
from .assets.delta_robot import create_delta_robot
from .assets.mobile_base import create_mobile_base
from .assets.robotiq_gripper import create_robotiq_2f85

ROBOT_REGISTRY: Dict[str, Callable[[], RobotModel]] = {
    "default_6dof_arm": create_sample_6dof_arm,
    "franka_panda": create_franka_panda,
    "ur5e": create_ur5e_robot,
    "ur10e": create_ur10e_robot,
    "delta_robot": create_delta_robot,
    "mobile_base": create_mobile_base,
    "robotiq_2f85": create_robotiq_2f85,
}


def list_available_robots() -> List[str]:
    """Returns all registered robot model keys."""
    return sorted(list(ROBOT_REGISTRY.keys()))


# Alias for backward-compatibility
list_registered_robots = list_available_robots


def get_robot_model(name: str) -> RobotModel:
    """Instantiates a robot model by registered name."""
    if name not in ROBOT_REGISTRY:
        raise KeyError(f"Robot model '{name}' not found. Available: {list_available_robots()}")
    return ROBOT_REGISTRY[name]()
