import base64
import io
import re
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

try:
    from qiskit import QuantumCircuit
    _QISKIT_OK = True
except ImportError:
    _QISKIT_OK = False
    QuantumCircuit = None


def _detect_num_qubits(prompt: str) -> int:
    prompt_lower = prompt.lower()
    patterns = [
        r"(\d+)\s*-?\s*qubit",
        r"(\d+)\s*qubits",
        r"qubit[s]?\s*(\d+)",
        r"(\d+)\s*bit",
    ]
    for pattern in patterns:
        match = re.search(pattern, prompt_lower)
        if match:
            n = int(match.group(1))
            return max(2, min(8, n))
    return 4


def _detect_circuit_type(prompt: str) -> str:
    p = prompt.lower()
    if "bell" in p or "entangle" in p:
        return "bell"
    if "grover" in p or "search" in p:
        return "grover"
    if "qft" in p or "fourier" in p:
        return "qft"
    if "teleport" in p:
        return "teleport"
    if "toffoli" in p:
        return "toffoli"
    return "ring"


def _build_bell_chain(n: int) -> QuantumCircuit:
    qc = QuantumCircuit(n, name="Bell Chain")
    qc.h(0)
    for i in range(n - 1):
        qc.cx(i, i + 1)
    return qc


def _build_grover(n: int) -> QuantumCircuit:
    qc = QuantumCircuit(n, name="Grover Search")
    qc.h(range(n))
    qc.x(range(n))
    qc.h(n - 1)
    qc.mcx(list(range(n - 1)), n - 1)
    qc.h(n - 1)
    qc.x(range(n))
    qc.h(range(n))
    qc.h(range(n))
    qc.x(range(n))
    qc.h(n - 1)
    qc.mcx(list(range(n - 1)), n - 1)
    qc.h(n - 1)
    qc.x(range(n))
    qc.h(range(n))
    return qc


