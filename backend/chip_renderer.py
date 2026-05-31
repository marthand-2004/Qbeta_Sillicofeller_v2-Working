"""
High-fidelity superconducting chip layout renderer (Qiskit Metal–style CAD + fabricated view).
"""
import base64
import io
from typing import Dict, List, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np


def _positions(n: int, topology: str, scale: float = 1.0) -> Dict[int, Tuple[float, float]]:
    if n == 4 and topology in ("ring", "grid", "star"):
        r = 0.95 * scale
        return {0: (0.0, r), 1: (r, 0.0), 2: (0.0, -r), 3: (-r, 0.0)}
    if topology == "line":
        span = 1.5 * scale * max(n - 1, 1)
        step = span / max(n - 1, 1)
        x0 = -span / 2
        return {i: (x0 + i * step, 0.0) for i in range(n)}
    radius = 1.0 * scale
    return {
        i: (radius * np.cos(np.pi / 2 + 2 * np.pi * i / n),
            radius * np.sin(np.pi / 2 + 2 * np.pi * i / n))
        for i in range(n)
    }


def _ring_edges(n: int) -> List[Tuple[int, int]]:
    return [(i, (i + 1) % n) for i in range(n)]


def _line_edges(n: int) -> List[Tuple[int, int]]:
    return [(i, i + 1) for i in range(n - 1)]


def _topology_edges(n: int, topology: str) -> List[Tuple[int, int]]:
    if topology == "line":
        return _line_edges(n)
    if n == 4 and topology == "grid":
        return [(0, 1), (1, 2), (2, 3), (3, 0)]
    return _ring_edges(n)


def _pad_anchor(
    pos: Tuple[float, float],
    target: Tuple[float, float],
    pad_w: float = 0.28,
    pad_h: float = 0.22,
) -> Tuple[float, float]:
    """Exit point on qubit pad edge toward coupling partner."""
    x, y = pos
    tx, ty = target
    dx, dy = tx - x, ty - y
    if abs(dx) >= abs(dy):
        return (x + (pad_w / 2) * np.sign(dx), y)
    return (x, y + (pad_h / 2) * np.sign(dy))


def _serpentine_path(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    meanders: int = 10,
    amplitude: float = 0.11,
    n_pts: int = 200,
) -> Tuple[np.ndarray, np.ndarray]:
    x1, y1 = p1
    x2, y2 = p2
    t = np.linspace(0, 1, n_pts)
    mx = x1 + t * (x2 - x1)
    my = y1 + t * (y2 - y1)
    dx, dy = x2 - x1, y2 - y1
    length = np.hypot(dx, dy) or 1.0
    px, py = -dy / length, dx / length
    wave = amplitude * np.sin(2 * np.pi * meanders * t)
    return mx + px * wave, my + py * wave


def _draw_cpw_line(ax, xs, ys, color="#3a3a3a", width=1.4, gap=0.018, zorder=2):
    """Coplanar waveguide: center trace + gap edges."""
    ax.plot(xs, ys, color=color, linewidth=width, solid_capstyle="round", zorder=zorder)
    dx = np.gradient(xs)
    dy = np.gradient(ys)
    norm = np.hypot(dx, dy)
    norm[norm == 0] = 1
    nx, ny = -dy / norm, dx / norm
    ax.plot(xs + nx * gap, ys + ny * gap, color=color, linewidth=0.5, alpha=0.55, zorder=zorder - 1)
    ax.plot(xs - nx * gap, ys - ny * gap, color=color, linewidth=0.5, alpha=0.55, zorder=zorder - 1)


