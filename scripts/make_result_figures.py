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
    from safari_bands.band_names import band_label

    plt = _plt()
    fig, ax = plt.subplots(figsize=(7.6, 4.0), facecolor=FIG_BG)
    _axes(ax, "Candidate band pool, 400–1750 nm", xlabel="wavelength (nm)")

    for label, lo, hi in FORBID:
        ax.axvspan(lo, hi, color=CRIT, alpha=0.17, zorder=1, lw=0)
        # Above the vertical band labels, which reach ~1.65.
        ax.text((lo + hi) / 2, 1.78, label, color=CRIT, fontsize=8.5,
                ha="center", va="bottom")

    for name, centre, fwhm, atm in BANDS:
        h = 0.52 if atm else 0.92
        col = MUTED if atm else S1
        ax.bar(centre, h, width=max(fwhm, 7), color=col, zorder=3,
               edgecolor=AX_BG, linewidth=0.8)
        # Vertical: "B8 (NIR)" and "B8A (Narrow NIR)" sit 23 nm apart, and
        # no horizontal label fits the red-edge/NIR cluster at this scale.
        nudge = {"B8": -8, "B8A": 8}.get(name, 0)
        ax.text(centre + nudge, h + 0.035, band_label(name), color=INK,
                fontsize=7.6, ha="center", va="bottom", rotation=90)

    ax.axvline(1750, color=MUTED, ls=":", lw=1.3, zorder=2)
    ax.text(1745, 1.70, "standard-InGaAs cutoff\nB12 (2190 nm) excluded",
            color=MUTED, fontsize=8, ha="right", va="top", linespacing=1.35)

    ax.set_xlim(400, 1800)
    ax.set_ylim(0, 2.0)
    ax.set_yticks([])
    ax.grid(axis="y", visible=False)

    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(facecolor=S1, label="surface band"),
        Patch(facecolor=MUTED, label="60 m native, bilinear to 20 m"),
        Patch(facecolor=CRIT, alpha=0.3, label="forbidden region"),
    ], loc="lower left", bbox_to_anchor=(0.30, 0.02), facecolor=AX_BG,
        edgecolor=SPINE, labelcolor=INK, fontsize=8.5, framealpha=0.95)

    fig.text(0.0, -0.06,
             "Bar width is FWHM. All eleven are packed and rankable: holding B1/B9 back "
             "would decide their value by assumption. B7 sits 1 nm clear of O2-A after its "
             "upper edge was corrected from 775 to 772 nm.",
             color=MUTED, fontsize=8.2, ha="left")
    return _save(fig, "band_pool.png")


# ──────────────────────────────────────────────────────────────────────────
# 3. Index feasibility -- read from the live config, never hard-coded
# ──────────────────────────────────────────────────────────────────────────

SETS = ["sensor_mantis_vnir6", "sensor_mantis_hs96", "sensor_mantis_swir4",
        "sensor_mantis_ms_plus_swir", "swir4_worldview3",
        "sentinel2_msi", "negative_control"]

