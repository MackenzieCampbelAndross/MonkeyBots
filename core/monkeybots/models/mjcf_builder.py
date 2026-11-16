"""
MonkeyBots MJCF Builder and MuJoCo Engine Compiler
Converts RobotModel into native DeepMind MuJoCo XML (MJCF) and verifies engine compilation.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Tuple, Dict
from .robot import RobotModel, JointType, GeometryType

try:
    import mujoco
    MUJOCO_INSTALLED = True
except ImportError:
    MUJOCO_INSTALLED = False


def export_mjcf(model: RobotModel) -> str:
    """
    Exports RobotModel to native MuJoCo XML (MJCF).
    Constructs nested <body> elements matching the kinematic tree,
    attaching inertial elements, geoms, and actuators.
    """
    root = ET.Element("mujoco", model=model.name)

    # Compiler & Defaults
    ET.SubElement(root, "compiler", angle="radian", coordinate="local", inertiafromgeom="false")
    ET.SubElement(root, "option", timestep="0.002", gravity="0 0 -9.81", integrator="RK4")

    default = ET.SubElement(root, "default")
    ET.SubElement(default, "joint", damping="0.5", armature="0.02")
    ET.SubElement(default, "geom", friction="0.8 0.1 0.1", margin="0.001")

    # Worldbody
    worldbody = ET.SubElement(root, "worldbody")
    ET.SubElement(worldbody, "light", directional="true", diffuse="0.8 0.8 0.8", pos="0 0 3", dir="0 0 -1")
    ET.SubElement(worldbody, "geom", name="floor", type="plane", size="5 5 0.1", rgba="0.15 0.18 0.25 1")

    # Build Nested Kinematic Tree
    # Map each link to its children
    children_map: Dict[str, list] = {}
    for j in model.joints.values():
        children_map.setdefault(j.parent, []).append(j)

    def _build_body_recursive(parent_elem: ET.Element, link_name: str, incoming_joint=None):
        link = model.links.get(link_name)
        if not link:
            return

        body_elem = ET.SubElement(parent_elem, "body", name=link_name)

        if incoming_joint is not None:
            # Set relative transform from joint origin
            body_elem.set("pos", f"{incoming_joint.origin.xyz[0]} {incoming_joint.origin.xyz[1]} {incoming_joint.origin.xyz[2]}")

            # Define Joint in body
            j_type = "hinge" if incoming_joint.type in (JointType.REVOLUTE, JointType.CONTINUOUS) else "slide" if incoming_joint.type == JointType.PRISMATIC else None
            if j_type:
                j_elem = ET.SubElement(
                    body_elem,
                    "joint",
                    name=incoming_joint.name,
                    type=j_type,
                    axis=f"{incoming_joint.axis[0]} {incoming_joint.axis[1]} {incoming_joint.axis[2]}",
                )
                if incoming_joint.limits and incoming_joint.type == JointType.REVOLUTE:
                    j_elem.set("range", f"{incoming_joint.limits.lower} {incoming_joint.limits.upper}")
                if incoming_joint.dynamics:
                    j_elem.set("damping", str(incoming_joint.dynamics.damping))
                    j_elem.set("frictionloss", str(incoming_joint.dynamics.friction))
                    j_elem.set("armature", str(incoming_joint.dynamics.armature))
        else:
            body_elem.set("pos", "0 0 0")

        # Inertial
        if link.inertial:
            ine = link.inertial
            ine_elem = ET.SubElement(
                body_elem,
                "inertial",
                pos=f"{ine.origin.xyz[0]} {ine.origin.xyz[1]} {ine.origin.xyz[2]}",
                mass=str(ine.mass),
            )
            # Full inertia tensor
            it = ine.inertia
            ine_elem.set("fullinertia", f"{it.ixx} {it.iyy} {it.izz} {it.ixy} {it.ixz} {it.iyz}")

        # Geoms (from visuals/collisions)
        if link.visuals:
            for i, vis in enumerate(link.visuals):
                _serialize_mjcf_geom(body_elem, f"{link_name}_vis_{i}", vis.geometry, vis.origin, is_visual=True)
        elif link.collisions:
            for i, col in enumerate(link.collisions):
                _serialize_mjcf_geom(body_elem, f"{link_name}_col_{i}", col.geometry, col.origin, is_visual=False)
        else:
            # Add small default geometry for visualization
            ET.SubElement(body_elem, "geom", name=f"{link_name}_geom", type="sphere", size="0.04", rgba="0.8 0.6 0.2 1")

        # Recurse children
        for child_joint in children_map.get(link_name, []):
            _build_body_recursive(body_elem, child_joint.child, incoming_joint=child_joint)

    _build_body_recursive(worldbody, model.root_link, incoming_joint=None)

    # Actuators
    actuators = ET.SubElement(root, "actuator")
    for j_name, joint in model.joints.items():
        if joint.type in (JointType.REVOLUTE, JointType.PRISMATIC):
            motor_elem = ET.SubElement(actuators, "motor", name=f"motor_{j_name}", joint=j_name)
            if joint.limits:
                motor_elem.set("ctrlrange", f"{-joint.limits.effort} {joint.limits.effort}")

    xml_str = ET.tostring(root, encoding="utf-8")
    return minidom.parseString(xml_str).toprettyxml(indent="  ")


def _serialize_mjcf_geom(parent: ET.Element, name: str, geom, origin, is_visual: bool):
    geom_elem = ET.SubElement(parent, "geom", name=name)
    geom_elem.set("pos", f"{origin.xyz[0]} {origin.xyz[1]} {origin.xyz[2]}")

    if is_visual:
        geom_elem.set("rgba", "0.85 0.6 0.2 1.0" if "base" not in name else "0.2 0.3 0.4 1.0")
        geom_elem.set("contype", "0")
        geom_elem.set("conaffinity", "0")
    else:
        geom_elem.set("rgba", "0.2 0.8 0.2 0.5")

    if geom.type == GeometryType.BOX and geom.size:
        # MJCF box size is half-lengths [x/2, y/2, z/2]
        geom_elem.set("type", "box")
        geom_elem.set("size", f"{geom.size[0]/2.0} {geom.size[1]/2.0} {geom.size[2]/2.0}")
    elif geom.type == GeometryType.CYLINDER and geom.radius and geom.length:
        # MJCF cylinder size is [radius, half_length]
        geom_elem.set("type", "cylinder")
        geom_elem.set("size", f"{geom.radius} {geom.length/2.0}")
    elif geom.type == GeometryType.SPHERE and geom.radius:
        geom_elem.set("type", "sphere")
        geom_elem.set("size", str(geom.radius))


def validate_in_mujoco(mjcf_xml: str) -> Tuple[bool, str]:
    """
    Compiles the MJCF XML string directly with the MuJoCo physics engine.
    Returns (True, "Compiled successfully") or (False, error_message).
    """
    if not MUJOCO_INSTALLED:
        return False, "MuJoCo package is not installed."

    try:
        model = mujoco.MjModel.from_xml_string(mjcf_xml)
        data = mujoco.MjData(model)
        # Perform 1 test step to verify numerical stability
        mujoco.mj_step(model, data)
        return True, f"Successfully compiled and stepped in MuJoCo! DOF={model.nv}, Geoms={model.ngeom}"
    except Exception as e:
        return False, f"MuJoCo compilation failed: {e}"
