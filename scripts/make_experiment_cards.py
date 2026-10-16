"""scripts/make_experiment_cards.py

One card per experiment family: inputs, labels, model, training, evaluation,
and what comes out.

Written so a card can be read on its own, without the rest of the repo in
your head. Where a field would be a guess it says so -- a spec sheet that
quietly invents its own parameters is worse than one with gaps, because the
gaps are the things that still need deciding.

    python scripts/make_experiment_cards.py

Writes docs/results/figures/experiments/.
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

OUT = Path("docs/results/figures/experiments")

FIG_BG, AX_BG, ROW_BG = "#14161a", "#1b1e24", "#20242c"
INK, INK_BRIGHT, MUTED, SPINE = "#c7ccd4", "#eef1f5", "#79818e", "#2c313a"
READY, SOON, LATER, BLOCKED = "#52a675", "#e8973f", "#9b7fd4", "#d1495b"

#: Field order is the order a reader needs them: what goes in, what it is
#: scored against, what computes it, how, how it is judged, what you get.
FIELDS = ("INPUT", "LABELS", "MODEL", "TRAINING", "EVALUATION", "OUTPUT",
          "CONTROLS", "STATUS")

CARDS = [
 dict(
  slug="01_vnir_selection", tier=READY, tier_name="READY",
  title="VNIR band selection",
  question="Which 6 of the 10 Sentinel-2 bands in 400-1000 nm should the "
           "Mantis MS mode carry?",
  INPUT="2,513 tiles, 256x256 at 20 m, EPSG:3978, from 292 patches. "
        "Candidate pool: B1 443, B2 490, B3 560, B4 665, B5 705, B6 740, "
        "B7 783, B8 842, B8A 865, B9 945. Bands are SELECTED from the packed "
        "11, never interpolated.",
  LABELS="NBAC fire perimeters rasterised to the patch grid, per pixel. "
         "Chosen because it is the only per-pixel label not computed from "
         "the model's own inputs -- dNBR uses B8 and B11 and is refused "
         "outright by labels.py.",
  MODEL="tier2-small (PlainFireCNN 16/32/32, 15k params) for the wide "
        "search. in_ch is set by the band set under test, so each candidate "
        "gets a correctly sized first layer.",
  TRAINING="Greedy forward selection, re-run INSIDE each of 6 folds. Folds "
           "are GroupKFold over 0.1-degree location blocks, never random "
           "rows: tiles of one patch share a weather vector exactly, so a "
           "random split is matchable on weather alone. 45 fits per fold.",
  EVALUATION="auc_px on the held-out fold. Not IoU@0.5 -- Stage A's own "
             "correction is that it conflates ranking quality with threshold "
             "placement. Fire-tile and false-alarm metrics reported "
             "separately; pooled IoU mixes them and they move opposite ways.",
  OUTPUT="A nested ranking: the best k-band set for every k, with the "
         "marginal gain and the decision margin at each rung. k=6 is the "
         "decision; the rest is context for reading it.",
  CONTROLS="Selection frequency across folds (6/6 is a finding, 3/6 a coin "
           "flip) · negative control band set, which must score badly · "
           "truncation fraction, flagged above 25%.",
  STATUS="Ready. Data staged as a 2.02 GB bundle. Only the epoch budget is "
         "unsettled.",
 ),
 dict(
  slug="02_swir_contribution", tier=READY, tier_name="READY",
  title="Does the SWIR chain earn its place?",
  question="Is a second detector chain worth carrying, given Sentinel-2 "
           "gives us only one band inside the SWIR window?",
  INPUT="The same tiles, pool widened to all 11 bands. Two arms: all11 "
        "(unconstrained, k_max 7) and vnir_swir (B11 forced in, k_max 7). "
        "Compared against the VNIR arm at matched k.",
  LABELS="NBAC, as above.",
  MODEL="tier2-small, as above.",
  TRAINING="Same greedy-per-fold protocol. 56 fits per fold per arm.",
  EVALUATION="auc_px. The quantity of interest is the DIFFERENCE from the "
             "VNIR arm at the same k, paired within fold -- fold levels vary "
             "by more than the effect does.",
  OUTPUT="The k at which B11 enters unforced, and the score delta from "
         "forcing it.",
  CONTROLS="Same as the VNIR arm.",
  STATUS="Ready, but ASYMMETRIC. If B11 helps, that is strong evidence for "
         "the chain -- four bands cannot be worse than one. If it does not, "
         "the evidence against is WEAK: a 1240 nm band unlocks Gao's NDWI "
         "which B11 alone cannot form, and H1 needs two SWIR bands with "
         "different water-to-dry-matter ratios. One band cannot test the "
         "mechanism the chain exists for.",
 ),
 dict(
  slug="03_per_band_value", tier=READY, tier_name="READY",
  title="Per-band value, conditional on the rest",
  question="What does each band in the chosen set actually contribute?",
  INPUT="The chosen k-band set from the selection arm, minus one band at a "
        "time.",
  LABELS="NBAC.",
  MODEL="tier2-small, unchanged, so only the input width differs.",
  TRAINING="Leave-one-out: k+1 fits, of which the full-set fit is free "
           "because greedy already paid for it.",
  EVALUATION="drop = full score - score without the band. Negative drops are "
             "REPORTED, not clipped: with six slots a band that costs "
             "accuracy is an expensive finding. Pooled across folds paired, "
             "and a drop under its own spread is labelled 'within noise'.",
  OUTPUT="A ranked table of per-band drops with standard deviations.",
  CONTROLS="Read beside the selection frequency, never alone. Leave-one-out "
           "CANNOT see redundancy: if two bands carry the same information, "
           "removing either alone costs nothing and both read as dead weight. "
           "B8 and B8A are near-duplicates by the validator's own measure.",
  STATUS="Ready. Wired into the sweep behind --leave-one-out.",
 ),
 dict(
  slug="04_label_controls", tier=READY, tier_name="READY",
  title="Leakage and confound controls",
  question="Is the ranking measuring fuel, or something correlated with the "
           "label?",
  INPUT="The chosen band sets, unchanged.",
  LABELS="Three swaps. (1) VIIRS thermal instead of NBAC -- built from "
         "radiance EMITTED at 4 and 11 um during the fire, so it cannot "
         "share information with pre-fire reflectance. (2) NBAC filtered to "
         "FIRECAUS = Natural, dropping human ignitions. (3) the negative "
         "control band set against the normal label.",
  MODEL="tier2-small.",
  TRAINING="Re-score the already-chosen sets; no new search.",
  EVALUATION="Rank correlation against the primary ranking, per control.",
  OUTPUT="For each control, whether the ranking survives.",
  CONTROLS="These ARE the controls. A band whose value collapses under the "
           "thermal label was reading the label, not the fuel. A band that "
           "loses value on lightning-only fires was reading roads and access.",
  STATUS="Ready. Thermal on 273/292 patches, FIRECAUS in NBAC per perimeter.",
 ),
 dict(
  slug="05_weather_arms", tier=SOON, tier_name="NEEDS A RE-PACK",
  title="Does our weather compression beat the FWI System's?",
  question="The FWI codes ARE a compression of 91 days of weather. Is ours "
           "better for this task?",
  INPUT="Bands + terrain rasters, plus a per-patch scalar vector. 21 scalars "
        "packed as a SUPERSET: CODES is columns 0-8, HISTORY drops "
        "ffmc/isi/bui, BOTH is all of it. One pack serves every arm.",
  LABELS="NBAC.",
  MODEL="tier2-small with a fusion head. Scalars inject at the BOTTLENECK, "
        "never broadcast -- ERA5-Land is ~11 km, so spreading one value over "
        "65,536 pixels wastes them and hands the model a patch identifier.",
  TRAINING="Four arms at a fixed band set: CODES (the CFFDRS baseline), "
           "HISTORY, BOTH, HISTORY_DIMENSIONLESS.",
  EVALUATION="auc_px, paired per fold. Read STRATIFIED BY LATITUDE BAND: the "
             "DMC and DC day-length factors are tabulated for ~46 N while "
             "Canada spans 42-83, so the claim is about high latitude and a "
             "pooled number cannot test it.",
  OUTPUT="Whether raw history beats the codes, and whether any gain is "
         "latitude-dependent.",
  CONTROLS="HISTORY_DIMENSIONLESS carries no absolute scale. If BOTH beats "
           "CODES but this does not, the gain came from absolute level -- "
           "which is latitude, i.e. geography in a weather costume. Plus the "
           "weather permutation test: shuffled weather must sit at chance.",
  STATUS="Scalars now packed. 198/1834 train tiles are NaN (cloud, water and "
         "bare scenes, where ERA5-Land has no land pixel) and must be "
         "filtered before any fusion arm runs.",
 ),
 dict(
  slug="06_ecology_arm", tier=SOON, tier_name="NEEDS A RE-PACK",
  title="Band ranking against vegetation structure",
  question="Which bands retrieve vegetation structure -- the thing the "
           "instrument actually measures?",
  INPUT="279 ecology patches, stratified across 8 SCANFI land-cover classes, "
        "2020. Same 11-band pool.",
  LABELS="SCANFI, 18 channels per pixel: land cover, time since disturbance, "
         "crown closure, height, biomass, 6 species fractions, 5 nontreed "
         "classes. DENSE -- every pixel is labelled, against one sparse "
         "outcome per patch in the fire arm.",
  MODEL="TinyEcologyUNet, seven heads (one categorical, five continuous, one "
        "composition).",
  TRAINING="The same greedy-per-fold protocol, scored on the ecology heads.",
  EVALUATION="Per-head error, and the combined embedding quality. Reported "
             "per target, not pooled -- the heads have different units and "
             "averaging them would weight by scale.",
  OUTPUT="The PRIMARY band ranking. The brief ranks bands on the retrieval "
         "targets (T1-T4), with fire outcome as a later relevance check; "
         "this is that ranking.",
  CONTROLS="Same folds and frequency reporting. Disagreement with the fire "
           "arm is a finding about which target a band serves, not a problem.",
  STATUS="250/279 patches have SCANFI. The 29 refusals are a real coverage "
         "gap -- SCANFI's structural layers thin out in the southeast -- and "
         "the ecology set still needs tiling and packing.",
 ),
 dict(
  slug="07_scanfi_refresh", tier=SOON, tier_name="NEEDS A RE-PACK",
  title="Does a refreshed fuel map beat a static one?",
  question="CFFDRS consumes a fixed-vintage fuel layer. Is a current "
           "estimate worth more, and by how much per year of staleness?",
  INPUT="Three things on one grid per fire patch: (A) SCANFI 2020 "
        "reprojected -- the static layer an operational system uses; (B) "
        "Stage 1's prediction from that year's imagery -- the same variables, "
        "refreshed; (C) the NBAC outcome.",
  LABELS="NBAC, for the downstream fire task.",
  MODEL="The fire model, run twice: once given A, once given B. Identical "
        "otherwise.",
  TRAINING="Paired, same folds.",
  EVALUATION="The SLOPE against staleness, not the level. At gap 0 our "
             "estimate is a noisy copy of its own training target and should "
             "LOSE by roughly the retrieval error; at gap 3 it also carries "
             "three years of real change. disagreement(gap) - "
             "disagreement(0) isolates the change from a constant noise "
             "offset.",
  OUTPUT="Value of currency, per year of staleness. The mission's value "
         "proposition as a measurement rather than a claim.",
  CONTROLS="17 of 207 patches EXCLUDED as leaky: SCANFI 2020 postdates their "
           "fire and already carries the scar. Includes 8 confusers, which "
           "are imaged 3 years BEFORE their burn. Read within class -- 72 "
           "confusers sit at gap 0 and 72 fires at gap +3, so a whole-set "
           "contrast would read the class label as a staleness effect.",
  STATUS="SCANFI attached to all 292. Needs the Stage-1 model trained to "
         "produce B. UNRESOLVED: the pre-fire composite runs 1 April to 30 "
         "June, so an early ignition falls inside its own window -- needs "
         "NBAC start dates before a positive result is trusted.",
 ),
 dict(
  slug="08_swir_placement", tier=LATER, tier_name="NEEDS NEW DATA",
  title="Where do the four SWIR bands go?",
  question="The Mantis SWIR mode carries 4 bands in 1000-1750 nm. Which four?",
  INPUT="AVIRIS-NG ABoVE: 574 Canadian flight lines, 380-2510 nm at 5 nm, "
        "~5 m, 2017-2022. Free, Earthdata login only. Any candidate band set "
        "is synthesised by convolving a response onto the contiguous "
        "spectrum -- which is what rule 2 requires, and what a multispectral "
        "archive cannot provide.",
  LABELS="SCANFI and NBAC, both national rasters, so every footprint is "
         "labellable with machinery already running.",
  MODEL="tier2-small, as the band arms.",
  TRAINING="Greedy over a centre x FWHM grid inside the two usable "
           "sub-windows, 1000-1300 (clear of the O2 band at 1270) and "
           "1500-1750.",
  EVALUATION="auc_px and the ecology heads, same protocol.",
  OUTPUT="Four band centres and widths, with tolerances. The actual SWIR "
         "specification.",
  CONTROLS="WorldView-3's flown set (1209, 1572, 1661, 1730) as a positive "
           "benchmark: does an optimised set beat a real instrument's "
           "choices? Also settles 1209 vs 1240 -- water sensitivity traded "
           "against O2 margin.",
  STATUS="Not fetched. 228 lines were flown BEFORE a burn they overlap, "
         "which is the pre-fire case. Western Canada only: nothing east of "
         "-93.2 degrees, so no Quebec black spruce and no budworm fir.",
 ),
 dict(
  slug="09_hardware_cost", tier=LATER, tier_name="HARDWARE",
  title="What each band costs in fabric",
  question="The brief asks for value per MARGINAL COST. This is the "
           "denominator.",
  INPUT="Each candidate model, converted for real -- not estimated.",
  LABELS="None. This measures the implementation, not a retrieval.",
  MODEL="All nine presets, 15k to 87M parameters, at 3 / 6 / 10 / 11 / 96 "
        "input channels.",
  TRAINING="None. hls4ml conversion, FINN at W8A8 and W4A4, Vitis AI DPU "
           "subgraph counts.",
  EVALUATION="BRAM, DSP, LUT and latency per preset per channel count. The "
             "BRAM law is ceil(width_bits/18) x ceil(depth/1024) per stream "
             "and matched two synthesis runs to the exact BRAM18K.",
  OUTPUT="Resources as a function of input channel count, which is what "
         "turns a band ranking into a band DECISION.",
  CONTROLS="Feasibility is a reported axis, not a filter. A set that does "
           "not fit is reported as not fitting, not dropped.",
  STATUS="Runs beside the band work; needs no data. Standing blocker "
         "unrelated to bands: the main core is at 405% BRAM and does not fit "
         "ZU7EV regardless of which bands win.",
 ),
]


def _wrap(text, width):
    out = []
    for para in text.split(" · "):
        out.extend(textwrap.wrap(para, width))
    return out


def card(spec) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK,
                         "figure.facecolor": FIG_BG,
                         "savefig.facecolor": FIG_BG})

    WRAP = 86
    blocks = [(f, _wrap(spec[f], WRAP)) for f in FIELDS]
    body = sum(len(v) for _, v in blocks)
    H, GAP = 0.185, 0.16
    total = 1.5 + body * H + len(blocks) * GAP

    fig, ax = plt.subplots(figsize=(11.6, total), facecolor=FIG_BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, total)
    ax.axis("off")

    y = total - 0.35
    ax.text(0, y, spec["title"], color=INK_BRIGHT, fontsize=14, va="center")
    ax.add_patch(FancyBboxPatch((84, y - 0.14), 16, 0.30,
                                boxstyle="round,pad=0.02",
                                facecolor=spec["tier"], edgecolor="none",
                                alpha=0.9))
    ax.text(92, y + 0.01, spec["tier_name"], color="#10131a", fontsize=7.8,
            ha="center", va="center", weight="bold")
    y -= 0.38
    for ln in textwrap.wrap(spec["question"], 100):
        ax.text(0, y, ln, color=MUTED, fontsize=9.4, va="center",
                style="italic")
        y -= 0.24
    y -= 0.12
    ax.plot([0, 100], [y, y], color=SPINE, lw=1.0)
    y -= 0.22

    for field, lines in blocks:
        box_h = len(lines) * H + 0.10
        ax.add_patch(FancyBboxPatch((0, y - box_h + 0.06), 100, box_h,
                                    boxstyle="round,pad=0.01",
                                    facecolor=ROW_BG, edgecolor="none",
                                    zorder=1))
        ax.text(1.2, y - 0.06, field, color=spec["tier"], fontsize=8.4,
                va="top", weight="bold", zorder=2)
        for i, ln in enumerate(lines):
            ax.text(16, y - 0.06 - i * H, ln, color=INK, fontsize=8.6,
                    va="top", zorder=2)
        y -= box_h + GAP

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{spec['slug']}.png"
    fig.savefig(out, dpi=160, facecolor=FIG_BG, bbox_inches="tight")
    plt.close(fig)
    return out


def main() -> int:
    for spec in CARDS:
        print(f"  wrote {card(spec)}")
    print()
    print(f"{len(CARDS)} cards -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
