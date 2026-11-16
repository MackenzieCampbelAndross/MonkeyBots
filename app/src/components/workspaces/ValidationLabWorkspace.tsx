import React from "react";
import { useAppStore } from "../../store/useAppStore";
import {
  ShieldCheck,
  Play,
  RotateCcw,
  CheckCircle2,
  Clock,
  Award,
} from "lucide-react";

export const ValidationLabWorkspace: React.FC = () => {
  const { validationTests, runValidationTest, resetValidationTests, addToast } = useAppStore();

  const handleRunAll = () => {
    validationTests.forEach((t) => runValidationTest(t.id));
    addToast("info", "Executing Test Suite", "Running 5 physical validation experiments at 500 Hz...");
  };

  const passedCount = validationTests.filter((t) => t.status === "PASSED").length;

  return (
    <div className="flex-1 overflow-y-auto p-6 bg-slate-950 text-slate-100 select-none space-y-6">
      {/* Workspace Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <span>Validation Laboratory & Engineering Benchmarks</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Rigorous mathematical verification: kinematics closure, dynamic stability, torque limits, and contact restitution.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={resetValidationTests}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded font-medium text-xs flex items-center space-x-1.5 transition border border-slate-700"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Suite</span>
          </button>

          <button
            onClick={handleRunAll}
            className="px-4 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded font-semibold text-xs flex items-center space-x-1.5 transition shadow"
          >
            <Play className="w-3.5 h-3.5" />
            <span>Run All Benchmarks</span>
          </button>
        </div>
      </div>

      {/* Certification Scorecard */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-emerald-500/10 border border-emerald-500/30 rounded-lg flex items-center justify-center text-emerald-400">
            <Award className="w-6 h-6" />
          </div>
          <div>
            <div className="text-sm font-bold text-slate-100">
              Robotics Validation Status: {passedCount === validationTests.length ? "VERIFIED" : "PENDING"}
            </div>
            <div className="text-xs text-slate-400 mt-0.5">
              {passedCount} of {validationTests.length} engineering verification experiments passed.
            </div>
          </div>
        </div>

        <div className="text-right font-mono">
          <div className="text-2xl font-bold text-emerald-400">
            {((passedCount / validationTests.length) * 100).toFixed(0)}%
          </div>
          <div className="text-[10px] text-slate-400 uppercase">Compliance Score</div>
        </div>
      </div>

      {/* Test Cases Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="p-3 border-b border-slate-800 text-xs font-semibold text-slate-200">
          AUTOMATED VERIFICATION EXPERIMENTS
        </div>

        <div className="divide-y divide-slate-800">
          {validationTests.map((t) => (
            <div key={t.id} className="p-4 hover:bg-slate-800/20 transition space-y-2">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center space-x-3">
                  {t.status === "PASSED" ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  ) : t.status === "RUNNING" ? (
                    <Clock className="w-4 h-4 text-amber-400 animate-spin shrink-0" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-slate-600 shrink-0" />
                  )}
                  <div>
                    <span className="font-semibold text-slate-200">{t.name}</span>
                    <span className="ml-2 text-[10px] px-1.5 py-0.5 bg-slate-800 text-slate-400 rounded font-mono">
                      {t.category}
                    </span>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <div className="text-right font-mono">
                    <div className="text-xs font-bold text-slate-100">{t.metricValue}</div>
                    <div className="text-[10px] text-slate-400">Tol: {t.tolerance}</div>
                  </div>

                  <button
                    onClick={() => runValidationTest(t.id)}
                    className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[11px] font-medium transition"
                  >
                    Run
                  </button>
                </div>
              </div>

              <p className="text-[11px] text-slate-400 pl-7 leading-relaxed">{t.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