def _draw_transmon_pad(ax, x: float, y: float, label: str, scale: float = 1.0):
    w, h = 0.30 * scale, 0.24 * scale
    pocket = mpatches.FancyBboxPatch(
        (x - w / 2 - 0.04, y - h / 2 - 0.04),
        w + 0.08, h + 0.08,
        boxstyle="round,pad=0.01,rounding_size=0.02",
        facecolor="#e8e8e8", edgecolor="#666666", linewidth=0.7, zorder=4,
    )
    ax.add_patch(pocket)
    pad = mpatches.Rectangle(
        (x - w / 2, y - h / 2), w, h,
        facecolor="#b5b5b5", edgecolor="#404040", linewidth=1.0, zorder=5,
    )
    ax.add_patch(pad)
    jj_w, jj_h = w * 0.12, h * 0.55
    ax.add_patch(mpatches.Rectangle(
        (x - jj_w / 2, y - jj_h / 2), jj_w, jj_h,
        facecolor="#d0d0d0", edgecolor="#505050", linewidth=0.6, zorder=6,
    ))
    for off in np.linspace(-w * 0.32, w * 0.32, 4):
        ax.plot([x + off, x + off], [y - h * 0.38, y + h * 0.38],
                color="#888888", linewidth=0.35, zorder=7)
    for off in np.linspace(-h * 0.3, h * 0.3, 3):
        ax.plot([x - w * 0.38, x + w * 0.38], [y + off, y + off],
                color="#888888", linewidth=0.35, zorder=7)
    ax.plot([x - w * 0.15, x + w * 0.15], [y, y], color="#555555", linewidth=0.8, zorder=8)
    ax.text(x, y - h / 2 - 0.14, label, ha="center", va="top", fontsize=8,
            color="#333333", fontweight="bold", zorder=9)


def _draw_readout_line(ax, x: float, y: float, extent: float = 1.38):
    d = np.hypot(x, y) or 1.0
    ux, uy = x / d, y / d
    ax.plot([x + ux * 0.20, ux * extent], [y + uy * 0.20, uy * extent],
            color="#555555", linewidth=1.0, zorder=1)


def _draw_alignment_marks(ax, lim: float = 1.42):
    for cx, cy in [(-lim, lim), (lim, lim), (-lim, -lim), (lim, -lim)]:
        s = 0.11
        sx = -1 if cx < 0 else 1
        sy = -1 if cy < 0 else 1
        ax.plot([cx, cx + sx * s], [cy, cy], color="#bbbbbb", lw=0.6, zorder=0)
        ax.plot([cx, cx], [cy, cy + sy * s], color="#bbbbbb", lw=0.6, zorder=0)


def _fig_to_b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def render_chip_schematic(
    n: int,
    topology: str = "ring",
    scale: float = 1.0,
    add_readout: bool = False,
) -> str:
    """CAD layout: white grid, grey transmon pads, serpentine RouteMeander-style CPWs."""
    positions = _positions(n, topology, scale)
    edges = _topology_edges(n, topology)

    fig, ax = plt.subplots(figsize=(7.5, 7.5), facecolor="#ffffff")
    ax.set_facecolor("#ffffff")
    lim = 1.55
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")
    ax.set_xlabel("mm", fontsize=9, color="#666666")
    ax.set_ylabel("mm", fontsize=9, color="#666666")
    ax.tick_params(labelsize=8, colors="#888888")
    ax.grid(True, color="#dcdcdc", linewidth=0.6, alpha=0.9)
    for spine in ax.spines.values():
        spine.set_color("#cccccc")

    _draw_alignment_marks(ax, lim - 0.1)

    drawn = set()
    for a, b in edges:
        pair = (min(a, b), max(a, b))
        if pair in drawn:
            continue
        drawn.add(pair)
        if a not in positions or b not in positions:
            continue
        p1 = _pad_anchor(positions[a], positions[b])
        p2 = _pad_anchor(positions[b], positions[a])
        dist = np.hypot(p2[0] - p1[0], p2[1] - p1[1])
        meanders = max(8, int(dist * 14))
        xs, ys = _serpentine_path(p1, p2, meanders=meanders, amplitude=0.10 * scale)
        _draw_cpw_line(ax, xs, ys)

    if add_readout:
        for i, (x, y) in positions.items():
            _draw_readout_line(ax, x, y)

    for i, (x, y) in positions.items():
        _draw_transmon_pad(ax, x, y, f"Q{i + 1}", scale)

    ax.set_title("Chip Design Layout", fontsize=12, color="#222222", pad=12, fontweight="bold")
    plt.tight_layout()
    return _fig_to_b64(fig)


