"""
netlist_generator.py  —  QBETA V2 Phase 6
==========================================
Single source of truth for chip connectivity (netlist).

WHY THIS EXISTS
---------------
Real CAD systems build connectivity first, geometry second.
QBETA previously called _connect_meander() directly throughout the code,
meaning geometry and connectivity were entangled.

This module defines the netlist BEFORE any Qiskit Metal objects are created.
All other generators (feedline, resonator, coupler) consume the netlist
instead of hardcoding connections themselves.

NETLIST STRUCTURE
-----------------
A netlist is a set of named nets. Each net connects two or more pins.
A pin is (component_name, pin_name).

Example for a 4-qubit chip:
{
  "feedline": {
    "pins": [("feedline_LP_L", "tie"), ("feedline_LP_R", "tie")],
    "type": "feedline"
  },
  "ro_Q1": {
    "pins": [("Q1", "readout"), ("FL_coup_Q1", "short")],
    "type": "resonator",
    "freq_GHz": 6.4,
    "length_mm": 4.639
  },
  "bus_Q1_Q2": {
    "pins": [("Q1", "a"), ("Q2", "c")],
    "type": "coupler"
  }
}

USAGE
-----
    netlist = build_netlist(freq_plan, placement)
    for name, net in netlist.nets.items():
        print(f"  {name}: {net.pins}")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Data containers
# ─────────────────────────────────────────────────────────────────────────────

Pin = Tuple[str, str]   # (component_name, pin_name)


@dataclass
class Net:
    """A single electrical net connecting two or more pins."""
    name:       str
    pins:       List[Pin]
    net_type:   str                    # 'feedline' | 'resonator' | 'coupler' | 'bias'
    freq_GHz:   Optional[float] = None # for resonators
    length_mm:  Optional[float] = None # for resonators
    detuning_GHz: Optional[float] = None


@dataclass
class Netlist:
    """Complete chip netlist — single source of truth for connectivity."""
    nets:    Dict[str, Net] = field(default_factory=dict)
    n_qubits: int = 0

    def add(self, net: Net) -> None:
        self.nets[net.name] = net

    def by_type(self, net_type: str) -> List[Net]:
        return [n for n in self.nets.values() if n.net_type == net_type]

    def pins_for(self, component: str) -> List[Tuple[str, str]]:
        """Return all (net_name, pin_name) connected to a given component."""
        result = []
        for net_name, net in self.nets.items():
            for comp, pin in net.pins:
                if comp == component:
                    result.append((net_name, pin))
        return result

    def to_dict(self) -> dict:
        return {
            "n_qubits": self.n_qubits,
            "nets": {
                name: {
                    "type":     net.net_type,
                    "pins":     [(c, p) for c, p in net.pins],
                    "freq_GHz":  net.freq_GHz,
                    "length_mm": net.length_mm,
                    "detuning_GHz": net.detuning_GHz,
                }
                for name, net in self.nets.items()
            },
            "summary": {
                "feedlines":  len(self.by_type("feedline")),
                "resonators": len(self.by_type("resonator")),
                "couplers":   len(self.by_type("coupler")),
                "bias_lines": len(self.by_type("bias")),
            },
        }


# ─────────────────────────────────────────────────────────────────────────────
# Netlist builder
# ─────────────────────────────────────────────────────────────────────────────

def build_netlist(
    freq_plan,      # FrequencyPlan from frequency_planner
    placement,      # PlacementResult from topology_router
    feedline_name: str = "feedline",
) -> Netlist:
    """
    Build the complete chip netlist from a FrequencyPlan + PlacementResult.

    This is called BEFORE any Qiskit Metal objects are created.
    The netlist is then consumed by feedline_generator, resonator_generator,
    and coupler_generator.

    Parameters
    ----------
    freq_plan     : FrequencyPlan (from frequency_planner.py)
    placement     : PlacementResult (from topology_router.py)
    feedline_name : base name for feedline nets

    Returns
    -------
    Netlist
    """
    nl = Netlist(n_qubits=len(placement.qubits))

    # ── 1. Feedline net ───────────────────────────────────────────────────────
    lp_left  = f"{feedline_name}_LP_L"
    lp_right = f"{feedline_name}_LP_R"
    nl.add(Net(
        name     = feedline_name,
        pins     = [(lp_left, "tie"), (lp_right, "tie")],
        net_type = "feedline",
    ))

    # ── 2. Resonator nets (one per qubit) ─────────────────────────────────────
    for res in freq_plan.resonators:
        coup_stub = f"FL_coup_{res.qubit}"
        nl.add(Net(
            name        = f"ro_{res.qubit}",
            pins        = [(res.qubit, "readout"), (coup_stub, "short")],
            net_type    = "resonator",
            freq_GHz    = res.freq_GHz,
            length_mm   = res.length_mm,
            detuning_GHz = res.detuning_GHz,
        ))

    # ── 3. Coupler nets (from placement edges) ────────────────────────────────
    for edge in placement.edges:
        nl.add(Net(
            name     = edge.label or f"bus_{edge.qubit_a}_{edge.qubit_b}",
            pins     = [(edge.qubit_a, edge.pin_a), (edge.qubit_b, edge.pin_b)],
            net_type = "coupler",
        ))

    # ── 4. Bias launchpad nets (corner pads, one per qubit if available) ──────
    for q in placement.qubits:
        nl.add(Net(
            name     = f"bias_{q.name}",
            pins     = [(f"BIAS_{q.name}", "tie")],
            net_type = "bias",
        ))

    return nl


# ─────────────────────────────────────────────────────────────────────────────
# Netlist → Qiskit Metal routing instructions
# ─────────────────────────────────────────────────────────────────────────────

def netlist_to_routes(netlist: Netlist) -> List[dict]:
    """
    Convert netlist to a flat list of routing instructions.
    Each instruction is:
      {
        "name":    "ro_Q1",
        "type":    "resonator",
        "start":   ("Q1", "readout"),
        "end":     ("FL_coup_Q1", "short"),
        "length_mm": 4.639,
        "freq_GHz":  6.4
      }

    These are consumed by the Metal builder to create RouteMeander/RouteStraight.
    """
    routes = []
    for name, net in netlist.nets.items():
        if net.net_type in ("resonator", "coupler") and len(net.pins) >= 2:
            routes.append({
                "name":       name,
                "type":       net.net_type,
                "start":      net.pins[0],
                "end":        net.pins[1],
                "length_mm":  net.length_mm,
                "freq_GHz":   net.freq_GHz,
                "detuning_GHz": net.detuning_GHz,
            })
    return routes


# ─────────────────────────────────────────────────────────────────────────────
# Standalone demo
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    from frequency_planner import plan_chip
    from topology_router   import place_qubits

    freq_plan = plan_chip(4)
    placement = place_qubits(4, "grid")
    netlist   = build_netlist(freq_plan, placement)

    data = netlist.to_dict()
    print(f"Netlist for 4-qubit grid chip:")
    print(f"  Feedlines:  {data['summary']['feedlines']}")
    print(f"  Resonators: {data['summary']['resonators']}")
    print(f"  Couplers:   {data['summary']['couplers']}")
    print()
    for name, net in data["nets"].items():
        pins_str = " → ".join(f"{c}.{p}" for c, p in net["pins"])
        freq_str = f"  f={net['freq_GHz']} GHz  L={net['length_mm']} mm" if net["freq_GHz"] else ""
        print(f"  [{net['type']:10s}] {name:<22} {pins_str}{freq_str}")