# The Mantis modes first, because they are the decision. The configurations
# A/B/C this figure used to show are retired (A-18): C needs extended InGaAs
# at 2190 nm, which no Mantis mode reaches.
#
# Each header names the set AND its spectral content, because "MS" and "HS"
# mean nothing without knowing that HS is NARROWER -- 470-900 against
# 400-1000 -- which is the whole reason the two columns differ.
COLHEAD = {
    "sensor_mantis_vnir6":        ("Mantis MS", "6 bands|400-1000"),
    "sensor_mantis_hs96":         ("Mantis HS", "96 bands|470-900"),
    "sensor_mantis_swir4":        ("Mantis SWIR", "4 bands|1000-1750"),
    "sensor_mantis_ms_plus_swir": ("MS + SWIR", "10 bands|both chains"),
    "swir4_worldview3":           ("WV-3 SWIR", "4 bands|1209-1730"),
    "sentinel2_msi":              ("S2 MSI", "reference|+2190"),
    "negative_control":           ("control", "4 red|bands only"),
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

    fig, ax = plt.subplots(figsize=(9.2, 5.6), facecolor=FIG_BG)
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

    fig.text(0.0, -0.52, chr(10).join([
        "Rows are reference indices, with the retrieval target they serve. Three results read straight off this matrix.",
        "",
        "SWIR ALONE FORMS NOTHING. Every moisture and curing index contrasts a SWIR band against NIR, and NIR is on the VNIR chain. The SWIR mode is not a weaker",
        "configuration than MS -- on its own it cannot form the products it exists for. Same for the WorldView-3 SWIR set, for the same reason.",
        "",
        "HS ADDS NO INDEX OVER MS. Both form NDVI, EVI, VARI and NDRE and nothing else. Index feasibility depends on WHICH wavelengths a set carries, not how many,",
        "and 96 bands between 470 and 900 nm reach no further than 6 do. Whatever HS is worth, it is not extra indices -- it has to come from full-spectrum retrieval.",
        "",
        "MS + SWIR UNLOCKS FOUR: NDMI, MSI, Gao's NDWI and NDSI. That is the index-level answer to whether the second chain earns its place.",
        "NMDI, NDTI and NBR stay out of reach at any SNR -- all need SWIR2 at ~2190 nm, past every Mantis mode. CAI needs three narrow 2.0-2.2 um bands,",
        "so no multispectral set reaches it. The control forms nothing, which is the correct result for four overlapping red bands.",
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
    fig_ecv_feasibility()
    fig_products()
    fig_cut_points()
    fig_pc_regression()
    fig_class_agreement()
    print(f"\nall figures -> {FIG_DIR.relative_to(_ROOT)}")
    return 0


# ──────────────────────────────────────────────────────────────────────────
# Essential Climate Variables, against the same band sets
#
# The mission offers preprocessed imagery on the calibration downlink, and
# ECVs are the candidate secondary product. The question is the same shape as
# index feasibility -- which roles does a set carry -- so it is answered the
# same way, from config/ecv_candidates.yaml.
# ──────────────────────────────────────────────────────────────────────────

def _ecv_grid():
    sys.path.insert(0, str(_ROOT / "src"))
    import yaml
    from safari_bands.config.loader import load_all_band_sets

    band_sets = load_all_band_sets()
    ecv = yaml.safe_load(open(_ROOT / "config/ecv_candidates.yaml",
                              encoding="utf-8"))["variables"]
    plt = _plt()
    import numpy as np

    # 1.0 carried outright, 0.6 core roles present but the set lacks a band
    # the retrieval also leans on, 0.3 out of reach for ANY optical set,
    # 0.0 missing a required role.
    #
    # 0.3 and not 0.5 for the out-of-reach rows: four colours over [0, 1] bin
    # at 0.25/0.5/0.75, so 0.5 fell in the same bin as 0.6 and "needs thermal
    # infrared" rendered in the identical green as "core roles present".
    grid = np.zeros((len(ecv), len(SETS)))
    for r, v in enumerate(ecv):
        req = v.get("requires_roles")
        for c, key in enumerate(SETS):
            if not req:
                grid[r, c] = 0.3          # needs thermal or microwave
                continue
            roles = band_sets[key].roles
            if not set(req) <= roles:
                grid[r, c] = 0.0
            else:
                extra = set(v.get("also_uses") or [])
                grid[r, c] = 1.0 if extra <= roles else 0.6

    return ecv, grid


def fig_ecv_feasibility():
    """ECVs alone, kept for anyone who wants just that panel."""
    plt = _plt()
    ecv, grid = _ecv_grid()
    fig, ax = plt.subplots(figsize=(9.2, 5.2), facecolor=FIG_BG)
    _axes(ax, "Which Essential Climate Variables each sensor combination reaches")
    ax.grid(False)

    from matplotlib.colors import ListedColormap
    ax.imshow(grid, cmap=ListedColormap([AX_BG, "#2a2f3d", "#2f6d52", S1]),
              vmin=0, vmax=1, aspect="auto")

    for r in range(len(ecv)):
        for c in range(len(SETS)):
            v = grid[r, c]
            txt, col = (("yes", "#ffffff") if v == 1.0 else
                        ("core", "#bfe3d0") if v == 0.6 else
                        ("n/a", MUTED) if v == 0.3 else ("—", MUTED))
            ax.text(c, r, txt, ha="center", va="center", color=col,
                    fontsize=8.2, family="monospace")

    ax.set_xticks(range(len(SETS)))
    ax.set_xticklabels([COLHEAD[s][0] for s in SETS], color=INK_BRIGHT,
                       fontsize=9.5)
    for c, key in enumerate(SETS):
        ax.annotate(chr(10).join(COLHEAD[key][1].split("|")),
                    xy=(c, 0), xycoords=("data", "axes fraction"),
                    xytext=(0, -30), textcoords="offset points",
                    ha="center", va="top", color=MUTED, fontsize=7.6,
                    family="monospace", linespacing=1.5, annotation_clip=False)
    ax.set_yticks(range(len(ecv)))
    ax.set_yticklabels([v["name"] for v in ecv], color=INK, fontsize=8.5)
    ax.set_xticks([x - 0.5 for x in range(1, len(SETS))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(ecv))], minor=True)
    ax.grid(which="minor", color=FIG_BG, linewidth=2.0)
    ax.tick_params(which="minor", length=0)

    # Count what each column actually delivers, for the caption.
    got = {k: int((grid[:, c] >= 0.6).sum()) for c, k in enumerate(SETS)}
    ms, hs = got["sensor_mantis_vnir6"], got["sensor_mantis_hs96"]
    sw, both = got["sensor_mantis_swir4"], got["sensor_mantis_ms_plus_swir"]

    fig.text(0.0, -0.46, chr(10).join([
        "yes = every role the retrieval uses.   core = the required roles, "
        "without a band the retrieval also leans on.   n/a = out of reach for "
        "any optical set.",
        "",
        f"MS alone reaches {ms} of {len(ecv)}. SWIR alone reaches {sw} -- every "
        f"ECV here needs a VNIR band, so the SWIR chain contributes nothing "
        f"on its own, exactly as it does for the indices.",
        f"TOGETHER they reach {both}: adding SWIR1 unlocks Land Cover, "
        f"Above-Ground Biomass, Fire Disturbance, Snow Cover, Lakes and "
        f"Surface Albedo.",
        "",
        f"HS reaches {hs}, the same as MS. Its 96 bands add spectral detail "
        f"within 470-900 nm, and every ECV beyond the three vegetation ones "
        f"needs a wavelength outside that window.",
        "",
        "Land Surface Temperature needs thermal infrared and Soil Moisture "
        "needs microwave; neither is reachable in 400-1750 nm at any SNR, and "
        "they are listed so the table is a scoping",
        "exercise rather than a list of successes. Nothing here has been "
        "produced or validated -- see OPEN_QUESTIONS Q22.",
    ]), color=MUTED, fontsize=8.2, ha="left", linespacing=1.5)
    return _save(fig, "ecv_feasibility.png")


# ──────────────────────────────────────────────────────────────────────────
# Indices and ECVs in one frame
#
# They answer the same question of a band set -- which roles does it carry --
# so splitting them across two files made the reader do the join by hand.
# Sharing a column axis makes the comparison the figure is actually for:
# what does each sensor combination deliver, in products.
# ──────────────────────────────────────────────────────────────────────────

def fig_products():
    sys.path.insert(0, str(_ROOT / "src"))
    from safari_bands.config.loader import load_all_band_sets, load_index_catalogue
    from safari_bands.indices import resolve_index
    plt = _plt()
    import numpy as np
    from matplotlib.colors import ListedColormap

    cat, band_sets = load_index_catalogue(), load_all_band_sets()
    idx_names = [i.name for i in cat.indices]
    igrid = np.zeros((len(idx_names), len(SETS)))
    for r, idx in enumerate(cat.indices):
        for c, key in enumerate(SETS):
            res = resolve_index(idx, band_sets[key])
            igrid[r, c] = 1.0 if res.feasible else (0.3 if res.hyperspectral_only else 0.0)
    ecv, egrid = _ecv_grid()

    n_i, n_e = len(idx_names), len(ecv)
    fig, (ax_i, ax_e) = plt.subplots(
        2, 1, figsize=(9.6, 1.4 + 0.42 * (n_i + n_e)), facecolor=FIG_BG,
        gridspec_kw={"height_ratios": [n_i, n_e], "hspace": 0.08})
    fig.suptitle("What each sensor combination can deliver",
                 color=INK_BRIGHT, fontsize=12.5, x=0.0, ha="left", y=0.995)

    cmap = ListedColormap([AX_BG, "#2a2f3d", "#2f6d52", S1])
    for ax, grid, labels, title in (
            (ax_i, igrid, [f"{n}  ({i.target})" for n, i in zip(idx_names, cat.indices)],
             "Reference indices"),
            (ax_e, egrid, [v["name"] for v in ecv],
             "Essential Climate Variables")):
        ax.set_facecolor(AX_BG)
        ax.imshow(grid, cmap=cmap, vmin=0, vmax=1, aspect="auto")
        ax.set_title(title, color=INK_BRIGHT, fontsize=10, loc="left", pad=6)
        for r in range(grid.shape[0]):
            for c in range(len(SETS)):
                v = grid[r, c]
                txt, col = (("yes", "#ffffff") if v == 1.0 else
                            ("core", "#bfe3d0") if v == 0.6 else
                            ("n/a", MUTED) if v == 0.3 else ("—", MUTED))
                ax.text(c, r, txt, ha="center", va="center", color=col,
                        fontsize=8.2, family="monospace")
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, color=INK, fontsize=8.3, family="monospace")
        ax.set_xticks([x - 0.5 for x in range(1, len(SETS))], minor=True)
        ax.set_yticks([y - 0.5 for y in range(1, grid.shape[0])], minor=True)
        ax.grid(which="minor", color=FIG_BG, linewidth=2.0)
        ax.grid(which="major", visible=False)
        ax.tick_params(which="minor", length=0)
        for side in ("top", "right", "left", "bottom"):
            ax.spines[side].set_visible(False)

    ax_i.set_xticks([])
    ax_e.set_xticks(range(len(SETS)))
    ax_e.set_xticklabels([COLHEAD[s][0] for s in SETS], color=INK_BRIGHT,
                         fontsize=9.5)
    for c, key in enumerate(SETS):
        ax_e.annotate(chr(10).join(COLHEAD[key][1].split("|")),
                      xy=(c, 0), xycoords=("data", "axes fraction"),
                      xytext=(0, -30), textcoords="offset points",
                      ha="center", va="top", color=MUTED, fontsize=7.6,
                      family="monospace", linespacing=1.5,
                      annotation_clip=False)

    n_idx = {k: int((igrid[:, c] >= 0.6).sum()) for c, k in enumerate(SETS)}
    n_ecv = {k: int((egrid[:, c] >= 0.6).sum()) for c, k in enumerate(SETS)}
    row = lambda d: "   ".join(
        f"{COLHEAD[k][0]} {d[k]}" for k in
        ("sensor_mantis_vnir6", "sensor_mantis_hs96",
         "sensor_mantis_swir4", "sensor_mantis_ms_plus_swir"))

    fig.text(0.0, -0.135, chr(10).join([
        f"indices   {row(n_idx)}",
        f"ECVs      {row(n_ecv)}",
        "",
        "SWIR ALONE DELIVERS NOTHING, in either panel. Every moisture index "
        "and every ECV here needs a VNIR band, and NIR is on the other chain.",
        "HS DELIVERS NO MORE THAN MS. Its 96 bands add detail inside 470-900 "
        "nm; everything the extra products need lies outside that window.",
        "MS + SWIR is where the gain is: four more indices and six more ECVs "
        "-- Land Cover, Above-Ground Biomass, Fire Disturbance, Snow Cover, "
        "Lakes, Surface Albedo.",
        "",
        "yes = every role used.   core = required roles, missing one the "
        "retrieval also leans on.   n/a = out of reach for any optical set "
        "(CAI needs 2.0-2.2 um; LST thermal; soil moisture microwave).",
        "Feasibility from band placement only. Nothing here has been produced "
        "or validated -- see OPEN_QUESTIONS Q22.",
    ]), color=MUTED, fontsize=8.2, ha="left", linespacing=1.5)
    return _save(fig, "index_and_ecv_feasibility.png")


if __name__ == "__main__":
    sys.exit(main())


