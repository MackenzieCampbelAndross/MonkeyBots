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

    for link in model.links:
        link_elem = ET.SubElement(robot_elem, "link", name=link.name)
        inertial = ET.SubElement(link_elem, "inertial")
        ET.SubElement(inertial, "mass", value=str(link.mass_kg))
        ixx, iyy, izz = link.inertia_diag
        ET.SubElement(inertial, "inertia", ixx=str(ixx), iyy=str(iyy), izz=str(izz), ixy="0", ixz="0", iyz="0")

    for joint in model.joints:
        joint_elem = ET.SubElement(robot_elem, "joint", name=joint.name, type=joint.type.value)
        ET.SubElement(joint_elem, "parent", link=joint.parent_link)
        ET.SubElement(joint_elem, "child", link=joint.child_link)
        ET.SubElement(joint_elem, "axis", xyz=f"{joint.axis[0]} {joint.axis[1]} {joint.axis[2]}")
        ET.SubElement(
            joint_elem,
            "limit",
            lower=str(joint.limits.lower_rad),
            upper=str(joint.limits.upper_rad),
            effort=str(joint.limits.effort_nm),
            velocity=str(joint.limits.velocity_rad_s),
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
    for link in model.links:
        body = ET.SubElement(current_parent, "body", name=link.name)
        ET.SubElement(body, "inertial", mass=str(link.mass_kg), diaginertia=f"{link.inertia_diag[0]} {link.inertia_diag[1]} {link.inertia_diag[2]}")
        # Find joint child of this link
        for j in model.joints:
            if j.child_link == link.name:
                ET.SubElement(
                    body,
                    "joint",
                    name=j.name,
                    type="hinge",
                    axis=f"{j.axis[0]} {j.axis[1]} {j.axis[2]}",
                    range=f"{j.limits.lower_rad} {j.limits.upper_rad}",
                )
        current_parent = body

    raw_xml = ET.tostring(mujoco, encoding="utf-8")
    parsed = minidom.parseString(raw_xml)
    return parsed.toprettyxml(indent="  ")
