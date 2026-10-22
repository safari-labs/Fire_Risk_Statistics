# Experiment register

**Generated from `src/safari_bands/experiments.py` by `scripts/make_experiments_doc.py`. Do not edit by hand** -- the figure `docs/results/figures/experiment_plan.png` renders from the same register, and a hand-kept copy drifts.

31 experiments. **14 can run today** on data already packed and staged.

## Feasibility at a glance

| State | Count | What it means | Experiments |
|---|---|---|---|
| **Runnable now** | 13 | data packed and staged; nothing missing | E-1, E-2, E-3, E-4, E-5, E-6, E-8, E-10, E-11, E-12, E-13, E-14, E-27 |
| **Partial result** | 1 | some folds or arms have completed; the rest are blocked | E-15 |
| **Needs code** | 7 | no new data; a runner or a flag has to be written | E-7, E-9, E-18, E-19, E-26, E-28, E-29 |
| **Needs a pack** | 3 | data held but not tiled, packed or transferred | E-20, E-21, E-22 |
| **Needs new data** | 4 | free to obtain, not yet held | E-17, E-23, E-24, E-25 |
| **No label exists** | 3 | cannot be run with any amount of work on data we hold | E-16, E-30, E-31 |

Numbering note: E-17 to E-20 were an earlier E-1 to E-4 from the CFFDRS gap audit. They were renumbered into this single register rather than left as a second scheme; `docs/CFFDRS_GAPS.md` points at the new ids.

## Experiments

### Band selection

| ID | Experiment | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|
| **E-1** | VNIR band selection ★ | which 6 of the 10 Sentinel-2 bands in 400-1000 nm | auc_px, scenario-held-out folds, per set size k | Runnable now | `sweep_arms.sh ARMS=vnir` |
| **E-2** | All-11 greedy | unconstrained choice over all 11 packed bands | auc_px, scenario-held-out folds; the k at which B11 first enters | Runnable now | `sweep_arms.sh ARMS=all11` |
| **E-3** | Forced-SWIR delta | B11 held in the set vs the VNIR-only set, matched k | the paired difference in auc_px, scenario-held-out folds | Runnable now | `sweep_arms.sh ARMS=vnir_swir` |
| **E-4** | SWIR-only floor | B11 alone, no VNIR band | auc_px, scenario-held-out folds | Runnable now | `sweep_arms.sh ARMS=swir_only` |
| **E-5** | Leave-one-out band value | each band removed in turn from the chosen set | the drop in auc_px, scenario-held-out folds on removing each band | Runnable now | `sweep_bands.py --leave-one-out (rides in E-1..E-4)` |
| **E-6** | Selection stability | the same search re-run inside each of 6 location folds | the fraction of folds that select each band at each k | Runnable now | `pool_bands.py (after E-1..E-4)` |
| **E-7** | Resolution requirement | ground sample distance: 20 / 40 / 80 m, coarsening only | auc_px, scenario-held-out folds vs GSD | Needs code | *none yet* |

### Controls

| ID | Experiment | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|
| **E-8** | Label independence control (control) | the label source: NBAC perimeters vs VIIRS thermal | change in the band ranking and in auc_px, scenario-held-out folds | Runnable now | `sweep_bands.sh LABEL=vnp14` |
| **E-9** | Lightning cohort (control) | fires filtered to NFDB CAUSE = lightning | auc_px, scenario-held-out folds, restricted cohort | Needs code | *none yet* |
| **E-10** | Negative control (control) | a deliberately redundant band pool | auc_px, scenario-held-out folds | Runnable now | `sweep_bands.sh BANDS=... (config/bands/negative_control.yaml)` |

### Index baselines

| ID | Experiment | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|
| **E-11** | Greenness vs moisture indices ★ | the index family given to the model: greenness (NDVI, EVI, VARI, NDRE) / moisture (NDMI, MSI) / both / raw bands | the paired difference in auc_px, scenario-held-out folds, against greenness | Runnable now | `sweep_indices.sh` |
| **E-12** | Index baseline vs learned bands | hand-built indices vs the learned model on raw bands | the paired difference in auc_px, scenario-held-out folds | Runnable now | `sweep_indices.sh ARMS=raw,both` |