def _grid_positions_4(scale: float) -> Dict[int, Tuple[float, float]]:
    """2×2 transmon grid (fabricated chip reference layout)."""
    d = 0.38 * scale
    return {0: (-d, d), 1: (d, d), 2: (-d, -d), 3: (d, -d)}


def _glow_trace(ax, xs, ys, glow="#4db8ff", core="#e8f8ff", glow_w=5.0, core_w=1.35, z=2):
    ax.plot(xs, ys, color=glow, linewidth=glow_w, alpha=0.22, solid_capstyle="round", zorder=z)
    ax.plot(xs, ys, color=glow, linewidth=glow_w * 0.55, alpha=0.45, solid_capstyle="round", zorder=z + 1)
    ax.plot(xs, ys, color=core, linewidth=core_w, alpha=0.98, solid_capstyle="round", zorder=z + 2)


def _meander_route(
    start: Tuple[float, float],
    end: Tuple[float, float],
    meanders: int = 14,
    amplitude: float = 0.055,
) -> Tuple[np.ndarray, np.ndarray]:
    return _serpentine_path(start, end, meanders=meanders, amplitude=amplitude, n_pts=280)


def _add_substrate_texture(ax, lim: float, seed: int = 42):
    rng = np.random.default_rng(seed)
    res = 256
    noise = rng.random((res, res)) * 0.04
    ax.imshow(
        noise, extent=(-lim, lim, -lim, lim), cmap="Blues_r", alpha=0.35,
        vmin=0, vmax=0.15, zorder=0, interpolation="bilinear",
    )


def _draw_fab_qubit(ax, x: float, y: float, scale: float):
    """Central transmon with ground-plane pocket (fabricated SEM style)."""
    ps = 0.20 * scale
    pocket = 0.30 * scale
    ax.add_patch(mpatches.Rectangle(
        (x - pocket / 2, y - pocket / 2), pocket, pocket,
        facecolor="#020810", edgecolor="#1a5080", linewidth=0.8, zorder=6,
    ))
    ax.add_patch(mpatches.Rectangle(
        (x - ps / 2, y - ps / 2), ps, ps,
        facecolor="#0a1e38", edgecolor="#88d4ff", linewidth=1.4, zorder=7,
    ))
    ax.add_patch(mpatches.Rectangle(
        (x - ps * 0.14, y - ps * 0.35), ps * 0.28, ps * 0.7,
        facecolor="#143050", edgecolor="#c8ecff", linewidth=0.7, zorder=8,
    ))
    ax.plot([x - ps * 0.22, x + ps * 0.22], [y, y], color="#e8f8ff", linewidth=1.0, zorder=9)


def _draw_bond_pad(ax, x: float, y: float, size: float = 0.14):
    ax.add_patch(mpatches.Rectangle(
        (x - size / 2, y - size / 2), size, size,
        facecolor="#0c2240", edgecolor="#a8e4ff", linewidth=1.6, zorder=10,
    ))


