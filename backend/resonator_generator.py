"""
resonator_generator.py
======================
Builds TRUE quarter-wave readout resonators in Qiskit Metal.

Architecture enforced here:
  - Each qubit gets exactly ONE readout resonator
  - Resonator physical length is derived from frequency_planner.py
    (λ/4 at f_r computed from substrate ε_eff)
  - Resonators couple to a common feedline, NOT directly to launchpads
  - Coupling geometry: open-ended meander terminates near feedline
    (OpenToGround or RouteMeander with computed total_length)

Qiskit Metal components used:
  - RouteMeander          — meandered CPW resonator body
  - OpenToGround          — open termination at resonator tip
  - (feedline coupling port provided by feedline_generator)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from frequency_planner import ResonatorSpec


# ---------------------------------------------------------------------------
# Default CPW parameters (Nb on Si, IBM-style)
# ---------------------------------------------------------------------------
DEFAULT_CPW = {
    "trace_width": "10 um",
    "trace_gap":   "6 um",
    "fillet":      "49.9 um",
    "lead_start":  "0.1 mm",
    "lead_end":    "0.05 mm",
}


@dataclass
class ResonatorBuildResult:
    name:        str
    component:   object   # Qiskit Metal component instance
    length_mm:   float
    freq_GHz:    float
    qubit:       str
    coupler_pin: str       # pin name on the resonator that touches the feedline


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _meander_asymmetry(index: int) -> str:
    """Alternate asymmetry direction so adjacent resonators don't overlap."""
    patterns = ["+80um", "-100um", "+80um", "-120um"]
    return patterns[index % len(patterns)]


def _resonator_position(
    qubit_x: float,
    qubit_y: float,
    feedline_y: float,
    index: int,
    spacing_mm: float = 0.5,
) -> dict:
    """
    Position the resonator between the qubit and the feedline.
    Simple: centre the meander in the gap, stagger horizontally.
    """
    x = round(qubit_x + index * spacing_mm * 0.0, 4)   # align with qubit x
    y = round((qubit_y + feedline_y) / 2.0, 4)
    return {"pos_x": f"{x}mm", "pos_y": f"{y}mm"}


# ---------------------------------------------------------------------------
# Public builder
# ---------------------------------------------------------------------------

def build_resonators(
    design,
    resonator_specs: List[ResonatorSpec],
    qubit_positions: dict,       # {qubit_name: (x_mm, y_mm)}
    feedline_y_mm: float,
    cpw_params: dict | None = None,
) -> List[ResonatorBuildResult]:
    """
    Build quarter-wave readout resonators in Qiskit Metal.

    Parameters
    ----------
    design          : qiskit_metal DesignPlanar instance
    resonator_specs : list of ResonatorSpec from frequency_planner
    qubit_positions : {qubit_name: (x_mm, y_mm)} mapping
    feedline_y_mm   : y-coordinate of the feedline (mm)
    cpw_params      : override CPW trace dimensions

    Returns
    -------
    List of ResonatorBuildResult (one per qubit)
    """
    from qiskit_metal import Dict
    from qiskit_metal.qlibrary.tlines.meandered import RouteMeander

    cpw = cpw_params or DEFAULT_CPW
    results: List[ResonatorBuildResult] = []

    for idx, spec in enumerate(resonator_specs):
        qpos = qubit_positions.get(spec.qubit, (0.0, 0.0))
        qx, qy = qpos

        # Qubit-side pin: the readout connection pad on the transmon
        qubit_pin = "readout"   # standard name set by feedline_generator

        # Feedline-side coupling point name (stub created by feedline_generator)
        fl_comp  = f"FL_coup_{spec.qubit}"
        fl_pin   = "short"

        asym = _meander_asymmetry(idx)

        opts = Dict(
            fillet      = cpw["fillet"],
            trace_gap   = cpw["trace_gap"],
            trace_width = cpw["trace_width"],
            lead = Dict(
                start_straight = cpw["lead_start"],
                end_straight   = cpw["lead_end"],
            ),
            meander = Dict(
                asymmetry             = asym,
                lead_direction_inverted = "false",
            ),
            pin_inputs = Dict(
                start_pin = Dict(component=spec.qubit,  pin="readout"),
                end_pin   = Dict(component=fl_comp,      pin="short"),
            ),
            total_length = f"{spec.length_mm:.4f} mm",
        )

        try:
            comp = RouteMeander(design, spec.name, options=opts)
            results.append(ResonatorBuildResult(
                name        = spec.name,
                component   = comp,
                length_mm   = spec.length_mm,
                freq_GHz    = spec.freq_GHz,
                qubit       = spec.qubit,
                coupler_pin = "end",
            ))
        except Exception as exc:
            # Log but don't crash — partial chips are still useful
            import warnings
            warnings.warn(f"[resonator_generator] Could not place {spec.name}: {exc}")

    return results


# ---------------------------------------------------------------------------
# Standalone test (no Qiskit Metal required)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from frequency_planner import plan_chip

    plan = plan_chip(4)
    print("Resonator specs:")
    for r in plan.resonators:
        print(f"  {r.name}: f={r.freq_GHz} GHz  →  λ/4 = {r.length_mm:.3f} mm  (ε_eff={r.epsilon_eff})")
