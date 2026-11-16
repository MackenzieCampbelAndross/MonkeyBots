import React, { useState, useEffect, useCallback } from "react";
import { useAppStore } from "../../store/useAppStore";
import {
  fetchLatestAnalytics,
  recordSimulationRun,
  fetchValidationExperiments,
  compareAnalyticsRuns,
  fetchAnalyticsCSV,
  fetchAnalyticsJSON,
  fetchAnalyticsMarkdown,
  fetchAnalyticsHTML,
} from "../../services/api";
import type {
  SimulationRunMetricsData,
  TelemetryTimeSeriesData,
  MultiRunComparisonReportData,
  ExperimentSummaryItem,
} from "../../types/api";
import {
  BarChart3,
  Download,
  FileText,
  CheckCircle2,
  Play,
  RotateCcw,
  GitCompare,
  Activity,
  Printer,
  TrendingUp,
} from "lucide-react";

export const ReportsWorkspace: React.FC = () => {
  const { activeProjectId, addToast } = useAppStore();

  const [activeTab, setActiveTab] = useState<"ANALYTICS" | "COMPARISON" | "REPORT">("ANALYTICS");
  const [loading, setLoading] = useState<boolean>(false);
  const [runningSim, setRunningSim] = useState<boolean>(false);

  // Analytics Data
  const [metrics, setMetrics] = useState<SimulationRunMetricsData | null>(null);
  const [telemetry, setTelemetry] = useState<TelemetryTimeSeriesData | null>(null);

  // Simulation run parameters
  const [simDuration, setSimDuration] = useState<number>(2.5);
  const [simTimestep, setSimTimestep] = useState<number>(0.002);
  const [simInterpolation, setSimInterpolation] = useState<string>("quintic");

  // Multi-Run Comparison State
  const [savedExps, setSavedExps] = useState<ExperimentSummaryItem[]>([]);
  const [selectedExpIds, setSelectedExpIds] = useState<string[]>([]);
  const [compReport, setCompReport] = useState<MultiRunComparisonReportData | null>(null);
  const [comparing, setComparing] = useState<boolean>(false);

  // Markdown Report Preview State
  const [markdownReport, setMarkdownReport] = useState<string>("");
  const [loadingReport, setLoadingReport] = useState<boolean>(false);

  // Active Chart View
  const [activeStream, setActiveStream] = useState<
    "POSITIONS" | "VELOCITIES" | "ACCELERATIONS" | "TORQUES" | "CARTESIAN" | "ERRORS" | "ORIENTATION" | "STEP" | "CONTACTS" | "PERFORMANCE"
  >("POSITIONS");

  // Load latest analytics
  const loadAnalytics = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchLatestAnalytics();
      setMetrics(res.metrics);
      setTelemetry(res.telemetry);
    } catch (err: any) {
      console.warn("No active analytics run yet:", err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Load saved experiments for comparison
  const loadExperiments = useCallback(async () => {
    try {
      const res = await fetchValidationExperiments();
      setSavedExps(res.experiments);
      if (res.experiments.length >= 2 && selectedExpIds.length === 0) {
        setSelectedExpIds([res.experiments[0].id, res.experiments[1].id]);
      }
    } catch (err: any) {
      console.error("Failed to load experiments:", err);
    }
  }, [selectedExpIds]);

  // Load Markdown report
  const loadMarkdown = useCallback(async () => {
    setLoadingReport(true);
    try {
      const md = await fetchAnalyticsMarkdown();
      setMarkdownReport(md);
    } catch (err: any) {
      addToast("error", "Report Fetch Error", err.message);
    } finally {
      setLoadingReport(false);
    }
  }, [addToast]);

  useEffect(() => {
    loadAnalytics();
    loadExperiments();
  }, []);

  useEffect(() => {
    if (activeTab === "REPORT" && !markdownReport) {
      loadMarkdown();
    }
  }, [activeTab, markdownReport, loadMarkdown]);

  // Execute actual simulation and record telemetry
  const handleExecuteRun = async () => {
    setRunningSim(true);
    try {
      const res = await recordSimulationRun({
        project_id: activeProjectId || "default_6dof_arm",
        duration: simDuration,
        timestep: simTimestep,
        interpolation: simInterpolation,
      });
      setMetrics(res.metrics);
      setTelemetry(res.telemetry);
      addToast(
        "success",
        "Physics Telemetry Recorded",
        `Captured ${res.total_points} steps. Cartesian RMSE: ${(res.metrics.overall_position_rmse_m * 1000).toFixed(2)} mm`
      );
      // Refresh markdown report
      fetchAnalyticsMarkdown().then(setMarkdownReport).catch(() => {});
    } catch (err: any) {
      addToast("error", "Simulation Run Error", err.message || "Failed to execute simulation");
    } finally {
      setRunningSim(false);
    }
  };

  // Compare multiple runs
  const handleCompare = async () => {
    if (selectedExpIds.length < 2) {
      addToast("warning", "Select Experiments", "Select at least 2 saved simulation runs to compare.");
      return;
    }
    setComparing(true);
    try {
      const report = await compareAnalyticsRuns(selectedExpIds);
      setCompReport(report);
      addToast("success", "Comparison Synthesized", `Compared ${report.compared_runs.length} simulation runs.`);
    } catch (err: any) {
      addToast("error", "Comparison Error", err.message);
    } finally {
      setComparing(false);
    }
  };

  // Export CSV
  const handleExportCSV = async () => {
    try {
      const csv = await fetchAnalyticsCSV();
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `MonkeyBots_Simulation_Telemetry_${Date.now()}.csv`;
      link.click();
      URL.revokeObjectURL(url);
      addToast("success", "CSV Exported", "Downloaded high-speed simulation telemetry timeseries.");
    } catch (err: any) {
      addToast("error", "Export Failed", err.message);
    }
  };

  // Export JSON
  const handleExportJSON = async () => {
    try {
      const data = await fetchAnalyticsJSON();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `MonkeyBots_Analytics_Report_${Date.now()}.json`;
      link.click();
      URL.revokeObjectURL(url);
      addToast("success", "JSON Exported", "Downloaded structured report with complete timeseries.");
    } catch (err: any) {
      addToast("error", "Export Failed", err.message);
    }
  };

  // Export Markdown
  const handleExportMarkdown = async () => {
    try {
      const md = await fetchAnalyticsMarkdown();
      const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `MonkeyBots_Engineering_Report_${Date.now()}.md`;
      link.click();
      URL.revokeObjectURL(url);
      addToast("success", "Markdown Exported", "Downloaded verification report.");
    } catch (err: any) {
      addToast("error", "Export Failed", err.message);
    }
  };

  // Print / PDF Export
  const handlePrintPDF = async () => {
    try {
      const html = await fetchAnalyticsHTML();
      const printWindow = window.open("", "_blank");
      if (printWindow) {
        printWindow.document.write(html);
        printWindow.document.close();
        printWindow.focus();
        setTimeout(() => {
          printWindow.print();
        }, 300);
      }
    } catch (err: any) {
      addToast("error", "Print Failed", err.message);
    }
  };

  const toggleExpSelection = (id: string) => {
    setSelectedExpIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950 text-slate-100 overflow-hidden select-none">
      {/* Workspace Header */}
      <div className="flex items-center justify-between px-6 py-3.5 border-b border-slate-800 bg-slate-900/60 shrink-0">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
            <BarChart3 className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-slate-100 tracking-wide flex items-center space-x-2">
              <span>ANALYTICS, VISUALIZATION & ENGINEERING REPORTS</span>
              <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded bg-sky-500/20 text-sky-400 border border-sky-500/30">
                STAGE 12
              </span>
            </h1>
            <p className="text-[11px] text-slate-400 font-sans">
              Ground-truth physics telemetry: kinematics, torques, tracking errors, step response, multi-run comparisons, and multi-format exports.
            </p>
          </div>
        </div>

        {/* Tab Switcher & Export Actions */}
        <div className="flex items-center space-x-3">
          <div className="flex bg-slate-800/80 p-0.5 rounded-lg border border-slate-700/60 text-xs font-medium">
            <button
              onClick={() => setActiveTab("ANALYTICS")}
              className={`px-3 py-1.5 rounded-md flex items-center space-x-1.5 transition ${
                activeTab === "ANALYTICS"
                  ? "bg-slate-900 text-slate-100 shadow border border-slate-700"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Activity className="w-3.5 h-3.5 text-sky-400" />
              <span>10 Core Analytics</span>
            </button>
            <button
              onClick={() => setActiveTab("COMPARISON")}
              className={`px-3 py-1.5 rounded-md flex items-center space-x-1.5 transition ${
                activeTab === "COMPARISON"
                  ? "bg-slate-900 text-slate-100 shadow border border-slate-700"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <GitCompare className="w-3.5 h-3.5 text-blue-400" />
              <span>Multi-Run Comparison</span>
            </button>
            <button
              onClick={() => setActiveTab("REPORT")}
              className={`px-3 py-1.5 rounded-md flex items-center space-x-1.5 transition ${
                activeTab === "REPORT"
                  ? "bg-slate-900 text-slate-100 shadow border border-slate-700"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <FileText className="w-3.5 h-3.5 text-amber-400" />
              <span>Export Center</span>
            </button>
          </div>

          {activeTab === "ANALYTICS" && (
            <div className="flex items-center space-x-2">
              <select
                value={simDuration}
                onChange={(e) => setSimDuration(parseFloat(e.target.value))}
                className="bg-slate-800 text-slate-300 border border-slate-700 rounded px-2 py-1 text-xs font-mono"
                title="Simulation Duration"
              >
                <option value={1.5}>1.5s</option>
                <option value={2.5}>2.5s</option>
                <option value={4.0}>4.0s</option>
              </select>

              <select
                value={simTimestep}
                onChange={(e) => setSimTimestep(parseFloat(e.target.value))}
                className="bg-slate-800 text-slate-300 border border-slate-700 rounded px-2 py-1 text-xs font-mono"
                title="Timestep"
              >
                <option value={0.001}>1ms (1000Hz)</option>
                <option value={0.002}>2ms (500Hz)</option>
                <option value={0.005}>5ms (200Hz)</option>
              </select>

              <select
                value={simInterpolation}
                onChange={(e) => setSimInterpolation(e.target.value)}
                className="bg-slate-800 text-slate-300 border border-slate-700 rounded px-2 py-1 text-xs font-mono"
                title="Trajectory Interpolation"
              >
                <option value="quintic">Quintic</option>
                <option value="cubic">Cubic</option>
                <option value="trapezoidal">Trapezoidal</option>
              </select>

              <button
                onClick={loadAnalytics}
                className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 rounded transition border border-slate-700"
                title="Refresh Analytics"
              >
                <RotateCcw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              </button>

              <button
                onClick={handleExecuteRun}
                disabled={runningSim}
                className="px-3.5 py-1.5 bg-sky-500 hover:bg-sky-400 disabled:bg-slate-800 text-slate-950 disabled:text-slate-500 rounded font-semibold text-xs flex items-center space-x-1.5 transition shadow"
              >
                {runningSim ? (
                  <RotateCcw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Play className="w-3.5 h-3.5 fill-current" />
                )}
                <span>{runningSim ? "Simulating Physics..." : "Execute & Record Run"}</span>
              </button>
            </div>
          )}

          {activeTab === "REPORT" && (
            <div className="flex items-center space-x-2">
              <button
                onClick={handleExportCSV}
                className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs flex items-center space-x-1 transition border border-slate-700"
                title="Download CSV"
              >
                <Download className="w-3.5 h-3.5 text-sky-400" />
                <span>CSV</span>
              </button>
              <button
                onClick={handleExportJSON}
                className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs flex items-center space-x-1 transition border border-slate-700"
                title="Download JSON"
              >
                <Download className="w-3.5 h-3.5 text-emerald-400" />
                <span>JSON</span>
              </button>
              <button
                onClick={handleExportMarkdown}
                className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs flex items-center space-x-1 transition border border-slate-700"
                title="Download Markdown"
              >
                <Download className="w-3.5 h-3.5 text-amber-400" />
                <span>Markdown</span>
              </button>
              <button
                onClick={handlePrintPDF}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-semibold flex items-center space-x-1.5 transition shadow"
                title="Print / Save PDF"
              >
                <Printer className="w-3.5 h-3.5" />
                <span>Print / PDF</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main Body */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* ============================================================== */}
        {/* TAB 1: 10 CORE ENGINEERING ANALYTICS STREAMS                   */}
        {/* ============================================================== */}
        {activeTab === "ANALYTICS" && (
          <div className="space-y-6 max-w-7xl mx-auto">
            {/* Metric Scorecard */}
            {metrics && (
              <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
                <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3">
                  <div className="text-[10px] font-mono text-slate-400 uppercase">Cartesian RMSE</div>
                  <div className="text-xl font-bold font-mono text-sky-400 mt-1">
                    {(metrics.overall_position_rmse_m * 1000).toFixed(2)}{" "}
                    <span className="text-[10px] text-slate-500 font-normal">mm</span>
                  </div>
                  <div className="text-[10px] text-emerald-400 mt-0.5">Tolerance: ±2.5 mm</div>
                </div>

                <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3">
                  <div className="text-[10px] font-mono text-slate-400 uppercase">Max Cartesian Err</div>
                  <div className="text-xl font-bold font-mono text-slate-200 mt-1">
                    {(metrics.max_cartesian_error_m * 1000).toFixed(2)}{" "}
                    <span className="text-[10px] text-slate-500 font-normal">mm</span>
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Peak Trajectory Offset</div>
                </div>

                <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3">
                  <div className="text-[10px] font-mono text-slate-400 uppercase">Peak Torque</div>
                  <div className="text-xl font-bold font-mono text-amber-400 mt-1">
                    {metrics.peak_applied_torque_nm}{" "}
                    <span className="text-[10px] text-slate-500 font-normal">Nm</span>
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Motor Limit: 150 Nm</div>
                </div>

                <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3">
                  <div className="text-[10px] font-mono text-slate-400 uppercase">Settling Time (2%)</div>
                  <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
                    {metrics.step_response.settling_time_s.toFixed(3)}{" "}
                    <span className="text-[10px] text-slate-500 font-normal">s</span>
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Rise Time: {metrics.step_response.rise_time_s.toFixed(2)}s</div>
                </div>

                <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3">
                  <div className="text-[10px] font-mono text-slate-400 uppercase">Energy Drift</div>
                  <div className="text-xl font-bold font-mono text-purple-400 mt-1">
                    {metrics.energy_drift_j}{" "}
                    <span className="text-[10px] text-slate-500 font-normal">J</span>
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Hamiltonian Invariant</div>
                </div>

                <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3">
                  <div className="text-[10px] font-mono text-slate-400 uppercase">Real-Time Factor</div>
                  <div className="text-xl font-bold font-mono text-blue-400 mt-1">
                    {metrics.real_time_factor}x
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Mean Latency: {metrics.mean_step_latency_us} μs</div>
                </div>
              </div>
            )}

            {/* Stream Selector Buttons (All 10 required capabilities) */}
            <div className="flex flex-wrap gap-1.5 p-2 bg-slate-900/60 rounded-xl border border-slate-800 text-xs font-mono">
              {[
                { id: "POSITIONS", label: "1. Joint Positions" },
                { id: "VELOCITIES", label: "2. Joint Velocities" },
                { id: "ACCELERATIONS", label: "3. Accelerations" },
                { id: "TORQUES", label: "4. Applied Torques" },
                { id: "CARTESIAN", label: "5. EE Trajectory" },
                { id: "ERRORS", label: "6. Tracking Errors" },
                { id: "ORIENTATION", label: "7. Orientation Errors" },
                { id: "STEP", label: "8. Controller Step" },
                { id: "CONTACTS", label: "9. Collision & Contacts" },
                { id: "PERFORMANCE", label: "10. Performance & RTF" },
              ].map((s) => (
                <button
                  key={s.id}
                  onClick={() => setActiveStream(s.id as any)}
                  className={`px-3 py-1.5 rounded-lg transition ${
                    activeStream === s.id
                      ? "bg-sky-500 text-slate-950 font-bold shadow"
                      : "bg-slate-800/80 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>

            {/* Active Visualization Card */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-sky-400" />
                  <span className="text-xs font-bold text-slate-100 uppercase tracking-wider">
                    {activeStream === "POSITIONS" && "STREAM 1: Joint Angular Positions [rad] (Actual vs Desired)"}
                    {activeStream === "VELOCITIES" && "STREAM 2: Joint Angular Velocities [rad/s]"}
                    {activeStream === "ACCELERATIONS" && "STREAM 3: Joint Angular Accelerations [rad/s²]"}
                    {activeStream === "TORQUES" && "STREAM 4: Applied Actuator Torques [Nm] vs Limits"}
                    {activeStream === "CARTESIAN" && "STREAM 5: End-Effector Cartesian Trajectory [m]"}
                    {activeStream === "ERRORS" && "STREAM 6: End-Effector Euclidean Position Error [mm]"}
                    {activeStream === "ORIENTATION" && "STREAM 7: Geodesic Orientation Tracking Error [rad / deg]"}
                    {activeStream === "STEP" && "STREAM 8: Closed-Loop Controller Step Response Dynamics"}
                    {activeStream === "CONTACTS" && "STREAM 9: Contact Force Transients & Impact Normal"}
                    {activeStream === "PERFORMANCE" && "STREAM 10: Numerical Solver Diagnostics & Execution Time"}
                  </span>
                </div>
                <div className="text-[11px] font-mono text-slate-400">
                  {telemetry ? `${telemetry.timestamps.length} sample points` : "Awaiting simulation"}
                </div>
              </div>

              {/* Data Table / Interactive View */}
              {telemetry ? (
                <div className="space-y-4">
                  {/* Table of Downsampled Telemetry */}
                  <div className="overflow-x-auto rounded-lg border border-slate-800 max-h-72 overflow-y-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-950 text-slate-400 text-[10px] font-mono border-b border-slate-800 sticky top-0">
                        <tr>
                          <th className="py-2 px-3">Time [s]</th>
                          {activeStream === "POSITIONS" && (
                            <>
                              <th className="py-2 px-3">Actual q1..q3 [rad]</th>
                              <th className="py-2 px-3">Target q1..q3 [rad]</th>
                              <th className="py-2 px-3">Actual q4..q6 [rad]</th>
                              <th className="py-2 px-3">Target q4..q6 [rad]</th>
                            </>
                          )}
                          {activeStream === "VELOCITIES" && (
                            <>
                              <th className="py-2 px-3">Vel q1..q3 [rad/s]</th>
                              <th className="py-2 px-3">Vel q4..q6 [rad/s]</th>
                              <th className="py-2 px-3">Max Velocity [rad/s]</th>
                            </>
                          )}
                          {activeStream === "ACCELERATIONS" && (
                            <>
                              <th className="py-2 px-3">Accel q1..q3 [rad/s²]</th>
                              <th className="py-2 px-3">Accel q4..q6 [rad/s²]</th>
                            </>
                          )}
                          {activeStream === "TORQUES" && (
                            <>
                              <th className="py-2 px-3">Torque Tau 1..3 [Nm]</th>
                              <th className="py-2 px-3">Torque Tau 4..6 [Nm]</th>
                              <th className="py-2 px-3">Max Torque [Nm]</th>
                            </>
                          )}
                          {activeStream === "CARTESIAN" && (
                            <>
                              <th className="py-2 px-3">Actual Flange [X, Y, Z]</th>
                              <th className="py-2 px-3">Target Flange [X, Y, Z]</th>
                              <th className="py-2 px-3">Pos Error [mm]</th>
                            </>
                          )}
                          {activeStream === "ERRORS" && (
                            <>
                              <th className="py-2 px-3">Position Error [mm]</th>
                              <th className="py-2 px-3">Orientation Error [rad]</th>
                            </>
                          )}
                          {activeStream === "ORIENTATION" && (
                            <>
                              <th className="py-2 px-3">Geodesic Error [rad]</th>
                              <th className="py-2 px-3">Error [deg]</th>
                            </>
                          )}
                          {activeStream === "STEP" && (
                            <>
                              <th className="py-2 px-3">Joint 2 Position [rad]</th>
                              <th className="py-2 px-3">Joint 2 Target [rad]</th>
                              <th className="py-2 px-3">Tracking Error [rad]</th>
                            </>
                          )}
                          {activeStream === "CONTACTS" && (
                            <>
                              <th className="py-2 px-3">Contact Count</th>
                              <th className="py-2 px-3">Max Normal Force [N]</th>
                            </>
                          )}
                          {activeStream === "PERFORMANCE" && (
                            <>
                              <th className="py-2 px-3">Total Energy [J]</th>
                              <th className="py-2 px-3">Solver Iterations</th>
                            </>
                          )}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                        {telemetry.timestamps.slice(0, 35).map((t, idx) => (
                          <tr key={idx} className="hover:bg-slate-800/20 transition">
                            <td className="py-1 px-3 text-slate-400">{t.toFixed(3)}</td>

                            {activeStream === "POSITIONS" && (
                              <>
                                <td className="py-1 px-3 text-sky-400">
                                  [{telemetry.q_actual[idx]?.slice(0, 3).map((v) => v.toFixed(3)).join(", ")}]
                                </td>
                                <td className="py-1 px-3 text-slate-400">
                                  [{telemetry.q_target[idx]?.slice(0, 3).map((v) => v.toFixed(3)).join(", ")}]
                                </td>
                                <td className="py-1 px-3 text-emerald-400">
                                  [{telemetry.q_actual[idx]?.slice(3, 6).map((v) => v.toFixed(3)).join(", ")}]
                                </td>
                                <td className="py-1 px-3 text-slate-400">
                                  [{telemetry.q_target[idx]?.slice(3, 6).map((v) => v.toFixed(3)).join(", ")}]
                                </td>
                              </>
                            )}

                            {activeStream === "VELOCITIES" && (
                              <>
                                <td className="py-1 px-3 text-sky-300">
                                  [{telemetry.qvel_actual[idx]?.slice(0, 3).map((v) => v.toFixed(2)).join(", ")}]
                                </td>
                                <td className="py-1 px-3 text-sky-300">
                                  [{telemetry.qvel_actual[idx]?.slice(3, 6).map((v) => v.toFixed(2)).join(", ")}]
                                </td>
                                <td className="py-1 px-3 text-amber-400 font-bold">
                                  {Math.max(...(telemetry.qvel_actual[idx] || [0])).toFixed(2)}
                                </td>
                              </>
                            )}

                            {activeStream === "ACCELERATIONS" && (
                              <>
                                <td className="py-1 px-3 text-purple-300">
                                  [{telemetry.qacc_actual[idx]?.slice(0, 3).map((v) => v.toFixed(2)).join(", ")}]
                                </td>
                                <td className="py-1 px-3 text-purple-300">
                                  [{telemetry.qacc_actual[idx]?.slice(3, 6).map((v) => v.toFixed(2)).join(", ")}]
                                </td>
                              </>
                            )}

                            {activeStream === "TORQUES" && (
                              <>
                                <td className="py-1 px-3 text-amber-400">
                                  [{telemetry.torques[idx]?.slice(0, 3).map((v) => v.toFixed(1)).join(", ")}]
                                </td>
                                <td className="py-1 px-3 text-amber-300">
                                  [{telemetry.torques[idx]?.slice(3, 6).map((v) => v.toFixed(1)).join(", ")}]
                                </td>
                                <td className="py-1 px-3 text-rose-400 font-bold">
                                  {Math.max(...(telemetry.torques[idx]?.map((u) => Math.abs(u)) || [0])).toFixed(1)}
                                </td>
                              </>
                            )}

                            {activeStream === "CARTESIAN" && (
                              <>
                                <td className="py-1 px-3 text-emerald-400">
                                  [{telemetry.ee_pos_actual[idx]?.map((v) => v.toFixed(4)).join(", ")}]
                                </td>
                                <td className="py-1 px-3 text-slate-400">
                                  [{telemetry.ee_pos_target[idx]?.map((v) => v.toFixed(4)).join(", ")}]
                                </td>
                                <td className="py-1 px-3 text-sky-400 font-bold">
                                  {(telemetry.pos_error_norm[idx] * 1000).toFixed(2)}
                                </td>
                              </>
                            )}

                            {activeStream === "ERRORS" && (
                              <>
                                <td className="py-1 px-3 text-sky-400 font-bold">
                                  {(telemetry.pos_error_norm[idx] * 1000).toFixed(3)}
                                </td>
                                <td className="py-1 px-3 text-slate-300">
                                  {telemetry.rot_error_rad[idx].toFixed(4)}
                                </td>
                              </>
                            )}

                            {activeStream === "ORIENTATION" && (
                              <>
                                <td className="py-1 px-3 text-purple-300">
                                  {telemetry.rot_error_rad[idx].toFixed(4)}
                                </td>
                                <td className="py-1 px-3 text-purple-400 font-bold">
                                  {(telemetry.rot_error_rad[idx] * 57.2958).toFixed(2)}°
                                </td>
                              </>
                            )}

                            {activeStream === "STEP" && (
                              <>
                                <td className="py-1 px-3 text-emerald-400">
                                  {telemetry.q_actual[idx]?.[1]?.toFixed(4)}
                                </td>
                                <td className="py-1 px-3 text-slate-400">
                                  {telemetry.q_target[idx]?.[1]?.toFixed(4)}
                                </td>
                                <td className="py-1 px-3 text-sky-400">
                                  {(Math.abs((telemetry.q_target[idx]?.[1] || 0) - (telemetry.q_actual[idx]?.[1] || 0)) * 1000).toFixed(2)} mrad
                                </td>
                              </>
                            )}

                            {activeStream === "CONTACTS" && (
                              <>
                                <td className="py-1 px-3 text-amber-300">
                                  {telemetry.contacts_count[idx]}
                                </td>
                                <td className="py-1 px-3 text-rose-400 font-bold">
                                  {telemetry.max_normal_force[idx].toFixed(2)}
                                </td>
                              </>
                            )}

                            {activeStream === "PERFORMANCE" && (
                              <>
                                <td className="py-1 px-3 text-emerald-400">
                                  {telemetry.energy_total[idx].toFixed(3)}
                                </td>
                                <td className="py-1 px-3 text-slate-300">
                                  {telemetry.solver_niter[idx]}
                                </td>
                              </>
                            )}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Joint Summary Table */}
                  {metrics && (
                    <div className="overflow-x-auto rounded-lg border border-slate-800">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-950 text-slate-400 text-[10px] font-mono border-b border-slate-800 uppercase">
                          <tr>
                            <th className="py-2 px-3">Joint</th>
                            <th className="py-2 px-3">Tracking RMSE [mrad]</th>
                            <th className="py-2 px-3">Max Pos Error [mrad]</th>
                            <th className="py-2 px-3">Max Velocity [rad/s]</th>
                            <th className="py-2 px-3">Max Accel [rad/s²]</th>
                            <th className="py-2 px-3">Peak Torque [Nm]</th>
                            <th className="py-2 px-3">RMS Torque [Nm]</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                          {metrics.joints.map((j) => (
                            <tr key={j.joint_index} className="hover:bg-slate-800/20">
                              <td className="py-1.5 px-3 font-sans font-semibold text-slate-200">{j.name}</td>
                              <td className="py-1.5 px-3 text-sky-400 font-bold">
                                {(j.position_rmse_rad * 1000).toFixed(2)}
                              </td>
                              <td className="py-1.5 px-3 text-slate-300">
                                {(j.max_position_error_rad * 1000).toFixed(2)}
                              </td>
                              <td className="py-1.5 px-3 text-slate-300">{j.max_velocity_rad_s}</td>
                              <td className="py-1.5 px-3 text-slate-400">{j.max_acceleration_rad_s2}</td>
                              <td className="py-1.5 px-3 text-amber-400 font-bold">{j.peak_torque_nm}</td>
                              <td className="py-1.5 px-3 text-slate-300">{j.rms_torque_nm}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              ) : (
                <div className="py-12 text-center text-slate-500 text-xs font-sans space-y-2">
                  <Activity className="w-8 h-8 mx-auto text-slate-600 animate-pulse" />
                  <div>No simulation data recorded yet. Click 'Execute & Record Run' above.</div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 2: MULTI-RUN SIMULATION COMPARATOR                         */}
        {/* ============================================================== */}
        {activeTab === "COMPARISON" && (
          <div className="space-y-6 max-w-7xl mx-auto">
            {/* Top Bar: Select Experiments */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center space-x-2">
                  <GitCompare className="w-4 h-4 text-blue-400" />
                  <span className="text-xs font-bold text-slate-100 uppercase tracking-wider">
                    Select Simulation Runs for Side-by-Side Comparison
                  </span>
                </div>

                <button
                  onClick={handleCompare}
                  disabled={comparing || selectedExpIds.length < 2}
                  className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white font-semibold rounded text-xs transition shadow flex items-center space-x-1.5"
                >
                  {comparing ? <RotateCcw className="w-3.5 h-3.5 animate-spin" /> : <GitCompare className="w-3.5 h-3.5" />}
                  <span>Synthesize Cross-Run Analytics ({selectedExpIds.length})</span>
                </button>
              </div>

              {/* Checkbox table of saved runs */}
              <div className="overflow-x-auto rounded-lg border border-slate-800 max-h-56 overflow-y-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-slate-400 text-[10px] font-mono border-b border-slate-800 sticky top-0">
                    <tr>
                      <th className="py-1.5 px-3 w-8"></th>
                      <th className="py-1.5 px-3">Run ID / Name</th>
                      <th className="py-1.5 px-3">Date</th>
                      <th className="py-1.5 px-3">Duration</th>
                      <th className="py-1.5 px-3">Tracking RMSE [mrad]</th>
                      <th className="py-1.5 px-3">Peak Torque [Nm]</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                    {savedExps.map((exp) => {
                      const isChecked = selectedExpIds.includes(exp.id);
                      return (
                        <tr key={exp.id} className="hover:bg-slate-800/30 transition">
                          <td className="py-1.5 px-3">
                            <input
                              type="checkbox"
                              checked={isChecked}
                              onChange={() => toggleExpSelection(exp.id)}
                              className="rounded bg-slate-950 border-slate-800 text-blue-500 focus:ring-0"
                            />
                          </td>
                          <td className="py-1.5 px-3 font-sans">
                            <span className="font-semibold text-slate-200">{exp.name}</span>
                            <span className="ml-2 font-mono text-[10px] text-slate-500">{exp.id}</span>
                          </td>
                          <td className="py-1.5 px-3 text-slate-400">{exp.timestamp?.slice(0, 10)}</td>
                          <td className="py-1.5 px-3 text-slate-300">{exp.duration}s</td>
                          <td className="py-1.5 px-3 text-sky-400 font-bold">{exp.position_rmse_mrad}</td>
                          <td className="py-1.5 px-3 text-amber-400">{exp.max_torque_nm}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Comparison Synthesis Results */}
            {compReport && (
              <div className="bg-slate-900/90 border border-blue-500/30 rounded-xl p-5 space-y-5">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <h2 className="text-xs font-bold text-blue-400 uppercase tracking-wider flex items-center space-x-1.5">
                      <TrendingUp className="w-4 h-4" />
                      <span>Comparative Performance Matrix</span>
                    </h2>
                    <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                      Baseline Reference: <strong>{compReport.baseline_run_id}</strong>
                    </div>
                  </div>
                </div>

                {/* Diff Table */}
                <div className="overflow-x-auto rounded-lg border border-slate-800">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-slate-950 text-slate-400 text-[10px] border-b border-slate-800 uppercase">
                      <tr>
                        <th className="py-2 px-3">Run Name</th>
                        <th className="py-2 px-3">Cartesian RMSE [mm]</th>
                        <th className="py-2 px-3">Δ RMSE [mm]</th>
                        <th className="py-2 px-3">Tracking Improvement</th>
                        <th className="py-2 px-3">Peak Torque [Nm]</th>
                        <th className="py-2 px-3">Settling Time [s]</th>
                        <th className="py-2 px-3">Real-Time Factor</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-[11px]">
                      {compReport.compared_runs.map((r, idx) => {
                        const deltaKey = `${r.run_id}_vs_${compReport.baseline_run_id}`;
                        const d = compReport.deltas[deltaKey];
                        const isBase = idx === 0;

                        return (
                          <tr key={r.run_id} className="hover:bg-slate-800/20">
                            <td className="py-2 px-3 font-sans font-semibold text-slate-200">
                              {r.run_name} {isBase && <span className="text-[10px] text-blue-400">(Base)</span>}
                            </td>
                            <td className="py-2 px-3 text-slate-200 font-bold">{r.cartesian_rmse_mm}</td>
                            <td className="py-2 px-3 text-slate-300">
                              {d ? `${d.delta_rmse_mm > 0 ? "+" : ""}${d.delta_rmse_mm}` : "-"}
                            </td>
                            <td className="py-2 px-3 font-bold text-emerald-400">
                              {d ? `${d.rmse_improvement_pct}%` : "-"}
                            </td>
                            <td className="py-2 px-3 text-amber-400">{r.peak_torque_nm}</td>
                            <td className="py-2 px-3 text-slate-300">{r.settling_time_s}</td>
                            <td className="py-2 px-3 text-purple-400">{r.real_time_factor}x</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Key Findings List */}
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-slate-300">Empirical Trade-off Conclusions:</div>
                  <div className="space-y-1.5 font-sans text-xs">
                    {compReport.key_findings.map((f, idx) => (
                      <div key={idx} className="p-2.5 rounded bg-slate-950 border border-slate-800 text-slate-300 flex items-start space-x-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                        <span>{f}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 3: FORMAL ENGINEERING REPORT & EXPORT CENTER               */}
        {/* ============================================================== */}
        {activeTab === "REPORT" && (
          <div className="max-w-5xl mx-auto space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h2 className="text-sm font-bold text-slate-100 flex items-center space-x-2">
                  <FileText className="w-4 h-4 text-amber-400" />
                  <span>Formal Engineering Validation & Performance Document</span>
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Includes full mathematical parameters, ISO 9283 compliance, tolerances, and data-driven conclusions.
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={loadMarkdown}
                  disabled={loadingReport}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs flex items-center space-x-1.5 transition border border-slate-700"
                >
                  <RotateCcw className={`w-3.5 h-3.5 ${loadingReport ? "animate-spin" : ""}`} />
                  <span>Refresh Document</span>
                </button>
              </div>
            </div>

            {loadingReport ? (
              <div className="p-12 text-center text-slate-400 text-xs flex items-center justify-center space-x-2">
                <RotateCcw className="w-4 h-4 animate-spin text-amber-400" />
                <span>Compiling engineering verification report...</span>
              </div>
            ) : (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 font-mono text-xs leading-relaxed text-slate-200 overflow-x-auto whitespace-pre-wrap selection:bg-blue-600 selection:text-white">
                {markdownReport}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
