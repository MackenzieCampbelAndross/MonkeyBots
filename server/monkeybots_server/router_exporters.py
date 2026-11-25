"""
Model Exporter REST API
Provides endpoints to export RobotModel instances to URDF or MJCF.
"""

from fastapi import APIRouter, HTTPException, Query, Response
from core.monkeybots.models.registry import get_robot_model
from core.monkeybots.models.exporters import export_to_urdf, export_to_mjcf

router = APIRouter(prefix="/api/v1/models/export", tags=["models"])


@router.get("/{format}")
async def export_model(format: str, robot_id: str = Query("default_6dof_arm")):
    """Exports the specified robot to 'urdf' or 'mjcf' format."""
    try:
        model = get_robot_model(robot_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Robot model '{robot_id}' not found.")

    fmt = format.lower()
    if fmt == "urdf":
        xml_content = export_to_urdf(model)
        filename = f"{robot_id}.urdf"
    elif fmt == "mjcf":
        xml_content = export_to_mjcf(model)
        filename = f"{robot_id}.xml"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format '{format}'. Use 'urdf' or 'mjcf'.")

    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
