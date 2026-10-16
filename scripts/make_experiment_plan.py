"""scripts/make_experiment_plan.py

Every experiment in the study, what each one varies, and what it settles.

Grouped by what stands between it and a result, because that is the only
ordering that tells you what to do next. An experiment that is blocked on a
purchase is not in the same category as one blocked on a two-gigabyte copy.

    python scripts/make_experiment_plan.py
"""
from __future__ import annotations

import sys
from pathlib import Path

OUT = Path("docs/results/figures")

FIG_BG, AX_BG = "#14161a", "#1b1e24"
INK, INK_BRIGHT, MUTED, SPINE = "#c7ccd4", "#eef1f5", "#79818e", "#2c313a"
#: One colour per readiness tier. HARDWARE gets its own rather than
#: sharing with NEW DATA -- the chips are the only cue once the reader
#: has scrolled past the heading.
READY, SOON, LATER = "#52a675", "#e8973f", "#9b7fd4"
HW, BLOCKED = "#4ea1d3", "#d1495b"

#: (section, colour, subtitle)
#: (name, varies, answers)
PLAN = [
    ("READY — data packed, nothing in the way", READY,
     "Sentinel-2, 2,513 tiles, 11 bands at 20 m. Six folds grouped by location.",
     [
      ("VNIR selection",
       "best 6 of 10 bands, 400-1000 nm",
       "WHICH SIX for the Mantis MS mode. The one complete answer available today"),
      ("All-11 greedy",
       "unconstrained over 11 candidates",
       "does B11 get picked, and at what k -- evidence the SWIR chain earns a slot"),
      ("Forced-SWIR",
       "B11 held in, same k as the VNIR arm",
       "the SWIR delta at matched band count. Lower bound: we have 1 SWIR band, Mantis has 4"),
      ("Leave-one-out",
       "remove each band from the chosen set",
       "per-band value CONDITIONAL on the rest -- the only importance that means anything here"),
      ("Selection frequency",
       "the same search inside each of 6 folds",
       "6/6 is a finding, 3/6 is a coin flip. Separates both from a single-fold fluke"),
      ("Label control",
       "NBAC swapped for VIIRS thermal",
       "LEAKAGE. A band whose value collapses on an independent label was exploiting it"),
      ("Lightning cohort",
       "fires filtered to FIRECAUS = Natural",
       "removes the roads-and-access confound from human ignitions"),
      ("Negative control",
       "4 overlapping red bands",
       "sanity. If this scores well the pipeline is broken, not the bands"),
     ]),

    ("NEEDS A RE-PACK — hours, no new downloads", SOON,
     "Scalars must be packed into the HDF5; the ecology set must be tiled.",
     [
      ("Weather arms",
       "FWI codes / history / both / dimensionless",
       "does OUR compression of 91 days beat the FWI System's? Baseline is CFFDRS as it stands"),
      ("Fusion arms",
       "rasters-only / two-head / bottleneck",
       "what the CFFDRS-shaped separation of fuel and weather costs or buys"),
      ("FMC arms  [VACUOUS]",
       "baseline / measured / augment",
       "CANNOT RUN: fmc_measured is written nowhere, so all three arms are the FBP equation"),
      ("Imagery vs FMC scalar",
       "bands + terrain against the FBP FMC alone",
       "G1 restated: does imagery carry moisture information the formula misses?"),
      ("Station-density split  [NEW]",
       "increment stratified by distance to the nearest station",
       "G3: CFS names thin station coverage as a limit. Fuel state is the integral of weather"),
      ("Snow-off startup  [NEW]",
       "per-pixel NDSI date vs the flat 90-day spinup",
       "G4: our own codes start ~1 April, frozen at 55-67 N. Fixes a latitude bias first"),
      ("Latitude-banded weather  [NEW]",
       "the weather-arm contrast, split by latitude",
       "G5: day-length factors are tabulated for ~46 N. A pooled number cannot test that"),
      ("Ecology arm",
       "the same searches against SCANFI structure",
       "PRIMARY band ranking. Dense per-pixel labels, not one sparse outcome per patch"),
      ("SCANFI refresh",
       "static 2020 layer vs our current estimate",
       "does a REFRESHED fuel map predict fire better, and does the gain grow with staleness?"),
      ("Resolution sweep",
       "20 / 40 / 80 m, coarsen only",
       "how much GSD the retrieval actually needs -- a mission requirement, not a curiosity"),
     ]),

    ("NEEDS NEW DATA — free, but not yet fetched", LATER,
     "AVIRIS-NG ABoVE: 574 Canadian lines at 5 nm, 228 of them flown before a burn.",
     [
      ("SWIR placement",
       "any 4 bands in 1000-1750 nm",
       "THE SWIR DECISION. Sentinel-2 has one band in that window; four cannot be chosen from one"),
      ("1209 vs 1240",
       "WorldView-3's choice against Gao's NDWI band",
       "water sensitivity traded against O2 margin -- the validator flagged it, nobody has measured it"),
      ("HS vs MS, properly",
       "96 bands at 4.5 nm vs the best 6",
       "what spectral RESOLUTION buys. Ten S2 bands cannot be interpolated into ninety-six"),
      ("Conditional large fire",
       "burned >100 ha, given it burned at all",
       "36% base rate, and 97% of area burned is in the tail. Fuel-dominated, unlike ignition"),
     ]),

    ("HARDWARE — runs beside the band work", HW,
     "Converts each model for real and applies a BRAM law matched to two synthesis runs.",
     [
      ("Cost vs input channels",
       "3 / 6 / 10 / 11 / 96 channels",
       "the MARGINAL COST denominator. The brief asks for value per cost, not value"),
      ("Misregistration",
       "sub-pixel VNIR/SWIR shifts at hard edges",
       "a tolerance to specify. The dichroic makes this small, not absent"),
     ]),

    ("OUT OF REACH — stated, not planned", BLOCKED,
     "Listed because a plan that only lists what it can do is not a plan.",
     [
      ("T1 live foliar moisture",
       "LFMC, the brief's lead target",
       "NO LABEL EXISTS in this data. Needs radiative transfer, or Globe-LFMC, or field sampling"),
      ("T2 curing / NPV",
       "grass curing fraction",
       "no label, no grassland in the ecology set, and NDLI needs 1754 nm -- past the detector"),
      ("Fire occurrence (FOP)",
       "ignition probability per cell-day",
       "out of scope by decision. Needs lightning strike data; the satellite sees no ignition"),
     ]),
]


