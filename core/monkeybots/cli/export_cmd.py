"""
CLI exporter subcommand
"""
import sys
from pathlib import Path
from core.monkeybots.models.registry import get_robot_model
from core.monkeybots.models.exporters import export_to_urdf, export_to_mjcf


def run_export(robot_id: str, format_type: str, output_path: str):
    try:
        model = get_robot_model(robot_id)
    except KeyError:
        print(f"Error: Unknown robot model '{robot_id}'.")
        sys.exit(1)

    fmt = format_type.lower()
    if fmt == "urdf":
        content = export_to_urdf(model)
    elif fmt == "mjcf":
        content = export_to_mjcf(model)
    else:
        print(f"Error: Unsupported format '{format_type}'.")
        sys.exit(1)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    print(f"Exported '{robot_id}' to {out.resolve()} ({fmt.upper()})")
