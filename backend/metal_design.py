"""
metal_design.py
===============
QBETA V2 — Natural language → superconducting chip design.

Pipeline:
  Prompt
    ↓ ml_intent.py (qubit count + topology)
    ↓ frequency_planner.py (f_q, f_r, λ/4 lengths)
    ↓ topology_router.py (physical placement)
    ↓ metal_fabricated.py / renderer.py (Qiskit Metal layout + image)
    ↓ gds_export.py (GDS if requested)
    ↓ JSON response to frontend
"""

from __future__ import annotations

import os
import re
import site
import sys
from typing import Any, Dict, List, Tuple

# Ensure user-installed packages are visible
_user_site = site.getusersitepackages()
if _user_site and _user_site not in sys.path:
    sys.path.insert(0, _user_site)

os.environ.setdefault("QISKIT_METAL_HEADLESS", "1")
os.environ.setdefault("QISKIT_METAL_SUPPRESS_RENAME_WARNING", "1")

MAX_QUBITS = 24


# ---------------------------------------------------------------------------
# ML intent resolution (unchanged from V1)
# ---------------------------------------------------------------------------

def _resolve_from_ml(prompt: str) -> Tuple[int, int, str, Dict[str, Any]]:
    """ML intent classifier + regex override."""
    from ml_intent import resolve_design_params
    return resolve_design_params(prompt, MAX_QUBITS)


def _detect_chip_scale(prompt: str) -> float:
    p = prompt.lower()
    if any(w in p for w in ("large", "big", "wide")):
        return 1.35
    if any(w in p for w in ("small", "compact", "dense")):
        return 0.75
    return 1.0


def _detect_label(prompt: str, n: int, topology: str, requested: int) -> str:
    p = prompt.lower()
    suffix = f" ({requested} requested, max {MAX_QUBITS})" if requested != n else ""
    if "fabricat" in p:
        return f"Fabricated {n}Q Superconducting Chip{suffix}"
    if "readout" in p or "resonator" in p:
        return f"Readout-Enhanced {n}Q Chip{suffix}"
    names = {"ring": "Ring Coupler", "line": "Linear Chain",
             "grid": "Grid Array",  "star": "Star Hub",
             "heavy_hex": "Heavy-Hex"}
    return f"{names.get(topology, 'Custom')} — {n}-Transmon Chip{suffix}"


def _interpret_prompt(
    prompt: str, n: int, requested: int, topology: str,
    scale: float, metal: bool, ml_info: Dict[str, Any] | None = None,
) -> str:
    engine = "Qiskit Metal V2 (λ/4 resonators + feedline)" if metal else "schematic"
    parts = [f"Designed {n}-qubit {topology} chip using {engine}", f"scale ×{scale:.2f}"]
    if ml_info:
        if ml_info.get("ml_skipped"):
            parts.append(ml_info.get("reason", "Rule-based parser"))
        elif ml_info.get("confidence") is not None:
            conf = int(ml_info["confidence"] * 100)
            parts.append(
                f"ML intent: {ml_info.get('qubits')} qubits ({conf}% confidence)"
            )
        else:
            parts.append(ml_info.get("reason", "Rule-based detection"))
    if requested != n:
        parts.append(f"you asked for {requested} qubits (capped at {MAX_QUBITS})")
    return "; ".join(parts) + "."


# ---------------------------------------------------------------------------
# Metal availability
# ---------------------------------------------------------------------------

def _metal_installed() -> bool:
    try:
        import qiskit_metal  # noqa
        return True
    except ImportError:
        return False


# ---------------------------------------------------------------------------
# V2 Metal build
# ---------------------------------------------------------------------------

def _try_v2_metal_build(
    n: int,
    scale: float,
    topology: str,
) -> Dict[str, Any]:
    """
    Full V2 pipeline build via Qiskit Metal.
    Returns all design artefacts as a dict.
    """
    from metal_fabricated import build_v2_chip, render_metal_fabricated
    from topology_router  import placement_to_dict
    from renderer         import render_schematic

    design, freq_plan, placement, netlist, drc_report = build_v2_chip(
        n=n, topology=topology, scale=scale
    )

    # Get per-step build log from metal_connector
    build_log = getattr(design, "_qbeta_build_log", None)
    build_log_dict = build_log.to_dict() if build_log else {}

    fabricated_image = render_metal_fabricated(design)
    schematic_image  = render_schematic(
        placement, freq_plan=freq_plan,
        title=f"QBETA V2 — {n}Q {topology.capitalize()} Chip",
    )

    components = list(design.components.keys())

    edge_pairs = [
        [
            next((i for i, q in enumerate(placement.qubits) if q.name == e.qubit_a), -1),
            next((i for i, q in enumerate(placement.qubits) if q.name == e.qubit_b), -1),
        ]
        for e in placement.edges
    ]

    gds_b64 = None
    try:
        from gds_export import export_gds_base64, gds_renderer_available
        if gds_renderer_available():
            gds_b64 = export_gds_base64(design)
    except Exception:
        pass

    return {
        "chip_image":        schematic_image,
        "fabricated_image":  fabricated_image,
        "gds_data":          gds_b64,
        "components":        components,
        "edges":             edge_pairs,
        "engine":            "qiskit-metal-v2",
        "solver":            placement_to_dict(placement).get("solver", "deterministic"),
        "build_log":         build_log_dict,
        "drc":               drc_report.to_dict(),
        "netlist_summary":   netlist.to_dict()["summary"],
        "frequency_plan": {
            "qubit_frequencies_GHz":    {q.name: q.freq_GHz    for q in freq_plan.qubits},
            "qubit_groups":             {q.name: q.group       for q in freq_plan.qubits},
            "EJ_GHz":                   {q.name: q.EJ_GHz      for q in freq_plan.qubits},
            "EC_GHz":                   {q.name: q.EC_GHz      for q in freq_plan.qubits},
            "resonator_frequencies_GHz":{r.name: r.freq_GHz    for r in freq_plan.resonators},
            "resonator_lengths_mm":     {r.name: r.length_mm   for r in freq_plan.resonators},
            "detunings_GHz":            {r.name: r.detuning_GHz for r in freq_plan.resonators},
            "epsilon_eff":              freq_plan.epsilon_eff,
            "warnings":                 [w.message for w in freq_plan.warnings],
        },
        "placement": placement_to_dict(placement),
    }


