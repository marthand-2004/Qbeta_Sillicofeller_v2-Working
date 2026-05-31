"""
renderer.py
===========
Thin rendering wrapper for QBETA V2.

Responsibilities:
  - Accept a Qiskit Metal design OR a PlacementResult + FrequencyPlan
  - Render to PNG (base64) using the Metal matplotlib backend
  - Apply the SEM-style colour aesthetic
  - Return a base64 string suitable for JSON API responses

This module does NOT generate geometry — it only renders what already exists.
"""

from __future__ import annotations

import base64
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


# ---------------------------------------------------------------------------
# SEM-style colour palette
# ---------------------------------------------------------------------------

PALETTE = {
    "background":  "#020610",
    "ground":      "#0a1e38",
    "metal":       "#c8ecff",
    "metal_edge":  "#a8e4ff",
    "feedline":    "#7ec8ff",
    "resonator":   "#88d4ff",
    "qubit_fill":  "#0c2240",
    "qubit_edge":  "#88d4ff",
    "text":        "#7ec8ff",
    "spine":       "#1a3a5c",
    "tick":        "#4a7a9a",
}


# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------

def _apply_sem_style(fig) -> None:
    """Apply navy/cyan SEM aesthetic to a matplotlib figure."""
    fig.patch.set_facecolor(PALETTE["background"])
    for ax in fig.axes:
        ax.set_facecolor(PALETTE["background"])
        ax.tick_params(colors=PALETTE["tick"], labelsize=7)
        for spine in ax.spines.values():
            spine.set_color(PALETTE["spine"])
        for line in ax.get_lines():
            line.set_color(PALETTE["metal"])
            line.set_linewidth(max(line.get_linewidth(), 1.2))
            line.set_alpha(0.95)
        for coll in ax.collections:
            try:
                coll.set_edgecolor(PALETTE["metal_edge"])
                coll.set_facecolor(PALETTE["ground"])
                coll.set_alpha(0.92)
                coll.set_linewidth(1.0)
            except Exception:
                pass
        for patch in ax.patches:
            try:
                fc = patch.get_facecolor()
                if np.mean(fc[:3]) > 0.3:
                    patch.set_facecolor(PALETTE["qubit_fill"])
                patch.set_edgecolor(PALETTE["qubit_edge"])
                patch.set_linewidth(1.2)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Metal design renderer
# ---------------------------------------------------------------------------

def render_design(
    design,
    title: str = "QBETA V2 — Superconducting Chip",
    dpi: int = 180,
    figsize: tuple = (10, 10),
) -> str:
    """
    Render a Qiskit Metal DesignPlanar to a base64 PNG.

    Parameters
    ----------
    design  : qiskit_metal DesignPlanar (must be rebuilt before calling)
    title   : plot title
    dpi     : output resolution
    figsize : figure dimensions in inches

    Returns
    -------
    base64-encoded PNG string
    """
    import qiskit_metal as qm

    fig = None
    try:
        fig = qm.view(design, figsize=figsize)
    except Exception:
        pass

    if fig is None:
        fig, ax = plt.subplots(figsize=figsize, facecolor=PALETTE["background"])
        ax.set_facecolor(PALETTE["background"])
        for comp in design.components.values():
            try:
                comp.qgeometry_plot(ax)
            except Exception:
                pass
        ax.set_aspect("equal")

    _apply_sem_style(fig)

    ax = fig.axes[0] if fig.axes else None
    if ax:
        ax.set_title(title, color=PALETTE["text"], fontsize=11, pad=8)
        ax.axis("off")

    return _fig_to_base64(fig, dpi)


# ---------------------------------------------------------------------------
# Schematic renderer (no Metal required)
# ---------------------------------------------------------------------------

