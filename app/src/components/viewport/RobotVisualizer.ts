/**
 * MonkeyBots High-Performance Three.js Robot Visualizer
 *
 * Dynamically constructs 3D visual and collision hierarchies from RobotModel descriptions.
 * Manages coordinate triads, joint axes indicators, collision hulls, and real-time state synchronization.
 */

import * as THREE from "three";

export interface RobotGeometrySpec {
  name: string;
  root_link: string;
  links: Record<
    string,
    {
      name: string;
      visuals: Array<{
        origin: { xyz: [number, number, number]; rpy: [number, number, number] };
        geometry: {
          type: "box" | "cylinder" | "sphere" | "mesh";
          size?: [number, number, number];
          radius?: number;
          length?: number;
        };
      }>;
      collisions: Array<{
        origin: { xyz: [number, number, number]; rpy: [number, number, number] };
        geometry: {
          type: "box" | "cylinder" | "sphere" | "mesh";
          size?: [number, number, number];
          radius?: number;
          length?: number;
        };
      }>;
    }
  >;
  joints: Record<
    string,
    {
      name: string;
      type: string;
      parent: string;
      child: string;
      origin: { xyz: [number, number, number]; rpy: [number, number, number] };
      axis: [number, number, number];
    }
  >;
}

export class RobotVisualizer {
  public rootGroup: THREE.Group;
  public linkGroups: Map<string, THREE.Group> = new Map();
  public jointGroups: Map<string, THREE.Group> = new Map();
  public visualMeshes: THREE.Mesh[] = [];
  public collisionMeshes: THREE.Mesh[] = [];
  public frameHelpers: THREE.AxesHelper[] = [];
  public jointAxesHelpers: THREE.Group[] = [];

  // Reusable Materials
  private matLink: THREE.MeshStandardMaterial;
  private matJoint: THREE.MeshStandardMaterial;
  private matFlange: THREE.MeshStandardMaterial;
  private matCollision: THREE.MeshStandardMaterial;

  constructor() {
    this.rootGroup = new THREE.Group();
    this.rootGroup.name = "Robot_Digital_Twin";

    // Industrial CAD Materials
    this.matLink = new THREE.MeshStandardMaterial({
      color: 0xe2e8f0,
      roughness: 0.25,
      metalness: 0.65,
      envMapIntensity: 1.0,
    });
    this.matJoint = new THREE.MeshStandardMaterial({
      color: 0xf59e0b,
      roughness: 0.35,
      metalness: 0.7,
    });
    this.matFlange = new THREE.MeshStandardMaterial({
      color: 0x0284c7,
      roughness: 0.2,
      metalness: 0.85,
    });
    // Collision hull: translucent orange wireframe/hull
    this.matCollision = new THREE.MeshStandardMaterial({
      color: 0xf97316,
      wireframe: true,
      transparent: true,
      opacity: 0.45,
    });
  }