def _generate_v2_code(n: int, topology: str, scale: float) -> str:
    return f'''"""QBETA V2 — generated chip script"""
import os
os.environ["QISKIT_METAL_HEADLESS"] = "1"

from metal_fabricated import build_v2_chip, render_metal_fabricated

design, freq_plan, placement = build_v2_chip(n={n}, topology="{topology}", scale={scale})

print("Qubit frequencies (GHz):")
for q in freq_plan.qubits:
    print(f"  {{q.name}}: {{q.freq_GHz}} GHz")

print("\\nResonator λ/4 lengths (mm):")
for r in freq_plan.resonators:
    print(f"  {{r.name}}: {{r.length_mm:.3f}} mm  @ {{r.freq_GHz}} GHz")

image_b64 = render_metal_fabricated(design)
print("\\nFabricated image ready (base64 PNG).")
'''


# ---------------------------------------------------------------------------
# Schematic fallback
# ---------------------------------------------------------------------------

def _build_schematic_response(
    prompt: str,
    error_hint: str,
    n: int,
    requested: int,
    topology: str,
    scale: float,
    label: str,
    ml_info: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    from metal_fabricated  import generate_schematic_image
    from topology_router   import place_qubits, placement_to_dict
    from frequency_planner import FrequencyPlanner

    freq_plan = FrequencyPlanner(n=n).plan()
    placement = place_qubits(n, topology=topology, scale=scale)

    chip_image = generate_schematic_image(n, topology, scale)

    edge_pairs = [
        [
            next((i for i, q in enumerate(placement.qubits) if q.name == e.qubit_a), -1),
            next((i for i, q in enumerate(placement.qubits) if q.name == e.qubit_b), -1),
        ]
        for e in placement.edges
    ]

    hint = f" [{error_hint}]" if error_hint else ""

    return {
        "label":            label,
        "chip_image":       chip_image,
        "fabricated_image": chip_image,
        "gds_data":         None,
        "code":             _generate_v2_code(n, topology, scale),
        "num_qubits":       n,
        "requested_qubits": requested,
        "topology":         topology,
        "components":       [q.name for q in placement.qubits],
        "edges":            edge_pairs,
        "engine":           "schematic-v2",
        "interpretation":   _interpret_prompt(prompt, n, requested, topology, scale, False, ml_info) + hint,
        "ml_prediction":    ml_info,
        "circuit_image":    "",
        "depth":            0,
        "error_hint":       error_hint or None,
        "frequency_plan": {
            "qubit_frequencies_GHz":    {q.name: q.freq_GHz    for q in freq_plan.qubits},
            "qubit_groups":             {q.name: q.group       for q in freq_plan.qubits},
            "EJ_GHz":                   {q.name: q.EJ_GHz      for q in freq_plan.qubits},
            "EC_GHz":                   {q.name: q.EC_GHz      for q in freq_plan.qubits},
            "resonator_frequencies_GHz":{r.name: r.freq_GHz    for r in freq_plan.resonators},
            "resonator_lengths_mm":     {r.name: r.length_mm   for r in freq_plan.resonators},
            "detunings_GHz":            {r.name: r.detuning_GHz for r in freq_plan.resonators},
            "epsilon_eff":              freq_plan.epsilon_eff,
            "warnings":                 [w.message for w in freq_plan.warnings],
        },
        "placement": placement_to_dict(placement),
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_metal_chip(prompt: str) -> Dict[str, Any]:
    """Generate superconducting chip from natural language (V2 pipeline)."""
    n, requested, topology, ml_info = _resolve_from_ml(prompt)
    n     = max(1, n)
    scale = _detect_chip_scale(prompt)
    label = _detect_label(prompt, n, topology, requested)

    if _metal_installed():
        try:
            metal = _try_v2_metal_build(n, scale, topology)

            result = {
                "label":            label,
                "num_qubits":       n,
                "requested_qubits": requested,
                "topology":         topology,
                "interpretation":   _interpret_prompt(prompt, n, requested, topology, scale, True, ml_info),
                "ml_prediction":    ml_info,
                "circuit_image":    "",
                "depth":            0,
                "code":             _generate_v2_code(n, topology, scale),
                **metal,
            }

            # Optional circuit diagram
            try:
                from circuit_gen import generate_chip_design
                c = generate_chip_design(prompt)
                result["circuit_image"] = c.get("circuit_image", "")
                result["depth"]         = c.get("depth", 0)
            except Exception:
                pass

            return result

        except Exception as exc:
            return _build_schematic_response(
                prompt, str(exc), n, requested, topology, scale, label, ml_info
            )

    return _build_schematic_response(
        prompt, "pip install --user quantum-metal",
        n, requested, topology, scale, label, ml_info,
    )
