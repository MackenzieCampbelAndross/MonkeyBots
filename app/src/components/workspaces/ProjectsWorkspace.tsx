import React, { useState } from "react";
import { useAppStore } from "../../store/useAppStore";
import { fetchProjectDetails } from "../../services/api";
import {
  FolderOpen,
  Plus,
  Box,
  FileCode,
  CheckCircle2,
} from "lucide-react";

export const ProjectsWorkspace: React.FC = () => {
  const { projects, activeProjectId, setActiveProject, setActiveWorkspace, addToast, addLog } =
    useAppStore();

  const [selectedProjId, setSelectedProjId] = useState<string>(activeProjectId || projects[0]?.id || "");

  const handleOpenProject = async (id: string) => {
    try {
      const manifest = await fetchProjectDetails(id);
      setActiveProject(manifest, id);
      setSelectedProjId(id);
      addToast("success", "Project Opened", `Loaded manifest for '${manifest.metadata.name}'`);
      addLog("INFO", "Projects", `Active project set to ${id}`);
    } catch (err: any) {
      addToast("error", "Failed to Open Project", err.message);
    }
  };

  const activeProjSummary = projects.find((p) => p.id === (selectedProjId || activeProjectId)) || projects[0];

  return (
    <div className="flex-1 overflow-y-auto p-6 bg-slate-950 text-slate-100 select-none space-y-6">
      {/* Workspace Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
            <FolderOpen className="w-5 h-5 text-amber-500" />
            <span>Local Filesystem Projects</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            100% file-based storage. Zero databases. Read, edit, and version-control directly.
          </p>
        </div>

        <button
          onClick={() => addToast("info", "Create Project", "Project creation wizard ready.")}
          className="px-3.5 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 rounded font-semibold text-xs flex items-center space-x-1.5 transition shadow"
        >
          <Plus className="w-4 h-4" />
          <span>New Robot Project</span>
        </button>
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {projects.map((p) => {
          const isSelected = p.id === (activeProjectId || selectedProjId);
          return (
            <div
              key={p.id}
              onClick={() => handleOpenProject(p.id)}
              className={`p-4 rounded-xl border text-xs cursor-pointer transition flex flex-col justify-between space-y-3 ${
                isSelected
                  ? "bg-amber-500/10 border-amber-500/50 text-slate-100 shadow"
                  : "bg-slate-900 border-slate-800 hover:border-slate-700 text-slate-300"
              }`}
            >
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 font-bold text-sm text-slate-100">
                    <Box className="w-4 h-4 text-amber-500" />
                    <span>{p.name}</span>
                  </div>
                  {isSelected && <CheckCircle2 className="w-4 h-4 text-amber-500" />}
                </div>
                <p className="text-slate-400 text-[11px] leading-relaxed line-clamp-2">
                  {p.description}
                </p>
              </div>

              <div className="space-y-2 pt-2 border-t border-slate-800/80">
                <div className="flex items-center space-x-2 font-mono text-[10px] text-slate-400">
                  <span className="px-1.5 py-0.5 bg-slate-800 rounded text-slate-200">{p.dof} DOF</span>
                  {p.has_mjcf && <span className="text-emerald-400">MJCF Valid</span>}
                  {p.has_urdf && <span className="text-sky-400">URDF Valid</span>}
                </div>
                <div className="text-[10px] text-slate-400 font-mono truncate">{p.path}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Detailed Project Inspector Card */}
      {activeProjSummary && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-xs font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
              <FileCode className="w-4 h-4 text-sky-400" />
              <span>Project Manifest Inspector (`project.json`)</span>
            </h2>
            <button
              onClick={() => setActiveWorkspace("simulation")}
              className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded font-medium text-xs transition border border-slate-700"
            >
              Simulate Active Project
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
            <div className="bg-slate-950 p-3 rounded border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-sans">Degrees of Freedom</div>
              <div className="text-amber-400 font-bold mt-1">{activeProjSummary.dof} Actuated Axes</div>
            </div>
            <div className="bg-slate-950 p-3 rounded border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-sans">Primary Model</div>
              <div className="text-slate-200 mt-1">robot.mjcf</div>
            </div>
            <div className="bg-slate-950 p-3 rounded border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-sans">Storage Paradigm</div>
              <div className="text-emerald-400 font-medium mt-1">Pure Filesystem</div>
            </div>
            <div className="bg-slate-950 p-3 rounded border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-sans">Version Control</div>
              <div className="text-sky-400 font-medium mt-1">Git Compatible</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
