import React from "react";
import { Viewport3D } from "../Viewport3D";
import { ContextualInspector } from "../inspector/ContextualInspector";
import { BottomEngineeringDock } from "../dock/BottomEngineeringDock";
import { ResizeHandle } from "../common/ResizeHandle";
import { useAppStore } from "../../store/useAppStore";

export const SimulationWorkspace: React.FC = () => {
  const {
    inspectorWidth,
    setInspectorWidth,
    bottomDockHeight,
    setBottomDockHeight,
  } = useAppStore();

  return (
    <div className="flex-1 flex flex-col overflow-hidden relative">
      <div className="flex-1 flex overflow-hidden">
        {/* Central 3D Viewport */}
        <div className="flex-1 relative min-w-0">
          <Viewport3D />
        </div>

        {/* Vertical Resize Handle */}
        <ResizeHandle
          direction="horizontal"
          onResize={(delta) => setInspectorWidth(inspectorWidth - delta)}
        />

        {/* Right Properties & Actuators Inspector */}
        <div style={{ width: `${inspectorWidth}px` }} className="shrink-0 h-full">
          <ContextualInspector />
        </div>
      </div>

      {/* Horizontal Resize Handle */}
      <ResizeHandle
        direction="vertical"
        onResize={(delta) => setBottomDockHeight(bottomDockHeight - delta)}
      />

      {/* Bottom Engineering Dock */}
      <BottomEngineeringDock />
    </div>
  );
};
