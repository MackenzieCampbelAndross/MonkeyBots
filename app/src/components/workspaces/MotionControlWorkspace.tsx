import React, { useState, useEffect, useCallback } from "react";
import { Viewport3D } from "../Viewport3D";
import { useAppStore } from "../../store/useAppStore";
import { simWebSocket } from "../../services/websocket";
import {
  fetchKinematicChain,
  calculateFK,
  calculateIK,
  fetchPosePresets,
  planTrajectory,
  executeTrajectory,
  runStepResponseTest,
  fetchTrajectoryPresets,
  sendGripperCommand,
  fetchGripperStatus,
  fetchCollisionEvents,
  executePickAndPlace,
  runManipulationBenchmarks,
} from "../../services/api";
import type {
  KinematicChainInfo,
  FKResultData,
  IKResultData,
  PosePreset,
  PlanTrajectoryResponse,
  ExecuteTrajectoryResponse,
  StepResponseData,
  TrajectoryPreset,
} from "../../types/api";
import {
  Move3d,
  Play,
  RotateCcw,
  Target,
  Sliders,
  Activity,
  Compass,
  Zap,
  RefreshCw,
  Gauge,
  TrendingUp,
  BarChart3,
  Plus,
  Trash2,
  Box,
  ShieldAlert,
  CheckCircle2,
  XCircle,
} from "lucide-react";