def render_schematic(
    placement,        # topology_router.PlacementResult
    freq_plan=None,   # frequency_planner.FrequencyPlan (optional)
    title: str = "QBETA V2 — Chip Schematic",
    dpi: int = 150,
    figsize: tuple = (10, 10),
) -> str:
    """
    Render a schematic chip diagram from a PlacementResult.
    No Qiskit Metal required — pure matplotlib.

    Returns base64 PNG.
    """
    from topology_router import PlacementResult

    fig, ax = plt.subplots(figsize=figsize, facecolor=PALETTE["background"])
    ax.set_facecolor(PALETTE["background"])
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, color=PALETTE["text"], fontsize=12, pad=10)

    # ---- Draw coupling edges ----
    qubit_pos = {q.name: (q.x_mm, q.y_mm) for q in placement.qubits}
    for edge in placement.edges:
        if edge.qubit_a in qubit_pos and edge.qubit_b in qubit_pos:
            xa, ya = qubit_pos[edge.qubit_a]
            xb, yb = qubit_pos[edge.qubit_b]
            ax.plot([xa, xb], [ya, yb], color=PALETTE["feedline"],
                    linewidth=1.8, alpha=0.7, zorder=1)

    # ---- Draw feedline ----
    fl_y = max(q.y_mm for q in placement.qubits) + 1.2
    xs   = sorted(q.x_mm for q in placement.qubits)
    if xs:
        fl_x0, fl_x1 = xs[0] - 0.8, xs[-1] + 0.8
        ax.plot([fl_x0, fl_x1], [fl_y, fl_y],
                color=PALETTE["feedline"], linewidth=3.0, alpha=0.85, zorder=2)
        # Launchpads
        for lp_x in [fl_x0, fl_x1]:
            ax.plot(lp_x, fl_y, "D", color=PALETTE["metal"],
                    markersize=9, zorder=3)
        # Coupling stubs
        for q in placement.qubits:
            ax.plot([q.x_mm, q.x_mm], [fl_y - 0.15, fl_y],
                    color=PALETTE["resonator"], linewidth=1.2, alpha=0.8, zorder=2)

    # ---- Draw resonators ----
    for q in placement.qubits:
        ro_y_mid = (q.y_mm + fl_y) / 2
        _draw_meander(ax, q.x_mm, q.y_mm + 0.2, ro_y_mid - 0.1, color=PALETTE["resonator"])

    # ---- Draw qubits ----
    for q in placement.qubits:
        _draw_transmon(ax, q.x_mm, q.y_mm, label=q.name, freq_plan=freq_plan)

    # ---- Axis limits ----
    all_x = [q.x_mm for q in placement.qubits]
    all_y = [q.y_mm for q in placement.qubits]
    pad = 1.5
    ax.set_xlim(min(all_x) - pad, max(all_x) + pad)
    ax.set_ylim(min(all_y) - pad, fl_y + 0.5)

    return _fig_to_base64(fig, dpi)


# ---------------------------------------------------------------------------
# Drawing primitives
# ---------------------------------------------------------------------------

def _draw_transmon(ax, cx, cy, label: str = "", freq_plan=None) -> None:
    """Draw a schematic transmon pocket."""
    from matplotlib.patches import FancyBboxPatch, Circle

    size = 0.3
    rect = FancyBboxPatch(
        (cx - size, cy - size), 2 * size, 2 * size,
        boxstyle="round,pad=0.03",
        facecolor=PALETTE["qubit_fill"],
        edgecolor=PALETTE["qubit_edge"],
        linewidth=1.5,
        zorder=4,
    )
    ax.add_patch(rect)

    # Josephson junction symbol
    ax.plot([cx - 0.08, cx + 0.08], [cy, cy],
            color=PALETTE["metal"], linewidth=2.5, zorder=5)
    ax.plot([cx, cx], [cy - 0.08, cy + 0.08],
            color=PALETTE["metal"], linewidth=2.5, zorder=5)

    # Label
    freq_str = ""
    if freq_plan:
        for q in freq_plan.qubits:
            if q.name == label:
                freq_str = f"\n{q.freq_GHz:.3f} GHz"
                break

    ax.text(cx, cy - size - 0.12, f"{label}{freq_str}",
            color=PALETTE["text"], fontsize=7, ha="center", va="top", zorder=6)


def _draw_meander(ax, x, y_bot, y_top, color, turns: int = 3) -> None:
    """Draw a simplified meander resonator schematic."""
    width = 0.12
    step  = (y_top - y_bot) / max(turns * 2, 1)
    xs, ys = [x], [y_bot]
    direction = 1
    y = y_bot
    for i in range(turns * 2):
        y += step
        xs.extend([x + direction * width, x + direction * width, x])
        ys.extend([ys[-1], y, y])
        direction *= -1
    xs.append(x)
    ys.append(y_top)
    ax.plot(xs, ys, color=color, linewidth=1.2, alpha=0.75, zorder=3)


# ---------------------------------------------------------------------------
# Shared utility
# ---------------------------------------------------------------------------

def _fig_to_base64(fig, dpi: int) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                facecolor=PALETTE["background"])
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")
