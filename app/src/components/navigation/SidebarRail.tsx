import React from "react";
import { useAppStore } from "../../store/useAppStore";
import type { WorkspaceId } from "../../types/engineering";
import {
  Home,
  FolderKanban,
  Cpu,
  PlayCircle,
  Move3d,
  ShieldCheck,
  FileSpreadsheet,
  Settings,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

interface NavItem {
  id: WorkspaceId;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  hotkey: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: "home", label: "Home", icon: Home, hotkey: "1" },
  { id: "projects", label: "Projects", icon: FolderKanban, hotkey: "2" },
  { id: "designer", label: "Robot Designer", icon: Cpu, hotkey: "3" },
  { id: "simulation", label: "Simulation", icon: PlayCircle, hotkey: "4" },
  { id: "motion", label: "Motion & Control", icon: Move3d, hotkey: "5" },
  { id: "validation", label: "Validation Lab", icon: ShieldCheck, hotkey: "6" },
  { id: "reports", label: "Reports", icon: FileSpreadsheet, hotkey: "7" },
  { id: "settings", label: "Settings", icon: Settings, hotkey: "8" },
];

export const SidebarRail: React.FC = () => {
  const { activeWorkspace, setActiveWorkspace, isSidebarCollapsed, toggleSidebar, addToast } =
    useAppStore();

  const handleSelect = (id: WorkspaceId, label: string) => {
    setActiveWorkspace(id);
    addToast("info", "Workspace Switched", `Active Workspace: ${label}`);
  };

  return (
    <aside
      className={`bg-slate-900 border-r border-slate-800 flex flex-col justify-between select-none transition-all duration-200 z-20 ${
        isSidebarCollapsed ? "w-14" : "w-52"
      }`}
    >
      {/* Brand Header */}
      <div className="h-12 border-b border-slate-800 flex items-center px-3.5 justify-between">
        <div className="flex items-center space-x-2.5 overflow-hidden">
          <span className="text-lg shrink-0">🐒</span>
          {!isSidebarCollapsed && (
            <span className="font-bold text-xs tracking-wider text-slate-100 uppercase truncate">
              Monkey<span className="text-amber-500">Bots</span>
            </span>
          )}
        </div>
        <button
          onClick={toggleSidebar}
          className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 rounded transition shrink-0"
          title={isSidebarCollapsed ? "Expand Sidebar (Ctrl+B)" : "Collapse Sidebar"}
        >
          {isSidebarCollapsed ? (
            <ChevronRight className="w-3.5 h-3.5" />
          ) : (
            <ChevronLeft className="w-3.5 h-3.5" />
          )}
        </button>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 py-2 px-1.5 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const isActive = activeWorkspace === item.id;
          const Icon = item.icon;

          return (
            <button
              key={item.id}
              onClick={() => handleSelect(item.id, item.label)}
              className={`w-full flex items-center rounded text-xs font-medium transition group relative ${
                isSidebarCollapsed ? "justify-center px-2 py-2.5" : "px-3 py-2 space-x-3"
              } ${
                isActive
                  ? "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent"
              }`}
              title={isSidebarCollapsed ? `${item.label} (Key: ${item.hotkey})` : undefined}
            >
              {/* Active Indicator Bar */}
              {isActive && (
                <div className="absolute left-0 top-1 bottom-1 w-0.5 bg-amber-500 rounded-r" />
              )}

              <Icon
                className={`w-4 h-4 shrink-0 transition ${
                  isActive ? "text-amber-400" : "text-slate-400 group-hover:text-slate-200"
                }`}
              />

              {!isSidebarCollapsed && (
                <div className="flex items-center justify-between w-full min-w-0">
                  <span className="truncate">{item.label}</span>
                  <span className="text-[10px] text-slate-400 font-mono group-hover:text-slate-400">
                    {item.hotkey}
                  </span>
                </div>
              )}
            </button>
          );
        })}
      </nav>

      {/* Bottom Engineering Metadata */}
      <div className="p-2 border-t border-slate-800 text-[10px] text-slate-400">
        {!isSidebarCollapsed ? (
          <div className="space-y-1 px-1">
            <div className="flex items-center justify-between">
              <span>Platform</span>
              <span className="font-mono text-emerald-400">Local Native</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Simulation</span>
              <span className="font-mono text-amber-400">MuJoCo Core</span>
            </div>
          </div>
        ) : (
          <div className="text-center font-mono text-[9px] text-slate-400">v0.1</div>
        )}
      </div>
    </aside>
  );
};
