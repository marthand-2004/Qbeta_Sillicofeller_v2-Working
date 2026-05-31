"""
coupler_generator.py
====================
Builds transmon-to-transmon coupling buses in Qiskit Metal.

Each coupling bus is a RouteMeander CPW segment connecting two qubit
connection pads. Bus length is set to satisfy the target coupling strength
(currently a realistic default range; full J-planner TBD).

Coupling types supported:
  - 'meander'  : RouteMeander (default, capacitive)
  - 'straight' : RouteStraight (nearest-neighbour, short distance)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from topology_router import CouplingEdge


# ---------------------------------------------------------------------------
# Default coupling parameters
# ---------------------------------------------------------------------------

# Typical transmon-transmon coupling capacitance → physical bus length
# J ~ 10–20 MHz at bus length ~2–4 mm on Si substrate
DEFAULT_BUS_LENGTH_MM = 2.5
BUS_LENGTH_VARIATION  = 0.15   # vary per pair to prevent length degeneracy

COUPLING_CPW = {
    "trace_width": "10 um",
    "trace_gap":   "6 um",
    "fillet":      "49.9 um",
    "lead_start":  "0.1 mm",
    "lead_end":    "0.1 mm",
}


# ---------------------------------------------------------------------------
# Data container
# ---------------------------------------------------------------------------

@dataclass
class CouplerBuildResult:
    name:      str
    component: object      # Qiskit Metal component
    qubit_a:   str
    qubit_b:   str
    length_mm: float
    kind:      str         # 'meander' or 'straight'


# ---------------------------------------------------------------------------
# Asymmetry helper
# ---------------------------------------------------------------------------

def _bus_asymmetry(index: int) -> tuple:
    """Return (asym_str, flip_bool) that alternates to avoid overlap."""
    patterns = [
        ("+100um", False),
        ("-100um", True),
        ("+120um", False),
        ("-120um", True),
    ]
    return patterns[index % len(patterns)]


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_couplers(
    design,
    edges: List[CouplingEdge],
    qubit_positions: dict,        # {qubit_name: (x_mm, y_mm)}
    cpw_params: dict | None = None,
    base_length_mm: float = DEFAULT_BUS_LENGTH_MM,
) -> List[CouplerBuildResult]:
    """
    Build all qubit-qubit coupling buses.

    Parameters
    ----------
    design          : qiskit_metal DesignPlanar
    edges           : coupling edges from topology_router.place_qubits()
    qubit_positions : {qubit_name: (x_mm, y_mm)}
    cpw_params      : override CPW dimensions
    base_length_mm  : base bus physical length

    Returns
    -------
    List of CouplerBuildResult
    """
    from qiskit_metal import Dict
    from qiskit_metal.qlibrary.tlines.meandered import RouteMeander
    from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight

    cpw = cpw_params or COUPLING_CPW
    results: List[CouplerBuildResult] = []
    used_pins: set = set()

    for idx, edge in enumerate(edges):
        pin_key_a = (edge.qubit_a, edge.pin_a)
        pin_key_b = (edge.qubit_b, edge.pin_b)

        # Skip if either pin already routed (prevents double-use)
        if pin_key_a in used_pins or pin_key_b in used_pins:
            continue

        bus_name   = edge.label or f"bus_{idx}"
        length_mm  = round(base_length_mm + idx * BUS_LENGTH_VARIATION, 4)
        asym, flip = _bus_asymmetry(idx)

        # Choose meander vs straight based on distance
        pos_a = qubit_positions.get(edge.qubit_a, (0.0, 0.0))
        pos_b = qubit_positions.get(edge.qubit_b, (0.0, 0.0))
        dist  = ((pos_a[0]-pos_b[0])**2 + (pos_a[1]-pos_b[1])**2) ** 0.5
        kind  = "straight" if dist < 0.6 else "meander"

        opts = Dict(
            fillet      = cpw["fillet"],
            trace_gap   = cpw["trace_gap"],
            trace_width = cpw["trace_width"],
            lead = Dict(
                start_straight = cpw["lead_start"],
                end_straight   = cpw["lead_end"],
            ),
            pin_inputs = Dict(
                start_pin = Dict(component=edge.qubit_a, pin=edge.pin_a),
                end_pin   = Dict(component=edge.qubit_b, pin=edge.pin_b),
            ),
            total_length = f"{length_mm} mm",
        )

        if kind == "meander":
            opts["meander"] = Dict(
                asymmetry               = asym,
                lead_direction_inverted = "true" if flip else "false",
            )

        try:
            if kind == "meander":
                comp = RouteMeander(design, bus_name, options=opts)
            else:
                comp = RouteStraight(design, bus_name, options=opts)

            used_pins.add(pin_key_a)
            used_pins.add(pin_key_b)

            results.append(CouplerBuildResult(
                name      = bus_name,
                component = comp,
                qubit_a   = edge.qubit_a,
                qubit_b   = edge.qubit_b,
                length_mm = length_mm,
                kind      = kind,
            ))
        except Exception as exc:
            import warnings
            warnings.warn(f"[coupler_generator] Could not route {bus_name}: {exc}")

    return results
