"""
MonkeyBots URDF Parser and Generator
Bi-directional serialization between RobotModel and ROS URDF XML format.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, List, Optional
from .robot import (
    RobotModel,
    Link,
    Joint,
    Inertial,
    InertiaTensor,
    Origin,
    Geometry,
    GeometryType,
    Material,
    Visual,
    Collision,
    JointType,
    JointLimits,
    JointDynamics,
)


def export_urdf(model: RobotModel) -> str:
    """Exports a RobotModel instance to standard ROS URDF XML string."""
    root = ET.Element("robot", name=model.name)

    # 1. Links
    for link_name, link in model.links.items():
        l_elem = ET.SubElement(root, "link", name=link_name)

        # Inertial
        if link.inertial:
            ine_elem = ET.SubElement(l_elem, "inertial")
            ET.SubElement(
                ine_elem,
                "origin",
                xyz=f"{link.inertial.origin.xyz[0]} {link.inertial.origin.xyz[1]} {link.inertial.origin.xyz[2]}",
                rpy=f"{link.inertial.origin.rpy[0]} {link.inertial.origin.rpy[1]} {link.inertial.origin.rpy[2]}",
            )
            ET.SubElement(ine_elem, "mass", value=str(link.inertial.mass))
            it = link.inertial.inertia
            ET.SubElement(
                ine_elem,
                "inertia",
                ixx=str(it.ixx),
                iyy=str(it.iyy),
                izz=str(it.izz),
                ixy=str(it.ixy),
                ixz=str(it.ixz),
                iyz=str(it.iyz),
            )

        # Visuals
        for vis in link.visuals:
            v_elem = ET.SubElement(l_elem, "visual")
            ET.SubElement(
                v_elem,
                "origin",
                xyz=f"{vis.origin.xyz[0]} {vis.origin.xyz[1]} {vis.origin.xyz[2]}",
                rpy=f"{vis.origin.rpy[0]} {vis.origin.rpy[1]} {vis.origin.rpy[2]}",
            )
            g_elem = ET.SubElement(v_elem, "geometry")
            _serialize_geometry(g_elem, vis.geometry)
            if vis.material:
                m_elem = ET.SubElement(v_elem, "material", name=vis.material.name)
                rgba_str = " ".join(str(c) for c in vis.material.rgba)
                ET.SubElement(m_elem, "color", rgba=rgba_str)

        # Collisions
        for col in link.collisions:
            c_elem = ET.SubElement(l_elem, "collision")
            ET.SubElement(
                c_elem,
                "origin",
                xyz=f"{col.origin.xyz[0]} {col.origin.xyz[1]} {col.origin.xyz[2]}",
                rpy=f"{col.origin.rpy[0]} {col.origin.rpy[1]} {col.origin.rpy[2]}",
            )
            g_elem = ET.SubElement(c_elem, "geometry")
            _serialize_geometry(g_elem, col.geometry)

    # 2. Joints
    for joint_name, joint in model.joints.items():
        j_elem = ET.SubElement(root, "joint", name=joint_name, type=joint.type.value)
        ET.SubElement(j_elem, "parent", link=joint.parent)
        ET.SubElement(j_elem, "child", link=joint.child)
        ET.SubElement(
            j_elem,
            "origin",
            xyz=f"{joint.origin.xyz[0]} {joint.origin.xyz[1]} {joint.origin.xyz[2]}",
            rpy=f"{joint.origin.rpy[0]} {joint.origin.rpy[1]} {joint.origin.rpy[2]}",
        )
        ET.SubElement(j_elem, "axis", xyz=f"{joint.axis[0]} {joint.axis[1]} {joint.axis[2]}")

        if joint.limits:
            ET.SubElement(
                j_elem,
                "limit",
                lower=str(joint.limits.lower),
                upper=str(joint.limits.upper),
                effort=str(joint.limits.effort),
                velocity=str(joint.limits.velocity),
            )

        if joint.dynamics:
            ET.SubElement(
                j_elem,
                "dynamics",
                damping=str(joint.dynamics.damping),
                friction=str(joint.dynamics.friction),
            )

    xml_str = ET.tostring(root, encoding="utf-8")
    return minidom.parseString(xml_str).toprettyxml(indent="  ")


def _serialize_geometry(parent: ET.Element, geom: Geometry):
    if geom.type == GeometryType.BOX and geom.size:
        ET.SubElement(parent, "box", size=f"{geom.size[0]} {geom.size[1]} {geom.size[2]}")
    elif geom.type == GeometryType.CYLINDER and geom.radius and geom.length:
        ET.SubElement(parent, "cylinder", radius=str(geom.radius), length=str(geom.length))
    elif geom.type == GeometryType.SPHERE and geom.radius:
        ET.SubElement(parent, "sphere", radius=str(geom.radius))
    elif geom.type == GeometryType.MESH and geom.filename:
        m_elem = ET.SubElement(parent, "mesh", filename=geom.filename)
        if geom.scale:
            m_elem.set("scale", f"{geom.scale[0]} {geom.scale[1]} {geom.scale[2]}")


def import_urdf(xml_content: str) -> RobotModel:
    """Parses a standard ROS URDF XML string into a RobotModel."""
    root = ET.fromstring(xml_content)
    robot_name = root.attrib.get("name", "robot")

    links: Dict[str, Link] = {}
    joints: Dict[str, Joint] = {}
    child_links = set()

    # Parse Links
    for l_elem in root.findall("link"):
        l_name = l_elem.attrib["name"]
        inertial = None

        ine_elem = l_elem.find("inertial")
        if ine_elem is not None:
            m_val = float(ine_elem.find("mass").attrib["value"]) if ine_elem.find("mass") is not None else 1.0
            o_elem = ine_elem.find("origin")
            orig = _parse_origin(o_elem)

            ine_node = ine_elem.find("inertia")
            if ine_node is not None:
                tensor = InertiaTensor(
                    ixx=float(ine_node.attrib.get("ixx", 0.01)),
                    iyy=float(ine_node.attrib.get("iyy", 0.01)),
                    izz=float(ine_node.attrib.get("izz", 0.01)),
                    ixy=float(ine_node.attrib.get("ixy", 0.0)),
                    ixz=float(ine_node.attrib.get("ixz", 0.0)),
                    iyz=float(ine_node.attrib.get("iyz", 0.0)),
                )
            else:
                tensor = InertiaTensor(ixx=0.01, iyy=0.01, izz=0.01)

            inertial = Inertial(mass=m_val, origin=orig, inertia=tensor)

        # Parse Visuals
        visuals = []
        for v_elem in l_elem.findall("visual"):
            v_orig = _parse_origin(v_elem.find("origin"))
            g_obj = _parse_geometry(v_elem.find("geometry"))
            visuals.append(Visual(origin=v_orig, geometry=g_obj))

        # Parse Collisions
        collisions = []
        for c_elem in l_elem.findall("collision"):
            c_orig = _parse_origin(c_elem.find("origin"))
            g_obj = _parse_geometry(c_elem.find("geometry"))
            collisions.append(Collision(origin=c_orig, geometry=g_obj))

        links[l_name] = Link(name=l_name, inertial=inertial, visuals=visuals, collisions=collisions)

    # Parse Joints
    for j_elem in root.findall("joint"):
        j_name = j_elem.attrib["name"]
        j_type = JointType(j_elem.attrib.get("type", "revolute"))
        parent_link = j_elem.find("parent").attrib["link"]
        child_link = j_elem.find("child").attrib["link"]
        child_links.add(child_link)

        j_orig = _parse_origin(j_elem.find("origin"))

        axis_elem = j_elem.find("axis")
        axis = [0.0, 0.0, 1.0]
        if axis_elem is not None and "xyz" in axis_elem.attrib:
            axis = [float(x) for x in axis_elem.attrib["xyz"].split()]

        # Limits
        lim_elem = j_elem.find("limit")
        limits = None
        if lim_elem is not None:
            limits = JointLimits(
                lower=float(lim_elem.attrib.get("lower", -3.14)),
                upper=float(lim_elem.attrib.get("upper", 3.14)),
                effort=float(lim_elem.attrib.get("effort", 100.0)),
                velocity=float(lim_elem.attrib.get("velocity", 3.14)),
            )

        # Dynamics
        dyn_elem = j_elem.find("dynamics")
        dynamics = None
        if dyn_elem is not None:
            dynamics = JointDynamics(
                damping=float(dyn_elem.attrib.get("damping", 0.1)),
                friction=float(dyn_elem.attrib.get("friction", 0.05)),
            )

        joints[j_name] = Joint(
            name=j_name,
            type=j_type,
            parent=parent_link,
            child=child_link,
            origin=j_orig,
            axis=axis,
            limits=limits,
            dynamics=dynamics,
        )

    # Find Root Link (Link that is never a child)
    root_link_candidates = [l for l in links if l not in child_links]
    root_link = root_link_candidates[0] if root_link_candidates else (list(links.keys())[0] if links else "")

    return RobotModel(name=robot_name, root_link=root_link, links=links, joints=joints)


def _parse_origin(elem: Optional[ET.Element]) -> Origin:
    if elem is None:
        return Origin()
    xyz = [float(x) for x in elem.attrib.get("xyz", "0 0 0").split()]
    rpy = [float(x) for x in elem.attrib.get("rpy", "0 0 0").split()]
    return Origin(xyz=xyz, rpy=rpy)


def _parse_geometry(elem: Optional[ET.Element]) -> Geometry:
    if elem is None:
        return Geometry(type=GeometryType.BOX, size=[0.1, 0.1, 0.1])

    b_elem = elem.find("box")
    if b_elem is not None:
        size = [float(x) for x in b_elem.attrib.get("size", "0.1 0.1 0.1").split()]
        return Geometry(type=GeometryType.BOX, size=size)

    c_elem = elem.find("cylinder")
    if c_elem is not None:
        return Geometry(
            type=GeometryType.CYLINDER,
            radius=float(c_elem.attrib.get("radius", 0.05)),
            length=float(c_elem.attrib.get("length", 0.2)),
        )

    s_elem = elem.find("sphere")
    if s_elem is not None:
        return Geometry(type=GeometryType.SPHERE, radius=float(s_elem.attrib.get("radius", 0.05)))

    m_elem = elem.find("mesh")
    if m_elem is not None:
        scale = None
        if "scale" in m_elem.attrib:
            scale = [float(x) for x in m_elem.attrib["scale"].split()]
        return Geometry(type=GeometryType.MESH, filename=m_elem.attrib.get("filename", ""), scale=scale)

    return Geometry(type=GeometryType.BOX, size=[0.1, 0.1, 0.1])