def _build_qft(n: int) -> QuantumCircuit:
    qc = QuantumCircuit(n, name="Quantum Fourier Transform")
    for j in range(n):
        qc.h(j)
        for k in range(j + 1, n):
            qc.cp(np.pi / (2 ** (k - j)), k, j)
    for i in range(n // 2):
        qc.swap(i, n - 1 - i)
    return qc


def _build_teleport() -> QuantumCircuit:
    qc = QuantumCircuit(3, name="Quantum Teleportation")
    qc.h(1)
    qc.cx(1, 2)
    qc.cx(0, 1)
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.h(1)
    qc.cx(1, 2)
    qc.cx(0, 1)
    return qc


def _build_toffoli(n: int) -> QuantumCircuit:
    qc = QuantumCircuit(n, name="Toffoli Gate")
    qc.h(range(n))
    if n >= 3:
        qc.ccx(0, 1, 2)
    if n >= 4:
        qc.ccx(1, 2, 3)
    if n >= 5:
        qc.ccx(2, 3, 4)
    for i in range(n - 1):
        qc.cx(i, (i + 1) % n)
    return qc


def _build_ring(n: int) -> QuantumCircuit:
    qc = QuantumCircuit(n, name="Ring Superposition")
    qc.h(range(n))
    for i in range(n):
        qc.cx(i, (i + 1) % n)
    qc.rz(np.pi / 4, range(n))
    for i in range(n - 1, -1, -1):
        qc.cx((i - 1) % n, i)
    return qc


def _build_circuit(circuit_type: str, n: int) -> QuantumCircuit:
    if circuit_type == "bell":
        return _build_bell_chain(n)
    if circuit_type == "grover":
        return _build_grover(n)
    if circuit_type == "qft":
        return _build_qft(n)
    if circuit_type == "teleport":
        return _build_teleport()
    if circuit_type == "toffoli":
        return _build_toffoli(max(n, 3))
    return _build_ring(n)


def _qubit_index(q, circuit=None) -> int:
    """Return integer index of a qubit regardless of Qiskit version."""
    # Qiskit < 0.45: Qubit had .index
    if hasattr(q, "index") and callable(q.index):
        try:
            return q.index
        except Exception:
            pass
    if hasattr(q, "_index"):
        return q._index
    # Qiskit >= 0.45: find index from circuit
    if circuit is not None:
        try:
            return circuit.find_bit(q).index
        except Exception:
            pass
    # Last resort
    try:
        return int(q)
    except (TypeError, ValueError):
        return 0


def _extract_edges(qc: "QuantumCircuit") -> List[Tuple[int, int]]:
    edges: List[Tuple[int, int]] = []
    seen = set()

    def add_edge(a: int, b: int):
        if a == b:
            return
        pair = (min(a, b), max(a, b))
        if pair not in seen:
            seen.add(pair)
            edges.append(pair)

    for instruction in qc.data:
        op = instruction.operation
        qubits = [_qubit_index(q, qc) for q in instruction.qubits]

        if len(qubits) == 2:
            add_edge(qubits[0], qubits[1])
        elif len(qubits) >= 3:
            for i in range(len(qubits)):
                for j in range(i + 1, len(qubits)):
                    add_edge(qubits[i], qubits[j])

    return edges


def _gate_label_on_edge(qc: "QuantumCircuit", a: int, b: int) -> str:
    labels = []
    for instruction in qc.data:
        op = instruction.operation
        qubits = [_qubit_index(q, qc) for q in instruction.qubits]
        if len(qubits) < 2:
            continue
        indices = set(qubits)
        if a in indices and b in indices:
            name = op.name.upper()
            if name in ("CX", "CNOT"):
                labels.append("CNOT")
            elif name == "CZ":
                labels.append("CZ")
            elif name in ("CCX", "TOFFOLI"):
                labels.append("CCX")
            elif name == "CP":
                labels.append("CP")
            elif name == "SWAP":
                labels.append("SWAP")
            else:
                labels.append(name)
    return labels[0] if labels else "LINK"


def _qubit_positions(n: int) -> Dict[int, Tuple[float, float]]:
    """Place qubits in a hardware-style layout (cross for 4, ring/grid for others)."""
    if n == 2:
        return {0: (-0.75, 0.0), 1: (0.75, 0.0)}
    if n == 3:
        return {0: (0.0, 0.85), 1: (-0.74, -0.43), 2: (0.74, -0.43)}
    if n == 4:
        return {0: (0.0, 0.95), 1: (0.95, 0.0), 2: (0.0, -0.95), 3: (-0.95, 0.0)}
    if n == 5:
        return {
            0: (0.0, 1.0),
            1: (0.95, 0.31),
            2: (0.59, -0.81),
            3: (-0.59, -0.81),
            4: (-0.95, 0.31),
        }
    if n == 6:
        return {
            0: (0.0, 1.0),
            1: (0.87, 0.5),
            2: (0.87, -0.5),
            3: (0.0, -1.0),
            4: (-0.87, -0.5),
            5: (-0.87, 0.5),
        }
    if n == 7:
        angles = [np.pi / 2 + 2 * np.pi * i / 7 for i in range(7)]
        return {i: (0.9 * np.cos(a), 0.9 * np.sin(a)) for i, a in enumerate(angles)}
    angles = [np.pi / 2 + 2 * np.pi * i / 8 for i in range(8)]
    return {i: (0.95 * np.cos(a), 0.95 * np.sin(a)) for i, a in enumerate(angles)}


def _draw_serpentine_coupler(
    ax, p1: Tuple[float, float], p2: Tuple[float, float], amplitude: float = 0.14
):
    """Draw a meander (serpentine) CPW resonator between two qubit pads."""
    x1, y1 = p1
    x2, y2 = p2
    t = np.linspace(0, 1, 120)
    mx = x1 + t * (x2 - x1)
    my = y1 + t * (y2 - y1)
    dx, dy = x2 - x1, y2 - y1
    length = np.hypot(dx, dy) or 1.0
    px, py = -dy / length, dx / length
    wiggles = max(5, int(length * 10))
    wave = amplitude * np.sin(2 * np.pi * wiggles * t)
    mx += px * wave
    my += py * wave
    ax.plot(mx, my, color="#4a4a4a", linewidth=1.15, solid_capstyle="round", zorder=2)


def _draw_qubit_pad(ax, x: float, y: float, label: str, w: float = 0.26, h: float = 0.26):
    """Grey rectangular transmon-style qubit with internal fine lines."""
    rect = mpatches.Rectangle(
        (x - w / 2, y - h / 2), w, h,
        facecolor="#c8c8c8", edgecolor="#3d3d3d", linewidth=0.9, zorder=4
    )
    ax.add_patch(rect)
    for offset in np.linspace(-0.07, 0.07, 5):
        ax.plot(
            [x + offset, x + offset], [y - 0.075, y + 0.075],
            color="#7a7a7a", linewidth=0.35, zorder=5
        )
    for offset in np.linspace(-0.07, 0.07, 5):
        ax.plot(
            [x - 0.075, x + 0.075], [y + offset, y + offset],
            color="#7a7a7a", linewidth=0.35, zorder=5
        )
    ax.text(x, y - h / 2 - 0.12, label, ha="center", va="top", fontsize=7, color="#333333", zorder=6)


def _draw_io_line(ax, x: float, y: float, extent: float = 1.42):
    """Control/readout line from qubit pad toward chip edge."""
    dist = np.hypot(x, y) or 1.0
    ux, uy = x / dist, y / dist
    x0 = x + ux * 0.18
    y0 = y + uy * 0.18
    x1 = ux * extent
    y1 = uy * extent
    ax.plot([x0, x1], [y0, y1], color="#5a5a5a", linewidth=0.9, zorder=1)


def _draw_alignment_markers(ax):
    """Small L-shaped alignment marks in chip corners."""
    corners = [(-1.35, 1.35), (1.35, 1.35), (-1.35, -1.35), (1.35, -1.35)]
    arm = 0.12
    for cx, cy in corners:
        sx = -1 if cx < 0 else 1
        sy = -1 if cy < 0 else 1
        ax.plot([cx, cx + sx * arm], [cy, cy], color="#aaaaaa", linewidth=0.6, zorder=0)
        ax.plot([cx, cx], [cy, cy + sy * arm], color="#aaaaaa", linewidth=0.6, zorder=0)


def _draw_chip_layout(qc: QuantumCircuit, edges: List[Tuple[int, int]], n: int) -> str:
    """Hardware schematic: white background, grey qubit pads, serpentine couplers."""
    positions = _qubit_positions(n)
    if not edges and n >= 2:
        edges = [(i, (i + 1) % n) for i in range(n)]

    fig, ax = plt.subplots(figsize=(7, 7), facecolor="#ffffff")
    ax.set_facecolor("#ffffff")
    ax.set_xlim(-1.55, 1.55)
    ax.set_ylim(-1.55, 1.55)
    ax.set_aspect("equal")
    ax.tick_params(colors="#888888", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#cccccc")

    _draw_alignment_markers(ax)

    drawn_pairs = set()
    for a, b in edges:
        pair = (min(a, b), max(a, b))
        if pair in drawn_pairs:
            continue
        drawn_pairs.add(pair)
        if a in positions and b in positions:
            _draw_serpentine_coupler(ax, positions[a], positions[b])

    for i in range(n):
        if i in positions:
            x, y = positions[i]
            _draw_io_line(ax, x, y)
            _draw_qubit_pad(ax, x, y, f"Q{i}")

    ax.set_xlabel("mm", fontsize=8, color="#888888")
    ax.set_ylabel("mm", fontsize=8, color="#888888")
    ax.set_title("Chip Design Layout", fontsize=11, color="#333333", pad=10)
    ax.grid(True, color="#e8e8e8", linewidth=0.5, linestyle="-", alpha=0.7)
    plt.tight_layout()
    return _fig_to_base64(fig)


def _draw_circuit_diagram(qc: QuantumCircuit) -> str:
    fig = qc.draw(output="mpl", style="bw", fold=-1)
    if isinstance(fig, tuple):
        fig = fig[0]
    fig.patch.set_facecolor("#FFFFFF")
    plt.tight_layout()
    return _fig_to_base64(fig)


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def generate_chip_design(prompt: str) -> dict:
    """Generate circuit diagram from prompt. Returns empty dict if qiskit unavailable."""
    if not _QISKIT_OK:
        return {"error": "qiskit not installed", "circuit_image": "", "depth": 0}

    try:
        circuit_type = _detect_circuit_type(prompt)
        n = _detect_num_qubits(prompt)

        if circuit_type == "teleport":
            n = 3
        elif circuit_type == "toffoli":
            n = max(n, 3)

        qc = _build_circuit(circuit_type, n)
        n = qc.num_qubits
        edges = _extract_edges(qc)
        depth = qc.depth()

        chip_image    = _draw_chip_layout(qc, edges, n)
        circuit_image = _draw_circuit_diagram(qc)
        code          = str(qc.draw(output="text", fold=-1))

        return {
            "label":         qc.name or "Quantum Circuit",
            "chip_image":    chip_image,
            "circuit_image": circuit_image,
            "edges":         edges,
            "num_qubits":    n,
            "depth":         depth,
            "code":          code,
        }
    except Exception as exc:
        import warnings
        warnings.warn(f"[circuit_gen] generate_chip_design failed: {exc}")
        return {"error": str(exc), "circuit_image": "", "depth": 0}
