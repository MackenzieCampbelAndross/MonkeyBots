import React, { useState, useEffect, useCallback } from "react";
import { Viewport3D } from "../Viewport3D";
import { useAppStore } from "../../store/useAppStore";
import { simWebSocket } from "../../services/websocket";
import {
  fetchKinematicChain,
  calculateFK,
  calculateIK,
  fetchPosePresets,
} from "../../services/api";
import type {
  KinematicChainInfo,
  FKResultData,
  IKResultData,
  PosePreset,
} from "../../types/api";
import {
  Move3d,
  Play,
  RotateCcw,
  Target,
  Sliders,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Activity,
  Layers,
  Compass,
  Zap,
  RefreshCw,
} from "lucide-react";

export const MotionControlWorkspace: React.FC = () => {
  const { addToast } = useAppStore();

  // Robot and Kinematic Chain State
  const [chainInfo, setChainInfo] = useState<KinematicChainInfo | null>(null);
  const [activeTab, setActiveTab] = useState<"FK" | "IK">("IK");
  const [inspectorTab, setInspectorTab] = useState<"METRICS" | "TRANSFORM" | "JACOBIAN" | "CHAIN">("METRICS");

  // Joint Angles (radians and degrees)
  const [jointAnglesRad, setJointAnglesRad] = useState<number[]>([0, -0.5, 1.2, 0, 0.8, 0]);

  // Target Cartesian Coordinates (IK)
  const [targetPos, setTargetPos] = useState<[number, number, number]>([0.45, 0.0, 0.55]);
  const [targetRpyDeg, setTargetRpyDeg] = useState<[number, number, number]>([0.0, 45.0, 0.0]);
  const [solverMethod, setSolverMethod] = useState<string>("damped_least_squares");
  const [continuousSolve, setContinuousSolve] = useState<boolean>(true);

  // Results
  const [fkResult, setFkResult] = useState<FKResultData | null>(null);
  const [ikResult, setIkResult] = useState<IKResultData | null>(null);
  const [presets, setPresets] = useState<PosePreset[]>([]);
  const [isSolving, setIsSolving] = useState<boolean>(false);

  // Load initial chain & presets
  useEffect(() => {
    fetchKinematicChain("default_6dof_arm")
      .then((data) => {
        setChainInfo(data);
      })
      .catch((err) => {
        console.error("Failed to load kinematic chain", err);
      });

    fetchPosePresets("default_6dof_arm")
      .then((data) => {
        if (data.presets) setPresets(data.presets);
      })
      .catch((err) => {
        console.error("Failed to load pose presets", err);
      });
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

  // Trigger initial FK
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
        maxIterations: 150,
      });
      setIkResult(res);

      if (res.converged && res.joint_positions_rad) {
        setJointAnglesRad(res.joint_positions_rad);
        if (res.achieved_pose) {
          setFkResult(res.achieved_pose);
        }
      }
    } catch (err) {
      console.error("IK solver failed", err);
      addToast("error", "IK Solver Failure", "Numerical inverse kinematics solver encountered an error.");
    } finally {
      setIsSolving(false);
    }
  }, [targetPos, targetRpyDeg, jointAnglesRad, solverMethod, addToast]);

  // Continuous IK trigger when Cartesian targets change
  useEffect(() => {
    if (activeTab === "IK" && continuousSolve) {
      const timer = setTimeout(() => {
        triggerIK();
      }, 60);
      return () => clearTimeout(timer);
    }
  }, [activeTab, continuousSolve, targetPos, targetRpyDeg, triggerIK]);

  // Handle single joint angle change
  const handleJointChange = (idx: number, degVal: number) => {
    const radVal = (degVal * Math.PI) / 180.0;
    const next = [...jointAnglesRad];
    next[idx] = radVal;
    setJointAnglesRad(next);
    triggerFK(next);
  };

  // Apply Pose Preset
  const handleApplyPreset = (preset: PosePreset) => {
    setTargetPos(preset.target_pos);
    if (preset.joints_rad && preset.joints_rad.length === 6) {
      setJointAnglesRad(preset.joints_rad);
      triggerFK(preset.joints_rad);
    }
    addToast("info", "Preset Applied", `Applied '${preset.name}' kinematics target.`);
  };

  // Dispatch current joint configuration to live MuJoCo simulation
  const handleSendToSimulation = () => {
    simWebSocket.sendJointPositions(jointAnglesRad, 0.05);
    addToast("info", "Dispatched to MuJoCo", "Commanded physical robot joints to computed kinematic coordinates.");
  };

  return (
    <div className="flex-1 flex overflow-hidden bg-slate-950 text-slate-100 font-sans select-none">
      {/* LEFT PANEL: Kinematic Controllers */}
      <div className="w-[390px] bg-slate-900 border-r border-slate-800 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-3 border-b border-slate-800 bg-slate-900/90 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Move3d className="w-4 h-4 text-sky-400" />
            <span className="font-bold text-xs uppercase tracking-wider text-slate-200">
              Robotics Kinematics Engine
            </span>
          </div>
          <span className="px-1.5 py-0.5 rounded bg-sky-950 text-sky-400 text-[10px] font-mono border border-sky-800">
            {chainInfo ? `${chainInfo.dof} DOF` : "6 DOF"}
          </span>
        </div>

        {/* Mode Switcher: FK vs IK */}
        <div className="grid grid-cols-2 p-2 bg-slate-950/70 border-b border-slate-800 gap-1 text-xs">
          <button
            onClick={() => setActiveTab("IK")}
            className={`py-1.5 rounded flex items-center justify-center space-x-1.5 font-semibold transition ${
              activeTab === "IK"
                ? "bg-amber-500 text-slate-950 shadow"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
            }`}
          >
            <Target className="w-3.5 h-3.5" />
            <span>Inverse Kinematics</span>
          </button>
          <button
            onClick={() => setActiveTab("FK")}
            className={`py-1.5 rounded flex items-center justify-center space-x-1.5 font-semibold transition ${
              activeTab === "FK"
                ? "bg-amber-500 text-slate-950 shadow"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Forward Kinematics</span>
          </button>
        </div>

        {/* Scrollable Control Content */}
        <div className="flex-1 overflow-y-auto p-3 space-y-4 text-xs">
          {/* ===================== INVERSE KINEMATICS CONTROLS ===================== */}
          {activeTab === "IK" && (
            <div className="space-y-4">
              {/* Target Cartesian Position (meters) */}
              <div className="bg-slate-950/70 p-2.5 rounded border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-[11px] font-semibold text-slate-300">
                  <span className="flex items-center space-x-1">
                    <Compass className="w-3.5 h-3.5 text-sky-400" />
                    <span>Target Position (X, Y, Z [m])</span>
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">Cartesian Base Frame</span>
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
                      <div className="flex justify-between mt-1 text-[9px] text-slate-500">
                        <button
                          onClick={() => {
                            const next = [...targetPos] as [number, number, number];
                            next[i] = Math.round((next[i] - 0.05) * 100) / 100;
                            setTargetPos(next);
                          }}
                          className="px-1 bg-slate-800 hover:bg-slate-700 rounded text-slate-300"
                        >
                          -0.05
                        </button>
                        <button
                          onClick={() => {
                            const next = [...targetPos] as [number, number, number];
                            next[i] = Math.round((next[i] + 0.05) * 100) / 100;
                            setTargetPos(next);
                          }}
                          className="px-1 bg-slate-800 hover:bg-slate-700 rounded text-slate-300"
                        >
                          +0.05
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Target Orientation RPY (degrees) */}
              <div className="bg-slate-950/70 p-2.5 rounded border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-[11px] font-semibold text-slate-300">
                  <span className="flex items-center space-x-1">
                    <RotateCcw className="w-3.5 h-3.5 text-amber-400" />
                    <span>Target Orientation (RPY [deg])</span>
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">Extrinsic XYZ</span>
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

              {/* Target Pose Presets */}
              <div className="space-y-1.5">
                <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                  Benchmark Target Presets
                </div>
                <div className="grid grid-cols-2 gap-1.5">
                  {presets.map((p) => (
                    <button
                      key={p.name}
                      onClick={() => handleApplyPreset(p)}
                      className="p-1.5 bg-slate-900 hover:bg-slate-800 text-left border border-slate-800 rounded transition"
                    >
                      <div className="font-semibold text-slate-200 text-[11px] truncate">{p.name}</div>
                      <div className="text-[9px] font-mono text-slate-500">
                        [{p.target_pos[0]}, {p.target_pos[1]}, {p.target_pos[2]}]m
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Solver Algorithm & Controls */}
              <div className="bg-slate-950/70 p-2.5 rounded border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold text-slate-300">Solver Method</span>
                  <label className="flex items-center space-x-1 text-[10px] text-slate-400 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={continuousSolve}
                      onChange={(e) => setContinuousSolve(e.target.checked)}
                      className="rounded bg-slate-900 border-slate-700 text-amber-500 focus:ring-0"
                    />
                    <span>Live Solve</span>
                  </label>
                </div>

                <select
                  value={solverMethod}
                  onChange={(e) => setSolverMethod(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-slate-200 text-xs font-mono"
                >
                  <option value="damped_least_squares">Damped Least Squares (Levenberg-Marquardt)</option>
                  <option value="pseudo_inverse">Pseudo-Inverse (with Nullspace Centering)</option>
                  <option value="jacobian_transpose">Jacobian Transpose (Gradient Descent)</option>
                </select>

                <button
                  onClick={triggerIK}
                  disabled={isSolving}
                  className="w-full py-2 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white font-bold rounded flex items-center justify-center space-x-1.5 transition shadow"
                >
                  {isSolving ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Zap className="w-3.5 h-3.5" />
                  )}
                  <span>Calculate Inverse Kinematics</span>
                </button>
              </div>

              {/* IK Solution Diagnostics */}
              {ikResult && (
                <div className="bg-slate-900/90 p-2.5 rounded border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-semibold text-slate-300">Solution Convergence</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold flex items-center space-x-1 ${
                        ikResult.converged
                          ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                          : ikResult.status === "UNREACHABLE_TARGET"
                          ? "bg-rose-950 text-rose-400 border border-rose-800"
                          : "bg-amber-950 text-amber-400 border border-amber-800"
                      }`}
                    >
                      {ikResult.converged ? (
                        <CheckCircle2 className="w-3 h-3" />
                      ) : (
                        <XCircle className="w-3 h-3" />
                      )}
                      <span>{ikResult.status}</span>
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-1.5 text-center font-mono text-[10px]">
                    <div className="bg-slate-950 p-1.5 rounded border border-slate-800/80">
                      <div className="text-slate-500">Position Err</div>
                      <div className="font-bold text-slate-200 mt-0.5">
                        {ikResult.position_error_mm} mm
                      </div>
                    </div>
                    <div className="bg-slate-950 p-1.5 rounded border border-slate-800/80">
                      <div className="text-slate-500">Angle Err</div>
                      <div className="font-bold text-slate-200 mt-0.5">
                        {ikResult.orientation_error_deg}&deg;
                      </div>
                    </div>
                    <div className="bg-slate-950 p-1.5 rounded border border-slate-800/80">
                      <div className="text-slate-500">Iterations</div>
                      <div className="font-bold text-slate-200 mt-0.5">
                        {ikResult.iterations}
                      </div>
                    </div>
                  </div>

                  {ikResult.warnings && ikResult.warnings.length > 0 && (
                    <div className="p-2 bg-amber-950/40 border border-amber-900/60 rounded text-amber-300 text-[10px] space-y-1">
                      <div className="font-semibold flex items-center space-x-1">
                        <AlertTriangle className="w-3 h-3 text-amber-400" />
                        <span>Kinematic Warnings</span>
                      </div>
                      {ikResult.warnings.map((w, i) => (
                        <div key={i} className="text-[9px] leading-tight text-amber-200/90 font-mono">
                          &bull; {w}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* ===================== FORWARD KINEMATICS CONTROLS ===================== */}
          {activeTab === "FK" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-slate-300">Active Joint Coordinates</span>
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

              {/* 6 Joint Sliders */}
              {chainInfo?.joints.map((joint, idx) => {
                const deg = Math.round((jointAnglesRad[idx] * 180.0) / Math.PI);
                return (
                  <div key={joint.name} className="bg-slate-950/70 p-2 rounded border border-slate-800 space-y-1">
                    <div className="flex justify-between items-center text-[10px] font-mono">
                      <span className="font-bold text-slate-300">
                        {joint.name} ({joint.type})
                      </span>
                      <span className="text-amber-400 font-bold">
                        {deg}&deg; ({jointAnglesRad[idx].toFixed(2)} rad)
                      </span>
                    </div>

                    <div className="flex items-center space-x-2">
                      <span className="text-[9px] font-mono text-slate-500 w-8 text-right">
                        {joint.lower_limit_deg}&deg;
                      </span>
                      <input
                        type="range"
                        min={joint.lower_limit_deg}
                        max={joint.upper_limit_deg}
                        step="1"
                        value={deg}
                        onChange={(e) => handleJointChange(idx, parseFloat(e.target.value))}
                        className="flex-1 accent-amber-500 cursor-pointer h-1.5 bg-slate-800 rounded"
                      />
                      <span className="text-[9px] font-mono text-slate-500 w-8">
                        {joint.upper_limit_deg}&deg;
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Action: Send to Live MuJoCo Sim */}
          <button
            onClick={handleSendToSimulation}
            className="w-full py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded flex items-center justify-center space-x-1.5 transition shadow"
          >
            <Play className="w-3.5 h-3.5" />
            <span>Apply To MuJoCo Simulation</span>
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

      {/* RIGHT PANEL: Precision Matrix & Metrics Inspector */}
      <div className="w-[380px] bg-slate-900 border-l border-slate-800 flex flex-col overflow-hidden text-xs">
        {/* Inspector Tab Header */}
        <div className="flex border-b border-slate-800 bg-slate-950/70 p-1 gap-1 text-[11px]">
          {[
            { id: "METRICS", label: "Metrics & SVD", icon: Activity },
            { id: "TRANSFORM", label: "SE(3) Matrix", icon: Move3d },
            { id: "JACOBIAN", label: "Jacobian (6x6)", icon: Compass },
            { id: "CHAIN", label: "Link Frames", icon: Layers },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setInspectorTab(tab.id as any)}
                className={`flex-1 py-1.5 px-2 rounded font-medium flex items-center justify-center space-x-1 transition ${
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
          {/* TAB 1: KINEMATIC METRICS & SINGULARITY SVD */}
          {inspectorTab === "METRICS" && fkResult?.jacobian_analysis && (
            <div className="space-y-3">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">
                Yoshikawa Manipulability & Singularity Metrics
              </div>

              {/* Singularity Alert Banner */}
              {fkResult.jacobian_analysis.is_singular ? (
                <div className="p-2.5 bg-rose-950/60 border border-rose-800 rounded text-rose-300 space-y-1">
                  <div className="flex items-center space-x-1.5 font-bold">
                    <AlertTriangle className="w-4 h-4 text-rose-400" />
                    <span>Kinematic Singularity Active</span>
                  </div>
                  <div className="text-[10px] text-rose-200/90 leading-tight">
                    End-effector has lost degree(s) of instantaneous Cartesian mobility.
                  </div>
                </div>
              ) : (
                <div className="p-2 bg-emerald-950/40 border border-emerald-900/60 rounded text-emerald-400 flex items-center space-x-1.5 font-semibold">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>Well-Conditioned Workspace</span>
                </div>
              )}

              {/* Metric Cards */}
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                  <div className="text-slate-500 text-[10px]">Manipulability (w)</div>
                  <div className="text-base font-bold text-sky-400 mt-1">
                    {fkResult.jacobian_analysis.manipulability.toFixed(4)}
                  </div>
                  <div className="text-[9px] text-slate-500">sqrt(det(J * J^T))</div>
                </div>

                <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                  <div className="text-slate-500 text-[10px]">Condition No. (&kappa;)</div>
                  <div className="text-base font-bold text-amber-400 mt-1">
                    {fkResult.jacobian_analysis.condition_number.toFixed(1)}
                  </div>
                  <div className="text-[9px] text-slate-500">&sigma;_max / &sigma;_min</div>
                </div>
              </div>

              {/* SVD Singular Values */}
              <div className="bg-slate-950 p-2.5 rounded border border-slate-800 space-y-2">
                <div className="text-slate-400 text-[10px] font-semibold flex justify-between">
                  <span>Singular Values (&sigma;_1 ... &sigma;_6)</span>
                  <span className="text-slate-500">SVD</span>
                </div>
                <div className="space-y-1.5">
                  {fkResult.jacobian_analysis.singular_values.map((s, idx) => (
                    <div key={idx} className="flex items-center space-x-2">
                      <span className="w-6 text-slate-500">&sigma;_{idx + 1}</span>
                      <div className="flex-1 bg-slate-800 h-2 rounded overflow-hidden">
                        <div
                          className="bg-sky-500 h-full rounded"
                          style={{
                            width: `${Math.min(100, (s / (fkResult.jacobian_analysis?.sigma_max || 1)) * 100)}%`,
                          }}
                        />
                      </div>
                      <span className="w-14 text-right text-slate-200">{s.toFixed(4)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: SE(3) HOMOGENEOUS TRANSFORMATION MATRIX */}
          {inspectorTab === "TRANSFORM" && fkResult && (
            <div className="space-y-3">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">
                Homogeneous Transformation Matrix T_0_ee &isin; SE(3)
              </div>

              <div className="bg-slate-950 p-3 rounded border border-slate-800 overflow-x-auto">
                <table className="w-full text-center border-collapse">
                  <tbody>
                    {fkResult.transform_matrix.map((row, rIdx) => (
                      <tr key={rIdx} className="border-b border-slate-900/60 last:border-b-0">
                        {row.map((val, cIdx) => (
                          <td
                            key={cIdx}
                            className={`p-1.5 ${
                              cIdx === 3
                                ? "text-emerald-400 font-bold bg-emerald-950/20"
                                : rIdx === 3
                                ? "text-slate-600"
                                : "text-sky-300"
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

              {/* Orientation Quaternion */}
              <div className="bg-slate-950 p-2.5 rounded border border-slate-800 space-y-1">
                <div className="text-slate-500 text-[10px]">Unit Quaternion [w, x, y, z]</div>
                <div className="text-slate-200 font-bold">
                  [{fkResult.quaternion.map((q) => q.toFixed(4)).join(", ")}]
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: GEOMETRIC JACOBIAN MATRIX */}
          {inspectorTab === "JACOBIAN" && fkResult?.jacobian_analysis && (
            <div className="space-y-3">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">
                Geometric Jacobian Matrix J(q) &isin; R^(6x6)
              </div>

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
                          {rIdx < 3 ? `v_${["x", "y", "z"][rIdx]}` : `&omega;_${["x", "y", "z"][rIdx - 3]}`}
                        </td>
                        {row.map((val, cIdx) => (
                          <td
                            key={cIdx}
                            className={`p-1 ${
                              Math.abs(val) < 1e-4
                                ? "text-slate-700"
                                : rIdx < 3
                                ? "text-sky-300"
                                : "text-amber-300"
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

          {/* TAB 4: LINK COORDINATE FRAMES */}
          {inspectorTab === "CHAIN" && fkResult && (
            <div className="space-y-2">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">
                Link Coordinate Frames in Base Frame
              </div>
              <div className="space-y-1.5">
                {Object.entries(fkResult.link_transforms).map(([linkName, transform]) => (
                  <div key={linkName} className="p-2 bg-slate-950 rounded border border-slate-800">
                    <div className="font-bold text-slate-300 text-[10px]">{linkName}</div>
                    <div className="text-[9px] text-slate-500 font-mono mt-0.5">
                      P: [{transform[0][3].toFixed(3)}, {transform[1][3].toFixed(3)}, {transform[2][3].toFixed(3)}]m
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
