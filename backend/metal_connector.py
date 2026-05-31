"""
metal_connector.py  —  QBETA V2 (2x2 Grid, Unique Per-Qubit Launchpads)
===========================================================================
Architecture matching reference images:

  LP_TL                LP_TR
    \\                  /
     R1 (meander)   R2 (meander)
      \\              /
       Q1 ──bus── Q2
       |              |
      bus            bus
       |              |
       Q3 ──bus── Q4
      /              \\
     R3 (meander)   R4 (meander)
    /                  \\
  LP_BL                LP_BR

Each qubit: RouteMeander resonator → its own unique LaunchpadWirebond
Adjacent qubits: RouteMeander coupling bus
"""

from __future__ import annotations
import os, io, base64, math
from dataclasses import dataclass, field
from typing import Any, List, Tuple

os.environ.setdefault("QISKIT_METAL_HEADLESS", "1")
os.environ.setdefault("QISKIT_METAL_SUPPRESS_RENAME_WARNING", "1")

QUBIT_PITCH = 2.0   # mm
LP_OFFSET   = 3.8   # mm from chip centre to launchpad
BUS_LENGTH  = 1.8   # mm


@dataclass
class BuildStep:
    name: str; status: str; detail: str = ""; count: int = 0

@dataclass
class MetalBuildLog:
    steps: List[BuildStep] = field(default_factory=list)
    def ok(self, n, d="", c=0): self.steps.append(BuildStep(n,"ok",d,c))
    def warn(self, n, d):       self.steps.append(BuildStep(n,"warn",d))
    def error(self, n, d):      self.steps.append(BuildStep(n,"error",d))
    def to_dict(self):
        return {"steps":[{"name":s.name,"status":s.status,"detail":s.detail}
                         for s in self.steps],
                "ok":sum(1 for s in self.steps if s.status=="ok"),
                "errors":sum(1 for s in self.steps if s.status=="error"),
                "warnings":sum(1 for s in self.steps if s.status=="warn")}


def metal_status() -> dict:
    st = {"installed":False,"version":None,"test_build":False,"error":None,"components":{}}
    try:
        import qiskit_metal as qm
        st["installed"]=True; st["version"]=getattr(qm,"__version__","unknown")
    except ImportError as e:
        st["error"]=str(e); return st
    for name,mod in {
        "TransmonPocket":    "qiskit_metal.qlibrary.qubits.transmon_pocket",
        "LaunchpadWirebond": "qiskit_metal.qlibrary.terminations.launchpad_wb",
        "RouteMeander":      "qiskit_metal.qlibrary.tlines.meandered",
        "RouteStraight":     "qiskit_metal.qlibrary.tlines.straight_path",
        "QGDSRenderer":      "qiskit_metal.renderers.renderer_gds.gds_renderer",
    }.items():
        try:   __import__(mod); st["components"][name]="available"
        except ImportError:    st["components"][name]="missing"
    try:   _quick_test(); st["test_build"]=True
    except Exception as e: st["error"]=str(e)
    return st


def _quick_test():
    from qiskit_metal import Dict
    from qiskit_metal.designs import DesignPlanar
    from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
    d=DesignPlanar(); d.overwrite_enabled=True
    TransmonPocket(d,"QT",options=Dict(pos_x="0mm",pos_y="0mm"))
    d.rebuild(); del d


def _grid_layout(n: int) -> dict:
    """2D grid positions + unique per-qubit launchpad positions (no sharing)."""
    cols  = max(2, math.ceil(math.sqrt(n)))
    rows  = math.ceil(n / cols)
    lp    = LP_OFFSET
    layout = {}
    idx = 0
    # Track how many qubits already landed at each corner quadrant
    corner_count: dict = {}
    for r in range(rows):
        for c in range(cols):
            if idx >= n:
                break
            x = round((c - (cols - 1) / 2.0) * QUBIT_PITCH, 4)
            y = round(((rows - 1) / 2.0 - r) * QUBIT_PITCH, 4)
            sx = 1.0 if x >= 0 else -1.0
            sy = 1.0 if y >= 0 else -1.0
            # Quadrant key (to count qubits per corner)
            qk = (int(sx), int(sy))
            count = corner_count.get(qk, 0)
            corner_count[qk] = count + 1
            # Spread LPs horizontally within the same corner quadrant (0.6 mm gap)
            lp_x = round(sx * lp + (-sx * count * 0.6), 4)
            lp_y = round(sy * lp, 4)
            # LP orientation: face inward toward chip centre
            ang  = math.degrees(math.atan2(-sy, -sx)) % 360
            layout[f"Q{idx + 1}"] = {
                "pos":    (x, y), "row": r, "col": c,
                "lp_pos": (lp_x, lp_y), "lp_ori": str(round(ang)),
                "ro_w":   int(sx), "ro_h": int(sy),
                "asym":   f"{'+' if idx % 2 == 0 else '-'}{100 + idx * 20}um",
            }
            idx += 1
    return layout


