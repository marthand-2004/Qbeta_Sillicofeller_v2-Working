"""
feedline_generator.py
=====================
Builds the feedline architecture for a superconducting quantum chip.

Real architecture implemented here:

    LaunchpadWirebond (left)
         │
    ===================================  ← CPW feedline (RouteStraight)
         │         │         │
      Coupler   Coupler   Coupler        ← capacitive coupling stubs
         │         │         │
       RO_Q1    RO_Q2    RO_Q3          ← quarter-wave resonators
         │         │         │
        Q1        Q2        Q3           ← TransmonPocket qubits
    ===================================
         │
    LaunchpadWirebond (right)

Qiskit Metal components used:
  - LaunchpadWirebond   — chip I/O pads
  - RouteStraight       — main feedline
  - RouteMeander        — coupling stubs to resonators

This module intentionally has NO routing of qubits → launchpads directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class FeedlineConfig:
    """Configuration for a single feedline segment."""
    name:         str
    x_start_mm:   float
    x_end_mm:     float
    y_mm:         float             # feedline y-position
    orientation:  int = 0          # 0 = horizontal
    lp_left_name: str = "LP_L"
    lp_right_name: str = "LP_R"


@dataclass
class FeedlineBuildResult:
    feedline_component:   object        # RouteStraight instance
    launchpad_left:       object        # LaunchpadWirebond
    launchpad_right:      object        # LaunchpadWirebond
    coupling_stubs:       list          # list of RouteStraight stubs
    config:               FeedlineConfig


# ---------------------------------------------------------------------------
# Default dimensions
# ---------------------------------------------------------------------------

FEEDLINE_CPW = {
    "trace_width": "10 um",
    "trace_gap":   "6 um",
}

LAUNCHPAD_OPTS = {
    "lead_length":   "25 um",
    "pad_gap":       "125 um",
    "pad_width":     "260 um",
    "pad_height":    "100 um",
    "taper_height":  "122 um",
}

COUPLING_STUB_LENGTH_UM = 100.0    # capacitive coupling stub (sets κ_ext)


# ---------------------------------------------------------------------------
# Feedline position calculator
# ---------------------------------------------------------------------------

def feedline_y_position(
    qubit_positions: dict,    # {name: (x_mm, y_mm)}
    margin_mm: float = 1.5,
) -> float:
    """
    Place feedline above all qubits with a fixed margin.
    Returns y-coordinate in mm.
    """
    if not qubit_positions:
        return margin_mm
    max_y = max(pos[1] for pos in qubit_positions.values())
    return round(max_y + margin_mm, 4)


def feedline_x_extents(
    qubit_positions: dict,
    margin_mm: float = 1.0,
) -> Tuple[float, float]:
    """
    Return (x_start, x_end) spanning all qubits + margin.
    """
    if not qubit_positions:
        return (-2.0, 2.0)
    xs = [pos[0] for pos in qubit_positions.values()]
    return (round(min(xs) - margin_mm, 4), round(max(xs) + margin_mm, 4))


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_feedline(
    design,
    qubit_positions: dict,       # {qubit_name: (x_mm, y_mm)}
    qubit_names: List[str],
    feedline_name: str = "feedline",
    margin_y_mm: float = 1.5,
    margin_x_mm: float = 1.0,
) -> FeedlineBuildResult:
    """
    Build the complete feedline structure:
      1. LaunchpadWirebond on each end
      2. RouteStraight feedline connecting the launchpads
      3. Coupling stub (short RouteStraight) at each qubit's x-position

    Parameters
    ----------
    design          : qiskit_metal DesignPlanar
    qubit_positions : {qubit_name: (x_mm, y_mm)}
    qubit_names     : ordered list of qubit names
    feedline_name   : base name for feedline components

    Returns
    -------
    FeedlineBuildResult
    """
    from qiskit_metal import Dict
    from qiskit_metal.qlibrary.terminations.launchpad_wb import LaunchpadWirebond
    from qiskit_metal.qlibrary.tlines.straight_path import RouteStraight

    fl_y   = feedline_y_position(qubit_positions, margin_y_mm)
    x0, x1 = feedline_x_extents(qubit_positions, margin_x_mm)

    lp_opts_base = dict(
        lead_length  = LAUNCHPAD_OPTS["lead_length"],
        pad_gap      = LAUNCHPAD_OPTS["pad_gap"],
        pad_width    = LAUNCHPAD_OPTS["pad_width"],
        pad_height   = LAUNCHPAD_OPTS["pad_height"],
        taper_height = LAUNCHPAD_OPTS["taper_height"],
    )

    # --- Left launchpad (signal IN) ---
    lp_left_name = f"{feedline_name}_LP_L"
    lp_left = LaunchpadWirebond(
        design, lp_left_name,
        options=dict(
            pos_x=f"{x0}mm", pos_y=f"{fl_y}mm",
            orientation="180",          # faces left
            **lp_opts_base,
        ),
    )

    # --- Right launchpad (signal OUT / through) ---
    lp_right_name = f"{feedline_name}_LP_R"
    lp_right = LaunchpadWirebond(
        design, lp_right_name,
        options=dict(
            pos_x=f"{x1}mm", pos_y=f"{fl_y}mm",
            orientation="0",            # faces right
            **lp_opts_base,
        ),
    )

    # --- Main CPW feedline ---
    fl_opts = Dict(
        trace_width = FEEDLINE_CPW["trace_width"],
        trace_gap   = FEEDLINE_CPW["trace_gap"],
        pin_inputs  = Dict(
            start_pin = Dict(component=lp_left_name,  pin="tie"),
            end_pin   = Dict(component=lp_right_name, pin="tie"),
        ),
    )
    feedline_comp = RouteStraight(design, feedline_name, options=fl_opts)

    # --- Coupling stubs (one per qubit) ---
    # Each stub is a short RouteStraight from feedline body down toward qubit.
    # The resonator_generator will connect to the far end of each stub.
    coupling_stubs = []
    stub_len_mm = COUPLING_STUB_LENGTH_UM / 1000.0

    for qname in qubit_names:
        qx, qy = qubit_positions.get(qname, (0.0, 0.0))
        stub_name = f"FL_coup_{qname}"

        # Place a tiny OpenToGround as coupling anchor point on the feedline
        # In Qiskit Metal, RouteStraight doesn't expose intermediate pins,
        # so we use a small RouteStraight stub hanging down from the feedline y.
        try:
            from qiskit_metal.qlibrary.terminations.open_to_ground import OpenToGround
            stub_opts = Dict(
                pos_x       = f"{qx}mm",
                pos_y       = f"{fl_y - stub_len_mm}mm",
                orientation = "270",          # points downward toward qubit
                termination_gap = "6 um",
                trace_width = FEEDLINE_CPW["trace_width"],
                trace_gap   = FEEDLINE_CPW["trace_gap"],
            )
            stub = OpenToGround(design, stub_name, options=stub_opts)
            coupling_stubs.append(stub)
        except Exception:
            # Fall back: no stub if OpenToGround unavailable
            coupling_stubs.append(None)

    config = FeedlineConfig(
        name          = feedline_name,
        x_start_mm    = x0,
        x_end_mm      = x1,
        y_mm          = fl_y,
        lp_left_name  = lp_left_name,
        lp_right_name = lp_right_name,
    )

    return FeedlineBuildResult(
        feedline_component = feedline_comp,
        launchpad_left     = lp_left,
        launchpad_right    = lp_right,
        coupling_stubs     = coupling_stubs,
        config             = config,
    )


# ---------------------------------------------------------------------------
# Convenience: add corner launchpads for DC/flux bias lines
# ---------------------------------------------------------------------------

def add_corner_launchpads(
    design,
    chip_half_width_mm: float,
    chip_half_height_mm: float,
    prefix: str = "BIAS",
) -> List[object]:
    """
    Add four corner launchpads (typically used for flux bias lines, not readout).
    These are NOT connected to the readout feedline.
    """
    from qiskit_metal.qlibrary.terminations.launchpad_wb import LaunchpadWirebond

    corners = [
        (f"{prefix}_TL", -chip_half_width_mm,  chip_half_height_mm, "135"),
        (f"{prefix}_TR",  chip_half_width_mm,  chip_half_height_mm,  "45"),
        (f"{prefix}_BL", -chip_half_width_mm, -chip_half_height_mm, "225"),
        (f"{prefix}_BR",  chip_half_width_mm, -chip_half_height_mm, "315"),
    ]
    pads = []
    for name, x, y, orient in corners:
        pad = LaunchpadWirebond(
            design, name,
            options=dict(
                pos_x=f"{x}mm", pos_y=f"{y}mm",
                orientation=orient,
                lead_length="25 um",
            ),
        )
        pads.append(pad)
    return pads
