import React, { useState, useEffect, useCallback } from "react";
import { useAppStore } from "../../store/useAppStore";
import {
  fetchProjects,
  fetchProjectDetails,
  createProject,
  duplicateProject,
  renameProject,
  deleteProject,
  validateProject,
  createProjectBackup,
  fetchProjectBackups,
  restoreProjectBackup,
} from "../../services/api";
import type {
  ProjectManifest,
  ProjectIntegrityReport,
  CreateProjectPayload,
  BackupItem,
} from "../../types/api";
import {
  FolderOpen,
  Plus,
  Box,
  CheckCircle2,
  AlertTriangle,
  Copy,
  Edit3,
  Trash2,
  Archive,
  RefreshCw,
  Search,
  ShieldCheck,
  HardDrive,
  Upload,
  ChevronRight,
} from "lucide-react";

export const ProjectsWorkspace: React.FC = () => {
  const {
    projects,
    activeProjectId,
    setProjects,
    setActiveProject,
    setActiveWorkspace,
    addToast,
    addLog,
  } = useAppStore();

  const [loading, setLoading] = useState<boolean>(false);
  const [selectedProjId, setSelectedProjId] = useState<string>(activeProjectId || projects[0]?.id || "");
  const [activeManifest, setActiveManifest] = useState<ProjectManifest | null>(null);
  const [integrityReport, setIntegrityReport] = useState<ProjectIntegrityReport | null>(null);
  const [backupsList, setBackupsList] = useState<BackupItem[]>([]);
  const [validating, setValidating] = useState<boolean>(false);

  // Search & Filters
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedType, setSelectedType] = useState<string>("ALL");

  // Modals state
  const [showNewModal, setShowNewModal] = useState<boolean>(false);
  const [showRenameModal, setShowRenameModal] = useState<boolean>(false);
  const [showDeleteModal, setShowDeleteModal] = useState<boolean>(false);
  const [showBackupModal, setShowBackupModal] = useState<boolean>(false);

  // Form states
  const [newProjName, setNewProjName] = useState<string>("SCARA Assembly Robot");
  const [newProjDesc, setNewProjDesc] = useState<string>("High precision 4-axis pick and place assembly robot");
  const [newProjPreset, setNewProjPreset] = useState<"6dof_industrial" | "workcell" | "blank">("6dof_industrial");
  const [newProjType, setNewProjType] = useState<string>("Articulated Arm");
  const [renameTargetName, setRenameTargetName] = useState<string>("");
  const [restoreFilePath, setRestoreFilePath] = useState<string>("");

  // Load project list
  const loadProjects = useCallback(async () => {
    setLoading(true);
    try {
      const list = await fetchProjects();
      setProjects(list);
      if (!selectedProjId && list.length > 0) {
        setSelectedProjId(list[0].id);
      }
    } catch (err: any) {
      addToast("error", "Error Loading Projects", err.message);
    } finally {
      setLoading(false);
    }
  }, [selectedProjId, setProjects, addToast]);

  // Load project details & integrity
  const loadDetails = useCallback(async (projId: string) => {
    if (!projId) return;
    try {
      const [manifest, report] = await Promise.all([
        fetchProjectDetails(projId),
        validateProject(projId).catch(() => null),
      ]);
      setActiveManifest(manifest);
      setIntegrityReport(report);
      fetchProjectBackups(projId).then((res) => setBackupsList(res.backups)).catch(() => {});
    } catch (err: any) {
      addToast("error", "Failed to Load Manifest", err.message);
    }
  }, [addToast]);

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (selectedProjId) {
      loadDetails(selectedProjId);
    }
  }, [selectedProjId, loadDetails]);

  // Open Project as Active Workspace
  const handleOpenProject = async (projId: string) => {
    try {
      const manifest = await fetchProjectDetails(projId);
      setActiveProject(manifest, projId);
      setSelectedProjId(projId);
      addToast("success", "Project Activated", `Loaded project '${manifest.metadata.name}'`);
      addLog("INFO", "Projects", `Active project set to ${projId}`);
    } catch (err: any) {
      addToast("error", "Failed to Open Project", err.message);
    }
  };

  // Run Integrity Audit
  const handleRunAudit = async (projId: string) => {
    setValidating(true);
    try {
      const rep = await validateProject(projId);
      setIntegrityReport(rep);
      addToast(
        rep.is_valid ? "success" : "warning",
        "Integrity Audit Complete",
        `Status: ${rep.status} | Checked ${rep.total_assets} assets`
      );
    } catch (err: any) {
      addToast("error", "Audit Error", err.message);
    } finally {
      setValidating(false);
    }
  };

  // Create Project
  const handleCreateProject = async () => {
    try {
      const payload: CreateProjectPayload = {
        name: newProjName,
        description: newProjDesc,
        robot_preset: newProjPreset,
        robot_type: newProjType,
        author: "MonkeyBots Engineer",
      };
      const created = await createProject(payload);
      setShowNewModal(false);
      await loadProjects();
      setSelectedProjId(created.metadata.id || "");
      addToast("success", "Project Created", `Successfully initialized '${created.metadata.name}'`);
    } catch (err: any) {
      addToast("error", "Creation Failed", err.message);
    }
  };

  // Duplicate Project
  const handleDuplicate = async (projId: string) => {
    try {
      const dup = await duplicateProject(projId);
      await loadProjects();
      setSelectedProjId(dup.metadata.id || "");
      addToast("success", "Project Cloned", `Created duplicate '${dup.metadata.name}'`);
    } catch (err: any) {
      addToast("error", "Duplicate Failed", err.message);
    }
  };

  // Rename Project
  const handleRename = async () => {
    if (!selectedProjId || !renameTargetName) return;
    try {
      const updated = await renameProject(selectedProjId, renameTargetName);
      setShowRenameModal(false);
      await loadProjects();
      setActiveManifest(updated);
      addToast("success", "Project Renamed", `Updated title to '${updated.metadata.name}'`);
    } catch (err: any) {
      addToast("error", "Rename Failed", err.message);
    }
  };

  // Delete Project
  const handleDelete = async () => {
    if (!selectedProjId) return;
    try {
      await deleteProject(selectedProjId);
      setShowDeleteModal(false);
      addToast("info", "Project Deleted", `Removed project '${selectedProjId}' from disk`);
      await loadProjects();
      setSelectedProjId(projects.find((p) => p.id !== selectedProjId)?.id || "");
    } catch (err: any) {
      addToast("error", "Deletion Failed", err.message);
    }
  };

  // Create Backup
  const handleCreateBackup = async (projId: string) => {
    try {
      const res = await createProjectBackup(projId);
      addToast("success", "Backup Archive Created", `Saved package to ${res.filename}`);
      fetchProjectBackups(projId).then((r) => setBackupsList(r.backups)).catch(() => {});
    } catch (err: any) {
      addToast("error", "Backup Failed", err.message);
    }
  };

  // Restore Backup
  const handleRestoreBackup = async () => {
    if (!restoreFilePath) return;
    try {
      const restored = await restoreProjectBackup(restoreFilePath);
      setShowBackupModal(false);
      await loadProjects();
      setSelectedProjId(restored.metadata.id || "");
      addToast("success", "Backup Restored", `Restored project '${restored.metadata.name}'`);
    } catch (err: any) {
      addToast("error", "Restore Failed", err.message);
    }
  };

  // Filter projects
  const filteredProjects = projects.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType =
      selectedType === "ALL" || (p.robot_type && p.robot_type.toUpperCase().includes(selectedType));
    return matchesSearch && matchesType;
  });

  const selectedSummary = projects.find((p) => p.id === selectedProjId) || projects[0];

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950 text-slate-100 overflow-hidden select-none">
      {/* Workspace Header */}
      <div className="flex items-center justify-between px-6 py-3.5 border-b border-slate-800 bg-slate-900/60 shrink-0">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-500">
            <FolderOpen className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-slate-100 tracking-wide flex items-center space-x-2">
              <span>LOCAL PROJECT MANAGEMENT & STORAGE</span>
              <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">
                STAGE 11
              </span>
            </h1>
            <p className="text-[11px] text-slate-400 font-sans">
              100% database-free structured filesystem storage. Atomic persistence, revisions, backups, and integrity verification.
            </p>
          </div>
        </div>

        {/* Global Header Actions */}
        <div className="flex items-center space-x-2.5">
          <button
            onClick={() => setShowBackupModal(true)}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs font-medium flex items-center space-x-1.5 transition border border-slate-700"
          >
            <Upload className="w-3.5 h-3.5 text-blue-400" />
            <span>Restore Backup</span>
          </button>

          <button
            onClick={() => setShowNewModal(true)}
            className="px-3.5 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 rounded font-semibold text-xs flex items-center space-x-1.5 transition shadow"
          >
            <Plus className="w-4 h-4" />
            <span>New Robot Project</span>
          </button>

          <button
            onClick={loadProjects}
            className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 rounded transition border border-slate-700"
            title="Refresh Projects"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Main Workspace Layout (Two-Column) */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Column: Project Browser & Filter (7 Cols equivalent) */}
        <div className="flex-1 flex flex-col border-r border-slate-800 overflow-hidden bg-slate-950/60">
          {/* Search & Filter Toolbar */}
          <div className="p-4 border-b border-slate-800 flex items-center space-x-3 bg-slate-900/40 shrink-0">
            <div className="relative flex-1">
              <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
              <input
                type="text"
                placeholder="Search local projects..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-md pl-8 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-500/60 font-sans"
              />
            </div>

            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1.5 text-xs text-slate-300 font-mono focus:outline-none"
            >
              <option value="ALL">All Robot Types</option>
              <option value="ARTICULATED">Articulated Arm</option>
              <option value="SCARA">SCARA Manipulator</option>
              <option value="MOBILE">Mobile Robot</option>
            </select>
          </div>

          {/* Projects Grid / List */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {filteredProjects.map((p) => {
              const isSelected = p.id === selectedProjId;
              const isActive = p.id === activeProjectId;
              const isHealthy = p.integrity_status === "HEALTHY";

              return (
                <div
                  key={p.id}
                  onClick={() => setSelectedProjId(p.id)}
                  className={`p-4 rounded-xl border text-xs cursor-pointer transition flex flex-col justify-between space-y-3 shadow-sm ${
                    isSelected
                      ? "bg-slate-900 border-amber-500/60 ring-1 ring-amber-500/30"
                      : "bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900/90"
                  }`}
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Box className={`w-4 h-4 ${isActive ? "text-amber-400" : "text-slate-400"}`} />
                        <span className="font-bold text-sm text-slate-100">{p.name}</span>
                        {isActive && (
                          <span className="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">
                            ACTIVE
                          </span>
                        )}
                      </div>

                      <div className="flex items-center space-x-2">
                        <span
                          className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full flex items-center space-x-1 border ${
                            isHealthy
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                              : "bg-amber-500/10 text-amber-400 border-amber-500/30"
                          }`}
                        >
                          {isHealthy ? <CheckCircle2 className="w-3 h-3" /> : <AlertTriangle className="w-3 h-3" />}
                          <span>{p.integrity_status || "HEALTHY"}</span>
                        </span>
                      </div>
                    </div>

                    <p className="text-slate-400 text-[11px] leading-relaxed line-clamp-2">
                      {p.description || "No description provided."}
                    </p>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-[10px] font-mono text-slate-400">
                    <div className="flex items-center space-x-2">
                      <span className="px-1.5 py-0.5 bg-slate-800 rounded text-slate-200 font-semibold">
                        {p.dof} DOF
                      </span>
                      <span className="text-slate-300">{p.robot_type || "Manipulator"}</span>
                      {p.has_mjcf && <span className="text-emerald-400">MJCF</span>}
                      {p.has_urdf && <span className="text-sky-400">URDF</span>}
                    </div>

                    <div className="flex items-center space-x-3 text-slate-500">
                      <span>{(p.size_bytes ? (p.size_bytes / 1024).toFixed(0) : "12")} KB</span>
                      <span>{p.updated_at ? p.updated_at.slice(0, 10) : "Today"}</span>
                    </div>
                  </div>
                </div>
              );
            })}

            {filteredProjects.length === 0 && (
              <div className="py-12 text-center text-slate-500 text-xs font-sans space-y-2">
                <FolderOpen className="w-8 h-8 mx-auto text-slate-600" />
                <div>No local projects match your filter.</div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Selected Project Inspector & Action Center (5 Cols) */}
        <div className="w-96 flex flex-col overflow-y-auto bg-slate-900/40 p-5 space-y-5 shrink-0 border-l border-slate-800/60">
          {selectedSummary ? (
            <>
              {/* Project Title Card & Primary Action */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-[10px] font-mono text-amber-500 font-semibold uppercase">
                      Selected Project
                    </span>
                    <h2 className="text-sm font-bold text-slate-100 mt-0.5">{selectedSummary.name}</h2>
                    <div className="text-[10px] font-mono text-slate-500">{selectedSummary.id}</div>
                  </div>

                  <button
                    onClick={() => handleOpenProject(selectedSummary.id)}
                    className="px-3 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs rounded shadow transition flex items-center space-x-1"
                  >
                    <span>Activate</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="text-[11px] text-slate-400 leading-relaxed font-sans">
                  {selectedSummary.description || "Local robotics engineering workspace."}
                </div>

                <div className="flex items-center space-x-2 pt-1">
                  <button
                    onClick={() => {
                      handleOpenProject(selectedSummary.id);
                      setActiveWorkspace("simulation");
                    }}
                    className="flex-1 py-1.5 bg-slate-800 hover:bg-slate-700 text-sky-400 font-semibold rounded text-xs transition border border-slate-700 text-center"
                  >
                    Launch Simulation
                  </button>
                </div>

                {/* Quick Action Buttons Toolbar */}
                <div className="grid grid-cols-4 gap-1.5 pt-2 border-t border-slate-800 text-[11px]">
                  <button
                    onClick={() => handleDuplicate(selectedSummary.id)}
                    className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded flex flex-col items-center justify-center space-y-1 transition border border-slate-700/60"
                    title="Duplicate Project"
                  >
                    <Copy className="w-3.5 h-3.5 text-blue-400" />
                    <span className="text-[9px]">Clone</span>
                  </button>

                  <button
                    onClick={() => {
                      setRenameTargetName(selectedSummary.name);
                      setShowRenameModal(true);
                    }}
                    className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded flex flex-col items-center justify-center space-y-1 transition border border-slate-700/60"
                    title="Rename Project"
                  >
                    <Edit3 className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-[9px]">Rename</span>
                  </button>

                  <button
                    onClick={() => handleCreateBackup(selectedSummary.id)}
                    className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded flex flex-col items-center justify-center space-y-1 transition border border-slate-700/60"
                    title="Export .mbpkg Archive"
                  >
                    <Archive className="w-3.5 h-3.5 text-amber-400" />
                    <span className="text-[9px]">Backup</span>
                  </button>

                  <button
                    onClick={() => setShowDeleteModal(true)}
                    className="p-1.5 bg-slate-800 hover:bg-rose-950/60 text-rose-400 rounded flex flex-col items-center justify-center space-y-1 transition border border-slate-700/60"
                    title="Delete Project"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span className="text-[9px]">Delete</span>
                  </button>
                </div>
              </div>

              {/* Physical Storage & Filesystem Context */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
                <div className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center space-x-1.5">
                  <HardDrive className="w-3.5 h-3.5 text-sky-400" />
                  <span>Filesystem Storage Inventory</span>
                </div>

                <div className="text-[10px] font-mono text-slate-400 bg-slate-950 p-2.5 rounded border border-slate-800 truncate" title={selectedSummary.path}>
                  {selectedSummary.path}
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="bg-slate-950 p-2 rounded border border-slate-800">
                    <div className="text-[9px] text-slate-500 uppercase font-sans">Primary Model</div>
                    <div className="text-slate-200 font-bold mt-0.5 truncate">
                      {activeManifest?.robot.model_file || "robot.mjcf"}
                    </div>
                  </div>

                  <div className="bg-slate-950 p-2 rounded border border-slate-800">
                    <div className="text-[9px] text-slate-500 uppercase font-sans">Integrator</div>
                    <div className="text-slate-200 font-bold mt-0.5">
                      {activeManifest?.physics.integrator || "RK4"}
                    </div>
                  </div>

                  <div className="bg-slate-950 p-2 rounded border border-slate-800">
                    <div className="text-[9px] text-slate-500 uppercase font-sans">Experiments</div>
                    <div className="text-slate-200 font-bold mt-0.5">
                      {integrityReport?.experiments_count ?? selectedSummary.experiments_count ?? 0} Saved
                    </div>
                  </div>

                  <div className="bg-slate-950 p-2 rounded border border-slate-800">
                    <div className="text-[9px] text-slate-500 uppercase font-sans">Trajectories</div>
                    <div className="text-slate-200 font-bold mt-0.5">
                      {integrityReport?.trajectories_count ?? selectedSummary.trajectories_count ?? 0} Paths
                    </div>
                  </div>

                  <div className="bg-slate-950 p-2 rounded border border-slate-800">
                    <div className="text-[9px] text-slate-500 uppercase font-sans">Geometries</div>
                    <div className="text-slate-200 font-bold mt-0.5">
                      {integrityReport?.total_assets ?? 0} Assets
                    </div>
                  </div>

                  <div className="bg-slate-950 p-2 rounded border border-slate-800">
                    <div className="text-[9px] text-slate-500 uppercase font-sans">Snapshots</div>
                    <div className="text-slate-200 font-bold mt-0.5">
                      {integrityReport?.snapshots_count ?? 0} Revisions
                    </div>
                  </div>
                </div>
              </div>

              {/* Project Integrity & Missing Asset Audit Card */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center space-x-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Integrity & Asset Audit</span>
                  </div>

                  <button
                    onClick={() => handleRunAudit(selectedSummary.id)}
                    disabled={validating}
                    className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[10px] font-mono transition border border-slate-700"
                  >
                    {validating ? "Auditing..." : "Audit"}
                  </button>
                </div>

                {integrityReport ? (
                  <div className="space-y-2 text-xs">
                    <div className="flex items-center justify-between bg-slate-950 p-2 rounded border border-slate-800 font-mono text-[11px]">
                      <span>Manifest Structure:</span>
                      <span className={integrityReport.manifest_valid ? "text-emerald-400" : "text-rose-400"}>
                        {integrityReport.manifest_valid ? "VALID" : "INVALID"}
                      </span>
                    </div>

                    <div className="flex items-center justify-between bg-slate-950 p-2 rounded border border-slate-800 font-mono text-[11px]">
                      <span>MJCF Physics Model:</span>
                      <span className={integrityReport.model_mjcf_valid ? "text-emerald-400" : "text-rose-400"}>
                        {integrityReport.model_mjcf_valid ? "VERIFIED" : "MISSING"}
                      </span>
                    </div>

                    <div className="flex items-center justify-between bg-slate-950 p-2 rounded border border-slate-800 font-mono text-[11px]">
                      <span>URDF Kinematics Model:</span>
                      <span className={integrityReport.model_urdf_valid ? "text-sky-400" : "text-slate-500"}>
                        {integrityReport.model_urdf_valid ? "VERIFIED" : "NONE"}
                      </span>
                    </div>

                    <div className="flex items-center justify-between bg-slate-950 p-2 rounded border border-slate-800 font-mono text-[11px]">
                      <span>Missing Assets:</span>
                      <span className={integrityReport.missing_assets_count === 0 ? "text-emerald-400" : "text-amber-400"}>
                        {integrityReport.missing_assets_count} Missing
                      </span>
                    </div>

                    {integrityReport.warnings.length > 0 && (
                      <div className="p-2 rounded bg-amber-500/10 border border-amber-500/20 text-[10px] text-amber-300 font-mono space-y-1">
                        {integrityReport.warnings.map((w, idx) => (
                          <div key={idx}>• {w}</div>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-slate-500 text-xs text-center py-2">
                    Click Audit to scan local project files.
                  </div>
                )}
              </div>

              {/* Backups & Snapshots List */}
              {backupsList.length > 0 && (
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
                  <div className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center space-x-1.5">
                    <Archive className="w-3.5 h-3.5 text-amber-400" />
                    <span>Local Packages (.mbpkg)</span>
                  </div>

                  <div className="space-y-1.5 max-h-36 overflow-y-auto font-mono text-[10px]">
                    {backupsList.map((bkp, idx) => (
                      <div
                        key={idx}
                        className="p-2 rounded bg-slate-950 border border-slate-800 flex items-center justify-between"
                      >
                        <div className="truncate text-slate-300 pr-2">{bkp.filename}</div>
                        <span className="text-slate-500 shrink-0">{(bkp.size_bytes / 1024).toFixed(0)} KB</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-slate-500 text-xs text-center py-12">Select a project to inspect.</div>
          )}
        </div>
      </div>

      {/* MODAL: New Project */}
      {showNewModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-5 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="text-sm font-bold text-slate-100 flex items-center space-x-2">
                <FolderOpen className="w-4 h-4 text-amber-500" />
                <span>Create New Robotics Project</span>
              </div>
              <button onClick={() => setShowNewModal(false)} className="text-slate-400 hover:text-slate-200">
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 block mb-1">Project Name</label>
                <input
                  type="text"
                  value={newProjName}
                  onChange={(e) => setNewProjName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Description</label>
                <textarea
                  rows={2}
                  value={newProjDesc}
                  onChange={(e) => setNewProjDesc(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 block mb-1">Robot Preset Template</label>
                  <select
                    value={newProjPreset}
                    onChange={(e) => setNewProjPreset(e.target.value as any)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1.5 font-mono text-slate-200"
                  >
                    <option value="6dof_industrial">Industrial 6-DOF Arm</option>
                    <option value="workcell">Gripper Workcell</option>
                    <option value="blank">Blank Structure</option>
                  </select>
                </div>

                <div>
                  <label className="text-slate-400 block mb-1">Kinematic Architecture</label>
                  <select
                    value={newProjType}
                    onChange={(e) => setNewProjType(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1.5 font-mono text-slate-200"
                  >
                    <option value="Articulated Arm">Articulated Arm</option>
                    <option value="SCARA Manipulator">SCARA Manipulator</option>
                    <option value="Delta Manipulator">Delta Manipulator</option>
                    <option value="Mobile Manipulator">Mobile Manipulator</option>
                  </select>
                </div>
              </div>

              <div className="pt-2 flex justify-end space-x-2 border-t border-slate-800">
                <button
                  onClick={() => setShowNewModal(false)}
                  className="px-3 py-1.5 bg-slate-800 text-slate-300 rounded text-xs"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateProject}
                  className="px-4 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded text-xs shadow"
                >
                  Create Project Folder
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Rename */}
      {showRenameModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-sm w-full p-5 space-y-4">
            <h3 className="text-xs font-bold text-slate-100 uppercase tracking-wider">Rename Project Title</h3>
            <input
              type="text"
              value={renameTargetName}
              onChange={(e) => setRenameTargetName(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
            />
            <div className="flex justify-end space-x-2 text-xs">
              <button
                onClick={() => setShowRenameModal(false)}
                className="px-3 py-1.5 bg-slate-800 text-slate-300 rounded"
              >
                Cancel
              </button>
              <button
                onClick={handleRename}
                className="px-3.5 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded"
              >
                Save Name
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Delete Confirmation */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-rose-500/40 rounded-xl max-w-sm w-full p-5 space-y-4">
            <div className="flex items-center space-x-2 text-rose-400 font-bold text-sm">
              <AlertTriangle className="w-5 h-5" />
              <span>Confirm Local Project Deletion</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Are you sure you want to permanently delete project <strong className="text-white">'{selectedSummary?.name}'</strong>? This removes the entire folder and its experiments from disk.
            </p>
            <div className="flex justify-end space-x-2 text-xs">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="px-3 py-1.5 bg-slate-800 text-slate-300 rounded"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-1.5 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded"
              >
                Delete Forever
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Restore Backup */}
      {showBackupModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-5 space-y-4">
            <h3 className="text-xs font-bold text-slate-100 uppercase tracking-wider flex items-center space-x-2">
              <Upload className="w-4 h-4 text-blue-400" />
              <span>Restore Project from .mbpkg Archive</span>
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Enter the absolute or relative path to a valid MonkeyBots package archive file on disk.
            </p>
            <input
              type="text"
              placeholder="e.g. projects/backups/default_6dof_arm_backup.mbpkg"
              value={restoreFilePath}
              onChange={(e) => setRestoreFilePath(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-blue-500"
            />
            <div className="flex justify-end space-x-2 text-xs">
              <button
                onClick={() => setShowBackupModal(false)}
                className="px-3 py-1.5 bg-slate-800 text-slate-300 rounded"
              >
                Cancel
              </button>
              <button
                onClick={handleRestoreBackup}
                disabled={!restoreFilePath}
                className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-bold rounded shadow"
              >
                Extract & Restore
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
