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
#: Written by Fire_Risk_Model/scripts/python/fuel_type_agreement.py.
AGREE_DIR = _ROOT.parent / "Fire_Risk_Model" / "output" / "fuel_agreement"

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

# "A", "B", "C" mean nothing without the bands behind them, and the whole
# point of the figure is which SWIR content a configuration carries. Each
# column header therefore names the set AND its SWIR bands, since that is the
# only axis the three SAFARI configurations differ on.
COLHEAD = {
    "config_a":                    ("Config A", "VNIR|+1610"),
    "config_b":                    ("Config B", "VNIR|+1240|+1610"),
    "config_c":                    ("Config C", "VNIR|+1610|+2190"),
    "sentinel2_11band_candidates": ("S2 pool", "11 bands|400-1750"),
    "sentinel2_msi":               ("S2 MSI", "full|+2190"),
    "negative_control":            ("control", "4 red|bands only"),
}


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

    fig, ax = plt.subplots(figsize=(7.0, 5.0), facecolor=FIG_BG)
    _axes(ax, "Which index each band set can form, from band placement alone")
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
    ax.set_xticklabels([COLHEAD[s][0] for s in SETS], color=INK_BRIGHT, fontsize=9.5)
    # Band content BELOW the tick labels. Drawn in data-x / axes-y with a
    # pixel offset: in data coordinates it landed on top of the tick label.
    for c, key in enumerate(SETS):
        ax.annotate(chr(10).join(COLHEAD[key][1].split("|")),
                    xy=(c, 0), xycoords=("data", "axes fraction"),
                    xytext=(0, -30), textcoords="offset points",
                    ha="center", va="top", color=MUTED, fontsize=7.6,
                    family="monospace", linespacing=1.5, annotation_clip=False)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels([f"{n}  ({i.target})" for n, i in zip(names, cat.indices)],
                       color=INK, fontsize=8.5, family="monospace")
    ax.set_xticks([x - 0.5 for x in range(1, len(SETS))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(names))], minor=True)
    ax.grid(which="minor", color=FIG_BG, lw=2)
    ax.tick_params(which="minor", length=0)

    fig.text(0.0, -0.175, chr(10).join([
        "Rows are reference indices, with the retrieval target they serve. "
        "Configurations A and B can form no curing index (T2) at any SNR:",
        "NDTI needs a SWIR1/SWIR2 contrast they do not carry. The control is a "
        "deliberately bad set - four overlapping red bands, no water",
        "sensitivity - and forming nothing is the correct result for it. "
        "CAI needs three narrow 2.0-2.2 um bands, so no multispectral set reaches it.",
    ]), color=MUTED, fontsize=8.2, ha="left", linespacing=1.5)
    return _save(fig, "index_feasibility.png")


# ──────────────────────────────────────────────────────────────────────────
# 4. Cut-point calibration
# ──────────────────────────────────────────────────────────────────────────