### Covariates

| ID | Experiment | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|
| **E-13** | Weather representation | the scalar columns the fusion head sees: FWI codes / our 12 compressed history features / both / dimensionless history | the paired difference in auc_px, scenario-held-out folds, against codes | Runnable now | `sweep_covariates.sh SETS=weather` |
| **E-14** | Fusion architecture | how weather enters: not at all / two-head late / bottleneck | the paired difference in auc_px, scenario-held-out folds | Runnable now | `sweep_covariates.sh SETS=fusion` |
| **E-15** | Imagery vs the FBP formula | the FBP foliar-moisture scalar alone vs that scalar plus all 9 surface bands | the paired difference in auc_px, scenario-held-out folds | Partial result | `sweep_covariates.sh SETS=g1` |
| **E-16** | FMC arms | baseline / measured / augment foliar moisture | (none obtainable) | No label exists | `-- (do not run)` |

### CFFDRS gaps

| ID | Experiment | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|
| **E-17** | Station-density stratification | distance from each patch to the nearest fire-weather station | the imagery increment in auc_px, scenario-held-out folds, stratified by that distance | Needs new data | *none yet* |
| **E-18** | Snow-off startup | FWI start date: per-pixel NDSI snow-off vs our flat 90-day spinup | change in the FWI codes, and auc_px, scenario-held-out folds | Needs code | *none yet* |
| **E-19** | Latitude-banded weather | the E-13 weather contrast, split by latitude band | the paired difference per band | Needs code | *none yet* |
| **E-20** | Weather staleness | the age of the weather at inference: 0 / 24 / 48 / 72 h / 7 d | auc_px, scenario-held-out folds vs weather age, per weather arm | Needs a pack | *none yet* |
| **E-21** | Fuel-layer refresh | the static 2020 SCANFI layer vs our current estimate, against staleness gap | the SLOPE of auc_px, scenario-held-out folds against staleness, not the level | Needs a pack | *none yet* |
| **E-22** | Ecology arm ★ | the same band searches, against SCANFI structure instead of a burn outcome | per-pixel error on cover, closure, height, biomass, species | Needs a pack | `train_ecology.sh` |

### Hyperspectral

| ID | Experiment | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|
| **E-23** | SWIR band placement | any 4 centres and widths in 1003-1359 and 1414-1749 nm (140 usable channels) | retrieval error per candidate set | Needs new data | `fetch_aviris.py + ingest_aviris.py` |
| **E-24** | 1209 vs 1240 nm | WorldView-3's flown centre against Gao's NDWI band | retrieval error, and O2 absorption margin | Needs new data | `ingest_aviris.py --mode both` |
| **E-25** | Spectral resolution: HS vs MS | 140 SWIR channels at 5 nm vs the best 4-6 broad bands | retrieval error vs channel count | Needs new data | `ingest_aviris.py, then sweep_bands.py` |
| **E-26** | Conditional large fire | burned area > 100 ha, conditional on having burned | auc_px, scenario-held-out folds on the conditional task | Needs code | *none yet* |

### Hardware

| ID | Experiment | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|
| **E-27** | Cost per input channel | input channel count: 3 / 6 / 10 / 11 / 96 | BRAM, DSP, LUT and latency from a real conversion | Runnable now | `sweep_architecture.py --widths` |
| **E-28** | Co-registration tolerance | sub-pixel VNIR/SWIR shift injected at hard edges | retrieval error vs shift | Needs code | *none yet* |

### Out of reach

| ID | Experiment | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|
| **E-29** | T1 live foliar moisture | LFMC, the brief's lead retrieval target | RMSE against gravimetric LFMC | Needs code | *none yet* |
| **E-30** | T2 curing / NPV fraction | grass curing fraction | error against field curing | No label exists | *none yet* |
| **E-31** | Fire occurrence prediction | ignition probability per cell-day | (out of scope) | No label exists | `-- (out of scope)` |

## What each experiment could conclude

The field that decides whether an experiment deserves GPU time. An experiment whose null result teaches nothing is not worth queueing, and writing this down is how that gets noticed before the run rather than after.