def build_metal_chip(n, topology, scale, freq_plan, placement) -> Tuple[Any, MetalBuildLog]:
    from qiskit_metal import Dict
    from qiskit_metal.designs import DesignPlanar
    log = MetalBuildLog()

    design = DesignPlanar()
    design.overwrite_enabled = True
    design.variables["cpw_width"] = "10 um"
    design.variables["cpw_gap"]   = "6 um"
    log.ok("DesignPlanar")

    layout = _grid_layout(n)
    cols   = max(2, math.ceil(math.sqrt(n)))
    rows   = math.ceil(n / cols)

    # ── 1. TransmonPockets ───────────────────────────────────────────────────
    try:
        from qiskit_metal.qlibrary.qubits.transmon_pocket import TransmonPocket
        for qname, info in layout.items():
            x, y   = info["pos"]
            ro_w   = info["ro_w"]
            ro_h   = info["ro_h"]
            TransmonPocket(design, qname,
                options=Dict(
                    pos_x=f"{x}mm", pos_y=f"{y}mm", orientation="0",
                    pad_width="455um", pocket_width="650um", pocket_height="650um",
                    connection_pads=Dict(
                        readout=dict(loc_W=ro_w,  loc_H=ro_h,
                                     pad_width="120um",pad_height="30um",cpw_extend="0um"),
                        bus_r  =dict(loc_W=+1, loc_H=-ro_h,
                                     pad_width="150um",pad_height="30um",cpw_extend="0um"),
                        bus_l  =dict(loc_W=-1, loc_H=-ro_h,
                                     pad_width="150um",pad_height="30um",cpw_extend="0um"),
                        bus_t  =dict(loc_W=-ro_w, loc_H=+1,
                                     pad_width="150um",pad_height="30um",cpw_extend="0um"),
                        bus_b  =dict(loc_W=-ro_w, loc_H=-1,
                                     pad_width="150um",pad_height="30um",cpw_extend="0um"),
                    ),
                ))
        log.ok("TransmonPocket", f"{n} qubits", n)
    except Exception as e:
        log.error("TransmonPocket", str(e))

    # ── 2. Per-Qubit LaunchpadWirebonds (one per qubit, no pin sharing) ──────
    lp_map: dict = {}
    try:
        from qiskit_metal.qlibrary.terminations.launchpad_wb import LaunchpadWirebond
        for qname, info in layout.items():
            lp_x, lp_y = info["lp_pos"]
            lp_name = f"LP_{qname}"
            LaunchpadWirebond(design, lp_name,
                options=dict(pos_x=f"{lp_x}mm", pos_y=f"{lp_y}mm",
                             orientation=info["lp_ori"], lead_length="30um"))
            lp_map[qname] = lp_name
        log.ok("LaunchpadWirebond", f"{len(lp_map)} unique launchpads (1 per qubit)")
    except Exception as e:
        log.error("LaunchpadWirebond", str(e))

    # ── 3. Readout resonators: qubit.readout → its own LP.tie ────────────────
    res_ok = 0
    try:
        from qiskit_metal.qlibrary.tlines.meandered import RouteMeander
        ASYMS = ["+120um","-120um","+100um","-100um","+140um","-140um","+80um","-80um"]
        for i,(qname,info) in enumerate(layout.items()):
            lp_name = lp_map.get(qname)
            res_spec = next((r for r in freq_plan.resonators if r.qubit==qname), None)
            if not lp_name or not res_spec:
                continue
            try:
                RouteMeander(design, res_spec.name,
                    options=Dict(
                        fillet="49um", trace_width="10um", trace_gap="6um",
                        lead=Dict(start_straight="0.1mm", end_straight="0.1mm"),
                        meander=Dict(asymmetry=ASYMS[i%len(ASYMS)],
                                     lead_direction_inverted="true"),
                        pin_inputs=Dict(
                            start_pin=Dict(component=qname,   pin="readout"),
                            end_pin  =Dict(component=lp_name, pin="tie"),
                        ),
                        total_length=f"{res_spec.length_mm:.4f}mm",
                    ))
                res_ok += 1
            except Exception as sub:
                log.warn(f"Resonator {res_spec.name}", str(sub))
        log.ok("Resonators",
               f"{res_ok}/{len(freq_plan.resonators)} — "
               f"{', '.join(f'{r.length_mm:.2f}mm' for r in freq_plan.resonators)}",
               res_ok)
    except Exception as e:
        log.error("RouteMeander (resonators)", str(e))

    # ── 4. Coupling buses (horizontal + vertical neighbours) ─────────────────
    bus_ok = 0
    BUS_ASYMS = ["+60um","-60um","+80um","-80um"]
    try:
        from qiskit_metal.qlibrary.tlines.meandered import RouteMeander
        for qname, info in layout.items():
            r, c = info["row"], info["col"]
            # Horizontal → right neighbour
            rn = f"Q{r*cols+c+2}"
            if c+1 < cols and rn in layout:
                bname = f"bus_{qname}_{rn}"
                if bname not in design.components:
                    try:
                        RouteMeander(design, bname,
                            options=Dict(
                                fillet="49um", trace_width="10um", trace_gap="6um",
                                lead=Dict(start_straight="0.05mm",end_straight="0.05mm"),
                                meander=Dict(asymmetry=BUS_ASYMS[bus_ok%len(BUS_ASYMS)],
                                             lead_direction_inverted="false"),
                                pin_inputs=Dict(
                                    start_pin=Dict(component=qname, pin="bus_r"),
                                    end_pin  =Dict(component=rn,    pin="bus_l"),
                                ),
                                total_length=f"{BUS_LENGTH}mm",
                            ))
                        bus_ok += 1
                    except Exception as sub:
                        log.warn(f"HBus {qname}-{rn}", str(sub))
            # Vertical → bottom neighbour
            bn = f"Q{(r+1)*cols+c+1}"
            if r+1 < rows and bn in layout:
                bname = f"bus_{qname}_{bn}"
                if bname not in design.components:
                    try:
                        RouteMeander(design, bname,
                            options=Dict(
                                fillet="49um", trace_width="10um", trace_gap="6um",
                                lead=Dict(start_straight="0.05mm",end_straight="0.05mm"),
                                meander=Dict(asymmetry=BUS_ASYMS[bus_ok%len(BUS_ASYMS)],
                                             lead_direction_inverted="false"),
                                pin_inputs=Dict(
                                    start_pin=Dict(component=qname, pin="bus_b"),
                                    end_pin  =Dict(component=bn,    pin="bus_t"),
                                ),
                                total_length=f"{BUS_LENGTH}mm",
                            ))
                        bus_ok += 1
                    except Exception as sub:
                        log.warn(f"VBus {qname}-{bn}", str(sub))
        log.ok("Coupling buses", f"{bus_ok} placed", bus_ok)
    except Exception as e:
        log.warn("Coupling buses", str(e))

    # ── 5. Rebuild ───────────────────────────────────────────────────────────
    try:
        design.rebuild()
        log.ok("rebuild()", f"{len(design.components)} components", len(design.components))
    except Exception as e:
        log.error("rebuild()", str(e))

    return design, log


