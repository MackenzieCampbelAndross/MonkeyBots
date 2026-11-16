/**
 * MonkeyBots Interactive 3D Simulation Environment & Digital Twin
 *
 * Implements Three.js rendering of robot geometry, collision hulls, coordinate triads,
 * joint axes, environment objects, perspective/orthographic projections, object selection,
 * and high-frequency simulation synchronization.
 */

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { useAppStore } from "../store/useAppStore";
import { fetchSample6DofModel } from "../services/api";
import { RobotVisualizer, type RobotGeometrySpec } from "./viewport/RobotVisualizer";
import { EnvironmentManager, type EnvironmentObjectSpec } from "./viewport/EnvironmentManager";
import { ViewportToolbar } from "./viewport/ViewportToolbar";
import { Compass, Box, Activity } from "lucide-react";

export const Viewport3D: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const telemetry = useAppStore((state) => state.telemetry);
  const setWorldCursorCoords = useAppStore((state) => state.setWorldCursorCoords);
  const addToast = useAppStore((state) => state.addToast);

  // Scene & Engine References
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const perspCameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const orthoCameraRef = useRef<THREE.OrthographicCamera | null>(null);
  const activeCameraRef = useRef<THREE.Camera | null>(null);

  const visualizerRef = useRef<RobotVisualizer>(new RobotVisualizer());
  const envManagerRef = useRef<EnvironmentManager>(new EnvironmentManager());
  const gridRef = useRef<THREE.GridHelper | null>(null);
  const dirLightRef = useRef<THREE.DirectionalLight | null>(null);

  // Viewport Settings State
  const [isOrthographic, setIsOrthographic] = useState<boolean>(false);
  const [showGrid, setShowGrid] = useState<boolean>(true);
  const [showFrames, setShowFrames] = useState<boolean>(false);
  const [showCollisions, setShowCollisions] = useState<boolean>(false);
  const [showJointAxes, setShowJointAxes] = useState<boolean>(false);
  const [showShadows, setShowShadows] = useState<boolean>(true);
  const [shadingMode, setShadingMode] = useState<"solid" | "wireframe" | "xray">("solid");

  // Selection & Diagnostics
  const [selectedEntity, setSelectedEntity] = useState<any | null>(null);
  const [syncLatencyMs, setSyncLatencyMs] = useState<number>(2.4);

  // Camera Orbit State
  const isDraggingRef = useRef<boolean>(false);
  const isPanningRef = useRef<boolean>(false);
  const previousMousePositionRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const cameraTargetRef = useRef<THREE.Vector3>(new THREE.Vector3(0, 0.35, 0));
  const sphericalRef = useRef<{ radius: number; theta: number; phi: number }>({
    radius: 2.2,
    theta: Math.PI / 4,
    phi: Math.PI / 3,
  });

  // 1. Initialize Three.js Scene and Render Loop
  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // A. Scene Setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x070a12);
    sceneRef.current = scene;

    // B. Cameras: Perspective & Orthographic
    const aspect = width / height;
    const perspCamera = new THREE.PerspectiveCamera(45, aspect, 0.05, 50);
    perspCameraRef.current = perspCamera;

    const frustumSize = 2.0;
    const orthoCamera = new THREE.OrthographicCamera(
      (frustumSize * aspect) / -2,
      (frustumSize * aspect) / 2,
      frustumSize / 2,
      frustumSize / -2,
      0.05,
      50
    );
    orthoCameraRef.current = orthoCamera;
    activeCameraRef.current = perspCamera;

    updateCameraPositions();

    // C. WebGL Renderer
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      powerPreference: "high-performance",
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // D. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.65);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 1.4);
    dirLight.position.set(3, 5, 4);
    dirLight.castShadow = true;
    dirLight.shadow.mapSize.width = 2048;
    dirLight.shadow.mapSize.height = 2048;
    dirLight.shadow.camera.near = 0.5;
    dirLight.shadow.camera.far = 15;
    dirLight.shadow.bias = -0.0005;
    scene.add(dirLight);
    dirLightRef.current = dirLight;

    const fillLight = new THREE.DirectionalLight(0x38bdf8, 0.45);
    fillLight.position.set(-3, -2, -2);
    scene.add(fillLight);

    // E. CAD Floor Grid & Ground Shadow Receiver
    const grid = new THREE.GridHelper(4, 40, 0x475569, 0x1e293b);
    grid.position.y = 0;
    scene.add(grid);
    gridRef.current = grid;

    const groundGeo = new THREE.PlaneGeometry(12, 12);
    const groundMat = new THREE.ShadowMaterial({ opacity: 0.35 });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.001;
    ground.receiveShadow = true;
    scene.add(ground);

    // Coordinate Triad at World Origin
    const worldAxes = new THREE.AxesHelper(0.35);
    worldAxes.position.set(0, 0.001, 0);
    scene.add(worldAxes);

    // F. Add Robot Model & Environment Hierarchies to Scene
    scene.add(visualizerRef.current.rootGroup);
    scene.add(envManagerRef.current.rootGroup);

    // Load initial 6-DOF Robot Model
    fetchSample6DofModel()
      .then((modelSpec: RobotGeometrySpec) => {
        visualizerRef.current.buildModel(modelSpec);
      })
      .catch((err) => console.error("Failed to load sample robot geometry", err));

    // G. Mouse Event Handlers for Navigation & Selection
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
        updateCameraPositions();
      } else if (isPanningRef.current && activeCameraRef.current) {
        const panSpeed = 0.0015 * sphericalRef.current.radius;
        const right = new THREE.Vector3();
        activeCameraRef.current.getWorldDirection(right);
        right.cross(activeCameraRef.current.up).normalize();

        cameraTargetRef.current.addScaledVector(right, -deltaX * panSpeed);
        cameraTargetRef.current.y += deltaY * panSpeed;
        updateCameraPositions();
      }

      // Cursor World Coordinate Raycasting
      if (containerRef.current && activeCameraRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        const mouseX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
        const mouseY = -((e.clientY - rect.top) / rect.height) * 2 + 1;
        const raycaster = new THREE.Raycaster();
        raycaster.setFromCamera(new THREE.Vector2(mouseX, mouseY), activeCameraRef.current);
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

    const handleClick = (e: MouseEvent) => {
      if (!containerRef.current || !activeCameraRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const mouseX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const mouseY = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      const raycaster = new THREE.Raycaster();
      raycaster.setFromCamera(new THREE.Vector2(mouseX, mouseY), activeCameraRef.current);

      // Intersect with robot links and environment objects
      const intersects = raycaster.intersectObjects([
        ...visualizerRef.current.visualMeshes,
        ...Array.from(envManagerRef.current.objects.values()),
      ], true);

      if (intersects.length > 0) {
        const hit = intersects[0].object;
        setSelectedEntity({
          name: hit.name || hit.userData?.linkName || hit.userData?.name || "Selected Entity",
          type: hit.userData?.type || "Mesh",
          position: [hit.position.x, hit.position.y, hit.position.z],
        });
      }
    };

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      sphericalRef.current.radius = Math.max(
        0.4,
        Math.min(10.0, sphericalRef.current.radius + e.deltaY * 0.002)
      );
      updateCameraPositions();
    };

    container.addEventListener("mousedown", handleMouseDown);
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    container.addEventListener("click", handleClick);
    container.addEventListener("wheel", handleWheel, { passive: false });
    container.addEventListener("contextmenu", (e) => e.preventDefault());

    // Resize Handler
    const handleResize = () => {
      if (!containerRef.current || !rendererRef.current) return;
      const w = containerRef.current.clientWidth;
      const h = containerRef.current.clientHeight;
      const asp = w / h;

      if (perspCameraRef.current) {
        perspCameraRef.current.aspect = asp;
        perspCameraRef.current.updateProjectionMatrix();
      }
      if (orthoCameraRef.current) {
        const fs = 2.0;
        orthoCameraRef.current.left = (fs * asp) / -2;
        orthoCameraRef.current.right = (fs * asp) / 2;
        orthoCameraRef.current.top = fs / 2;
        orthoCameraRef.current.bottom = fs / -2;
        orthoCameraRef.current.updateProjectionMatrix();
      }
      rendererRef.current.setSize(w, h);
    };
    window.addEventListener("resize", handleResize);

    // Animation Loop
    let animId: number;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      if (rendererRef.current && sceneRef.current && activeCameraRef.current) {
        rendererRef.current.render(sceneRef.current, activeCameraRef.current);
      }
    };
    animate();

    return () => {
      cancelAnimationFrame(animId);
      container.removeEventListener("mousedown", handleMouseDown);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
      container.removeEventListener("click", handleClick);
      container.removeEventListener("wheel", handleWheel);
      window.removeEventListener("resize", handleResize);
      if (rendererRef.current && container.contains(rendererRef.current.domElement)) {
        container.removeChild(rendererRef.current.domElement);
      }
      renderer.dispose();
    };
  }, []);

  const updateCameraPositions = () => {
    const { radius, theta, phi } = sphericalRef.current;
    const target = cameraTargetRef.current;
    const x = target.x + radius * Math.sin(phi) * Math.sin(theta);
    const y = target.y + radius * Math.cos(phi);
    const z = target.z + radius * Math.sin(phi) * Math.cos(theta);

    if (perspCameraRef.current) {
      perspCameraRef.current.position.set(x, y, z);
      perspCameraRef.current.lookAt(target);
    }
    if (orthoCameraRef.current) {
      orthoCameraRef.current.position.set(x, y, z);
      orthoCameraRef.current.lookAt(target);
    }
  };

  // 2. Synchronize Robot Joint Rotations on Telemetry Arrival
  useEffect(() => {
    if (!telemetry) return;
    const t0 = performance.now();
    visualizerRef.current.updateJointPositions(telemetry.joint_names, telemetry.qpos);
    const delta = performance.now() - t0;
    setSyncLatencyMs(Math.max(0.5, Math.round(delta * 10) / 10));
  }, [telemetry]);

  // 3. Toolbar Handlers
  const handleCameraPreset = (preset: "iso" | "front" | "top" | "side") => {
    cameraTargetRef.current.set(0, 0.35, 0);
    if (preset === "iso") {
      sphericalRef.current = { radius: 2.2, theta: Math.PI / 4, phi: Math.PI / 3 };
    } else if (preset === "top") {
      sphericalRef.current = { radius: 2.2, theta: 0, phi: 0.02 };
    } else if (preset === "front") {
      sphericalRef.current = { radius: 2.0, theta: 0, phi: Math.PI / 2 - 0.02 };
    } else if (preset === "side") {
      sphericalRef.current = { radius: 2.0, theta: Math.PI / 2, phi: Math.PI / 2 - 0.02 };
    }
    updateCameraPositions();
  };

  const handleToggleProjection = () => {
    const nextOrtho = !isOrthographic;
    setIsOrthographic(nextOrtho);
    activeCameraRef.current = nextOrtho ? orthoCameraRef.current : perspCameraRef.current;
    updateCameraPositions();
  };

  const handleToggleGrid = () => {
    setShowGrid(!showGrid);
    if (gridRef.current) gridRef.current.visible = !showGrid;
  };

  const handleToggleFrames = () => {
    setShowFrames(!showFrames);
    visualizerRef.current.setFramesVisibility(!showFrames);
  };

  const handleToggleCollisions = () => {
    setShowCollisions(!showCollisions);
    visualizerRef.current.setCollisionVisibility(!showCollisions);
  };

  const handleToggleJointAxes = () => {
    setShowJointAxes(!showJointAxes);
    visualizerRef.current.setJointAxesVisibility(!showJointAxes);
  };

  const handleToggleShadows = () => {
    setShowShadows(!showShadows);
    if (rendererRef.current) {
      rendererRef.current.shadowMap.enabled = !showShadows;
    }
  };

  const handleChangeShading = (mode: "solid" | "wireframe" | "xray") => {
    setShadingMode(mode);
    visualizerRef.current.setShadingMode(mode);
  };

  const handleAddObstacle = (type: "table" | "box" | "cylinder" | "target") => {
    const id = `obj_${Date.now()}`;
    const name = `${type.toUpperCase()} Obstacle`;
    const spec: EnvironmentObjectSpec = {
      id,
      name,
      type,
      position: [0.35, 0.25, -0.2],
      rotation: [0, 0, 0],
      size: type === "box" ? [0.15, 0.15, 0.15] : type === "cylinder" ? [0.1, 0.2, 0.1] : [0.08, 0.08, 0.08],
      color: type === "target" ? "#10b981" : "#f59e0b",
    };
    envManagerRef.current.addObject(spec);
    addToast("info", "Environment Object Added", `Spawned '${name}' in 3D simulation scene.`);
  };

  return (
    <div className="relative w-full h-full bg-slate-950 overflow-hidden select-none" ref={containerRef}>
      {/* 3D Viewport Controls Toolbar */}
      <ViewportToolbar
        onCameraPreset={handleCameraPreset}
        isOrthographic={isOrthographic}
        onToggleProjection={handleToggleProjection}
        showGrid={showGrid}
        onToggleGrid={handleToggleGrid}
        showFrames={showFrames}
        onToggleFrames={handleToggleFrames}
        showCollisions={showCollisions}
        onToggleCollisions={handleToggleCollisions}
        showJointAxes={showJointAxes}
        onToggleJointAxes={handleToggleJointAxes}
        showShadows={showShadows}
        onToggleShadows={handleToggleShadows}
        shadingMode={shadingMode}
        onChangeShading={handleChangeShading}
        onAddObstacle={handleAddObstacle}
      />

      {/* Selected Entity Card */}
      {selectedEntity && (
        <div className="absolute top-14 left-3 bg-slate-900/90 backdrop-blur-md px-3 py-2 rounded-lg border border-slate-800 text-[11px] font-mono text-slate-300 space-y-1 shadow-lg z-10">
          <div className="flex items-center justify-between space-x-3 text-sky-400 font-bold font-sans">
            <span className="flex items-center space-x-1">
              <Box className="w-3.5 h-3.5" />
              <span>{selectedEntity.name}</span>
            </span>
            <button
              onClick={() => setSelectedEntity(null)}
              className="text-slate-500 hover:text-slate-200"
            >
              &times;
            </button>
          </div>
          <div className="text-[10px] text-slate-400">
            Type: <span className="text-slate-200">{selectedEntity.type}</span>
          </div>
          <div className="text-[10px] text-slate-400">
            Pos: [{selectedEntity.position.map((x: number) => x.toFixed(3)).join(", ")}]m
          </div>
        </div>
      )}

      {/* Real-Time Digital Twin Synchronization & Latency HUD */}
      <div className="absolute bottom-3 left-3 bg-slate-900/90 backdrop-blur-md px-3 py-2 rounded-lg border border-slate-800 text-[11px] font-mono text-slate-300 space-y-0.5 shadow-lg">
        <div className="text-[10px] text-slate-400 font-sans uppercase font-semibold flex items-center justify-between space-x-3">
          <span className="flex items-center space-x-1">
            <Compass className="w-3 h-3 text-sky-400" />
            <span>Digital Twin Synchronization</span>
          </span>
          <span className="text-emerald-400 font-bold flex items-center space-x-1">
            <Activity className="w-3 h-3" />
            <span>{syncLatencyMs} ms</span>
          </span>
        </div>
        {telemetry?.end_effector && (
          <div>
            EE Pos: X: <span className="text-amber-400">{telemetry.end_effector.position[0].toFixed(3)}</span>m | Y:{" "}
            <span className="text-emerald-400">{telemetry.end_effector.position[1].toFixed(3)}</span>m | Z:{" "}
            <span className="text-sky-400">{telemetry.end_effector.position[2].toFixed(3)}</span>m
          </div>
        )}
      </div>

      {/* Navigation Help Prompt */}
      <div className="absolute top-3 right-3 text-[10px] text-slate-400 bg-slate-900/70 backdrop-blur px-2.5 py-1 rounded border border-slate-800/80">
        Left Drag: Orbit | Right/Middle Drag: Pan | Scroll: Zoom | Click: Inspect
      </div>
    </div>
  );
};
