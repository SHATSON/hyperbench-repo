#!/usr/bin/env python3
"""
make_architecture_figure.py -- Generate Figure 1, the HYPERBENCH pipeline diagram.

The diagram is drawn programmatically rather than stored as a hand-edited binary
so that it stays part of the reproducible artifact: re-running this script
regenerates the exact figure embedded in the manuscript.

Outputs (into figures/):
    architecture.png   300 dpi raster, embedded in the .docx
    architecture.pdf   vector, for LaTeX or print submission
    architecture.svg   vector, for the web

Usage:
    python figures/make_architecture_figure.py
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# --- palette (chosen to remain legible in greyscale print) -----------------
NAVY = "#1F4E79"
INK = "#12263A"
STAGE_FILL = "#EDF3F9"
STAGE_EDGE = "#1F4E79"
IO_FILL = "#F4F4F2"
IO_EDGE = "#6B7280"
BRANCH_FILL = "#F7FAFC"
ARROW = "#37474F"

HERE = os.path.dirname(os.path.abspath(__file__))


def box(ax, x, y, w, h, *, fill, edge, lw=1.4, radius=0.9, z=2):
    """Rounded rectangle anchored at its centre."""
    patch = FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        linewidth=lw, facecolor=fill, edgecolor=edge, zorder=z,
    )
    ax.add_patch(patch)
    return patch


def arrow(ax, x1, y1, x2, y2, *, lw=1.6, z=3):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>", mutation_scale=14,
        linewidth=lw, color=ARROW, zorder=z,
        shrinkA=0, shrinkB=0,
    ))


def line(ax, x1, y1, x2, y2, *, lw=1.6, z=3):
    ax.plot([x1, x2], [y1, y2], color=ARROW, linewidth=lw, zorder=z,
            solid_capstyle="round")


def label(ax, x, y, text, *, size=9.5, weight="normal", color=INK,
          ha="center", va="center", style="normal", family="DejaVu Sans"):
    ax.text(x, y, text, fontsize=size, fontweight=weight, color=color,
            ha=ha, va=va, style=style, family=family, zorder=4)


def build():
    fig, ax = plt.subplots(figsize=(7.4, 9.3))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    CX = 50.0

    # ---------------- INPUT --------------------------------------------
    box(ax, CX, 93.4, 62, 11.2, fill=IO_FILL, edge=IO_EDGE, lw=1.2)
    label(ax, CX, 97.2, "INPUT", size=8.5, weight="bold", color="#6B7280")
    label(ax, CX, 93.8, "Metric specification", size=10.5, weight="bold")
    label(ax, CX, 90.5, "b(r), Φ(r)   or   ADM lapse + shift", size=9.5)

    arrow(ax, CX, 87.8, CX, 84.2)
    label(ax, CX + 2.0, 86.0, "g$_{ab}$  (symbolic)", size=8.8,
          color=ARROW, ha="left")

    # ---------------- STAGE 1 ------------------------------------------
    box(ax, CX, 76.0, 68, 15.4, fill=STAGE_FILL, edge=STAGE_EDGE)
    label(ax, CX, 81.4, "STAGE 1   SYMBOLIC LAYER", size=10.5,
          weight="bold", color=NAVY)
    label(ax, CX, 78.3, "gr_core.py", size=9.0, style="italic",
          color="#5A6B7B", family="DejaVu Sans Mono")
    label(ax, CX, 74.6, "Christoffel  →  Riemann  →  Ricci", size=9.8)
    label(ax, CX, 71.9, "→  Einstein tensor G$_{ab}$", size=9.8)
    label(ax, CX, 69.4, "→  orthonormal frame projection", size=9.8)

    arrow(ax, CX, 68.2, CX, 63.0)
    label(ax, CX + 2.0, 65.6, "ρ,  p$_r$,  p$_t$", size=8.8,
          color=ARROW, ha="left")

    # ---------------- STAGE 2 ------------------------------------------
    box(ax, CX, 55.6, 68, 14.2, fill=STAGE_FILL, edge=STAGE_EDGE)
    label(ax, CX, 60.6, "STAGE 2   AUDIT LAYER", size=10.5,
          weight="bold", color=NAVY)
    label(ax, CX, 57.2, "NEC :   ρ + p$_i$  ≥  0  ?", size=9.8)
    label(ax, CX, 54.4, "WEC :   NEC  and  ρ ≥ 0  ?", size=9.8)
    label(ax, CX, 51.6, "Volume-integral quantifier  I$_V$", size=9.8)

    # ---------------- branch -------------------------------------------
    LX, RX = 26.0, 74.0
    line(ax, CX, 48.5, CX, 45.6)          # stem down
    line(ax, LX, 45.6, RX, 45.6)          # horizontal bus
    arrow(ax, LX, 45.6, LX, 40.6)
    arrow(ax, RX, 45.6, RX, 40.6)

    label(ax, LX - 1.5, 43.1, "I$_V$ + constraints", size=8.8,
          color=ARROW, ha="right")
    label(ax, RX + 1.5, 43.1, "λ  (growth rate)", size=8.8,
          color=ARROW, ha="left")

    # ---------------- STAGE 3A / 3B ------------------------------------
    box(ax, LX, 29.4, 42, 22.4, fill=BRANCH_FILL, edge=STAGE_EDGE, lw=1.3)
    label(ax, LX, 38.0, "STAGE 3A", size=10.0, weight="bold", color=NAVY)
    label(ax, LX, 35.2, "OPTIMISATION", size=10.0, weight="bold", color=NAVY)
    label(ax, LX, 31.6, "SLSQP over shape functions", size=9.2)
    label(ax, LX, 28.2, "minimise  |I$_V$|   subject to", size=9.2)
    label(ax, LX, 25.4, "flare-out,   |b′| ≤ B,", size=9.2)
    label(ax, LX, 22.6, "flat-space matching", size=9.2)

    box(ax, RX, 29.4, 42, 22.4, fill=BRANCH_FILL, edge=STAGE_EDGE, lw=1.3)
    label(ax, RX, 38.0, "STAGE 3B", size=10.0, weight="bold", color=NAVY)
    label(ax, RX, 35.2, "CONTROL", size=10.0, weight="bold", color=NAVY)
    label(ax, RX, 31.6, "linearise  →  LQR", size=9.2)
    label(ax, RX, 28.8, "→  delay margin", size=9.2)
    label(ax, RX, 26.0, "→  DDE simulation", size=9.2)
    label(ax, RX, 22.8, "verdict: causally stabilisable?", size=9.2,
          style="italic", color="#42606F")

    # ---------------- merge to output ----------------------------------
    line(ax, LX, 18.2, LX, 14.2)
    line(ax, RX, 18.2, RX, 14.2)
    line(ax, LX, 14.2, RX, 14.2)
    arrow(ax, CX, 14.2, CX, 9.4)

    box(ax, CX, 5.6, 46, 7.0, fill=IO_FILL, edge=IO_EDGE, lw=1.2)
    label(ax, CX, 7.3, "OUTPUT", size=8.5, weight="bold", color="#6B7280")
    label(ax, CX, 4.4, "results_summary.json", size=10.0,
          family="DejaVu Sans Mono")

    # ---------------- note ---------------------------------------------
    label(ax, CX, 0.6,
          "Stages 3A and 3B are alternative consumers of the audit layer, "
          "not sequential steps.",
          size=8.2, style="italic", color="#5A6B7B")

    fig.tight_layout(pad=0.3)
    for ext in ("png", "pdf", "svg"):
        out = os.path.join(HERE, f"architecture.{ext}")
        fig.savefig(out, dpi=300, bbox_inches="tight",
                    facecolor="white", edgecolor="none")
        print(f"wrote {out}")
    plt.close(fig)


if __name__ == "__main__":
    build()