def render_metal_design(design, dpi: int = 200, title: str = "") -> str:
    """SEM-style render: dark ground plane, bright metal traces."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    BG = "#050a18"; METAL = "#c8e8ff"; EDGE = "#80c0ff"; FILL = "#0a1e3a"

    fig = None
    try:
        import qiskit_metal as qm
        fig = qm.view(design, figsize=(12, 10))
    except Exception:
        pass

    if fig is None:
        fig, ax = plt.subplots(figsize=(12, 10))
        ax.set_facecolor(BG)
        for comp in design.components.values():
            try: comp.qgeometry_plot(ax)
            except Exception: pass
        ax.set_aspect("equal")

    fig.patch.set_facecolor(BG)
    for ax in fig.axes:
        ax.set_facecolor(BG)
        ax.tick_params(colors="#2a5080", labelsize=7)
        for sp in ax.spines.values(): sp.set_color("#0a2040")
        for patch in ax.patches:
            try:
                fc = np.array(patch.get_facecolor())[:3]
                b  = float(np.mean(fc))
                if b > 0.4:    patch.set_facecolor(METAL); patch.set_edgecolor(EDGE)
                elif b > 0.15: patch.set_facecolor(FILL);  patch.set_edgecolor(EDGE)
                else:          patch.set_facecolor(BG);    patch.set_edgecolor("#0a2040")
                patch.set_linewidth(0.8); patch.set_alpha(0.95)
            except Exception: pass
        for coll in ax.collections:
            try:
                coll.set_edgecolor(EDGE); coll.set_facecolor(FILL)
                coll.set_alpha(0.9);      coll.set_linewidth(0.8)
            except Exception: pass

    if fig.axes:
        ax0 = fig.axes[0]
        if title: ax0.set_title(title, color="#60b0f0", fontsize=10, pad=6)
        ax0.set_xlabel("x (mm)", color="#2a5080", fontsize=8)
        ax0.set_ylabel("y (mm)", color="#2a5080", fontsize=8)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")