  /**
   * Constructs the Three.js scene hierarchy from a RobotModel description.
   */
  public buildModel(model: RobotGeometrySpec) {
    this.clear();

    const rootLinkName = model.root_link;
    const rootLinkGroup = new THREE.Group();
    rootLinkGroup.name = `link_${rootLinkName}`;
    rootLinkGroup.userData = { linkName: rootLinkName, type: "link" };
    this.linkGroups.set(rootLinkName, rootLinkGroup);
    this.rootGroup.add(rootLinkGroup);

    // Build visual and collision geometry for root link
    const rootLinkSpec = model.links[rootLinkName];
    if (rootLinkSpec) {
      this.buildLinkGeometries(rootLinkGroup, rootLinkSpec);
    }

    // Map parent to child joints
    const parentToJoints: Record<string, any[]> = {};
    for (const joint of Object.values(model.joints)) {
      if (!parentToJoints[joint.parent]) parentToJoints[joint.parent] = [];
      parentToJoints[joint.parent].push(joint);
    }

    // Recursive tree builder
    const buildBranch = (parentLinkName: string, parentGroup: THREE.Group) => {
      const childJoints = parentToJoints[parentLinkName] || [];
      for (const joint of childJoints) {
        // Joint origin frame
        const jointGroup = new THREE.Group();
        jointGroup.name = `joint_${joint.name}`;
        jointGroup.userData = {
          jointName: joint.name,
          jointType: joint.type,
          axis: joint.axis,
          type: "joint",
        };

        const xyz = joint.origin?.xyz || [0, 0, 0];
        const rpy = joint.origin?.rpy || [0, 0, 0];
        jointGroup.position.set(xyz[0], xyz[1], xyz[2]);
        jointGroup.rotation.set(rpy[0], rpy[1], rpy[2], "XYZ");

        // Coordinate frame triad at joint
        const triad = new THREE.AxesHelper(0.12);
        triad.name = `frame_${joint.name}`;
        jointGroup.add(triad);
        this.frameHelpers.push(triad);

        // Joint rotation axis visualization indicator
        const axisGroup = this.createJointAxisIndicator(joint.axis);
        jointGroup.add(axisGroup);
        this.jointAxesHelpers.push(axisGroup);

        parentGroup.add(jointGroup);
        this.jointGroups.set(joint.name, jointGroup);

        // Child link frame
        const childLinkName = joint.child;
        const childLinkGroup = new THREE.Group();
        childLinkGroup.name = `link_${childLinkName}`;
        childLinkGroup.userData = { linkName: childLinkName, type: "link" };
        jointGroup.add(childLinkGroup);
        this.linkGroups.set(childLinkName, childLinkGroup);

        const childLinkSpec = model.links[childLinkName];
        if (childLinkSpec) {
          this.buildLinkGeometries(childLinkGroup, childLinkSpec);
        }

        // Recursively build children
        buildBranch(childLinkName, childLinkGroup);
      }
    };

    buildBranch(rootLinkName, rootLinkGroup);
  }

  private buildLinkGeometries(linkGroup: THREE.Group, spec: any) {
    // 1. Visual Geometries
    for (const vis of spec.visuals || []) {
      const mesh = this.createMeshFromGeometry(vis.geometry, this.matLink);
      if (mesh) {
        const xyz = vis.origin?.xyz || [0, 0, 0];
        const rpy = vis.origin?.rpy || [0, 0, 0];
        mesh.position.set(xyz[0], xyz[1], xyz[2]);
        mesh.rotation.set(rpy[0], rpy[1], rpy[2], "XYZ");
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        mesh.userData = { linkName: spec.name, type: "visual" };
        linkGroup.add(mesh);
        this.visualMeshes.push(mesh);
      }
    }

    // 2. Collision Geometries
    for (const col of spec.collisions || []) {
      const mesh = this.createMeshFromGeometry(col.geometry, this.matCollision);
      if (mesh) {
        const xyz = col.origin?.xyz || [0, 0, 0];
        const rpy = col.origin?.rpy || [0, 0, 0];
        mesh.position.set(xyz[0], xyz[1], xyz[2]);
        mesh.rotation.set(rpy[0], rpy[1], rpy[2], "XYZ");
        mesh.visible = false; // Hidden by default, toggleable
        mesh.userData = { linkName: spec.name, type: "collision" };
        linkGroup.add(mesh);
        this.collisionMeshes.push(mesh);
      }
    }
  }

