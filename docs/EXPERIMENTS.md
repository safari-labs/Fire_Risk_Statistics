# Experiment register

**Generated from `src/safari_bands/experiments.py` by `scripts/make_experiments_doc.py`. Do not edit by hand** -- the figure `docs/results/figures/experiment_plan.png` renders from the same register, and a hand-kept copy drifts.

68 experiments. **25 can run today** on data already packed and staged.

## Read this first: the label

**Every result on the original 11-band pack trained on a circular label.** Its `/mask` is not NBAC: for fire scenes, `download.py` writes `_mask.tif` as **dNBR > 0.27**, and NBAC sat in a `_nbac.npy` sidecar that nothing in the tile or pack path read. All 861 fire tiles across the three splits reproduce `_mask.tif`'s dNBR exactly; against the patches' own NBAC masks the mean IoU is 0.755. dNBR is `NBR_pre - NBR_post` with `NBR = (B8 - B11)/(B8 + B11)`, so `NBR_pre` is reconstructible from the input bands -- rule 3's circularity. `sweep_bands.py --label nbac` was validated, printed and recorded, and never read.

The damage concentrates where it matters most: B8, B8A and B11 in the ranking, and E-11 above all, because NDMI is `(B8A - B11)/(B8A + B11)` -- nearly the label's own input.

**Fixed:** `stage2_fire_11band_nbac` swaps NBAC into the fire masks and changes nothing else -- tiles, splits and bands are byte-identical, so the held-out test set does not move. It declares `label_source = nbac`, and the sweep refuses any pack that does not declare one. NBAC marks 43% more burned pixels than dNBR did in the fire tiles: perimeters are filled polygons, so they include the inclusions dNBR skipped.

## Feasibility at a glance

| State | Count | What it means | Experiments |
|---|---|---|---|
| **Concluded** | 33 | every registered part has run; the verdict is in the phase sheets | E-1, E-2, E-3, E-4, E-5, E-6, E-7, E-10, E-11, E-12, E-17, E-18, E-19, E-20, E-22, E-23, E-26, E-27, E-28, E-29, E-33, E-34, E-54, E-55, E-57, E-58, E-59, E-60, E-64, E-65, E-66, E-67, E-68 |
| **Runnable now** | 5 | data packed and staged; nothing missing | E-9, E-24, E-25, E-35, E-37 |
| **Partial result** | 20 | some folds or arms have completed; the rest are blocked | E-21, E-32, E-36, E-38, E-41, E-43, E-44, E-45, E-46, E-47, E-48, E-49, E-50, E-51, E-52, E-53, E-56, E-61, E-62, E-63 |
| **Needs code** | 2 | no new data; a runner or a flag has to be written | E-39, E-40 |
| **Needs a pack** | 2 | data held but not tiled, packed or transferred | E-8, E-42 |
| **Closed, no result** | 3 | closed without a valid result; the note names what answers it instead | E-13, E-14, E-15 |
| **No label exists** | 3 | cannot be run with any amount of work on data we hold | E-16, E-30, E-31 |

Numbering note: E-17 to E-20 were an earlier E-1 to E-4 from the CFFDRS gap audit. They were renumbered into this single register rather than left as a second scheme; `docs/CFFDRS_GAPS.md` points at the new ids.

## Experiments

### CFFDRS mirror

| ID | Experiment | Hypothesis | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|---|
| **E-32** | CFFDRS as is (R0) ★ | FBP head-fire intensity ranks burned pixels above chance within fire patches, and FWI/BUI ranks fire above confuser patches. WRONG IF the physics scores sit at chance on both: then the outcome measures something CFFDRS does not rate, and every imagery delta would be against a meaningless floor. | none learned: FBP ROS / HFI / CFB per pixel and FWI codes per patch, computed from the operational inputs | within-patch and between-patch AUC, per process | Partial result | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` |
| **E-33** | Fuel inventory comparison | Pre-fire inventories (CWFIS 2019 and 2014b, the SCANFI v2 pre-fire step) give R0 skill within noise of each other, and the post-fire ones (CWFIS 2024, SCANFI 2025) score far higher. WRONG IF a post-fire inventory does NOT inflate skill: then the leakage measured in A-25 does not reach the outcome. | the fuel inventory feeding R0: CWFIS 2024 / 2019 / 2014b, SCANFI v2 2005-2025, SCANFI v1 2020 | R0 within-patch AUC per process, and the gap between pre- and post-fire inventories | Concluded | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` |
| **E-34** | Learned CFFDRS (R1/R2) | A model given exactly the CFFDRS inputs (R1) beats R0, and physics plus a learned residual (R2) is within noise of R1. WRONG IF R1 does not beat R0, which would say the outcome is already as predictable from CFFDRS inputs as CFFDRS makes it. | R0 vs R1 vs R2 on identical inputs and folds | paired within/between-patch AUC per process | Concluded | `Fire_Risk_FW/scripts/shell/sweep_slots.sh CONFIGS=r0_scanfi,r0_cwfis,r1,r2,r2_cwfis` |
| **E-35** | Fuel-type slot | Imagery-derived fuel type improves within-patch skill over the pre-fire operational layer. WRONG IF the shuffled-imagery twin gains as much, which would make the gain a shortcut. | the fuel-type slot's source: pre-fire inventory vs imagery_replace (ecology model) vs imagery_correct | paired delta in within-patch AUC per process | Runnable now | `Fire_Risk_FW RUN_ID=20261102-1959 SUBMIT=1 bash scripts/shell/sweep_eco_fire.sh (FW 15a705b; done 2026-11-10); then SUBMIT=1 EXP_NAME=slots_e35 RUN_ID=20261110-1901 SKIP_DONE=1 ECO_DATA=$HOME/scratch/eco_fire_v1 CONFIGS=r2,r3_fuel_replace,r3_fuel_replace_shuffled,r3_fuel_pc_replace,r3_fuel_pc_replace_shuffled,r3_pc_replace,r3_pc_replace_shuffled bash scripts/shell/sweep_slots.sh` |
| **E-36** | Percent-conifer slot | Imagery percent conifer improves M-1/M-2 spread and intensity. WRONG IF no gain survives on mixedwood pixels. | percent-conifer source for M-1/M-2: inventory vs imagery | paired delta on M-1/M-2 pixels | Partial result | `Fire_Risk_FW/scripts/shell/sweep_slots.sh CONFIGS=r3_pc,r3_pc_shuffled` |
| **E-37** | Crown-base-height slot | Imagery-informed CBH changes crown fraction burned enough to move intensity skill. WRONG IF the CFB term never engages at our fire weather. | CBH source: ST-X-3 default vs height-derived | paired delta in the intensity branch | Runnable now | `Fire_Risk_FW SUBMIT=1 EXP_NAME=slots_e35 RUN_ID=20261110-1901 SKIP_DONE=1 ECO_DATA=$HOME/scratch/eco_fire_v1 CONFIGS=...,r3_cbh_replace,r3_cbh_replace_shuffled bash scripts/shell/sweep_slots.sh (correct form: CONFIGS=r3_cbh,r3_cbh_shuffled)` |
| **E-38** | Curing slot | Imagery curing beats the CWFIS curing product on O-1 pixels. WRONG IF it does not -- but O-1 is about 3 % of burned pixels, so a null is likely to be 'n insufficient'. | curing source: CWFIS percent curing (2020-2025) or the time-of-year default vs S2 curing | ignition and spread on O-1 pixels | Partial result | `Fire_Risk_FW/scripts/shell/sweep_slots.sh CONFIGS=r2_cwfis,r3_curing_cwfis,r3_curing_cwfis_shuffled` |
| **E-39** | Canopy closure to in-stand moisture | Imagery stand density sharpens ignition receptivity through the stand-specific FFMC adjustment. WRONG IF the adjusted in-stand FFMC ranks ignitions no better than open FFMC. | closure source for the in-stand FFMC adjustment | Stage C ignition AUC and calibration | Needs code | *none yet* |
| **E-40** | Green-up slot | An S2 green-up date beats the CWFIS green-up product for the D-1/M-1/M-2 leafless-to-green switch. WRONG IF the two agree to within a few days, leaving nothing to gain. | green-up source: CWFIS product (2020-2025, held) vs S2 phenology | spread and ignition on deciduous and mixedwood pixels | Needs code | *none yet* |
| **E-41** | Spread R0 (CFSDS) | FBP ROS correlates with observed daily spread (Spearman rho > 0). WRONG IF it does not, which would bound everything the spread branch can claim. | none learned: FBP ROS on each fire-day | Spearman rho and log-ratio error against CFSDS spread | Partial result | `Fire_Risk_Model/scripts/python/eval_spread_r0.py` |
| **E-42** | Spread slot value | Fuel-side imagery slots improve per-fire-day spread prediction. WRONG IF only weather-side inputs move it. | slot sources, as in E-35 to E-40, on the spread target | paired change in Spearman rho per fire-day | Needs a pack | *none yet* |
| **E-44** | Ignition R0 | P(sustained flaming) x P(lightning holdover) ranks lightning starts above matched controls. WRONG IF at chance. | none learned: the published ignition relationships | AUC and calibration, starts vs matched controls | Partial result | `Fire_Risk_Model build_ignition_dataset.py --stage weather / scanfi / filter, then eval_ignition_r0.py (CPU, no fitting)` |
| **E-45** | Ignition slot value | Closure, green-up and fuel-type slots improve ignition ranking. WRONG IF the shuffled twins gain as much. | slot sources on the ignition target | paired AUC change | Partial result | `Fire_Risk_FW SUBMIT=1 bash scripts/shell/sweep_ignition.sh (run_ignition.py; 8 configs x 5 folds x 3 seeds, R0 at seed 0: 100 fits)` |
| **E-46** | Band and index decision | The combined ranking keeps at least one red-edge band and B11 within the Mantis k=6 / k=4 sets. WRONG IF SWIR never earns a slot on any process's weighted evidence. | per-slot nested rankings weighted by slot value (A-29) | the chosen band and index sets, with their margins | Partial result | `Statistics scripts/make_band_options.py (consensus, grid, provisional table); then on Nibi docs/results/P12/p12_bands/rescore_commands.md (8 sweep_eco_arch runs and one sweep_hs references run), then make_band_options.py --eco-rescore --hs-rescore` |
| **E-47** | Architecture decision | Restated 2026-11-05, before any result (A-49): the onboard model is the ecology estimator (A-41), not the fire network. At E-46's bands, TinyEcologyUNet at the size the bands were ranked with (base_ch 8, depth 2) is within one paired SE of the best rung on the equal-weight combined skill, with sensor noise. WRONG IF only a larger rung (base_ch >= 16 or depth 3) reaches it: then the onboard model is bigger than the band search assumed and E-48 must size for it. | TinyEcologyUNet base_ch 4/8/16/32 x depth 1/2/3 at the chosen bands (raw + indices), with sensor noise | combined and per-head skill on the outer fold, paired by fold and seed with eco_v3; parameters and MACs per pixel and per 1000 x 1000 px scene | Partial result | `Fire_Risk_FW BANDS=<E-46 set> SUBMIT=1 bash scripts/shell/sweep_eco_arch.sh (run_eco_arch.py)` |
| **E-49** | Dating the weather (R0) | Moving R0's weather from the legacy 30-June daily aggregates to each patch's D-1 at 13:00 LDT RAISES the between-patch AUC of the fast codes (FFMC, ISI) and LOWERS that of the slow codes (DC, BUI): the fast codes will describe the day before the fire rather than 30 June, and part of the slow codes' legacy 0.83 (DC) came from reading the fire year's drought after most fires had started. WRONG IF the fast and slow codes move in the same direction, or no code moves outside its CI. | weather design, as a chain on the same patches: legacy -> dated (daily aggregates, flat spin-up) -> dated at 13:00 LDT -> dated with the Appendix C-2 start-up and overwintered DC (the P3 design) | between-patch AUC and paired fire-vs-own-confuser win rate per FWI code; within-patch HFI AUC, reported | Partial result | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` |
| **E-52** | Weather source: station vs ERA5 (R0) | The nearest CWFIS station's reported codes at D-1 rank fire above non-fire patches at least as well as ERA5-Land at 13:00 LDT (they are what CFFDRS actually runs on), and the ERA5-to-station disagreement in the codes grows with distance to the station. WRONG IF the disagreement is flat with distance: E-17's mechanism (weather error grows away from stations) would then have no support in the codes. | weather source for the same patches and date: ERA5-Land at the patch centre vs the nearest CWFIS station's reported observation and codes | between-patch AUC per code and source; \|ERA5 - station\| per code against station distance (Spearman) | Partial result | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` |
| **E-55** | Operational FWI grid vs the reconstruction | The FWI grid CWFIS issued for D-1 ranks fire above non-fire development patches as well as our ERA5-Land FWI does: the two between-patch AUCs are within 0.03 of each other, and the two FWI values agree across patches (Spearman rho >= 0.8). WRONG IF they differ by more than 0.03 with a CI excluding 0, or rho < 0.8: then R0 does not stand in for operational CFFDRS, and every imagery delta measured against R0 or R2 is measured against a different baseline from the one operations use. | FWI source on D-1 for the same patches: CWFIS operational grid (GeoServer public:fwi, 2 km, archived from 2018-01-01) vs ERA5-Land at 13:00 LDT (fwi.py, variant c2) vs the nearest CWFIS station's reported FWI | between-patch AUC per source (all pairs and same-year pairs), paired by patch with a fire/block-group bootstrap; Spearman rho and median difference, operational vs ERA5 and vs station | Concluded | `Fire_Risk_Model/scripts/python/fetch_cwfis_grids.py` |
| **E-56** | Operational FBP outputs on a 2024-2025 cohort | On fires that started in 2024-2025, the HFI CWFIS issued for D-1 ranks fire above non-fire patches within 0.03 of our R0 HFI for the same patches and day (between-patch AUC), and the two agree across patches (Spearman rho >= 0.7). WRONG IF they differ by more than 0.03 with a CI excluding 0: the operational inputs our reconstruction replaces (interpolated station weather, the CWFIS fuel grid, its FMC, green-up and curing) then carry, or lose, skill R0 does not. | HFI (and ROS, CFB, FMC, fuel type) source on D-1: CWFIS operational grids (public:hfi etc., 2 km, from 2024-01-01) vs our R0 on the same patches | between-patch AUC per source, paired by patch; Spearman rho per output; fuel-type agreement (share of area) | Partial result | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py --cohort` |
| **E-57** | Percent-conifer correction with an imagery-free offset | Once a learned imagery-free offset absorbs the tile-wide shift (P7-C1), the imagery percent-conifer correction carries information its shuffled twin does not: within-patch AUC on M-1/M-2 pixels beats the twin's (paired group-bootstrap CI above 0), and the imagery part varies more within tiles than the twin's. WRONG IF the real-imagery arm and its twin stay within noise on M-1/M-2 pixels (CI spanning 0): then, at this n, imagery percent conifer adds nothing through the physics even freed of the shift. | imagery percent-conifer correction with an offset (r3_pc_offset) vs the same with imagery shuffled across tiles (r3_pc_offset_shuffled); R2 as the floor | paired within-patch AUC on M-1/M-2 pixels and on all pixels; the learned offset (points); within-tile SD of the imagery part | Concluded | `Fire_Risk_FW/scripts/shell/sweep_slots.sh CONFIGS=r2,r3_pc_offset,r3_pc_offset_shuffled` |
| **E-58** | Closing R2's within-patch gap to R1 | R2's within-patch deficit to R1 (-0.025 [-0.034, -0.015], P7) is an optimisation artefact of starting the residual at zero beside the physics. Either starting the residual from the R1 trained on the same fold and seed (r2_warm) or training it at 10x the learning rate (r2_lr10) brings R2 within 0.01 of R1 within patches, without losing more than 0.01 between patches against R2. WRONG IF both arms stay more than 0.01 below R1 within patches with a CI excluding 0: the gap is then the cost of anchoring the score to the physics, and is reported as such in the P12 architecture choice. | R2's residual: zero start at the base rate (r2) vs started from the trained R1 (r2_warm) vs 10x the learning rate (r2_lr10); R1 as the target, rerun in the same sweep | paired within- and between-patch AUC against R1 and R2, per fire patch, fire/block-group bootstrap | Concluded | `Fire_Risk_FW/scripts/shell/sweep_slots.sh CONFIGS=r1,r2,r2_warm,r2_lr10` |
| **E-63** | Out-of-time generalisation, two training regimes | (a) Regime B -- trained and selected on 2019-2023 only -- keeps its skill on 2024 and 2025: R1's and R2's between- and within-patch AUC there are within 0.05 of their 2019-2023 cross-validated AUC, and R1 still beats R0 (paired CI above 0). (b) Regime A -- 2024 added to training and selection -- beats regime B on 2025 within patches (paired CI above 0). WRONG IF (a) either rung drops by more than 0.05 with a CI excluding it, or R1 - R0 on 2024-2025 has a CI reaching 0; or (b) regime A minus regime B on 2025 has a CI reaching 0. | training and selection years: regime A, 2019-2024 (tested once on 2025); regime B, 2019-2023 (tested once on 2024 and 2025). Same ladder, configurations, folds and seeds; each regime makes its own selections | between- and within-patch AUC on the held-out years, paired by fire with a fire/block-group bootstrap; the drop from cross-validated AUC | Partial result | `Fire_Risk_FW/scripts/shell/sweep_slots.sh REGIME=A|B` |

### Band selection

| ID | Experiment | Hypothesis | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|---|
| **E-1** | VNIR band selection ★ | Red-edge earns a slot: the best six include at least one of B5/B6/B7 and exclude both 60 m atmospheric bands (B1, B9). WRONG IF an atmospheric band survives into the best six, which would say the ranking is reading haze rather than vegetation. | which 6 of the 10 Sentinel-2 bands in 400-1000 nm | auc_px, scenario-held-out folds, per set size k | Concluded | `Fire_Risk_FW SCRATCH_DATA=$HOME/scratch/stage2_fire_cffdrs_v2 ARMS=vnir SUBMIT=1 bash scripts/shell/sweep_arms.sh` |
| **E-2** | All-11 greedy | B11 enters by k=3, because the NIR/SWIR contrast is the strongest single moisture signal available. WRONG IF it has not entered by k=7, which would be weak evidence against the SWIR chain -- weak, because one band cannot stand in for four. | unconstrained choice over all 11 packed bands | auc_px, scenario-held-out folds; the k at which B11 first enters | Concluded | `Fire_Risk_FW SCRATCH_DATA=$HOME/scratch/stage2_fire_cffdrs_v2 ARMS=all11 SUBMIT=1 bash scripts/shell/sweep_arms.sh` |
| **E-3** | Forced-SWIR delta | Positive but small: under +0.02 auc_px. One band in the window is a poor proxy for a four-band mode, so a large gain would be surprising and a null is not disqualifying. | B11 held in the set vs the VNIR-only set, matched k | the paired difference in auc_px, scenario-held-out folds | Concluded | `Fire_Risk_FW SCRATCH_DATA=$HOME/scratch/stage2_fire_cffdrs_v2 ARMS=vnir_swir SUBMIT=1 bash scripts/shell/sweep_arms.sh` |
| **E-4** | SWIR-only floor | Clearly above chance and clearly below the VNIR set. The water features at 1200 and 1600 nm are physically present, so a learned model should find something; without the NIR anchor it cannot normalise for canopy structure or illumination. WRONG IF it matches the VNIR set, which would make the MS chain arguable. | B11 alone, no VNIR band | auc_px, scenario-held-out folds | Concluded | `Fire_Risk_FW SCRATCH_DATA=$HOME/scratch/stage2_fire_cffdrs_v2 ARMS=swir_only SUBMIT=1 bash scripts/shell/sweep_arms.sh` |
| **E-5** | Leave-one-out band value | Every individual drop is small, because the pool is redundant. B8 and B8A in particular each look worthless while the pair is not: leave-one-out cannot see mutual substitution, and reading a small drop as 'this band does not matter' is the trap. WRONG IF any single removal costs more than about 0.02, which would mean the pool is far less redundant than the near-duplicate pairs suggest and the chosen set is already minimal. | each band removed in turn from the chosen set | the drop in auc_px, scenario-held-out folds on removing each band | Concluded | `rides in E-1 to E-4 on v2 (SCRATCH_DATA=$HOME/scratch/stage2_fire_cffdrs_v2 SUBMIT=1 bash scripts/shell/sweep_arms.sh)` |
| **E-6** | Selection stability | The top two or three bands are selected in 6/6 folds and the tail is unstable. WRONG IF even the top band swings, which would mean the ranking is fold noise and no k is reportable. | the same search re-run inside each of 6 location folds | the fraction of folds that select each band at each k | Concluded | `pool_bands.py over the v2 arms (sweep_bands_*_v2) after E-1 to E-4` |
| **E-7** | Resolution requirement | Graceful degradation from 20 to 40 m and a sharper fall by 80 m. WRONG IF 20 -> 40 m already costs materially, which matters more than it sounds: the Mantis MS mode is 32 m at 500 km, so our 20 m results would overstate what the sensor delivers. | ground sample distance 20 / 40 / 80 m, in 'pixels' mode: pooled then re-expanded, so INFORMATION is degraded while the tile keeps its shape | auc_px, scenario-held-out folds vs GSD, paired against 20 m | Concluded | `Fire_Risk_FW SCRATCH_DATA=$HOME/scratch/stage2_fire_cffdrs_v2 SETS=gsd SUBMIT=1 bash scripts/shell/sweep_axes.sh` |

### Controls

| ID | Experiment | Hypothesis | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|---|
| **E-8** | Label independence control (control) | The ranking is largely preserved. WRONG IF B11's value collapses specifically -- that would say it was reading NBR-like information shared with the perimeter delineation rather than fuel, which is exactly the circularity rule 3 exists to catch. | the label source: NBAC perimeters vs VIIRS thermal | change in the band ranking and in auc_px, scenario-held-out folds | Needs a pack | *none yet* |
| **E-9** | Lightning cohort (control) | Absolute skill drops (fewer and harder cases) but the band ranking holds. WRONG IF the ranking changes, which would say human-ignition access signals -- roads, settlement -- were driving it. | fires filtered to NFDB CAUSE = lightning | auc_px, scenario-held-out folds, restricted cohort | Runnable now | `post-hoc readout on the v2 band sweeps (sweep_bands_*_v2), natural-cause fires only (Q42 option 2), when they return` |
| **E-10** | Negative control (control) | The noise arm is within noise of 0.5, and the real-band arm clearly beats it. WRONG IF the noise arm sits clearly above 0.5: then a POSITIONAL PRIOR -- where burn tends to sit in a tile, learnable from zero padding without reading a band -- inflates every arm in this register, and must be subtracted before any of them is quoted. | the input: the 9 surface bands vs fresh Gaussian noise of the same width | auc_px, scenario-held-out folds against chance, and against the real-band arm | Concluded | `Fire_Risk_FW SCRATCH_DATA=$HOME/scratch/stage2_fire_cffdrs_v2 SETS=neg SUBMIT=1 bash scripts/shell/sweep_axes.sh` |
| **E-26** | Within-fire burn pattern | Imagery separates burned from unburned pixels INSIDE fire patches at least as well as it does across all patches, because inside a perimeter the outcome is fuel, terrain and firebreaks rather than whether a fire started. WRONG IF within-fire skill is clearly lower, which would say most unconditional skill comes from recognising WHICH patches burned -- between-patch discrimination, not fuel. | the training cohort: all scenes vs fire patches only, with each fold's locations held fixed | auc_px, scenario-held-out folds within fire tiles vs overall; and both models scored on the SAME fire tiles | Concluded | `Fire_Risk_FW SCRATCH_DATA=$HOME/scratch/stage2_fire_cffdrs_v2 SETS=cond SUBMIT=1 bash scripts/shell/sweep_axes.sh` |
| **E-43** | Date-only control (control) | Day of year and latitude alone separate fire from non-fire at about chance. WRONG IF they do not: the pseudo-date rule for negatives would then be a shortcut every arm can read. | date features only (day-of-year sin/cos, latitude) | between-patch AUC | Partial result | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` |
| **E-54** | Legacy composite leakage | For fires that started before 30 June, the legacy April-June composite already shows the burn: on burned pixels its NIR-SWIR1 index (B8, B11) is lower than in the pre-fire composite ending D-1, relative to the same change on the patch's unburned pixels, and the drop grows with the days between the fire's start and 30 June. Fires starting in July or later show no drop. WRONG IF the early fires show no drop: then the v1 imagery did not read the outcome, whatever its weather did. | composite: legacy April-June of the patch year vs pre-fire (D-45 to D-1, extended to D-90, else last summer) | difference-in-differences of the B8/B11 index (legacy minus pre-fire, burned minus unburned pixels) per fire patch, against days of overlap (30 June minus D) | Concluded | `Fire_Risk_Model/scripts/python/build_prefire.py` |

