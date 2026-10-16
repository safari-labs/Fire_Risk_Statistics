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
#: (name, varies, answers, script)
#:
#: SCRIPT is the actual runner, verified to exist. "--" means nothing runs it
#: yet, which is the single most useful column in this figure: it is the
#: to-write list. Env vars shown are ones the script reads.
PLAN = [
    ("READY — data packed, nothing in the way", READY,
     "Sentinel-2, 2,513 tiles, 11 bands at 20 m. Six folds grouped by location.",
     [
      ("VNIR selection",
       "best 6 of 10 bands, 400-1000 nm",
       "WHICH SIX for the Mantis MS mode. The one complete answer available today",
       "sweep_arms.sh ARMS=vnir   << LAUNCHED"),
      ("All-11 greedy",
       "unconstrained over 11 candidates",
       "does B11 get picked, and at what k -- evidence the SWIR chain earns a slot",
       "sweep_arms.sh ARMS=all11   << LAUNCHED"),
      ("Forced-SWIR",
       "B11 held in, same k as the VNIR arm",
       "the SWIR delta at matched band count. Lower bound: we have 1 SWIR band, Mantis has 4",
       "sweep_arms.sh ARMS=vnir_swir   << LAUNCHED"),
      ("Leave-one-out",
       "remove each band from the chosen set",
       "per-band value CONDITIONAL on the rest -- the only importance that means anything here",
       "sweep_bands.py --leave-one-out   << in all 3"),
      ("Selection frequency",
       "the same search inside each of 6 folds",
       "6/6 is a finding, 3/6 is a coin flip. Separates both from a single-fold fluke",
       "pool_bands.py   (run after the arrays)"),
      ("Label control",
       "NBAC swapped for VIIRS thermal",
       "LEAKAGE. A band whose value collapses on an independent label was exploiting it",
       "sweep_bands.sh LABEL=vnp14"),
      ("Lightning cohort",
       "fires filtered to NFDB CAUSE = lightning",
       "removes the roads-and-access confound from human ignitions",
       "labels.is_lightning() exists; no runner"),
      ("Negative control",
       "a deliberately redundant band pool",
       "sanity. If this scores well the pipeline is broken, not the bands",
       "sweep_bands.sh BANDS=...  / negative_control.yaml"),
     ]),

    ("MOSTLY NO RE-PACK — a column mask over the pack we have", SOON,
     "The pack carries weather_arm=both, the UNION of all arms,"
     " so most of these are flags not repacks.",
     [
      ("Weather arms",
       "FWI codes / history / both / dimensionless",
       "does OUR compression of 91 days beat the FWI System's? Baseline is CFFDRS as it stands",
       "sweep_bands.py --weather-arm   (no repack)"),
      ("Weather staleness  [NEW]",
       "weather aged 0 / 24 / 48 / 72 h / 7 d",
       "G7: uplink is daily at best, so CFFDRS's same-day noon"
       " observation is not what we will have",
       "-- needs lagged FWI sidecars (E-4)"),
      ("Fusion arms",
       "rasters_only / two_head / bottleneck",
       "what the CFFDRS-shaped separation of fuel and weather costs or buys",
       "sweep_bands.sh FUSION=two_head|bottleneck"),
      ("FMC arms  [VACUOUS]",
       "baseline / measured / augment",
       "CANNOT RUN: fmc_measured is written nowhere, so all three arms are the FBP equation",
       "sweep_bands.sh FMC_ARM=  (do not bother)"),
      ("Imagery vs FMC scalar",
       "bands + terrain against the FBP FMC alone",
       "G1 restated: does imagery carry moisture information the formula misses?",
       "sweep_bands.sh FUSION=two_head, no band pool"),
      ("Station-density split  [NEW]",
       "increment stratified by distance to the nearest station",
       "G3: CFS names thin station coverage as a limit. Fuel state is the integral of weather",
       "-- needs a CWFIS station fetch (E-1)"),
      ("Snow-off startup  [NEW]",
       "per-pixel NDSI date vs the flat 90-day spinup",
       "G4: our own codes start ~1 April, frozen at 55-67 N. Fixes a latitude bias first",
       "-- needs an Earth Engine NDSI pass (E-2)"),
      ("Latitude-banded weather  [NEW]",
       "the weather-arm contrast, split by latitude",
       "G5: day-length factors are tabulated for ~46 N. A pooled number cannot test that",
       "pool_bands.py -- needs a band-split flag (E-3)"),
      ("Ecology arm",
       "the same searches against SCANFI structure",
       "PRIMARY band ranking. Dense per-pixel labels, not one sparse outcome per patch",
       "train_ecology.sh / train_ecology.py"),
      ("SCANFI refresh",
       "static 2020 layer vs our current estimate",
       "does a REFRESHED fuel map predict fire better, and does the gain grow with staleness?",
       "attach_scanfi_to_fire.py (done) + train_ecology.py"),
      ("Resolution sweep",
       "20 / 40 / 80 m, coarsen only",
       "how much GSD the retrieval actually needs -- a mission requirement, not a curiosity",
       "data.py coarsen() exists; no CLI flag"),
     ]),

    ("NEEDS NEW DATA — free, and now partly fetched", LATER,
     "AVIRIS-NG ABoVE: 163 of 574 Canadian lines are published at 5 nm;"
     " 42 of those precede a burn. 3 are on disk.",
     [
      ("SWIR placement",
       "any 4 bands in 1003-1359 and 1414-1749 nm",
       "THE SWIR DECISION. Sentinel-2 has one band in that window; four cannot be chosen from one",
       "fetch_aviris.py (3 done) + ingest_aviris.py"),
      ("1209 vs 1240",
       "WorldView-3's choice against Gao's NDWI band",
       "water sensitivity traded against O2 margin -- the validator flagged it, nobody measured it",
       "ingest_aviris.py --mode both"),
      ("HS vs MS, properly",
       "140 SWIR channels at 5 nm vs the best 6 VNIR",
       "what spectral RESOLUTION buys. Ten S2 bands cannot be interpolated into ninety-six",
       "ingest_aviris.py, then sweep_bands.py"),
      ("Conditional large fire",
       "burned >100 ha, given it burned at all",
       "36% base rate, and 97% of area burned is in the tail. Fuel-dominated, unlike ignition",
       "-- needs an NBAC area filter at pack time"),
     ]),

    ("HARDWARE — runs beside the band work", HW,
     "Converts each model for real and applies a BRAM law matched to two synthesis runs.",
     [
      ("Cost vs input channels",
       "3 / 6 / 10 / 11 / 96 channels",
       "the MARGINAL COST denominator. The brief asks for value per cost, not value",
       "sweep_architecture.py --widths"),
      ("Misregistration",
       "sub-pixel VNIR/SWIR shifts at hard edges",
       "a tolerance to specify. The dichroic makes this small, not absent",
       "-- no runner yet"),
     ]),

    ("OUT OF REACH — stated, not planned", BLOCKED,
     "Listed because a plan that only lists what it can do is not a plan.",
     [
      ("T1 live foliar moisture",
       "LFMC, the brief's lead target",
       "NO LABEL EXISTS in this data. Needs radiative transfer, or Globe-LFMC, or field sampling",
       "-- no label, so no script"),
      ("T2 curing / NPV",
       "grass curing fraction",
       "no label, no grassland in the ecology set, and NDLI needs 1754 nm -- past the detector",
       "-- no label, so no script"),
      ("Fire occurrence (FOP)",
       "ignition probability per cell-day",
       "out of scope by decision. Needs lightning strike data; the satellite sees no ignition",
       "-- out of scope"),
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

    fig, ax = plt.subplots(figsize=(19.0, 0.45 + total), facecolor=FIG_BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.08, total + 0.12)
    ax.axis("off")
    fig.suptitle("Every experiment, what it varies, what it settles, and "
                 "what runs it",
                 color=INK_BRIGHT, fontsize=13.5, x=0.0, ha="left", y=1.0)
    ax.text(2.0, total + 0.02, "EXPERIMENT / WHAT VARIES", color=MUTED,
            fontsize=7.2, va="center", weight="bold")
    ax.text(24, total + 0.02, "WHAT IT SETTLES", color=MUTED, fontsize=7.2,
            va="center", weight="bold")
    ax.text(70.5, total + 0.02, "RUNNER", color=MUTED, fontsize=7.2,
            va="center", weight="bold")

    y = total
    for title, col, sub, items in PLAN:
        y -= HEAD
        ax.text(0, y + 0.24, title, color=col, fontsize=10.2, weight="bold",
                va="center")
        ax.text(0, y + 0.02, sub, color=MUTED, fontsize=7.8, va="center",
                style="italic")
        ax.plot([0, 100], [y - 0.12, y - 0.12], color=SPINE, lw=0.8)
        for name, varies, answers, script in items:
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
            ax.text(24, y + 0.07, answers, color=INK, fontsize=8.3,
                    va="center", zorder=2)
            # A launched arm is called out, and a missing runner is dimmed:
            # the eye should land on what is running and what is unwritten.
            launched = "<<" in script
            unwritten = script.startswith("--")
            ax.text(70.5, y + 0.07, script,
                    color=READY if launched else (
                        BLOCKED if unwritten else MUTED),
                    fontsize=7.8, va="center", zorder=2, family="monospace",
                    weight="bold" if launched else "normal")

    n_live = sum(1 for _, _, _, items in PLAN
                 for *_, s in items if "<<" in s)
    n_todo = sum(1 for _, _, _, items in PLAN
                 for *_, s in items if s.startswith("--"))
    fig.text(0.0, -0.045, chr(10).join([
        f"LAUNCHED: {n_live} rows, which is the three band-selection arms "
        f"plus the leave-one-out riding inside each of them. One sbatch array "
        f"of 6 folds per arm, 18 tasks, ~1,056 fits,",
        "tier2-small at 35 epochs against the NBAC label. Those 35 epochs are "
        "a RANKING budget: the output is an order, and no number from it is "
        "quotable as an accuracy until the top sets",
        "are re-run at full budget. Nothing is a result until pool_bands.py "
        "has combined the six folds, because one fold is a sample.",
        "",
        f"The RUNNER column is the honest part: {n_todo} experiments have no "
        f"script at all, and saying which is more useful than a plan that "
        f"implies everything is one command away.",
        "",
        "Three rows are CONTROLS, not results, and a positive finding is not "
        "reportable without them: the thermal label (a band whose value "
        "survives only on NBAC was reading the label,",
        "not the fuel), the lightning cohort (human ignitions carry a "
        "roads-and-access signal), and per-fold selection frequency. None of "
        "the three is in the launched set.",
        "",
        "Three experiments marked [NEW] came from auditing our claims against "
        "CFFDRS's stated gaps (docs/CFFDRS_GAPS.md): without them G3, G4 and "
        "G5 were claims we could assert",
        "but not test. The FMC arms are VACUOUS for a related reason -- "
        "fmc_measured is read in four places and written in none, so all three "
        "arms reduce to the FBP equation and would",
        "have produced three identical numbers looking like 'no difference'.",
        "",
        "The last block is not a backlog. T1 and T2 have no label anywhere in "
        "this data and cannot be obtained by working harder on what we hold. "
        "Saying so is part of the answer.",
    ]), color=MUTED, fontsize=8.2, ha="left", linespacing=1.5)

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "experiment_plan.png"
    fig.savefig(out, dpi=165, facecolor=FIG_BG, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {out}  ({n_rows} experiments in {n_head} groups)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
