# QBETA Backend

Python Flask API that powers the QBETA quantum chip design platform.  
Converts natural language prompts into physics-accurate superconducting chip layouts.

---

## Requirements

- Python 3.10+
- pip

```bash
pip install -r requirements.txt
```

**Optional (enables full fabrication mode):**
```bash
pip install --user qiskit-metal
```

**Optional (enables ML intent classification):**
```bash
pip install torch
```

---

## Starting the Server

```bash
python app.py
# → http://localhost:5000
```

The server starts with:
- `QISKIT_METAL_HEADLESS=1` set automatically (no GUI needed)
- Graceful fallback to schematic mode if Qiskit Metal is not installed
- Graceful fallback to regex parsing if PyTorch is not installed

---

## Module Reference

### `app.py` — Flask Entry Point

The API server. Hosts all HTTP endpoints and delegates to the pipeline modules.

**Key endpoints:**

| Endpoint | Input | Output |
|----------|-------|--------|
| `POST /generate` | `{ "prompt": "..." }` | Full chip result (image, freq plan, DRC, netlist) |
| `POST /frequency-plan` | `{ "n_qubits": 4 }` | Frequency assignments + resonator lengths |
| `POST /placement` | `{ "n_qubits": 4, "topology": "grid" }` | Qubit (x, y) positions + coupling edges |
| `POST /netlist` | `{ "n_qubits": 4, "topology": "grid" }` | Full chip netlist JSON |
| `POST /drc` | `{ "n_qubits": 4 }` | DRC violations list |
| `GET /health` | — | System status (Metal, torch, model loaded) |
| `GET /metal-status` | — | Qiskit Metal component availability |

---

### `ml_intent.py` — Intent Classifier

Reads a natural language prompt and predicts the number of qubits and chip topology.

**Architecture:**
- A small PyTorch feedforward neural network: `8 → 16 → 7`
- Bag-of-words input features (8 keywords: qubit, grid, star, line, etc.)
- Output: one of 7 classes (= 1–7 qubits)
- Topology is refined by keyword matching after classification

**Fallback behavior:**
- If `torch` is not installed → uses pure regex/rule-based parsing
- If qubit count > 7 → skips ML, uses regex directly

**Key functions:**
```python
resolve_design_params(prompt, max_qubits=24)
# Returns: (n_qubits, requested_qubits, topology, ml_info_dict)
```

---

### `frequency_planner.py` — Frequency Assignment

Assigns GHz frequencies to all qubits and readout resonators using IBM-style physics.

**Algorithm:**
1. **A/B bipartite coloring** — graph 2-coloring ensures adjacent qubits have different frequency groups
2. **Qubit frequencies** — Group A: 5.0–5.4 GHz, Group B: 4.6–5.0 GHz (100 MHz steps)
3. **Resonator frequencies** — 6.4–7.2 GHz band, spread evenly, detuned 1.2–2.0 GHz from qubit
4. **λ/4 length** — computed from `c / (4 × f × √ε_eff)` with Nb-on-Si substrate (`ε_r = 11.9`)

**Key functions:**
```python
plan_chip(n_qubits, topology="grid")
# Returns: FrequencyPlan with .qubits, .resonators, .substrate

plan_chip(n_qubits).to_dict()
# Returns JSON-serialisable dict for the API
```

---

### `topology_router.py` — Physical Placement

Converts qubit count + topology into physical (x, y) coordinates and coupling edges.

**Supported topologies:**

| Topology | Description |
|----------|-------------|
| `grid` | 2D rectangular grid (default) |
| `line` | 1D linear chain |
| `star` | Central hub with satellite qubits |
| `ring` | Circular arrangement |
| `heavy-hex` | IBM heavy-hexagon lattice |

**Layout engine:**
- Uses NetworkX `kamada_kawai_layout` for graph-based optimal spacing
- Falls back to spring layout for very large chips
- Output coordinates normalised to mm scale

**Key functions:**
```python
place_qubits(n_qubits, topology="grid")
# Returns: PlacementResult with .qubits (list of QubitPosition) and .edges (list of CouplingEdge)
```

---

### `netlist_generator.py` — Chip Netlist

Builds the connectivity graph of all chip components before any geometry is created.

**Netlist structure:**
```
feedline      → LP_L.tie ── LP_R.tie
ro_Q1         → Q1.readout ── FL_coup_Q1.short    (resonator net)
bus_Q1_Q2     → Q1.a ── Q2.c                       (coupler net)
bias_Q1       → BIAS_Q1.tie                         (flux bias)
```

**Key functions:**
```python
build_netlist(freq_plan, placement)
# Returns: Netlist object

netlist.to_dict()
# Returns: JSON with nets summary (feedlines, resonators, couplers, bias_lines)
```

---

### `drc.py` — Design Rule Checker

Validates the chip design before any fabrication step. Catches errors that would cause a real device to fail.

**7 rule categories:**