### Index baselines

| ID | Experiment | Hypothesis | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|---|
| **E-11** | Greenness vs moisture indices ★ | `both` beats `greenness` by a small but fold-consistent margin, because direct water absorption at 1610 nm carries information a greenness proxy cannot; and `moisture` (2 bands) draws with `greenness` (5 bands). WRONG IF `both` does not beat `greenness`, which would say the 1610 nm moisture signal adds nothing this label can see -- a publishable null, and one that would weaken the case for the SWIR chain considerably. | the index family given to the model: greenness (NDVI, EVI, VARI, NDRE) / moisture (NDMI, MSI) / both / raw bands | the paired difference in auc_px, scenario-held-out folds, against greenness | Concluded | `Fire_Risk_FW SCRATCH_DATA=$HOME/scratch/stage2_fire_cffdrs_v2 SUBMIT=1 bash scripts/shell/sweep_indices.sh` |
| **E-12** | Index baseline vs learned bands | The learned model on raw bands beats every index family, because an index is a fixed projection that discards information a model could use. WRONG IF indices match it, which would be a strong argument for shipping indices -- cheap on an FPGA and interpretable to an operational user. | hand-built indices vs the learned model on raw bands | the paired difference in auc_px, scenario-held-out folds | Concluded | `Fire_Risk_FW SCRATCH_DATA=$HOME/scratch/stage2_fire_cffdrs_v2 ARMS=raw,both SUBMIT=1 bash scripts/shell/sweep_indices.sh` |
| **E-59** | Indices as model inputs | For the P6 ecology estimators, giving the model every index its bands can form, alongside the raw bands, lowers error at matched band count, most at small k (k <= 4), under the sensor noise model; indices alone do worse than raw + indices. WRONG IF raw + indices beats raw at no k (spatial-block paired CI spanning 0 at every k, every target). | input mode at each nested band set: raw bands / indices only / raw + indices (an index enters only when its bands are in the set); same bands, folds and seeds | per-target held-out error (RMSE for percent conifer, closure, height; balanced accuracy for fuel family), noisy and noise-free | Concluded | `Fire_Risk_FW/scripts/shell/sweep_eco.sh` |

### Covariates

| ID | Experiment | Hypothesis | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|---|
| **E-13** | Weather representation | BOTH is within noise of CODES. The FWI codes already integrate the same 91 days through a recursion tuned over decades, so our 12 features are unlikely to extract much the codes have not. WRONG IF BOTH wins clearly -- then check DIMENSIONLESS, because a gain that disappears there came from absolute level, which at 45-70 N is latitude wearing a weather costume. | the scalar columns the fusion head sees: FWI codes / our 12 compressed history features / both / dimensionless history | the paired difference in auc_px, scenario-held-out folds, against codes | Closed, no result | `sweep_covariates.sh SETS=weather` |
| **E-14** | Fusion architecture | Both fusion variants beat rasters_only, and two_head is within noise of bottleneck. The CFFDRS-shaped separation is expected to cost little; if it costs a lot, the architecture argument has to give way to the measurement. WRONG IF rasters_only matches both, which would say the weather scalars add nothing at this label and sample size -- and would make E-13 moot. | how weather enters: not at all / two-head late / bottleneck | the paired difference in auc_px, scenario-held-out folds | Closed, no result | `sweep_covariates.sh SETS=fusion` |
| **E-15** | Imagery vs the FBP formula | Imagery plus the FMC scalar beats the scalar alone, substantially. The FBP equation is a function of latitude, longitude, elevation and date only -- it carries no information about the stand -- so a null here would be surprising, and would cast doubt on the imagery rather than vindicate the formula. | the FBP foliar-moisture scalar alone vs that scalar plus all 9 surface bands | the paired difference in auc_px, scenario-held-out folds | Closed, no result | `sweep_covariates.sh SETS=g1` |
| **E-16** | FMC arms | None. The arms are identical by construction, so no prediction is possible and any apparent difference would be seed noise. | baseline / measured / augment foliar moisture | (none obtainable) | No label exists | `-- (do not run)` |

### CFFDRS gaps