def _render_fabricated_4q(scale: float = 1.0) -> str:
    """High-fidelity 4-qubit fabricated chip matching reference SEM/CAD style."""
    positions = _grid_positions_4(scale)
    lim = 1.48

    fig, ax = plt.subplots(figsize=(8, 8), facecolor="#020610")
    ax.set_facecolor("#020610")
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")
    ax.axis("off")

    _add_substrate_texture(ax, lim)

    die = mpatches.FancyBboxPatch(
        (-1.25, -1.25), 2.5, 2.5,
        boxstyle="square,pad=0",
        facecolor="#030c1a", edgecolor="#1e4a78", linewidth=2.0, zorder=1,
    )
    ax.add_patch(die)

    for cx, cy in [(-1.15, 1.15), (1.15, 1.15), (-1.15, -1.15), (1.15, -1.15)]:
        s = 0.10
        sx, sy = (-1 if cx < 0 else 1), (-1 if cy < 0 else 1)
        ax.plot([cx, cx + sx * s], [cy, cy], color="#d8f0ff", lw=1.2, zorder=11, solid_capstyle="butt")
        ax.plot([cx, cx], [cy, cy + sy * s], color="#d8f0ff", lw=1.2, zorder=11, solid_capstyle="butt")

    couplings = [(0, 1), (2, 3), (0, 2), (1, 3)]
    for a, b in couplings:
        p1 = _pad_anchor(positions[a], positions[b], pad_w=0.22, pad_h=0.22)
        p2 = _pad_anchor(positions[b], positions[a], pad_w=0.22, pad_h=0.22)
        xs, ys = _meander_route(p1, p2, meanders=6, amplitude=0.025)
        _glow_trace(ax, xs, ys, z=3)

    readout_routes = [
        (0, (positions[0][0], 1.18), 20),
        (1, (positions[1][0], 1.18), 20),
        (2, (positions[2][0], -1.18), 20),
        (3, (positions[3][0], -1.18), 20),
        (0, (-1.18, positions[0][1]), 18),
        (1, (1.18, positions[1][1]), 18),
        (2, (-1.18, positions[2][1]), 18),
        (3, (1.18, positions[3][1]), 18),
    ]
    for qidx, end_pt, meanders in readout_routes:
        sx, sy = positions[qidx]
        start = _pad_anchor((sx, sy), end_pt, pad_w=0.22, pad_h=0.22)
        xs, ys = _meander_route(start, end_pt, meanders=meanders, amplitude=0.050)
        _glow_trace(ax, xs, ys, z=4)

    bond_pads = [
        (0.0, 1.32), (0.0, -1.32), (-1.32, 0.0), (1.32, 0.0),
        (-1.05, 1.05), (1.05, 1.05), (-1.05, -1.05), (1.05, -1.05),
    ]
    for bx, by in bond_pads:
        _draw_bond_pad(ax, bx, by, 0.13 * scale)

    feedlines = [
        ((0.0, 1.32), (0.0, 0.72)),
        ((0.0, -1.32), (0.0, -0.72)),
        ((-1.32, 0.0), (-0.72, 0.0)),
        ((1.32, 0.0), (0.72, 0.0)),
    ]
    for (x0, y0), (x1, y1) in feedlines:
        _glow_trace(ax, np.array([x0, x1]), np.array([y0, y1]), glow_w=3.5, core_w=1.1, z=5)

    perimeter_bus = [
        [(-0.95, 1.05), (0.95, 1.05)],
        [(-0.95, -1.05), (0.95, -1.05)],
        [(-1.05, -0.95), (-1.05, 0.95)],
        [(1.05, -0.95), (1.05, 0.95)],
    ]
    for seg in perimeter_bus:
        xs, ys = zip(*seg)
        _glow_trace(ax, np.array(xs), np.array(ys), glow_w=3.0, core_w=0.9, z=2)

    for i, (x, y) in positions.items():
        _draw_fab_qubit(ax, x, y, scale)

    ax.set_title("Fabricated Superconducting Chip", fontsize=12, color="#7ec8ff", pad=8, fontweight="bold")
    plt.tight_layout(pad=0.3)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def _grid_positions(n: int, scale: float) -> Dict[int, Tuple[float, float]]:
    cols = int(np.ceil(np.sqrt(n)))
    rows = int(np.ceil(n / cols))
    pitch = 0.38 * scale
    pos = {}
    idx = 0
    for r in range(rows):
        for c in range(cols):
            if idx >= n:
                break
            pos[idx] = ((c - (cols - 1) / 2) * pitch, ((rows - 1) / 2 - r) * pitch)
            idx += 1
    return pos


