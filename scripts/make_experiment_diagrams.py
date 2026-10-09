"""scripts/make_experiment_diagrams.py

Diagrams of the experiments Stage 1 plans to run.

Design documents rather than results: what will be varied, what is held fixed,
how many training runs that costs, and what blocks each arm. Rendered as PNGs
in the repo so they can be opened beside the plan.

Boxes size themselves to their content. The first version used fixed heights
and the text ran out through the bottom edge of every box, which is the kind
of thing that only shows up when you look at the output.

Surfaces and ink match Fire_Risk_FW's charts.py; accents are the validated
slots used by make_result_figures.py.

    python scripts/make_experiment_diagrams.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = _ROOT / "docs" / "results" / "figures"

FIG_BG, AX_BG = "#0f1117", "#1a1d27"
SPINE, INK, INK_BRIGHT, MUTED = "#333344", "#cccccc", "#eeeeee", "#8b8b9a"
S1, S3, WARN, CRIT = "#3987e5", "#199e70", "#fab219", "#e66767"
DPI = 150

PAD_TOP, LINE_H, TITLE_H = 3.0, 3.9, 5.2


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _canvas(w, h):
    plt = _plt()
    fig, ax = plt.subplots(figsize=(w, h), facecolor=FIG_BG)
    ax.set_facecolor(FIG_BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


def box_h(lines, has_title=True):
    """Height a box needs for its content."""
    return PAD_TOP * 2 + (TITLE_H if has_title else 0) + len(lines) * LINE_H


def box(ax, x, top, w, title, lines=(), edge=S1, fs=8.0, tfs=9.4, mono=True):
    """Draw a box whose TOP edge is at `top`, sized to its content.

    Returns (bottom_y, height) so the caller can chain boxes without guessing.
    """
    from matplotlib.patches import FancyBboxPatch
    h = box_h(lines, bool(title))
    y = top - h
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0,rounding_size=1.4",
                                linewidth=1.5, edgecolor=edge, facecolor=AX_BG,
                                zorder=2))
    cursor = top - PAD_TOP
    if title:
        ax.text(x + w / 2, cursor, title, ha="center", va="top",
                color=INK_BRIGHT, fontsize=tfs, fontweight="bold", zorder=3)
        cursor -= TITLE_H
    for ln in lines:
        ax.text(x + w / 2, cursor, ln, ha="center", va="top", color=INK,
                fontsize=fs, zorder=3,
                family="monospace" if mono else None)
        cursor -= LINE_H
    return y, h


def arrow(ax, x1, y1, x2, y2, col=MUTED, lw=1.5):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=col, lw=lw,
                                shrinkA=3, shrinkB=3), zorder=1)


def heading(ax, text, sub=""):
    ax.text(0, 99, text, ha="left", va="top", color=INK_BRIGHT, fontsize=13,
            fontweight="bold")
    if sub:
        ax.text(0, 93, sub, ha="left", va="top", color=MUTED, fontsize=9.2)


def caption(fig, lines):
    fig.text(0.0, -0.015, chr(10).join(lines), color=MUTED, fontsize=8.4,
             ha="left", va="top", linespacing=1.55)


def _save(fig, name):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = FIG_DIR / name
    fig.savefig(out, dpi=DPI, facecolor=FIG_BG, bbox_inches="tight")
    print(f"  wrote {out.relative_to(_ROOT)}")


# ──────────────────────────────────────────────────────────────────────────
# 1. What varies
# ──────────────────────────────────────────────────────────────────────────

def diagram_axes():
    fig, ax = _canvas(10.0, 5.6)
    heading(ax, "What the Stage 1 experiments vary",
            "Two axes are the question. Three are controls that keep the answer honest.")

    # Question axes: two wide boxes.
    box(ax, 0, 85, 48, "BANDS", [
        "11 candidates, 400-1750 nm",
        "VNIR: best 6 of 10",
        "SWIR: best 4 of 1 (needs WV-3)",
    ], edge=S1, fs=8.6)
    box(ax, 52, 85, 48, "ARCHITECTURE", [
        "9 presets, 15k to 87M params",
        "tier2 / tier3 / tier4 / tier5",
        "all accept any band count",
    ], edge=S1, fs=8.6)
    ax.text(24, 87.5, "the question", ha="center", color=S1, fontsize=8.4,
            style="italic")
    ax.text(76, 87.5, "the question", ha="center", color=S1, fontsize=8.4,
            style="italic")

    # Control axes: three narrower boxes.
    ctrl = [
        ("FUSION", S3, ["rasters_only", "two_head", "bottleneck"]),
        ("FMC ARM", S3, ["baseline", "measured", "augment"]),
        ("LABEL", WARN, ["nbac   train", "vnp14  control", "dnbr   REFUSED"]),
    ]
    for i, (name, col, lines) in enumerate(ctrl):
        x = i * 34.5
        box(ax, x, 55, 31, name, lines, edge=col, fs=8.4)
        ax.text(x + 15.5, 57.3, "control", ha="center", color=col, fontsize=8.2,
                style="italic")

    # Held fixed.
    ax.text(0, 26, "Held fixed across every run", color=INK_BRIGHT, fontsize=10,
            fontweight="bold", va="top")
    fixed = [
        ("selection metric", "auc_px; IoU@0.5 partly selects for a lucky threshold"),
        ("splits", "grouped by LOCATION, not patch"),
        ("seeds", ">= 6; a claim at n=3 vanished at n=6"),
        ("reporting", "fire-tile and false-alarm metrics kept separate"),
    ]
    for i, (k, v) in enumerate(fixed):
        y = 20 - i * 5.0
        ax.text(1, y, k, color=INK_BRIGHT, fontsize=8.6, va="center",
                family="monospace")
        ax.text(23, y, v, color=INK, fontsize=8.5, va="center")

    caption(fig, [
        "The band and architecture axes are crossed. The three controls are run as "
        "separate arms against a fixed band set rather than crossed",
        "with it: crossing all five would be roughly 40x the compute and would answer "
        "no question the separate arms do not.",
    ])
    _save(fig, "exp_axes.png")


# ──────────────────────────────────────────────────────────────────────────
# 2. The two-tier selection protocol
# ──────────────────────────────────────────────────────────────────────────

def diagram_protocol():
    fig, ax = _canvas(10.0, 6.6)
    heading(ax, "How the band ranking is produced",
            "Greedy selection re-run inside every fold, then the shortlist confirmed "
            "across every architecture.")

    y1, _ = box(ax, 0, 88, 27, "TIER 1  wide sweep", [
        "preset tier2-small", "15k params", "45 fits per fold",
    ], edge=S1, fs=8.2)
    y2, _ = box(ax, 0, y1 - 6, 27, "x 6 FOLDS", [
        "search re-runs independently", "in each fold", "270 fits total",
    ], edge=S1, fs=7.8)
    arrow(ax, 13.5, y1, 13.5, y1 - 6)

    yn, hn = box(ax, 34, 84, 30, "NESTED RANKING", [
        "best 1-band set", "best 2-band set", "...", "best 9-band set",
        "+ margin at each k", "+ marginal gain",
    ], edge=S3, fs=8.2)
    arrow(ax, 27, y2 + 6, 34, yn + hn / 2)

    yf, _ = box(ax, 70, 84, 30, "SELECTION FREQUENCY", [
        "how often each band", "is picked across folds",
    ], edge=WARN, fs=8.2)
    yc, _ = box(ax, 70, yf - 5, 30, "CONSENSUS SET", [
        "picked in >= half", "the folds; may be", "SMALLER than k",
    ], edge=WARN, fs=8.2)
    arrow(ax, 64, yn + hn - 4, 70, yf - 4)
    arrow(ax, 85, yf, 85, yf - 5)

    yt, ht = box(ax, 0, 34, 46, "TIER 2  confirm", [
        "top sets x 9 presets x 6 seeds", "486 fits",
        "only here are absolute numbers meaningful",
    ], edge=CRIT, fs=7.8)
    arrow(ax, 44, yn, 25, 34, col=CRIT)

    box(ax, 54, 34, 46, "HARDWARE COST", [
        "BRAM / DSP / LUT / latency", "vs input channel count",
        "-> value per MARGINAL cost",
    ], edge=CRIT, fs=7.8)
    arrow(ax, 46, yt + ht / 2, 54, yt + ht / 2, col=CRIT)

    ax.text(50, 6.0, "Tier 1 runs 35 epochs: a RANKING budget, not an accuracy budget.",
            ha="center", color=CRIT, fontsize=9, fontweight="bold")
    ax.text(50, 1.5,
            "Every run reports whether it peaked at its final epoch. Above a quarter "
            "truncated, the ranking is void.",
            ha="center", color=MUTED, fontsize=8.3)

    caption(fig, [
        "Greedy over the 10 VNIR candidates is 55 fits for the full nesting, so the wide sweep "
        "uses the cheapest preset and the expensive ones see only the",
        "shortlist. Per-fold variation is not noise to average away: a band chosen in "
        "every fold is a finding, one chosen in three of six is a coin flip.",
    ])
    _save(fig, "exp_protocol.png")


# ──────────────────────────────────────────────────────────────────────────
# 3. CFFDRS baseline and what is tested against it
# ──────────────────────────────────────────────────────────────────────────

def diagram_cffdrs():
    fig, ax = _canvas(10.0, 6.4)
    heading(ax, "CFFDRS as the baseline, and what is tested against it",
            "FBP's documented inputs are the reference. Each supplementary input "
            "replaces or augments one slot.")

    box(ax, 0, 85, 45, "FBP BASELINE", [
        "wind speed + direction", "FFMC / ISI / BUI",
        "percent slope + aspect", "fuel type: 2024 layer",
        "foliar moisture: equation", "from elevation, lat/lon, date",
    ], edge=MUTED, fs=8.3)
    box(ax, 55, 85, 45, "SAFARI SUPPLEMENTARY", [
        "spectral bands", "fuel type: from SCANFI",
        "foliar moisture: spectral", "", "each REPLACES or AUGMENTS",
        "one baseline slot",
    ], edge=S1, fs=8.3)
    arrow(ax, 45, 68, 55, 68, col=S1, lw=2)
    ax.text(50, 70.5, "delta", ha="center", color=S1, fontsize=8.6, style="italic")

    status = [
        ("FOLIAR MOISTURE", ["baseline  equation", "measured  spectral",
                             "augment   both", "", "BLOCKED: no spectral", "estimate yet (Q14)"]),
        ("FUEL TYPE", ["baseline  2024 layer", "derived   SCANFI", "",
                       "MEASURED: R2 -0.071", "worse than predicting", "the mean"]),
        ("BANDS", ["the main question", "", "11 candidates, ranked", "on a non-circular label",
                   "", "BLOCKED: data is 3-band"]),
    ]
    for i, (name, lines) in enumerate(status):
        box(ax, i * 34.5, 42, 31, name, lines, edge=CRIT, fs=8.0)

    ax.text(50, 6, "FOP (ignition probability) is out of scope by decision.",
            ha="center", color=MUTED, fontsize=8.6, style="italic")

    caption(fig, [
        "A CFFDRS baseline gives every supplementary input a defined thing to beat. "
        "FBP already sanctions the foliar-moisture swap: its reference",
        "implementation uses a supplied FMC as given and falls back to the equation "
        "only when none is provided, so the measured arm is a",
        "documented override rather than a modification.",
    ])
    _save(fig, "exp_cffdrs.png")


# ──────────────────────────────────────────────────────────────────────────
# 4. What blocks what
# ──────────────────────────────────────────────────────────────────────────

def diagram_critical_path():
    fig, ax = _canvas(10.0, 5.4)
    heading(ax, "What is built, and what blocks the rest",
            "The data path is done. The VNIR selection is the next step "
            "and nothing is stopping it.")

    steps = [
        ("11-band\ndownload", S3, "292 patches\nEPSG:3978"),
        ("tile, split,\npack HDF5", S3, "1834/473/206\n11 bands"),
        ("covariate\nsidecars", WARN, "terrain 100%\nweather redo"),
        ("VNIR sweep\n(Narval)", WARN, "best 6 of 10\njob not written"),
        ("pool folds", S3, "pool_bands.py\nwritten, tested"),
        ("results\nnote", CRIT, "needs the\nsweep"),
    ]
    from matplotlib.patches import FancyBboxPatch
    w, gap, top, h = 13.6, 3.7, 80, 20
    for i, (label, col, note) in enumerate(steps):
        x = i * (w + gap)
        ax.add_patch(FancyBboxPatch((x, top - h), w, h,
                                    boxstyle="round,pad=0,rounding_size=1.4",
                                    linewidth=1.5, edgecolor=col, facecolor=AX_BG,
                                    zorder=2))
        ax.text(x + w / 2, top - 5.5, label, ha="center", va="center",
                color=INK_BRIGHT, fontsize=8.6, fontweight="bold", linespacing=1.4,
                zorder=3)
        ax.text(x + w / 2, top - 14.5, note, ha="center", va="center", color=col,
                fontsize=7.4, linespacing=1.4, family="monospace", zorder=3)
        if i < len(steps) - 1:
            arrow(ax, x + w, top - h / 2, x + w + gap, top - h / 2)

    ax.text(0, 50, "Built and tested, waiting only on data", color=INK_BRIGHT,
            fontsize=10, fontweight="bold", va="top")
    built = [
        "band registry: 11 bands at 20 m, append-only order",
        "non-circular labels; a dNBR label is refused outright",
        "splits grouped by location (fixed a real leak: 141 of 637 keys)",
        "greedy nested search, per fold, with stability reporting",
        "both fusion variants; all 9 presets take any band count",
        "SLURM array with preflight gates on the band pool and the label",
    ]
    for i, b in enumerate(built):
        y = 43 - i * 5.6
        ax.text(1, y, "v", color=S3, fontsize=9.5, va="center", fontweight="bold",
                family="monospace")
        ax.text(5, y, b, color=INK, fontsize=8.5, va="center")

    caption(fig, [
        "The data blocker is gone: 292 patches are packed at 11 bands, splits are grouped by location, and pool_bands.py is written and "
        "tested. What remains is the Narval job for the VNIR selection itself. The weather redo is an Earth Engine pass and runs locally, "
        "since Narval compute nodes have no outbound network.",
    ])
    _save(fig, "exp_critical_path.png")


# ──────────────────────────────────────────────────────────────────────────
# 5. Our rating against the operational one
# ──────────────────────────────────────────────────────────────────────────

def diagram_vs_cffdrs():
    """The comparison ladder: raw inputs, codes, subsystems, then ours."""
    fig, ax = _canvas(10.6, 8.2)
    heading(ax, "Our rating against CFFDRS, rung by rung",
            "Each level is scored as a predictor in its own right, so it is visible "
            "WHERE the predictive power comes from.")

    # (label, items, granularity, availability colour, note)
    RUNGS = [
        ("raw weather inputs", "temp · RH · wind speed · wind direction · rain",
         "scalar", S3, "free"),
        ("FWI codes, individually", "FFMC · DMC · DC · ISI · BUI",
         "scalar", S3, "free"),
        ("FWI subsystem output", "FWI",
         "scalar", S3, "free"),
        ("FBP inputs, individually", "fuel type · percent slope · aspect · FMC · wind",
         "mixed", WARN, "needs fuel layer"),
        ("FBP subsystem output", "ROS · HFI · CFB · fire type",
         "spatial", CRIT, "NEEDS A PORT"),
        ("ours, bands only", "9 candidate bands",
         "spatial", S1, "needs 11-band"),
        ("ours, bands + CFFDRS", "bands + terrain + the scalars above",
         "spatial", S1, "needs both"),
    ]

    top, rh_ = 84, 7.4
    for i, (name, items, gran, col, note) in enumerate(RUNGS):
        y = top - i * rh_
        from matplotlib.patches import FancyBboxPatch
        ax.add_patch(FancyBboxPatch((0, y - 5.6), 100, 5.6,
                                    boxstyle="round,pad=0,rounding_size=1.0",
                                    linewidth=1.3, edgecolor=col, facecolor=AX_BG,
                                    zorder=2))
        ax.text(1.6, y - 2.8, name, va="center", color=INK_BRIGHT, fontsize=8.8,
                fontweight="bold", zorder=3)
        ax.text(30, y - 2.8, items, va="center", color=INK, fontsize=8.0,
                family="monospace", zorder=3)
        ax.text(76, y - 2.8, gran, va="center", color=MUTED, fontsize=7.8,
                family="monospace", zorder=3)
        ax.text(98.4, y - 2.8, note, va="center", ha="right", color=col,
                fontsize=7.8, zorder=3)

    ax.text(30, 87.5, "predictor", color=MUTED, fontsize=7.6, family="monospace")
    ax.text(76, 87.5, "grain", color=MUTED, fontsize=7.6, family="monospace")
    ax.text(98.4, 87.5, "status", color=MUTED, fontsize=7.6, family="monospace",
            ha="right")

    ax.text(0, 29, "Two rules that keep the ladder honest", color=INK_BRIGHT,
            fontsize=9.8, fontweight="bold", va="top")

    box(ax, 0, 24, 48, "SCORE AT MATCHING GRAIN", [
        "A per-patch scalar and a per-pixel map",
        "cannot share an AUC. Scalars are scored",
        "at PATCH level (did this patch burn),",
        "spatial predictors at PIXEL level.",
    ], edge=MUTED, fs=7.8, mono=False)

    box(ax, 52, 24, 48, "TWO FRAMINGS, ONE FAIR", [
        "Unconditional (did it burn) disadvantages",
        "CFFDRS: FWI and FBP predict BEHAVIOUR",
        "given ignition, not where fire starts.",
        "Within-fire severity is the fair test.",
    ], edge=MUTED, fs=7.8, mono=False)

    caption(fig, [
        "Scoring each rung separately answers a question the combined model cannot: if "
        "a single slow code like DC does nearly as well as the full",
        "FBP system, that is worth knowing before any hardware is specified. "
        "auc_px is rank-based, so an index and a probability compare directly.",
        "",
        "Only one rung costs new code. fwi.py already emits all six codes and fbp.py the "
        "FBP inputs; the FBP behaviour equations - fuel-type-specific",
        "rate of spread, crown fraction burned, head fire intensity - are not "
        "implemented, and there is no Python package, only the CRAN R one.",
    ])
    _save(fig, "exp_vs_cffdrs.png")


# ──────────────────────────────────────────────────────────────────────────
# 6. Report claims against the experiments that substantiate them
# ──────────────────────────────────────────────────────────────────────────

def diagram_claims():
    """Which experiment backs which claim in the mission report."""
    fig, ax = _canvas(11.2, 8.6)
    heading(ax, "Report claims, and the experiment that substantiates each",
            "Green is measured or designed. Amber is partial. Red is claimed in the "
            "report with nothing measuring it.")

    OK, PART, GAP = S3, WARN, CRIT
    CLAIMS = [
        ("compare fuel-condition estimates used by CFFDRS",
         "the rung-by-rung comparison ladder", OK),
        ("directly observe properties CFFDRS INFERS",
         "FMC arms: equation vs spectral vs both", OK),
        ("characterize fuel types",
         "derived vs published layer -- MEASURED, R2 -0.071", OK),
        ("canopy water content",
         "target T1; blocked on a spectral FMC estimate (Q14)", PART),
        ("combine with uplinked weather + topography",
         "fusion arms, scored at 0/24/72 h staleness", OK),
        ("vegetation stress",
         "nearest is T3 mortality; no stress target defined", PART),
        ("wildfire-risk POLYGONS as the primary product",
         "nothing produces or scores polygons -- all metrics are per-pixel", GAP),
        ("a few kilobytes, several orders of magnitude",
         "arithmetic checks out (~94,000x) but nothing measures it", GAP),
        ("operational frequency for fire danger rating",
         "29-33 ms/frame measured; not tied to orbit cadence", PART),
        ("onboard AI models, end-to-end in orbit",
         "hls4ml path works; main core is 405% over BRAM", PART),
        ("preprocessed imagery for Essential Climate Variables",
         "no ECV is defined, produced or validated", GAP),
    ]

    top, rh_ = 86, 6.2
    from matplotlib.patches import FancyBboxPatch
    for i, (claim, backing, col) in enumerate(CLAIMS):
        y = top - i * rh_
        ax.add_patch(FancyBboxPatch((0, y - 4.9), 100, 4.9,
                                    boxstyle="round,pad=0,rounding_size=0.9",
                                    linewidth=1.2, edgecolor=col, facecolor=AX_BG,
                                    zorder=2))
        mark = {OK: "v", PART: "~", GAP: "x"}[col]
        ax.text(1.8, y - 2.45, mark, va="center", color=col, fontsize=9.5,
                fontweight="bold", family="monospace", zorder=3)
        ax.text(5, y - 2.45, claim, va="center", color=INK_BRIGHT, fontsize=8.5,
                zorder=3)
        ax.text(48, y - 2.45, backing, va="center", color=col, fontsize=8.0,
                zorder=3)

    ax.text(0, 15, "The three gaps, in order of consequence", color=INK_BRIGHT,
            fontsize=9.8, fontweight="bold", va="top")
    gaps = [
        "POLYGONS are the stated primary product and every metric in the study is "
        "per-pixel. A model can score well on auc_px and",
        "   fragment into hundreds of unusable slivers; nothing would currently catch "
        "that.",
        "DOWNLINK BUDGET is a quantified claim in the report. It should be measured "
        "from real model output, not asserted.",
        "ECVs appear in the report with no variable named. SCANFI already gives biomass, "
        "canopy height and cover, which are ECV-adjacent.",
    ]
    for i, g in enumerate(gaps):
        ax.text(0.5, 9.5 - i * 3.6, g, color=INK if i != 1 else MUTED,
                fontsize=8.2, va="top")

    caption(fig, [
        "Every claim about comparing against CFFDRS is well covered -- that is what the "
        "ladder was built for. The gaps are all on the PRODUCT side:",
        "what the satellite actually downlinks, how big it is, and how often. Those are "
        "the claims a reviewer can check most easily, so they are",
        "the ones worth measuring rather than asserting.",
    ])
    _save(fig, "exp_claims.png")


def main() -> int:
    print("rendering experiment diagrams")
    diagram_axes()
    diagram_protocol()
    diagram_cffdrs()
    diagram_critical_path()
    diagram_vs_cffdrs()
    diagram_claims()
    print(f"\nall diagrams -> {FIG_DIR.relative_to(_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
