"""
gds_export.py
=============
GDS export pipeline for QBETA via Qiskit Metal's GDS renderer.

Workflow:
  design → QGeometryTables → GDSRenderer → .gds file → base64 for API

Layers used (standard IBM-style):
  1  : Nb base metal (ground plane, CPW centres)
  2  : Josephson junction markers
  10 : Qubit pockets (etch)
  11 : Coupling buses
  12 : Readout resonators
  30 : Launchpads / bond pads

References:
  - Qiskit Metal GDS renderer docs
  - gdspy / klayout for verification
"""

from __future__ import annotations

import base64
import io
import os
import tempfile
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Default GDS layer map
# ---------------------------------------------------------------------------

GDS_LAYER_MAP = {
    "TransmonPocket":    10,
    "RouteMeander":      11,
    "RouteStraight":     11,
    "LaunchpadWirebond": 30,
    "OpenToGround":      12,
}

DEFAULT_GDS_OPTIONS = {
    "short_segment_to_not_fillet": "True",
    "check_short_segments_by_scaling_fillet": "True",
    "fabrication_line_width": "10um",
}


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------

def export_gds(
    design,
    output_path: str | Path | None = None,
    options: dict | None = None,
) -> Path:
    """
    Render design to GDS file via Qiskit Metal's GDS renderer.

    Parameters
    ----------
    design      : qiskit_metal DesignPlanar (already rebuilt)
    output_path : destination .gds path; if None, a temp file is used
    options     : override GDS renderer options

    Returns
    -------
    Path to the written .gds file
    """
    from qiskit_metal.renderers.renderer_gds.gds_renderer import QGDSRenderer

    if output_path is None:
        tmp_dir = tempfile.mkdtemp()
        output_path = Path(tmp_dir) / "chip.gds"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    renderer = QGDSRenderer(design)
    renderer.options.update(options or DEFAULT_GDS_OPTIONS)

    # Render all components
    renderer.render_design()
    renderer.save_to_file(str(output_path))
    renderer.close()

    return output_path


def gds_to_base64(gds_path: Path) -> str:
    """Read GDS binary and return base64 string for API embedding."""
    with open(gds_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def export_gds_base64(
    design,
    options: dict | None = None,
) -> str:
    """
    One-shot: export GDS and return as base64 string.
    Cleans up temp file afterward.
    """
    path = export_gds(design, options=options)
    b64  = gds_to_base64(path)
    try:
        path.unlink()
    except Exception:
        pass
    return b64


# ---------------------------------------------------------------------------
# QGeometry summary
# ---------------------------------------------------------------------------

def get_qgeometry_summary(design) -> dict:
    """
    Return a dict summarising the QGeometry tables:
      - component count by type
      - total polygon count
      - bounding box estimate
    """
    try:
        tables = design.qgeometry.tables
        summary = {}
        for kind, df in tables.items():
            summary[kind] = {
                "rows": len(df),
                "components": list(df["component"].unique()) if "component" in df.columns else [],
            }
        return summary
    except Exception as exc:
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Renderer check
# ---------------------------------------------------------------------------

def gds_renderer_available() -> bool:
    """True if the Qiskit Metal GDS renderer can be imported."""
    try:
        from qiskit_metal.renderers.renderer_gds.gds_renderer import QGDSRenderer  # noqa
        return True
    except ImportError:
        return False
