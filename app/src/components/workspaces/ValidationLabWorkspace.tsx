import React, { useState, useEffect, useCallback } from "react";
import { useAppStore } from "../../store/useAppStore";
import {
  fetchValidationSuite,
  fetchValidationCapability,
  fetchValidationReportMarkdown,
  fetchValidationExperiments,
  runValidationExperiment,
  fetchValidationExperimentDetails,
  compareValidationExperiments,
} from "../../services/api";
import type {
  ValidationSuiteReportData,
  ExperimentConfigData,
  ExperimentResultData,
  ExperimentSummaryItem,
  ExperimentComparisonData,
} from "../../types/api";
import {
  ShieldCheck,
  Play,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Award,
  FileText,
  FlaskConical,
  Download,
  Copy,
  ChevronDown,
  ChevronRight,
  Sliders,
  Scale,
  RefreshCw,
  GitCompare,
  Cpu,
} from "lucide-react";

export const ValidationLabWorkspace: React.FC = () => {
  const { addToast } = useAppStore();

  // Active Workspace Tab
  const [activeTab, setActiveTab] = useState<"BENCHMARKS" | "EXPERIMENTS" | "REPORT">("BENCHMARKS");

  // Benchmarks State
  const [suiteReport, setSuiteReport] = useState<ValidationSuiteReportData | null>(null);
  const [loadingSuite, setLoadingSuite] = useState<boolean>(false);
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({
    VAL_CAP_01: true,
    VAL_CAP_03: true,
    VAL_CAP_04: true,
  });
  const [runningCapId, setRunningCapId] = useState<string | null>(null);

  // Markdown Report State
  const [reportMarkdown, setReportMarkdown] = useState<string>("");
  const [loadingReport, setLoadingReport] = useState<boolean>(false);

  // Repeatable Experiments State
  const [experimentsList, setExperimentsList] = useState<ExperimentSummaryItem[]>([]);
  const [selectedExpIds, setSelectedExpIds] = useState<string[]>([]);
  const [activeExperiment, setActiveExperiment] = useState<ExperimentResultData | null>(null);
  const [comparisonData, setComparisonData] = useState<ExperimentComparisonData | null>(null);
  const [runningExperiment, setRunningExperiment] = useState<boolean>(false);
  const [loadingComparison, setLoadingComparison] = useState<boolean>(false);

  // New Experiment Form State
  const [expId, setExpId] = useState<string>(`EXP_${Date.now().toString().slice(-4)}`);
  const [expName, setExpName] = useState<string>("PID Step Tracking Benchmark");
  const [timestep, setTimestep] = useState<number>(0.002);
  const [duration, setDuration] = useState<number>(2.5);
  const [trajType, setTrajType] = useState<string>("quintic");
  const [kpGains, setKpGains] = useState<string>("250, 300, 200, 100, 60, 30");
  const [kdGains, setKdGains] = useState<string>("25, 35, 20, 8, 4, 2");

  // Load Validation Suite
  const loadSuite = useCallback(async () => {
    setLoadingSuite(true);
    try {
      const data = await fetchValidationSuite();
      setSuiteReport(data);
      addToast(
        "success",
        "Validation Suite Completed",
        `Compliance: ${data.compliance_percentage}% (${data.verified_count}/${data.total_tests} Verified)`
      );
    } catch (err: any) {
      addToast("error", "Validation Failed", err.message || "Failed to execute validation suite.");
    } finally {
      setLoadingSuite(false);
    }
  }, [addToast]);

  // Load Saved Experiments
  const loadExperiments = useCallback(async () => {
    try {
      const res = await fetchValidationExperiments();
      setExperimentsList(res.experiments);
      if (res.experiments.length > 0 && !activeExperiment) {
        // Load first experiment details by default
        const first = await fetchValidationExperimentDetails(res.experiments[0].id);
        setActiveExperiment(first);
      }
    } catch (err: any) {
      console.error("Failed to load experiments:", err);
    }
  }, [activeExperiment]);

  // Load Markdown Report
  const loadMarkdownReport = useCallback(async () => {
    setLoadingReport(true);
    try {
      const md = await fetchValidationReportMarkdown();
      setReportMarkdown(md);
    } catch (err: any) {
      addToast("error", "Report Fetch Error", err.message || "Failed to load Markdown report.");
    } finally {
      setLoadingReport(false);
    }
  }, [addToast]);

  // Initial Data Fetch
  useEffect(() => {
    loadSuite();
    loadExperiments();
  }, []);

  // When switching to Report tab, load markdown
  useEffect(() => {
    if (activeTab === "REPORT" && !reportMarkdown) {
      loadMarkdownReport();
    }
  }, [activeTab, reportMarkdown, loadMarkdownReport]);

  // Toggle capability card collapse
  const toggleCard = (id: string) => {
    setExpandedCards((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  // Run individual capability
  const handleRunCapability = async (id: string) => {
    setRunningCapId(id);
    try {
      const updatedCase = await fetchValidationCapability(id);
      if (suiteReport) {
        const nextCases = suiteReport.test_cases.map((tc) => (tc.id === id ? updatedCase : tc));
        setSuiteReport({ ...suiteReport, test_cases: nextCases });
      }
      addToast("info", "Capability Evaluated", `${updatedCase.name} is ${updatedCase.status}`);
    } catch (err: any) {
      addToast("error", "Execution Failed", err.message || `Failed to run ${id}`);
    } finally {
      setRunningCapId(null);
    }
  };

  // Run New Repeatable Experiment
  const handleExecuteExperiment = async () => {
    setRunningExperiment(true);
    try {
      const kp = kpGains.split(",").map((v) => parseFloat(v.trim()) || 100.0);
      const kd = kdGains.split(",").map((v) => parseFloat(v.trim()) || 10.0);
      const ki = [2.0, 5.0, 3.0, 1.0, 0.5, 0.2];

      const config: ExperimentConfigData = {
        id: expId,
        name: expName,
        timestep,
        duration,
        controller_type: "PID",
        kp,
        ki,
        kd,
        trajectory_type: trajType,
        waypoints: [
          [0.0, -0.6, 1.2, 0.0, 0.6, 0.0],
          [0.4, -0.3, 0.9, 0.2, 0.4, 0.3],
          [-0.3, -0.5, 1.1, -0.1, 0.5, -0.2],
          [0.0, -0.6, 1.2, 0.0, 0.6, 0.0],
        ],
        v_max: 2.0,
        a_max: 4.0,
      };

      const result = await runValidationExperiment(config);
      setActiveExperiment(result);
      await loadExperiments();
      setExpId(`EXP_${Date.now().toString().slice(-4)}`);
      addToast(
        "success",
        "Experiment Saved",
        `Tracking RMSE: ${(result.metrics.position_rmse_rad * 1000).toFixed(2)} mrad | RTF: ${result.metrics.real_time_factor}x`
      );
    } catch (err: any) {
      addToast("error", "Experiment Execution Failed", err.message || "Failed to execute experiment.");
    } finally {
      setRunningExperiment(false);
    }
  };

  // Select/Unselect Experiment for Comparison
  const toggleExpSelection = (id: string) => {
    setSelectedExpIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  // Compare Selected Experiments
  const handleCompare = async () => {
    if (selectedExpIds.length < 2) {
      addToast("warning", "Select Experiments", "Select at least 2 saved experiments to compare.");
      return;
    }
    setLoadingComparison(true);
    try {
      const comp = await compareValidationExperiments(selectedExpIds);
      setComparisonData(comp);
      addToast("success", "Comparison Generated", `Compared ${comp.experiment_ids.length} simulation runs.`);
    } catch (err: any) {
      addToast("error", "Comparison Error", err.message || "Failed to compare experiments.");
    } finally {
      setLoadingComparison(false);
    }
  };

  // Export Markdown Report to file
  const handleDownloadMarkdown = () => {
    if (!reportMarkdown) return;
    const blob = new Blob([reportMarkdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `MonkeyBots_Validation_Report_${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    addToast("info", "Report Exported", "Downloaded markdown validation report.");
  };

  // Copy Markdown to Clipboard
  const handleCopyMarkdown = () => {
    if (!reportMarkdown) return;
    navigator.clipboard.writeText(reportMarkdown);
    addToast("info", "Copied", "Markdown validation report copied to clipboard.");
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950 text-slate-100 overflow-hidden select-none">
      {/* Top Workspace Header */}
      <div className="flex items-center justify-between px-6 py-3.5 border-b border-slate-800 bg-slate-900/60 shrink-0">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-slate-100 tracking-wide flex items-center space-x-2">
              <span>ENGINEERING VALIDATION & BENCHMARKING LABORATORY</span>
              <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                STAGE 10
              </span>
            </h1>
            <p className="text-[11px] text-slate-400 font-sans">
              Rigorous analytical verification, mathematical determinism, and local repeatable experiment tracking.
            </p>
          </div>
        </div>

        {/* Tab Switcher & Global Actions */}
        <div className="flex items-center space-x-3">
          <div className="flex bg-slate-800/80 p-0.5 rounded-lg border border-slate-700/60 text-xs font-medium">
            <button
              onClick={() => setActiveTab("BENCHMARKS")}
              className={`px-3 py-1.5 rounded-md flex items-center space-x-1.5 transition ${
                activeTab === "BENCHMARKS"
                  ? "bg-slate-900 text-slate-100 shadow border border-slate-700"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Award className="w-3.5 h-3.5 text-emerald-400" />
              <span>10 Core Capabilities</span>
            </button>
            <button
              onClick={() => setActiveTab("EXPERIMENTS")}
              className={`px-3 py-1.5 rounded-md flex items-center space-x-1.5 transition ${
                activeTab === "EXPERIMENTS"
                  ? "bg-slate-900 text-slate-100 shadow border border-slate-700"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <FlaskConical className="w-3.5 h-3.5 text-blue-400" />
              <span>Repeatable Experiments</span>
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
              <span>Validation Report</span>
            </button>
          </div>

          {activeTab === "BENCHMARKS" && (
            <button
              onClick={loadSuite}
              disabled={loadingSuite}
              className="px-3.5 py-1.5 bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-800 text-slate-950 disabled:text-slate-500 rounded font-semibold text-xs flex items-center space-x-1.5 transition shadow"
            >
              {loadingSuite ? (
                <RotateCcw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Play className="w-3.5 h-3.5 fill-current" />
              )}
              <span>{loadingSuite ? "Evaluating Suite..." : "Run All Benchmarks"}</span>
            </button>
          )}

          {activeTab === "REPORT" && (
            <div className="flex items-center space-x-2">
              <button
                onClick={handleCopyMarkdown}
                className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs flex items-center space-x-1 transition border border-slate-700"
                title="Copy Markdown"
              >
                <Copy className="w-3.5 h-3.5" />
                <span>Copy</span>
              </button>
              <button
                onClick={handleDownloadMarkdown}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs flex items-center space-x-1.5 transition shadow"
                title="Download Report"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download Report</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main Workspace Body */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* ============================================================== */}
        {/* TAB 1: 10 CORE ENGINEERING CAPABILITIES BENCHMARKS              */}
        {/* ============================================================== */}
        {activeTab === "BENCHMARKS" && (
          <div className="space-y-6 max-w-7xl mx-auto">
            {/* Executive Compliance Scorecard */}
            {suiteReport && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
                  <div>
                    <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                      Overall Compliance
                    </div>
                    <div className="text-2xl font-bold font-mono text-emerald-400 mt-0.5">
                      {suiteReport.compliance_percentage}%
                    </div>
                    <div className="text-[11px] text-slate-500 mt-0.5">
                      Status: <span className="font-semibold text-emerald-400">{suiteReport.overall_status}</span>
                    </div>
                  </div>
                  <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                    <Award className="w-5 h-5" />
                  </div>
                </div>

                <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
                  <div>
                    <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                      Capabilities Verified
                    </div>
                    <div className="text-2xl font-bold font-mono text-slate-100 mt-0.5">
                      {suiteReport.verified_count} <span className="text-xs text-slate-500 font-normal">/ {suiteReport.total_tests}</span>
                    </div>
                    <div className="text-[11px] text-emerald-400/90 mt-0.5">
                      Zero Tolerance Failures
                    </div>
                  </div>
                  <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
                    <CheckCircle2 className="w-5 h-5" />
                  </div>
                </div>

                <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
                  <div>
                    <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                      Physics Engine Context
                    </div>
                    <div className="text-sm font-bold font-mono text-slate-200 mt-1">
                      MuJoCo v{suiteReport.system_info?.mujoco_version || "4.0.1"}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-0.5">
                      {suiteReport.system_info?.os} ({suiteReport.system_info?.architecture})
                    </div>
                  </div>
                  <div className="w-10 h-10 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
                    <Cpu className="w-5 h-5" />
                  </div>
                </div>

                <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
                  <div>
                    <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                      Validation Standards
                    </div>
                    <div className="text-xs font-bold text-slate-200 mt-1">
                      ISO 9283 / IEEE 754
                    </div>
                    <div className="text-[11px] text-slate-400 mt-0.5">
                      Deterministic Physics / Zero Cloud
                    </div>
                  </div>
                  <div className="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                    <Scale className="w-5 h-5" />
                  </div>
                </div>
              </div>
            )}

            {/* Benchmarks Capability Cards */}
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider px-1">
                <span>10 Standardized Robotic Engineering Benchmarks</span>
                <span>Analytical Tolerances & Verification Status</span>
              </div>

              {suiteReport?.test_cases.map((tc) => {
                const isExpanded = !!expandedCards[tc.id];
                const isRunning = runningCapId === tc.id;
                const isVerified = tc.status === "VERIFIED";

                return (
                  <div
                    key={tc.id}
                    className="bg-slate-900/90 border border-slate-800 hover:border-slate-700/80 rounded-xl overflow-hidden transition shadow-sm"
                  >
                    {/* Capability Header */}
                    <div
                      className="p-4 flex items-center justify-between cursor-pointer hover:bg-slate-800/30 transition select-none"
                      onClick={() => toggleCard(tc.id)}
                    >
                      <div className="flex items-center space-x-3.5">
                        <button className="text-slate-500 hover:text-slate-300 transition">
                          {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                        </button>

                        <div className="flex items-center space-x-2">
                          <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                            {tc.id}
                          </span>
                          <span className="font-semibold text-sm text-slate-100">{tc.name}</span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800/80 text-slate-400">
                            {tc.category}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center space-x-4">
                        <span className="text-[11px] font-mono text-slate-400">
                          {tc.execution_time_ms.toFixed(1)} ms
                        </span>

                        <div
                          className={`text-xs font-semibold px-2.5 py-1 rounded-full flex items-center space-x-1.5 border ${
                            isVerified
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                              : tc.status === "KNOWN_LIMITATION"
                              ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                              : "bg-rose-500/10 text-rose-400 border-rose-500/30"
                          }`}
                        >
                          {isVerified ? (
                            <CheckCircle2 className="w-3.5 h-3.5" />
                          ) : (
                            <AlertTriangle className="w-3.5 h-3.5" />
                          )}
                          <span>{tc.status}</span>
                        </div>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRunCapability(tc.id);
                          }}
                          disabled={isRunning}
                          className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-300 text-xs font-medium rounded transition border border-slate-700 flex items-center space-x-1"
                        >
                          {isRunning ? (
                            <RotateCcw className="w-3 h-3 animate-spin" />
                          ) : (
                            <Play className="w-3 h-3" />
                          )}
                          <span>{isRunning ? "Testing" : "Test"}</span>
                        </button>
                      </div>
                    </div>

                    {/* Collapsible Details & Metric Table */}
                    {isExpanded && (
                      <div className="px-5 pb-5 pt-1 border-t border-slate-800/60 bg-slate-950/40 space-y-3">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between text-xs text-slate-400 gap-1 pt-2">
                          <p className="leading-relaxed">{tc.description}</p>
                          <div className="shrink-0 text-[11px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                            Ref: {tc.standard_reference}
                          </div>
                        </div>

                        {tc.failure_reason && (
                          <div className="p-2.5 rounded bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300">
                            Notice: {tc.failure_reason}
                          </div>
                        )}

                        {tc.metrics.length > 0 && (
                          <div className="overflow-x-auto rounded-lg border border-slate-800 mt-2">
                            <table className="w-full text-left text-xs">
                              <thead className="bg-slate-900/90 text-slate-400 text-[11px] font-mono border-b border-slate-800 uppercase">
                                <tr>
                                  <th className="py-2 px-3">Measured Parameter</th>
                                  <th className="py-2 px-3">Expected Reference</th>
                                  <th className="py-2 px-3">Simulated / Actual</th>
                                  <th className="py-2 px-3">Absolute Delta</th>
                                  <th className="py-2 px-3">Tolerance Limit</th>
                                  <th className="py-2 px-3">Status</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                                {tc.metrics.map((m, idx) => {
                                  const mPass = m.status === "VERIFIED";
                                  return (
                                    <tr key={idx} className="hover:bg-slate-800/20 transition">
                                      <td className="py-2 px-3 text-slate-200 font-sans font-medium">
                                        {m.name}
                                        {m.unit && <span className="ml-1 text-slate-400 text-[10px]">[{m.unit}]</span>}
                                      </td>
                                      <td className="py-2 px-3 text-slate-300">{m.expected_value}</td>
                                      <td className="py-2 px-3 text-slate-200 font-semibold">{m.actual_value}</td>
                                      <td className="py-2 px-3 text-emerald-400 font-semibold">{m.difference}</td>
                                      <td className="py-2 px-3 text-slate-400">±{m.tolerance}</td>
                                      <td className="py-2 px-3">
                                        <span
                                          className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                                            mPass
                                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                                              : "bg-rose-500/10 text-rose-400 border border-rose-500/30"
                                          }`}
                                        >
                                          {mPass ? "PASS" : "FAIL"}
                                        </span>
                                      </td>
                                    </tr>
                                  );
                                })}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 2: REPEATABLE SIMULATION EXPERIMENTS LABORATORY             */}
        {/* ============================================================== */}
        {activeTab === "EXPERIMENTS" && (
          <div className="space-y-6 max-w-7xl mx-auto">
            {/* Top Grid: Configure New Run + Saved Experiments */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Column: Configure Experiment Form (5 Cols) */}
              <div className="lg:col-span-5 bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4">
                <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
                  <Sliders className="w-4 h-4 text-blue-400" />
                  <span className="text-xs font-bold text-slate-100 uppercase tracking-wider">
                    Configure Repeatable Experiment
                  </span>
                </div>

                <div className="space-y-3 text-xs">
                  <div>
                    <label className="text-slate-400 block mb-1">Experiment Identifier</label>
                    <input
                      type="text"
                      value={expId}
                      onChange={(e) => setExpId(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 font-mono text-slate-200 focus:outline-none focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="text-slate-400 block mb-1">Experiment Title</label>
                    <input
                      type="text"
                      value={expName}
                      onChange={(e) => setExpName(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-blue-500"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-slate-400 block mb-1">Physics Timestep [s]</label>
                      <select
                        value={timestep}
                        onChange={(e) => setTimestep(parseFloat(e.target.value))}
                        className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1.5 font-mono text-slate-200"
                      >
                        <option value={0.001}>0.001 s (1000 Hz)</option>
                        <option value={0.002}>0.002 s (500 Hz)</option>
                        <option value={0.005}>0.005 s (200 Hz)</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-slate-400 block mb-1">Duration [s]</label>
                      <input
                        type="number"
                        step={0.5}
                        min={0.5}
                        max={10.0}
                        value={duration}
                        onChange={(e) => setDuration(parseFloat(e.target.value))}
                        className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 font-mono text-slate-200"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-slate-400 block mb-1">Trajectory Profile</label>
                      <select
                        value={trajType}
                        onChange={(e) => setTrajType(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1.5 font-mono text-slate-200"
                      >
                        <option value="quintic">Quintic (C2 Smooth)</option>
                        <option value="cubic">Cubic Spline (C1)</option>
                        <option value="trapezoidal">Trapezoidal Velocity</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-slate-400 block mb-1">Controller Architecture</label>
                      <div className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 font-mono text-slate-300">
                        Multi-Joint PID + Limit
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="text-slate-400 block mb-1">Proportional Gains (Kp) [Nm/rad]</label>
                    <input
                      type="text"
                      value={kpGains}
                      onChange={(e) => setKpGains(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 font-mono text-slate-200"
                    />
                  </div>

                  <div>
                    <label className="text-slate-400 block mb-1">Derivative Gains (Kd) [Nm·s/rad]</label>
                    <input
                      type="text"
                      value={kdGains}
                      onChange={(e) => setKdGains(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 font-mono text-slate-200"
                    />
                  </div>

                  <button
                    onClick={handleExecuteExperiment}
                    disabled={runningExperiment}
                    className="w-full py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 text-white font-semibold rounded text-xs flex items-center justify-center space-x-2 transition shadow mt-2"
                  >
                    {runningExperiment ? (
                      <RotateCcw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Play className="w-4 h-4 fill-current" />
                    )}
                    <span>{runningExperiment ? "Executing in MuJoCo..." : "Run & Save Experiment"}</span>
                  </button>
                </div>
              </div>

              {/* Right Column: Persisted Experiments Table & Comparison (7 Cols) */}
              <div className="lg:col-span-7 bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div className="flex items-center space-x-2">
                    <FlaskConical className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs font-bold text-slate-100 uppercase tracking-wider">
                      Saved Local Experiments ({experimentsList.length})
                    </span>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={handleCompare}
                      disabled={loadingComparison || selectedExpIds.length < 2}
                      className="px-3 py-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-blue-400 text-xs font-medium rounded flex items-center space-x-1.5 transition border border-slate-700"
                    >
                      <GitCompare className="w-3.5 h-3.5" />
                      <span>Compare Selected ({selectedExpIds.length})</span>
                    </button>

                    <button
                      onClick={loadExperiments}
                      className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 rounded transition border border-slate-700"
                      title="Refresh"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Experiments List Table */}
                <div className="overflow-x-auto rounded-lg border border-slate-800 max-h-64 overflow-y-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950 text-slate-400 text-[11px] font-mono border-b border-slate-800 sticky top-0">
                      <tr>
                        <th className="py-2 px-3 w-8"></th>
                        <th className="py-2 px-3">ID / Title</th>
                        <th className="py-2 px-3">RMSE [mrad]</th>
                        <th className="py-2 px-3">Peak Torque</th>
                        <th className="py-2 px-3">Energy Drift</th>
                        <th className="py-2 px-3 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                      {experimentsList.map((exp) => {
                        const isChecked = selectedExpIds.includes(exp.id);
                        const isCurrent = activeExperiment?.id === exp.id;
                        return (
                          <tr
                            key={exp.id}
                            className={`hover:bg-slate-800/30 transition ${
                              isCurrent ? "bg-blue-900/10" : ""
                            }`}
                          >
                            <td className="py-2 px-3">
                              <input
                                type="checkbox"
                                checked={isChecked}
                                onChange={() => toggleExpSelection(exp.id)}
                                className="rounded bg-slate-950 border-slate-800 text-blue-500 focus:ring-0"
                              />
                            </td>
                            <td className="py-2 px-3 font-sans">
                              <div className="font-semibold text-slate-200">{exp.name}</div>
                              <div className="text-[10px] font-mono text-slate-500">{exp.id}</div>
                            </td>
                            <td className="py-2 px-3 text-emerald-400 font-bold">{exp.position_rmse_mrad}</td>
                            <td className="py-2 px-3 text-slate-300">{exp.max_torque_nm} Nm</td>
                            <td className="py-2 px-3 text-slate-400">{exp.energy_drift_j} J</td>
                            <td className="py-2 px-3 text-right">
                              <button
                                onClick={async () => {
                                  const data = await fetchValidationExperimentDetails(exp.id);
                                  setActiveExperiment(data);
                                }}
                                className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[10px] font-sans transition"
                              >
                                View
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                      {experimentsList.length === 0 && (
                        <tr>
                          <td colSpan={6} className="py-6 text-center text-slate-500 text-xs font-sans">
                            No experiments saved yet. Configure and execute an experiment above.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Comparative Analytics Results Card */}
                {comparisonData && (
                  <div className="mt-4 p-4 rounded-xl bg-slate-950 border border-blue-500/30 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="text-xs font-bold text-blue-400 flex items-center space-x-1.5">
                        <GitCompare className="w-4 h-4" />
                        <span>Multi-Experiment Comparative Analysis</span>
                      </div>
                      <span className="text-[10px] font-mono text-slate-400">
                        Base: {comparisonData.experiment_ids[0]}
                      </span>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead className="text-[10px] font-mono text-slate-400 border-b border-slate-800">
                          <tr>
                            <th className="py-1 px-2">Experiment</th>
                            <th className="py-1 px-2">RMSE [mrad]</th>
                            <th className="py-1 px-2">Δ RMSE</th>
                            <th className="py-1 px-2">RMSE Improvement</th>
                            <th className="py-1 px-2">Δ Peak Torque</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/40 font-mono text-[11px]">
                          {comparisonData.experiments.map((exp, idx) => {
                            const compKey = `${exp.id}_vs_${comparisonData.experiments[0].id}`;
                            const diff = comparisonData.comparative_analysis[compKey];
                            return (
                              <tr key={exp.id}>
                                <td className="py-1.5 px-2 font-sans font-medium text-slate-200">
                                  {exp.name} {idx === 0 && <span className="text-[10px] text-blue-400">(Base)</span>}
                                </td>
                                <td className="py-1.5 px-2 text-slate-200">{exp.position_rmse_mrad}</td>
                                <td className="py-1.5 px-2 text-slate-300">
                                  {diff ? `${diff.delta_rmse_mrad > 0 ? "+" : ""}${diff.delta_rmse_mrad}` : "-"}
                                </td>
                                <td className="py-1.5 px-2 font-bold text-emerald-400">
                                  {diff ? `${diff.rmse_improvement_percent}%` : "-"}
                                </td>
                                <td className="py-1.5 px-2 text-slate-400">
                                  {diff ? `${diff.delta_max_torque_nm > 0 ? "+" : ""}${diff.delta_max_torque_nm} Nm` : "-"}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Active Experiment Deep Dive Inspector */}
            {activeExperiment && (
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                        {activeExperiment.id}
                      </span>
                      <span className="font-bold text-sm text-slate-100">{activeExperiment.config.name}</span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1">{activeExperiment.summary}</p>
                  </div>

                  <div className="text-right font-mono text-xs">
                    <div className="text-slate-300">
                      Duration: {activeExperiment.config.duration}s @ {activeExperiment.config.timestep * 1000}ms
                    </div>
                    <div className="text-slate-500 text-[10px]">{activeExperiment.timestamp}</div>
                  </div>
                </div>

                {/* Metrics Highlights Grid */}
                <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <div className="text-[10px] font-mono text-slate-500 uppercase">Tracking RMSE</div>
                    <div className="text-base font-bold font-mono text-emerald-400 mt-0.5">
                      {(activeExperiment.metrics.position_rmse_rad * 1000).toFixed(2)}{" "}
                      <span className="text-[10px] text-slate-400 font-normal">mrad</span>
                    </div>
                  </div>

                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <div className="text-[10px] font-mono text-slate-500 uppercase">Max Pos Error</div>
                    <div className="text-base font-bold font-mono text-slate-200 mt-0.5">
                      {(activeExperiment.metrics.max_position_error_rad * 1000).toFixed(2)}{" "}
                      <span className="text-[10px] text-slate-400 font-normal">mrad</span>
                    </div>
                  </div>

                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <div className="text-[10px] font-mono text-slate-500 uppercase">Peak Torque</div>
                    <div className="text-base font-bold font-mono text-amber-400 mt-0.5">
                      {activeExperiment.metrics.max_applied_torque_nm}{" "}
                      <span className="text-[10px] text-slate-400 font-normal">Nm</span>
                    </div>
                  </div>

                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <div className="text-[10px] font-mono text-slate-500 uppercase">RMS Torque</div>
                    <div className="text-base font-bold font-mono text-slate-200 mt-0.5">
                      {activeExperiment.metrics.rms_torque_nm}{" "}
                      <span className="text-[10px] text-slate-400 font-normal">Nm</span>
                    </div>
                  </div>

                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <div className="text-[10px] font-mono text-slate-500 uppercase">Energy Drift</div>
                    <div className="text-base font-bold font-mono text-blue-400 mt-0.5">
                      {activeExperiment.metrics.energy_drift_j}{" "}
                      <span className="text-[10px] text-slate-400 font-normal">J</span>
                    </div>
                  </div>

                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <div className="text-[10px] font-mono text-slate-500 uppercase">Real-Time Factor</div>
                    <div className="text-base font-bold font-mono text-purple-400 mt-0.5">
                      {activeExperiment.metrics.real_time_factor}x
                    </div>
                  </div>
                </div>

                {/* Time-Series Preview Table */}
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-slate-300">
                    Recorded Downsampled Trajectory Samples (Every 10 Physics Steps)
                  </div>
                  <div className="overflow-x-auto rounded-lg border border-slate-800 max-h-48 overflow-y-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-950 text-slate-400 text-[10px] font-mono border-b border-slate-800 sticky top-0">
                        <tr>
                          <th className="py-1.5 px-3">Time [s]</th>
                          <th className="py-1.5 px-3">Target Joint 1-3 [rad]</th>
                          <th className="py-1.5 px-3">Actual Joint 1-3 [rad]</th>
                          <th className="py-1.5 px-3">Position Errors [rad]</th>
                          <th className="py-1.5 px-3">Actuator Torques [Nm]</th>
                          <th className="py-1.5 px-3">Total Energy [J]</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/40 font-mono text-[10px]">
                        {activeExperiment.time_series.timestamps.slice(0, 25).map((t, idx) => (
                          <tr key={idx} className="hover:bg-slate-800/20">
                            <td className="py-1 px-3 text-slate-400">{t.toFixed(3)}</td>
                            <td className="py-1 px-3 text-slate-300">
                              [{activeExperiment.time_series.q_target[idx]?.slice(0, 3).join(", ")}]
                            </td>
                            <td className="py-1 px-3 text-emerald-400">
                              [{activeExperiment.time_series.q_actual[idx]?.slice(0, 3).join(", ")}]
                            </td>
                            <td className="py-1 px-3 text-slate-400">
                              [{activeExperiment.time_series.position_errors[idx]?.slice(0, 3).join(", ")}]
                            </td>
                            <td className="py-1 px-3 text-amber-400">
                              [{activeExperiment.time_series.torques[idx]?.slice(0, 3).join(", ")}]
                            </td>
                            <td className="py-1 px-3 text-blue-300">
                              {activeExperiment.time_series.energies[idx]}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ============================================================== */}
        {/* TAB 3: FORMAL VALIDATION REPORT MARKDOWN VIEWER                 */}
        {/* ============================================================== */}
        {activeTab === "REPORT" && (
          <div className="max-w-5xl mx-auto space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h2 className="text-sm font-bold text-slate-100 flex items-center space-x-2">
                  <FileText className="w-4 h-4 text-amber-400" />
                  <span>Formal Engineering Validation & Certification Document</span>
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Analytical standards citation, mathematical derivations, and multi-test verification summary.
                </p>
              </div>

              <button
                onClick={loadMarkdownReport}
                disabled={loadingReport}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs flex items-center space-x-1.5 transition border border-slate-700"
              >
                <RotateCcw className={`w-3.5 h-3.5 ${loadingReport ? "animate-spin" : ""}`} />
                <span>Refresh Document</span>
              </button>
            </div>

            {loadingReport ? (
              <div className="p-12 text-center text-slate-400 text-xs flex items-center justify-center space-x-2">
                <RotateCcw className="w-4 h-4 animate-spin text-amber-400" />
                <span>Compiling engineering verification report...</span>
              </div>
            ) : (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 font-mono text-xs leading-relaxed text-slate-200 overflow-x-auto whitespace-pre-wrap selection:bg-blue-600 selection:text-white">
                {reportMarkdown}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