### Band selection

**E-1 — VNIR band selection**

Names the six bands for the Mantis MS mode. The one complete answer the packed data can give today, and it settles one of the three sensor modes outright.

**E-2 — All-11 greedy**

If greedy reaches for B11 early, the SWIR chain earns a slot on fire-outcome evidence. If it never does, that is weak evidence against, not strong -- one SWIR band cannot test a four-band mode.

**E-3 — Forced-SWIR delta**

The marginal value of one SWIR band at equal band count. A lower bound on the SWIR chain: we hold 1 band in the window, the sensor would carry 4.

**E-4 — SWIR-only floor**

The third sensor option -- SWIR instead of MS -- had no number. Structurally a SWIR-only set forms 0 of 12 catalogue indices and 0 ECVs, measured; this says what a LEARNED model does with it anyway, which rule 4 treats as the real question.

*Note:* A quarter of the sensor. Read strictly as a floor.

**E-5 — Leave-one-out band value**

Per-band value CONDITIONAL on the rest, which is the only kind that means anything when bands are near-duplicates. Cannot see redundancy: B8 and B8A are 23 nm apart, so each may look worthless while the pair is essential.

**E-6 — Selection stability**

6/6 is a finding, 3/6 is a coin flip. Without it a single fold's ranking would be reported as the ranking.

**E-7 — Resolution requirement**

How much resolution the retrieval needs — a mission requirement, and sharper than it looks: the Mantis MS mode is 32 m at 500 km and 39.7 m at 620 km, so ~40 m is the real operating point and our 20 m results are optimistic.

*Blocked on:* data.coarsen() exists; no CLI flag on sweep_bands.py

### Controls

**E-8 — Label independence control**

A band whose value collapses when the label becomes thermal was exploiting the label, not reading fuel. VNP14 keys off 4 and 11 um emission, so it cannot share information with 400-1750 nm reflectance.

**E-9 — Lightning cohort**

Human ignitions carry a roads-and-settlement signal that a model can read off the imagery instead of the fuel. If the ranking holds on lightning fires only, it is about fuel.

*Blocked on:* labels.is_lightning() exists; no cohort filter at pack time

**E-10 — Negative control**

Sanity. If a deliberately poor set scores well, the pipeline is broken and no other result here is interpretable.

### Index baselines

**E-11 — Greenness vs moisture indices**

THE MISSION'S CENTRAL CLAIM. FWI2025 accepts grassland curing from remote sensing and its current option is NDVI-based GREENNESS -- a proxy for dryness. Greenness tracks moisture only while they co-vary seasonally, and a conifer stand stays green as it dries. If moisture beats greenness on a burn outcome, that is a concrete, quantified recommendation to the operational system. If `both` does not beat `greenness`, the 1610 nm moisture signal adds nothing this label can see -- also publishable.

*Note:* Primary contrast is `both` vs `greenness`: a strict superset, so a positive result is unambiguous. Tests ONE moisture index at 1610 nm -- NDWI_Gao needs 1240 nm and NMDI/NDTI/NBR need SWIR2, none of which Sentinel-2 carries.

*CFFDRS gap:* FWI2025 curing input

**E-12 — Index baseline vs learned bands**

If the learned model beats every index family by a wide margin, the recommendation to CFFDRS is to take BANDS rather than indices — a finding about the system's interface, not only about our sensor. The heritage baseline rule 4 asks for.

### Covariates

**E-13 — Weather representation**

Does our compression of 91 days beat the FWI System's? CODES is CFFDRS as it stands and is the baseline. If BOTH beats CODES but DIMENSIONLESS does not, the gain came from absolute level, which at 45-70 N is latitude -- geography wearing a weather costume.

*Note:* No repack: the pack carries weather_arm=both, the union, so each arm is a column mask.

**E-14 — Fusion architecture**

What the CFFDRS-shaped separation of fuel and weather costs or buys against early fusion. rasters_only is the no-weather floor and is also the configuration the band ranking is read from, which ties the two together.

**E-15 — Imagery vs the FBP formula**

