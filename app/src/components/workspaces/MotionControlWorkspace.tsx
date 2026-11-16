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
} from "lucide-react";

export const MotionControlWorkspace: React.FC = () => {
  const { addToast } = useAppStore();

  // Navigation / Mode Switcher
  const [activeTab, setActiveTab] = useState<"IK" | "FK" | "TRAJECTORY" | "PID">("TRAJECTORY");
  const [inspectorTab, setInspectorTab] = useState<"METRICS" | "TRANSFORM" | "JACOBIAN" | "TELEMETRY">("TELEMETRY");

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

        {/* 4-Tab Mode Navigation */}
        <div className="grid grid-cols-4 p-1.5 bg-slate-950/70 border-b border-slate-800 gap-1 text-[11px]">
          {[
            { id: "TRAJECTORY", label: "Trajectory", icon: TrendingUp },
            { id: "PID", label: "PID Control", icon: Gauge },
            { id: "IK", label: "Cartesian IK", icon: Target },
            { id: "FK", label: "Joint FK", icon: Sliders },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-1.5 rounded flex flex-col items-center justify-center space-y-0.5 font-semibold transition ${
                  activeTab === tab.id
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
                      className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        stepResponse.is_stable
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
                      className={`px-1.5 py-0.5 rounded font-bold ${
                        ikResult.converged ? "bg-emerald-950 text-emerald-400" : "bg-rose-950 text-rose-400"
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
            { id: "METRICS", label: "SVD Metrics", icon: Gauge },
            { id: "TRANSFORM", label: "SE(3) Matrix", icon: Move3d },
            { id: "JACOBIAN", label: "Jacobian", icon: Compass },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setInspectorTab(tab.id as any)}
                className={`flex-1 py-1.5 px-1.5 rounded font-medium flex items-center justify-center space-x-1 transition ${
                  inspectorTab === tab.id
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
                            className={`p-1.5 ${
                              cIdx === 3 ? "text-emerald-400 font-bold bg-emerald-950/20" : "text-sky-300"
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
                            className={`p-1 ${
                              Math.abs(val) < 1e-4 ? "text-slate-700" : rIdx < 3 ? "text-sky-300" : "text-amber-300"
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
        </div>
      </div>
    </div>
  );
};
