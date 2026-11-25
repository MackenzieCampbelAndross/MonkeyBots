"""
Robot Model Exporters
Generates standard URDF and MuJoCo MJCF XML format definitions from RobotModel structures.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from core.monkeybots.models.robot import RobotModel


def export_to_urdf(model: RobotModel) -> str:
    """Exports a RobotModel into standard URDF XML format."""
    robot_elem = ET.Element("robot", name=model.name)

    for link in model.links.values():
        link_elem = ET.SubElement(robot_elem, "link", name=link.name)
        if link.inertial:
            inertial = ET.SubElement(link_elem, "inertial")
            ET.SubElement(inertial, "mass", value=str(link.inertial.mass))
            ixx = link.inertial.inertia.ixx
            iyy = link.inertial.inertia.iyy
            izz = link.inertial.inertia.izz
            ET.SubElement(inertial, "inertia", ixx=str(ixx), iyy=str(iyy), izz=str(izz), ixy="0", ixz="0", iyz="0")

    for joint in model.joints.values():
        joint_elem = ET.SubElement(robot_elem, "joint", name=joint.name, type=joint.type.value)
        ET.SubElement(joint_elem, "parent", link=joint.parent)
        ET.SubElement(joint_elem, "child", link=joint.child)
        ET.SubElement(joint_elem, "axis", xyz=f"{joint.axis[0]} {joint.axis[1]} {joint.axis[2]}")
        if joint.limits:
            ET.SubElement(
                joint_elem,
                "limit",
                lower=str(joint.limits.lower),
                upper=str(joint.limits.upper),
                effort=str(joint.limits.effort),
                velocity=str(joint.limits.velocity),
            )

    raw_xml = ET.tostring(robot_elem, encoding="utf-8")
    parsed = minidom.parseString(raw_xml)
    return parsed.toprettyxml(indent="  ")


def export_to_mjcf(model: RobotModel) -> str:
    """Exports a RobotModel into MuJoCo MJCF XML format."""
    mujoco = ET.Element("mujoco", model=model.name)
    ET.SubElement(mujoco, "compiler", angle="radian", coordinate="local")
    worldbody = ET.SubElement(mujoco, "worldbody")

    current_parent = worldbody
    for link in model.links.values():
        body = ET.SubElement(current_parent, "body", name=link.name)
        if link.inertial:
            ixx = link.inertial.inertia.ixx
            iyy = link.inertial.inertia.iyy
            izz = link.inertial.inertia.izz
            ET.SubElement(body, "inertial", mass=str(link.inertial.mass), diaginertia=f"{ixx} {iyy} {izz}")
        
        # Find joints having this link as child
        for j in model.joints.values():
            if j.child == link.name:
                low = j.limits.lower if j.limits else -3.14
                high = j.limits.upper if j.limits else 3.14
                ET.SubElement(
                    body,
                    "joint",
                    name=j.name,
                    type="hinge",
                    axis=f"{j.axis[0]} {j.axis[1]} {j.axis[2]}",
                    range=f"{low} {high}",
                )
        current_parent = body

    raw_xml = ET.tostring(mujoco, encoding="utf-8")
    parsed = minidom.parseString(raw_xml)
    return parsed.toprettyxml(indent="  ")