G1 restated into something testable: does imagery carry foliar-moisture information the FBP equation does not? It CANNOT say our spectral estimate beats theirs -- that needs an LFMC label (E-29).

*Note:* The imagery-free floor has run: 6/6 folds, auc_px 0.5396-0.7660, mean 0.642. Its counterpart was lost to the device bug, so the contrast is still missing.

*CFFDRS gap:* G1 foliar moisture is computed, never observed

**E-16 — FMC arms**

NOTHING. fmc_measured is read in four places and written in none, so all three arms reduce to the FBP equation and would return three identical numbers looking like 'no difference'. Listed so it is not run by mistake.

*Blocked on:* fmc_measured is never written; needs E-29

### CFFDRS gaps

**E-17 — Station-density stratification**

CFS names thin station density as a limit on model accuracy (GLC-X-42 7.2). Fuel moisture is the integral of weather, so satellite fuel state should be worth most where the weather grid is weakest -- the north, which is also where most of the area burns.

*Blocked on:* CWFIS station locations not held; ERA5-Land says nothing about where the observing stations are

*CFFDRS gap:* G3 station density

**E-18 — Snow-off startup**

Fixes our own defect first: the spinup starts ~1 April, which at 55-67 N is frozen and snow-covered, so the recursion accumulates weeks of spurious drying and the error scales with latitude. Then it tests whether a per-pixel snow-off date beats the regional rule.

*Blocked on:* an Earth Engine NDSI reduction over the S2 collection; no new imagery

*CFFDRS gap:* G4 snow-off keyed by regional rule

**E-19 — Latitude-banded weather**

DMC and DC day-length factors are tabulated for ~46 N while Canada spans 42-83. A pooled number cannot distinguish 'history is better' from 'history is better at high latitude', which is the actual claim.

*Blocked on:* a latitude-split flag on report_arms.py or pool_bands.py

*CFFDRS gap:* G5 day-length tabulated for ~46 N

**E-20 — Weather staleness**