def main() -> int:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK,
                         "figure.facecolor": FIG_BG,
                         "savefig.facecolor": FIG_BG})

    n_rows = sum(len(items) for _, _, _, items in PLAN)
    n_head = len(PLAN)
    H, HEAD = 0.40, 0.62
    total = n_rows * H + n_head * HEAD

    fig, ax = plt.subplots(figsize=(15.0, 0.45 + total), facecolor=FIG_BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.08, total + 0.12)
    ax.axis("off")
    fig.suptitle("Every experiment, what it varies, and what it settles",
                 color=INK_BRIGHT, fontsize=13.5, x=0.0, ha="left", y=1.0)

    y = total
    for title, col, sub, items in PLAN:
        y -= HEAD
        ax.text(0, y + 0.24, title, color=col, fontsize=10.2, weight="bold",
                va="center")
        ax.text(0, y + 0.02, sub, color=MUTED, fontsize=7.8, va="center",
                style="italic")
        ax.plot([0, 100], [y - 0.12, y - 0.12], color=SPINE, lw=0.8)
        for name, varies, answers in items:
            y -= H
            ax.add_patch(FancyBboxPatch(
                (0, y - 0.03), 100, H - 0.07, boxstyle="round,pad=0.01",
                facecolor=AX_BG, edgecolor="none", zorder=1))
            # A colour chip, so readiness is readable without the heading.
            ax.add_patch(FancyBboxPatch(
                (0.3, y + 0.02), 0.7, H - 0.17, boxstyle="square,pad=0",
                facecolor=col, edgecolor="none", alpha=0.9, zorder=2))
            ax.text(2.0, y + 0.15, name, color=INK_BRIGHT, fontsize=9,
                    va="center", zorder=2)
            ax.text(2.0, y - 0.01, varies, color=MUTED, fontsize=7.6,
                    va="center", zorder=2)
            ax.text(30, y + 0.07, answers, color=INK, fontsize=8.3,
                    va="center", zorder=2)

    fig.text(0.0, -0.045, chr(10).join([
        "Grouped by what blocks each one, because that is the ordering that "
        "says what to do next. The VNIR selection is the only complete answer "
        "available today, and it",
        "settles one of the three Mantis modes outright.",
        "",
        "Three things run as CONTROLS rather than results, and a positive "
        "finding is not reportable without them: the thermal label (a band "
        "whose value survives only on NBAC was",
        "reading the label, not the fuel), the lightning cohort (human "
        "ignitions carry a roads-and-access signal), and per-fold selection "
        "frequency (one fold is a sample, not a result).",
        "",
        "Three experiments marked [NEW] were added by auditing our claims "
        "against CFFDRS's stated gaps (docs/CFFDRS_GAPS.md): without them, G3, "
        "G4 and G5 were",
        "claims we could assert but not test. The FMC arms are marked VACUOUS "
        "for the same reason -- fmc_measured is read in four places and "
        "written in none, so all three arms",
        "reduce to the FBP equation and would have produced three identical "
        "numbers looking like 'no difference'.",
        "",
        "The last block is not a backlog. T1 and T2 have no label anywhere in "
        "this data and cannot be obtained by working harder on what we hold -- "
        "they need radiative transfer or",
        "field measurement. Saying so is part of the answer.",
    ]), color=MUTED, fontsize=8.2, ha="left", linespacing=1.5)

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "experiment_plan.png"
    fig.savefig(out, dpi=165, facecolor=FIG_BG, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {out}  ({n_rows} experiments in {n_head} groups)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