export const MotionControlWorkspace: React.FC = () => {
  const { addToast, telemetry } = useAppStore();

  // Navigation / Mode Switcher
  const [activeTab, setActiveTab] = useState<"IK" | "FK" | "TRAJECTORY" | "PID" | "MANIPULATION">("TRAJECTORY");
  const [inspectorTab, setInspectorTab] = useState<"METRICS" | "TRANSFORM" | "JACOBIAN" | "TELEMETRY" | "CONTACTS">("TELEMETRY");

  // Robot State
  const [chainInfo, setChainInfo] = useState<KinematicChainInfo | null>(null);
  const [jointAnglesRad, setJointAnglesRad] = useState<number[]>([0, -0.6, 1.2, 0, 0.6, 0]);

  // IK Targets
  const [targetPos, setTargetPos] = useState<[number, number, number]>([0.45, 0.0, 0.55]);
  const [targetRpyDeg, setTargetRpyDeg] = useState<[number, number, number]>([0.0, 45.0, 0.0]);
  const [solverMethod, setSolverMethod] = useState<string>("damped_least_squares");
  const [continuousSolve, setContinuousSolve] = useState<boolean>(true);

  // Trajectory Planning State
  const [waypoints, setWaypoints] = useState<number[][]>([
    [0.0, -0.785, 1.57, 0.0, 0.785, 0.0],
    [0.5, -0.4, 1.2, 0.0, 0.6, 0.2],
    [0.5, 0.1, 0.9, 0.0, 0.3, 0.2],
    [-0.5, -0.2, 1.3, 0.0, 0.7, -0.2],
    [0.0, -0.785, 1.57, 0.0, 0.785, 0.0],
  ]);
  const [interpolation, setInterpolation] = useState<string>("quintic");
  const [vMax, setVMax] = useState<number>(2.0);
  const [aMax, setAMax] = useState<number>(4.0);
  const [plannedTraj, setPlannedTraj] = useState<PlanTrajectoryResponse | null>(null);
  const [execResult, setExecResult] = useState<ExecuteTrajectoryResponse | null>(null);
  const [isPlanning, setIsPlanning] = useState<boolean>(false);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);

  // PID Tuning & Step Response State
  const [selectedJoint, setSelectedJoint] = useState<number>(1);
  const [kp, setKp] = useState<number>(280.0);
  const [ki, setKi] = useState<number>(2.0);
  const [kd, setKd] = useState<number>(50.0);
  const [stepAmp, setStepAmp] = useState<number>(0.30);
  const [stepDuration, setStepDuration] = useState<number>(2.0);
  const [stepResponse, setStepResponse] = useState<StepResponseData | null>(null);
  const [isTestingStep, setIsTestingStep] = useState<boolean>(false);

  // Presets & Diagnostics
  const [fkResult, setFkResult] = useState<FKResultData | null>(null);
  const [ikResult, setIkResult] = useState<IKResultData | null>(null);
  const [posePresets, setPosePresets] = useState<PosePreset[]>([]);
  const [trajPresets, setTrajPresets] = useState<TrajectoryPreset[]>([]);
  const [isSolving, setIsSolving] = useState<boolean>(false);

  // Stage 09: Manipulation & Contact Physics State
  const [gripperForce, setGripperForce] = useState<number>(16.0);
  const [gripperStatus, setGripperStatus] = useState<{
    width: number;
    left_force: number;
    right_force: number;
    is_grasping: boolean;
  }>({ width: 0.08, left_force: 0, right_force: 0, is_grasping: false });
  const [pickPos, setPickPos] = useState<[number, number, number]>([0.45, 0.0, 0.225]);
  const [placePos, setPlacePos] = useState<[number, number, number]>([0.35, -0.20, 0.225]);
  const [liftHeight, setLiftHeight] = useState<number>(0.15);
  const [isExecutingPnP, setIsExecutingPnP] = useState<boolean>(false);
  const [pnpResult, setPnpResult] = useState<any | null>(null);
  const [manipBenchmarks, setManipBenchmarks] = useState<any | null>(null);
  const [isRunningBenchmarks, setIsRunningBenchmarks] = useState<boolean>(false);
  const [collisionEvents, setCollisionEvents] = useState<any[]>([]);

  // Refresh gripper & collision events periodically when on relevant tab
  useEffect(() => {
    if (activeTab === "MANIPULATION" || inspectorTab === "CONTACTS") {
      fetchGripperStatus()
        .then((st) => setGripperStatus(st))
        .catch(() => {});
      fetchCollisionEvents(25)
        .then((res) => setCollisionEvents(res.events || []))
        .catch(() => {});
    }
  }, [activeTab, inspectorTab, telemetry]);

  const handleGripperOpen = async () => {
    try {
      await sendGripperCommand("OPEN", 0.0);
      const st = await fetchGripperStatus();
      setGripperStatus(st);
      addToast("info", "Gripper Opened", "Jaws opened to full aperture.");
    } catch (err: any) {
      addToast("error", "Gripper Error", err.message || "Failed to open gripper");
    }
  };

  const handleGripperClose = async () => {
    try {
      await sendGripperCommand("CLOSE", gripperForce);
      const st = await fetchGripperStatus();
      setGripperStatus(st);
      addToast(
        st.is_grasping ? "success" : "info",
        st.is_grasping ? "Object Grasped" : "Gripper Closed",
        `Applied ${gripperForce} N squeeze. Left: ${st.left_force} N, Right: ${st.right_force} N`
      );
    } catch (err: any) {
      addToast("error", "Gripper Error", err.message || "Failed to close gripper");
    }
  };

  const handleExecutePickAndPlace = async () => {
    setIsExecutingPnP(true);
    addToast("info", "Pick & Place Started", "Initiating physics-governed pick and place sequence...");
    try {
      const res = await executePickAndPlace({
        pick_pos: pickPos,
        place_pos: placePos,
        lift_height: liftHeight,
        grip_force: gripperForce,
      });
      setPnpResult(res);
      const st = await fetchGripperStatus();
      setGripperStatus(st);
      if (res.success) {
        addToast("success", "Pick & Place Succeeded", `Object lifted +${res.phases.find((p: any) => p.phase === "FRICTION_LIFT")?.lift_delta_z_m || 0.12} m purely via friction.`);
      } else {
        addToast("warning", "Pick & Place Warning", "Grasp or lift verification condition was not fully met.");
      }
    } catch (err: any) {
      addToast("error", "Execution Failed", err.message || "Pick and place cycle failed.");
    } finally {
      setIsExecutingPnP(false);
    }
  };

  const handleRunBenchmarks = async () => {
    setIsRunningBenchmarks(true);
    addToast("info", "Running Benchmarks", "Executing 5 controlled physical verification experiments...");
    try {
      const res = await runManipulationBenchmarks();
      setManipBenchmarks(res);
      if (res.all_passed) {
        addToast("success", "All 5 Benchmarks Passed", "Verified contact onset, obstacle impact, bilateral grasp, friction lift & free-fall.");
      } else {
        addToast("error", "Benchmark Failures", `${res.failed_count} of 5 benchmarks failed.`);
      }
    } catch (err: any) {
      addToast("error", "Benchmark Run Error", err.message || "Failed to run benchmarks.");
    } finally {
      setIsRunningBenchmarks(false);
    }
  };

  // Load initial robot chain and presets
  useEffect(() => {
    fetchKinematicChain("default_6dof_arm")
      .then((data) => setChainInfo(data))
      .catch((err) => console.error("Chain fetch error", err));

    fetchPosePresets("default_6dof_arm")
      .then((data) => data.presets && setPosePresets(data.presets))
      .catch((err) => console.error("Pose presets error", err));

    fetchTrajectoryPresets()
      .then((data) => data.trajectories && setTrajPresets(data.trajectories))
      .catch((err) => console.error("Trajectory presets error", err));
  }, []);

  // Compute FK whenever joint angles change
  const triggerFK = useCallback(async (angles: number[]) => {
    try {
      const res = await calculateFK(angles, "default_6dof_arm");
      setFkResult(res);
    } catch (err) {
      console.error("FK calculation failed", err);
    }
  }, []);

  useEffect(() => {
    triggerFK(jointAnglesRad);
  }, [triggerFK, jointAnglesRad]);

  // Solve IK
  const triggerIK = useCallback(async () => {
    setIsSolving(true);
    try {
      const res = await calculateIK({
        robotId: "default_6dof_arm",
        targetPosition: targetPos,
        targetRpyDeg: targetRpyDeg,
        initialSeed: jointAnglesRad,
        method: solverMethod,
        posToleranceM: 1e-4,
        rotToleranceRad: 1e-3,
      });
      setIkResult(res);
      if (res.converged && res.joint_positions_rad) {
        setJointAnglesRad(res.joint_positions_rad);
        if (res.achieved_pose) setFkResult(res.achieved_pose);
      }
    } catch (err) {
      console.error("IK error", err);
    } finally {
      setIsSolving(false);
    }
  }, [targetPos, targetRpyDeg, jointAnglesRad, solverMethod]);

  useEffect(() => {
    if (activeTab === "IK" && continuousSolve) {
      const timer = setTimeout(() => triggerIK(), 60);
      return () => clearTimeout(timer);
    }
  }, [activeTab, continuousSolve, targetPos, targetRpyDeg, triggerIK]);

  // Plan Trajectory
  const handlePlanTrajectory = async () => {
    setIsPlanning(true);
    try {
      const res = await planTrajectory({
        waypoints,
        interpolation,
        vMax,
        aMax,
        sampleDt: 0.02,
      });
      setPlannedTraj(res);
      addToast("info", "Trajectory Planned", `Generated ${res.num_samples} samples over ${res.total_duration}s.`);
    } catch (err: any) {
      addToast("error", "Planning Failed", err.message || "Failed to generate trajectory.");
    } finally {
      setIsPlanning(false);
    }
  };

  // Execute Trajectory on live MuJoCo simulation
  const handleExecuteTrajectory = async () => {
    setIsExecuting(true);
    try {
      const res = await executeTrajectory({
        waypoints,
        interpolation,
        vMax,
        aMax,
      });
      setExecResult(res);
      addToast(
        "info",
        "Trajectory Executed",
        `Tracking complete. Overall RMSE: ${(res.overall_position_rmse_rad * 1000).toFixed(2)} mrad.`
      );
    } catch (err: any) {
      addToast("error", "Execution Failed", err.message || "Simulation execution error.");
    } finally {
      setIsExecuting(false);
    }
  };

  // Run Step Response Test
  const handleRunStepResponse = async () => {
    setIsTestingStep(true);
    try {
      const res = await runStepResponseTest({
        jointIndex: selectedJoint,
        stepAmplitudeRad: stepAmp,
        testDuration: stepDuration,
        kp,
        ki,
        kd,
      });
      setStepResponse(res);
      addToast("info", "Step Response Complete", `Stability: ${res.stability}, Overshoot: ${res.overshoot_percent}%.`);
    } catch (err: any) {
      addToast("error", "Step Test Failed", err.message || "Could not execute step response test.");
    } finally {
      setIsTestingStep(false);
    }
  };

  // Dispatch live joint angles to MuJoCo
  const handleSendToSimulation = () => {
    simWebSocket.sendJointPositions(jointAnglesRad, 0.05);
    addToast("info", "Dispatched to MuJoCo", "Commanded physical robot joints to coordinates.");
  };

  return (
    <div className="flex-1 flex overflow-hidden bg-slate-950 text-slate-100 font-sans select-none">
      {/* LEFT PANEL: Kinematics, Planning & Control Docks */}
      <div className="w-[410px] bg-slate-900 border-r border-slate-800 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-3 border-b border-slate-800 bg-slate-900/90 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Move3d className="w-4 h-4 text-sky-400" />
            <span className="font-bold text-xs uppercase tracking-wider text-slate-200">
              Motion Planning & Robot Control
            </span>
          </div>
          <span className="px-1.5 py-0.5 rounded bg-sky-950 text-sky-400 text-[10px] font-mono border border-sky-800">
            {chainInfo ? `${chainInfo.dof} DOF` : "6 DOF"}
          </span>
        </div>

        {/* 5-Tab Mode Navigation */}
        <div className="grid grid-cols-5 p-1.5 bg-slate-950/70 border-b border-slate-800 gap-1 text-[11px]">
          {[
            { id: "TRAJECTORY", label: "Trajectory", icon: TrendingUp },
            { id: "PID", label: "PID Tuning", icon: Gauge },
            { id: "IK", label: "Cartesian IK", icon: Target },
            { id: "FK", label: "Joint FK", icon: Sliders },
            { id: "MANIPULATION", label: "Manipulation", icon: Box },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-1.5 rounded flex flex-col items-center justify-center space-y-0.5 font-semibold transition ${activeTab === tab.id
                  ? "bg-amber-500 text-slate-950 shadow"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                  }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span className="text-[10px]">{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Scrollable Control Workspaces */}
        <div className="flex-1 overflow-y-auto p-3 space-y-4 text-xs">
          {/* ===================== TAB 1: TRAJECTORY PLANNING ===================== */}
          {activeTab === "TRAJECTORY" && (
            <div className="space-y-4">
              {/* Presets Bar */}
              <div className="space-y-1.5">
                <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                  Industrial Trajectory Presets
                </div>
                <div className="grid grid-cols-2 gap-1.5">
                  {trajPresets.map((t) => (
                    <button
                      key={t.name}
                      onClick={() => {
                        setWaypoints(t.waypoints);
                        addToast("info", "Preset Loaded", `Loaded '${t.name}'.`);
                      }}
                      className="p-1.5 bg-slate-950 hover:bg-slate-800 text-left border border-slate-800 rounded transition"
                    >
                      <div className="font-semibold text-slate-200 text-[10px] truncate">{t.name}</div>
                      <div className="text-[9px] text-slate-500 font-mono">{t.waypoints.length} waypoints</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Waypoints Configuration */}
              <div className="bg-slate-950/70 p-2.5 rounded border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-[11px] font-semibold text-slate-300">
                  <span>Waypoints (Joint Space [rad])</span>
                  <button
                    onClick={() => setWaypoints([...waypoints, [...jointAnglesRad]])}
                    className="px-1.5 py-0.5 bg-slate-800 hover:bg-slate-700 rounded text-[10px] flex items-center space-x-1 text-sky-400"
                  >
                    <Plus className="w-3 h-3" />
                    <span>Add Current Pose</span>
                  </button>
                </div>

                <div className="space-y-1 max-h-40 overflow-y-auto pr-1">
                  {waypoints.map((wp, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-1.5 bg-slate-900 rounded border border-slate-800/80 font-mono text-[10px]"
                    >
                      <span className="text-amber-400 font-bold w-7">WP{idx + 1}</span>
                      <span className="text-slate-300 flex-1 truncate text-center">
                        [{wp.map((v) => v.toFixed(2)).join(", ")}]
                      </span>
                      {waypoints.length > 2 && (
                        <button
                          onClick={() => setWaypoints(waypoints.filter((_, i) => i !== idx))}
                          className="text-slate-500 hover:text-rose-400 p-0.5"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Motion Constraints & Interpolation */}
              <div className="bg-slate-950/70 p-2.5 rounded border border-slate-800 space-y-2.5">
                <div className="text-[11px] font-semibold text-slate-300">Motion Profile & Constraints</div>

                <div>
                  <label className="text-[10px] text-slate-400">Interpolation Algorithm</label>
                  <select
                    value={interpolation}
                    onChange={(e) => setInterpolation(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-slate-200 text-xs font-mono mt-0.5"
                  >
                    <option value="quintic">Quintic Spline (C2 - Continuous Acceleration & Jerk)</option>
                    <option value="cubic">Cubic Spline (C1 - Continuous Velocity)</option>
                    <option value="trapezoidal">Linear / Trapezoidal Velocity Blend</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                      <span>v_max</span>
                      <span className="text-sky-400 font-bold">{vMax} rad/s</span>
                    </div>
                    <input
                      type="range"
                      min="0.5"
                      max="5.0"
                      step="0.1"
                      value={vMax}
                      onChange={(e) => setVMax(parseFloat(e.target.value))}
                      className="w-full accent-sky-500 cursor-pointer h-1.5 bg-slate-800 rounded mt-1"
                    />
                  </div>

                  <div>
                    <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                      <span>a_max</span>
                      <span className="text-amber-400 font-bold">{aMax} rad/s²</span>
                    </div>
                    <input
                      type="range"
                      min="1.0"
                      max="10.0"
                      step="0.5"
                      value={aMax}
                      onChange={(e) => setAMax(parseFloat(e.target.value))}
                      className="w-full accent-amber-500 cursor-pointer h-1.5 bg-slate-800 rounded mt-1"
                    />
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={handlePlanTrajectory}
                  disabled={isPlanning}
                  className="py-2 bg-slate-800 hover:bg-slate-700 text-sky-400 font-bold rounded flex items-center justify-center space-x-1.5 border border-slate-700 transition"
                >
                  {isPlanning ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <TrendingUp className="w-3.5 h-3.5" />}
                  <span>Plan Trajectory</span>
                </button>

                <button
                  onClick={handleExecuteTrajectory}
                  disabled={isExecuting}
                  className="py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded flex items-center justify-center space-x-1.5 transition shadow"
                >
                  {isExecuting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                  <span>Execute on Sim</span>
                </button>
              </div>

              {plannedTraj && (
                <div className="p-2 bg-sky-950/40 border border-sky-800 rounded font-mono text-[10px] text-sky-300 flex justify-between">
                  <span>Planned: {plannedTraj.num_samples} samples</span>
                  <span className="font-bold">{plannedTraj.total_duration}s duration</span>
                </div>
              )}

              {/* Execution Performance Results */}
              {execResult && (
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800 space-y-2 font-mono text-[10px]">
                  <div className="flex justify-between text-slate-300 font-sans text-[11px] font-semibold">
                    <span>Tracking Performance</span>
                    <span className="text-emerald-400 font-bold">500 Hz Feedback</span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-center">
                    <div className="bg-slate-900 p-1.5 rounded border border-slate-800">
                      <div className="text-slate-500 text-[9px]">Position RMSE</div>
                      <div className="text-xs font-bold text-emerald-400 mt-0.5">
                        {(execResult.overall_position_rmse_rad * 1000).toFixed(2)} mrad
                      </div>
                    </div>
                    <div className="bg-slate-900 p-1.5 rounded border border-slate-800">
                      <div className="text-slate-500 text-[9px]">Max Tracking Error</div>
                      <div className="text-xs font-bold text-sky-400 mt-0.5">
                        {(execResult.max_tracking_error_rad * 1000).toFixed(2)} mrad
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ===================== TAB 2: PID CONTROL & STEP RESPONSE ===================== */}
          {activeTab === "PID" && (
            <div className="space-y-4">
              <div className="bg-slate-950/70 p-2.5 rounded border border-slate-800 space-y-2">
                <div className="flex justify-between items-center text-[11px] font-semibold text-slate-300">
                  <span>Joint Actuator Gains Tuning</span>
                  <select
                    value={selectedJoint}
                    onChange={(e) => setSelectedJoint(parseInt(e.target.value))}
                    className="bg-slate-900 border border-slate-800 rounded px-1.5 py-0.5 text-xs text-amber-400 font-mono"
                  >
                    {[0, 1, 2, 3, 4, 5].map((j) => (
                      <option key={j} value={j}>Joint {j + 1}</option>
                    ))}
                  </select>
                </div>

                {/* PID Sliders */}
                <div className="space-y-2">
                  <div>
                    <div className="flex justify-between text-[10px] font-mono text-slate-400">
                      <span>Proportional (Kp)</span>
                      <span className="text-sky-400 font-bold">{kp}</span>
                    </div>
                    <input
                      type="range"
                      min="10"
                      max="600"
                      step="10"
                      value={kp}
                      onChange={(e) => setKp(parseFloat(e.target.value))}
                      className="w-full accent-sky-500 cursor-pointer h-1.5 bg-slate-800 rounded"
                    />
                  </div>

                  <div>
                    <div className="flex justify-between text-[10px] font-mono text-slate-400">
                      <span>Integral (Ki)</span>
                      <span className="text-amber-400 font-bold">{ki}</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="20"
                      step="0.5"
                      value={ki}
                      onChange={(e) => setKi(parseFloat(e.target.value))}
                      className="w-full accent-amber-500 cursor-pointer h-1.5 bg-slate-800 rounded"
                    />
                  </div>

                  <div>
                    <div className="flex justify-between text-[10px] font-mono text-slate-400">
                      <span>Derivative (Kd)</span>
                      <span className="text-emerald-400 font-bold">{kd}</span>
                    </div>
                    <input
                      type="range"
                      min="1"
                      max="80"
                      step="1"
                      value={kd}
                      onChange={(e) => setKd(parseFloat(e.target.value))}
                      className="w-full accent-emerald-500 cursor-pointer h-1.5 bg-slate-800 rounded"
                    />
                  </div>
                </div>
              </div>

              {/* Step Response Controls */}
              <div className="bg-slate-950/70 p-2.5 rounded border border-slate-800 space-y-2">
                <div className="text-[11px] font-semibold text-slate-300">Closed-Loop Step Response Test</div>
                <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
                  <div>
                    <span className="text-slate-500">Step Amplitude: </span>
                    <span className="text-slate-200 font-bold">{stepAmp} rad</span>
                    <input
                      type="range"
                      min="0.1"
                      max="0.8"
                      step="0.05"
                      value={stepAmp}
                      onChange={(e) => setStepAmp(parseFloat(e.target.value))}
                      className="w-full accent-emerald-500 cursor-pointer h-1.5 bg-slate-800 rounded mt-1"
                    />
                  </div>
                  <div>
                    <span className="text-slate-500">Duration: </span>
                    <span className="text-slate-200 font-bold">{stepDuration}s</span>
                    <input
                      type="range"
                      min="1.0"
                      max="5.0"
                      step="0.5"
                      value={stepDuration}
                      onChange={(e) => setStepDuration(parseFloat(e.target.value))}
                      className="w-full accent-emerald-500 cursor-pointer h-1.5 bg-slate-800 rounded mt-1"
                    />
                  </div>
                </div>

                <button
                  onClick={handleRunStepResponse}
                  disabled={isTestingStep}
                  className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded flex items-center justify-center space-x-1.5 transition shadow"
                >
                  {isTestingStep ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <BarChart3 className="w-3.5 h-3.5" />}
                  <span>Evaluate Step Response</span>
                </button>
              </div>

              {/* Step Response Analysis Result */}
              {stepResponse && (
                <div className="bg-slate-900/90 p-2.5 rounded border border-slate-800 space-y-2 font-mono text-[10px]">
                  <div className="flex justify-between items-center text-slate-300 font-sans text-[11px] font-semibold">
                    <span>Response Stability</span>
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${stepResponse.is_stable
                        ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                        : "bg-rose-950 text-rose-400 border border-rose-800"
                        }`}
                    >
                      {stepResponse.stability}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-1.5 text-center">
                    <div className="bg-slate-950 p-1.5 rounded border border-slate-800">
                      <div className="text-slate-500 text-[9px]">Overshoot (Mp)</div>
                      <div className="font-bold text-amber-400 mt-0.5">{stepResponse.overshoot_percent}%</div>
                    </div>
                    <div className="bg-slate-950 p-1.5 rounded border border-slate-800">
                      <div className="text-slate-500 text-[9px]">Rise Time (tr)</div>
                      <div className="font-bold text-sky-400 mt-0.5">{stepResponse.rise_time_seconds}s</div>
                    </div>
                    <div className="bg-slate-950 p-1.5 rounded border border-slate-800">
                      <div className="text-slate-500 text-[9px]">Settling Time (ts)</div>
                      <div className="font-bold text-slate-200 mt-0.5">{stepResponse.settling_time_seconds}s</div>
                    </div>
                    <div className="bg-slate-950 p-1.5 rounded border border-slate-800">
                      <div className="text-slate-500 text-[9px]">Steady-State Error</div>
                      <div className="font-bold text-emerald-400 mt-0.5">
                        {(stepResponse.steady_state_error_rad * 1000).toFixed(2)} mrad
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ===================== TAB 3: CARTESIAN INVERSE KINEMATICS ===================== */}
          {activeTab === "IK" && (
            <div className="space-y-4">
              <div className="bg-slate-950/70 p-2.5 rounded border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-[11px] font-semibold text-slate-300">
                  <span className="flex items-center space-x-1">
                    <Compass className="w-3.5 h-3.5 text-sky-400" />
                    <span>Target Position (X, Y, Z [m])</span>
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {(["X", "Y", "Z"] as const).map((axis, i) => (
                    <div key={axis} className="bg-slate-900 p-2 rounded border border-slate-800/80">
                      <div className="text-[10px] text-slate-400 font-mono flex justify-between">
                        <span className="font-bold text-sky-400">{axis}</span>
                        <span>[m]</span>
                      </div>
                      <input
                        type="number"
                        step="0.01"
                        value={targetPos[i]}
                        onChange={(e) => {
                          const val = parseFloat(e.target.value) || 0;
                          const next = [...targetPos] as [number, number, number];
                          next[i] = val;
                          setTargetPos(next);
                        }}
                        className="w-full bg-slate-950 border border-slate-800 rounded px-1.5 py-1 text-slate-100 font-mono text-xs mt-1"
                      />
                    </div>
                  ))}
                </div>
              </div>

              {/* Target Orientation */}
              <div className="bg-slate-950/70 p-2.5 rounded border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-[11px] font-semibold text-slate-300">
                  <span className="flex items-center space-x-1">
                    <RotateCcw className="w-3.5 h-3.5 text-amber-400" />
                    <span>Target Orientation (RPY [deg])</span>
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { label: "Roll", idx: 0 },
                    { label: "Pitch", idx: 1 },
                    { label: "Yaw", idx: 2 },
                  ].map((item) => (
                    <div key={item.label} className="bg-slate-900 p-2 rounded border border-slate-800/80">
                      <div className="text-[10px] text-slate-400 font-mono flex justify-between">
                        <span className="font-bold text-amber-400">{item.label}</span>
                        <span>[deg]</span>
                      </div>
                      <input
                        type="number"
                        step="5"
                        value={targetRpyDeg[item.idx]}
                        onChange={(e) => {
                          const val = parseFloat(e.target.value) || 0;
                          const next = [...targetRpyDeg] as [number, number, number];
                          next[item.idx] = val;
                          setTargetRpyDeg(next);
                        }}
                        className="w-full bg-slate-950 border border-slate-800 rounded px-1.5 py-1 text-slate-100 font-mono text-xs mt-1"
                      />
                    </div>
                  ))}
                </div>
              </div>

              {/* Pose Presets */}
              <div className="space-y-1.5">
                <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Target Presets</div>
                <div className="grid grid-cols-2 gap-1.5">
                  {posePresets.map((p) => (
                    <button
                      key={p.name}
                      onClick={() => {
                        setTargetPos(p.target_pos);
                        if (p.joints_rad && p.joints_rad.length === 6) {
                          setJointAnglesRad(p.joints_rad);
                          triggerFK(p.joints_rad);
                        }
                      }}
                      className="p-1.5 bg-slate-900 hover:bg-slate-800 text-left border border-slate-800 rounded transition"
                    >
                      <div className="font-semibold text-slate-200 text-[10px] truncate">{p.name}</div>
                      <div className="text-[9px] font-mono text-slate-500">[{p.target_pos.join(", ")}]m</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Solver Options */}
              <div className="flex items-center justify-between text-[10px] font-mono bg-slate-950 p-2 rounded border border-slate-800">
                <select
                  value={solverMethod}
                  onChange={(e) => setSolverMethod(e.target.value)}
                  className="bg-slate-900 border border-slate-800 rounded px-1.5 py-0.5 text-slate-200"
                >
                  <option value="damped_least_squares">Damped Least Squares (DLS)</option>
                  <option value="pseudo_inverse">Pseudo-Inverse</option>
                  <option value="jacobian_transpose">Jacobian Transpose</option>
                </select>
                <label className="flex items-center space-x-1 cursor-pointer text-slate-400">
                  <input
                    type="checkbox"
                    checked={continuousSolve}
                    onChange={(e) => setContinuousSolve(e.target.checked)}
                    className="accent-amber-500 rounded"
                  />
                  <span>Live</span>
                </label>
              </div>

              {/* Solve Button & Convergence Card */}
              <button
                onClick={triggerIK}
                disabled={isSolving}
                className="w-full py-2 bg-sky-600 hover:bg-sky-500 text-white font-bold rounded flex items-center justify-center space-x-1.5 transition shadow"
              >
                {isSolving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5" />}
                <span>Solve Inverse Kinematics</span>
              </button>

              {ikResult && (
                <div className="bg-slate-900/90 p-2.5 rounded border border-slate-800 space-y-2 font-mono text-[10px]">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-semibold text-slate-300">Status</span>
                    <span
                      className={`px-1.5 py-0.5 rounded font-bold ${ikResult.converged ? "bg-emerald-950 text-emerald-400" : "bg-rose-950 text-rose-400"
                        }`}
                    >
                      {ikResult.status}
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-1 text-center">
                    <div className="bg-slate-950 p-1 rounded">
                      <div className="text-slate-500 text-[9px]">Pos Err</div>
                      <div className="text-slate-200 font-bold">{ikResult.position_error_mm} mm</div>
                    </div>
                    <div className="bg-slate-950 p-1 rounded">
                      <div className="text-slate-500 text-[9px]">Angle Err</div>
                      <div className="text-slate-200 font-bold">{ikResult.orientation_error_deg}&deg;</div>
                    </div>
                    <div className="bg-slate-950 p-1 rounded">
                      <div className="text-slate-500 text-[9px]">Iters</div>
                      <div className="text-slate-200 font-bold">{ikResult.iterations}</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ===================== TAB 4: FORWARD KINEMATICS SLIDERS ===================== */}
          {activeTab === "FK" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-slate-300">Joint Sliders</span>
                <button
                  onClick={() => {
                    const zeros = [0, 0, 0, 0, 0, 0];
                    setJointAnglesRad(zeros);
                    triggerFK(zeros);
                  }}
                  className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[10px]"
                >
                  Zero All
                </button>
              </div>

              {chainInfo?.joints.map((joint, idx) => {
                const deg = Math.round((jointAnglesRad[idx] * 180.0) / Math.PI);
                return (
                  <div key={joint.name} className="bg-slate-950/70 p-2 rounded border border-slate-800 space-y-1">
                    <div className="flex justify-between items-center text-[10px] font-mono">
                      <span className="font-bold text-slate-300">{joint.name}</span>
                      <span className="text-amber-400 font-bold">{deg}&deg;</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-[9px] font-mono text-slate-500 w-8 text-right">{joint.lower_limit_deg}&deg;</span>
                      <input
                        type="range"
                        min={joint.lower_limit_deg}
                        max={joint.upper_limit_deg}
                        step="1"
                        value={deg}
                        onChange={(e) => {
                          const rad = (parseFloat(e.target.value) * Math.PI) / 180.0;
                          const next = [...jointAnglesRad];
                          next[idx] = rad;
                          setJointAnglesRad(next);
                          triggerFK(next);
                        }}
                        className="flex-1 accent-amber-500 cursor-pointer h-1.5 bg-slate-800 rounded"
                      />
                      <span className="text-[9px] font-mono text-slate-500 w-8">{joint.upper_limit_deg}&deg;</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* ===================== TAB 5: OBJECT MANIPULATION & GRASPING ===================== */}
          {activeTab === "MANIPULATION" && (
            <div className="space-y-4">
              {/* Gripper Actuation Card */}
              <div className="bg-slate-950/70 p-3 rounded border border-slate-800 space-y-3">
                <div className="flex items-center justify-between text-[11px] font-semibold text-slate-200">
                  <span className="flex items-center space-x-1.5">
                    <Box className="w-4 h-4 text-amber-400" />
                    <span>Parallel-Jaw Gripper Control</span>
                  </span>
                  <span
                    className={`px-1.5 py-0.5 rounded text-[9px] font-bold font-mono ${
                      gripperStatus.is_grasping
                        ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                        : "bg-slate-800 text-slate-400"
                    }`}
                  >
                    {gripperStatus.is_grasping ? "GRASP SECURED" : "OPEN / IDLE"}
                  </span>
                </div>

                {/* Squeeze Force Slider */}
                <div className="space-y-1">
                  <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                    <span>Squeeze Force Command</span>
                    <span className="text-amber-400 font-bold">{gripperForce.toFixed(1)} N</span>
                  </div>
                  <input
                    type="range"
                    min="5"
                    max="35"
                    step="1"
                    value={gripperForce}
                    onChange={(e) => setGripperForce(parseFloat(e.target.value))}
                    className="w-full accent-amber-500 cursor-pointer h-1.5 bg-slate-800 rounded"
                  />
                  <div className="flex justify-between text-[9px] text-slate-600 font-mono">
                    <span>5 N (Gentle)</span>
                    <span>35 N (Heavy Grip)</span>
                  </div>
                </div>

                {/* Gripper Buttons */}
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={handleGripperClose}
                    className="py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded flex items-center justify-center space-x-1 transition shadow"
                  >
                    <Box className="w-3.5 h-3.5" />
                    <span>Grip / Squeeze</span>
                  </button>
                  <button
                    onClick={handleGripperOpen}
                    className="py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold rounded flex items-center justify-center space-x-1 border border-slate-700 transition"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Release / Open</span>
                  </button>
                </div>

                {/* Live Finger Force Telemetry */}
                <div className="grid grid-cols-3 gap-1.5 text-center font-mono text-[10px]">
                  <div className="bg-slate-900 p-1.5 rounded border border-slate-800">
                    <div className="text-slate-500 text-[9px]">Aperture</div>
                    <div className="text-slate-200 font-bold mt-0.5">{(gripperStatus.width * 1000).toFixed(1)} mm</div>
                  </div>
                  <div className="bg-slate-900 p-1.5 rounded border border-slate-800">
                    <div className="text-slate-500 text-[9px]">Left Jaw Fn</div>
                    <div className="text-emerald-400 font-bold mt-0.5">{gripperStatus.left_force.toFixed(1)} N</div>
                  </div>
                  <div className="bg-slate-900 p-1.5 rounded border border-slate-800">
                    <div className="text-slate-500 text-[9px]">Right Jaw Fn</div>
                    <div className="text-emerald-400 font-bold mt-0.5">{gripperStatus.right_force.toFixed(1)} N</div>
                  </div>
                </div>
              </div>

              {/* Autonomous Pick & Place Card */}
              <div className="bg-slate-950/70 p-3 rounded border border-slate-800 space-y-2.5">
                <div className="flex items-center justify-between text-[11px] font-semibold text-slate-200">
                  <span className="flex items-center space-x-1.5">
                    <TrendingUp className="w-4 h-4 text-sky-400" />
                    <span>Autonomous Pick & Place Sequencer</span>
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">MuJoCo Physics</span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[10px]">
                  <div>
                    <label className="text-slate-400 font-semibold block mb-1">Pick Target [m]</label>
                    <div className="grid grid-cols-3 gap-1 font-mono">
                      {[0, 1, 2].map((i) => (
                        <input
                          key={i}
                          type="number"
                          step="0.02"
                          value={pickPos[i]}
                          onChange={(e) => {
                            const val = parseFloat(e.target.value) || 0;
                            const next = [...pickPos] as [number, number, number];
                            next[i] = val;
                            setPickPos(next);
                          }}
                          className="bg-slate-900 border border-slate-800 rounded px-1 py-0.5 text-center text-slate-200"
                        />
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="text-slate-400 font-semibold block mb-1">Place Target [m]</label>
                    <div className="grid grid-cols-3 gap-1 font-mono">
                      {[0, 1, 2].map((i) => (
                        <input
                          key={i}
                          type="number"
                          step="0.02"
                          value={placePos[i]}
                          onChange={(e) => {
                            const val = parseFloat(e.target.value) || 0;
                            const next = [...placePos] as [number, number, number];
                            next[i] = val;
                            setPlacePos(next);
                          }}
                          className="bg-slate-900 border border-slate-800 rounded px-1 py-0.5 text-center text-slate-200"
                        />
                      ))}
                    </div>
                  </div>
                </div>

                {/* Lift Height Setting */}
                <div className="space-y-1">
                  <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                    <span>Vertical Lift Clearance</span>
                    <span className="text-sky-400 font-bold">{(liftHeight * 100).toFixed(0)} cm</span>
                  </div>
                  <input
                    type="range"
                    min="0.08"
                    max="0.25"
                    step="0.01"
                    value={liftHeight}
                    onChange={(e) => setLiftHeight(parseFloat(e.target.value))}
                    className="w-full accent-sky-500 cursor-pointer h-1.5 bg-slate-800 rounded"
                  />
                </div>

                <button
                  onClick={handleExecutePickAndPlace}
                  disabled={isExecutingPnP}
                  className="w-full py-2 bg-sky-600 hover:bg-sky-500 text-white font-bold rounded flex items-center justify-center space-x-1.5 transition shadow"
                >
                  {isExecutingPnP ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Play className="w-3.5 h-3.5" />
                  )}
                  <span>Execute Physics Pick & Place Cycle</span>
                </button>

                {pnpResult && (
                  <div className="p-2 bg-slate-900 rounded border border-slate-800 text-[10px] space-y-1 font-mono">
                    <div className="flex justify-between items-center text-slate-300">
                      <span>Status: {pnpResult.success ? "COMPLETED" : "FAILED"}</span>
                      <span className="text-emerald-400 font-bold">{pnpResult.execution_time_s}s</span>
                    </div>
                    <div className="text-slate-400 flex justify-between">
                      <span>Friction Hold:</span>
                      <span className={pnpResult.friction_hold_verified ? "text-emerald-400 font-bold" : "text-amber-400"}>
                        {pnpResult.friction_hold_verified ? "VERIFIED (NON-SLIP)" : "SLIPPED"}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* 5 Physical Verification Experiments Card */}
              <div className="bg-slate-950/70 p-3 rounded border border-slate-800 space-y-2.5">
                <div className="flex items-center justify-between text-[11px] font-semibold text-slate-200">
                  <span className="flex items-center space-x-1.5">
                    <Zap className="w-4 h-4 text-emerald-400" />
                    <span>5 Controlled Verification Experiments</span>
                  </span>
                  <button
                    onClick={handleRunBenchmarks}
                    disabled={isRunningBenchmarks}
                    className="px-2 py-0.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[10px] font-bold flex items-center space-x-1"
                  >
                    {isRunningBenchmarks ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
                    <span>Run Suite</span>
                  </button>
                </div>

                <div className="space-y-1.5 text-[10px]">
                  {[
                    { id: 1, name: "1. Robot Touching Object (Onset, Fn > 0)" },
                    { id: 2, name: "2. Obstacle Collision & Stability (Impulse J)" },
                    { id: 3, name: "3. Bilateral Contact Grasping (Fn_left, Fn_right)" },
                    { id: 4, name: "4. Friction-Based Lifting (>= 10cm, No Parenting)" },
                    { id: 5, name: "5. Controlled Release & Gravity Free-Fall" },
                  ].map((item, idx) => {
                    const bench = manipBenchmarks?.results?.[idx];
                    return (
                      <div
                        key={item.id}
                        className="p-1.5 bg-slate-900 rounded border border-slate-800 flex items-center justify-between font-mono"
                      >
                        <span className="text-slate-300 truncate">{item.name}</span>
                        {bench ? (
                          <span
                            className={`px-1.5 py-0.2 rounded font-bold text-[9px] flex items-center space-x-0.5 ${
                              bench.passed ? "text-emerald-400 bg-emerald-950" : "text-rose-400 bg-rose-950"
                            }`}
                          >
                            {bench.passed ? <CheckCircle2 className="w-2.5 h-2.5" /> : <XCircle className="w-2.5 h-2.5" />}
                            <span>{bench.passed ? "PASS" : "FAIL"}</span>
                          </span>
                        ) : (
                          <span className="text-slate-600 text-[9px]">PENDING</span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* Simulation Dispatch Action */}
          <button
            onClick={handleSendToSimulation}
            className="w-full py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded flex items-center justify-center space-x-1.5 transition shadow mt-2"
          >
            <Play className="w-3.5 h-3.5" />
            <span>Apply Current Configuration to MuJoCo</span>
          </button>
        </div>
      </div>

      {/* CENTER: 3D VIEWPORT WITH REAL-TIME KINEMATICS HUD */}
      <div className="flex-1 relative flex flex-col">
        {/* Floating Real-Time HUD */}
        {fkResult && (
          <div className="absolute top-3 left-3 z-10 bg-slate-900/90 backdrop-blur border border-slate-800/90 rounded px-3 py-2 text-xs font-mono space-y-1 shadow-lg pointer-events-none">
            <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
              End-Effector Pose (Link 6)
            </div>
            <div className="flex space-x-4 text-slate-200 text-[11px]">
              <div>
                <span className="text-slate-500">POS: </span>
                <span className="text-emerald-400 font-bold">
                  [{fkResult.position[0].toFixed(3)}, {fkResult.position[1].toFixed(3)}, {fkResult.position[2].toFixed(3)}]m
                </span>
              </div>
              <div>
                <span className="text-slate-500">RPY: </span>
                <span className="text-sky-400 font-bold">
                  [{fkResult.rpy_deg[0].toFixed(1)}&deg;, {fkResult.rpy_deg[1].toFixed(1)}&deg;, {fkResult.rpy_deg[2].toFixed(1)}&deg;]
                </span>
              </div>
            </div>
          </div>
        )}

        <Viewport3D />
      </div>

      {/* RIGHT PANEL: Diagnostics, SVD & Telemetry Inspector */}
      <div className="w-[380px] bg-slate-900 border-l border-slate-800 flex flex-col overflow-hidden text-xs">
        {/* Tab Headers */}
        <div className="flex border-b border-slate-800 bg-slate-950/70 p-1 gap-1 text-[11px]">
          {[
            { id: "TELEMETRY", label: "Telemetry", icon: Activity },
            { id: "CONTACTS", label: "Contacts", icon: ShieldAlert },
            { id: "METRICS", label: "SVD Metrics", icon: Gauge },
            { id: "TRANSFORM", label: "SE(3)", icon: Move3d },
            { id: "JACOBIAN", label: "Jacobian", icon: Compass },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setInspectorTab(tab.id as any)}
                className={`flex-1 py-1.5 px-1.5 rounded font-medium flex items-center justify-center space-x-1 transition ${inspectorTab === tab.id
                  ? "bg-slate-800 text-sky-400 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
                  }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span className="truncate">{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Inspector Tab Content */}
        <div className="flex-1 overflow-y-auto p-3 space-y-4 font-mono text-[11px]">
          {/* TAB 1: TELEMETRY & STEP RESPONSE OSCILLOSCOPE */}
          {inspectorTab === "TELEMETRY" && (
            <div className="space-y-3">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">
                Control Performance & Transient Response
              </div>

              {stepResponse ? (
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800 space-y-2">
                  <div className="text-[10px] text-slate-400 flex justify-between font-sans">
                    <span className="font-semibold text-slate-200">Joint {selectedJoint + 1} Transient Curve</span>
                    <span className="text-emerald-400 font-mono">y(t) vs y_target</span>
                  </div>

                  {/* SVG Oscilloscope */}
                  <div className="h-32 w-full bg-slate-900 rounded border border-slate-800/80 relative overflow-hidden flex items-end">
                    <svg className="w-full h-full">
                      {/* Grid Lines */}
                      <line x1="0" y1="25%" x2="100%" y2="25%" stroke="#334155" strokeDasharray="3 3" />
                      <line x1="0" y1="50%" x2="100%" y2="50%" stroke="#334155" strokeDasharray="3 3" />
                      <line x1="0" y1="75%" x2="100%" y2="75%" stroke="#334155" strokeDasharray="3 3" />

                      {/* Step Target Horizontal Line */}
                      <line x1="0" y1="30%" x2="100%" y2="30%" stroke="#f59e0b" strokeWidth="1.5" strokeDasharray="4 2" />

                      {/* Actual Step Curve Polyline */}
                      {stepResponse.positions.length > 1 && (
                        <polyline
                          fill="none"
                          stroke="#10b981"
                          strokeWidth="2"
                          points={stepResponse.positions
                            .map((p, idx) => {
                              const x = (idx / (stepResponse.positions.length - 1)) * 340;
                              const minVal = stepResponse.initial_position_rad;
                              const maxVal = stepResponse.target_position_rad * 1.35;
                              const range = maxVal - minVal || 1;
                              const norm = (p - minVal) / range;
                              const y = 120 - Math.min(115, Math.max(5, norm * 110));
                              return `${x},${y}`;
                            })
                            .join(" ")}
                        />
                      )}
                    </svg>
                  </div>

                  <div className="flex justify-between text-[9px] text-slate-500">
                    <span>t = 0.0s</span>
                    <span>t = {stepResponse.settling_time_seconds}s</span>
                    <span>t = {stepDuration}s</span>
                  </div>
                </div>
              ) : (
                <div className="p-3 bg-slate-950 rounded border border-slate-800 text-slate-500 text-center font-sans">
                  Execute a trajectory or run a Step Response test to record transient telemetry curves.
                </div>
              )}

              {/* Trajectory Sampling Telemetry Table */}
              {execResult && (
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800 space-y-1.5 font-sans">
                  <div className="text-[10px] text-slate-400 font-semibold uppercase">Per-Joint Tracking Errors</div>
                  <div className="space-y-1 font-mono text-[10px]">
                    {execResult.joint_rmse_rad.map((err, idx) => (
                      <div key={idx} className="flex justify-between items-center bg-slate-900 p-1.5 rounded">
                        <span className="text-slate-400">Joint {idx + 1} RMSE</span>
                        <span className="text-sky-400 font-bold">{(err * 1000).toFixed(2)} mrad</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: METRICS & SVD */}
          {inspectorTab === "METRICS" && fkResult?.jacobian_analysis && (
            <div className="space-y-3">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Yoshikawa Manipulability</div>
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                  <div className="text-slate-500 text-[10px]">Manipulability (w)</div>
                  <div className="text-base font-bold text-sky-400 mt-1">
                    {fkResult.jacobian_analysis.manipulability.toFixed(4)}
                  </div>
                </div>
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                  <div className="text-slate-500 text-[10px]">Condition No. (&kappa;)</div>
                  <div className="text-base font-bold text-amber-400 mt-1">
                    {fkResult.jacobian_analysis.condition_number.toFixed(1)}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: SE(3) MATRIX */}
          {inspectorTab === "TRANSFORM" && fkResult && (
            <div className="space-y-3">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">T_0_ee &isin; SE(3)</div>
              <div className="bg-slate-950 p-3 rounded border border-slate-800 overflow-x-auto">
                <table className="w-full text-center border-collapse">
                  <tbody>
                    {fkResult.transform_matrix.map((row, rIdx) => (
                      <tr key={rIdx} className="border-b border-slate-900/60 last:border-b-0">
                        {row.map((val, cIdx) => (
                          <td
                            key={cIdx}
                            className={`p-1.5 ${cIdx === 3 ? "text-emerald-400 font-bold bg-emerald-950/20" : "text-sky-300"
                              }`}
                          >
                            {val.toFixed(4)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 4: JACOBIAN */}
          {inspectorTab === "JACOBIAN" && fkResult?.jacobian_analysis && (
            <div className="space-y-3">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Geometric Jacobian J(q)</div>
              <div className="bg-slate-950 p-2 rounded border border-slate-800 overflow-x-auto">
                <table className="w-full text-[10px] text-right border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-500">
                      <th className="p-1 text-left">Row</th>
                      {chainInfo?.joints.map((j) => (
                        <th key={j.name} className="p-1">{j.name.replace("joint_", "J")}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {fkResult.jacobian_analysis.jacobian.map((row, rIdx) => (
                      <tr key={rIdx} className="border-b border-slate-900/60 font-mono">
                        <td className="p-1 text-left text-slate-500 font-bold">
                          {rIdx < 3 ? `v_${["x", "y", "z"][rIdx]}` : `w_${["x", "y", "z"][rIdx - 3]}`}
                        </td>
                        {row.map((val, cIdx) => (
                          <td
                            key={cIdx}
                            className={`p-1 ${Math.abs(val) < 1e-4 ? "text-slate-700" : rIdx < 3 ? "text-sky-300" : "text-amber-300"
                              }`}
                          >
                            {val.toFixed(3)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 5: ACTIVE CONTACT MANIFOLDS & COLLISION EVENT LOG */}
          {inspectorTab === "CONTACTS" && (
            <div className="space-y-4">
              {/* Active Contacts Section */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-[10px] text-slate-400 font-sans font-semibold uppercase">
                  <span className="flex items-center space-x-1">
                    <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
                    <span>Active Contact Manifolds</span>
                  </span>
                  <span className="text-emerald-400 font-mono">
                    {telemetry?.contacts?.length || 0} active
                  </span>
                </div>

                {(!telemetry?.contacts || telemetry.contacts.length === 0) ? (
                  <div className="p-3 bg-slate-950 rounded border border-slate-800/80 text-center text-slate-500 text-[10px] font-sans">
                    No active contact manifolds currently engaged.
                  </div>
                ) : (
                  <div className="space-y-1.5 max-h-56 overflow-y-auto">
                    {telemetry.contacts.map((c, idx) => (
                      <div
                        key={idx}
                        className="p-2 bg-slate-950 rounded border border-slate-800 text-[10px] space-y-1"
                      >
                        <div className="flex justify-between items-center font-bold">
                          <span className="text-slate-200 truncate max-w-[190px]">
                            {c.geom1} &harr; {c.geom2}
                          </span>
                          <span
                            className={`px-1 py-0.2 rounded text-[9px] font-mono ${
                              c.category === "robot_object"
                                ? "bg-amber-950 text-amber-400 border border-amber-800"
                                : c.category === "robot_env"
                                ? "bg-rose-950 text-rose-400 border border-rose-800"
                                : c.category === "object_env"
                                ? "bg-sky-950 text-sky-400 border border-sky-800"
                                : "bg-slate-800 text-slate-400"
                            }`}
                          >
                            {c.category || "contact"}
                          </span>
                        </div>

                        <div className="grid grid-cols-3 gap-1 font-mono text-[9px] text-slate-400 pt-0.5">
                          <div>
                            Fn: <span className="text-emerald-400 font-bold">{c.force.toFixed(2)} N</span>
                          </div>
                          <div>
                            Ft: <span className="text-sky-400 font-bold">{(c.friction_force || 0).toFixed(2)} N</span>
                          </div>
                          <div>
                            Slip:{" "}
                            <span
                              className={
                                c.slip_state === "slipping"
                                  ? "text-rose-400 font-bold"
                                  : "text-emerald-400 font-bold"
                              }
                            >
                              {c.slip_state || "sticking"}
                            </span>
                          </div>
                        </div>

                        {c.position && (
                          <div className="text-[9px] text-slate-500 font-mono">
                            Pos: [{c.position[0].toFixed(3)}, {c.position[1].toFixed(3)}, {c.position[2].toFixed(3)}]
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Collision Events Log Section */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-[10px] text-slate-400 font-sans font-semibold uppercase">
                  <span>Dynamic Collision Event Log</span>
                  <span className="text-slate-500 font-mono">{collisionEvents.length} events</span>
                </div>

                {collisionEvents.length === 0 ? (
                  <div className="p-3 bg-slate-950 rounded border border-slate-800/80 text-center text-slate-500 text-[10px] font-sans">
                    No collision onset or impact events recorded yet.
                  </div>
                ) : (
                  <div className="space-y-1 max-h-52 overflow-y-auto font-mono text-[9px]">
                    {collisionEvents.slice(-10).reverse().map((ev, idx) => (
                      <div
                        key={idx}
                        className="p-1.5 bg-slate-950 rounded border border-slate-800 flex items-center justify-between"
                      >
                        <div>
                          <div className="text-slate-200 font-bold truncate max-w-[200px]">
                            {ev.geom1} &harr; {ev.geom2}
                          </div>
                          <div className="text-slate-500 text-[8px]">
                            t={ev.timestamp.toFixed(3)}s &bull; {ev.event_type} &bull; J={ev.impulse.toFixed(4)} Ns
                          </div>
                        </div>
                        <div className="text-right">
                          <span className="text-amber-400 font-bold">{ev.normal_force.toFixed(1)} N</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