| Rule | Severity | What it checks |
|------|----------|----------------|
| `SPACING.QUBIT` | ERROR | Qubit centre-to-centre ≥ 0.6 mm |
| `CPW.GAP` | ERROR | CPW gap ≥ 4 µm (Nb on Si minimum) |
| `CPW.WIDTH` | ERROR | CPW width ≥ 5 µm |
| `FREQUENCY.QUBIT_COLLISION` | ERROR | Adjacent qubit detuning ≥ 100 MHz |
| `FREQUENCY.RESONATOR_COLLISION` | ERROR | Resonator separation ≥ 50 MHz |
| `FREQUENCY.DISPERSIVE_DETUNING_LOW` | ERROR | `|f_r − f_q|` ≥ 1.0 GHz |
| `FREQUENCY.DISPERSIVE_DETUNING_HIGH` | WARNING | `|f_r − f_q|` ≤ 3.0 GHz |

**Key functions:**
```python
run_drc(placement, freq_plan)
# Returns: DRCReport with .errors, .warnings, .passed(), .to_dict()
```

---

### `metal_connector.py` — Qiskit Metal Geometry Builder

Creates actual Qiskit Metal component objects on a `DesignPlanar` canvas.

**Components placed:**
- `TransmonPocket` — one per qubit, with 5 connection pads (readout + 4 bus pins)
- `LaunchpadWirebond` — one per qubit (unique, non-shared), staggered if same quadrant
- `RouteMeander` — quarter-wave readout resonators (qubit → launchpad)
- `RouteMeander` — coupling buses (horizontal + vertical neighbours)

**Key fix applied (this session):** Each qubit gets its own dedicated `LaunchpadWirebond` — multiple qubits in the same corner quadrant are staggered 0.6 mm apart. This prevents the previous `LP.tie` pin collision that caused routing failures.

**Key functions:**
```python
metal_status()
# Returns: dict with installed/version/test_build/components

build_metal_chip(n, topology, scale, freq_plan, placement)
# Returns: (DesignPlanar, MetalBuildLog)

render_metal_design(design, dpi=200, title="")
# Returns: base64-encoded PNG string
```

---

### `metal_design.py` — Pipeline Orchestrator

The main public gateway for generating a chip. Chooses between Metal mode and schematic fallback.

```python
generate_metal_chip(prompt)
# Returns dict with all fields the API sends to the frontend:
# { fabricated_image, frequency_plan, topology, num_qubits,
#   engine, interpretation, drc, build_log, netlist }
```

**Decision logic:**
1. Call `ml_intent.resolve_design_params(prompt)` → qubit count + topology
2. Call `frequency_planner.plan_chip()` → FrequencyPlan
3. Call `topology_router.place_qubits()` → PlacementResult
4. Call `netlist_generator.build_netlist()` → Netlist
5. Call `drc.run_drc()` → DRCReport
6. If Qiskit Metal available → call `metal_connector.build_metal_chip()` + `render_metal_design()`
7. Else → call `chip_renderer.render_chip()` for schematic fallback

---

### `chip_renderer.py` — SEM-Style Renderer

Produces a high-fidelity SEM-style image using `matplotlib` without requiring Qiskit Metal.

- **Dark ground plane** (`#050a18` navy)
- **Cyan CPW traces** with meander routing
- **Transmon pocket** rectangles with junction lines
- **Launchpad** trapezoids at chip edges
- Used as fallback when Metal is not installed

---

### `frequency_planner.py` substrate parameters

```python
SUBSTRATE = {
    "name":         "Si",
    "epsilon_r":    11.9,        # Silicon relative permittivity
    "cpw_width_um": 10.0,        # centre conductor (µm)
    "cpw_gap_um":   6.0,         # CPW gap (µm)
    "thickness_um": 525.0,       # wafer thickness (µm)
}
```

---

### `gds_export.py` — GDSII Export

Exports the Qiskit Metal design to a `.gds` file for mask-making.

```python
export_gds(design, output_path="chip.gds")
# Uses QGDSRenderer from qiskit_metal.renderers
```

> **Note:** Requires Qiskit Metal to be installed. Output `.gds` files are excluded from git.

---

### `circuit_gen.py` — Quantum Circuit Diagrams

Generates Qiskit circuit diagrams from prompts (Bell chain, GHZ, QFT, Grover, Toffoli, ring).

- Gracefully skips if `qiskit` is not installed (`_QISKIT_OK` flag)
- `_qubit_index()` handles both Qiskit < 0.45 and ≥ 0.45 Bit API changes

---

## Running Tests

```bash
# Quick API smoke test (server must be running)
python test_api.py

# Full pipeline test (no server needed)
python test_v2_pipeline.py
```

---

## Training the ML Model

```bash
python train_ml_model.py
# Trains a new QuantumIntentModel and saves to models/intent_model.pt
```

The model is a tiny bag-of-words classifier trained on ~70 example prompts.  
It runs in under 1 second and produces a < 10 KB `.pt` file.

---

## Requirements

```
flask
flask-cors
matplotlib
networkx
numpy
requests
torch              # optional — enables ML intent classification
qiskit             # optional — enables circuit diagram generation
qiskit-aer         # optional
pylatexenc         # optional — needed by qiskit circuit drawer
# qiskit-metal     # optional — install from source for full fabrication
```