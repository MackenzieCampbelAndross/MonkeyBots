import React from "react";
import { useAppStore } from "../store/useAppStore";
import { fetchProjectDetails } from "../services/api";
import { Folder, Box, CheckCircle2 } from "lucide-react";

export const ProjectExplorer: React.FC = () => {
  const { projects, activeProjectId, setActiveProject, addLog } = useAppStore();

  const handleSelectProject = async (id: string) => {
    try {
      const manifest = await fetchProjectDetails(id);
      setActiveProject(manifest, id);
      addLog("INFO", "ProjectExplorer", `Loaded project '${manifest.metadata.name}'`);
    } catch (err: any) {
      addLog("ERROR", "ProjectExplorer", `Failed to load project: ${err.message}`);
    }
  };

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-full select-none">
      <div className="p-3 border-b border-slate-800 flex items-center space-x-2 text-xs font-semibold text-slate-200">
        <Folder className="w-4 h-4 text-sky-400" />
        <span>LOCAL PROJECTS</span>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {projects.length === 0 ? (
          <div className="p-4 text-center text-xs text-slate-400">Scanning local filesystem...</div>
        ) : (
          projects.map((p) => {
            const isSelected = activeProjectId === p.id;
            return (
              <div
                key={p.id}
                onClick={() => handleSelectProject(p.id)}
                className={`p-2.5 rounded-lg border text-xs cursor-pointer transition flex flex-col space-y-1 ${
                  isSelected
                    ? "bg-sky-950/40 border-sky-500/50 text-sky-200"
                    : "bg-slate-950/40 border-slate-800/80 hover:bg-slate-800/40 text-slate-300"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 font-medium truncate">
                    <Box className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                    <span className="truncate">{p.name}</span>
                  </div>
                  {isSelected && <CheckCircle2 className="w-3.5 h-3.5 text-sky-400 shrink-0" />}
                </div>

                <div className="text-[10px] text-slate-400 truncate">{p.description}</div>

                <div className="flex items-center space-x-2 pt-1 text-[9px] text-slate-400">
                  <span className="px-1.5 py-0.5 bg-slate-800 rounded font-mono">{p.dof} DOF</span>
                  {p.has_mjcf && <span className="text-emerald-400">MJCF</span>}
                  {p.has_urdf && <span className="text-sky-400">URDF</span>}
                </div>
              </div>
            );
          })
        )}
      </div>

      <div className="p-3 border-t border-slate-800 text-[10px] text-slate-400 flex items-center justify-between">
        <span>Filesystem: Pure Local</span>
        <span className="text-emerald-400 font-mono">Zero Cloud</span>
      </div>
    </aside>
  );
};