def render_fabricated_chip(
    n: int,
    topology: str = "ring",
    scale: float = 1.0,
) -> str:
    """Fabricated chip: navy substrate, cyan traces, 2×2 grid + meander readout."""
    if n == 4 and topology in ("grid", "ring", "star"):
        return _render_fabricated_4q(scale)
    if topology == "grid" or n > 4:
        return _render_fabricated_grid(n, scale)
    return _render_fabricated_generic(n, topology, scale)


def _render_fabricated_grid(n: int, scale: float) -> str:
    """N-qubit grid fabricated view (matches Metal grid layout)."""
    positions = _grid_positions(n, scale)
    cols = int(np.ceil(np.sqrt(n)))
    edges = []
    for i in range(n):
        if (i + 1) % cols != 0 and i + 1 < n:
            edges.append((i, i + 1))
        if i + cols < n:
            edges.append((i, i + cols))

    lim = max(1.5, 0.5 * cols * 0.38 * scale + 1.0)
    fig, ax = plt.subplots(figsize=(8, 8), facecolor="#020610")
    ax.set_facecolor("#020610")
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")
    ax.axis("off")
    _add_substrate_texture(ax, lim)

    drawn = set()
    for a, b in edges:
        pair = (min(a, b), max(a, b))
        if pair in drawn:
            continue
        drawn.add(pair)
        p1 = _pad_anchor(positions[a], positions[b], pad_w=0.18, pad_h=0.18)
        p2 = _pad_anchor(positions[b], positions[a], pad_w=0.18, pad_h=0.18)
        xs, ys = _meander_route(p1, p2, meanders=8, amplitude=0.04)
        _glow_trace(ax, xs, ys)

    for i, (x, y) in positions.items():
        d = np.hypot(x, y) or 1.0
        end = (x / d * (lim - 0.1), y / d * (lim - 0.1))
        start = _pad_anchor((x, y), end, pad_w=0.18, pad_h=0.18)
        xs, ys = _meander_route(start, end, meanders=12, amplitude=0.045)
        _glow_trace(ax, xs, ys, z=4)
        _draw_fab_qubit(ax, x, y, scale * 0.85)

    ax.set_title(f"Fabricated Chip — {n} Qubits", fontsize=11, color="#7ec8ff", pad=8)
    plt.tight_layout()
    return _fig_to_b64(fig)


def _render_fabricated_generic(n: int, topology: str, scale: float) -> str:
    positions = _positions(n, topology, scale)
    edges = _topology_edges(n, topology)
    lim = 1.55

    fig, ax = plt.subplots(figsize=(8, 8), facecolor="#020610")
    ax.set_facecolor("#020610")
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")
    ax.axis("off")
    _add_substrate_texture(ax, lim)

    for cx, cy in [(-1.15, 1.15), (1.15, 1.15), (-1.15, -1.15), (1.15, -1.15)]:
        s = 0.10
        sx, sy = (-1 if cx < 0 else 1), (-1 if cy < 0 else 1)
        ax.plot([cx, cx + sx * s], [cy, cy], color="#d8f0ff", lw=1.2, zorder=11)
        ax.plot([cx, cx], [cy, cy + sy * s], color="#d8f0ff", lw=1.2, zorder=11)

    drawn = set()
    for a, b in edges:
        pair = (min(a, b), max(a, b))
        if pair in drawn:
            continue
        drawn.add(pair)
        p1 = _pad_anchor(positions[a], positions[b])
        p2 = _pad_anchor(positions[b], positions[a])
        xs, ys = _meander_route(p1, p2, meanders=10)
        _glow_trace(ax, xs, ys)

    for i, (x, y) in positions.items():
        d = np.hypot(x, y) or 1.0
        end = (x / d * 1.25, y / d * 1.25)
        start = _pad_anchor((x, y), end)
        xs, ys = _meander_route(start, end, meanders=14)
        _glow_trace(ax, xs, ys)
        _draw_bond_pad(ax, end[0], end[1])
        _draw_fab_qubit(ax, x, y, scale)

    ax.set_title("Fabricated Superconducting Chip", fontsize=12, color="#7ec8ff", pad=8)
    plt.tight_layout()
    return _fig_to_b64(fig)