def fig_cut_points():
    """Why two thresholds exist at all, and where they land.

    The derivation produces a CONTINUOUS percent conifer; the published layer
    reports DISCRETE classes. Comparing them means cutting the continuum into
    three classes, which needs two boundaries -- and those boundaries were a
    guess until they were fitted.
    """
    plt = _plt()
    fig, ax = plt.subplots(figsize=(7.6, 3.2), facecolor=FIG_BG)
    _axes(ax, "Turning continuous percent conifer into the layer's three classes",
          xlabel="percent conifer  (0 = all broadleaf,  1 = all conifer)")

    ZONE = [("deciduous", S2), ("mixedwood", WARN), ("conifer", S3)]
    rows = [
        ("judgement", 0.20, 0.80, "guessed when the derivation was written"),
        ("fitted",    0.10, 0.45, "best match to the layer — 67.3% correct"),
    ]

    for i, (lab, lo, hi, note) in enumerate(rows):
        y = len(rows) - 1 - i
        for (zname, zcol), (a, b) in zip(ZONE, [(0, lo), (lo, hi), (hi, 1)]):
            ax.barh(y, b - a, left=a, height=0.42, color=zcol, alpha=0.78,
                    edgecolor=AX_BG, linewidth=2, zorder=2)
            if b - a > 0.13:                       # only label a zone with room
                ax.text((a + b) / 2, y, zname, ha="center", va="center",
                        color="#0f1117", fontsize=8.8, fontweight="bold", zorder=3)
        for v in (lo, hi):
            ax.plot([v, v], [y - 0.30, y + 0.30], color=INK_BRIGHT, lw=1.6, zorder=4)
            ax.text(v, y + 0.345, f"{v:.2f}", ha="center", va="bottom",
                    color=INK_BRIGHT, fontsize=9, family="monospace", zorder=4)
        ax.text(1.015, y, note, va="center", color=INK, fontsize=8.4)

    # Both boundaries moved LEFT, which is the finding: the derivation reads
    # systematically more conifer than the layer, so the cuts must drop to
    # compensate.
    for a, b in [(0.20, 0.10), (0.80, 0.45)]:
        ax.annotate("", xy=(b, 0.42), xytext=(a, 0.58),
                    arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.3,
                                    shrinkA=0, shrinkB=0))
    ax.text(0.625, 0.655, "both cuts move left", color=MUTED, fontsize=8.2,
            ha="center", va="bottom", style="italic")

    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in reversed(rows)], color=INK_BRIGHT, fontsize=10.5)
    ax.set_xlim(0, 1.0)
    ax.set_ylim(-0.52, len(rows) - 0.30)
    ax.grid(axis="y", visible=False)

    fig.text(0.0, -0.42, chr(10).join([
        "The derivation outputs a continuous percent conifer; the published CFFDRS layer "
        "reports discrete classes. Comparing the two means cutting",
        "the continuum into deciduous / mixedwood / conifer, which takes two boundaries. "
        "Those were a judgement call until they were fitted on 29",
        "distinct unburned sites. Both moved sharply left, because the derivation reads "
        "more conifer than the layer (bias +0.098) and the cuts",
        "have to drop to compensate. Even at the best pair, only 67.3% of pixels land in "
        "the layer's class.",
        "",
        "This affects REPORTING only. The model consumes continuous percent conifer, so "
        "neither threshold enters the retrieval.",
    ]), color=MUTED, fontsize=8.2, ha="left", linespacing=1.55)
    return _save(fig, "cut_points.png")


def fig_pc_regression():
    """Where the derivation puts its mass at each published level.

    NOT a scatter or a 2D histogram. The published percent conifer is
    DISCRETE -- the layer encodes it in its class codes, so it only ever takes
    six values (0, 0.15, 0.25, 0.50, 0.75, 1.0). Plotting a continuous
    derived value against it produces six vertical stripes and hides the one
    thing worth seeing: at each published level, where does the derivation
    actually sit?
    """
    import numpy as np
    src = AGREE_DIR / "pairs.npz"
    if not src.exists():
        print(f"  skip pc_regression: {src} not found")
        return None
    z = np.load(src)
    derived, published = z["derived_pc"], z["published_pc"]

    levels = sorted(set(np.round(published, 2).tolist()))
    groups = [derived[np.isclose(published, lv, atol=1e-3)] for lv in levels]
    keep = [(lv, g) for lv, g in zip(levels, groups) if g.size >= 50]

    plt = _plt()
    fig, ax = plt.subplots(figsize=(7.0, 4.0), facecolor=FIG_BG)
    _axes(ax, "Derived percent conifer at each published level",
          xlabel="published percent conifer (the layer's own six values)",
          ylabel="derived (from SCANFI)")

    pos = range(len(keep))
    bp = ax.boxplot([g for _, g in keep], positions=list(pos), widths=0.55,
                    patch_artist=True, showfliers=False, zorder=3)
    for box in bp["boxes"]:
        box.set(facecolor=S1, alpha=0.75, edgecolor=INK_BRIGHT, linewidth=1.1)
    for part in ("whiskers", "caps"):
        for ln in bp[part]:
            ln.set(color=INK, linewidth=1.1)
    for med in bp["medians"]:
        med.set(color=INK_BRIGHT, linewidth=1.8)

    # Where each box SHOULD sit if the two agreed.
    ax.plot(list(pos), [lv for lv, _ in keep], marker="D", ms=7, ls="--",
            lw=1.4, color=S2, zorder=4, label="published value (perfect agreement)")

    ax.set_xticks(list(pos))
    ax.set_xticklabels([f"{lv:.2f}" for lv, _ in keep], color=INK, fontsize=9,
                       family="monospace")
    for i, (lv, g) in enumerate(keep):
        ax.text(i, 1.04, f"{g.size/1000:.0f}k", ha="center", color=MUTED,
                fontsize=7.6, family="monospace")
    ax.set_ylim(-0.03, 1.10)
    ax.legend(loc="lower right", facecolor=AX_BG, edgecolor=SPINE,
              labelcolor=INK, fontsize=8.5, framealpha=0.95)

    fig.text(0.0, -0.20, chr(10).join([
        "29 unburned sites, 200k sampled fuel pixels; counts above each box. Boxes are "
        "quartiles, whiskers 1.5 IQR, outliers hidden.",
        "Every box sits ABOVE its diamond except at the top of the range: the derivation "
        "reads more conifer than the layer at",
        "every level, which is the +0.098 bias. The gap is widest where the layer says "
        "pure deciduous, matching the 0.4%",
        "categorical agreement on D-1/D-2.",
    ]), color=MUTED, fontsize=8.2, ha="left", linespacing=1.5)
    return _save(fig, "pc_regression.png")


