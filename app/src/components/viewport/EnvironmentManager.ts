/**
 * MonkeyBots Simulation Environment & Obstacle Manager
 *
 * Manages 3D scene objects, work surfaces, obstacles, and pick/place targets.
 */

import * as THREE from "three";

export interface EnvironmentObjectSpec {
  id: string;
  name: string;
  type: "table" | "box" | "cylinder" | "sphere" | "target";
  position: [number, number, number];
  rotation: [number, number, number];
  size: [number, number, number];
  color: string;
}

export class EnvironmentManager {
  public rootGroup: THREE.Group;
  public objects: Map<string, THREE.Mesh> = new Map();
  public objectSpecs: Map<string, EnvironmentObjectSpec> = new Map();

  constructor() {
    this.rootGroup = new THREE.Group();
    this.rootGroup.name = "Environment_Objects";

    // Add default work cell table and pick target
    this.addObject({
      id: "work_table",
      name: "Work Table Surface",
      type: "table",
      position: [0.45, 0.15, 0.0],
      rotation: [0, 0, 0],
      size: [0.6, 0.3, 0.8],
      color: "#334155",
    });

    this.addObject({
      id: "target_part",
      name: "Pick Target Part",
      type: "box",
      position: [0.45, 0.33, 0.0],
      rotation: [0, 0, 0],
      size: [0.06, 0.06, 0.06],
      color: "#f59e0b",
    });
  }

  public addObject(spec: EnvironmentObjectSpec): THREE.Mesh {
    // Remove previous if exists
    if (this.objects.has(spec.id)) {
      this.removeObject(spec.id);
    }

    let geometry: THREE.BufferGeometry;
    let material: THREE.Material;

    if (spec.type === "table") {
      // Table surface with 4 legs
      const groupMesh = new THREE.Group() as any;
      const topGeo = new THREE.BoxGeometry(spec.size[0], 0.04, spec.size[2]);
      const topMat = new THREE.MeshStandardMaterial({
        color: new THREE.Color(spec.color),
        roughness: 0.3,
        metalness: 0.5,
      });
      const topMesh = new THREE.Mesh(topGeo, topMat);
      topMesh.position.y = spec.size[1];
      topMesh.castShadow = true;
      topMesh.receiveShadow = true;
      groupMesh.add(topMesh);

      // Legs
      const legMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.8 });
      const legGeo = new THREE.CylinderGeometry(0.02, 0.02, spec.size[1], 16);
      const halfX = spec.size[0] / 2 - 0.04;
      const halfZ = spec.size[2] / 2 - 0.04;
      const legY = spec.size[1] / 2;

      for (const [lx, lz] of [
        [-halfX, -halfZ],
        [halfX, -halfZ],
        [-halfX, halfZ],
        [halfX, halfZ],
      ]) {
        const leg = new THREE.Mesh(legGeo, legMat);
        leg.position.set(lx, legY, lz);
        leg.castShadow = true;
        groupMesh.add(leg);
      }

      groupMesh.position.set(spec.position[0], 0, spec.position[2]);
      groupMesh.userData = { id: spec.id, name: spec.name, type: "environment" };
      this.rootGroup.add(groupMesh);
      this.objects.set(spec.id, groupMesh);
      this.objectSpecs.set(spec.id, spec);
      return groupMesh;
    }

    // Primitive geometries (box, cylinder, sphere, target)
    if (spec.type === "box") {
      geometry = new THREE.BoxGeometry(spec.size[0], spec.size[1], spec.size[2]);
    } else if (spec.type === "cylinder") {
      geometry = new THREE.CylinderGeometry(spec.size[0] / 2, spec.size[0] / 2, spec.size[1], 24);
    } else if (spec.type === "sphere") {
      geometry = new THREE.SphereGeometry(spec.size[0] / 2, 24, 24);
    } else {
      // Target marker
      geometry = new THREE.OctahedronGeometry(spec.size[0] / 2);
    }

    material = new THREE.MeshStandardMaterial({
      color: new THREE.Color(spec.color),
      roughness: 0.25,
      metalness: 0.4,
    });

    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(spec.position[0], spec.position[1], spec.position[2]);
    mesh.rotation.set(spec.rotation[0], spec.rotation[1], spec.rotation[2]);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.userData = { id: spec.id, name: spec.name, type: "environment" };

    this.rootGroup.add(mesh);
    this.objects.set(spec.id, mesh);
    this.objectSpecs.set(spec.id, spec);
    return mesh;
  }

  public updatePosition(id: string, pos: [number, number, number]) {
    const mesh = this.objects.get(id);
    const spec = this.objectSpecs.get(id);
    if (mesh && spec) {
      mesh.position.set(pos[0], pos[1], pos[2]);
      spec.position = pos;
    }
  }

  public removeObject(id: string) {
    const mesh = this.objects.get(id);
    if (mesh) {
      this.rootGroup.remove(mesh);
      this.objects.delete(id);
      this.objectSpecs.delete(id);
    }
  }

  public getAllSpecs(): EnvironmentObjectSpec[] {
    return Array.from(this.objectSpecs.values());
  }
}
