import React, { useEffect, useRef } from "react";
import * as THREE from "three";
import { useAppStore } from "../store/useAppStore";
import { Compass } from "lucide-react";

export const Viewport3D: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const telemetry = useAppStore((state) => state.telemetry);

  // References for scene, camera, renderer, and robot joints
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const jointMeshesRef = useRef<THREE.Group[]>([]);
  const isDraggingRef = useRef<boolean>(false);
  const previousMousePositionRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
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
    scene.background = new THREE.Color(0x0b0f19);
    sceneRef.current = scene;

    // 2. Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.05, 50);
    cameraRef.current = camera;
    updateCameraPosition();

    // 3. Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: "high-performance" });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // 4. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight.position.set(3, 5, 4);
    dirLight.castShadow = true;
    dirLight.shadow.mapSize.width = 1024;
    dirLight.shadow.mapSize.height = 1024;
    scene.add(dirLight);

    const fillLight = new THREE.DirectionalLight(0x38bdf8, 0.4);
    fillLight.position.set(-3, -2, -2);
    scene.add(fillLight);

    // 5. Ground Grid & Shadow Plane
    const grid = new THREE.GridHelper(4, 40, 0x334155, 0x1e293b);
    grid.position.y = 0;
    scene.add(grid);

    const groundGeo = new THREE.PlaneGeometry(10, 10);
    const groundMat = new THREE.ShadowMaterial({ opacity: 0.3 });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.001;
    ground.receiveShadow = true;
    scene.add(ground);

    // Coordinate Axes (Red=X, Green=Y, Blue=Z)
    const axesHelper = new THREE.AxesHelper(0.3);
    axesHelper.position.set(0, 0.002, 0);
    scene.add(axesHelper);

    // 6. Build Parametric 6-DOF Robotic Arm Model Hierarchy
    const joints: THREE.Group[] = [];
    const matBase = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.4, metalness: 0.8 });
    const matLink = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, roughness: 0.3, metalness: 0.6 });
    const matJoint = new THREE.MeshStandardMaterial({ color: 0xf59e0b, roughness: 0.3, metalness: 0.7 });
    const matEnd = new THREE.MeshStandardMaterial({ color: 0x0284c7, roughness: 0.2, metalness: 0.8 });

    // Base Pedestal
    const baseGroup = new THREE.Group();
    const baseCyl = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.14, 0.08, 32), matBase);
    baseCyl.position.y = 0.04;
    baseCyl.castShadow = true;
    baseGroup.add(baseCyl);
    scene.add(baseGroup);

    // Joint 1 (Z-axis rotation)
    const j1Group = new THREE.Group();
    j1Group.position.set(0, 0.08, 0);
    const j1Mesh = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 0.12, 24), matJoint);
    j1Mesh.position.y = 0.06;
    j1Mesh.castShadow = true;
    j1Group.add(j1Mesh);
    baseGroup.add(j1Group);
    joints.push(j1Group);

    // Joint 2 (Shoulder - pitch)
    const j2Group = new THREE.Group();
    j2Group.position.set(0, 0.12, 0);
    const link2Mesh = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.38, 0.08), matLink);
    link2Mesh.position.set(0, 0.19, 0.04);
    link2Mesh.castShadow = true;
    j2Group.add(link2Mesh);
    j1Group.add(j2Group);
    joints.push(j2Group);

    // Joint 3 (Elbow - pitch)
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

    // Parallel Gripper Fingers
    const fingerLeft = new THREE.Mesh(new THREE.BoxGeometry(0.015, 0.05, 0.02), matBase);
    fingerLeft.position.set(0.025, 0.04, 0);
    j6Group.add(fingerLeft);

    const fingerRight = new THREE.Mesh(new THREE.BoxGeometry(0.015, 0.05, 0.02), matBase);
    fingerRight.position.set(-0.025, 0.04, 0);
    j6Group.add(fingerRight);

    j5Group.add(j6Group);
    joints.push(j6Group);

    jointMeshesRef.current = joints;

    // Mouse Navigation Listeners (Rotate, Pan, Zoom)
    const handleMouseDown = (e: MouseEvent) => {
      isDraggingRef.current = true;
      previousMousePositionRef.current = { x: e.clientX, y: e.clientY };
    };

    const handleMouseMove = (e: MouseEvent) => {
      if (!isDraggingRef.current) return;
      const deltaX = e.clientX - previousMousePositionRef.current.x;
      const deltaY = e.clientY - previousMousePositionRef.current.y;

      sphericalRef.current.theta -= deltaX * 0.008;
      sphericalRef.current.phi = Math.max(
        0.1,
        Math.min(Math.PI / 2 - 0.05, sphericalRef.current.phi - deltaY * 0.008)
      );

      previousMousePositionRef.current = { x: e.clientX, y: e.clientY };
      updateCameraPosition();
    };

    const handleMouseUp = () => {
      isDraggingRef.current = false;
    };

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      sphericalRef.current.radius = Math.max(
        0.5,
        Math.min(8.0, sphericalRef.current.radius + e.deltaY * 0.002)
      );
      updateCameraPosition();
    };

    container.addEventListener("mousedown", handleMouseDown);
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    container.addEventListener("wheel", handleWheel, { passive: false });

    // Handle Window Resize
    const handleResize = () => {
      if (!containerRef.current || !rendererRef.current || !cameraRef.current) return;
      const w = containerRef.current.clientWidth;
      const h = containerRef.current.clientHeight;
      cameraRef.current.aspect = w / h;
      cameraRef.current.updateProjectionMatrix();
      rendererRef.current.setSize(w, h);
    };
    window.addEventListener("resize", handleResize);

    // Render Loop
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

  // Update Robot Joint Angles when live telemetry arrives
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

  const updateCameraPosition = () => {
    if (!cameraRef.current) return;
    const { radius, theta, phi } = sphericalRef.current;
    const x = radius * Math.sin(phi) * Math.sin(theta);
    const y = radius * Math.cos(phi);
    const z = radius * Math.sin(phi) * Math.cos(theta);

    cameraRef.current.position.set(x, y + 0.35, z);
    cameraRef.current.lookAt(0, 0.35, 0);
  };

  const setCameraPreset = (preset: "iso" | "top" | "front" | "side") => {
    if (preset === "iso") {
      sphericalRef.current = { radius: 2.2, theta: Math.PI / 4, phi: Math.PI / 3 };
    } else if (preset === "top") {
      sphericalRef.current = { radius: 2.2, theta: 0, phi: 0.1 };
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
          className="px-2 py-1 rounded hover:bg-slate-800 hover:text-white transition font-medium"
        >
          ISO
        </button>
        <button
          onClick={() => setCameraPreset("front")}
          className="px-2 py-1 rounded hover:bg-slate-800 hover:text-white transition font-medium"
        >
          FRONT
        </button>
        <button
          onClick={() => setCameraPreset("top")}
          className="px-2 py-1 rounded hover:bg-slate-800 hover:text-white transition font-medium"
        >
          TOP
        </button>
        <button
          onClick={() => setCameraPreset("side")}
          className="px-2 py-1 rounded hover:bg-slate-800 hover:text-white transition font-medium"
        >
          SIDE
        </button>
      </div>

      {/* Real-time End-Effector Coordinates HUD */}
      {telemetry?.end_effector && (
        <div className="absolute bottom-3 left-3 bg-slate-900/80 backdrop-blur-md px-3 py-2 rounded-lg border border-slate-800 text-[11px] font-mono text-slate-300 space-y-0.5">
          <div className="text-[10px] text-slate-400 font-sans uppercase font-semibold flex items-center space-x-1">
            <Compass className="w-3 h-3 text-sky-400" />
            <span>End-Effector Pose (XYZ)</span>
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
        Left Drag: Orbit | Scroll: Zoom
      </div>
    </div>
  );
};