def fig_class_agreement():
    """Where the categorical agreement actually fails."""
    import json
    src = AGREE_DIR / "agreement.json"
    if not src.exists():
        print(f"  skip class_agreement: {src} not found")
        return None
    per = json.load(open(src))["pooled"]["per_class"]
    rows = sorted(((k, v[0], v[1]) for k, v in per.items()),
                  key=lambda r: -r[2])

    plt = _plt()
    fig, ax = plt.subplots(figsize=(7.0, 3.8), facecolor=FIG_BG)
    _axes(ax, "Agreement by published class",
          xlabel="share of that class the derivation also calls that class")

    UNREACHABLE = {"C-5", "C-7"}       # SCANFI folds white/red pine into OtherCon
    labels, ys = [], []
    for i, (name, hit, tot) in enumerate(rows):
        y = len(rows) - 1 - i
        frac = hit / tot if tot else 0.0
        col = MUTED if name in UNREACHABLE else (S3 if frac >= 0.5 else
              (WARN if frac >= 0.15 else S2))
        ax.barh(y, frac, height=0.62, color=col, zorder=2)
        ax.text(frac + 0.012, y, f"{frac*100:4.1f}%   {tot/1e6:.1f}M px",
                va="center", color=INK, fontsize=8.3, family="monospace")
        labels.append(name + ("  *" if name in UNREACHABLE else ""))
        ys.append(y)

    ax.set_yticks(ys); ax.set_yticklabels(labels, color=INK_BRIGHT, fontsize=9,
                                          family="monospace")
    ax.set_xlim(0, 1.0); ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.grid(axis="y", visible=False)

    fig.text(0.0, -0.27, chr(10).join([
        "Pooled over 29 unburned sites; 27.6% overall. The derivation agrees on closed "
        "boreal spruce (C-2, 78%) and fails almost",
        "completely on deciduous (D-1/D-2, 0.4% of 6.6M pixels) - the same story as the "
        "+0.098 conifer bias, seen categorically.",
        "",
        "*  C-5 and C-7 are UNREACHABLE by construction: SCANFI folds white and red pine "
        "into OtherCon, so the derivation",
        "   can never emit them. 0% is the expected result, not a failure.",
    ]), color=MUTED, fontsize=8.2, ha="left", linespacing=1.5)
    return _save(fig, "class_agreement.png")


def main() -> int:
    print("rendering Stage 1 result figures")
    fig_scene_split()
    fig_band_pool()
    fig_feasibility()
    fig_cut_points()
    fig_pc_regression()
    fig_class_agreement()
    print(f"\nall figures -> {FIG_DIR.relative_to(_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
