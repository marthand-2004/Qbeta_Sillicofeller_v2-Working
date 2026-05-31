"""
metal_fabricated.py  —  QBETA V2
=================================
Orchestrates the full chip build pipeline and delegates ALL Qiskit Metal
geometry to metal_connector.py.

Pipeline order:
  1. FrequencyPlanner  → freq_plan  (physics)
  2. TopologyRouter    → placement  (graph-solver coordinates)
  3. NetlistGenerator  → netlist    (connectivity source of truth)
  4. DRC               → drc_report (validate before geometry)
  5. metal_connector   → design + build_log  (Qiskit Metal geometry)
  6. renderer          → base64 PNG

Returns 5-tuple: (design, freq_plan, placement, netlist, drc_report)
"""

from __future__ import annotations

import os

os.environ.setdefault("QISKIT_METAL_HEADLESS", "1")
os.environ.setdefault("QISKIT_METAL_SUPPRESS_RENAME_WARNING", "1")


# ---------------------------------------------------------------------------
# Availability check
# ---------------------------------------------------------------------------

def _metal_available() -> bool:
    try:
        import qiskit_metal  # noqa: F401
        return True
    except ImportError:
        return False


# ---------------------------------------------------------------------------
# Main chip builder
# ---------------------------------------------------------------------------

def build_v2_chip(
    n: int = 4,
    topology: str = "grid",
    scale: float = 1.0,
    substrate: dict | None = None,
) -> tuple:
    """
    Full V2 pipeline. Returns (design, freq_plan, placement, netlist, drc_report).
    The design object is a Qiskit Metal DesignPlanar with all components placed.
    """
    from frequency_planner  import FrequencyPlanner
    from topology_router    import place_qubits
    from netlist_generator  import build_netlist
    from drc                import run_drc
    from metal_connector    import build_metal_chip

    # ── 1. Frequency planning ─────────────────────────────────────────────
    freq_plan = FrequencyPlanner(n=n, substrate=substrate).plan()

    # ── 2. Graph-solver placement ─────────────────────────────────────────
    placement = place_qubits(n, topology=topology, scale=scale)

    # ── 3. Netlist (connectivity before geometry) ─────────────────────────
    netlist = build_netlist(freq_plan, placement)

    # ── 4. DRC ────────────────────────────────────────────────────────────
    drc_report = run_drc(placement, freq_plan)
    if drc_report.has_errors():
        import warnings as _w
        for v in drc_report.errors:
            _w.warn(f"[DRC] {v}")

    # ── 5. Qiskit Metal geometry (via metal_connector) ────────────────────
    design, build_log = build_metal_chip(n, topology, scale, freq_plan, placement)

    # Attach build_log to the design object for inspection
    design._qbeta_build_log = build_log

    return design, freq_plan, placement, netlist, drc_report


# ---------------------------------------------------------------------------
# Render helpers
# ---------------------------------------------------------------------------

def render_metal_fabricated(design, dpi: int = 180) -> str:
    """Render a Qiskit Metal design to base64 PNG (SEM style)."""
    from metal_connector import render_metal_design
    title = f"QBETA V2 — Superconducting Chip ({len(design.components)} components)"
    return render_metal_design(design, dpi=dpi, title=title)


# ---------------------------------------------------------------------------
# Schematic fallback (no Metal required)
# ---------------------------------------------------------------------------

def generate_schematic_image(n: int, topology: str, scale: float) -> str:
    """Return a schematic base64 PNG using the renderer without Metal."""
    from frequency_planner import FrequencyPlanner
    from topology_router   import place_qubits
    from renderer          import render_schematic

    freq_plan = FrequencyPlanner(n=n).plan()
    placement = place_qubits(n, topology=topology, scale=scale)
    return render_schematic(
        placement,
        freq_plan = freq_plan,
        title     = f"QBETA V2 — {n}Q {topology.capitalize()} Chip",
    )


# ---------------------------------------------------------------------------
# Legacy shims
# ---------------------------------------------------------------------------

def build_fabricated_design_n(n: int = 4, scale: float = 1.0):
    """Legacy shim: returns design only."""
    design, _, _, _, _ = build_v2_chip(n=n, scale=scale)
    return design


def build_fabricated_design(scale: float = 1.0):
    """Legacy shim for 4-qubit 2×2 grid."""
    return build_fabricated_design_n(n=4, scale=scale)


def generate_fabricated_metal(n: int = 4, scale: float = 1.0, topology: str = "grid") -> tuple:
    """Returns (design, freq_plan, placement, netlist, drc_report, image_base64)."""
    design, freq_plan, placement, netlist, drc_report = build_v2_chip(n, topology, scale)
    image = render_metal_fabricated(design)
    return design, freq_plan, placement, netlist, drc_report, image
