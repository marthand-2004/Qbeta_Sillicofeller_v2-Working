"""
app.py — QBETA V2 Flask backend
"""
import os
import site
import sys

_user_site = site.getusersitepackages()
if _user_site and _user_site not in sys.path:
    sys.path.insert(0, _user_site)

os.environ.setdefault("QISKIT_METAL_HEADLESS", "1")
os.environ.setdefault("QISKIT_METAL_SUPPRESS_RENAME_WARNING", "1")

from flask import Flask, jsonify, request
from flask_cors import CORS

from metal_design import MAX_QUBITS, _metal_installed, generate_metal_chip


def _ml_ready() -> bool:
    try:
        from ml_intent import get_model
        get_model()
        return True
    except Exception:
        return False


def _gds_ready() -> bool:
    try:
        from gds_export import gds_renderer_available
        return gds_renderer_available()
    except Exception:
        return False


app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:4173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:4173",
])


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    from metal_connector import metal_status as _ms
    ms = _ms()
    return jsonify({
        "status":       "ok",
        "version":      "v2",
        "qiskit_metal": "available" if ms["installed"] else "not_installed",
        "metal_version":ms["version"],
        "test_build":   ms["test_build"],
        "ml_intent":    "ready" if _ml_ready() else "unavailable",
        "gds_renderer": "available" if _gds_ready() else "not_installed",
        "max_qubits":   MAX_QUBITS,
        "pipeline": [
            "FrequencyPlanner",
            "TopologyRouter (Kamada-Kawai)",
            "NetlistGenerator",
            "DRC",
            "MetalConnector (Qiskit Metal)",
            "GDSExport",
        ],
        "components": ms["components"],
    })


@app.route("/metal-status", methods=["GET"])
def metal_status_endpoint():
    """Full Qiskit Metal installation and component status report."""
    from metal_connector import metal_status as _ms
    return jsonify(_ms())


# ---------------------------------------------------------------------------
# Main generation endpoint
# ---------------------------------------------------------------------------

@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json(silent=True)
        if not data or "prompt" not in data:
            return jsonify({"error": "Missing 'prompt' in request body"}), 400

        prompt = data["prompt"]
        if not isinstance(prompt, str) or not prompt.strip():
            return jsonify({"error": "Prompt must be a non-empty string"}), 400

        result = generate_metal_chip(prompt.strip())
        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Design generation failed: {str(e)}"}), 500


# ---------------------------------------------------------------------------
# Frequency plan endpoint (standalone, no Metal required)
# ---------------------------------------------------------------------------

@app.route("/frequency-plan", methods=["POST"])
def frequency_plan():
    """
    Phase 2: Return a full frequency plan (qubit A/B groups, EJ/EC,
    resonator band 6.3–7.2 GHz, λ/4 lengths, collision warnings).

    Body: {"n": 4, "topology": "grid", "substrate": {...optional...}}
    """
    try:
        data     = request.get_json(silent=True) or {}
        n        = max(1, min(MAX_QUBITS, int(data.get("n", 4))))
        topology = data.get("topology", "grid")
        substrate = data.get("substrate", None)

        from frequency_planner import generate_frequency_plan, FrequencyPlanner
        plan = generate_frequency_plan(n, topology=topology)

        # Also include substrate info
        substrate_info = FrequencyPlanner(n=n, substrate=substrate).substrate
        return jsonify({"n": n, "substrate": substrate_info, **plan})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# DRC endpoint — Phase 7
# ---------------------------------------------------------------------------

@app.route("/drc", methods=["POST"])
def drc():
    """
    Run Design Rule Check for a given chip spec.
    Body: {"n": 4, "topology": "grid", "scale": 1.0, "rules": {...optional overrides...}}
    Returns: DRCReport as JSON
    """
    try:
        data     = request.get_json(silent=True) or {}
        n        = max(1, min(MAX_QUBITS, int(data.get("n", 4))))
        topology = data.get("topology", "grid")
        scale    = float(data.get("scale", 1.0))
        rules    = data.get("rules", None)

        from frequency_planner import plan_chip
        from topology_router   import place_qubits
        from drc               import run_drc

        freq_plan = plan_chip(n)
        placement = place_qubits(n, topology=topology, scale=scale)
        report    = run_drc(placement, freq_plan, rules)

        return jsonify({"n": n, "topology": topology, **report.to_dict()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Netlist endpoint — Phase 6
# ---------------------------------------------------------------------------

@app.route("/netlist", methods=["POST"])
def netlist():
    """
    Build and return the chip netlist (connectivity source of truth).
    Body: {"n": 4, "topology": "grid"}
    """
    try:
        data     = request.get_json(silent=True) or {}
        n        = max(1, min(MAX_QUBITS, int(data.get("n", 4))))
        topology = data.get("topology", "grid")

        from frequency_planner  import plan_chip
        from topology_router    import place_qubits
        from netlist_generator  import build_netlist

        freq_plan = plan_chip(n)
        placement = place_qubits(n, topology=topology)
        nl        = build_netlist(freq_plan, placement)

        return jsonify(nl.to_dict())

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# EM simulation stub — Phase 9
# ---------------------------------------------------------------------------

@app.route("/em-simulation", methods=["POST"])
def em_simulation():
    """
    Phase 9 stub: EM simulation integration (HFSS / Sonnet via Qiskit Metal renderers).
    Body: {"n": 4, "topology": "grid", "backend": "hfss"}
    Currently returns simulation parameters; full HFSS/Sonnet integration is Phase 9.
    """
    try:
        data     = request.get_json(silent=True) or {}
        n        = max(1, min(MAX_QUBITS, int(data.get("n", 4))))
        topology = data.get("topology", "grid")
        backend  = data.get("backend", "hfss")   # 'hfss' | 'q3d' | 'sonnet'

        from frequency_planner import plan_chip
        from topology_router   import place_qubits

        freq_plan = plan_chip(n)
        placement = place_qubits(n, topology=topology)

        # Simulation parameters that would be passed to HFSS/Sonnet
        sim_params = {
            "backend":    backend,
            "n_qubits":   n,
            "topology":   topology,
            "sim_ready":  False,    # True when Metal→HFSS renderer is wired up
            "note":       "Full EM simulation requires Ansys HFSS or Sonnet licence + renderer",
            "resonator_targets": {
                r.name: {
                    "freq_GHz":  r.freq_GHz,
                    "length_mm": r.length_mm,
                    "validate":  ["Q_ext", "Q_int", "kappa", "chi"],
                }
                for r in freq_plan.resonators
            },
            "qubit_targets": {
                q.name: {
                    "freq_GHz": q.freq_GHz,
                    "EJ_GHz":   q.EJ_GHz,
                    "validate": ["f_01", "anharmonicity", "T1", "T2"],
                }
                for q in freq_plan.qubits
            },
        }
        return jsonify(sim_params)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Placement endpoint — Phase 3 (graph-based solver)
# ---------------------------------------------------------------------------

@app.route("/placement", methods=["POST"])
def placement():
    """
    Return graph-solver physical placement for a given topology.
    Body: {"n": 4, "topology": "grid", "scale": 1.0}
    """
    try:
        data     = request.get_json(silent=True) or {}
        n        = max(1, min(MAX_QUBITS, int(data.get("n", 4))))
        topology = data.get("topology", "grid")
        scale    = float(data.get("scale", 1.0))

        from topology_router import place_qubits, placement_to_dict
        result = place_qubits(n, topology=topology, scale=scale)
        return jsonify(placement_to_dict(result))

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