  private createMeshFromGeometry(geom: any, mat: THREE.Material): THREE.Mesh | null {
    if (!geom) return null;
    let threeGeo: THREE.BufferGeometry;

    if (geom.type === "box") {
      const size = geom.size || [0.1, 0.1, 0.1];
      threeGeo = new THREE.BoxGeometry(size[0], size[1], size[2]);
    } else if (geom.type === "cylinder") {
      const radius = geom.radius || 0.05;
      const length = geom.length || 0.1;
      threeGeo = new THREE.CylinderGeometry(radius, radius, length, 24);
      // URDF cylinders are aligned along Z axis by standard, Three.js aligns along Y
      threeGeo.rotateX(Math.PI / 2);
    } else if (geom.type === "sphere") {
      const radius = geom.radius || 0.05;
      threeGeo = new THREE.SphereGeometry(radius, 24, 24);
    } else {
      threeGeo = new THREE.BoxGeometry(0.08, 0.08, 0.08);
    }

    return new THREE.Mesh(threeGeo, mat);
  }

  private createJointAxisIndicator(axis: [number, number, number]): THREE.Group {
    const group = new THREE.Group();
    const dir = new THREE.Vector3(axis[0], axis[1], axis[2]).normalize();
    
    // Axis arrow helper
    const arrow = new THREE.ArrowHelper(dir, new THREE.Vector3(0, 0, 0), 0.14, 0xf59e0b, 0.04, 0.025);
    group.add(arrow);

    // Torus rotation ring perpendicular to axis
    const ringGeo = new THREE.TorusGeometry(0.06, 0.003, 8, 24);
    const ringMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    // Align torus normal with axis vector
    const defaultNormal = new THREE.Vector3(0, 0, 1);
    const quat = new THREE.Quaternion().setFromUnitVectors(defaultNormal, dir);
    ring.quaternion.copy(quat);
    group.add(ring);

    return group;
  }

  /**
   * Synchronizes joint positions from live simulation telemetry.
   * Zero reallocation - updates existing object transform matrices directly.
   */
  public updateJointPositions(jointNames: string[], qpos: number[]) {
    for (let i = 0; i < jointNames.length; i++) {
      const name = jointNames[i];
      const val = qpos[i];
      if (val === undefined) continue;

      const group = this.jointGroups.get(name);
      if (!group) continue;

      const axis = (group.userData?.axis || [0, 0, 1]) as [number, number, number];
      const type = group.userData?.jointType;

      if (type === "prismatic") {
        group.position.set(axis[0] * val, axis[1] * val, axis[2] * val);
      } else {
        // Revolute: rotate around local axis
        const axisVec = new THREE.Vector3(axis[0], axis[1], axis[2]).normalize();
        group.quaternion.setFromAxisAngle(axisVec, val);
      }
    }
  }

  /**
   * Toggles visibility of collision hulls.
   */
  public setCollisionVisibility(visible: boolean) {
    for (const mesh of this.collisionMeshes) {
      mesh.visible = visible;
    }
  }

  /**
   * Toggles coordinate triads.
   */
  public setFramesVisibility(visible: boolean) {
    for (const helper of this.frameHelpers) {
      helper.visible = visible;
    }
  }

  /**
   * Toggles joint rotation indicators.
   */
  public setJointAxesVisibility(visible: boolean) {
    for (const helper of this.jointAxesHelpers) {
      helper.visible = visible;
    }
  }

  /**
   * Updates shading mode: solid CAD, wireframe, or translucent X-ray.
   */
  public setShadingMode(mode: "solid" | "wireframe" | "xray") {
    const isWire = mode === "wireframe";
    const isXray = mode === "xray";

    this.matLink.wireframe = isWire;
    this.matJoint.wireframe = isWire;
    this.matFlange.wireframe = isWire;

    this.matLink.transparent = isXray;
    this.matLink.opacity = isXray ? 0.4 : 1.0;
    this.matJoint.transparent = isXray;
    this.matJoint.opacity = isXray ? 0.45 : 1.0;
  }

  public clear() {
    while (this.rootGroup.children.length > 0) {
      this.rootGroup.remove(this.rootGroup.children[0]);
    }
    this.linkGroups.clear();
    this.jointGroups.clear();
    this.visualMeshes = [];
    this.collisionMeshes = [];
    this.frameHelpers = [];
    this.jointAxesHelpers = [];
  }
}
