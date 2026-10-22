"""The experiment register: one entry per experiment, E-1 to E-31.

SINGLE SOURCE OF TRUTH. `docs/EXPERIMENTS.md` and
`docs/results/figures/experiment_plan.png` are both generated from this
module, so the table and the figure cannot drift from each other -- which
they did, the figure once carrying a count of AVIRIS lines that three
documents repeated and the data contradicted.

Each entry records four things the previous plan left implicit:

    independent   what the experiment VARIES, and only that
    dependent     what is MEASURED, so a result is a number and not an
                  impression
    conclusion    what could be concluded either way. An experiment whose
                  null result teaches nothing is not worth GPU time, and
                  writing this field is how that gets noticed before the
                  queue rather than after
    state         whether it can run today, and if not, what is missing

RUNNERS ARE CHECKED. Every command named here exists; where nothing runs an
experiment the runner is "--", which makes this register the to-write list
as well as the plan.

NUMBERING. E-1 to E-31 replace an earlier, narrower E-1 to E-4 that came
out of the CFFDRS gap audit. Those four are now E-17 to E-20, and
docs/CFFDRS_GAPS.md points at the new ids. Two numbering schemes for one
set of experiments is worse than renumbering once.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: Feasibility states, in the order a reader should care about them.
#: `label` is for the table, `colour` for the figure.
STATES: dict[str, dict[str, str]] = {
    "RUNNABLE": {
        "label": "Runnable now",
        "detail": "data packed and staged; nothing missing",
        "colour": "#52a675",
    },
    "PARTIAL": {
        "label": "Partial result",
        "detail": "some folds or arms have completed; the rest are blocked",
        "colour": "#7fb069",
    },
    "NEEDS_CODE": {
        "label": "Needs code",
        "detail": "no new data; a runner or a flag has to be written",
        "colour": "#e8973f",
    },
    "NEEDS_PACK": {
        "label": "Needs a pack",
        "detail": "data held but not tiled, packed or transferred",
        "colour": "#d98c3f",
    },
    "NEEDS_DATA": {
        "label": "Needs new data",
        "detail": "free to obtain, not yet held",
        "colour": "#9b7fd4",
    },
    "NEEDS_PURCHASE": {
        "label": "Needs purchase",
        "detail": "commercial or licensed data",
        "colour": "#6f6fae",
    },
    "BLOCKED": {
        "label": "No label exists",
        "detail": "cannot be run with any amount of work on data we hold",
        "colour": "#d1495b",
    },
}

GROUPS = (
    "Band selection",
    "Controls",
    "Index baselines",
    "Covariates",
    "CFFDRS gaps",
    "Hyperspectral",
    "Hardware",
    "Out of reach",
)


@dataclass(frozen=True)
class Experiment:
    eid: str
    name: str
    group: str
    independent: str
    dependent: str
    conclusion: str
    state: str
    runner: str = "--"
    gap: str = ""
    blocker: str = ""
    note: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)

    @property
    def runnable(self) -> bool:
        return self.state in ("RUNNABLE", "PARTIAL")


#: Every dependent variable here is read the same way -- see the
#: standing caveat in the generated document -- so the phrase is
#: short enough to sit in a table cell and the pairing is stated
#: once rather than twenty times.
_M = "auc_px, scenario-held-out folds"

EXPERIMENTS: tuple[Experiment, ...] = (
    # ───────────────────────────── Band selection ────────────────────────
    Experiment(
        "E-1", "VNIR band selection", "Band selection",
        independent="which 6 of the 10 Sentinel-2 bands in 400-1000 nm",
        dependent=_M + ", per set size k",
        conclusion="Names the six bands for the Mantis MS mode. The one "
                   "complete answer the packed data can give today, and it "
                   "settles one of the three sensor modes outright.",
        state="RUNNABLE",
        runner="sweep_arms.sh ARMS=vnir",
        tags=("primary",),
    ),
    Experiment(
        "E-2", "All-11 greedy", "Band selection",
        independent="unconstrained choice over all 11 packed bands",
        dependent=_M + "; the k at which B11 first enters",
        conclusion="If greedy reaches for B11 early, the SWIR chain earns a "
                   "slot on fire-outcome evidence. If it never does, that is "
                   "weak evidence against, not strong -- one SWIR band "
                   "cannot test a four-band mode.",
        state="RUNNABLE",
        runner="sweep_arms.sh ARMS=all11",
    ),
    Experiment(
        "E-3", "Forced-SWIR delta", "Band selection",
        independent="B11 held in the set vs the VNIR-only set, matched k",
        dependent="the paired difference in " + _M,
        conclusion="The marginal value of one SWIR band at equal band count. "
                   "A lower bound on the SWIR chain: we hold 1 band in the "
                   "window, the sensor would carry 4.",
        state="RUNNABLE",
        runner="sweep_arms.sh ARMS=vnir_swir",
    ),
    Experiment(
        "E-4", "SWIR-only floor", "Band selection",
        independent="B11 alone, no VNIR band",
        dependent=_M,
        conclusion="The third sensor option -- SWIR instead of MS -- had no "
                   "number. Structurally a SWIR-only set forms 0 of 12 "
                   "catalogue indices and 0 ECVs, measured; this says what a "
                   "LEARNED model does with it anyway, which rule 4 treats "
                   "as the real question.",
        state="RUNNABLE",
        runner="sweep_arms.sh ARMS=swir_only",
        note="A quarter of the sensor. Read strictly as a floor.",
    ),
    Experiment(
        "E-5", "Leave-one-out band value", "Band selection",
        independent="each band removed in turn from the chosen set",
        dependent="the drop in " + _M + " on removing each band",
        conclusion="Per-band value CONDITIONAL on the rest, which is the "
                   "only kind that means anything when bands are "
                   "near-duplicates. Cannot see redundancy: B8 and B8A are "
                   "23 nm apart, so each may look worthless while the pair "
                   "is essential.",
        state="RUNNABLE",
        runner="sweep_bands.py --leave-one-out (rides in E-1..E-4)",
    ),
    Experiment(
        "E-6", "Selection stability", "Band selection",
        independent="the same search re-run inside each of 6 location folds",
        dependent="the fraction of folds that select each band at each k",
        conclusion="6/6 is a finding, 3/6 is a coin flip. Without it a "
                   "single fold's ranking would be reported as the ranking.",
        state="RUNNABLE",
        runner="pool_bands.py (after E-1..E-4)",
    ),
    Experiment(
        "E-7", "Resolution requirement", "Band selection",
        independent="ground sample distance: 20 / 40 / 80 m, coarsening only",
        dependent=_M + " vs GSD",
        conclusion="How much resolution the retrieval needs — a mission "
                   "requirement, and sharper than it looks: the Mantis MS "
                   "mode is 32 m at 500 km and 39.7 m at 620 km, so ~40 m is "
                   "the real operating point and our 20 m results are "
                   "optimistic.",
        state="NEEDS_CODE",
        runner="--",
        blocker="data.coarsen() exists; no CLI flag on sweep_bands.py",
    ),

    # ─────────────────────────────── Controls ────────────────────────────
    Experiment(
        "E-8", "Label independence control", "Controls",
        independent="the label source: NBAC perimeters vs VIIRS thermal",
        dependent="change in the band ranking and in " + _M,
        conclusion="A band whose value collapses when the label becomes "
                   "thermal was exploiting the label, not reading fuel. "
                   "VNP14 keys off 4 and 11 um emission, so it cannot share "
                   "information with 400-1750 nm reflectance.",
        state="RUNNABLE",
        runner="sweep_bands.sh LABEL=vnp14",
        tags=("control",),
    ),
    Experiment(
        "E-9", "Lightning cohort", "Controls",
        independent="fires filtered to NFDB CAUSE = lightning",
        dependent=_M + ", restricted cohort",
        conclusion="Human ignitions carry a roads-and-settlement signal that "
                   "a model can read off the imagery instead of the fuel. If "
                   "the ranking holds on lightning fires only, it is about "
                   "fuel.",
        state="NEEDS_CODE",
        runner="--",
        blocker="labels.is_lightning() exists; no cohort filter at pack time",
        tags=("control",),
    ),
    Experiment(
        "E-10", "Negative control", "Controls",
        independent="a deliberately redundant band pool",
        dependent=_M,
        conclusion="Sanity. If a deliberately poor set scores well, the "
                   "pipeline is broken and no other result here is "
                   "interpretable.",
        state="RUNNABLE",
        runner="sweep_bands.sh BANDS=... (config/bands/negative_control.yaml)",
        tags=("control",),
    ),

    # ────────────────────────── Index baselines ──────────────────────────
    Experiment(
        "E-11", "Greenness vs moisture indices", "Index baselines",
        independent="the index family given to the model: greenness "
                    "(NDVI, EVI, VARI, NDRE) / moisture (NDMI, MSI) / both / "
                    "raw bands",
        dependent="the paired difference in " + _M + ", against greenness",
        conclusion="THE MISSION'S CENTRAL CLAIM. FWI2025 accepts grassland "
                   "curing from remote sensing and its current option is "
                   "NDVI-based GREENNESS -- a proxy for dryness. Greenness "
                   "tracks moisture only while they co-vary seasonally, and "
                   "a conifer stand stays green as it dries. If moisture "
                   "beats greenness on a burn outcome, that is a concrete, "
                   "quantified recommendation to the operational system. If "
                   "`both` does not beat `greenness`, the 1610 nm moisture "
                   "signal adds nothing this label can see -- also "
                   "publishable.",
        state="RUNNABLE",
        runner="sweep_indices.sh",
        gap="FWI2025 curing input",
        note="Primary contrast is `both` vs `greenness`: a strict superset, "
             "so a positive result is unambiguous. Tests ONE moisture index "
             "at 1610 nm -- NDWI_Gao needs 1240 nm and NMDI/NDTI/NBR need "
             "SWIR2, none of which Sentinel-2 carries.",
        tags=("primary",),
    ),
    Experiment(
        "E-12", "Index baseline vs learned bands", "Index baselines",
        independent="hand-built indices vs the learned model on raw bands",
        dependent="the paired difference in " + _M,
        conclusion="If the learned model beats every index family by a wide "
                   "margin, the recommendation to CFFDRS is to take BANDS "
                   "rather than indices — a finding about the system's "
                   "interface, not only about our sensor. The heritage "
                   "baseline rule 4 asks for.",
        state="RUNNABLE",
        runner="sweep_indices.sh ARMS=raw,both",
    ),

    # ─────────────────────────────── Covariates ──────────────────────────
    Experiment(
        "E-13", "Weather representation", "Covariates",
        independent="the scalar columns the fusion head sees: FWI codes / "
                    "our 12 compressed history features / both / "
                    "dimensionless history",
        dependent="the paired difference in " + _M + ", against codes",
        conclusion="Does our compression of 91 days beat the FWI System's? "
                   "CODES is CFFDRS as it stands and is the baseline. If "
                   "BOTH beats CODES but DIMENSIONLESS does not, the gain "
                   "came from absolute level, which at 45-70 N is latitude "
                   "-- geography wearing a weather costume.",
        state="RUNNABLE",
        runner="sweep_covariates.sh SETS=weather",
        note="No repack: the pack carries weather_arm=both, the union, so "
             "each arm is a column mask.",
    ),
    Experiment(
        "E-14", "Fusion architecture", "Covariates",
        independent="how weather enters: not at all / two-head late / "
                    "bottleneck",
        dependent="the paired difference in " + _M,
        conclusion="What the CFFDRS-shaped separation of fuel and weather "
                   "costs or buys against early fusion. rasters_only is the "
                   "no-weather floor and is also the configuration the band "
                   "ranking is read from, which ties the two together.",
        state="RUNNABLE",
        runner="sweep_covariates.sh SETS=fusion",
    ),
    Experiment(
        "E-15", "Imagery vs the FBP formula", "Covariates",
        independent="the FBP foliar-moisture scalar alone vs that scalar "
                    "plus all 9 surface bands",
        dependent="the paired difference in " + _M,
        conclusion="G1 restated into something testable: does imagery carry "
                   "foliar-moisture information the FBP equation does not? "
                   "It CANNOT say our spectral estimate beats theirs -- that "
                   "needs an LFMC label (E-29).",
        state="PARTIAL",
        runner="sweep_covariates.sh SETS=g1",
        gap="G1 foliar moisture is computed, never observed",
        note="The imagery-free floor has run: 6/6 folds, auc_px 0.5396-0.7660, "
             "mean 0.642. Its counterpart was lost to the device bug, so the "
             "contrast is still missing.",
    ),
    Experiment(
        "E-16", "FMC arms", "Covariates",
        independent="baseline / measured / augment foliar moisture",
        dependent="(none obtainable)",
        conclusion="NOTHING. fmc_measured is read in four places and written "
                   "in none, so all three arms reduce to the FBP equation "
                   "and would return three identical numbers looking like "
                   "'no difference'. Listed so it is not run by mistake.",
        state="BLOCKED",
        runner="-- (do not run)",
        blocker="fmc_measured is never written; needs E-29",
    ),

    # ───────────────────────────── CFFDRS gaps ───────────────────────────
    Experiment(
        "E-17", "Station-density stratification", "CFFDRS gaps",
        independent="distance from each patch to the nearest fire-weather "
                    "station",
        dependent="the imagery increment in " + _M + ", stratified by that "
                  "distance",
        conclusion="CFS names thin station density as a limit on model "
                   "accuracy (GLC-X-42 7.2). Fuel moisture is the integral "
                   "of weather, so satellite fuel state should be worth most "
                   "where the weather grid is weakest -- the north, which is "
                   "also where most of the area burns.",
        state="NEEDS_DATA",
        runner="--",
        blocker="CWFIS station locations not held; ERA5-Land says nothing "
                "about where the observing stations are",
        gap="G3 station density",
    ),
    Experiment(
        "E-18", "Snow-off startup", "CFFDRS gaps",
        independent="FWI start date: per-pixel NDSI snow-off vs our flat "
                    "90-day spinup",
        dependent="change in the FWI codes, and " + _M,
        conclusion="Fixes our own defect first: the spinup starts ~1 April, "
                   "which at 55-67 N is frozen and snow-covered, so the "
                   "recursion accumulates weeks of spurious drying and the "
                   "error scales with latitude. Then it tests whether a "
                   "per-pixel snow-off date beats the regional rule.",
        state="NEEDS_CODE",
        runner="--",
        blocker="an Earth Engine NDSI reduction over the S2 collection; no "
                "new imagery",
        gap="G4 snow-off keyed by regional rule",
    ),
    Experiment(
        "E-19", "Latitude-banded weather", "CFFDRS gaps",
        independent="the E-13 weather contrast, split by latitude band",
        dependent="the paired difference per band",
        conclusion="DMC and DC day-length factors are tabulated for ~46 N "
                   "while Canada spans 42-83. A pooled number cannot "
                   "distinguish 'history is better' from 'history is better "
                   "at high latitude', which is the actual claim.",
        state="NEEDS_CODE",
        runner="--",
        blocker="a latitude-split flag on report_arms.py or pool_bands.py",
        gap="G5 day-length tabulated for ~46 N",
    ),
    Experiment(
        "E-20", "Weather staleness", "CFFDRS gaps",
        independent="the age of the weather at inference: 0 / 24 / 48 / 72 h "
                    "/ 7 d",
        dependent=_M + " vs weather age, per weather arm",
        conclusion="Every FWI code is defined on a same-day noon "
                   "observation and a daily uplink cannot supply one. The "
                   "input drift is already measured (DC 8.2% over three days "
                   "against ISI's 89.9%) and fwi.py reasons from it to a "
                   "recommendation -- BUI best, FWI worst. Drift in a "
                   "feature is not loss in a prediction, and this measures "
                   "the half nobody has.",
        state="NEEDS_PACK",
        runner="--",
        blocker="lagged FWI sidecars: an ERA5 pass over data already held, "
                "then a repack",
        gap="G7 CFFDRS assumes same-day observations",
        note="Train once, score at each lag: one model, five scores. The "
             "leakage guard makes an earlier target date strictly safer.",
    ),
    Experiment(
        "E-21", "Fuel-layer refresh", "CFFDRS gaps",
        independent="the static 2020 SCANFI layer vs our current estimate, "
                    "against staleness gap",
        dependent="the SLOPE of " + _M + " against staleness, not the level",
        conclusion="FBP consumes a fixed-vintage fuel grid while fuel type "
                   "changes with harvest, insects, fire and regrowth. The "
                   "slope is the estimator because at gap 0 our estimate is "
                   "a noisy copy of its own training target and would lose "
                   "on noise alone.",
        state="NEEDS_PACK",
        runner="--",
        blocker="needs E-22 first (the ecology model), then the refreshed "
                "estimate attached",
        gap="G2 fuel-type layer is a fixed vintage",
    ),
    Experiment(
        "E-22", "Ecology arm", "CFFDRS gaps",
        independent="the same band searches, against SCANFI structure "
                    "instead of a burn outcome",
        dependent="per-pixel error on cover, closure, height, biomass, "
                  "species",
        conclusion="THE PRIMARY BAND RANKING. Dense per-pixel labels rather "
                   "than one sparse outcome per patch, so it has orders of "
                   "magnitude more signal per scene than the fire arm and "
                   "measures what the bands actually retrieve rather than "
                   "what correlates with ignition.",
        state="NEEDS_PACK",
        runner="train_ecology.sh",
        blocker="279 patches on disk, never tiled or packed; needs a pack "
                "and a second transfer",
        tags=("primary",),
    ),

    # ───────────────────────────── Hyperspectral ─────────────────────────
    Experiment(
        "E-23", "SWIR band placement", "Hyperspectral",
        independent="any 4 centres and widths in 1003-1359 and 1414-1749 nm "
                    "(140 usable channels)",
        dependent="retrieval error per candidate set",
        conclusion="THE SWIR SPECIFICATION. Sentinel-2 has one band in that "
                   "window and the mode carries four: four cannot be chosen "
                   "from one. Only a contiguous source can answer it.",
        state="NEEDS_DATA",
        runner="fetch_aviris.py + ingest_aviris.py",
        blocker="3 of 42 pre-fire lines on disk, 0 ingested",
        note="Grid measured from AVIRIS-NG's own bad-band list (A-22), which "
             "puts the water-vapour gap at 1364-1408 nm -- narrower than "
             "assumed, so 1300-1359 and 1414-1500 were being excluded for "
             "no reason.",
    ),
    Experiment(
        "E-24", "1209 vs 1240 nm", "Hyperspectral",
        independent="WorldView-3's flown centre against Gao's NDWI band",
        dependent="retrieval error, and O2 absorption margin",
        conclusion="Water sensitivity traded against O2 margin. The "
                   "validator flagged the conflict; nobody has measured it.",
        state="NEEDS_DATA",
        runner="ingest_aviris.py --mode both",
        blocker="same as E-23",
    ),
    Experiment(
        "E-25", "Spectral resolution: HS vs MS", "Hyperspectral",
        independent="140 SWIR channels at 5 nm vs the best 4-6 broad bands",
        dependent="retrieval error vs channel count",
        conclusion="What spectral RESOLUTION buys, which decides the Mantis "
                   "HS mode. Cannot be faked: ten Sentinel-2 bands cannot be "
                   "interpolated into ninety-six, and rule 2 forbids trying.",
        state="NEEDS_DATA",
        runner="ingest_aviris.py, then sweep_bands.py",
        blocker="same as E-23",
    ),
    Experiment(
        "E-26", "Conditional large fire", "Hyperspectral",
        independent="burned area > 100 ha, conditional on having burned",
        dependent=_M + " on the conditional task",
        conclusion="36% base rate, and 97% of area burned is in the tail. "
                   "Conditioning on ignition removes the weather-and-chance "
                   "component, leaving a fuel-dominated target -- which is "
                   "what the sensor can actually see.",
        state="NEEDS_CODE",
        runner="--",
        blocker="an NBAC area filter at pack time",
    ),

    # ─────────────────────────────── Hardware ────────────────────────────
    Experiment(
        "E-27", "Cost per input channel", "Hardware",
        independent="input channel count: 3 / 6 / 10 / 11 / 96",
        dependent="BRAM, DSP, LUT and latency from a real conversion",
        conclusion="The MARGINAL COST denominator. The brief asks for value "
                   "per marginal cost, and without this the ranking has a "
                   "numerator only. Stream BRAM is "
                   "ceil(width/18) x ceil(depth/1024), so width never stops "
                   "paying.",
        state="RUNNABLE",
        runner="sweep_architecture.py --widths",
    ),
    Experiment(
        "E-28", "Co-registration tolerance", "Hardware",
        independent="sub-pixel VNIR/SWIR shift injected at hard edges",
        dependent="retrieval error vs shift",
        conclusion="A number for the requirements table. The dichroic makes "
                   "this small, not absent, and snow/forest boundaries are "
                   "the flagged engineering risk.",
        state="NEEDS_CODE",
        runner="--",
        blocker="no shift-injection harness",
    ),

    # ────────────────────────────── Out of reach ─────────────────────────
    Experiment(
        "E-29", "T1 live foliar moisture", "Out of reach",
        independent="LFMC, the brief's lead retrieval target",
        dependent="RMSE against gravimetric LFMC",
        conclusion="Would make G1's STRONG claim testable -- that a spectral "
                   "estimate beats the FBP equation -- and unblock E-16. "
                   "Globe-LFMC 2.0 is fetched and measured: 2,884 usable "
                   "records at 83 sites, no Canadian ones, and C-2 black "
                   "spruce has 51. It carries no spectra, so each record "
                   "must be paired with a Sentinel-2 acquisition.",
        state="NEEDS_CODE",
        runner="--",
        blocker="Globe-LFMC held; the S2 pairing pipeline is unwritten "
                "(Phase 6a), and PROSAIL for simulated labels is not "
                "installed (Phase 1)",
        gap="G1 strong form",
    ),
    Experiment(
        "E-30", "T2 curing / NPV fraction", "Out of reach",
        independent="grass curing fraction",
        dependent="error against field curing",
        conclusion="The other half of the FWI2025 curing input. Blocked "
                   "three ways: no curing label anywhere in our data, no "
                   "grassland in the ecology set, and NDLI needs 1754 nm, "
                   "past the standard-InGaAs cutoff.",
        state="BLOCKED",
        runner="--",
        blocker="no label, no grassland, and the band is past the detector",
    ),
    Experiment(
        "E-31", "Fire occurrence prediction", "Out of reach",
        independent="ignition probability per cell-day",
        dependent="(out of scope)",
        conclusion="Parked by decision. Recorded because the argument is "
                   "strong: FOP runs on 20 km cells, and a 20 m imager "
                   "supplies the within-cell distribution a coarse model "
                   "structurally cannot have -- 10^6 pixels per cell. The "
                   "product that implies is a distribution summary, not a "
                   "mean.",
        state="BLOCKED",
        runner="-- (out of scope)",
        blocker="out of scope by decision; needs lightning strike data",
        gap="G6 FOP cannot see within its cells",
    ),
)


def by_id(eid: str) -> Experiment:
    for e in EXPERIMENTS:
        if e.eid == eid:
            return e
    raise KeyError(eid)


def by_group() -> dict[str, list[Experiment]]:
    out: dict[str, list[Experiment]] = {g: [] for g in GROUPS}
    for e in EXPERIMENTS:
        out[e.group].append(e)
    return {g: v for g, v in out.items() if v}


def by_state() -> dict[str, list[Experiment]]:
    out: dict[str, list[Experiment]] = {s: [] for s in STATES}
    for e in EXPERIMENTS:
        out[e.state].append(e)
    return {s: v for s, v in out.items() if v}


def runnable() -> list[Experiment]:
    return [e for e in EXPERIMENTS if e.runnable]


def counts() -> dict[str, int]:
    return {s: len(v) for s, v in by_state().items()}
