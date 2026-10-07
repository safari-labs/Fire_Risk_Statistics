"""scripts/make_result_figures.py

Render the Stage 1 result figures as PNGs next to the notes that cite them.

Figures live in the repo rather than on a URL, so they are versioned with the
results they illustrate and can be opened beside the note while reading it.

HOUSE STYLE, WITH A CORRECTED PALETTE
-------------------------------------
Surfaces and ink match Fire_Risk_FW/src/fire_risk_fw/charts.py, so these sit
alongside the Stage A figures rather than looking like a second project.

The DATA colours do not. The existing house palette fails a colourblind-safety
check on its own surface -- `#2ecc71` sits at OKLCH L 0.746, outside the
0.48-0.67 band for a dark ground, and the blue/green pair comes in at tritan
delta-E 9.4. The three slots used here were validated against the house surface
`#1a1d27` and pass every gate: worst adjacent CVD delta-E 9.4, normal-vision
26.5, all above 3:1 contrast.

Every series is also directly labelled, so identity never rests on hue alone.

    python scripts/make_result_figures.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = _ROOT / "docs" / "results" / "figures"

# Surfaces and ink from the Fire_Risk_FW house style.
FIG_BG, AX_BG = "#0f1117", "#1a1d27"
SPINE, INK, INK_BRIGHT, MUTED = "#333344", "#cccccc", "#eeeeee", "#8b8b9a"
# Validated against #1a1d27 -- see the module docstring.
S1, S2, S3 = "#3987e5", "#d95926", "#199e70"
CRIT, WARN = "#e66767", "#fab219"
DPI = 150


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _axes(ax, title="", xlabel="", ylabel=""):
    ax.set_facecolor(AX_BG)
    for s in ax.spines.values():
        s.set_color(SPINE)
    ax.tick_params(colors=INK, labelsize=9)
    ax.grid(True, color=SPINE, lw=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    if title:
        ax.set_title(title, color=INK_BRIGHT, fontsize=11.5, pad=11, loc="left")
    if xlabel:
        ax.set_xlabel(xlabel, color=INK, fontsize=9.5)
    if ylabel:
        ax.set_ylabel(ylabel, color=INK, fontsize=9.5)


def _save(fig, name):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = FIG_DIR / name
    fig.savefig(out, dpi=DPI, facecolor=FIG_BG, bbox_inches="tight")
    print(f"  wrote {out.relative_to(_ROOT)}")
    return out


# ──────────────────────────────────────────────────────────────────────────
# 1. The scene-type split -- the headline finding
# ──────────────────────────────────────────────────────────────────────────

SCENE = [
    ("unburned", [0.220, 0.299], False),
    ("fire",     [0.790, 0.842], True),
    ("confuser", [0.878, 0.686], True),
]


def fig_scene_split():
    plt = _plt()
    fig, ax = plt.subplots(figsize=(7.2, 2.9), facecolor=FIG_BG)
    _axes(ax, "", xlabel="MAE, derived vs published (lower is better agreement)")
    fig.suptitle("Percent-conifer disagreement, by scene type", color=INK_BRIGHT,
                 fontsize=11.5, x=0.0, ha="left", y=1.17)

    for i, (name, vals, burned) in enumerate(SCENE):
        y = len(SCENE) - 1 - i
        col = S2 if burned else S1
        ax.plot([min(vals), max(vals)], [y, y], color=col, lw=2.4, alpha=0.45,
                solid_capstyle="round", zorder=2)
        ax.scatter(vals, [y] * len(vals), s=76, color=col, zorder=3,
                   edgecolors=AX_BG, linewidths=1.6)
        ax.text(max(vals) + 0.022, y, f"{min(vals):.2f}–{max(vals):.2f}",
                color=INK, fontsize=9, va="center", family="monospace")

    ax.set_yticks(range(len(SCENE)))
    ax.set_yticklabels([s[0] for s in reversed(SCENE)], color=INK_BRIGHT, fontsize=10)
    ax.set_xlim(0, 1.06)
    ax.set_ylim(-0.6, len(SCENE) - 0.4)

    # Legend ABOVE the axes: inside the plot it sat squarely on the confuser
    # row, hiding the two marks that carry the finding.
    from matplotlib.lines import Line2D
    ax.legend(handles=[
        Line2D([], [], marker="o", ls="", color=S1, markersize=7,
               label="stable — both sources see the same stand"),
        Line2D([], [], marker="o", ls="", color=S2, markersize=7,
               label="burned between 2020 and 2024"),
    ], loc="lower left", bbox_to_anchor=(0, 1.02), ncol=2, frameon=False,
        labelcolor=INK, fontsize=8.5)

    fig.text(0.0, -0.07,
             "SCANFI is pinned to its 2020 time step; the published fuel layer is 2024. "
             "Each mark is one patch (n=2 per scene).",
             color=MUTED, fontsize=8.2, ha="left")
    return _save(fig, "scene_split.png")


# ──────────────────────────────────────────────────────────────────────────
# 2. The candidate band pool against the atmospheric windows
# ──────────────────────────────────────────────────────────────────────────

BANDS = [
    ("B1", 443, 20, True), ("B2", 490, 65, False), ("B3", 560, 35, False),
    ("B4", 665, 30, False), ("B5", 705, 15, False), ("B6", 740, 15, False),
    ("B7", 783, 20, False), ("B8", 842, 115, False), ("B8A", 865, 20, False),
    ("B9", 945, 20, True), ("B11", 1610, 90, False),
]
FORBID = [("O$_2$-A", 755, 772), ("O$_2$", 1262, 1288), ("H$_2$O", 1330, 1490)]


def fig_band_pool():
    plt = _plt()
    fig, ax = plt.subplots(figsize=(7.6, 3.1), facecolor=FIG_BG)
    _axes(ax, "Candidate band pool, 400–1750 nm", xlabel="wavelength (nm)")

    for label, lo, hi in FORBID:
        ax.axvspan(lo, hi, color=CRIT, alpha=0.17, zorder=1, lw=0)
        # Above the staggered band labels, which reach ~1.03.
        ax.text((lo + hi) / 2, 1.15, label, color=CRIT, fontsize=8.5,
                ha="center", va="bottom")

    for name, centre, fwhm, atm in BANDS:
        h = 0.52 if atm else 0.92
        col = MUTED if atm else S1
        ax.bar(centre, h, width=max(fwhm, 7), color=col, zorder=3,
               edgecolor=AX_BG, linewidth=0.8)
        # Stagger labels through the crowded red-edge/NIR cluster: at this
        # scale B8 (842) and B8A (865) printed on top of each other as "BB8A".
        stagger = 0.075 if name in ("B5", "B7", "B8A") else 0.0
        ax.text(centre, h + 0.035 + stagger, name, color=INK, fontsize=8,
                ha="center", va="bottom", family="monospace")

    ax.axvline(1750, color=MUTED, ls=":", lw=1.3, zorder=2)
    ax.text(1752, 1.30, "standard-InGaAs cutoff\nB12 (2190 nm) excluded",
            color=MUTED, fontsize=8, ha="right", va="top", linespacing=1.35)

    ax.set_xlim(400, 1800)
    ax.set_ylim(0, 1.46)
    ax.set_yticks([])
    ax.grid(axis="y", visible=False)

    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(facecolor=S1, label="surface band"),
        Patch(facecolor=MUTED, label="atmospheric (not default input)"),
        Patch(facecolor=CRIT, alpha=0.3, label="forbidden region"),
    ], loc="lower left", bbox_to_anchor=(0.30, 0.02), facecolor=AX_BG,
        edgecolor=SPINE, labelcolor=INK, fontsize=8.5, framealpha=0.95)

    fig.text(0.0, -0.06,
             "Bar width is FWHM. B7 (783 nm) sits 1 nm clear of the O2-A region after its upper "
             "edge was corrected from 775 to 772 nm.",
             color=MUTED, fontsize=8.2, ha="left")
    return _save(fig, "band_pool.png")


# ──────────────────────────────────────────────────────────────────────────
# 3. Index feasibility -- read from the live config, never hard-coded
# ──────────────────────────────────────────────────────────────────────────

SETS = ["config_a", "config_b", "config_c",
        "sentinel2_11band_candidates", "sentinel2_msi", "negative_control"]
SHORT = {"config_a": "A", "config_b": "B", "config_c": "C",
         "sentinel2_11band_candidates": "S2 11-band",
         "sentinel2_msi": "S2 MSI", "negative_control": "control"}


def fig_feasibility():
    sys.path.insert(0, str(_ROOT / "src"))
    from safari_bands.config.loader import load_all_band_sets, load_index_catalogue
    from safari_bands.indices import resolve_index

    cat, band_sets = load_index_catalogue(), load_all_band_sets()
    plt = _plt()
    import numpy as np

    names = [i.name for i in cat.indices]
    grid = np.zeros((len(names), len(SETS)))
    for r, idx in enumerate(cat.indices):
        for c, key in enumerate(SETS):
            res = resolve_index(idx, band_sets[key])
            grid[r, c] = 1.0 if res.feasible else (0.5 if res.hyperspectral_only else 0.0)

    fig, ax = plt.subplots(figsize=(6.4, 4.6), facecolor=FIG_BG)
    _axes(ax, "Which index each band set can form")
    ax.grid(False)

    from matplotlib.colors import ListedColormap
    ax.imshow(grid, cmap=ListedColormap([AX_BG, "#2a2f3d", S1]),
              vmin=0, vmax=1, aspect="auto")

    for r in range(len(names)):
        for c in range(len(SETS)):
            v = grid[r, c]
            txt, col = ("yes", "#ffffff") if v == 1 else \
                       ("n/a", MUTED) if v == 0.5 else ("—", MUTED)
            ax.text(c, r, txt, ha="center", va="center", color=col, fontsize=8.5,
                    family="monospace")

    ax.set_xticks(range(len(SETS)))
    ax.set_xticklabels([SHORT[s] for s in SETS], color=INK_BRIGHT, fontsize=9)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels([f"{n}  ({i.target})" for n, i in zip(names, cat.indices)],
                       color=INK, fontsize=8.5, family="monospace")
    ax.set_xticks([x - 0.5 for x in range(1, len(SETS))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(names))], minor=True)
    ax.grid(which="minor", color=FIG_BG, lw=2)
    ax.tick_params(which="minor", length=0)

    fig.text(0.0, -0.04,
             "Configurations A and B can form no curing index (T2) at any SNR: NDTI needs a "
             "SWIR1/SWIR2 contrast they do not carry.",
             color=MUTED, fontsize=8.2, ha="left")
    return _save(fig, "index_feasibility.png")


# ──────────────────────────────────────────────────────────────────────────
# 4. Cut-point calibration
# ──────────────────────────────────────────────────────────────────────────

def fig_cut_points():
    plt = _plt()
    fig, ax = plt.subplots(figsize=(7.0, 2.3), facecolor=FIG_BG)
    _axes(ax, "Percent-conifer cut points, judgement vs fitted",
          xlabel="percent conifer")

    rows = [("judgement", 0.20, 0.80, MUTED, None),
            ("fitted", 0.10, 0.45, S1, "67.3% three-class accuracy")]
    for i, (lab, lo, hi, col, acc) in enumerate(rows):
        y = len(rows) - 1 - i
        ax.plot([0, 1], [y, y], color=SPINE, lw=7, solid_capstyle="round", zorder=1)
        ax.plot([lo, hi], [y, y], color=col, lw=7, solid_capstyle="round",
                alpha=0.42, zorder=2)
        ax.scatter([lo, hi], [y, y], s=74, color=col, zorder=3,
                   edgecolors=AX_BG, linewidths=1.6)
        for v in (lo, hi):
            ax.text(v, y + 0.22, f"{v:.2f}", color=INK, fontsize=8.5,
                    ha="center", family="monospace")
        if acc:
            ax.text(1.03, y, acc, color=INK, fontsize=8.5, va="center")

    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in reversed(rows)], color=INK_BRIGHT, fontsize=10)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.55, len(rows) - 0.3)
    ax.grid(axis="y", visible=False)

    fig.text(0.0, -0.12,
             "Fitted on 29 distinct unburned sites. The model input is continuous percent conifer, "
             "so no cut point enters the retrieval.",
             color=MUTED, fontsize=8.2, ha="left")
    return _save(fig, "cut_points.png")


def main() -> int:
    print("rendering Stage 1 result figures")
    fig_scene_split()
    fig_band_pool()
    fig_feasibility()
    fig_cut_points()
    print(f"\nall figures -> {FIG_DIR.relative_to(_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