Every FWI code is defined on a same-day noon observation and a daily uplink cannot supply one. The input drift is already measured (DC 8.2% over three days against ISI's 89.9%) and fwi.py reasons from it to a recommendation -- BUI best, FWI worst. Drift in a feature is not loss in a prediction, and this measures the half nobody has.

*Note:* Train once, score at each lag: one model, five scores. The leakage guard makes an earlier target date strictly safer.

*Blocked on:* lagged FWI sidecars: an ERA5 pass over data already held, then a repack

*CFFDRS gap:* G7 CFFDRS assumes same-day observations

**E-21 — Fuel-layer refresh**

FBP consumes a fixed-vintage fuel grid while fuel type changes with harvest, insects, fire and regrowth. The slope is the estimator because at gap 0 our estimate is a noisy copy of its own training target and would lose on noise alone.

*Blocked on:* needs E-22 first (the ecology model), then the refreshed estimate attached

*CFFDRS gap:* G2 fuel-type layer is a fixed vintage

**E-22 — Ecology arm**

THE PRIMARY BAND RANKING. Dense per-pixel labels rather than one sparse outcome per patch, so it has orders of magnitude more signal per scene than the fire arm and measures what the bands actually retrieve rather than what correlates with ignition.

*Blocked on:* 279 patches on disk, never tiled or packed; needs a pack and a second transfer

### Hyperspectral

**E-23 — SWIR band placement**

THE SWIR SPECIFICATION. Sentinel-2 has one band in that window and the mode carries four: four cannot be chosen from one. Only a contiguous source can answer it.

*Note:* Grid measured from AVIRIS-NG's own bad-band list (A-22), which puts the water-vapour gap at 1364-1408 nm -- narrower than assumed, so 1300-1359 and 1414-1500 were being excluded for no reason.

*Blocked on:* 3 of 42 pre-fire lines on disk, 0 ingested

**E-24 — 1209 vs 1240 nm**

Water sensitivity traded against O2 margin. The validator flagged the conflict; nobody has measured it.

*Blocked on:* same as E-23

**E-25 — Spectral resolution: HS vs MS**

What spectral RESOLUTION buys, which decides the Mantis HS mode. Cannot be faked: ten Sentinel-2 bands cannot be interpolated into ninety-six, and rule 2 forbids trying.

*Blocked on:* same as E-23

**E-26 — Conditional large fire**

36% base rate, and 97% of area burned is in the tail. Conditioning on ignition removes the weather-and-chance component, leaving a fuel-dominated target -- which is what the sensor can actually see.

*Blocked on:* an NBAC area filter at pack time

### Hardware

**E-27 — Cost per input channel**

The MARGINAL COST denominator. The brief asks for value per marginal cost, and without this the ranking has a numerator only. Stream BRAM is ceil(width/18) x ceil(depth/1024), so width never stops paying.

**E-28 — Co-registration tolerance**

A number for the requirements table. The dichroic makes this small, not absent, and snow/forest boundaries are the flagged engineering risk.

*Blocked on:* no shift-injection harness

### Out of reach

**E-29 — T1 live foliar moisture**

Would make G1's STRONG claim testable -- that a spectral estimate beats the FBP equation -- and unblock E-16. Globe-LFMC 2.0 is fetched and measured: 2,884 usable records at 83 sites, no Canadian ones, and C-2 black spruce has 51. It carries no spectra, so each record must be paired with a Sentinel-2 acquisition.

*Blocked on:* Globe-LFMC held; the S2 pairing pipeline is unwritten (Phase 6a), and PROSAIL for simulated labels is not installed (Phase 1)

*CFFDRS gap:* G1 strong form

**E-30 — T2 curing / NPV fraction**

The other half of the FWI2025 curing input. Blocked three ways: no curing label anywhere in our data, no grassland in the ecology set, and NDLI needs 1754 nm, past the standard-InGaAs cutoff.

*Blocked on:* no label, no grassland, and the band is past the detector

**E-31 — Fire occurrence prediction**

Parked by decision. Recorded because the argument is strong: FOP runs on 20 km cells, and a 20 m imager supplies the within-cell distribution a coarse model structurally cannot have -- 10^6 pixels per cell. The product that implies is a distribution summary, not a mean.

*Blocked on:* out of scope by decision; needs lightning strike data

*CFFDRS gap:* G6 FOP cannot see within its cells

## Runnable today

| ID | Experiment | Command |
|---|---|---|
| **E-1** | VNIR band selection | `sweep_arms.sh ARMS=vnir` |
| **E-2** | All-11 greedy | `sweep_arms.sh ARMS=all11` |
| **E-3** | Forced-SWIR delta | `sweep_arms.sh ARMS=vnir_swir` |
| **E-4** | SWIR-only floor | `sweep_arms.sh ARMS=swir_only` |
| **E-5** | Leave-one-out band value | `sweep_bands.py --leave-one-out (rides in E-1..E-4)` |
| **E-6** | Selection stability | `pool_bands.py (after E-1..E-4)` |
| **E-8** | Label independence control | `sweep_bands.sh LABEL=vnp14` |
| **E-10** | Negative control | `sweep_bands.sh BANDS=... (config/bands/negative_control.yaml)` |
| **E-11** | Greenness vs moisture indices | `sweep_indices.sh` |
| **E-12** | Index baseline vs learned bands | `sweep_indices.sh ARMS=raw,both` |
| **E-13** | Weather representation | `sweep_covariates.sh SETS=weather` |
| **E-14** | Fusion architecture | `sweep_covariates.sh SETS=fusion` |
| **E-15** | Imagery vs the FBP formula | `sweep_covariates.sh SETS=g1` |
| **E-27** | Cost per input channel | `sweep_architecture.py --widths` |

All of these read the `stage2_fire_11band` pack already in `~/scratch` on Narval. None needs a new download or a re-pack.

Two standing caveats on every number they produce. The 35-epoch budget is a **ranking** budget, so the output is an order and not an accuracy until the top sets are re-run at full budget. And the fold spread is large -- the one arm that has completed spanned 0.5396 to 0.7660 across six folds from a single model on a single input -- so results must be read as **paired** per-fold contrasts via `report_arms.py`, never as two means compared by eye.