| ID | Experiment | Hypothesis | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|---|
| **E-17** | Station-density stratification | The imagery increment grows with distance to the nearest station. Fuel moisture is the integral of weather, so a satellite estimate should be worth most where the weather grid is interpolated from furthest away -- the north, which is also where most area burns. | distance from each patch to the nearest fire-weather station | the imagery increment in auc_px, scenario-held-out folds, stratified by that distance | Concluded | `Statistics scripts/make_results_package.py --phase P7f --run narval_results/slots_v2/7289478 (station_km from the development pack)` |
| **E-18** | Snow-off startup | Correcting the start date changes DC and DMC materially above 55 N and improves skill there, with little effect in the south. Our flat 90-day spinup starts around 1 April into frozen, snow-covered ground, so the spurious drying should scale with latitude. WRONG IF, above 55 N, the imagery start-up neither moves the median lag-1 DC by 10 % or more against the ERA5 rule nor raises the between-patch AUC of DC or FWI with a CI above 0. | FWI start date: the Appendix C-2 start-up keyed to a Sentinel-2 snow-off date per patch (the E-60 classifier, SWIR allowed and VNIR only) vs keyed to ERA5-Land snow (E-51's operational rule) vs our flat 90-day spinup | change in the FWI codes by latitude band, and between-patch AUC of DC, DMC, BUI and FWI (paired by patch, block bootstrap) | Concluded | `Fire_Risk_Model/scripts/python/build_s2_startup.py` |
| **E-19** | Latitude-banded weather | History beats codes at high latitude specifically, and not in the south. The day-length factors are tabulated for ~46 N, so the codes should be least trustworthy where that assumption is furthest from the truth. WRONG IF the gain is uniform across bands, which would make the mechanism something other than day length. | the E-13 weather contrast, scored separately in 0-55 / 55-60 / 60-90 N on the same trained models | the INTERACTION: (history - codes) in 60-90 N minus the same in 0-55 N, paired by fold | Concluded | `Fire_Risk_FW SUBMIT=1 EXP_NAME=slots_e19 CONFIGS=r2,r2_daylat bash scripts/shell/sweep_slots.sh` |
| **E-20** | Weather staleness | Skill decays with weather age, fastest for CODES and slowest for the dimensionless history. This is the testable half of a claim fwi.py already makes from input drift alone (DC 8.2% over three days against ISI's 89.9%). WRONG IF decay is flat, which would mean a daily uplink costs nothing and the slow-code argument is unnecessary. | the age of the weather at inference: 0 / 24 / 48 / 72 h / 7 d | auc_px, scenario-held-out folds vs weather age, per weather arm | Concluded | `Fire_Risk_FW SUBMIT=1 EXP_NAME=lags_v2 CONFIGS=r0_scanfi,r2 SCORE_LAGS=1,2,3,7 SCORE_LAG_INPUTS=ffmc,dmc,dc,isi,bui,fwi,wx FITS_PER_TASK=8 SCRATCH_DATA=$HOME/scratch/stage2_fire_cffdrs_v2_lags bash scripts/shell/sweep_slots.sh (per-input half; run_slots --score-lag-inputs). First half: Fire_Risk_FW SUBMIT=1 EXP_NAME=lags_v1 CONFIGS=r0_scanfi,r2,r2_age7 SCORE_LAGS=1,2,3,7 SCRATCH_DATA=$HOME/scratch/stage2_fire_cffdrs_v2_lags bash scripts/shell/sweep_slots.sh (run_slots.py --score-lags, A-50)` |
| **E-21** | Fuel-layer refresh | A positive slope: the advantage of a refreshed estimate grows with the staleness gap. At gap 0 our estimate should LOSE, because it is a noisy copy of its own training target -- which is why the slope and not the level is the estimator. WRONG IF the slope is flat or negative. (This clause restates the prediction's negation; it was written 2026-10-24, after P2's inventory-half result, and changes nothing it predicts.) | the fuel inventory's vintage (SCANFI v2 2005-2020, pre-fire steps only), and later our refreshed estimate, against the gap to the fire year | the SLOPE of auc_px, scenario-held-out folds against staleness, not the level | Partial result | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` |
| **E-22** | Ecology arm ★ | The ranking from dense SCANFI labels differs from the fire-outcome ranking, and SWIR ranks higher in it. Structure and biomass retrieval leans on SWIR more than a burn outcome does, because the outcome is diluted by ignition and weather. If the two rankings agree, that is a strong convergent result for whichever bands win. WRONG IF the first SWIR band (B11 or B12) enters the combined-skill nested set no earlier than B11 entered the fire-outcome search (median rung 3.5 over E-2's folds), taking the median over E-22's outer folds and seeds. | the same band searches, against SCANFI structure instead of a burn outcome | per-pixel error on cover, closure, height, biomass, species | Concluded | `Fire_Risk_FW/scripts/shell/sweep_eco.sh` |
| **E-50** | Latitude-correct day length (R0) | Scaling the DMC day-length factors from 46 N to each patch's latitude raises DMC more at >=60 N than at <55 N (longer summer days), and raises R0's between-patch AUC of DMC and BUI more in the north. WRONG IF the DMC shift is uniform across bands. The AUC half rests on 19 northern fire patches and is read only beside the shift. | DMC day-length factors: Van Wagner's 46 N table vs the same table scaled by astronomical day length at the patch latitude over that at 46 N (our construction) | DMC and BUI shift by latitude band; between-patch AUC per band | Partial result | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` |
| **E-51** | Operational start-up (R0) | The GLC-X-42 Appendix C-2 start-up (codes begin 3 days after ERA5-Land snow cover is gone, or after 3 days at or above 12 C at 13:00 where snow is absent) with an overwintered DC moves DC and DMC at D-1 more at >=60 N than at <55 N, compared with a flat 90-day spin-up from the default start values, and its effect on R0's between-patch AUC is larger in the north. WRONG IF the code shift does not grow with latitude. This is E-18's mechanism under the operational rule; E-18's imagery arm is P6. | start-up: flat 90-day spin-up from FFMC 85 / DMC 6 / DC 15 vs Appendix C-2 start-up with overwintered DC (cffdrs coefficients a = b = 0.75) | DC and DMC shift at D-1 by latitude band; between-patch AUC per band | Partial result | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` |
| **E-53** | Weather staleness under R0 | R0's between-patch AUC decays with the age of the weather (D-1, D-2, D-3, D-7), fastest for FFMC and ISI and slowest for DC and BUI. WRONG IF the fast codes do not lose more than the slow ones by D-7. This is E-20's mechanism without learning: the curve E-20's learned arms are compared with. | weather age at scoring: 1, 2, 3, 7 days before D | between-patch AUC per code against weather age | Partial result | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` |
| **E-60** | Snow-off without SWIR | Judged against the snow-off date measured at ECCC climate stations (observed snow on ground), a per-station snow-off date from visible and NIR Sentinel-2 bands alone has a median absolute error of at most 7 days and is no more than 3 days worse than the best set that may use SWIR1 (the NDSI family). WRONG IF the VNIR-only error exceeds 7 days or is more than 3 days worse: snow-off then needs the SWIR chain, which counts toward its cost in P12. | bands available to the per-observation snow classifier: VNIR only vs VNIR + SWIR1 (+ SWIR2), each searched as nested sets inside training folds of station blocks | median and 90th-percentile \|S2 snow-off - station snow-off\| (days) per station-year; per-observation snow accuracy against the station's snow on ground that day; downstream, the FWI start-up change (E-18) | Concluded | `Fire_Risk_FW/scripts/shell/sweep_snow.sh` |
| **E-64** | LFMC: simulation-trained, Sentinel-2 empirical, FBP equation | (a) Both spectral LFMC estimates -- the simulation-trained retrieval (PROSPECT-D + 4SAIL with the noise model, never fit to Globe-LFMC) and the best empirical Sentinel-2 model fit on Globe-LFMC with site-grouped cross-validation (calibrated NDMI, MSI or NMDI, or a GPR on the bands) -- beat FBP's foliar moisture equation on conifer records. (b) The empirical model beats the simulation-trained one, by less than 10 LFMC points of RMSE. WRONG IF (a) either estimate's RMSE minus the equation's has a site-bootstrap CI reaching 0; or (b) the simulation-trained retrieval wins, or loses by more than 10 points. | LFMC source: FBP equation (latitude, longitude, elevation, date); simulation-trained retrieval; calibrated index models; GPR on Sentinel-2 bands | RMSE, bias and R2 against gravimetric LFMC, Globe-LFMC 2017+ in Canadian-relevant species, development sites, paired by record, bootstrap over sites; per species and season | Concluded | `P6f: Statistics scripts/simulate_lfmc.py and Model pair_globe_lfmc.py (both run, bundle lfmc_v1); then on Nibi Fire_Risk_FW SEEDS="0 1 2" SUBMIT=1 bash scripts/shell/sweep_lfmc.sh (FW 2544d00)` |
| **E-65** | LFMC: simulation retrieval with fold-wise narrowed priors (P6f-v2) | Registered 2026-11-05, before any v2 result (A-51). With the prior cut, inside each outer site fold, to the LFMC range of that fold's training records by species and season, the simulation GP on the ten bands, on conifer records: (a) has a bias within +-10 LFMC points; (b) beats prior_mean_fold, the training stratum mean; (c) beats FBP's equation; (d) loses skill without B12 on jack and red pine (E-29). WRONG IF (a) \|bias\| >= 10; (b), (c) the site-bootstrap CI of its RMSE minus the comparator's reaches 0; (d) the CI of no_b12 minus all10 reaches 0. | prior: lfmc_v1 (60-250 %) or fold-wise narrowed by species x season; band set all10 or no_b12; controls prior_mean_fold and FBP's equation | RMSE, bias and R2 against gravimetric LFMC on the development records, paired by record, bootstrap over sites; per species and season | Concluded | `Fire_Risk_FW EXP_NAME=lfmc_v2 SEEDS="0 1 2" SUBMIT=1 bash scripts/shell/sweep_lfmc.sh (run_lfmc.py; same lfmc_v1 bundle, v1 arms rerun beside the new ones)` |

### Hyperspectral

| ID | Experiment | Hypothesis | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|---|
| **E-23** | SWIR band placement | The best four cluster near 1240, 1610 and 1680-1730 nm, with the fourth in the 1500s. From brief hypotheses H1 and H3: resolving a dry-matter change needs two water-sensitive bands with different water-to-dry-matter absorption ratios. | any 4 centres and widths in 1003-1359 and 1414-1749 nm (140 usable channels) | retrieval error per candidate set | Concluded | `fetch_aviris.py + ingest_aviris.py` |
| **E-24** | 1209 vs 1240 nm | 1240 nm is slightly better for water sensitivity and 1209 slightly better for O2 margin, with the difference small enough that the flown WorldView-3 centre is defensible. A large difference either way is the interesting outcome. WRONG IF (made testable 2026-11-11, before the run) the paired combined-skill difference has its 95 % CI wholly outside +-0.005. | WorldView-3's flown centre against Gao's NDWI band | retrieval error, and O2 absorption margin | Runnable now | `Fire_Risk_FW SCRATCH_DATA=$HOME/scratch/aviris_v4 EXP_NAME=hs_e24_e25 SIZES=64x2 SETS='sensor_mantis_ms_plus_swir e24_slots_1210 e25_vnir6_swir_all sensor_mantis_vnir6' SUBMIT=1 bash scripts/shell/sweep_hs_arch.sh` |
| **E-25** | Spectral resolution: HS vs MS | Diminishing returns beyond roughly 10-15 well-placed bands, so the HS mode's 96 channels buy little over a well-chosen MS set. WRONG IF the curve keeps climbing, which would make the HS mode the better instrument and change the payload decision. | 140 SWIR channels at 5 nm vs the best 4-6 broad bands | retrieval error vs channel count | Runnable now | `Fire_Risk_FW SCRATCH_DATA=$HOME/scratch/aviris_v4 EXP_NAME=hs_e24_e25 SIZES=64x2 SETS='sensor_mantis_ms_plus_swir e24_slots_1210 e25_vnir6_swir_all sensor_mantis_vnir6' SUBMIT=1 bash scripts/shell/sweep_hs_arch.sh` |
| **E-61** | Best SWIR bands, searched broadly | For the ecology targets, the best 4-band SWIR set within standard InGaAs (1000-1750 nm) recovers at least 90 % of the error reduction of the best 4-band set allowed to reach 2000-2400 nm (extended InGaAs), with the VNIR set fixed. WRONG IF allowing 2000-2400 nm improves any target by more than 10 % of its standard-window gain, with a CI excluding 0: then structure retrieval pays for the extended detector. Reported alongside, not predicted: how much of each optimum a vendor filter set (e.g. the best 4 of DFA's 12) recovers. | SWIR band sets from a broad grid (centres every 10 nm, FWHM 20-100 nm, in 1003-1359, 1414-1749 and 1970-2400 nm, A-22), nested k = 1-4, per detector window; vendor sets as reference points | per-target held-out error on AVIRIS-NG (20 m, labels SCANFI v2 2020), spatial-block folds by flight line, under the noise model | Partial result | `Fire_Risk_FW/scripts/shell/sweep_hs.sh ARMS='swir_std swir_ext references'` |
| **E-62** | Best VNIR bands, searched broadly | The best 6-band VNIR set from a broad grid includes at least one band in 700-760 nm (red edge), and the best 6-band set with no band there is at least 5 % worse on percent conifer and canopy closure. WRONG IF the best set has no red-edge band, or the best no-red-edge set is within 5 % on both targets. | VNIR band sets from a broad grid (centres every 10 nm, FWHM 10-100 nm, 400-1000 nm), nested k = 1-6; the same search with 700-760 nm excluded; vendor sets (e.g. DFA's standard 6) and Sentinel-2's bands as reference points | per-target held-out error on AVIRIS-NG and, for Sentinel-2's bands, on the P6 ecology pack; under the noise model | Partial result | `Fire_Risk_FW/scripts/shell/sweep_hs.sh ARMS='vnir vnir_no_red_edge references'` |

### Hardware

| ID | Experiment | Hypothesis | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|---|
| **E-27** | Cost per input channel | BRAM scales roughly linearly with input channel count, so 96 channels are infeasible on the target part and 11 are affordable. Stream BRAM is ceil(width/18) x ceil(depth/1024) and width never stops paying. WRONG IF scaling is sub-linear because the first convolution dominates, which would make a wide input cheaper than the marginal-cost argument assumes. | input channel count: 3 / 6 / 10 / 11 / 96 | BRAM, DSP, LUT and latency from a real conversion | Concluded | `Fire_Risk_FW export_eco_qonnx.py --in-ch 3/11/16/22/96 + the FINN build via finn.sh; vitis_ai.sh inspect; Statistics scripts/make_hw_mantis_package.py` |
| **E-28** | Co-registration tolerance | Negligible cost below a quarter pixel, material by one pixel. WRONG IF a half-pixel shift already costs materially, which would tighten the dichroic and focal-plane alignment budget; or if two pixels cost little, which would retire the registration risk. | SWIR-channel shift at evaluation: 0, 0.25, 0.5, 1, 2 px, on a model trained with the channels registered | the drop in auc_px, scenario-held-out folds against the unshifted score, paired by fold | Concluded | `Fire_Risk_FW SCRATCH_DATA=$HOME/scratch/stage2_fire_cffdrs_v2 SETS=shift SUBMIT=1 bash scripts/shell/sweep_axes.sh` |
| **E-48** | Hardware decision | The chosen model fits a Q8 at <= 80 % of every resource. WRONG IF only the Q9 fits, or none does. | board (Q7, Q8, Q9) x model x input channels | BRAM / DSP / LUT, latency, power (A-29) | Partial result | `Fire_Risk_FW scripts/check_eco_convert.py, export_eco_qonnx.py + the FINN build via scripts/finn.sh, scripts/vitis_ai.sh inspect; then Statistics scripts/make_hw_mantis_package.py` |
| **E-66** | What each Dragonfly Mantis mode would offer | Registered 2026-11-06 on James's approval, before any result (PLAN_NEXT section 6; Chameleon and Caiman left out). On AVIRIS-NG with hs_v4's folds: (1) the custom Mantis MS block (490, 560, 665, 705, 740, 865) beats DFA's standard block as published; (2) MS custom alone beats Mantis SWIR alone (best 4 of DFA's filters); (3) all HS channels 470-900 nm are within one paired SE of MS custom; (4) MS custom + the best 4 DFA SWIR filters beats MS custom alone; (5) RGB scores below every MS set. WRONG IF, for (1), (2) and (4), the paired CI reaches 0; for (3), HS leads by more than one SE; for (5), RGB ties an MS set. | Mantis band set: RGB, MS standard (as published; rule-7-clean subset), MS custom, HS (all 81 surface channels; 6 chosen in orbit), SWIR (4 of DFA's 10 usable filters), MS + SWIR | combined skill and RMSE per head on SCANFI labels, paired by fold and seed with hs_v4; lidar height for the leading rows | Concluded | `Fire_Risk_FW ARMS="references dfa_swir_alone dfa_swir_on_custom dfa_swir_on_standard dfa_hs_select" GRID=configs/noise/p12_sensors_grid.json SCRATCH_DATA=$HOME/scratch/aviris_v4 EXP_NAME=sensors_v1 SUBMIT=1 bash scripts/shell/sweep_hs.sh` |
| **E-67** | VNIR against SWIR: the Mantis cameras' models at every size | Registered 2026-11-10 on James's request, before any result. On AVIRIS-NG with hs_v4's folds and seeds, per-pixel models from 16x2 to 256x3, raw + indices with noise: (1) the VNIR standard block beats SWIR alone (DFA L4 L6 L9 L11) at every size; (2) VNIR + SWIR beats VNIR alone at the largest size (256x3), so SWIR's gain is not a small-model effect; (3) for each camera the best size is within 0.005 of 64x2. On Sentinel-2 (U-Net ladder, E-47's design): (4) adding B11 to the Mantis VNIR stand-in raises the best rung's skill. WRONG IF, for (1), SWIR alone ties or beats VNIR at any size; for (2) and (4), the paired CI reaches 0; for (3), a size beats 64x2 by more than 0.005. | camera (VNIR standard block with pan; SWIR 4 filters; both) x model size (hidden units x layers on AVIRIS-NG; base_ch x depth on Sentinel-2) | combined skill and RMSE per head, paired by fold and seed with hs_v4 / eco_v3; parameters and MACs per pixel | Concluded | `Fire_Risk_FW SCRATCH_DATA=$HOME/scratch/aviris_v4 EXP_NAME=hs_arch SUBMIT=1 bash scripts/shell/sweep_hs_arch.sh (run_hs_arch.py); and BANDS=B2,B3,B4,B7,B8A,B11 EXP_NAME=arch_mantis_both SUBMIT=1 bash scripts/shell/sweep_eco_arch.sh` |
| **E-68** | SWIR2's potential on the general track: the consensus sets with and without B12 | Registered 2026-11-10 and revised 2026-11-11, before any run, on James's E-46 answer (A-55): SWIR2 is unlikely to fly, so it is priced on the general (Sentinel-2) track only and kept out of every Mantis run. On the Sentinel-2 U-Net ladder, E-47's design: B12 raises the best rung's skill in both pairs, k=5 (B4 B5 B8A B11 B12) against k=5 without B12, and k=8 (B3 B4 B5 B6 B8 B8A B11 B12) against k=8 without B12. WRONG IF, in either pair, the paired CI of the best-rung difference reaches 0. | B12 (SWIR2, 2190 nm) present or absent in each Sentinel-2 consensus set, at every model size | combined skill and per-head RMSE, paired by fold and seed with arch_k5 / arch_k8 (same folds, seeds and noise) | Concluded | `Fire_Risk_FW BANDS=B4,B5,B8A,B11 EXP_NAME=arch_k5_no_b12 SUBMIT=1 bash scripts/shell/sweep_eco_arch.sh; BANDS=B3,B4,B5,B6,B8,B8A,B11 EXP_NAME=arch_k8_no_b12 SUBMIT=1 bash scripts/shell/sweep_eco_arch.sh` |

### Out of reach

| ID | Experiment | Hypothesis | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|---|
| **E-29** | T1 live foliar moisture | From Jolly et al. (2014), the brief's lead hypothesis H1: dry matter, not water content, drives seasonal conifer LFMC, so water-only bands will return EWT rather than LFMC and a two-band water contrast is required. Restated testably on 2026-11-03, before any simulation or score: with Sentinel-2's bands, the simulation-trained retrieval (E-64) has lower LFMC error on Globe-LFMC jack and red pine with B11 (1610 nm) and B12 (2190 nm) than with B11 alone. WRONG IF removing B12 does not raise that RMSE with a site-bootstrap CI excluding 0. Reported alongside, not predicted: the same contrast in spring (April-June, the dip) and in summer. | the simulation-trained retrieval's Sentinel-2 bands: all ten 10/20 m bands; the same without B12; without B11 and B12 (VNIR floor) | RMSE and bias against gravimetric LFMC, Globe-LFMC jack and red pine 2017+, development sites, paired by record, bootstrap over sites | Concluded | `P6f (E-64's runs): the no_b12 arm of Fire_Risk_FW/scripts/shell/sweep_lfmc.sh` |
| **E-30** | T2 curing / NPV fraction | Brief hypothesis H2: SWIR2 is necessary for curing and 1240 nm is not a substitute, because the cellulose/lignin feature near 2100 nm is what separates NPV from soil. Untestable here: no curing label, no grassland, and the band is past the detector. | grass curing fraction | error against field curing | No label exists | *none yet* |
| **E-31** | Fire occurrence prediction | None offered. Out of scope by decision, and a hypothesis recorded for work that will not run invites being mistaken for a finding. | ignition probability per cell-day | (out of scope) | No label exists | `-- (out of scope)` |

## Hypotheses and conclusions

Each experiment carries a falsifiable **prediction** and the condition that would refute it, then what could be **concluded** either way. The conclusion field is what decides whether an experiment deserves GPU time: one whose null result teaches nothing is not worth queueing, and writing it down is how that gets noticed before the run.

The hypotheses are written to be capable of being wrong. `CLAUDE.md` is explicit that the study's job is to **test** the brief's hypotheses rather than confirm them, so each states what being wrong would look like. Where a prediction comes from the brief (H1, H2, H3) it is attributed; the rest are this study's own and carry no more authority than that.

### CFFDRS mirror

**E-32 — CFFDRS as is (R0)**

*Hypothesis:* FBP head-fire intensity ranks burned pixels above chance within fire patches, and FWI/BUI ranks fire above confuser patches. WRONG IF the physics scores sit at chance on both: then the outcome measures something CFFDRS does not rate, and every imagery delta would be against a meaningless floor.

The non-learned reference every imagery slot is measured against -- CFFDRS itself, not a model trained on its inputs.

*Note:* P2, legacy design (docs/results/P2/p2_r0): SUPPORTED. Within fire patches, FBP HFI AUC 0.676 [0.65, 0.70] on pre-fire SCANFI, 0.623 on CWFIS 2019; half that margin is water and non-fuel (land only: 0.589, 0.558). Between patches FWI 0.738, BUI 0.765, DC 0.828; fire beats its own confuser on DC in 88 % of 68 pairs. P(sustained flaming) is ~0.5 within patches: NBAC is not an ignition outcome (Stage C is). P3, dated design: SUPPORTED. Within HFI 0.681 (SCANFI), dated minus legacy +0.005 [-0.002, +0.012]; between: patch-mean HFI 0.863, BUI 0.878, FWI 0.841.

*Blocked on:* legacy 30-June design only; P3 re-dates the weather to each fire's start

**E-33 — Fuel inventory comparison**

*Hypothesis:* Pre-fire inventories (CWFIS 2019 and 2014b, the SCANFI v2 pre-fire step) give R0 skill within noise of each other, and the post-fire ones (CWFIS 2024, SCANFI 2025) score far higher. WRONG IF a post-fire inventory does NOT inflate skill: then the leakage measured in A-25 does not reach the outcome.

Which operational fuel input is honest on burned ground, and how much a post-fire inventory would flatter a result.

*Note:* P2 (docs/results/P2/p2_r0): REFUTED on both counts. Pre-fire inventories are not equal: SCANFI through the CFS tree beats CWFIS 2019 by +0.053 [+0.037, +0.071] within-patch HFI AUC (+0.031 on land only; resolution alone adds nothing once water is masked). Post-fire inventories DEFLATE R0: CWFIS 2024 0.21, SCANFI 2025 0.49. The leak reaches the outcome (+0.41 AUC) but unlearned physics reads it backwards; a learner would not. The CFS tree beats the A-11 rules by +0.081 on land. Re-scored 2026-11-10 with SCANFI 2005: 0.668, 2010 0.671, 2015 0.675 within-patch HFI AUC (83 fire patches each). 2026-11-11 (runs/20261111-e33_cffdrs_r0, A-54): SCANFI v2 vs v1.2, both 2020, +0.005 [-0.004, +0.014] within-patch HFI AUC (+0.003 on land), though the two maps agree on a median 49 % of fuel codes on the 99 fire patches. Every registered inventory is now scored.

*CFFDRS gap:* G2 fuel-type layer is a fixed vintage

**E-34 — Learned CFFDRS (R1/R2)**

*Hypothesis:* A model given exactly the CFFDRS inputs (R1) beats R0, and physics plus a learned residual (R2) is within noise of R1. WRONG IF R1 does not beat R0, which would say the outcome is already as predictable from CFFDRS inputs as CFFDRS makes it.

The learned baseline the imagery slots are added to, and whether the physics layer costs or buys anything.

*Note:* P5: SlotNet R0-R2 written (Fire_Risk_FW cffdrs_net.py); R2 starts as R0 by construction. P7 (docs/results/P7/p7_slots): MIXED. R1 - R0 within +0.051 [+0.034, +0.068], 5/5 folds; R2 - R1 within -0.025 [-0.034, -0.015], between -0.006 (CI spans 0). Against the FWI CWFIS issued (P7b): R1 +0.042, R2 +0.035, R4 +0.035 between patches, every CI spanning 0. Q29.3: whether R2's within-patch gap to R1 closes is E-58.

**E-35 — Fuel-type slot**

*Hypothesis:* Imagery-derived fuel type improves within-patch skill over the pre-fire operational layer. WRONG IF the shuffled-imagery twin gains as much, which would make the gain a shortcut.

Whether the imager should refresh FBP fuel type.

*Note:* P5: the cffdrs half runs now (r2 vs r2_cwfis: SCANFI tree vs CWFIS 2019 under R2); the imagery replace form waits for E-22. P7: CWFIS 2019 vs SCANFI fuel under R2 -0.007 [-0.017, +0.003] within (under R0 -0.048): learning absorbs most of the inventory gap. 2026-11-10: eco_fire ran; slots_e35/20261110-1901 came back with 48 of 105 fits (R2 15/15, each replace config 3-9/15). Tasks 1-5 hit the 2:30 limit: the sidecars were auto-chunked across tiles, so a replace fit took 21 min instead of 3 (FW fix: one chunk per tile, re-chunked while staging). Resubmit with RUN_ID=20261110-1901 SKIP_DONE=1.

*CFFDRS gap:* G2 fuel-type layer is a fixed vintage

**E-36 — Percent-conifer slot**

*Hypothesis:* Imagery percent conifer improves M-1/M-2 spread and intensity. WRONG IF no gain survives on mixedwood pixels.

Brief target T4 as a CFFDRS input rather than a map.

*Note:* P5: the imagery_correct form is runnable (pc + 30 tanh(head), through the physics); the imagery_replace form waits for the ecology estimator (E-22, P6). P7: AT RISK. Correct form -0.001 [-0.004, +0.001] within, equal to its twin; the head learned a near-uniform -24-point shift. M-1/M-2-restricted scoring added to run_slots after this sweep. Q29.2: the offset arm (imagery-free constant + imagery deviation) is E-57, alongside these arms.

*Blocked on:* the registered replace form (imagery-estimated percent conifer) runs in slots_e35 (r3_pc_replace), after E-35's eco_fire step

*CFFDRS gap:* G2 fuel-type layer is a fixed vintage

**E-37 — Crown-base-height slot**

*Hypothesis:* Imagery-informed CBH changes crown fraction burned enough to move intensity skill. WRONG IF the CFB term never engages at our fire weather.

Whether stand height from orbit belongs in FBP's crown fire initiation.

*Note:* P5: the imagery_correct form is runnable (CBH x exp(0.7 tanh(head))); the height-derived replace form waits for P6. P7: AT RISK. Correct form -0.0005 [-0.003, +0.002], equal to its twin; CFB > 0 on 47 % of burnable pixels, so the falsifier did not fire. Height-derived form waits for P6. 2026-11-10: the replace form is built (A-53, PLACEHOLDER ratio: CBH = ST-X-3 default x eco height / the fuel's median SCANFI height, bounded 0.25-4) and rides with E-35's slots_e35 resubmission on the same sidecars.

**E-38 — Curing slot**

*Hypothesis:* Imagery curing beats the CWFIS curing product on O-1 pixels. WRONG IF it does not -- but O-1 is about 3 % of burned pixels, so a null is likely to be 'n insufficient'.

The FWI2025 curing input, tested where grass exists.

*Note:* P5: the imagery_correct form is runnable against the cffdrs default (80 %); the CWFIS curing product is still not held, so the operational comparison waits. P7: not tested. The SCANFI fuel tree has no O-1 pixel, so the correction never acts (delta exactly 0). Needs the curing run on CWFIS fuel (O-1b 4.6 % of pixels). Q29.1 (James, 2026-10-26): curing now runs on CWFIS fuel (O-1b on 4.6 % of pixels), against r2_cwfis, scored on O-1 pixels (run_slots by_fuel). The comparison is to the 80 % FBP default; the CWFIS curing product is not held. P7c: PARTIAL. O-1 pixels (60 fires): vs twin +0.021 [+0.007, +0.034], vs R2 on CWFIS fuel +0.013 [+0.002, +0.024] -- against the 80 % default; the CWFIS curing product comparison has not run (product not held). P6b (2026-10-29): CWFIS grass curing (public:grasscuring, 1 km, NDVI-based) is archived only from 2024-01-01, so no fire in 2019-2023 has an issued curing value; the operational comparison needs the 2024-2025 cohort (E-56) or a reconstruction (Q36).

*Blocked on:* the registered comparison is with the CWFIS curing product, which is not held

*CFFDRS gap:* curing

**E-39 — Canopy closure to in-stand moisture**

*Hypothesis:* Imagery stand density sharpens ignition receptivity through the stand-specific FFMC adjustment. WRONG IF the adjusted in-stand FFMC ranks ignitions no better than open FFMC.

The ignition-side slot GLC-X-42 p.32 points at: fuel moisture by canopy closure.

*Blocked on:* instand_ffmc needs Wotton & Beverly (2007) coefficients (Q26); the function exists and refuses to guess

**E-40 — Green-up slot**

*Hypothesis:* An S2 green-up date beats the CWFIS green-up product for the D-1/M-1/M-2 leafless-to-green switch. WRONG IF the two agree to within a few days, leaving nothing to gain.

Whether the imager should own the leaf-state switch FBP applies to aspen and mixedwood.

*Note:* P3: the CWFIS side is built (greenup.py); leaf state on D from the product for 191 patches, climatology for 37. P5: r2_leaf_ablated (leaf state forced green) measures what the CWFIS green-up product is worth under R2. P7: leaf state forced green under R2 +0.001 [-0.002, +0.004]: the CWFIS green-up product adds nothing measurable.

*Blocked on:* the S2 green-up estimator moved to P6 (James, 2026-10-24); P3 builds the CWFIS side (greenup.py). CWFIS green-up 2020-2023 is held, 2019 is not published

**E-41 — Spread R0 (CFSDS)**

*Hypothesis:* FBP ROS correlates with observed daily spread (Spearman rho > 0). WRONG IF it does not, which would bound everything the spread branch can claim.

Stage B's floor. CFSDS v1.1 (90 m, fires > 500 ha, 2002-2024) covers all 99 fire patches: 82 fires, 7,835 fire-days.

*Note:* Development fires, 2026-11-03 (docs/results/P8/p8a_spread, A-46): rho 0.54 [0.49, 0.59], and 0.39 [0.34, 0.44] on days with spread.

*Blocked on:* the frozen test fires are read in P10

**E-42 — Spread slot value**

*Hypothesis:* Fuel-side imagery slots improve per-fire-day spread prediction. WRONG IF only weather-side inputs move it.

Imagery's value on the outcome FBP actually predicts.

*Blocked on:* only 805 of 4,925 fire-days lie on a patch with imagery (A-46)

**E-44 — Ignition R0**

*Hypothesis:* P(sustained flaming) x P(lightning holdover) ranks lightning starts above matched controls. WRONG IF at chance.

Stage C's floor: ignition receptivity, not occurrence (A-28).

*Note:* Design, fixed 2026-11-03 before any score (A-46). A control's weather is its start's, by construction, so within a matched set only fuel and leaf state can differ: P(holdover) and the GLC-X-42 classes are constant inside a set and the product's within-set ranking is P(sustained flaming)'s (Beverly & Wotton 2007, by fuel category). Scored as the matched-set AUC (each start against its own controls, ties 0.5), CI by bootstrap over 1-degree blocks; the pooled AUC beside it. DESIGN CHECK: a weather-only score (FFMC class) must give a matched-set AUC of exactly 0.5; anything else means the weather is not shared. Fuel from the SCANFI step before the start's year (fuel_tree), and from the CWFIS layer before it (2014b for 2017-2019, 2019 with burn scars for 2020-2024) as the operational arm. P9 (2026-11-03, 2021-2024, 758 sets): design check 0.500; SCANFI 0.526 [0.507, 0.545], CWFIS 0.535 [0.512, 0.558]. All years (2026-11-04, 2017-2024, 1,298 sets): design check 0.500; SCANFI 0.530 [0.513, 0.546], CWFIS 0.523 [0.506, 0.539] on 1,213 sets. 2017-2020 alone: SCANFI 0.536 [0.511, 0.561], CWFIS 0.506 [0.484, 0.530]. Above chance, barely; the edge is black spruce over aspen.

*Blocked on:* the lightning holdover model needs the Wotton & Wheatley (2025) GAM table (Q26); calibration is not scored (case-control sampling fixes the base rate)

**E-45 — Ignition slot value**

*Hypothesis:* Closure, green-up and fuel-type slots improve ignition ranking. WRONG IF the shuffled twins gain as much.

Imagery's value on the ignition process.

*Note:* ignition_v1 complete 2026-11-10 (docs/results/P9/p9b_ignition_rungs, 100/100): REFUTED on what ran. r4 - r4_shuffled +0.008 [-0.006, +0.023]; r4 - r2 +0.003; r2 - r0 +0.052 [+0.035, +0.068]; r2_leaf_ablated - r2 +0.003 [-0.006, +0.010] (inconclusive). Imagery adds no ignition skill beyond the CFFDRS inputs. Earlier: ignition_v1 partial 2026-11-05 (36/100 fits): r1 - r0_scanfi +0.052 [+0.033, +0.072] on 1,292 sets; r2 - r0 +0.056 [+0.038, +0.075] on folds 0-3, so prediction 2 fails provisionally; r4, r4_shuffled and r2_leaf_ablated not yet in. A-48 approved by James 2026-11-05: noise-free for now (rule 6 caveat on any band claim); epoch chosen on the inner 15 % of training groups (rule 5, confirmed). Predictions registered 2026-11-05 before any fit: r4 beats r4_shuffled with the paired CI above 0; r2 within +-0.01 of r0; r2_leaf_ablated within +-0.005 of r2. Design 2026-11-04 (A-48), before any fit: conditional logistic loss over each matched set; R2 starts as logit P(sustained flaming); best epoch chosen on a 15 % inner split of the training groups. Green-up is tested by r2_leaf_ablated against r2, imagery by r4 against r4_shuffled. The fuel slot's replace form needs eco sidecars for the points; closure waits for Q26.

*Blocked on:* the fuel slot's replace form needs eco sidecars for the points (E-35's eco_fire step); closure waits for Q26

**E-46 — Band and index decision**

*Hypothesis:* The combined ranking keeps at least one red-edge band and B11 within the Mantis k=6 / k=4 sets. WRONG IF SWIR never earns a slot on any process's weighted evidence.

The CubeSat's bands and indices, presented as options with pros and cons for James to choose (A-49).

*Note:* 2026-11-05 (A-49, docs/results/P12/p12_weights): under six head-weighting schemes the equal-weight search's best set is tied (paired, one SE) with the overall best under five; only maximin separates them, by 0.009 +- 0.009. The best sets are 7-8 bands under every scheme. Consensus 2026-11-05 (docs/results/P12/p12_bands): Sentinel-2 stable at k=1 (B12) and k=5 (B4, B5, B8A, B11, B12; weakest region 10/15), 6-9/15 elsewhere; no AVIRIS-NG SWIR consensus is stable (4-8/15 per 50 nm slot). Re-scores 2026-11-09 (bands_consensus k=1, bands_consensus_v2 k=2-8, all 15/15): each fixed set within ~2 SE of its search; stable k=5 0.4055, 0.010 +- 0.003 below the best; k=8 consensus ties (0.4157). SUPPORTED: B5 and B11 in the stable set.

*Blocked on:* E-35 for the fuel-type slot's value; E-68 for SWIR2's increment on the general track only (not the Mantis track). James chose 2026-11-10 (A-55): both tracks, Mantis first

**E-47 — Architecture decision**

*Hypothesis:* Restated 2026-11-05, before any result (A-49): the onboard model is the ecology estimator (A-41), not the fire network. At E-46's bands, TinyEcologyUNet at the size the bands were ranked with (base_ch 8, depth 2) is within one paired SE of the best rung on the equal-weight combined skill, with sensor noise. WRONG IF only a larger rung (base_ch >= 16 or depth 3) reaches it: then the onboard model is bigger than the band search assumed and E-48 must size for it.

The onboard model, as options (each rung within one SE of the best, with its size, pros and cons). The onboard/ground split follows A-41: structure maps onboard, weather-dependent products on the ground, bounded by E-20.

*Note:* 2026-11-09 (docs/results/P12/p12_arch): at B2 B3 B4 B7 B8A, the Mantis standard-block stand-in, REFUTED: best rung 32x1 (0.413); 8x2 0.011 +- 0.002 below, 16x1 0.005 +- 0.001; only base_ch 32 ties. 32x1 needs the Q8 (0.1 s) or a wider FINN fold on the Q7 (138 s at minimal folding); 16x1 fits the Q7 (35 s). Ladders at E-46's options and the stand-in + B11 (2026-11-10, docs/results/P12/p12_arch): width 32 is best for every band set; 8x2 is 0.011-0.022 below, 16x1 0.005-0.008. k=8 best 0.438, k=5 0.426, stand-in + B11 0.427, stand-in 0.413.2026-11-11: general-track ladders without B12 in (E-68): k=5 no B12 best 32x3, k=8 no B12 best 32x3 (0.438, tied with k=8's 32x1).

*Blocked on:* none for the choice: both tracks' ladders are in. Mantis: stand-in 32x1 (0.413), + B11 32x2 (0.427). General: k=8 32x1 (0.438), k=5 32x3 (0.426); James to choose (A-49)

**E-49 — Dating the weather (R0)**

*Hypothesis:* Moving R0's weather from the legacy 30-June daily aggregates to each patch's D-1 at 13:00 LDT RAISES the between-patch AUC of the fast codes (FFMC, ISI) and LOWERS that of the slow codes (DC, BUI): the fast codes will describe the day before the fire rather than 30 June, and part of the slow codes' legacy 0.83 (DC) came from reading the fire year's drought after most fires had started. WRONG IF the fast and slow codes move in the same direction, or no code moves outside its CI.

Whether the legacy design flattered or hid CFFDRS, and what each design step moves -- the baseline every later delta is read against.

*Note:* P3 (docs/results/P3/p3_dated): REFUTED. Legacy -> dated: FFMC 0.695 -> 0.799, ISI 0.701 -> 0.781, but BUI 0.765 -> 0.878 and DC 0.828 -> 0.830. Year alone scores 0.87, and within a year the fast codes do not gain (FFMC 0.730 -> 0.717) while the slow ones do (DMC 0.673 -> 0.839, BUI 0.691 -> 0.845, DC 0.743 -> 0.827). Dating helps through the slow codes; the prediction had them backwards.

*Blocked on:* needs the same chain on the frozen test set (P10)

**E-52 — Weather source: station vs ERA5 (R0)**

*Hypothesis:* The nearest CWFIS station's reported codes at D-1 rank fire above non-fire patches at least as well as ERA5-Land at 13:00 LDT (they are what CFFDRS actually runs on), and the ERA5-to-station disagreement in the codes grows with distance to the station. WRONG IF the disagreement is flat with distance: E-17's mechanism (weather error grows away from stations) would then have no support in the codes.

How far the reanalysis we use stands from operational CFFDRS input, and whether station distance is a real stratifier for E-17.

*Note:* P3 (docs/results/P3/p3_dated): REFUTED. rho(|ERA5 - station|, distance) -0.03 to +0.05, all CIs span 0 (195 patches, median 56 km). AUC station vs ERA5: FFMC 0.81 vs 0.80, BUI 0.87 vs 0.88, DC 0.78 vs 0.83. P7: under R2, station weather -0.017 [-0.034, -0.001] within and +0.024 [-0.027, +0.076] between, relative to ERA5.

*Blocked on:* 2019 station file now held; needs the frozen test set (P10)

*CFFDRS gap:* G3 station density

**E-55 — Operational FWI grid vs the reconstruction**

*Hypothesis:* The FWI grid CWFIS issued for D-1 ranks fire above non-fire development patches as well as our ERA5-Land FWI does: the two between-patch AUCs are within 0.03 of each other, and the two FWI values agree across patches (Spearman rho >= 0.8). WRONG IF they differ by more than 0.03 with a CI excluding 0, or rho < 0.8: then R0 does not stand in for operational CFFDRS, and every imagery delta measured against R0 or R2 is measured against a different baseline from the one operations use.

Whether R0 can stand in for operational CFFDRS when imagery deltas are reported, and how far it is from it where it cannot.

*Note:* Only the FWI itself is archived before 2024: FFMC, DMC, DC, ISI, BUI and every FBP output start 2024-01-01 (GetCapabilities, 2026-10-26). All CWFIS grids are 2 km, so the comparison is between patches only: an operational map cannot rank pixels inside a 5 km patch. Whether the archive is as issued or reprocessed is not documented (Q30). P7b (docs/results/P7/p7b_operational, 2026-10-26): MIXED. 181 patches: AUC ISSUED by CWFIS 0.860 vs ours (ERA5) 0.851 (-0.009 [-0.073, +0.057], within 0.03); rho 0.76 [0.63, 0.85] (< 0.8). ERA5 runs 3.6 FWI lower (median); 10 of 19 large misses are ERA5 light rain the station did not see, 4 a later snow start-up. Same-year pairs: operational 0.744, ERA5 0.799.

**E-56 — Operational FBP outputs on a 2024-2025 cohort**

*Hypothesis:* On fires that started in 2024-2025, the HFI CWFIS issued for D-1 ranks fire above non-fire patches within 0.03 of our R0 HFI for the same patches and day (between-patch AUC), and the two agree across patches (Spearman rho >= 0.7). WRONG IF they differ by more than 0.03 with a CI excluding 0: the operational inputs our reconstruction replaces (interpolated station weather, the CWFIS fuel grid, its FMC, green-up and curing) then carry, or lose, skill R0 does not.

The first comparison against what operational FBP actually reported. The cohort is also an out-of-time test for every model trained on 2019-2023.

*Note:* Registered with E-55, before any grid value was scored. Runs on both 2024 and 2025 under either training regime (E-63): no learning is involved in the comparison. 2024 half, 2026-10-30 (docs/results/P6/p6b_cohort): PARTIAL. HFI AUC 0.834 ISSUED, 0.837 ours (CWFIS 2024 fuel), gap -0.003 [-0.060, +0.057], rho 0.82; SCANFI 2020 fuel +0.005, rho 0.84. 2025 is frozen and waits for P10 (A-42). 2026-11-10 (eval_e56_fire_type_fmc.py): FMC ISSUED vs ours median difference 0.00, MAE 0.83 points, rho 0.99 (101 patches). The archived 'ft' layer is FBP fire type (splits at CFB 0.1/0.9), not fuel type: no issued fuel-type grid exists, so the registered share-of-area fuel agreement cannot be measured. Substitutes: fire type agrees on 0.703 [0.646, 0.757] of the burnable area (ours calls less intermittent crown, 18 % vs 28 %); fuel/non-fuel 0.89. The earlier 79/111 family agreement was an artefact (every issued code mapped to conifer) and is withdrawn.

*Blocked on:* 2025 half waits for P10 (A-42)

**E-57 — Percent-conifer correction with an imagery-free offset**

*Hypothesis:* Once a learned imagery-free offset absorbs the tile-wide shift (P7-C1), the imagery percent-conifer correction carries information its shuffled twin does not: within-patch AUC on M-1/M-2 pixels beats the twin's (paired group-bootstrap CI above 0), and the imagery part varies more within tiles than the twin's. WRONG IF the real-imagery arm and its twin stay within noise on M-1/M-2 pixels (CI spanning 0): then, at this n, imagery percent conifer adds nothing through the physics even freed of the shift.

Whether the correct form can carry spatial imagery information at all, before the replace form (E-22) exists. Q29.2 (James, 2026-10-26): added alongside E-36's arms, not replacing them.

*Note:* The offset is in units of the bound (pc: 30 points), so it can reach the -24-point shift P7 found at the base learning rate. P7c: SUPPORTED as registered. M-1/M-2: vs twin +0.0065 [+0.0003, +0.0131], imagery-part SD 6.2 vs 0.4; but vs R2 +0.0009 (CI spans 0), and the offset settled at -6 points while the imagery part kept -24.

**E-58 — Closing R2's within-patch gap to R1**

*Hypothesis:* R2's within-patch deficit to R1 (-0.025 [-0.034, -0.015], P7) is an optimisation artefact of starting the residual at zero beside the physics. Either starting the residual from the R1 trained on the same fold and seed (r2_warm) or training it at 10x the learning rate (r2_lr10) brings R2 within 0.01 of R1 within patches, without losing more than 0.01 between patches against R2. WRONG IF both arms stay more than 0.01 below R1 within patches with a CI excluding 0: the gap is then the cost of anchoring the score to the physics, and is reported as such in the P12 architecture choice.

Whether the physics-anchored model (R2-R4) carries a real accuracy cost, which the P12 architecture rule weighs. Q29.3 (James, 2026-10-26).

*Note:* The warm start keeps R2's physics weights at their usual start and copies only R1's network into the residual, so R2 begins as physics + R1. P7c (docs/results/P7/p7c_slots_v3, 2026-10-27): REFUTED. Within patches vs R1: warm -0.033 [-0.048, -0.019], 10x -0.056 [-0.075, -0.038]; the gap is the cost of the physics anchor. Warm start best between patches (0.892; ISSUED by CWFIS 0.857).

**E-63 — Out-of-time generalisation, two training regimes**

*Hypothesis:* (a) Regime B -- trained and selected on 2019-2023 only -- keeps its skill on 2024 and 2025: R1's and R2's between- and within-patch AUC there are within 0.05 of their 2019-2023 cross-validated AUC, and R1 still beats R0 (paired CI above 0). (b) Regime A -- 2024 added to training and selection -- beats regime B on 2025 within patches (paired CI above 0). WRONG IF (a) either rung drops by more than 0.05 with a CI excluding it, or R1 - R0 on 2024-2025 has a CI reaching 0; or (b) regime A minus regime B on 2025 has a CI reaching 0.

Whether the models hold up in a year they never saw -- the condition an operational satellite always predicts in -- and what one more training year buys. 2025 is frozen in both regimes and read once, in P10.

*Note:* James (2026-10-29): 2024 joins training in regime A; 2025 stays frozen as the out-of-time test; regime B excludes both. Regime B makes no use of any choice regime A made with 2024 in view, and its 2024 test is scored before regime A's 2024 training results are looked at. Pack and regimes built 2026-10-30 (A-42). Both regimes ran 2026-11-02 (docs/results/P6/p6e_out_of_time). On 2024, (a) is AT RISK: R1 and R2 fall 0.06-0.11, no CI excludes 0.05, and R1 - R0 between patches is -0.035 [-0.095, +0.021]. R0 itself falls 0.05-0.06. (b) waits for 2025.

*Blocked on:* 2025 is read once, in P10

### Band selection

**E-1 — VNIR band selection**

*Hypothesis:* Red-edge earns a slot: the best six include at least one of B5/B6/B7 and exclude both 60 m atmospheric bands (B1, B9). WRONG IF an atmospheric band survives into the best six, which would say the ranking is reading haze rather than vegetation.

Names the six bands for the Mantis MS mode. The one complete answer the packed data can give today, and it settles one of the three sensor modes outright.

*Note:* First NBAC search done (job 6844532, 6/6 folds; docs/results/band_search_nbac). Open: at k=6 B5 is in 6/6 folds and B7 in 5/6, but B9 is in 4/6, and the k=6 set scores no better than k=1 (0.758 vs 0.766). Replay pending: sweep_replay.sh refits the chosen sets with artefacts under the full-tile evaluation, seeds 0 and 1. 2026-11-10 (A-56, James): re-run on the v2 pack (composite ending the day before each fire; the slot sweeps' 5 folds). Any v1 result above stays as legacy.2026-11-11 (docs/results/P7/p7i_legacy_v2, v2 pack, 5 folds): REFUTED. red edge is in the best six (B5, B6 4/5 folds; B7 3/5) but B1 survives in 3/5 folds; the score is flat from k=3 (0.694) to k=6 (0.696).

**E-2 — All-11 greedy**

*Hypothesis:* B11 enters by k=3, because the NIR/SWIR contrast is the strongest single moisture signal available. WRONG IF it has not entered by k=7, which would be weak evidence against the SWIR chain -- weak, because one band cannot stand in for four.

If greedy reaches for B11 early, the SWIR chain earns a slot on fire-outcome evidence. If it never does, that is weak evidence against, not strong -- one SWIR band cannot test a four-band mode.

*Note:* First NBAC search done (job 6844530; docs/results/band_search_nbac). B11 entry rung per fold: never, 3, 2, 5, 2, 7 -- open. Under the old dNBR label it entered at k=1 in two folds. Replay pending: sweep_replay.sh refits the chosen sets with artefacts under the full-tile evaluation, seeds 0 and 1. 2026-11-10 (A-56, James): re-run on the v2 pack (composite ending the day before each fire; the slot sweeps' 5 folds). Any v1 result above stays as legacy.2026-11-11 (docs/results/P7/p7i_legacy_v2, v2 pack, 5 folds): REFUTED. B11 enters all11's greedy search at k=3, 5, 7, 7 and never in one fold.

**E-3 — Forced-SWIR delta**

*Hypothesis:* Positive but small: under +0.02 auc_px. One band in the window is a poor proxy for a four-band mode, so a large gain would be surprising and a null is not disqualifying.

The marginal value of one SWIR band at equal band count. A lower bound on the SWIR chain: we hold 1 band in the window, the sensor would carry 4.

*Note:* Read through report_arms.py's MATCHED-k section: vnir_swir and vnir are paired rung by rung, not at their deepest rungs, which would set k=7 against k=6. First NBAC search done (job 6844531; docs/results/band_search_nbac): within noise at every k from 2 to 6 (2-SE about +-0.02), so the +0.02 bound is not yet tested. SWIR's gain over vnir fell after the dNBR -> NBAC relabel in 11 of 12 matched-k cells. Replay pending: sweep_replay.sh refits the chosen sets with artefacts under the full-tile evaluation, seeds 0 and 1. 2026-11-10 (A-56, James): re-run on the v2 pack (composite ending the day before each fire; the slot sweeps' 5 folds). Any v1 result above stays as legacy.2026-11-11 (docs/results/P7/p7i_legacy_v2, v2 pack, 5 folds): MIXED. forced B11 against vnir at matched k: +0.005 at k=5, +0.003 at k=6, every k from 2 to 6 within noise: small, not shown positive.

**E-4 — SWIR-only floor**

*Hypothesis:* Clearly above chance and clearly below the VNIR set. The water features at 1200 and 1600 nm are physically present, so a learned model should find something; without the NIR anchor it cannot normalise for canopy structure or illumination. WRONG IF it matches the VNIR set, which would make the MS chain arguable.

The third sensor option -- SWIR instead of MS -- had no number. Structurally a SWIR-only set forms 0 of 12 catalogue indices and 0 ECVs, measured; this says what a LEARNED model does with it anyway, which rule 4 treats as the real question.

*Note:* A quarter of the sensor. Read strictly as a floor. 2026-11-10 (A-56, James): re-run on the v2 pack (composite ending the day before each fire; the slot sweeps' 5 folds). Any v1 result above stays as legacy.2026-11-11 (docs/results/P7/p7i_legacy_v2, v2 pack, 5 folds): SUPPORTED. B11 alone +0.099 [+0.081, +0.116] above chance and -0.097 [-0.123, -0.072] below vnir's k=6.

**E-5 — Leave-one-out band value**

*Hypothesis:* Every individual drop is small, because the pool is redundant. B8 and B8A in particular each look worthless while the pair is not: leave-one-out cannot see mutual substitution, and reading a small drop as 'this band does not matter' is the trap. WRONG IF any single removal costs more than about 0.02, which would mean the pool is far less redundant than the near-duplicate pairs suggest and the chosen set is already minimal.

Per-band value CONDITIONAL on the rest, which is the only kind that means anything when bands are near-duplicates. Cannot see redundancy: B8 and B8A are 23 nm apart, so each may look worthless while the pair is essential.

*Note:* In the first NBAC searches no band clears 2 SE, and in vnir fold 0 removing ANY of the six raised the score: the noise floor, not redundancy, is what the drops show so far (docs/results/band_search_nbac). 2026-11-10 (A-56, James): re-run on the v2 pack (composite ending the day before each fire; the slot sweeps' 5 folds). Any v1 result above stays as legacy.2026-11-11 (docs/results/P7/p7i_legacy_v2, v2 pack, 5 folds): REFUTED. single removals cost more than 0.02: B5 0.029 (all11), B2 0.024, B5 0.023, B3 0.020 (vnir_swir); B8 and B8A each look worthless, as predicted.

**E-6 — Selection stability**

*Hypothesis:* The top two or three bands are selected in 6/6 folds and the tail is unstable. WRONG IF even the top band swings, which would mean the ranking is fold noise and no k is reportable.

6/6 is a finding, 3/6 is a coin flip. Without it a single fold's ranking would be reported as the ranking.

*Note:* WRONG so far, at this budget: no band is chosen at k=1 in more than 1/6 vnir or all11 folds, and the median greedy margin (0.005-0.008) is a tenth of the fold SD. Whether that is the bands or the crop-based evaluation is what the replays decide (docs/results/band_search_nbac). 2026-11-10 (A-56, James): re-run on the v2 pack (composite ending the day before each fire; the slot sweeps' 5 folds). Any v1 result above stays as legacy.2026-11-11 (docs/results/P7/p7i_legacy_v2, v2 pack, 5 folds): REFUTED. the k=1 band (B7) is chosen in 3/5 folds: even the top band swings.

**E-7 — Resolution requirement**

*Hypothesis:* Graceful degradation from 20 to 40 m and a sharper fall by 80 m. WRONG IF 20 -> 40 m already costs materially, which matters more than it sounds: the Mantis MS mode is 32 m at 500 km, so our 20 m results would overstate what the sensor delivers.

How much resolution the retrieval needs -- a mission requirement. The Mantis MS mode is 32 m at 500 km and 39.7 m at 620 km, so ~40 m is the real operating point and every 20 m result in this register is optimistic. This is the information cost only; the pixel-count cost (memory, latency) is E-27's.

*Note:* 'extent' mode (shrink the tile) is refused: it shrinks the input but not the mask, and the loss raises on the first batch. As first wired it would have crashed every 40 m and 80 m run. 2026-11-10 (A-56, James): re-run on the v2 pack (composite ending the day before each fire; the slot sweeps' 5 folds). Any v1 result above stays as legacy.2026-11-11 (docs/results/P7/p7i_legacy_v2, v2 pack, 5 folds): SUPPORTED. 40 m -0.004 [-0.007, -0.000], 80 m -0.009 [-0.014, -0.005].

### Controls

**E-8 — Label independence control**

*Hypothesis:* The ranking is largely preserved. WRONG IF B11's value collapses specifically -- that would say it was reading NBR-like information shared with the perimeter delineation rather than fuel, which is exactly the circularity rule 3 exists to catch.

A band whose value collapses when the label becomes thermal was exploiting the label, not reading fuel. VNP14 keys off 4 and 11 um emission, so it cannot share information with 400-1750 nm reflectance.

*Note:* WAS MARKED RUNNABLE AND WAS VACUOUS. --label was validated, printed and recorded, and never read: LABEL=vnp14 would have trained on the packed mask and confirmed its own hypothesis. sweep_bands.py now refuses any --label that is not the pack's declared label_source. 2026-11-11: root cause found. The label read NASA/LANCE/NOAA20_VIIRS/C2, a near-real-time collection whose archive starts 2023-10-08, after every development fire season. It now reads the archived NASA/VIIRS/002/VNP14A1 (2012 on; FireMask >= 7) and records its granule count. Rebuilt for all 292 patches: fire 99/99 detected (was 6/99), confuser 7/108, cloud 2/22, bare, unburned and water 0.

*Blocked on:* the label is fixed (2026-11-11): what remains is the pack design, a patch-level control or a 1 km FireMask raster (Q43)

**E-9 — Lightning cohort**

*Hypothesis:* Absolute skill drops (fewer and harder cases) but the band ranking holds. WRONG IF the ranking changes, which would say human-ignition access signals -- roads, settlement -- were driving it.

Human ignitions carry a roads-and-settlement signal that a model can read off the imagery instead of the fuel. If the ranking holds on lightning fires only, it is about fuel.

*Note:* Was listed as 'needs code'; the code exists, the data does not. 2026-11-11: measured, development fire patches by NBAC cause: Natural 76 (2019 5, 2021 10, 2022 3, 2023 58), Human 7 (2019 2, 2020 2, 2021 3). Human-access signals can act through 7 fires at most; a band ranking restricted to the natural cohort shares 92 % of its fires with the unrestricted one.

*Blocked on:* cause is held (NBAC FIRECAUS, cached in nbac_fire_dates.json; NFDB too): 76 of the 83 development fire patches are natural-cause, so the cohort is 92 % of the sample and cannot discriminate. Close or keep: James (Q42)

**E-10 — Negative control**

*Hypothesis:* The noise arm is within noise of 0.5, and the real-band arm clearly beats it. WRONG IF the noise arm sits clearly above 0.5: then a POSITIONAL PRIOR -- where burn tends to sit in a tile, learnable from zero padding without reading a band -- inflates every arm in this register, and must be subtracted before any of them is quoted.

Sanity and calibration at once. Near 0.5: the pipeline is sound and arms can be read at face value. Above it: the excess is the floor every arm got for free, and it is the number to subtract.

*Note:* REDESIGNED. The old control was 'a deliberately redundant band pool' with the hypothesis 'at or near chance', and those cannot both hold: every real Sentinel-2 band carries surface signal, and the YAML's four overlapping red bands cannot be built from a sensor with one red band. Its runner was 'BANDS=...', not a command. Run this set first. RESULT, noise half (job 6844515): 0.5022 +- 0.0007, above 0.5 in 6/6 folds -- a positional prior of 0.002, about 1% of any real arm's skill. neg_real was not submitted (docs/results/band_search_nbac). 2026-11-10 (A-56, James): re-run on the v2 pack (composite ending the day before each fire; the slot sweeps' 5 folds). Any v1 result above stays as legacy.2026-11-11 (docs/results/P7/p7i_legacy_v2, v2 pack, 5 folds): SUPPORTED. noise arm 0.5005 (positional prior 0.0005, about 0.3 % of real skill); real bands +0.193.

**E-26 — Within-fire burn pattern**

*Hypothesis:* Imagery separates burned from unburned pixels INSIDE fire patches at least as well as it does across all patches, because inside a perimeter the outcome is fuel, terrain and firebreaks rather than whether a fire started. WRONG IF within-fire skill is clearly lower, which would say most unconditional skill comes from recognising WHICH patches burned -- between-patch discrimination, not fuel.

Conditioning on ignition removes the component a reflectance spectrum structurally cannot see. AUC ignores prevalence, so within-fire against overall reads as which task the imagery predicts better. Water and rock inside a perimeter are easy unburned pixels, so part of any within-fire skill is 'non-fuel is visible' -- fuel, but not moisture.

*Note:* REDESIGNED. As first written it asked 'burned > 100 ha, given it burned'. Patches are ~530 x 530 px, ~11,257 ha, and every one of the 99 fire patches exceeds 100 ha -- the smallest burned area is 3,017 ha -- so the cut separated nothing. Folds are now assigned BEFORE the scene filter: fold_indices deals the blocks present round-robin, so filtering first had reshuffled which ground landed in which fold. 2026-11-10 (A-56, James): re-run on the v2 pack (composite ending the day before each fire; the slot sweeps' 5 folds). Any v1 result above stays as legacy.2026-11-11 (docs/results/P7/p7i_legacy_v2, v2 pack, 5 folds): SUPPORTED. within-fire minus overall +0.040 [+0.028, +0.051], 5/5 folds.

**E-43 — Date-only control**

*Hypothesis:* Day of year and latitude alone separate fire from non-fire at about chance. WRONG IF they do not: the pseudo-date rule for negatives would then be a shortcut every arm can read.

Guards the fire-date design (A-24).

*Note:* P3 (docs/results/P3/p3_dated): SUPPORTED. Day of year 0.55 [0.50, 0.59], sin 0.45, cos 0.45, latitude 0.53. The confound is the year (0.87), not the pseudo-dates.

*Blocked on:* the learned date-only classifier waits for P5 (training is Narval only)

**E-54 — Legacy composite leakage**

*Hypothesis:* For fires that started before 30 June, the legacy April-June composite already shows the burn: on burned pixels its NIR-SWIR1 index (B8, B11) is lower than in the pre-fire composite ending D-1, relative to the same change on the patch's unburned pixels, and the drop grows with the days between the fire's start and 30 June. Fires starting in July or later show no drop. WRONG IF the early fires show no drop: then the v1 imagery did not read the outcome, whatever its weather did.

How much the v1 band searches (E-1 to E-14) could have read the burn itself, and so which of their results survive P4.

*Note:* P4 (docs/results/P4/p4_prefire): MIXED. As registered, early fires show the drop (-0.061 [-0.081, -0.041], 83 % negative, n=54), but late fires show it too (-0.082, n=29) and it does not grow with overlap (rho +0.05 [-0.20, +0.30]). A control added after registration -- the same pixels at the same place in the confuser year -- takes both to about 0 (early -0.005 [-0.033, +0.023], late +0.005): the drop is the seasonal change of what later burns, not the burn. At most a weak leak in the longest overlaps (41+ days: -0.029). The legacy imagery's fault is snow and season, not a visible burn.2026-11-11 (docs/results/P7/p7i_legacy_v2): the v1 band searches re-run on v2 score 0.674-0.704 pooled AUC against v1's 0.755-0.790 (not paired: 6 vs 5 folds, different label dating), and their rankings differ. The v1 band results are superseded.

### Index baselines

**E-11 — Greenness vs moisture indices**

*Hypothesis:* `both` beats `greenness` by a small but fold-consistent margin, because direct water absorption at 1610 nm carries information a greenness proxy cannot; and `moisture` (2 bands) draws with `greenness` (5 bands). WRONG IF `both` does not beat `greenness`, which would say the 1610 nm moisture signal adds nothing this label can see -- a publishable null, and one that would weaken the case for the SWIR chain considerably.

THE MISSION'S CENTRAL CLAIM. FWI2025 accepts grassland curing from remote sensing and its current option is NDVI-based GREENNESS -- a proxy for dryness. Greenness tracks moisture only while they co-vary seasonally, and a conifer stand stays green as it dries. If moisture beats greenness on a burn outcome, that is a concrete, quantified recommendation to the operational system. If `both` does not beat `greenness`, the 1610 nm moisture signal adds nothing this label can see -- also publishable.

*Note:* Primary contrast is `both` vs `greenness`: a strict superset, so a positive result is unambiguous. Tests ONE moisture index at 1610 nm -- NDWI_Gao needs 1240 nm and NMDI/NDTI/NBR need SWIR2, none of which Sentinel-2 carries. 2026-11-10 (A-56, James): re-run on the v2 pack (composite ending the day before each fire; the slot sweeps' 5 folds). Any v1 result above stays as legacy.2026-11-11 (docs/results/P7/p7i_legacy_v2, v2 pack, 5 folds): MIXED. both beats greenness by +0.016 [+0.001, +0.032] (4/5 folds), but moisture is -0.020 [-0.032, -0.007] below greenness rather than level.

*CFFDRS gap:* FWI2025 curing input

**E-12 — Index baseline vs learned bands**

*Hypothesis:* The learned model on raw bands beats every index family, because an index is a fixed projection that discards information a model could use. WRONG IF indices match it, which would be a strong argument for shipping indices -- cheap on an FPGA and interpretable to an operational user.

If the learned model beats every index family by a wide margin, the recommendation to CFFDRS is to take BANDS rather than indices — a finding about the system's interface, not only about our sensor. The heritage baseline rule 4 asks for.

*Note:* 2026-11-10 (A-56, James): re-run on the v2 pack (composite ending the day before each fire; the slot sweeps' 5 folds). Any v1 result above stays as legacy.2026-11-11 (docs/results/P7/p7i_legacy_v2, v2 pack, 5 folds): SUPPORTED. raw beats greenness (+0.034), moisture (+0.054) and both (+0.018, 5/5 folds, 2-SE interval reaching 0).

**E-59 — Indices as model inputs**

*Hypothesis:* For the P6 ecology estimators, giving the model every index its bands can form, alongside the raw bands, lowers error at matched band count, most at small k (k <= 4), under the sensor noise model; indices alone do worse than raw + indices. WRONG IF raw + indices beats raw at no k (spatial-block paired CI spanning 0 at every k, every target).

Whether the on-board model should compute indices before the network, which changes both the band value (a band is worth the indices it unlocks) and the compute budget (P12).

*Note:* Indices are inputs only, never labels (rule 3). ECVs are not inputs unless one is shown worthwhile. Runs inside E-22's sweep (A-38): every evaluated set in raw / indices / raw + indices, noisy and noise-free. Run on Nibi 2026-10-29 (docs/results/P6/p6a_ecology): MIXED. Raw + indices beats raw only at k = 5-8 (+0.006 to +0.007 combined skill, CIs above 0); nothing at k <= 4, the opposite of 'most at small k'. Indices alone are worse at every k they form. eco_v3, 2026-11-04 (docs/results/P6/p6a_ecology_v3): MIXED again, +0.0030 [+0.0006, +0.0057] at k = 8 only; maps per input mode show the same structure.

### Covariates

**E-13 — Weather representation**

*Hypothesis:* BOTH is within noise of CODES. The FWI codes already integrate the same 91 days through a recursion tuned over decades, so our 12 features are unlikely to extract much the codes have not. WRONG IF BOTH wins clearly -- then check DIMENSIONLESS, because a gain that disappears there came from absolute level, which at 45-70 N is latitude wearing a weather costume.

Does our compression of 91 days beat the FWI System's? CODES is CFFDRS as it stands and is the baseline. If BOTH beats CODES but DIMENSIONLESS does not, the gain came from absolute level, which at 45-70 N is latitude -- geography wearing a weather costume.

*Note:* No repack: the pack carries weather_arm=both, the union, so each arm is a column mask. 2026-11-10 (A-56, James): closed, not re-run on v2: the v2 pack has no 91-day history features; R1 against R2 and the weather-age experiment E-20 answer what weather representation adds. It never produced a valid result (not run on the NBAC pack).

*Blocked on:* closed 2026-11-10 (A-56): no v2 history features; R1/R2 and E-20 answer it

**E-14 — Fusion architecture**

*Hypothesis:* Both fusion variants beat rasters_only, and two_head is within noise of bottleneck. The CFFDRS-shaped separation is expected to cost little; if it costs a lot, the architecture argument has to give way to the measurement. WRONG IF rasters_only matches both, which would say the weather scalars add nothing at this label and sample size -- and would make E-13 moot.

What the CFFDRS-shaped separation of fuel and weather costs or buys against early fusion. rasters_only is the no-weather floor and is also the configuration the band ranking is read from, which ties the two together.

*Note:* two_head is submitted once, as wx_both, and report_arms.py aliases it into the fusion family; without that alias the main contrast was never produced. The second baseline, bottleneck, tests the hypothesis's other clause. 2026-11-10 (A-56, James): closed, not re-run on v2: the CFFDRS ladder fixes how scalars enter (R2's physics layer plus residual); R4 against R2 is the fusion question in its terms. It never produced a valid result (not run on the NBAC pack).

*Blocked on:* closed 2026-11-10 (A-56): the CFFDRS ladder (R4 against R2) answers it

**E-15 — Imagery vs the FBP formula**

*Hypothesis:* Imagery plus the FMC scalar beats the scalar alone, substantially. The FBP equation is a function of latitude, longitude, elevation and date only -- it carries no information about the stand -- so a null here would be surprising, and would cast doubt on the imagery rather than vindicate the formula.

G1 restated into something testable: does imagery carry foliar-moisture information the FBP equation does not? It CANNOT say our spectral estimate beats theirs -- that needs an LFMC label (E-29).

*Note:* The imagery-free floor that ran (6/6 folds, auc_px 0.5396 to 0.7660) was trained and scored on the dNBR pack, so it does NOT count: both halves must be rerun on the NBAC pack. The spread is still a fair picture of fold-to-fold variance. 2026-11-10 (A-56, James): closed, not re-run on v2: R4 against R2 measures imagery beyond the FBP inputs; the FMC slot (E-16) stays blocked on measured FMC. It never produced a valid result (its only run used the dNBR label, which does not count).

*Blocked on:* closed 2026-11-10 (A-56): R4 against R2 answers it; E-16 needs measured FMC

*CFFDRS gap:* G1 foliar moisture is computed, never observed

**E-16 — FMC arms**

*Hypothesis:* None. The arms are identical by construction, so no prediction is possible and any apparent difference would be seed noise.

NOTHING. fmc_measured is read in four places and written in none, so all three arms reduce to the FBP equation and would return three identical numbers looking like 'no difference'. Listed so it is not run by mistake.

*Note:* P5: the correct form of the FMC slot runs as r3_fmc (+/- 30 % through the physics); the replace form stays blocked on E-29. P7: r3_fmc (correct form) +0.002 [-0.001, +0.005] within, its twin +0.0015; the correction is a near-uniform +24 %.

*Blocked on:* fmc_measured is never written; needs E-29

### CFFDRS gaps

**E-17 — Station-density stratification**

*Hypothesis:* The imagery increment grows with distance to the nearest station. Fuel moisture is the integral of weather, so a satellite estimate should be worth most where the weather grid is interpolated from furthest away -- the north, which is also where most area burns.

CFS names thin station density as a limit on model accuracy (GLC-X-42 7.2). Fuel moisture is the integral of weather, so satellite fuel state should be worth most where the weather grid is weakest -- the north, which is also where most of the area burns.

*Note:* Measured 2026-10-23: fire patches sit a median 37 km from the nearest reporting CWFIS station (IQR 23-63, max 191); terciles at 30 and 54 km. Provincial agency stations are not in the CWFIS export, so true density is higher than this says. P3 (E-52): ERA5 vs station disagreement does not grow with distance (rho about 0), so the premise is AT RISK before the imagery increment is measured. 2026-11-10 (docs/results/P7/p7f_station_distance), on slots_v2 with the pack's station_km (all 193 development patches, 2019 included): REFUTED. R4 - R2 between-patch share against distance rho +0.04 [-0.10, +0.17]; by tercile (< 32 / 32-58 / > 58 km) -0.001, +0.004, +0.000. The PC + FMC + CBH slot arm rho -0.03 [-0.16, +0.09]. Within patches flat as well. The verdict rule moved from the within-patch to the between-patch difference after the first readout (weather cannot act within a patch); neither shows growth.

*CFFDRS gap:* G3 station density

**E-18 — Snow-off startup**

*Hypothesis:* Correcting the start date changes DC and DMC materially above 55 N and improves skill there, with little effect in the south. Our flat 90-day spinup starts around 1 April into frozen, snow-covered ground, so the spurious drying should scale with latitude. WRONG IF, above 55 N, the imagery start-up neither moves the median lag-1 DC by 10 % or more against the ERA5 rule nor raises the between-patch AUC of DC or FWI with a CI above 0.

Fixes our own defect first: the spinup starts ~1 April, which at 55-67 N is frozen and snow-covered, so the recursion accumulates weeks of spurious drying and the error scales with latitude. Then it tests whether an imagery snow-off date beats the regional rule.

*Note:* P3 (E-51): the operational start-up moves DC by +38 at >=60 N and lifts DC AUC 0.77 -> 0.91 there; ERA5 melts snow late, which is the error an S2 snow-off date could fix. AMENDED 2026-10-29, before any patch snow-off date existed: the imagery date comes from the E-60 classifier (median over 25 points per patch, Sentinel-2 to D-1), not a per-pixel NDSI threshold, and it is compared with the ERA5 C-2 rule as well as the flat spinup. The falsifier in the hypothesis was added at the same time, before any date existed. E-60 found the imagery date 16 d off the station on median, both ways. Run 2026-10-30 (docs/results/P6/p6d_startup): REFUTED. Above 55 N the SWIR-allowed date moves median DC +7.0 %, AUC DC +0.015 [-0.008, +0.040], FWI +0.002 [-0.009, +0.013]: the falsifier fires. VNIR only moves DC -20.2 % and loses skill (FWI -0.042 [-0.086, -0.007], DMC -0.126). The ERA5 rule stays; SAFARI is not asked for this date (A-41).

*CFFDRS gap:* G4 snow-off keyed by regional rule

**E-19 — Latitude-banded weather**

*Hypothesis:* History beats codes at high latitude specifically, and not in the south. The day-length factors are tabulated for ~46 N, so the codes should be least trustworthy where that assumption is furthest from the truth. WRONG IF the gain is uniform across bands, which would make the mechanism something other than day length.

DMC and DC day-length factors are tabulated for ~46 N while Canada spans 42-83. A pooled number cannot distinguish 'history is better' from 'history is better at high latitude', which is the actual claim -- so the test is the interaction, not either band alone.

*Note:* Bands hold 745 / 594 / 495 of the 1834 training tiles, so ~80-125 per band per validation fold -- above the 25-tile floor below which a band is skipped rather than scored. 2026-11-10 (A-56): re-scoped to one R2 configuration, r2_daylat (latitude-correct day length in DMC and BUI), paired with r2 by fold and seed.2026-11-11 (docs/results/P7/p7h_daylat, slots_e19 15/15 each): REFUTED. r2_daylat - r2 overall: within -0.001, between -0.003 [-0.012, +0.006]; interaction (60-90 N) - (0-55 N) between patches -0.003 [-0.013, +0.005]; the north band is slightly worse (-0.007).

*CFFDRS gap:* G5 day-length tabulated for ~46 N

**E-20 — Weather staleness**

*Hypothesis:* Skill decays with weather age, fastest for CODES and slowest for the dimensionless history. This is the testable half of a claim fwi.py already makes from input drift alone (DC 8.2% over three days against ISI's 89.9%). WRONG IF decay is flat, which would mean a daily uplink costs nothing and the slow-code argument is unnecessary.

Every FWI code is defined on a same-day noon observation and a daily uplink cannot supply one. The input drift is already measured (DC 8.2% over three days against ISI's 89.9%) and fwi.py reasons from it to a recommendation -- BUI best, FWI worst. Drift in a feature is not loss in a prediction, and this measures the half nobody has.

*Note:* Train once, score at each lag: one model, five scores. The leakage guard makes an earlier target date strictly safer. P3 (E-53, no learning): FFMC and ISI lose about 0.10 AUC from D-1 to D-7 with ERA5, DC and BUI about 0.03-0.04. P5: r2_lag7 trains R2 on 7-day-old codes; the train-once-score-at-each-lag design still needs a scoring mode in run_slots. P7: r2_lag7 within -0.024 [-0.039, -0.011], between -0.052 [-0.101, -0.010]: decay is not flat (PARTIAL; per-code ordering and score-at-lag not run). 2026-11-05 (A-50): r2_lag7 aged the codes only; wind and humidity stayed at D-1. The pack now carries all 13:00 weather at lags 1, 2, 3 and 7 (no new ERA5 pass: the sidecars held it), run_slots scores one model at each lag (--score-lags), and r2_age7 trains on weather that is all 7 days old. lags_v1 2026-11-05 (docs/results/P7/p7d_weather_age, 35/35 fits): between patches R2 loses -0.023 [-0.056, +0.012] at 2 days, -0.055 [-0.075, -0.034] at 3 and -0.051 [-0.091, -0.011] at 7; R0 HFI -0.044, -0.093, -0.061. Within patches flat (<= 0.007). r2_age7 is worse than r2 at every age (within -0.018 to -0.022, 5/5 folds). PARTIAL: decay is not flat; the per-code ordering half was not run. 2026-11-10, registered before the run: the per-input half (lags_v2) trains r2 once per fold and seed and scores it with ONE input 2, 3 and 7 days old (each of the six codes, and wind + direction + humidity as 'wx'), every other at D-1. Prediction, from fwi.py's input drift (DC 8.2 % over three days against ISI 89.9 %): at 3 and 7 days, ageing FFMC or ISI costs more between-patch AUC than ageing DC or BUI. WRONG IF DC or BUI ageing costs as much as FFMC or ISI (the paired CI on the difference reaches 0).2026-11-11 (docs/results/P7/p7g_weather_inputs, lags_v2 15/15): per-input half SUPPORTED. R2 between patches, mean(FFMC, ISI aged) - mean(DC, BUI aged): 3 days -0.020 [-0.027, -0.012], 7 days -0.012 [-0.021, -0.001]. FFMC alone 3 days old costs 0.035, about two-thirds of the 0.055 lost with all weather 3 days old; DC, DMC and BUI cost almost nothing at a week.

*CFFDRS gap:* G7 CFFDRS assumes same-day observations

**E-21 — Fuel-layer refresh**

*Hypothesis:* A positive slope: the advantage of a refreshed estimate grows with the staleness gap. At gap 0 our estimate should LOSE, because it is a noisy copy of its own training target -- which is why the slope and not the level is the estimator. WRONG IF the slope is flat or negative. (This clause restates the prediction's negation; it was written 2026-10-24, after P2's inventory-half result, and changes nothing it predicts.)

FBP consumes a fixed-vintage fuel grid while fuel type changes with harvest, insects, fire and regrowth. The slope is the estimator because at gap 0 our estimate is a noisy copy of its own training target and would lose on noise alone.

*Note:* P2 (docs/results/P2/p2_r0): inventory half done under R0. Within-patch HFI AUC moves -0.005 per decade of SCANFI age [-0.015, +0.007] (patch fixed effects, 79 fire patches, ages 1-13 y). No staleness cost to recover on this sample, so the prediction is at risk before E-22 runs. Pre-fire steps only: the 2020 step already shows the 2019-2020 fires (A-25). P3, dated design: -0.009 per decade [-0.017, +0.001]; a cost of age of at most about 0.02 AUC per decade. Re-scored 2026-11-10 with SCANFI 2005 (ages 1-18 y, 83 patches): legacy -0.006 [-0.013, +0.001], dated -0.006 [-0.013, +0.000]. The cost of age is at most about 0.013 AUC per decade.

*Blocked on:* the refreshed-estimate half needs E-35's eco_fire sidecars (ecology-model fuel on the fire patches), still on the cluster

*CFFDRS gap:* G2 fuel-type layer is a fixed vintage

**E-22 — Ecology arm**

*Hypothesis:* The ranking from dense SCANFI labels differs from the fire-outcome ranking, and SWIR ranks higher in it. Structure and biomass retrieval leans on SWIR more than a burn outcome does, because the outcome is diluted by ignition and weather. If the two rankings agree, that is a strong convergent result for whichever bands win. WRONG IF the first SWIR band (B11 or B12) enters the combined-skill nested set no earlier than B11 entered the fire-outcome search (median rung 3.5 over E-2's folds), taking the median over E-22's outer folds and seeds.

THE PRIMARY BAND RANKING. Dense per-pixel labels rather than one sparse outcome per patch, so it has orders of magnitude more signal per scene than the fire arm and measures what the bands actually retrieve rather than what correlates with ignition.

*Note:* P6a (A-38): packed as data/ecology_v2 (dev 226 patches / 904 tiles; frozen test 45 patches, splits/ecology_test_v1.json), 12 bands with B12, SCANFI v2 2020 labels. The WRONG IF clause was added 2026-10-28, after submission and before any E-22 result existed; E-2's rungs (never, 3, 2, 5, 2, 7) were already known. Run on Nibi 2026-10-29 (docs/results/P6/p6a_ecology): SUPPORTED. First SWIR band at step 1 in 13/15 runs (B12 60 %, B11 27 %), median 1. Caveats: SCANFI is Landsat-mapped, SWIR included (Q35); the family target's D class is 82 % open ground (P6a-M1). eco_v3 on the corrected labels, 2026-11-04 (docs/results/P6/p6a_ecology_v3): SUPPORTED again, first SWIR at step 1 in 11/15 (B12), median 1.

**E-50 — Latitude-correct day length (R0)**

*Hypothesis:* Scaling the DMC day-length factors from 46 N to each patch's latitude raises DMC more at >=60 N than at <55 N (longer summer days), and raises R0's between-patch AUC of DMC and BUI more in the north. WRONG IF the DMC shift is uniform across bands. The AUC half rests on 19 northern fire patches and is read only beside the shift.

Whether the fixed 46 N day length (gap G5) costs CFFDRS skill where Canada burns most.

*Note:* cffdrs lat.adjust is NOT the variant: in cffdrs 1.9.2 it only changes the factors at or south of 30 N, so it is a no-op for every patch here. FWI2025's sunrise-to-sunset hourly DMC changes far more than day length and may not feed FBP1992. DC's monthly factor is a seasonal adjustment, not a day length, and is left. P3 (docs/results/P3/p3_dated): SUPPORTED. DMC shift +1.4 / +3.8 / +6.4 by band; AUC moves by 0.006 or less: a calibration gap, not a skill gap, under R0.

*Blocked on:* needs the frozen test set (P10)

*CFFDRS gap:* G5 day-length tabulated for ~46 N

**E-51 — Operational start-up (R0)**

*Hypothesis:* The GLC-X-42 Appendix C-2 start-up (codes begin 3 days after ERA5-Land snow cover is gone, or after 3 days at or above 12 C at 13:00 where snow is absent) with an overwintered DC moves DC and DMC at D-1 more at >=60 N than at <55 N, compared with a flat 90-day spin-up from the default start values, and its effect on R0's between-patch AUC is larger in the north. WRONG IF the code shift does not grow with latitude. This is E-18's mechanism under the operational rule; E-18's imagery arm is P6.

How much the operational start-up matters before imagery tries to improve on it (G4).

*Note:* P3 (docs/results/P3/p3_dated): MIXED. DC shift -19.8 / +30.1 / +38.4 by band (grows north), DC AUC 0.77 -> 0.91 at >=60 N (19 fires); DMC shift -1.3 / -2.0 / -1.4 (flat).

*Blocked on:* needs the frozen test set (P10)

*CFFDRS gap:* G4 snow-off keyed by regional rule

**E-53 — Weather staleness under R0**

*Hypothesis:* R0's between-patch AUC decays with the age of the weather (D-1, D-2, D-3, D-7), fastest for FFMC and ISI and slowest for DC and BUI. WRONG IF the fast codes do not lose more than the slow ones by D-7. This is E-20's mechanism without learning: the curve E-20's learned arms are compared with.

How stale CFFDRS's own inputs can get -- the bar for a weather-dependent onboard product (A-29 rule 2).

*Note:* P3 (docs/results/P3/p3_dated): SUPPORTED with ERA5: D-1 -> D-7, FFMC -0.10, ISI -0.11, DC -0.03, BUI -0.04. Station series: BUI -0.11 and DMC -0.12, as fast as FFMC.

*Blocked on:* needs the frozen test set (P10)

*CFFDRS gap:* G7 CFFDRS assumes same-day observations

**E-60 — Snow-off without SWIR**

*Hypothesis:* Judged against the snow-off date measured at ECCC climate stations (observed snow on ground), a per-station snow-off date from visible and NIR Sentinel-2 bands alone has a median absolute error of at most 7 days and is no more than 3 days worse than the best set that may use SWIR1 (the NDSI family). WRONG IF the VNIR-only error exceeds 7 days or is more than 3 days worse: snow-off then needs the SWIR chain, which counts toward its cost in P12.

Whether a VNIR-only camera can supply the start-up date.

*Note:* AMENDED 2026-10-27, before any snow-off data or code existed (Q32, James): the reference was the NDSI-based date, an index threshold used as truth, which rule 3 forbids. It is now the station-measured snow on ground; NDSI is a candidate like any other. Q33 (James, same day, still before any snow-off data): the CWFIS fwi_obs snow on ground proved to be mostly a gridded analysis, so the station truth is ECCC climate-station observed snow on ground. P6c (A-39): packed as data/snow_v1 (dev 915 station-years, 21,291 observations; frozen test 122 station-years). Run on Nibi 2026-10-29 (docs/results/P6/p6c_snow): REFUTED. VNIR-only best 19.5 d (with noise); +3.8 d [+2.0, +5.6] worse than SWIR allowed (15.7 d), 5/5 folds. The 7 d clause sat below the sampling floor (a perfect classifier: 7.5 d), unattainable for any camera; SWIR1 is worth about 4 days here.

**E-64 — LFMC: simulation-trained, Sentinel-2 empirical, FBP equation**

*Hypothesis:* (a) Both spectral LFMC estimates -- the simulation-trained retrieval (PROSPECT-D + 4SAIL with the noise model, never fit to Globe-LFMC) and the best empirical Sentinel-2 model fit on Globe-LFMC with site-grouped cross-validation (calibrated NDMI, MSI or NMDI, or a GPR on the bands) -- beat FBP's foliar moisture equation on conifer records. (b) The empirical model beats the simulation-trained one, by less than 10 LFMC points of RMSE. WRONG IF (a) either estimate's RMSE minus the equation's has a site-bootstrap CI reaching 0; or (b) the simulation-trained retrieval wins, or loses by more than 10 points.

Whether an observed foliar moisture beats the computed one (G1's strong claim), and whether a retrieval trained on physics transfers to real data with no local calibration -- the condition SAFARI faces in Canada, which has no LFMC sites. The winner becomes the measured-FMC sidecar that unblocks E-16.

*Note:* FBP's equation describes conifer foliage, so (a) is scored on conifers; aspen is reported, not tested. A 15 % of sites, seeded, is frozen for P10. Placeholders (A-47): +/- 5-day pairing, 4SAIL turbid medium for every fuel, soil-only backgrounds, an atmospheric-correction residual as extra noise. Run 2026-11-04 (docs/results/P6/p6f_lfmc): REFUTED. Conifer RMSE minus the equation (14.0): simulation GP +26.0 [+22.4, +29.3], best empirical +0.6 [-0.1, +1.2]; simulation minus empirical +25.5. Conifer LFMC SD is 15.2.

*CFFDRS gap:* G1 foliar moisture is computed, never observed

**E-65 — LFMC: simulation retrieval with fold-wise narrowed priors (P6f-v2)**

*Hypothesis:* Registered 2026-11-05, before any v2 result (A-51). With the prior cut, inside each outer site fold, to the LFMC range of that fold's training records by species and season, the simulation GP on the ten bands, on conifer records: (a) has a bias within +-10 LFMC points; (b) beats prior_mean_fold, the training stratum mean; (c) beats FBP's equation; (d) loses skill without B12 on jack and red pine (E-29). WRONG IF (a) |bias| >= 10; (b), (c) the site-bootstrap CI of its RMSE minus the comparator's reaches 0; (d) the CI of no_b12 minus all10 reaches 0.

Whether the +31 bias was the prior, and whether the spectra then carry LFMC beyond the prior's mean. If (b) fails, the simulation route on Sentinel-2 bands has no spectral skill on conifers even with a right-sized prior, and steps 3-4 (backgrounds, a discontinuous canopy) are the remaining physics to try.

*Note:* Step 1 of the fix (docs/results/P6/p6f_reference): PROSPECT-D + 4SAIL match Feret's R packages to 5e-15 with the same leaf-angle classes, so the code is not the cause of E-64's bias. The leaf-angle binning (13 against 18 classes) is at most 0.1 sigma of the atmospheric residual. Only the LFMC range of the training fold enters the prior; the frozen LFMC test sites stay unread. lfmc_v2 2026-11-06 (docs/results/P6/p6f_lfmc_v2): MIXED. Conifers: narrowed GP RMSE 13.2, bias +4.2 (1 holds); minus the stratum mean +1.09 [+0.59, +1.60] (2 fails: no spectral skill beyond the prior); minus FBP -0.80 [-1.66, -0.01] (3 holds), but the stratum mean beats FBP by -1.89; no B12 +0.07 (4 fails).

*Blocked on:* the FW commit must be pushed and pulled

*CFFDRS gap:* G1 foliar moisture is computed, never observed

### Hyperspectral

**E-23 — SWIR band placement**

*Hypothesis:* The best four cluster near 1240, 1610 and 1680-1730 nm, with the fourth in the 1500s. From brief hypotheses H1 and H3: resolving a dry-matter change needs two water-sensitive bands with different water-to-dry-matter absorption ratios.

THE SWIR SPECIFICATION. Sentinel-2 has one band in that window and the mode carries four: four cannot be chosen from one. Only a contiguous source can answer it.

*Note:* Grid measured from AVIRIS-NG's own bad-band list (A-22), which puts the water-vapour gap at 1364-1408 nm -- narrower than assumed, so 1300-1359 and 1414-1500 were being excluded for no reason.2026-11-11, read from runs already held (aviris_v4 holds all 42 lines; the blocker was stale): MIXED. The best measured standard-InGaAs 4-band set is the predicted placement: the configured slots 1240, 1550, 1610, 1680 nm score 0.2853, ahead of every searched and consensus standard set (best consensus k=4 0.2796; hs_consensus, P12/p12_bands), and DFA's nearest filters L4 L6 L9 L11 are within 0.002 (P12/p12_sensors). But the broad searches do not find it: they converge on 1500-1630 nm (k=4 consensus 1500, 1530, 1580, 1630; 8-9 of 15 searches, not stable) and never pick a band near 1240 or above 1680 (the standard placeholder stops at 1700 nm, A-40). Search noise, not the spectrum, separates the two.

**E-24 — 1209 vs 1240 nm**

*Hypothesis:* 1240 nm is slightly better for water sensitivity and 1209 slightly better for O2 margin, with the difference small enough that the flown WorldView-3 centre is defensible. A large difference either way is the interesting outcome. WRONG IF (made testable 2026-11-11, before the run) the paired combined-skill difference has its 95 % CI wholly outside +-0.005.

Water sensitivity traded against O2 margin. The validator flagged the conflict; nobody has measured it.

*Note:* 2026-11-11, registered before the run: a clean pair on aviris_v4 at 64x2 (the band-search size), e24_slots_1210 against sensor_mantis_ms_plus_swir; they differ only in 1210/20 against 1240/20. Prediction: the paired combined-skill difference lies within +-0.005. WRONG IF its 95 % CI lies wholly outside +-0.005. Evidence so far (P12/p12_sensors): DFA L4 (1213/83) with L6 L9 L11 is within 0.002 of the configured slots, but every band differs there.

**E-25 — Spectral resolution: HS vs MS**

*Hypothesis:* Diminishing returns beyond roughly 10-15 well-placed bands, so the HS mode's 96 channels buy little over a well-chosen MS set. WRONG IF the curve keeps climbing, which would make the HS mode the better instrument and change the payload decision.

What spectral RESOLUTION buys, which decides the Mantis HS mode. Cannot be faked: ten Sentinel-2 bands cannot be interpolated into ninety-six, and rule 2 forbids trying.

*Note:* 2026-11-11: the VNIR half is answered by E-66 (all 81 Mantis HS channels +0.004 [-0.005, +0.014] over the 6-band custom block). The SWIR half is registered before the run: e25_vnir6_swir_all (custom block + every rule-7-clean 5 nm channel from 1005 to 1695 nm, 99 SWIR channels) against sensor_mantis_ms_plus_swir (4 SWIR bands), at 64x2 on aviris_v4. Prediction: within one paired SE. WRONG IF the 99 channels beat the 4 bands with a CI excluding 0.

**E-61 — Best SWIR bands, searched broadly**

*Hypothesis:* For the ecology targets, the best 4-band SWIR set within standard InGaAs (1000-1750 nm) recovers at least 90 % of the error reduction of the best 4-band set allowed to reach 2000-2400 nm (extended InGaAs), with the VNIR set fixed. WRONG IF allowing 2000-2400 nm improves any target by more than 10 % of its standard-window gain, with a CI excluding 0: then structure retrieval pays for the extended detector. Reported alongside, not predicted: how much of each optimum a vendor filter set (e.g. the best 4 of DFA's 12) recovers.

Which SWIR placements, and which detector, the structure targets need; feeds E-46 and the SWIR chain choice.

*Note:* Broadens E-23 (which stays as registered) beyond 1750 nm and adds vendor reference points. DFA L5 (1348/64) has ~28 % of its response inside the 1364-1408 nm water-vapour gap (A-22). A-40 / Q34: the grid applies rule 7, which also removes 1262-1288, 1330-1359, 1414-1490 and 1970-1980 nm, and the standard InGaAs placeholder stops at 1700 nm. Provisional sweep 2026-10-29: VOID (docs/results/P6/p6a_hs_provisional). Partial sweep on the corrected pack, 2026-11-01: no verdict, 51 of 75 tasks and extended InGaAs on two folds only (docs/results/P6/p6a_hs_v2_provisional). Full sweep hs_v3, 2026-11-02 (docs/results/P6/p6a_hs_v3): the falsifier does not fire (extra from extended: conifer -0.24, closure +0.06, height +0.04, all CIs reach 0), but the searches are unstable and a hand-set 1610 + 2190 nm pair beats them on height. Full sweep hs_v4 on the final labels, 2026-11-03 (docs/results/P6/p6a_hs_v4): REFUTED on height only, +0.09 m [+0.01, +0.23] against a standard gain of -0.01 m, so the 10 % threshold is degenerate. Lidar height (docs/results/P6/p6a_external_labels_v2) does not reproduce it: extended minus standard +0.05 m worse [-0.00, +0.11].

*Blocked on:* the held-out AVIRIS test lines wait for P10

**E-62 — Best VNIR bands, searched broadly**

*Hypothesis:* The best 6-band VNIR set from a broad grid includes at least one band in 700-760 nm (red edge), and the best 6-band set with no band there is at least 5 % worse on percent conifer and canopy closure. WRONG IF the best set has no red-edge band, or the best no-red-edge set is within 5 % on both targets.

Whether a VNIR camera without red edge (as some standard filter sets are) gives up structure skill, and which placements win.

*Note:* The VNIR arm searches the camera alone (no SWIR band), the question E-62 asks; Sentinel-2's bands and DFA's standard 6 enter as references (A-40). Sentinel-2 half, run on Nibi 2026-10-29 (docs/results/P6/p6a_ecology): AT RISK. Red edge (B5/B6) is in 13/15 best 6-band sets, but without B5-B7 the k = 6 error is within 5 % on percent conifer (+0.9 %) and closure (-0.2 %), because SWIR substitutes. The VNIR-only camera question waits for the AVIRIS-NG search; the provisional sweep of 2026-10-29 is VOID (docs/results/P6/p6a_hs_provisional). Partial sweep on the corrected pack, 2026-11-01: not tested, the two VNIR arms share no fold (docs/results/P6/p6a_hs_v2_provisional). Full sweep hs_v3, 2026-11-02 (docs/results/P6/p6a_hs_v3): the falsifier fires. No red edge is within 5 % on percent conifer (-1.2 %) and closure (+2.2 %), though 12/15 best sets keep a 700-760 nm band. Full sweep hs_v4, 2026-11-03 (docs/results/P6/p6a_hs_v4): REFUTED again. Red edge is in 15/15 best sets, but without it conifer is -1.1 % [-2.1, -0.3] and closure +2.1 % [+0.9, +3.3]. Sentinel-2 half on eco_v3, 2026-11-04 (docs/results/P6/p6a_ecology_v3): REFUTED. Red edge in 15/15 best 6-band sets; without it at k = 6 conifer +0.7 % [-2.0, +2.9], closure -0.9 % [-2.0, +0.5].

*Blocked on:* the held-out AVIRIS test lines wait for P10

### Hardware

**E-27 — Cost per input channel**

*Hypothesis:* BRAM scales roughly linearly with input channel count, so 96 channels are infeasible on the target part and 11 are affordable. Stream BRAM is ceil(width/18) x ceil(depth/1024) and width never stops paying. WRONG IF scaling is sub-linear because the first convolution dominates, which would make a wide input cheaper than the marginal-cost argument assumes.

The MARGINAL COST denominator. The brief asks for value per marginal cost, and without this the ranking has a numerator only. Stream BRAM is ceil(width/18) x ceil(depth/1024), so width never stops paying.

*Note:* 2026-11-11 (docs/results/P12/p12_hw_mantis): measured on the onboard ecology network (TinyEcologyUNet 32x1), not the legacy fire network, through FINN and the DPU. From 3 to 96 inputs: FINN BRAM +16 %, LUT +14 %, DPU work +42 %, throughput unchanged; hls4ml 11 to 16 inputs +1 % BRAM. REFUTED: strongly sub-linear, the body dominates.

**E-28 — Co-registration tolerance**

*Hypothesis:* Negligible cost below a quarter pixel, material by one pixel. WRONG IF a half-pixel shift already costs materially, which would tighten the dichroic and focal-plane alignment budget; or if two pixels cost little, which would retire the registration risk.

A number for the requirements table. The dichroic makes misregistration small, not absent. This is the deployment question -- a model built on co-registered imagery meeting a misregistered instrument.

*Note:* REDESIGNED. Shifting during training too would understate the cost, because a convolution can learn to compensate a fixed offset. Rigid translation only -- not rotation, scale or pushbroom keystone -- so the tolerance is NECESSARY, not sufficient. The original hypothesis also placed the loss at snow/forest boundaries; this reports the scene-average cost and cannot localise it, so that clause was dropped rather than left untestable. 2026-11-10 (A-56, James): re-run on the v2 pack (composite ending the day before each fire; the slot sweeps' 5 folds). Any v1 result above stays as legacy.2026-11-11 (docs/results/P7/p7i_legacy_v2, v2 pack, 5 folds): REFUTED. rigid SWIR shift costs 0.0001 at 1/4 px, 0.0007 at 1 px and 0.0024 at 2 px: two pixels cost little, so the rigid-shift risk is retired.

**E-48 — Hardware decision**

*Hypothesis:* The chosen model fits a Q8 at <= 80 % of every resource. WRONG IF only the Q9 fits, or none does.

The onboard hardware.

*Note:* Conversion pre-check 2026-11-05 (docs/results/P12/p12_convert), untrained P6 four-head TinyEcologyUNet, 22 inputs (8 bands raw + indices), all 12 E-47 rungs. hls4ml: all convert and C-simulate (max |err| 0.0014), but only 4x1 at tile 16-32 comes near the Q8 (84-91 % BRAM; 8x2 258 %). DPU (Q8): every rung is one DPU subgraph, only fix2float on the CPU, at most 0.28 s per scene at peak. FINN (estimate only, BRAM a floor with FIFOs unsized): all 24 builds convert; 23 fit the Q8 and 20 the Q7 at <= 80 %, and base_ch 4-16 meet 43 s at minimal folding (8x2 W4A4: 24 % of the Q7, 8.6 s). Next: FIFO sizing (Vivado on Linux) before the Q7 is an option. The index front end divides and is in none of these graphs.2026-11-11 (docs/results/P12/p12_hw_mantis, Mantis track, A-55): 16x1, 32x1 and 32x2 at the real inputs (11; 16 with B11). Q8 DPU: one subgraph each, 0.03-0.19 s per scene. Q7 FINN W4A4 (estimate only): 34.6 s per scene with width 32 folded for about 6 tiles/s, largest share 18-46 %. hls4ml: 217-1424 % of the Q8's BRAM. SUPPORTED on the Mantis track.

*Blocked on:* the general track waits for E-68's ladders; the Q7 fit is provisional until a Vivado (Linux) build sizes FINN's FIFOs; power is from datasheets

**E-66 — What each Dragonfly Mantis mode would offer**

*Hypothesis:* Registered 2026-11-06 on James's approval, before any result (PLAN_NEXT section 6; Chameleon and Caiman left out). On AVIRIS-NG with hs_v4's folds: (1) the custom Mantis MS block (490, 560, 665, 705, 740, 865) beats DFA's standard block as published; (2) MS custom alone beats Mantis SWIR alone (best 4 of DFA's filters); (3) all HS channels 470-900 nm are within one paired SE of MS custom; (4) MS custom + the best 4 DFA SWIR filters beats MS custom alone; (5) RGB scores below every MS set. WRONG IF, for (1), (2) and (4), the paired CI reaches 0; for (3), HS leads by more than one SE; for (5), RGB ties an MS set.

P12's sensor option table: what each Mantis mode would deliver, with GSD, swath, power, size and TRL from DFA's datasheet beside it (A-41: cost never ranks).

*Note:* Vendor data and Mantis datasheet in config/vendors/dragonfly.yaml (A-52). Grid config/grids/p12_sensors.yaml; the standard block's rule-7 exception is recorded in it (Q39). SWIR candidates: DFA's 10 usable filters (L5 fails rule 7; L12 runs past 1700 nm, A-19). Spectral comparison only: GSD, swath, SNR beyond the placeholder model and misregistration are reported beside the scores, not modelled. sensors_v1 2026-11-06 (docs/results/P12/p12_sensors), 75/75: MIXED. (2), (3), (5) hold; (1) +0.013 and (4) +0.008 have CIs reaching 0. SWIR at the fixed configured slots adds +0.016 [+0.004, +0.029]; searched per fold it does not. Next: DFA filters as fixed sets (config/grids/p12_sensors_fixed.yaml). sensors_fixed 2026-11-09 (15/15; anchors reproduce exactly): four fixed DFA filters (L4 L6 L9 L11) add +0.025 [+0.006, +0.045] to the standard block and +0.015 [+0.005, +0.024] to the custom; with SWIR the blocks tie (+0.002); DFA's filters match the configured slots (-0.002). Standard + 4 filters 0.282, S2 0.286.

**E-67 — VNIR against SWIR: the Mantis cameras' models at every size**

*Hypothesis:* Registered 2026-11-10 on James's request, before any result. On AVIRIS-NG with hs_v4's folds and seeds, per-pixel models from 16x2 to 256x3, raw + indices with noise: (1) the VNIR standard block beats SWIR alone (DFA L4 L6 L9 L11) at every size; (2) VNIR + SWIR beats VNIR alone at the largest size (256x3), so SWIR's gain is not a small-model effect; (3) for each camera the best size is within 0.005 of 64x2. On Sentinel-2 (U-Net ladder, E-47's design): (4) adding B11 to the Mantis VNIR stand-in raises the best rung's skill. WRONG IF, for (1), SWIR alone ties or beats VNIR at any size; for (2) and (4), the paired CI reaches 0; for (3), a size beats 64x2 by more than 0.005.

Whether the VNIR-against-SWIR ranking and the SWIR gain hold at every model size, for P12's camera options (A-49).

*Note:* The SWIR camera's filters (1213-1674 nm) have one Sentinel-2 counterpart (B11), so the SWIR-only model is compared on AVIRIS-NG only; Sentinel-2 adds B11 to the VNIR stand-in for the U-Net. 64x2 is the size every band search used, so its rows must reproduce sensors_fixed exactly (anchor check). hs_arch + arch_mantis_both 2026-11-10 (docs/results/P12/p12_vnir_swir), 15/15 each, anchor exact: MIXED. (1) VNIR beats SWIR at every size, lowest CI bound +0.001: SUPPORTED. (2) VNIR+SWIR - VNIR at 256x3 +0.032 [-0.002, +0.066]: REFUTED narrowly (+0.025 to +0.033 at every size). (3) VNIR +0.002, SWIR +0.004, both +0.007 from 64x2: REFUTED by the combined camera. (4) +B11 on Sentinel-2, best rung vs best rung +0.013 [+0.010, +0.016]: SUPPORTED (+0.004 at 8x2).

**E-68 — SWIR2's potential on the general track: the consensus sets with and without B12**

*Hypothesis:* Registered 2026-11-10 and revised 2026-11-11, before any run, on James's E-46 answer (A-55): SWIR2 is unlikely to fly, so it is priced on the general (Sentinel-2) track only and kept out of every Mantis run. On the Sentinel-2 U-Net ladder, E-47's design: B12 raises the best rung's skill in both pairs, k=5 (B4 B5 B8A B11 B12) against k=5 without B12, and k=8 (B3 B4 B5 B6 B8 B8A B11 B12) against k=8 without B12. WRONG IF, in either pair, the paired CI of the best-rung difference reaches 0.

How much a SWIR2 band adds to the general band requirement, for P12's options table (A-49). It prices SWIR2; it does not put it on the Mantis track, which carries no SWIR2.

*Note:* 2026-11-11 revision (James): the first registration also added a 2190 nm band to the Mantis VNIR + SWIR sets (AVIRIS-NG) and B12 to the Mantis stand-in. Both were withdrawn before any run, because SWIR2 will most likely not be on the CubeSat; the grid references were removed.2026-11-11 (docs/results/P12/p12_swir2): REFUTED. Best rung without B12 minus with: k=5 -0.0025 [-0.0041, -0.0009] (B12 helps), k=8 +0.0001 [-0.0015, +0.0018] (nothing). At 8x2 B12 is worth about 0.006 in both sets; at base_ch 4 the five-band set is better without it.

### Out of reach

**E-29 — T1 live foliar moisture**

*Hypothesis:* From Jolly et al. (2014), the brief's lead hypothesis H1: dry matter, not water content, drives seasonal conifer LFMC, so water-only bands will return EWT rather than LFMC and a two-band water contrast is required. Restated testably on 2026-11-03, before any simulation or score: with Sentinel-2's bands, the simulation-trained retrieval (E-64) has lower LFMC error on Globe-LFMC jack and red pine with B11 (1610 nm) and B12 (2190 nm) than with B11 alone. WRONG IF removing B12 does not raise that RMSE with a site-bootstrap CI excluding 0. Reported alongside, not predicted: the same contrast in spring (April-June, the dip) and in summer.

Would make G1's STRONG claim testable -- that a spectral estimate beats the FBP equation -- and unblock E-16. Globe-LFMC 2.0 is fetched and measured: 2,884 usable records at 83 sites, no Canadian ones, and C-2 black spruce has 51. It carries no spectra, so each record must be paired with a Sentinel-2 acquisition. Also the first moisture evidence for SWIR2 as A-41's tie-breaker.

*Note:* James (2026-11-03): start the simulation-trained retrieval of brief Phases 1-4 and compare it with LFMC from Sentinel-2's bands, while CWFIS is asked about field LFMC. Globe-LFMC holds LFMC only, not Cw or Cm, so H1 is read through LFMC error. Run 2026-11-04 (docs/results/P6/p6f_lfmc): SUPPORTED, weakly. Without B12 the simulation GP is +1.7 [+0.4, +3.2] worse on jack and red pine, in spring and summer, but that retrieval is biased +31 and worse than a constant.

*CFFDRS gap:* G1 strong form

**E-30 — T2 curing / NPV fraction**

*Hypothesis:* Brief hypothesis H2: SWIR2 is necessary for curing and 1240 nm is not a substitute, because the cellulose/lignin feature near 2100 nm is what separates NPV from soil. Untestable here: no curing label, no grassland, and the band is past the detector.

The other half of the FWI2025 curing input. Blocked three ways: no curing label anywhere in our data, no grassland in the ecology set, and NDLI needs 1754 nm, past the standard-InGaAs cutoff.

*Blocked on:* no label, no grassland, and the band is past the detector

**E-31 — Fire occurrence prediction**

*Hypothesis:* None offered. Out of scope by decision, and a hypothesis recorded for work that will not run invites being mistaken for a finding.

Parked by decision. Recorded because the argument is strong: FOP runs on 20 km cells, and a 20 m imager supplies the within-cell distribution a coarse model structurally cannot have -- 10^6 pixels per cell. The product that implies is a distribution summary, not a mean.

*Blocked on:* out of scope by decision; needs lightning strike data

*CFFDRS gap:* G6 FOP cannot see within its cells

## Runnable today

| ID | Experiment | Command | Narval resources per task |
|---|---|---|---|
| **E-9** | Lightning cohort | `post-hoc readout on the v2 band sweeps (sweep_bands_*_v2), natural-cause fires only (Q42 option 2), when they return` | -- |
| **E-21** | Fuel-layer refresh | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` | -- |
| **E-24** | 1209 vs 1240 nm | `Fire_Risk_FW SCRATCH_DATA=$HOME/scratch/aviris_v4 EXP_NAME=hs_e24_e25 SIZES=64x2 SETS='sensor_mantis_ms_plus_swir e24_slots_1210 e25_vnir6_swir_all sensor_mantis_vnir6' SUBMIT=1 bash scripts/shell/sweep_hs_arch.sh` | sweep_hs_arch.sh: 15 tasks (5 folds x 3 seeds) of 8 fits (4 sets x noise on/off, 64x2 only), 3 per 1:30:00 job on one A100 (hs_arch's 42 fits took 20 min) |
| **E-25** | Spectral resolution: HS vs MS | `Fire_Risk_FW SCRATCH_DATA=$HOME/scratch/aviris_v4 EXP_NAME=hs_e24_e25 SIZES=64x2 SETS='sensor_mantis_ms_plus_swir e24_slots_1210 e25_vnir6_swir_all sensor_mantis_vnir6' SUBMIT=1 bash scripts/shell/sweep_hs_arch.sh` | sweep_hs_arch.sh: 15 tasks (5 folds x 3 seeds) of 8 fits (4 sets x noise on/off, 64x2 only), 3 per 1:30:00 job on one A100 (hs_arch's 42 fits took 20 min) |
| **E-32** | CFFDRS as is (R0) | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` | -- |
| **E-35** | Fuel-type slot | `Fire_Risk_FW RUN_ID=20261102-1959 SUBMIT=1 bash scripts/shell/sweep_eco_fire.sh (FW 15a705b; done 2026-11-10); then SUBMIT=1 EXP_NAME=slots_e35 RUN_ID=20261110-1901 SKIP_DONE=1 ECO_DATA=$HOME/scratch/eco_fire_v1 CONFIGS=r2,r3_fuel_replace,r3_fuel_replace_shuffled,r3_fuel_pc_replace,r3_fuel_pc_replace_shuffled,r3_pc_replace,r3_pc_replace_shuffled bash scripts/shell/sweep_slots.sh` | sweep_eco_fire: --time=1:00:00 --gpus=a100:1 --cpus-per-task=8 --mem=48G per job (a first guess: one eco_v3 fit, about 2 min on an A100, plus forward passes); then the slot sweep as E-36 |
| **E-36** | Percent-conifer slot | `Fire_Risk_FW/scripts/shell/sweep_slots.sh CONFIGS=r3_pc,r3_pc_shuffled` | --time=2:30:00 --gpus=a100:1 --cpus-per-task=12 --mem=32G per task of 18 fits (slots_v3 measured: tasks 10 min median, 17 max; GPU 25 %, 1.5 GB peak; A-35) |
| **E-37** | Crown-base-height slot | `Fire_Risk_FW SUBMIT=1 EXP_NAME=slots_e35 RUN_ID=20261110-1901 SKIP_DONE=1 ECO_DATA=$HOME/scratch/eco_fire_v1 CONFIGS=...,r3_cbh_replace,r3_cbh_replace_shuffled bash scripts/shell/sweep_slots.sh (correct form: CONFIGS=r3_cbh,r3_cbh_shuffled)` | --time=2:30:00 --gpus=a100:1 --cpus-per-task=12 --mem=32G per task of 18 fits (slots_v3 measured: tasks 10 min median, 17 max; GPU 25 %, 1.5 GB peak; A-35) |
| **E-38** | Curing slot | `Fire_Risk_FW/scripts/shell/sweep_slots.sh CONFIGS=r2_cwfis,r3_curing_cwfis,r3_curing_cwfis_shuffled` | --time=2:30:00 --gpus=a100:1 --cpus-per-task=12 --mem=32G per task of 18 fits (slots_v3 measured: tasks 10 min median, 17 max; GPU 25 %, 1.5 GB peak; A-35) |
| **E-41** | Spread R0 (CFSDS) | `Fire_Risk_Model/scripts/python/eval_spread_r0.py` | -- |
| **E-43** | Date-only control | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` | -- |
| **E-44** | Ignition R0 | `Fire_Risk_Model build_ignition_dataset.py --stage weather / scanfi / filter, then eval_ignition_r0.py (CPU, no fitting)` | -- |
| **E-45** | Ignition slot value | `Fire_Risk_FW SUBMIT=1 bash scripts/shell/sweep_ignition.sh (run_ignition.py; 8 configs x 5 folds x 3 seeds, R0 at seed 0: 100 fits)` | --time=3:00:00 --gpus=a100:1 --cpus-per-task=8 --mem=32G per task of 6 fits, 17 tasks (a first guess: tiles read at 242/s locally, about 12 min of reading per fit) |
| **E-46** | Band and index decision | `Statistics scripts/make_band_options.py (consensus, grid, provisional table); then on Nibi docs/results/P12/p12_bands/rescore_commands.md (8 sweep_eco_arch runs and one sweep_hs references run), then make_band_options.py --eco-rescore --hs-rescore` | -- |
| **E-47** | Architecture decision | `Fire_Risk_FW BANDS=<E-46 set> SUBMIT=1 bash scripts/shell/sweep_eco_arch.sh (run_eco_arch.py)` | --time=1:30:00 --gpus=a100:1 --cpus-per-task=12 --mem=32G; 15 tasks (5 folds x 3 seeds), 3 per job, 12 rungs each (a first guess from eco_v3's 14 s per 8x2 fit) |
| **E-48** | Hardware decision | `Fire_Risk_FW scripts/check_eco_convert.py, export_eco_qonnx.py + the FINN build via scripts/finn.sh, scripts/vitis_ai.sh inspect; then Statistics scripts/make_hw_mantis_package.py` | -- |
| **E-49** | Dating the weather (R0) | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` | -- |
| **E-50** | Latitude-correct day length (R0) | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` | -- |
| **E-51** | Operational start-up (R0) | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` | -- |
| **E-52** | Weather source: station vs ERA5 (R0) | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` | -- |
| **E-53** | Weather staleness under R0 | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` | -- |
| **E-56** | Operational FBP outputs on a 2024-2025 cohort | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py --cohort` | -- |
| **E-61** | Best SWIR bands, searched broadly | `Fire_Risk_FW/scripts/shell/sweep_hs.sh ARMS='swir_std swir_ext references'` | --time=6:00:00 --gpus=a100:1 --cpus-per-task=8 --mem=32G per job of 6 tasks, 3 at once (A-43); hs_v3 measured 81 min median per standard InGaAs task, 153 per extended InGaAs task |
| **E-62** | Best VNIR bands, searched broadly | `Fire_Risk_FW/scripts/shell/sweep_hs.sh ARMS='vnir vnir_no_red_edge references'` | as E-61; hs_v3 measured 130 min median per VNIR task, 123 per no-red-edge task |
| **E-63** | Out-of-time generalisation, two training regimes | `Fire_Risk_FW/scripts/shell/sweep_slots.sh REGIME=A|B` | --time=2:30:00 --gpus=a100:1 --cpus-per-task=12 --mem=32G per task of 18 fits, as E-58 (slots_v3 measured 10 min median, 17 max); a first guess here, since regime A adds 1,080 training tiles and regime B a scoring pass |

All of these read the **`stage2_fire_11band_nbac`** pack. It replaces the one already in `~/scratch`, which the sweep now refuses.

### How the resources were derived

From the only completed runs (the imagery-free G1 floor, six folds): every 35-epoch fit took **122 s**, identical across folds, with the GPU at **0.2-0.6% utilisation** and 0.6 GB of GPU memory; venv build and staging took under 45 s; sacct MaxRSS 1.04 GB. Identical times on a 337-parameter model is an input-bound signature -- the cost is h5py decompressing tiles in the DataLoader, not the GPU.

- **`--time`** is 2 x (fits x 2.5 min) + 2 min, rounded up to 30 min. 2.5 min is the measured 122 s plus a margin, because no CNN fit has completed yet. The old request was 11:00:00 for every job, including two-minute ones; jobs of 3 h or less can start on far more of Narval.
- **`--cpus-per-task=12`**: one A100's share of a 48-core, 4-GPU node, so free in billing -- and since the job is CPU-bound, the workers are where speed comes from. Ten DataLoader workers, kept alive across epochs.
- **`--mem=16G`**: 1.04 GB measured at load plus ten workers' buffers.
- **Fit counts are simulated** by running each search through the real greedy and leave-one-out code with a counting scorer. Memoisation made the old formula wrong: it said 63 fits for `vnir_swir`, which is 51.

The whole programme is about **50 GPU-hours**. Recalibrate once real CNN fits exist: every fit now appends its wall time to `fits.jsonl`, and `narval_resources.py --runs` re-derives every request from them. If a fit takes under ~1.4 min, the band arms fit the 3 h bin.

Two standing caveats on every number they produce. The 35-epoch budget is a **ranking** budget, so the output is an order and not an accuracy until the top sets are re-run at full budget. And the fold spread is large -- the one arm that has completed spanned 0.5396 to 0.7660 across six folds from a single model on a single input -- so results must be read as **paired** per-fold contrasts via `report_arms.py`, never as two means compared by eye.

