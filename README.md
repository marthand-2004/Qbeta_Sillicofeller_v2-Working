# QBETA V2 — AI-Native Superconducting Quantum Chip Engineering Platform

> **Natural language → Physics-accurate quantum chip layout → Fabricated GDS export**

QBETA is a full-stack engineering workspace that takes a plain-English description of a quantum chip and produces a physically accurate, fabrication-ready superconducting chip layout — complete with frequency planning, coupling topology, Design Rule Checking, and SEM-style rendering.

---

## What QBETA Does

You type:
```
Design a 4-qubit grid superconducting chip with readout resonators
```

QBETA delivers:
- A **fabricated chip image** (SEM-style dark render with CPW traces, transmon pockets, launchpads)
- **Frequency plan** — every qubit and resonator assigned a GHz frequency using IBM-style A/B bipartite detuning
- **Quarter-wave resonator lengths** — physics-computed λ/4 CPW lengths based on substrate permittivity
- **DRC report** — Design Rule Check covering spacing, frequency collisions, dispersive regime validation
- **Chip netlist** — connectivity map of all components

---

## Architecture Overview

```
User Prompt (natural language)
        │
        ▼
┌─────────────────┐
│  ML Intent      │  ← PyTorch neural net (1–7 qubits) or
│  ml_intent.py   │    regex fallback (8+ qubits / no torch)
└────────┬────────┘
         │  (n_qubits, topology)
         ▼
┌─────────────────┐
│ Frequency Plan  │  ← IBM-style A/B bipartite qubit detuning
│ frequency_plan  │    λ/4 resonator physics (Nb on Si, εᵣ=11.9)
│     ner.py      │
└────────┬────────┘
         │  (FrequencyPlan: qubit & resonator specs)
         ▼
┌─────────────────┐
│ Topology Router │  ← Kamada-Kawai / spring graph layout
│ topology_router │    returns qubit (x,y) positions + coupling edges
│     .py         │
└────────┬────────┘
         │  (PlacementResult)
         ▼
┌─────────────────┐
│ Netlist Builder │  ← Connectivity: feedline, resonators, buses, bias
│ netlist_gen.py  │
└────────┬────────┘
         │  (Netlist)
         ▼
┌─────────────────┐
│      DRC        │  ← 7 rule categories checked
│    drc.py       │    spacing / CPW dims / freq detuning / dispersive
└────────┬────────┘
         │  (DRCReport)
         ▼
┌─────────────────────────────────────────┐
│  Qiskit Metal Connector (if available)  │  ← DesignPlanar
│  metal_connector.py                     │    TransmonPocket × N
│                                         │    LaunchpadWirebond × N (unique, no sharing)
│                                         │    RouteMeander resonators
│                                         │    RouteMeander coupling buses
└────────┬────────────────────────────────┘
         │  OR  (if Metal not installed)
         ▼
┌─────────────────┐
│  Chip Renderer  │  ← matplotlib SEM-style fallback
│ chip_renderer.py│
└────────┬────────┘
         │  (base64 PNG)
         ▼
    Flask API  →  React Frontend
```

---

## Repository Structure

```
QBETA_sillicofeller v2/
├── backend/                  # Python Flask API + all chip design logic
│   ├── app.py                # Flask entry point, all API endpoints
│   ├── ml_intent.py          # PyTorch intent classifier
│   ├── frequency_planner.py  # IBM-style frequency assignment + λ/4 physics
│   ├── topology_router.py    # Graph-based qubit placement
│   ├── netlist_generator.py  # Chip connectivity netlist
│   ├── drc.py                # Design Rule Checker (7 rule categories)
│   ├── metal_connector.py    # Qiskit Metal geometry builder
│   ├── metal_design.py       # Orchestration: chooses Metal vs. schematic
│   ├── metal_fabricated.py   # High-level build orchestrator
│   ├── chip_renderer.py      # SEM-style matplotlib renderer
│   ├── renderer.py           # Rendering helpers and style system
│   ├── circuit_gen.py        # Qiskit circuit diagram generator
│   ├── coupler_generator.py  # Qubit–qubit coupling bus builder
│   ├── feedline_generator.py # CPW feedline + launchpad builder
│   ├── resonator_generator.py# λ/4 readout resonator builder
│   ├── gds_export.py         # GDSII export (Qiskit Metal QGDSRenderer)
│   ├── train_ml_model.py     # One-shot ML model training script
│   ├── test_api.py           # Quick API smoke test
│   ├── test_v2_pipeline.py   # End-to-end pipeline test
│   └── requirements.txt      # Python dependencies
│
├── frontend/                 # React + Vite chat UI
│   ├── src/
│   │   ├── main.jsx          # Entire React app (chatbot + chip viewer)
│   │   └── styles.css        # ChatGPT-style dark theme
│   ├── index.html            # HTML entry with Google Fonts
│   ├── package.json          # Node dependencies
│   └── serve-dist.mjs        # Static production server
│
├── .gitignore                # Excludes: __pycache__, Design, *.gds, models/*.pt
└── .venv/                    # Python virtual environment (not committed)
```

---

## Quick Start

### 1. Backend

```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Optional: install Qiskit Metal for full fabrication mode
# pip install --user qiskit-metal

# Start the API server
python app.py
# → Running on http://localhost:5000
```

### 2. Frontend

```bash
cd frontend

npm install
npm run dev
# → Running on http://localhost:5173
```

Then open **http://localhost:5173** in your browser.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/generate` | Generate chip from a natural language prompt |
| `POST` | `/frequency-plan` | Standalone frequency plan (no Metal required) |
| `POST` | `/placement` | Compute qubit positions (Kamada-Kawai) |
| `POST` | `/netlist` | Build chip connectivity netlist |
| `POST` | `/drc` | Run Design Rule Check |
| `POST` | `/em-simulation` | EM simulation stub (HFSS/Sonnet — future) |
| `GET`  | `/health` | Full system status report |
| `GET`  | `/metal-status` | Qiskit Metal installation details |

### Example: Generate a chip

```bash
curl -X POST http://localhost:5000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Design a 4-qubit grid superconducting chip"}'
```

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `QISKIT_METAL_HEADLESS` | `1` | Run Qiskit Metal without a GUI |
| `QISKIT_METAL_SUPPRESS_RENAME_WARNING` | `1` | Suppress component rename logs |
| `VITE_API_BASE_URL` | `http://localhost:5000` | Backend URL for the frontend |

---

## Optional Dependencies

| Package | Required? | Effect if missing |
|---------|-----------|-------------------|
| `qiskit-metal` | Optional | Falls back to matplotlib schematic renderer |
| `torch` | Optional | Intent classification uses regex instead of ML |
| `qiskit` | Optional | Circuit diagram generation disabled gracefully |

---

## See Also

- [Backend README](./backend/README.md) — detailed Python module reference
- [Frontend README](./frontend/README.md) — React UI documentation
