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
    #: A falsifiable PREDICTION, with the condition that would refute it.
    #: CLAUDE.md is explicit that the study's job is to test the brief's
    #: hypotheses rather than confirm them, so each one is written to be
    #: capable of being wrong and says what wrong would look like. Where a
    #: prediction comes from the brief (H1, H2, H3) it is attributed; the
    #: rest are this study's own and carry no more authority than that.
    hypothesis: str = ""
    runner: str = "--"
    gap: str = ""
    blocker: str = ""
    note: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)
    #: What one task asks Narval for, derived by scripts/narval_resources.py
    #: in Fire_Risk_FW from MEASURED timing (122 s per 35-epoch fit). A test
    #: checks that any --time named here is what the runner's wrapper asks.
    resources: str = ""

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
        hypothesis="Red-edge earns a slot: the best six include at least one of "
                   "B5/B6/B7 and exclude both 60 m atmospheric bands (B1, B9). "
                   "WRONG IF an atmospheric band survives into the best six, which "
                   "would say the ranking is reading haze rather than vegetation.",
        independent="which 6 of the 10 Sentinel-2 bands in 400-1000 nm",
        dependent=_M + ", per set size k",
        conclusion="Names the six bands for the Mantis MS mode. The one "
                   "complete answer the packed data can give today, and it "
                   "settles one of the three sensor modes outright.",
        state="RUNNABLE",
        runner="sweep_arms.sh ARMS=vnir",
        tags=("primary",),
        resources="49 fits/task x 6 tasks; est 2:05; --time=4:30:00 --mem=16G --cpus-per-task=12 "
                  "--gpus=a100:1",
    ),
    Experiment(
        "E-2", "All-11 greedy", "Band selection",
        hypothesis="B11 enters by k=3, because the NIR/SWIR contrast is the "
                   "strongest single moisture signal available. WRONG IF it has "
                   "not entered by k=7, which would be weak evidence against the "
                   "SWIR chain -- weak, because one band cannot stand in for four.",
        independent="unconstrained choice over all 11 packed bands",
        dependent=_M + "; the k at which B11 first enters",
        conclusion="If greedy reaches for B11 early, the SWIR chain earns a "
                   "slot on fire-outcome evidence. If it never does, that is "
                   "weak evidence against, not strong -- one SWIR band "
                   "cannot test a four-band mode.",
        state="RUNNABLE",
        runner="sweep_arms.sh ARMS=all11",
        resources="60 fits/task x 6 tasks; est 2:32; --time=5:30:00 --mem=16G --cpus-per-task=12 "
                  "--gpus=a100:1",
    ),
    Experiment(
        "E-3", "Forced-SWIR delta", "Band selection",
        hypothesis="Positive but small: under +0.02 auc_px. One band in the window "
                   "is a poor proxy for a four-band mode, so a large gain would be "
                   "surprising and a null is not disqualifying.",
        independent="B11 held in the set vs the VNIR-only set, matched k",
        dependent="the paired difference in " + _M,
        conclusion="The marginal value of one SWIR band at equal band count. "
                   "A lower bound on the SWIR chain: we hold 1 band in the "
                   "window, the sensor would carry 4.",
        state="RUNNABLE",
        runner="sweep_arms.sh ARMS=vnir_swir",
        resources="51 fits/task x 6 tasks; est 2:10; --time=4:30:00 --mem=16G --cpus-per-task=12 "
                  "--gpus=a100:1",
        note="Read through report_arms.py's MATCHED-k section: vnir_swir and vnir are paired rung "
             "by rung, not at their deepest rungs, which would set k=7 against k=6.",
    ),
    Experiment(
        "E-4", "SWIR-only floor", "Band selection",
        hypothesis="Clearly above chance and clearly below the VNIR set. The water "
                   "features at 1200 and 1600 nm are physically present, so a "
                   "learned model should find something; without the NIR anchor it "
                   "cannot normalise for canopy structure or illumination. WRONG "
                   "IF it matches the VNIR set, which would make the MS chain "
                   "arguable.",
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
        resources="1 fit/task x 6 tasks; est 0:05; --time=0:30:00 --mem=16G --cpus-per-task=12 "
                  "--gpus=a100:1",
    ),
    Experiment(
        "E-5", "Leave-one-out band value", "Band selection",
        hypothesis="Every individual drop is small, because the pool is redundant. "
                   "B8 and B8A in particular each look worthless while the pair is "
                   "not: leave-one-out cannot see mutual substitution, and reading "
                   "a small drop as 'this band does not matter' is the "
                   "trap. WRONG IF any single removal costs more than "
                   "about 0.02, which would mean the pool is far less "
                   "redundant than the near-duplicate pairs suggest and "
                   "the chosen set is already minimal.",
        independent="each band removed in turn from the chosen set",
        dependent="the drop in " + _M + " on removing each band",
        conclusion="Per-band value CONDITIONAL on the rest, which is the "
                   "only kind that means anything when bands are "
                   "near-duplicates. Cannot see redundancy: B8 and B8A are "
                   "23 nm apart, so each may look worthless while the pair "
                   "is essential.",
        state="RUNNABLE",
        runner="sweep_bands.py --leave-one-out (rides in E-1..E-4)",
        resources="no separate job: rides inside E-1 to E-3",
    ),
    Experiment(
        "E-6", "Selection stability", "Band selection",
        hypothesis="The top two or three bands are selected in 6/6 folds and the "
                   "tail is unstable. WRONG IF even the top band swings, which "
                   "would mean the ranking is fold noise and no k is reportable.",
        independent="the same search re-run inside each of 6 location folds",
        dependent="the fraction of folds that select each band at each k",
        conclusion="6/6 is a finding, 3/6 is a coin flip. Without it a "
                   "single fold's ranking would be reported as the ranking.",
        state="RUNNABLE",
        runner="pool_bands.py (after E-1..E-4)",
        resources="no job: pool_bands.py, minutes, on a login node",
    ),
    Experiment(
        "E-7", "Resolution requirement", "Band selection",
        hypothesis="Graceful degradation from 20 to 40 m and a sharper fall "
                   "by 80 m. WRONG IF 20 -> 40 m already costs materially, "
                   "which matters more than it sounds: the Mantis MS mode is "
                   "32 m at 500 km, so our 20 m results would overstate what "
                   "the sensor delivers.",
        independent="ground sample distance 20 / 40 / 80 m, in 'pixels' mode: "
                    "pooled then re-expanded, so INFORMATION is degraded "
                    "while the tile keeps its shape",
        dependent=_M + " vs GSD, paired against 20 m",
        conclusion="How much resolution the retrieval needs -- a mission "
                   "requirement. The Mantis MS mode is 32 m at 500 km and "
                   "39.7 m at 620 km, so ~40 m is the real operating point "
                   "and every 20 m result in this register is optimistic. "
                   "This is the information cost only; the pixel-count cost "
                   "(memory, latency) is E-27's.",
        state="RUNNABLE",
        runner="sweep_axes.sh SETS=gsd",
        note="'extent' mode (shrink the tile) is refused: it shrinks the "
             "input but not the mask, and the loss raises on the first batch. "
             "As first wired it would have crashed every 40 m and 80 m run.",
        resources="1 fit/task x 18 tasks; est 0:05; --time=0:30:00 --mem=16G --cpus-per-task=12 "
                  "--gpus=a100:1",
    ),

    # ─────────────────────────────── Controls ────────────────────────────
    Experiment(
        "E-8", "Label independence control", "Controls",
        hypothesis="The ranking is largely preserved. WRONG IF B11's value "
                   "collapses specifically -- that would say it was reading "
                   "NBR-like information shared with the perimeter "
                   "delineation rather than fuel, which is exactly the "
                   "circularity rule 3 exists to catch.",
        independent="the label source: NBAC perimeters vs VIIRS thermal",
        dependent="change in the band ranking and in " + _M,
        conclusion="A band whose value collapses when the label becomes "
                   "thermal was exploiting the label, not reading fuel. VNP14 "
                   "keys off 4 and 11 um emission, so it cannot share "
                   "information with 400-1750 nm reflectance.",
        state="NEEDS_PACK",
        runner="--",
        blocker="the thermal label is a per-patch scalar (_thermal.json) that "
                "is not in the pack, and nothing selects a training target "
                "other than the packed /mask",
        note="WAS MARKED RUNNABLE AND WAS VACUOUS. --label was validated, "
             "printed and recorded, and never read: LABEL=vnp14 would have "
             "trained on the packed mask and confirmed its own hypothesis. "
             "sweep_bands.py now refuses any --label that is not the pack's "
             "declared label_source.",
        tags=("control",),
    ),
    Experiment(
        "E-9", "Lightning cohort", "Controls",
        hypothesis="Absolute skill drops (fewer and harder cases) but the "
                   "band ranking holds. WRONG IF the ranking changes, which "
                   "would say human-ignition access signals -- roads, "
                   "settlement -- were driving it.",
        independent="fires filtered to NFDB CAUSE = lightning",
        dependent=_M + ", restricted cohort",
        conclusion="Human ignitions carry a roads-and-settlement signal that "
                   "a model can read off the imagery instead of the fuel. If "
                   "the ranking holds on lightning fires only, it is about "
                   "fuel.",
        state="NEEDS_DATA",
        runner="--",
        blocker="NFDB is not held -- there is no NFDB directory in "
                "Fire_Risk_Model/data. labels.is_lightning() exists but has "
                "nothing to read. Fetch NFDB, attach CAUSE per patch, then "
                "filter with sweep_bands.py --scenes's machinery",
        note="Was listed as 'needs code'; the code exists, the data does not.",
        tags=("control",),
    ),
    Experiment(
        "E-10", "Negative control", "Controls",
        hypothesis="The noise arm is within noise of 0.5, and the real-band "
                   "arm clearly beats it. WRONG IF the noise arm sits clearly "
                   "above 0.5: then a POSITIONAL PRIOR -- where burn tends to "
                   "sit in a tile, learnable from zero padding without "
                   "reading a band -- inflates every arm in this register, "
                   "and must be subtracted before any of them is quoted.",
        independent="the input: the 9 surface bands vs fresh Gaussian noise "
                    "of the same width",
        dependent=_M + " against chance, and against the real-band arm",
        conclusion="Sanity and calibration at once. Near 0.5: the pipeline "
                   "is sound and arms can be read at face value. Above it: "
                   "the excess is the floor every arm got for free, and it is "
                   "the number to subtract.",
        state="RUNNABLE",
        runner="sweep_axes.sh SETS=neg",
        note="REDESIGNED. The old control was 'a deliberately redundant band "
             "pool' with the hypothesis 'at or near chance', and those cannot "
             "both hold: every real Sentinel-2 band carries surface signal, "
             "and the YAML's four overlapping red bands cannot be built from a "
             "sensor with one red band. Its runner was 'BANDS=...', not a "
             "command. Run this set first.",
        tags=("control",),
        resources="1 fit/task x 12 tasks; est 0:05; --time=0:30:00 --mem=16G --cpus-per-task=12 "
                  "--gpus=a100:1",
    ),

    # ────────────────────────── Index baselines ──────────────────────────
    Experiment(
        "E-11", "Greenness vs moisture indices", "Index baselines",
        hypothesis="`both` beats `greenness` by a small but fold-consistent "
                   "margin, because direct water absorption at 1610 nm carries "
                   "information a greenness proxy cannot; and `moisture` (2 bands) "
                   "draws with `greenness` (5 bands). WRONG IF `both` does not "
                   "beat `greenness`, which would say the 1610 nm moisture signal "
                   "adds nothing this label can see -- a publishable null, and one "
                   "that would weaken the case for the SWIR chain considerably.",
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
        resources="1 fit/task x 24 tasks; est 0:05; --time=0:30:00 --mem=16G --cpus-per-task=12 "
                  "--gpus=a100:1",
    ),
    Experiment(
        "E-12", "Index baseline vs learned bands", "Index baselines",
        hypothesis="The learned model on raw bands beats every index family, "
                   "because an index is a fixed projection that discards "
                   "information a model could use. WRONG IF indices match it, "
                   "which would be a strong argument for shipping indices -- cheap "
                   "on an FPGA and interpretable to an operational user.",
        independent="hand-built indices vs the learned model on raw bands",
        dependent="the paired difference in " + _M,
        conclusion="If the learned model beats every index family by a wide "
                   "margin, the recommendation to CFFDRS is to take BANDS "
                   "rather than indices — a finding about the system's "
                   "interface, not only about our sensor. The heritage "
                   "baseline rule 4 asks for.",
        state="RUNNABLE",
        runner="sweep_indices.sh ARMS=raw,both",
        resources="shares E-11's runs",
    ),

    # ─────────────────────────────── Covariates ──────────────────────────
    Experiment(
        "E-13", "Weather representation", "Covariates",
        hypothesis="BOTH is within noise of CODES. The FWI codes already integrate "
                   "the same 91 days through a recursion tuned over decades, so "
                   "our 12 features are unlikely to extract much the codes have "
                   "not. WRONG IF BOTH wins clearly -- then check DIMENSIONLESS, "
                   "because a gain that disappears there came from absolute level, "
                   "which at 45-70 N is latitude wearing a weather costume.",
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
        resources="1 fit/task x 24 tasks; est 0:05; --time=0:30:00 --mem=16G --cpus-per-task=12 "
                  "--gpus=a100:1",
    ),
    Experiment(
        "E-14", "Fusion architecture", "Covariates",
        hypothesis="Both fusion variants beat rasters_only, and two_head is within "
                   "noise of bottleneck. The CFFDRS-shaped separation is expected "
                   "to cost little; if it costs a lot, the architecture argument "
                   "has to give way to the measurement. WRONG IF "
                   "rasters_only matches both, which would say the "
                   "weather scalars add nothing at this label and sample "
                   "size -- and would make E-13 moot.",
        independent="how weather enters: not at all / two-head late / "
                    "bottleneck",
        dependent="the paired difference in " + _M,
        conclusion="What the CFFDRS-shaped separation of fuel and weather "
                   "costs or buys against early fusion. rasters_only is the "
                   "no-weather floor and is also the configuration the band "
                   "ranking is read from, which ties the two together.",
        state="RUNNABLE",
        runner="sweep_covariates.sh SETS=fusion",
        resources="1 fit/task x 12 tasks (+ wx_both from E-13); est 0:05; --time=0:30:00 --mem=16G "
                  "--cpus-per-task=12 --gpus=a100:1",
        note="two_head is submitted once, as wx_both, and report_arms.py aliases it into the "
             "fusion family; without that alias the main contrast was never produced. The second "
             "baseline, bottleneck, tests the hypothesis's other clause.",
    ),
    Experiment(
        "E-15", "Imagery vs the FBP formula", "Covariates",
        hypothesis="Imagery plus the FMC scalar beats the scalar alone, "
                   "substantially. The FBP equation is a function of "
                   "latitude, longitude, elevation and date only -- it "
                   "carries no information about the stand -- so a null here "
                   "would be surprising, and would cast doubt on the imagery "
                   "rather than vindicate the formula.",
        independent="the FBP foliar-moisture scalar alone vs that scalar plus "
                    "all 9 surface bands",
        dependent="the paired difference in " + _M,
        conclusion="G1 restated into something testable: does imagery carry "
                   "foliar-moisture information the FBP equation does not? "
                   "It CANNOT say our spectral estimate beats theirs -- that "
                   "needs an LFMC label (E-29).",
        state="RUNNABLE",
        runner="sweep_covariates.sh SETS=g1",
        gap="G1 foliar moisture is computed, never observed",
        note="The imagery-free floor that ran (6/6 folds, auc_px 0.5396 to "
             "0.7660) was trained and scored on the dNBR pack, so it does NOT "
             "count: both halves must be rerun on the NBAC pack. The spread "
             "is still a fair picture of fold-to-fold variance.",
        resources="1 fit/task x 12 tasks; est 0:05; --time=0:30:00 --mem=16G --cpus-per-task=12 "
                  "--gpus=a100:1",
    ),
    Experiment(
        "E-16", "FMC arms", "Covariates",
        hypothesis="None. The arms are identical by construction, so no prediction "
                   "is possible and any apparent difference would be seed noise.",
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
        hypothesis="The imagery increment grows with distance to the nearest "
                   "station. Fuel moisture is the integral of weather, so a "
                   "satellite estimate should be worth most where the weather grid "
                   "is interpolated from furthest away -- the north, which is also "
                   "where most area burns.",
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
        hypothesis="Correcting the start date changes DC and DMC materially above "
                   "55 N and improves skill there, with little effect in the "
                   "south. Our flat 90-day spinup starts around 1 April into "
                   "frozen, snow-covered ground, so the spurious drying should "
                   "scale with latitude.",
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
        hypothesis="History beats codes at high latitude specifically, and "
                   "not in the south. The day-length factors are tabulated "
                   "for ~46 N, so the codes should be least trustworthy where "
                   "that assumption is furthest from the truth. WRONG IF the "
                   "gain is uniform across bands, which would make the "
                   "mechanism something other than day length.",
        independent="the E-13 weather contrast, scored separately in "
                    "0-55 / 55-60 / 60-90 N on the same trained models",
        dependent="the INTERACTION: (history - codes) in 60-90 N minus the "
                  "same in 0-55 N, paired by fold",
        conclusion="DMC and DC day-length factors are tabulated for ~46 N "
                   "while Canada spans 42-83. A pooled number cannot "
                   "distinguish 'history is better' from 'history is better "
                   "at high latitude', which is the actual claim -- so the "
                   "test is the interaction, not either band alone.",
        state="RUNNABLE",
        runner="sweep_covariates.sh SETS=weather",
        gap="G5 day-length tabulated for ~46 N",
        note="Bands hold 745 / 594 / 495 of the 1834 training tiles, so "
             "~80-125 per band per validation fold -- above the 25-tile "
             "floor below which a band is skipped rather than scored.",
        resources="shares E-13's runs; latitude scoring adds seconds",
    ),
    Experiment(
        "E-20", "Weather staleness", "CFFDRS gaps",
        hypothesis="Skill decays with weather age, fastest for CODES and slowest "
                   "for the dimensionless history. This is the testable half of a "
                   "claim fwi.py already makes from input drift alone (DC 8.2% "
                   "over three days against ISI's 89.9%). WRONG IF decay is flat, "
                   "which would mean a daily uplink costs nothing and the "
                   "slow-code argument is unnecessary.",
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
        hypothesis="A positive slope: the advantage of a refreshed estimate grows "
                   "with the staleness gap. At gap 0 our estimate should LOSE, "
                   "because it is a noisy copy of its own training target -- which "
                   "is why the slope and not the level is the estimator.",
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
        hypothesis="The ranking from dense SCANFI labels differs from the "
                   "fire-outcome ranking, and SWIR ranks higher in it. Structure "
                   "and biomass retrieval leans on SWIR more than a burn outcome "
                   "does, because the outcome is diluted by ignition and weather. "
                   "If the two rankings agree, that is a strong convergent result "
                   "for whichever bands win.",
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
        hypothesis="The best four cluster near 1240, 1610 and 1680-1730 nm, with "
                   "the fourth in the 1500s. From brief hypotheses H1 and H3: "
                   "resolving a dry-matter change needs two water-sensitive bands "
                   "with different water-to-dry-matter absorption ratios.",
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
        hypothesis="1240 nm is slightly better for water sensitivity and 1209 "
                   "slightly better for O2 margin, with the difference small "
                   "enough that the flown WorldView-3 centre is defensible. A "
                   "large difference either way is the interesting outcome.",
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
        hypothesis="Diminishing returns beyond roughly 10-15 well-placed bands, so "
                   "the HS mode's 96 channels buy little over a well-chosen MS "
                   "set. WRONG IF the curve keeps climbing, which would make the "
                   "HS mode the better instrument and change the payload decision.",
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
        "E-26", "Within-fire burn pattern", "Controls",
        hypothesis="Imagery separates burned from unburned pixels INSIDE fire "
                   "patches at least as well as it does across all patches, "
                   "because inside a perimeter the outcome is fuel, terrain "
                   "and firebreaks rather than whether a fire started. WRONG "
                   "IF within-fire skill is clearly lower, which would say "
                   "most unconditional skill comes from recognising WHICH "
                   "patches burned -- between-patch discrimination, not "
                   "fuel.",
        independent="the training cohort: all scenes vs fire patches only, "
                    "with each fold's locations held fixed",
        dependent=_M + " within fire tiles vs overall; and both models scored "
                       "on the SAME fire tiles",
        conclusion="Conditioning on ignition removes the component a "
                   "reflectance spectrum structurally cannot see. AUC ignores "
                   "prevalence, so within-fire against overall reads as which "
                   "task the imagery predicts better. Water and rock inside a "
                   "perimeter are easy unburned pixels, so part of any "
                   "within-fire skill is 'non-fuel is visible' -- fuel, but "
                   "not moisture.",
        state="RUNNABLE",
        runner="sweep_axes.sh SETS=cond",
        note="REDESIGNED. As first written it asked 'burned > 100 ha, given "
             "it burned'. Patches are ~530 x 530 px, ~11,257 ha, and every "
             "one of the 99 fire patches exceeds 100 ha -- the smallest burned "
             "area is 3,017 ha -- so the cut separated nothing. Folds are now "
             "assigned BEFORE the scene filter: fold_indices deals the blocks "
             "present round-robin, so filtering first had reshuffled which "
             "ground landed in which fold.",
        resources="1 fit/task x 12 tasks; est 0:05; --time=0:30:00 --mem=16G --cpus-per-task=12 "
                  "--gpus=a100:1",
    ),

    # ─────────────────────────────── Hardware ────────────────────────────
    Experiment(
        "E-27", "Cost per input channel", "Hardware",
        hypothesis="BRAM scales roughly linearly with input channel count, so 96 "
                   "channels are infeasible on the target part and 11 are "
                   "affordable. Stream BRAM is ceil(width/18) x ceil(depth/1024) "
                   "and width never stops paying. WRONG IF scaling is "
                   "sub-linear because the first convolution dominates, "
                   "which would make a wide input cheaper than the "
                   "marginal-cost argument assumes.",
        independent="input channel count: 3 / 6 / 10 / 11 / 96",
        dependent="BRAM, DSP, LUT and latency from a real conversion",
        conclusion="The MARGINAL COST denominator. The brief asks for value "
                   "per marginal cost, and without this the ranking has a "
                   "numerator only. Stream BRAM is "
                   "ceil(width/18) x ceil(depth/1024), so width never stops "
                   "paying.",
        state="RUNNABLE",
        runner="sweep_architecture.py --widths",
        resources="CPU only: model conversion, no Narval GPU allocation",
    ),
    Experiment(
        "E-28", "Co-registration tolerance", "Hardware",
        hypothesis="Negligible cost below a quarter pixel, material by one "
                   "pixel. WRONG IF a half-pixel shift already costs "
                   "materially, which would tighten the dichroic and "
                   "focal-plane alignment budget; or if two pixels cost "
                   "little, which would retire the registration risk.",
        independent="SWIR-channel shift at evaluation: 0, 0.25, 0.5, 1, 2 px, "
                    "on a model trained with the channels registered",
        dependent="the drop in " + _M + " against the unshifted score, "
                  "paired by fold",
        conclusion="A number for the requirements table. The dichroic makes "
                   "misregistration small, not absent. This is the "
                   "deployment question -- a model built on co-registered "
                   "imagery meeting a misregistered instrument.",
        state="RUNNABLE",
        runner="sweep_axes.sh SETS=shift",
        note="REDESIGNED. Shifting during training too would understate the "
             "cost, because a convolution can learn to compensate a fixed "
             "offset. Rigid translation only -- not rotation, scale or "
             "pushbroom keystone -- so the tolerance is NECESSARY, not "
             "sufficient. The original hypothesis also placed the loss at "
             "snow/forest boundaries; this reports the scene-average cost and "
             "cannot localise it, so that clause was dropped rather than left "
             "untestable.",
        resources="1 fit + 5 evaluations/task x 6 tasks; est 0:06; "
                  "--time=0:30:00 --mem=16G --cpus-per-task=12 --gpus=a100:1",
    ),

    # ────────────────────────────── Out of reach ─────────────────────────
    Experiment(
        "E-29", "T1 live foliar moisture", "Out of reach",
        hypothesis="From Jolly et al. (2014), the brief's lead hypothesis H1: dry "
                   "matter, not water content, drives seasonal conifer LFMC, so "
                   "water-only bands will return EWT rather than LFMC and a "
                   "two-band water contrast is required. Untestable here until an "
                   "LFMC label exists.",
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
        hypothesis="Brief hypothesis H2: SWIR2 is necessary for curing and 1240 nm "
                   "is not a substitute, because the cellulose/lignin feature near "
                   "2100 nm is what separates NPV from soil. Untestable here: no "
                   "curing label, no grassland, and the band is past the detector.",
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
        hypothesis="None offered. Out of scope by decision, and a hypothesis "
                   "recorded for work that will not run invites being mistaken for "
                   "a finding.",
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
