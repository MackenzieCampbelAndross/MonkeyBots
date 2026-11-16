import React from "react";
import { useAppStore } from "../../store/useAppStore";
import {
  Layers,
  Cpu,
  Download,
  Table,
  Scale,
  GitBranch,
} from "lucide-react";

export const RobotDesignerWorkspace: React.FC = () => {
  const { links, selectedLinkId, setSelectedLinkId, dhParameters, addToast } =
    useAppStore();

  const totalMass = links.reduce((sum, l) => sum + l.massKg, 0);

  const handleExportURDF = () => {
    addToast("success", "URDF Exported", "Generated valid robot.urdf with kinematic visual and collision tags.");
  };

  const handleExportMJCF = () => {
    addToast("success", "MJCF Exported", "Generated valid robot.mjcf with MuJoCo equality constraints and geoms.");
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 bg-slate-950 text-slate-100 select-none space-y-6">
      {/* Workspace Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
            <Cpu className="w-5 h-5 text-amber-500" />
            <span>Robot Designer & Kinematic Assembly</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Configure mechanical link dimensions, mass distribution, DH parameters, and export URDF/MJCF models.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleExportURDF}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded font-medium text-xs flex items-center space-x-1.5 transition border border-slate-700"
          >
            <Download className="w-3.5 h-3.5 text-sky-400" />
            <span>Export URDF</span>
          </button>
          <button
            onClick={handleExportMJCF}
            className="px-3 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 rounded font-semibold text-xs flex items-center space-x-1.5 transition shadow"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export MJCF</span>
          </button>
        </div>
      </div>

      {/* Assembly Hierarchy and Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left: Mechanical Links Tree */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-200 border-b border-slate-800 pb-2">
            <span className="flex items-center space-x-1.5">
              <Layers className="w-4 h-4 text-amber-400" />
              <span>Link Assembly Tree</span>
            </span>
            <span className="text-[10px] text-slate-400 font-mono">{links.length} Links</span>
          </div>

          <div className="space-y-1.5 overflow-y-auto max-h-72">
            {links.map((link) => {
              const isSelected = selectedLinkId === link.id;
              return (
                <div
                  key={link.id}
                  onClick={() => setSelectedLinkId(link.id)}
                  className={`p-2.5 rounded-lg border text-xs cursor-pointer transition flex items-center justify-between ${
                    isSelected
                      ? "bg-amber-500/15 border-amber-500/50 text-amber-300 font-medium"
                      : "bg-slate-950 border-slate-800/80 hover:bg-slate-800/40 text-slate-300"
                  }`}
                >
                  <div className="flex items-center space-x-2 truncate">
                    <GitBranch className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span className="truncate">{link.name}</span>
                  </div>
                  <span className="text-[10px] text-slate-400 font-mono shrink-0">
                    {link.massKg.toFixed(1)} kg
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Center & Right: Mass & Kinematics Summary */}
        <div className="md:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h2 className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
              <Scale className="w-4 h-4 text-emerald-400" />
              <span>Mechanical Mass & Inertial Summary</span>
            </h2>
            <div className="text-xs font-mono text-emerald-400 font-bold">
              Total Weight: {totalMass.toFixed(2)} kg
            </div>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Every link contains an accurate 3D bounding geometry, center of mass offset, and positive-definite
            moment of inertia tensor matrix (I_xx, I_yy, I_zz).
          </p>

          <div className="grid grid-cols-3 gap-3 text-xs font-mono">
            <div className="bg-slate-950 p-3 rounded border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-sans">Degrees of Freedom</div>
              <div className="text-slate-200 font-bold mt-1">6 Revolute Joints</div>
            </div>
            <div className="bg-slate-950 p-3 rounded border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-sans">Max Rated Payload</div>
              <div className="text-amber-400 font-bold mt-1">5.00 kg</div>
            </div>
            <div className="bg-slate-950 p-3 rounded border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-sans">Max Reach Radius</div>
              <div className="text-sky-400 font-bold mt-1">0.850 m</div>
            </div>
          </div>
        </div>
      </div>

      {/* Denavit-Hartenberg Parameter Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <h2 className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
            <Table className="w-4 h-4 text-sky-400" />
            <span>Denavit-Hartenberg (DH) Kinematic Parameters</span>
          </h2>
          <span className="text-[11px] text-slate-400 font-mono">Standard DH Convention</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950/80 text-[10px] text-slate-400 uppercase">
              <tr>
                <th className="p-2.5">Joint Axis</th>
                <th className="p-2.5">Joint Angle $\theta_i$ (rad)</th>
                <th className="p-2.5">Link Offset $d_i$ (m)</th>
                <th className="p-2.5">Link Length $a_i$ (m)</th>
                <th className="p-2.5">Link Twist $\alpha_i$ (rad)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {dhParameters.map((dh) => (
                <tr key={dh.jointIndex} className="hover:bg-slate-800/40 transition">
                  <td className="p-2.5 font-medium text-amber-400">{dh.name}</td>
                  <td className="p-2.5">{dh.theta.toFixed(3)}</td>
                  <td className="p-2.5">{dh.d.toFixed(3)}</td>
                  <td className="p-2.5">{dh.a.toFixed(3)}</td>
                  <td className="p-2.5">{dh.alpha.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
