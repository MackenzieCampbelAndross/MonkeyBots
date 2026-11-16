import React, { useEffect, useRef } from "react";
import * as THREE from "three";
import { useAppStore } from "../store/useAppStore";
import { Compass } from "lucide-react";

export const Viewport3D: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const telemetry = useAppStore((state) => state.telemetry);
  const viewportSettings = useAppStore((state) => state.viewportSettings);
  const setWorldCursorCoords = useAppStore((state) => state.setWorldCursorCoords);

  // References
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const gridRef = useRef<THREE.GridHelper | null>(null);
  const axesRef = useRef<THREE.AxesHelper | null>(null);
  const jointMeshesRef = useRef<THREE.Group[]>([]);
  const robotMaterialsRef = useRef<THREE.Material[]>([]);

  // Camera Orbit Controls State
  const isDraggingRef = useRef<boolean>(false);
  const isPanningRef = useRef<boolean>(false);
  const previousMousePositionRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const cameraTargetRef = useRef<THREE.Vector3>(new THREE.Vector3(0, 0.35, 0));
  const sphericalRef = useRef<{ radius: number; theta: number; phi: number }>({
    radius: 2.2,
    theta: Math.PI / 4,
    phi: Math.PI / 3,
  });

  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // 1. Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x070a12);
    sceneRef.current = scene;

    // 2. Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.05, 50);
    cameraRef.current = camera;
    updateCameraPosition();

    // 3. Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // 4. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 1.4);
    dirLight.position.set(3, 5, 4);
    dirLight.castShadow = true;
    dirLight.shadow.mapSize.width = 1024;
    dirLight.shadow.mapSize.height = 1024;
    scene.add(dirLight);

    const fillLight = new THREE.DirectionalLight(0x38bdf8, 0.5);
    fillLight.position.set(-3, -2, -2);
    scene.add(fillLight);

    // 5. CAD Ground Grid
    const grid = new THREE.GridHelper(4, 40, 0x475569, 0x1e293b);
    grid.position.y = 0;
    scene.add(grid);
    gridRef.current = grid;

    const groundGeo = new THREE.PlaneGeometry(10, 10);
    const groundMat = new THREE.ShadowMaterial({ opacity: 0.35 });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.001;
    ground.receiveShadow = true;
    scene.add(ground);

    // Coordinate Axes Triad (Red=X, Green=Y, Blue=Z)
    const axesHelper = new THREE.AxesHelper(0.35);
    axesHelper.position.set(0, 0.002, 0);
    scene.add(axesHelper);
    axesRef.current = axesHelper;

    // 6. Build Parametric 6-DOF Robotic Arm Model Hierarchy
    const joints: THREE.Group[] = [];
    const matBase = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.3, metalness: 0.8 });
    const matLink = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, roughness: 0.25, metalness: 0.6 });
    const matJoint = new THREE.MeshStandardMaterial({ color: 0xf59e0b, roughness: 0.3, metalness: 0.7 });
    const matEnd = new THREE.MeshStandardMaterial({ color: 0x0284c7, roughness: 0.2, metalness: 0.8 });
    robotMaterialsRef.current = [matBase, matLink, matJoint, matEnd];

    // Base Pedestal
    const baseGroup = new THREE.Group();
    const baseCyl = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.14, 0.08, 32), matBase);
    baseCyl.position.y = 0.04;
    baseCyl.castShadow = true;
    baseGroup.add(baseCyl);
    scene.add(baseGroup);

    // Joint 1 (Base Yaw)
    const j1Group = new THREE.Group();
    j1Group.position.set(0, 0.08, 0);
    const j1Mesh = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 0.12, 24), matJoint);
    j1Mesh.position.y = 0.06;
    j1Mesh.castShadow = true;
    j1Group.add(j1Mesh);
    baseGroup.add(j1Group);
    joints.push(j1Group);

    // Joint 2 (Shoulder Pitch)
    const j2Group = new THREE.Group();
    j2Group.position.set(0, 0.12, 0);
    const link2Mesh = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.38, 0.08), matLink);
    link2Mesh.position.set(0, 0.19, 0.04);
    link2Mesh.castShadow = true;
    j2Group.add(link2Mesh);
    j1Group.add(j2Group);
    joints.push(j2Group);

    // Joint 3 (Elbow Pitch)
    const j3Group = new THREE.Group();
    j3Group.position.set(0, 0.38, 0);
    const link3Mesh = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.34, 0.07), matLink);
    link3Mesh.position.set(0, 0.17, -0.03);
    link3Mesh.castShadow = true;
    j3Group.add(link3Mesh);
    j2Group.add(j3Group);
    joints.push(j3Group);

    // Joint 4 (Wrist 1)
    const j4Group = new THREE.Group();
    j4Group.position.set(0, 0.34, 0);
    const j4Mesh = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 0.08, 16), matJoint);
    j4Mesh.rotation.x = Math.PI / 2;
    j4Mesh.castShadow = true;
    j4Group.add(j4Mesh);
    j3Group.add(j4Group);
    joints.push(j4Group);

    // Joint 5 (Wrist 2)
    const j5Group = new THREE.Group();
    j5Group.position.set(0, 0.08, 0);
    const j5Mesh = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.08, 16), matJoint);
    j5Mesh.position.y = 0.04;
    j5Mesh.castShadow = true;
    j5Group.add(j5Mesh);
    j4Group.add(j5Group);
    joints.push(j5Group);

    // Joint 6 & Gripper Flange
    const j6Group = new THREE.Group();
    j6Group.position.set(0, 0.08, 0);
    const flangeMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.03, 24), matEnd);
    flangeMesh.position.y = 0.015;
    j6Group.add(flangeMesh);

    const fingerLeft = new THREE.Mesh(new THREE.BoxGeometry(0.015, 0.05, 0.02), matBase);
    fingerLeft.position.set(0.025, 0.04, 0);
    j6Group.add(fingerLeft);

    const fingerRight = new THREE.Mesh(new THREE.BoxGeometry(0.015, 0.05, 0.02), matBase);
    fingerRight.position.set(-0.025, 0.04, 0);
    j6Group.add(fingerRight);

    j5Group.add(j6Group);
    joints.push(j6Group);

    jointMeshesRef.current = joints;

    // Mouse Navigation Listeners (Left Drag: Orbit, Middle Drag: Pan, Scroll: Zoom)
    const handleMouseDown = (e: MouseEvent) => {
      if (e.button === 0) {
        isDraggingRef.current = true;
      } else if (e.button === 1 || e.button === 2) {
        isPanningRef.current = true;
      }
      previousMousePositionRef.current = { x: e.clientX, y: e.clientY };
    };

    const handleMouseMove = (e: MouseEvent) => {
      const deltaX = e.clientX - previousMousePositionRef.current.x;
      const deltaY = e.clientY - previousMousePositionRef.current.y;
      previousMousePositionRef.current = { x: e.clientX, y: e.clientY };

      if (isDraggingRef.current) {
        sphericalRef.current.theta -= deltaX * 0.008;
        sphericalRef.current.phi = Math.max(
          0.05,
          Math.min(Math.PI / 2 - 0.02, sphericalRef.current.phi - deltaY * 0.008)
        );
        updateCameraPosition();
      } else if (isPanningRef.current && cameraRef.current) {
        const panSpeed = 0.0015 * sphericalRef.current.radius;
        const right = new THREE.Vector3();
        cameraRef.current.getWorldDirection(right);
        right.cross(cameraRef.current.up).normalize();

        cameraTargetRef.current.addScaledVector(right, -deltaX * panSpeed);
        cameraTargetRef.current.y += deltaY * panSpeed;
        updateCameraPosition();
      }

      // Raycast ground plane coordinates for Status Bar HUD
      if (containerRef.current && cameraRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        const mouseX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        const mouseY = -((e.clientY - rect.top) / rect.height) * 2 + 1;
        const raycaster = new THREE.Raycaster();
        raycaster.setFromCamera(new THREE.Vector2(mouseX, mouseY), cameraRef.current);
        const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
        const intersectPoint = new THREE.Vector3();
        if (raycaster.ray.intersectPlane(plane, intersectPoint)) {
          setWorldCursorCoords({
            x: intersectPoint.x,
            y: 0,
            z: intersectPoint.z,
          });
        }
      }
    };

    const handleMouseUp = () => {
      isDraggingRef.current = false;
      isPanningRef.current = false;
    };

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      sphericalRef.current.radius = Math.max(
        0.4,
        Math.min(10.0, sphericalRef.current.radius + e.deltaY * 0.002)
      );
      updateCameraPosition();
    };

    container.addEventListener("mousedown", handleMouseDown);
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    container.addEventListener("wheel", handleWheel, { passive: false });
    container.addEventListener("contextmenu", (e) => e.preventDefault());

    // Resize Observer
    const handleResize = () => {
      if (!containerRef.current || !rendererRef.current || !cameraRef.current) return;
      const w = containerRef.current.clientWidth;
      const h = containerRef.current.clientHeight;
      cameraRef.current.aspect = w / h;
      cameraRef.current.updateProjectionMatrix();
      rendererRef.current.setSize(w, h);
    };
    window.addEventListener("resize", handleResize);

    // Animation Loop
    let animId: number;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      if (rendererRef.current && sceneRef.current && cameraRef.current) {
        rendererRef.current.render(sceneRef.current, cameraRef.current);
      }
    };
    animate();

    return () => {
      cancelAnimationFrame(animId);
      container.removeEventListener("mousedown", handleMouseDown);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
      container.removeEventListener("wheel", handleWheel);
      window.removeEventListener("resize", handleResize);
      if (rendererRef.current && container.contains(rendererRef.current.domElement)) {
        container.removeChild(rendererRef.current.domElement);
      }
      renderer.dispose();
    };
  }, []);

  // Update Joint Rotations when live telemetry arrives
  useEffect(() => {
    if (!telemetry || jointMeshesRef.current.length < 6) return;
    const q = telemetry.qpos;
    const joints = jointMeshesRef.current;

    if (q[0] !== undefined) joints[0].rotation.y = q[0];
    if (q[1] !== undefined) joints[1].rotation.z = q[1];
    if (q[2] !== undefined) joints[2].rotation.z = q[2];
    if (q[3] !== undefined) joints[3].rotation.y = q[3];
    if (q[4] !== undefined) joints[4].rotation.z = q[4];
    if (q[5] !== undefined) joints[5].rotation.y = q[5];
  }, [telemetry]);

  // Update Viewport Settings (Grid, Axes, Shading Mode)
  useEffect(() => {
    if (gridRef.current) gridRef.current.visible = viewportSettings.showGrid;
    if (axesRef.current) axesRef.current.visible = viewportSettings.showAxes;

    // Shading mode wireframe toggle
    robotMaterialsRef.current.forEach((mat) => {
      if ("wireframe" in mat) {
        (mat as THREE.MeshStandardMaterial).wireframe = viewportSettings.shadingMode === "wireframe";
      }
    });
  }, [viewportSettings]);

  const updateCameraPosition = () => {
    if (!cameraRef.current) return;
    const { radius, theta, phi } = sphericalRef.current;
    const target = cameraTargetRef.current;
    const x = target.x + radius * Math.sin(phi) * Math.sin(theta);
    const y = target.y + radius * Math.cos(phi);
    const z = target.z + radius * Math.sin(phi) * Math.cos(theta);

    cameraRef.current.position.set(x, y, z);
    cameraRef.current.lookAt(target);
  };

  const setCameraPreset = (preset: "iso" | "top" | "front" | "side") => {
    cameraTargetRef.current.set(0, 0.35, 0);
    if (preset === "iso") {
      sphericalRef.current = { radius: 2.2, theta: Math.PI / 4, phi: Math.PI / 3 };
    } else if (preset === "top") {
      sphericalRef.current = { radius: 2.2, theta: 0, phi: 0.05 };
    } else if (preset === "front") {
      sphericalRef.current = { radius: 2.0, theta: 0, phi: Math.PI / 2 - 0.05 };
    } else if (preset === "side") {
      sphericalRef.current = { radius: 2.0, theta: Math.PI / 2, phi: Math.PI / 2 - 0.05 };
    }
    updateCameraPosition();
  };

  return (
    <div className="relative w-full h-full bg-slate-950 overflow-hidden select-none" ref={containerRef}>
      {/* Viewport Overlay Controls */}
      <div className="absolute top-3 left-3 flex items-center space-x-1.5 bg-slate-900/80 backdrop-blur-md p-1 rounded-lg border border-slate-800 text-xs text-slate-300">
        <button
          onClick={() => setCameraPreset("iso")}
          className="px-2 py-0.5 rounded hover:bg-slate-800 hover:text-white transition font-medium"
        >
          ISO
        </button>
        <button
          onClick={() => setCameraPreset("front")}
          className="px-2 py-0.5 rounded hover:bg-slate-800 hover:text-white transition font-medium"
        >
          FRONT
        </button>
        <button
          onClick={() => setCameraPreset("top")}
          className="px-2 py-0.5 rounded hover:bg-slate-800 hover:text-white transition font-medium"
        >
          TOP
        </button>
        <button
          onClick={() => setCameraPreset("side")}
          className="px-2 py-0.5 rounded hover:bg-slate-800 hover:text-white transition font-medium"
        >
          SIDE
        </button>
      </div>

      {/* Real-time End-Effector Coordinates HUD */}
      {telemetry?.end_effector && (
        <div className="absolute bottom-3 left-3 bg-slate-900/80 backdrop-blur-md px-3 py-2 rounded-lg border border-slate-800 text-[11px] font-mono text-slate-300 space-y-0.5">
          <div className="text-[10px] text-slate-400 font-sans uppercase font-semibold flex items-center space-x-1">
            <Compass className="w-3 h-3 text-sky-400" />
            <span>Flange Pose (World Frame)</span>
          </div>
          <div>
            X: <span className="text-amber-400">{telemetry.end_effector.position[0].toFixed(3)}</span>m | Y:{" "}
            <span className="text-emerald-400">{telemetry.end_effector.position[1].toFixed(3)}</span>m | Z:{" "}
            <span className="text-sky-400">{telemetry.end_effector.position[2].toFixed(3)}</span>m
          </div>
        </div>
      )}

      {/* Navigation Help Prompt */}
      <div className="absolute top-3 right-3 text-[10px] text-slate-400 bg-slate-900/70 backdrop-blur px-2.5 py-1 rounded border border-slate-800/80">
        Left: Orbit | Right/Middle: Pan | Scroll: Zoom
      </div>
    </div>
  );
};
