# Experiment register

**Generated from `src/safari_bands/experiments.py` by `scripts/make_experiments_doc.py`. Do not edit by hand** -- the figure `docs/results/figures/experiment_plan.png` renders from the same register, and a hand-kept copy drifts.

56 experiments. **31 can run today** on data already packed and staged.

## Read this first: the label

**Every result on the original 11-band pack trained on a circular label.** Its `/mask` is not NBAC: for fire scenes, `download.py` writes `_mask.tif` as **dNBR > 0.27**, and NBAC sat in a `_nbac.npy` sidecar that nothing in the tile or pack path read. All 861 fire tiles across the three splits reproduce `_mask.tif`'s dNBR exactly; against the patches' own NBAC masks the mean IoU is 0.755. dNBR is `NBR_pre - NBR_post` with `NBR = (B8 - B11)/(B8 + B11)`, so `NBR_pre` is reconstructible from the input bands -- rule 3's circularity. `sweep_bands.py --label nbac` was validated, printed and recorded, and never read.

The damage concentrates where it matters most: B8, B8A and B11 in the ranking, and E-11 above all, because NDMI is `(B8A - B11)/(B8A + B11)` -- nearly the label's own input.

**Fixed:** `stage2_fire_11band_nbac` swaps NBAC into the fire masks and changes nothing else -- tiles, splits and bands are byte-identical, so the held-out test set does not move. It declares `label_source = nbac`, and the sweep refuses any pack that does not declare one. NBAC marks 43% more burned pixels than dNBR did in the fire tiles: perimeters are filled polygons, so they include the inclusions dNBR skipped.

## Feasibility at a glance

| State | Count | What it means | Experiments |
|---|---|---|---|
| **Runnable now** | 15 | data packed and staged; nothing missing | E-4, E-7, E-11, E-12, E-13, E-14, E-15, E-19, E-26, E-27, E-28, E-34, E-36, E-37, E-38 |
| **Partial result** | 16 | some folds or arms have completed; the rest are blocked | E-1, E-2, E-3, E-5, E-6, E-10, E-21, E-32, E-33, E-43, E-49, E-50, E-51, E-52, E-53, E-54 |
| **Needs code** | 6 | no new data; a runner or a flag has to be written | E-17, E-18, E-29, E-39, E-40, E-41 |
| **Needs a pack** | 9 | data held but not tiled, packed or transferred | E-8, E-20, E-22, E-35, E-42, E-46, E-47, E-48, E-56 |
| **Needs new data** | 7 | free to obtain, not yet held | E-9, E-23, E-24, E-25, E-44, E-45, E-55 |
| **No label exists** | 3 | cannot be run with any amount of work on data we hold | E-16, E-30, E-31 |

Numbering note: E-17 to E-20 were an earlier E-1 to E-4 from the CFFDRS gap audit. They were renumbered into this single register rather than left as a second scheme; `docs/CFFDRS_GAPS.md` points at the new ids.

## Experiments

### CFFDRS mirror

| ID | Experiment | Hypothesis | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|---|
| **E-32** | CFFDRS as is (R0) ★ | FBP head-fire intensity ranks burned pixels above chance within fire patches, and FWI/BUI ranks fire above confuser patches. WRONG IF the physics scores sit at chance on both: then the outcome measures something CFFDRS does not rate, and every imagery delta would be against a meaningless floor. | none learned: FBP ROS / HFI / CFB per pixel and FWI codes per patch, computed from the operational inputs | within-patch and between-patch AUC, per process | Partial result | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` |
| **E-33** | Fuel inventory comparison | Pre-fire inventories (CWFIS 2019 and 2014b, the SCANFI v2 pre-fire step) give R0 skill within noise of each other, and the post-fire ones (CWFIS 2024, SCANFI 2025) score far higher. WRONG IF a post-fire inventory does NOT inflate skill: then the leakage measured in A-25 does not reach the outcome. | the fuel inventory feeding R0: CWFIS 2024 / 2019 / 2014b, SCANFI v2 2005-2025, SCANFI v1 2020 | R0 within-patch AUC per process, and the gap between pre- and post-fire inventories | Partial result | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` |
| **E-34** | Learned CFFDRS (R1/R2) | A model given exactly the CFFDRS inputs (R1) beats R0, and physics plus a learned residual (R2) is within noise of R1. WRONG IF R1 does not beat R0, which would say the outcome is already as predictable from CFFDRS inputs as CFFDRS makes it. | R0 vs R1 vs R2 on identical inputs and folds | paired within/between-patch AUC per process | Runnable now | `Fire_Risk_FW/scripts/shell/sweep_slots.sh CONFIGS=r0_scanfi,r0_cwfis,r1,r2,r2_cwfis` |
| **E-35** | Fuel-type slot | Imagery-derived fuel type improves within-patch skill over the pre-fire operational layer. WRONG IF the shuffled-imagery twin gains as much, which would make the gain a shortcut. | the fuel-type slot's source: pre-fire inventory vs imagery_replace (ecology model) vs imagery_correct | paired delta in within-patch AUC per process | Needs a pack | *none yet* |
| **E-36** | Percent-conifer slot | Imagery percent conifer improves M-1/M-2 spread and intensity. WRONG IF no gain survives on mixedwood pixels. | percent-conifer source for M-1/M-2: inventory vs imagery | paired delta on M-1/M-2 pixels | Runnable now | `Fire_Risk_FW/scripts/shell/sweep_slots.sh CONFIGS=r3_pc,r3_pc_shuffled` |
| **E-37** | Crown-base-height slot | Imagery-informed CBH changes crown fraction burned enough to move intensity skill. WRONG IF the CFB term never engages at our fire weather. | CBH source: ST-X-3 default vs height-derived | paired delta in the intensity branch | Runnable now | `Fire_Risk_FW/scripts/shell/sweep_slots.sh CONFIGS=r3_cbh,r3_cbh_shuffled` |
| **E-38** | Curing slot | Imagery curing beats the CWFIS curing product on O-1 pixels. WRONG IF it does not -- but O-1 is about 3 % of burned pixels, so a null is likely to be 'n insufficient'. | curing source: CWFIS percent curing (2020-2025) or the time-of-year default vs S2 curing | ignition and spread on O-1 pixels | Runnable now | `Fire_Risk_FW/scripts/shell/sweep_slots.sh CONFIGS=r3_curing,r3_curing_shuffled` |
| **E-39** | Canopy closure to in-stand moisture | Imagery stand density sharpens ignition receptivity through the stand-specific FFMC adjustment. WRONG IF the adjusted in-stand FFMC ranks ignitions no better than open FFMC. | closure source for the in-stand FFMC adjustment | Stage C ignition AUC and calibration | Needs code | *none yet* |
| **E-40** | Green-up slot | An S2 green-up date beats the CWFIS green-up product for the D-1/M-1/M-2 leafless-to-green switch. WRONG IF the two agree to within a few days, leaving nothing to gain. | green-up source: CWFIS product (2020-2025, held) vs S2 phenology | spread and ignition on deciduous and mixedwood pixels | Needs code | *none yet* |
| **E-41** | Spread R0 (CFSDS) | FBP ROS correlates with observed daily spread (Spearman rho > 0). WRONG IF it does not, which would bound everything the spread branch can claim. | none learned: FBP ROS on each fire-day | Spearman rho and log-ratio error against CFSDS spread | Needs code | *none yet* |
| **E-42** | Spread slot value | Fuel-side imagery slots improve per-fire-day spread prediction. WRONG IF only weather-side inputs move it. | slot sources, as in E-35 to E-40, on the spread target | paired change in Spearman rho per fire-day | Needs a pack | *none yet* |
| **E-44** | Ignition R0 | P(sustained flaming) x P(lightning holdover) ranks lightning starts above matched controls. WRONG IF at chance. | none learned: the published ignition relationships | AUC and calibration, starts vs matched controls | Needs new data | *none yet* |
| **E-45** | Ignition slot value | Closure, green-up and fuel-type slots improve ignition ranking. WRONG IF the shuffled twins gain as much. | slot sources on the ignition target | paired AUC change | Needs new data | *none yet* |
| **E-46** | Band and index decision | The combined ranking keeps at least one red-edge band and B11 within the Mantis k=6 / k=4 sets. WRONG IF SWIR never earns a slot on any process's weighted evidence. | per-slot nested rankings weighted by slot value (A-29) | the chosen band and index sets, with their margins | Needs a pack | *none yet* |
| **E-47** | Architecture decision | A tier2-class model is within one SE of the best preset at the chosen bands. WRONG IF only tier3 or larger reaches it. | model preset, R2 vs R4 form | paired skill at the chosen bands; the onboard/ground split | Needs a pack | *none yet* |
| **E-49** | Dating the weather (R0) | Moving R0's weather from the legacy 30-June daily aggregates to each patch's D-1 at 13:00 LDT RAISES the between-patch AUC of the fast codes (FFMC, ISI) and LOWERS that of the slow codes (DC, BUI): the fast codes will describe the day before the fire rather than 30 June, and part of the slow codes' legacy 0.83 (DC) came from reading the fire year's drought after most fires had started. WRONG IF the fast and slow codes move in the same direction, or no code moves outside its CI. | weather design, as a chain on the same patches: legacy -> dated (daily aggregates, flat spin-up) -> dated at 13:00 LDT -> dated with the Appendix C-2 start-up and overwintered DC (the P3 design) | between-patch AUC and paired fire-vs-own-confuser win rate per FWI code; within-patch HFI AUC, reported | Partial result | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` |
| **E-52** | Weather source: station vs ERA5 (R0) | The nearest CWFIS station's reported codes at D-1 rank fire above non-fire patches at least as well as ERA5-Land at 13:00 LDT (they are what CFFDRS actually runs on), and the ERA5-to-station disagreement in the codes grows with distance to the station. WRONG IF the disagreement is flat with distance: E-17's mechanism (weather error grows away from stations) would then have no support in the codes. | weather source for the same patches and date: ERA5-Land at the patch centre vs the nearest CWFIS station's reported observation and codes | between-patch AUC per code and source; \|ERA5 - station\| per code against station distance (Spearman) | Partial result | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` |
| **E-55** | Operational FWI grid vs the reconstruction | The FWI grid CWFIS issued for D-1 ranks fire above non-fire development patches as well as our ERA5-Land FWI does: the two between-patch AUCs are within 0.03 of each other, and the two FWI values agree across patches (Spearman rho >= 0.8). WRONG IF they differ by more than 0.03 with a CI excluding 0, or rho < 0.8: then R0 does not stand in for operational CFFDRS, and every imagery delta measured against R0 or R2 is measured against a different baseline from the one operations use. | FWI source on D-1 for the same patches: CWFIS operational grid (GeoServer public:fwi, 2 km, archived from 2018-01-01) vs ERA5-Land at 13:00 LDT (fwi.py, variant c2) vs the nearest CWFIS station's reported FWI | between-patch AUC per source (all pairs and same-year pairs), paired by patch with a fire/block-group bootstrap; Spearman rho and median difference, operational vs ERA5 and vs station | Needs new data | *none yet* |
| **E-56** | Operational FBP outputs on a 2024-2025 cohort | On fires that started in 2024-2025, the HFI CWFIS issued for D-1 ranks fire above non-fire patches within 0.03 of our R0 HFI for the same patches and day (between-patch AUC), and the two agree across patches (Spearman rho >= 0.7). WRONG IF they differ by more than 0.03 with a CI excluding 0: the operational inputs our reconstruction replaces (interpolated station weather, the CWFIS fuel grid, its FMC, green-up and curing) then carry, or lose, skill R0 does not. | HFI (and ROS, CFB, FMC, fuel type) source on D-1: CWFIS operational grids (public:hfi etc., 2 km, from 2024-01-01) vs our R0 on the same patches | between-patch AUC per source, paired by patch; Spearman rho per output; fuel-type agreement (share of area) | Needs a pack | *none yet* |

### Band selection

| ID | Experiment | Hypothesis | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|---|
| **E-1** | VNIR band selection ★ | Red-edge earns a slot: the best six include at least one of B5/B6/B7 and exclude both 60 m atmospheric bands (B1, B9). WRONG IF an atmospheric band survives into the best six, which would say the ranking is reading haze rather than vegetation. | which 6 of the 10 Sentinel-2 bands in 400-1000 nm | auc_px, scenario-held-out folds, per set size k | Partial result | `sweep_arms.sh ARMS=vnir` |
| **E-2** | All-11 greedy | B11 enters by k=3, because the NIR/SWIR contrast is the strongest single moisture signal available. WRONG IF it has not entered by k=7, which would be weak evidence against the SWIR chain -- weak, because one band cannot stand in for four. | unconstrained choice over all 11 packed bands | auc_px, scenario-held-out folds; the k at which B11 first enters | Partial result | `sweep_arms.sh ARMS=all11` |
| **E-3** | Forced-SWIR delta | Positive but small: under +0.02 auc_px. One band in the window is a poor proxy for a four-band mode, so a large gain would be surprising and a null is not disqualifying. | B11 held in the set vs the VNIR-only set, matched k | the paired difference in auc_px, scenario-held-out folds | Partial result | `sweep_arms.sh ARMS=vnir_swir` |
| **E-4** | SWIR-only floor | Clearly above chance and clearly below the VNIR set. The water features at 1200 and 1600 nm are physically present, so a learned model should find something; without the NIR anchor it cannot normalise for canopy structure or illumination. WRONG IF it matches the VNIR set, which would make the MS chain arguable. | B11 alone, no VNIR band | auc_px, scenario-held-out folds | Runnable now | `sweep_arms.sh ARMS=swir_only` |
| **E-5** | Leave-one-out band value | Every individual drop is small, because the pool is redundant. B8 and B8A in particular each look worthless while the pair is not: leave-one-out cannot see mutual substitution, and reading a small drop as 'this band does not matter' is the trap. WRONG IF any single removal costs more than about 0.02, which would mean the pool is far less redundant than the near-duplicate pairs suggest and the chosen set is already minimal. | each band removed in turn from the chosen set | the drop in auc_px, scenario-held-out folds on removing each band | Partial result | `sweep_bands.py --leave-one-out (rides in E-1..E-4)` |
| **E-6** | Selection stability | The top two or three bands are selected in 6/6 folds and the tail is unstable. WRONG IF even the top band swings, which would mean the ranking is fold noise and no k is reportable. | the same search re-run inside each of 6 location folds | the fraction of folds that select each band at each k | Partial result | `pool_bands.py (after E-1..E-4)` |
| **E-7** | Resolution requirement | Graceful degradation from 20 to 40 m and a sharper fall by 80 m. WRONG IF 20 -> 40 m already costs materially, which matters more than it sounds: the Mantis MS mode is 32 m at 500 km, so our 20 m results would overstate what the sensor delivers. | ground sample distance 20 / 40 / 80 m, in 'pixels' mode: pooled then re-expanded, so INFORMATION is degraded while the tile keeps its shape | auc_px, scenario-held-out folds vs GSD, paired against 20 m | Runnable now | `sweep_axes.sh SETS=gsd` |

### Controls

| ID | Experiment | Hypothesis | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|---|
| **E-8** | Label independence control (control) | The ranking is largely preserved. WRONG IF B11's value collapses specifically -- that would say it was reading NBR-like information shared with the perimeter delineation rather than fuel, which is exactly the circularity rule 3 exists to catch. | the label source: NBAC perimeters vs VIIRS thermal | change in the band ranking and in auc_px, scenario-held-out folds | Needs a pack | *none yet* |
| **E-9** | Lightning cohort (control) | Absolute skill drops (fewer and harder cases) but the band ranking holds. WRONG IF the ranking changes, which would say human-ignition access signals -- roads, settlement -- were driving it. | fires filtered to NFDB CAUSE = lightning | auc_px, scenario-held-out folds, restricted cohort | Needs new data | *none yet* |
| **E-10** | Negative control (control) | The noise arm is within noise of 0.5, and the real-band arm clearly beats it. WRONG IF the noise arm sits clearly above 0.5: then a POSITIONAL PRIOR -- where burn tends to sit in a tile, learnable from zero padding without reading a band -- inflates every arm in this register, and must be subtracted before any of them is quoted. | the input: the 9 surface bands vs fresh Gaussian noise of the same width | auc_px, scenario-held-out folds against chance, and against the real-band arm | Partial result | `sweep_axes.sh SETS=neg` |
| **E-26** | Within-fire burn pattern | Imagery separates burned from unburned pixels INSIDE fire patches at least as well as it does across all patches, because inside a perimeter the outcome is fuel, terrain and firebreaks rather than whether a fire started. WRONG IF within-fire skill is clearly lower, which would say most unconditional skill comes from recognising WHICH patches burned -- between-patch discrimination, not fuel. | the training cohort: all scenes vs fire patches only, with each fold's locations held fixed | auc_px, scenario-held-out folds within fire tiles vs overall; and both models scored on the SAME fire tiles | Runnable now | `sweep_axes.sh SETS=cond` |
| **E-43** | Date-only control (control) | Day of year and latitude alone separate fire from non-fire at about chance. WRONG IF they do not: the pseudo-date rule for negatives would then be a shortcut every arm can read. | date features only (day-of-year sin/cos, latitude) | between-patch AUC | Partial result | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` |
| **E-54** | Legacy composite leakage | For fires that started before 30 June, the legacy April-June composite already shows the burn: on burned pixels its NIR-SWIR1 index (B8, B11) is lower than in the pre-fire composite ending D-1, relative to the same change on the patch's unburned pixels, and the drop grows with the days between the fire's start and 30 June. Fires starting in July or later show no drop. WRONG IF the early fires show no drop: then the v1 imagery did not read the outcome, whatever its weather did. | composite: legacy April-June of the patch year vs pre-fire (D-45 to D-1, extended to D-90, else last summer) | difference-in-differences of the B8/B11 index (legacy minus pre-fire, burned minus unburned pixels) per fire patch, against days of overlap (30 June minus D) | Partial result | `Fire_Risk_Model/scripts/python/build_prefire.py` |

### Index baselines

| ID | Experiment | Hypothesis | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|---|
| **E-11** | Greenness vs moisture indices ★ | `both` beats `greenness` by a small but fold-consistent margin, because direct water absorption at 1610 nm carries information a greenness proxy cannot; and `moisture` (2 bands) draws with `greenness` (5 bands). WRONG IF `both` does not beat `greenness`, which would say the 1610 nm moisture signal adds nothing this label can see -- a publishable null, and one that would weaken the case for the SWIR chain considerably. | the index family given to the model: greenness (NDVI, EVI, VARI, NDRE) / moisture (NDMI, MSI) / both / raw bands | the paired difference in auc_px, scenario-held-out folds, against greenness | Runnable now | `sweep_indices.sh` |
| **E-12** | Index baseline vs learned bands | The learned model on raw bands beats every index family, because an index is a fixed projection that discards information a model could use. WRONG IF indices match it, which would be a strong argument for shipping indices -- cheap on an FPGA and interpretable to an operational user. | hand-built indices vs the learned model on raw bands | the paired difference in auc_px, scenario-held-out folds | Runnable now | `sweep_indices.sh ARMS=raw,both` |

### Covariates

| ID | Experiment | Hypothesis | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|---|
| **E-13** | Weather representation | BOTH is within noise of CODES. The FWI codes already integrate the same 91 days through a recursion tuned over decades, so our 12 features are unlikely to extract much the codes have not. WRONG IF BOTH wins clearly -- then check DIMENSIONLESS, because a gain that disappears there came from absolute level, which at 45-70 N is latitude wearing a weather costume. | the scalar columns the fusion head sees: FWI codes / our 12 compressed history features / both / dimensionless history | the paired difference in auc_px, scenario-held-out folds, against codes | Runnable now | `sweep_covariates.sh SETS=weather` |
| **E-14** | Fusion architecture | Both fusion variants beat rasters_only, and two_head is within noise of bottleneck. The CFFDRS-shaped separation is expected to cost little; if it costs a lot, the architecture argument has to give way to the measurement. WRONG IF rasters_only matches both, which would say the weather scalars add nothing at this label and sample size -- and would make E-13 moot. | how weather enters: not at all / two-head late / bottleneck | the paired difference in auc_px, scenario-held-out folds | Runnable now | `sweep_covariates.sh SETS=fusion` |
| **E-15** | Imagery vs the FBP formula | Imagery plus the FMC scalar beats the scalar alone, substantially. The FBP equation is a function of latitude, longitude, elevation and date only -- it carries no information about the stand -- so a null here would be surprising, and would cast doubt on the imagery rather than vindicate the formula. | the FBP foliar-moisture scalar alone vs that scalar plus all 9 surface bands | the paired difference in auc_px, scenario-held-out folds | Runnable now | `sweep_covariates.sh SETS=g1` |
| **E-16** | FMC arms | None. The arms are identical by construction, so no prediction is possible and any apparent difference would be seed noise. | baseline / measured / augment foliar moisture | (none obtainable) | No label exists | `-- (do not run)` |

### CFFDRS gaps

| ID | Experiment | Hypothesis | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|---|
| **E-17** | Station-density stratification | The imagery increment grows with distance to the nearest station. Fuel moisture is the integral of weather, so a satellite estimate should be worth most where the weather grid is interpolated from furthest away -- the north, which is also where most area burns. | distance from each patch to the nearest fire-weather station | the imagery increment in auc_px, scenario-held-out folds, stratified by that distance | Needs code | *none yet* |
| **E-18** | Snow-off startup | Correcting the start date changes DC and DMC materially above 55 N and improves skill there, with little effect in the south. Our flat 90-day spinup starts around 1 April into frozen, snow-covered ground, so the spurious drying should scale with latitude. | FWI start date: per-pixel NDSI snow-off vs our flat 90-day spinup | change in the FWI codes, and auc_px, scenario-held-out folds | Needs code | *none yet* |
| **E-19** | Latitude-banded weather | History beats codes at high latitude specifically, and not in the south. The day-length factors are tabulated for ~46 N, so the codes should be least trustworthy where that assumption is furthest from the truth. WRONG IF the gain is uniform across bands, which would make the mechanism something other than day length. | the E-13 weather contrast, scored separately in 0-55 / 55-60 / 60-90 N on the same trained models | the INTERACTION: (history - codes) in 60-90 N minus the same in 0-55 N, paired by fold | Runnable now | `sweep_covariates.sh SETS=weather` |
| **E-20** | Weather staleness | Skill decays with weather age, fastest for CODES and slowest for the dimensionless history. This is the testable half of a claim fwi.py already makes from input drift alone (DC 8.2% over three days against ISI's 89.9%). WRONG IF decay is flat, which would mean a daily uplink costs nothing and the slow-code argument is unnecessary. | the age of the weather at inference: 0 / 24 / 48 / 72 h / 7 d | auc_px, scenario-held-out folds vs weather age, per weather arm | Needs a pack | *none yet* |
| **E-21** | Fuel-layer refresh | A positive slope: the advantage of a refreshed estimate grows with the staleness gap. At gap 0 our estimate should LOSE, because it is a noisy copy of its own training target -- which is why the slope and not the level is the estimator. WRONG IF the slope is flat or negative. (This clause restates the prediction's negation; it was written 2026-10-24, after P2's inventory-half result, and changes nothing it predicts.) | the fuel inventory's vintage (SCANFI v2 2005-2020, pre-fire steps only), and later our refreshed estimate, against the gap to the fire year | the SLOPE of auc_px, scenario-held-out folds against staleness, not the level | Partial result | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` |
| **E-22** | Ecology arm ★ | The ranking from dense SCANFI labels differs from the fire-outcome ranking, and SWIR ranks higher in it. Structure and biomass retrieval leans on SWIR more than a burn outcome does, because the outcome is diluted by ignition and weather. If the two rankings agree, that is a strong convergent result for whichever bands win. | the same band searches, against SCANFI structure instead of a burn outcome | per-pixel error on cover, closure, height, biomass, species | Needs a pack | `train_ecology.sh` |
| **E-50** | Latitude-correct day length (R0) | Scaling the DMC day-length factors from 46 N to each patch's latitude raises DMC more at >=60 N than at <55 N (longer summer days), and raises R0's between-patch AUC of DMC and BUI more in the north. WRONG IF the DMC shift is uniform across bands. The AUC half rests on 19 northern fire patches and is read only beside the shift. | DMC day-length factors: Van Wagner's 46 N table vs the same table scaled by astronomical day length at the patch latitude over that at 46 N (our construction) | DMC and BUI shift by latitude band; between-patch AUC per band | Partial result | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` |
| **E-51** | Operational start-up (R0) | The GLC-X-42 Appendix C-2 start-up (codes begin 3 days after ERA5-Land snow cover is gone, or after 3 days at or above 12 C at 13:00 where snow is absent) with an overwintered DC moves DC and DMC at D-1 more at >=60 N than at <55 N, compared with a flat 90-day spin-up from the default start values, and its effect on R0's between-patch AUC is larger in the north. WRONG IF the code shift does not grow with latitude. This is E-18's mechanism under the operational rule; E-18's imagery arm is P6. | start-up: flat 90-day spin-up from FFMC 85 / DMC 6 / DC 15 vs Appendix C-2 start-up with overwintered DC (cffdrs coefficients a = b = 0.75) | DC and DMC shift at D-1 by latitude band; between-patch AUC per band | Partial result | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` |
| **E-53** | Weather staleness under R0 | R0's between-patch AUC decays with the age of the weather (D-1, D-2, D-3, D-7), fastest for FFMC and ISI and slowest for DC and BUI. WRONG IF the fast codes do not lose more than the slow ones by D-7. This is E-20's mechanism without learning: the curve E-20's learned arms are compared with. | weather age at scoring: 1, 2, 3, 7 days before D | between-patch AUC per code against weather age | Partial result | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` |

### Hyperspectral

| ID | Experiment | Hypothesis | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|---|
| **E-23** | SWIR band placement | The best four cluster near 1240, 1610 and 1680-1730 nm, with the fourth in the 1500s. From brief hypotheses H1 and H3: resolving a dry-matter change needs two water-sensitive bands with different water-to-dry-matter absorption ratios. | any 4 centres and widths in 1003-1359 and 1414-1749 nm (140 usable channels) | retrieval error per candidate set | Needs new data | `fetch_aviris.py + ingest_aviris.py` |
| **E-24** | 1209 vs 1240 nm | 1240 nm is slightly better for water sensitivity and 1209 slightly better for O2 margin, with the difference small enough that the flown WorldView-3 centre is defensible. A large difference either way is the interesting outcome. | WorldView-3's flown centre against Gao's NDWI band | retrieval error, and O2 absorption margin | Needs new data | `ingest_aviris.py --mode both` |
| **E-25** | Spectral resolution: HS vs MS | Diminishing returns beyond roughly 10-15 well-placed bands, so the HS mode's 96 channels buy little over a well-chosen MS set. WRONG IF the curve keeps climbing, which would make the HS mode the better instrument and change the payload decision. | 140 SWIR channels at 5 nm vs the best 4-6 broad bands | retrieval error vs channel count | Needs new data | `ingest_aviris.py, then sweep_bands.py` |

### Hardware

| ID | Experiment | Hypothesis | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|---|
| **E-27** | Cost per input channel | BRAM scales roughly linearly with input channel count, so 96 channels are infeasible on the target part and 11 are affordable. Stream BRAM is ceil(width/18) x ceil(depth/1024) and width never stops paying. WRONG IF scaling is sub-linear because the first convolution dominates, which would make a wide input cheaper than the marginal-cost argument assumes. | input channel count: 3 / 6 / 10 / 11 / 96 | BRAM, DSP, LUT and latency from a real conversion | Runnable now | `sweep_architecture.py --widths` |
| **E-28** | Co-registration tolerance | Negligible cost below a quarter pixel, material by one pixel. WRONG IF a half-pixel shift already costs materially, which would tighten the dichroic and focal-plane alignment budget; or if two pixels cost little, which would retire the registration risk. | SWIR-channel shift at evaluation: 0, 0.25, 0.5, 1, 2 px, on a model trained with the channels registered | the drop in auc_px, scenario-held-out folds against the unshifted score, paired by fold | Runnable now | `sweep_axes.sh SETS=shift` |
| **E-48** | Hardware decision | The chosen model fits a Q8 at <= 80 % of every resource. WRONG IF only the Q9 fits, or none does. | board (Q7, Q8, Q9) x model x input channels | BRAM / DSP / LUT, latency, power (A-29) | Needs a pack | *none yet* |

### Out of reach

| ID | Experiment | Hypothesis | Independent variable | Dependent variable | State | Runner |
|---|---|---|---|---|---|---|
| **E-29** | T1 live foliar moisture | From Jolly et al. (2014), the brief's lead hypothesis H1: dry matter, not water content, drives seasonal conifer LFMC, so water-only bands will return EWT rather than LFMC and a two-band water contrast is required. Untestable here until an LFMC label exists. | LFMC, the brief's lead retrieval target | RMSE against gravimetric LFMC | Needs code | *none yet* |
| **E-30** | T2 curing / NPV fraction | Brief hypothesis H2: SWIR2 is necessary for curing and 1240 nm is not a substitute, because the cellulose/lignin feature near 2100 nm is what separates NPV from soil. Untestable here: no curing label, no grassland, and the band is past the detector. | grass curing fraction | error against field curing | No label exists | *none yet* |
| **E-31** | Fire occurrence prediction | None offered. Out of scope by decision, and a hypothesis recorded for work that will not run invites being mistaken for a finding. | ignition probability per cell-day | (out of scope) | No label exists | `-- (out of scope)` |

## Hypotheses and conclusions

Each experiment carries a falsifiable **prediction** and the condition that would refute it, then what could be **concluded** either way. The conclusion field is what decides whether an experiment deserves GPU time: one whose null result teaches nothing is not worth queueing, and writing it down is how that gets noticed before the run.

The hypotheses are written to be capable of being wrong. `CLAUDE.md` is explicit that the study's job is to **test** the brief's hypotheses rather than confirm them, so each states what being wrong would look like. Where a prediction comes from the brief (H1, H2, H3) it is attributed; the rest are this study's own and carry no more authority than that.

### CFFDRS mirror

**E-32 — CFFDRS as is (R0)**

*Hypothesis:* FBP head-fire intensity ranks burned pixels above chance within fire patches, and FWI/BUI ranks fire above confuser patches. WRONG IF the physics scores sit at chance on both: then the outcome measures something CFFDRS does not rate, and every imagery delta would be against a meaningless floor.

The non-learned reference every imagery slot is measured against -- CFFDRS itself, not a model trained on its inputs.

*Note:* P2, legacy design (docs/results/p2_r0): SUPPORTED. Within fire patches, FBP HFI AUC 0.676 [0.65, 0.70] on pre-fire SCANFI, 0.623 on CWFIS 2019; half that margin is water and non-fuel (land only: 0.589, 0.558). Between patches FWI 0.738, BUI 0.765, DC 0.828; fire beats its own confuser on DC in 88 % of 68 pairs. P(sustained flaming) is ~0.5 within patches: NBAC is not an ignition outcome (Stage C is). P3, dated design: SUPPORTED. Within HFI 0.681 (SCANFI), dated minus legacy +0.005 [-0.002, +0.012]; between: patch-mean HFI 0.863, BUI 0.878, FWI 0.841.

*Blocked on:* legacy 30-June design only; P3 re-dates the weather to each fire's start

**E-33 — Fuel inventory comparison**

*Hypothesis:* Pre-fire inventories (CWFIS 2019 and 2014b, the SCANFI v2 pre-fire step) give R0 skill within noise of each other, and the post-fire ones (CWFIS 2024, SCANFI 2025) score far higher. WRONG IF a post-fire inventory does NOT inflate skill: then the leakage measured in A-25 does not reach the outcome.

Which operational fuel input is honest on burned ground, and how much a post-fire inventory would flatter a result.

*Note:* P2 (docs/results/p2_r0): REFUTED on both counts. Pre-fire inventories are not equal: SCANFI through the CFS tree beats CWFIS 2019 by +0.053 [+0.037, +0.071] within-patch HFI AUC (+0.031 on land only; resolution alone adds nothing once water is masked). Post-fire inventories DEFLATE R0: CWFIS 2024 0.21, SCANFI 2025 0.49. The leak reaches the outcome (+0.41 AUC) but unlearned physics reads it backwards; a learner would not. The CFS tree beats the A-11 rules by +0.081 on land.

*Blocked on:* the SCANFI v1 adapter is not written; SCANFI 2005 pending

*CFFDRS gap:* G2 fuel-type layer is a fixed vintage

**E-34 — Learned CFFDRS (R1/R2)**

*Hypothesis:* A model given exactly the CFFDRS inputs (R1) beats R0, and physics plus a learned residual (R2) is within noise of R1. WRONG IF R1 does not beat R0, which would say the outcome is already as predictable from CFFDRS inputs as CFFDRS makes it.

The learned baseline the imagery slots are added to, and whether the physics layer costs or buys anything.

*Note:* P5: SlotNet R0-R2 written (Fire_Risk_FW cffdrs_net.py); R2 starts as R0 by construction. P7 (docs/results/p7_slots): MIXED. R1 - R0 within +0.051 [+0.034, +0.068], 5/5 folds; R2 - R1 within -0.025 [-0.034, -0.015], between -0.006 (CI spans 0).

**E-35 — Fuel-type slot**

*Hypothesis:* Imagery-derived fuel type improves within-patch skill over the pre-fire operational layer. WRONG IF the shuffled-imagery twin gains as much, which would make the gain a shortcut.

Whether the imager should refresh FBP fuel type.

*Note:* P5: the cffdrs half runs now (r2 vs r2_cwfis: SCANFI tree vs CWFIS 2019 under R2); the imagery replace form waits for E-22. P7: CWFIS 2019 vs SCANFI fuel under R2 -0.007 [-0.017, +0.003] within (under R0 -0.048): learning absorbs most of the inventory gap.

*Blocked on:* E-22 (ecology model) and pack v2

*CFFDRS gap:* G2 fuel-type layer is a fixed vintage

**E-36 — Percent-conifer slot**

*Hypothesis:* Imagery percent conifer improves M-1/M-2 spread and intensity. WRONG IF no gain survives on mixedwood pixels.

Brief target T4 as a CFFDRS input rather than a map.

*Note:* P5: the imagery_correct form is runnable (pc + 30 tanh(head), through the physics); the imagery_replace form waits for the ecology estimator (E-22, P6). P7: AT RISK. Correct form -0.001 [-0.004, +0.001] within, equal to its twin; the head learned a near-uniform -24-point shift. M-1/M-2-restricted scoring added to run_slots after this sweep.

*CFFDRS gap:* G2 fuel-type layer is a fixed vintage

**E-37 — Crown-base-height slot**

*Hypothesis:* Imagery-informed CBH changes crown fraction burned enough to move intensity skill. WRONG IF the CFB term never engages at our fire weather.

Whether stand height from orbit belongs in FBP's crown fire initiation.

*Note:* P5: the imagery_correct form is runnable (CBH x exp(0.7 tanh(head))); the height-derived replace form waits for P6. P7: AT RISK. Correct form -0.0005 [-0.003, +0.002], equal to its twin; CFB > 0 on 47 % of burnable pixels, so the falsifier did not fire. Height-derived form waits for P6.

**E-38 — Curing slot**

*Hypothesis:* Imagery curing beats the CWFIS curing product on O-1 pixels. WRONG IF it does not -- but O-1 is about 3 % of burned pixels, so a null is likely to be 'n insufficient'.

The FWI2025 curing input, tested where grass exists.

*Note:* P5: the imagery_correct form is runnable against the cffdrs default (80 %); the CWFIS curing product is still not held, so the operational comparison waits. P7: not tested. The SCANFI fuel tree has no O-1 pixel, so the correction never acts (delta exactly 0). Needs the curing run on CWFIS fuel (O-1b 4.6 % of pixels).

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

*Blocked on:* FBP port; cfsds.py and the spread dataset are not written

**E-42 — Spread slot value**

*Hypothesis:* Fuel-side imagery slots improve per-fire-day spread prediction. WRONG IF only weather-side inputs move it.

Imagery's value on the outcome FBP actually predicts.

*Blocked on:* the spread dataset and the slot network

**E-44 — Ignition R0**

*Hypothesis:* P(sustained flaming) x P(lightning holdover) ranks lightning starts above matched controls. WRONG IF at chance.

Stage C's floor: ignition receptivity, not occurrence (A-28).

*Blocked on:* NFDB points not fetched; the continuous model needs Q26 or the Wotton & Wheatley (2025) GAM table (from the authors); GLC-X-42 classes are the interim score

**E-45 — Ignition slot value**

*Hypothesis:* Closure, green-up and fuel-type slots improve ignition ranking. WRONG IF the shuffled twins gain as much.

Imagery's value on the ignition process.

*Blocked on:* E-44

**E-46 — Band and index decision**

*Hypothesis:* The combined ranking keeps at least one red-edge band and B11 within the Mantis k=6 / k=4 sets. WRONG IF SWIR never earns a slot on any process's weighted evidence.

The CubeSat's bands and indices.

*Blocked on:* plan P6/P7 results

**E-47 — Architecture decision**

*Hypothesis:* A tier2-class model is within one SE of the best preset at the chosen bands. WRONG IF only tier3 or larger reaches it.

The onboard model.

*Blocked on:* E-46

**E-49 — Dating the weather (R0)**

*Hypothesis:* Moving R0's weather from the legacy 30-June daily aggregates to each patch's D-1 at 13:00 LDT RAISES the between-patch AUC of the fast codes (FFMC, ISI) and LOWERS that of the slow codes (DC, BUI): the fast codes will describe the day before the fire rather than 30 June, and part of the slow codes' legacy 0.83 (DC) came from reading the fire year's drought after most fires had started. WRONG IF the fast and slow codes move in the same direction, or no code moves outside its CI.

Whether the legacy design flattered or hid CFFDRS, and what each design step moves -- the baseline every later delta is read against.

*Note:* P3 (docs/results/p3_dated): REFUTED. Legacy -> dated: FFMC 0.695 -> 0.799, ISI 0.701 -> 0.781, but BUI 0.765 -> 0.878 and DC 0.828 -> 0.830. Year alone scores 0.87, and within a year the fast codes do not gain (FFMC 0.730 -> 0.717) while the slow ones do (DMC 0.673 -> 0.839, BUI 0.691 -> 0.845, DC 0.743 -> 0.827). Dating helps through the slow codes; the prediction had them backwards.

*Blocked on:* needs the same chain on the frozen test set (P10)

**E-52 — Weather source: station vs ERA5 (R0)**

*Hypothesis:* The nearest CWFIS station's reported codes at D-1 rank fire above non-fire patches at least as well as ERA5-Land at 13:00 LDT (they are what CFFDRS actually runs on), and the ERA5-to-station disagreement in the codes grows with distance to the station. WRONG IF the disagreement is flat with distance: E-17's mechanism (weather error grows away from stations) would then have no support in the codes.

How far the reanalysis we use stands from operational CFFDRS input, and whether station distance is a real stratifier for E-17.

*Note:* P3 (docs/results/p3_dated): REFUTED. rho(|ERA5 - station|, distance) -0.03 to +0.05, all CIs span 0 (195 patches, median 56 km). AUC station vs ERA5: FFMC 0.81 vs 0.80, BUI 0.87 vs 0.88, DC 0.78 vs 0.83. P7: under R2, station weather -0.017 [-0.034, -0.001] within and +0.024 [-0.027, +0.076] between, relative to ERA5.

*Blocked on:* 2019 station file now held; needs the frozen test set (P10)

*CFFDRS gap:* G3 station density

**E-55 — Operational FWI grid vs the reconstruction**

*Hypothesis:* The FWI grid CWFIS issued for D-1 ranks fire above non-fire development patches as well as our ERA5-Land FWI does: the two between-patch AUCs are within 0.03 of each other, and the two FWI values agree across patches (Spearman rho >= 0.8). WRONG IF they differ by more than 0.03 with a CI excluding 0, or rho < 0.8: then R0 does not stand in for operational CFFDRS, and every imagery delta measured against R0 or R2 is measured against a different baseline from the one operations use.

Whether R0 can stand in for operational CFFDRS when imagery deltas are reported, and how far it is from it where it cannot.

*Note:* Only the FWI itself is archived before 2024: FFMC, DMC, DC, ISI, BUI and every FBP output start 2024-01-01 (GetCapabilities, 2026-10-26). All CWFIS grids are 2 km, so the comparison is between patches only: an operational map cannot rank pixels inside a 5 km patch. Whether the archive is as issued or reprocessed is not documented (Q30).

*Blocked on:* the fetch (Fire_Risk_Model/scripts/python/fetch_cwfis_grids.py) is not written. The grid covers 188 of 194 development patches (all 83 fires; the 6 confusers dated 2016-2017 precede it)

**E-56 — Operational FBP outputs on a 2024-2025 cohort**

*Hypothesis:* On fires that started in 2024-2025, the HFI CWFIS issued for D-1 ranks fire above non-fire patches within 0.03 of our R0 HFI for the same patches and day (between-patch AUC), and the two agree across patches (Spearman rho >= 0.7). WRONG IF they differ by more than 0.03 with a CI excluding 0: the operational inputs our reconstruction replaces (interpolated station weather, the CWFIS fuel grid, its FMC, green-up and curing) then carry, or lose, skill R0 does not.

The first comparison against what operational FBP actually reported. The cohort is also an out-of-time test for every model trained on 2019-2023.

*Note:* Registered with E-55, before any grid value was scored.

*Blocked on:* NBAC 2024-2025 are held; patches, pre-fire composites, dated weather and the v2 sidecars for a 2024-2025 cohort are not built

### Band selection

**E-1 — VNIR band selection**

*Hypothesis:* Red-edge earns a slot: the best six include at least one of B5/B6/B7 and exclude both 60 m atmospheric bands (B1, B9). WRONG IF an atmospheric band survives into the best six, which would say the ranking is reading haze rather than vegetation.

Names the six bands for the Mantis MS mode. The one complete answer the packed data can give today, and it settles one of the three sensor modes outright.

*Note:* First NBAC search done (job 6844532, 6/6 folds; docs/results/band_search_nbac). Open: at k=6 B5 is in 6/6 folds and B7 in 5/6, but B9 is in 4/6, and the k=6 set scores no better than k=1 (0.758 vs 0.766). Replay pending: sweep_replay.sh refits the chosen sets with artefacts under the full-tile evaluation, seeds 0 and 1.

**E-2 — All-11 greedy**

*Hypothesis:* B11 enters by k=3, because the NIR/SWIR contrast is the strongest single moisture signal available. WRONG IF it has not entered by k=7, which would be weak evidence against the SWIR chain -- weak, because one band cannot stand in for four.

If greedy reaches for B11 early, the SWIR chain earns a slot on fire-outcome evidence. If it never does, that is weak evidence against, not strong -- one SWIR band cannot test a four-band mode.

*Note:* First NBAC search done (job 6844530; docs/results/band_search_nbac). B11 entry rung per fold: never, 3, 2, 5, 2, 7 -- open. Under the old dNBR label it entered at k=1 in two folds. Replay pending: sweep_replay.sh refits the chosen sets with artefacts under the full-tile evaluation, seeds 0 and 1.

**E-3 — Forced-SWIR delta**

*Hypothesis:* Positive but small: under +0.02 auc_px. One band in the window is a poor proxy for a four-band mode, so a large gain would be surprising and a null is not disqualifying.

The marginal value of one SWIR band at equal band count. A lower bound on the SWIR chain: we hold 1 band in the window, the sensor would carry 4.

*Note:* Read through report_arms.py's MATCHED-k section: vnir_swir and vnir are paired rung by rung, not at their deepest rungs, which would set k=7 against k=6. First NBAC search done (job 6844531; docs/results/band_search_nbac): within noise at every k from 2 to 6 (2-SE about +-0.02), so the +0.02 bound is not yet tested. SWIR's gain over vnir fell after the dNBR -> NBAC relabel in 11 of 12 matched-k cells. Replay pending: sweep_replay.sh refits the chosen sets with artefacts under the full-tile evaluation, seeds 0 and 1.

**E-4 — SWIR-only floor**

*Hypothesis:* Clearly above chance and clearly below the VNIR set. The water features at 1200 and 1600 nm are physically present, so a learned model should find something; without the NIR anchor it cannot normalise for canopy structure or illumination. WRONG IF it matches the VNIR set, which would make the MS chain arguable.

The third sensor option -- SWIR instead of MS -- had no number. Structurally a SWIR-only set forms 0 of 12 catalogue indices and 0 ECVs, measured; this says what a LEARNED model does with it anyway, which rule 4 treats as the real question.

*Note:* A quarter of the sensor. Read strictly as a floor.

**E-5 — Leave-one-out band value**

*Hypothesis:* Every individual drop is small, because the pool is redundant. B8 and B8A in particular each look worthless while the pair is not: leave-one-out cannot see mutual substitution, and reading a small drop as 'this band does not matter' is the trap. WRONG IF any single removal costs more than about 0.02, which would mean the pool is far less redundant than the near-duplicate pairs suggest and the chosen set is already minimal.

Per-band value CONDITIONAL on the rest, which is the only kind that means anything when bands are near-duplicates. Cannot see redundancy: B8 and B8A are 23 nm apart, so each may look worthless while the pair is essential.

*Note:* In the first NBAC searches no band clears 2 SE, and in vnir fold 0 removing ANY of the six raised the score: the noise floor, not redundancy, is what the drops show so far (docs/results/band_search_nbac).

**E-6 — Selection stability**

*Hypothesis:* The top two or three bands are selected in 6/6 folds and the tail is unstable. WRONG IF even the top band swings, which would mean the ranking is fold noise and no k is reportable.

6/6 is a finding, 3/6 is a coin flip. Without it a single fold's ranking would be reported as the ranking.

*Note:* WRONG so far, at this budget: no band is chosen at k=1 in more than 1/6 vnir or all11 folds, and the median greedy margin (0.005-0.008) is a tenth of the fold SD. Whether that is the bands or the crop-based evaluation is what the replays decide (docs/results/band_search_nbac).

**E-7 — Resolution requirement**

*Hypothesis:* Graceful degradation from 20 to 40 m and a sharper fall by 80 m. WRONG IF 20 -> 40 m already costs materially, which matters more than it sounds: the Mantis MS mode is 32 m at 500 km, so our 20 m results would overstate what the sensor delivers.

How much resolution the retrieval needs -- a mission requirement. The Mantis MS mode is 32 m at 500 km and 39.7 m at 620 km, so ~40 m is the real operating point and every 20 m result in this register is optimistic. This is the information cost only; the pixel-count cost (memory, latency) is E-27's.

*Note:* 'extent' mode (shrink the tile) is refused: it shrinks the input but not the mask, and the loss raises on the first batch. As first wired it would have crashed every 40 m and 80 m run.

### Controls

**E-8 — Label independence control**

*Hypothesis:* The ranking is largely preserved. WRONG IF B11's value collapses specifically -- that would say it was reading NBR-like information shared with the perimeter delineation rather than fuel, which is exactly the circularity rule 3 exists to catch.

A band whose value collapses when the label becomes thermal was exploiting the label, not reading fuel. VNP14 keys off 4 and 11 um emission, so it cannot share information with 400-1750 nm reflectance.

*Note:* WAS MARKED RUNNABLE AND WAS VACUOUS. --label was validated, printed and recorded, and never read: LABEL=vnp14 would have trained on the packed mask and confirmed its own hypothesis. sweep_bands.py now refuses any --label that is not the pack's declared label_source.

*Blocked on:* the thermal label is BROKEN, not just unpacked: only 6 of 99 fire patches carry thermal = 1, and n_granules is null in every _thermal.json, so the VNP14 fetch never counted a granule. Refetch before packing; a control built on it would say the fires did not burn

**E-9 — Lightning cohort**

*Hypothesis:* Absolute skill drops (fewer and harder cases) but the band ranking holds. WRONG IF the ranking changes, which would say human-ignition access signals -- roads, settlement -- were driving it.

Human ignitions carry a roads-and-settlement signal that a model can read off the imagery instead of the fuel. If the ranking holds on lightning fires only, it is about fuel.

*Note:* Was listed as 'needs code'; the code exists, the data does not.

*Blocked on:* NFDB is not held -- there is no NFDB directory in Fire_Risk_Model/data. labels.is_lightning() exists but has nothing to read. Fetch NFDB, attach CAUSE per patch, then filter with sweep_bands.py --scenes's machinery

**E-10 — Negative control**

*Hypothesis:* The noise arm is within noise of 0.5, and the real-band arm clearly beats it. WRONG IF the noise arm sits clearly above 0.5: then a POSITIONAL PRIOR -- where burn tends to sit in a tile, learnable from zero padding without reading a band -- inflates every arm in this register, and must be subtracted before any of them is quoted.

Sanity and calibration at once. Near 0.5: the pipeline is sound and arms can be read at face value. Above it: the excess is the floor every arm got for free, and it is the number to subtract.

*Note:* REDESIGNED. The old control was 'a deliberately redundant band pool' with the hypothesis 'at or near chance', and those cannot both hold: every real Sentinel-2 band carries surface signal, and the YAML's four overlapping red bands cannot be built from a sensor with one red band. Its runner was 'BANDS=...', not a command. Run this set first. RESULT, noise half (job 6844515): 0.5022 +- 0.0007, above 0.5 in 6/6 folds -- a positional prior of 0.002, about 1% of any real arm's skill. neg_real was not submitted (docs/results/band_search_nbac).

**E-26 — Within-fire burn pattern**

*Hypothesis:* Imagery separates burned from unburned pixels INSIDE fire patches at least as well as it does across all patches, because inside a perimeter the outcome is fuel, terrain and firebreaks rather than whether a fire started. WRONG IF within-fire skill is clearly lower, which would say most unconditional skill comes from recognising WHICH patches burned -- between-patch discrimination, not fuel.

Conditioning on ignition removes the component a reflectance spectrum structurally cannot see. AUC ignores prevalence, so within-fire against overall reads as which task the imagery predicts better. Water and rock inside a perimeter are easy unburned pixels, so part of any within-fire skill is 'non-fuel is visible' -- fuel, but not moisture.

*Note:* REDESIGNED. As first written it asked 'burned > 100 ha, given it burned'. Patches are ~530 x 530 px, ~11,257 ha, and every one of the 99 fire patches exceeds 100 ha -- the smallest burned area is 3,017 ha -- so the cut separated nothing. Folds are now assigned BEFORE the scene filter: fold_indices deals the blocks present round-robin, so filtering first had reshuffled which ground landed in which fold.

**E-43 — Date-only control**

*Hypothesis:* Day of year and latitude alone separate fire from non-fire at about chance. WRONG IF they do not: the pseudo-date rule for negatives would then be a shortcut every arm can read.

Guards the fire-date design (A-24).

*Note:* P3 (docs/results/p3_dated): SUPPORTED. Day of year 0.55 [0.50, 0.59], sin 0.45, cos 0.45, latitude 0.53. The confound is the year (0.87), not the pseudo-dates.

*Blocked on:* the learned date-only classifier waits for P5 (training is Narval only)

**E-54 — Legacy composite leakage**

*Hypothesis:* For fires that started before 30 June, the legacy April-June composite already shows the burn: on burned pixels its NIR-SWIR1 index (B8, B11) is lower than in the pre-fire composite ending D-1, relative to the same change on the patch's unburned pixels, and the drop grows with the days between the fire's start and 30 June. Fires starting in July or later show no drop. WRONG IF the early fires show no drop: then the v1 imagery did not read the outcome, whatever its weather did.

How much the v1 band searches (E-1 to E-14) could have read the burn itself, and so which of their results survive P4.

*Note:* P4 (docs/results/p4_prefire): MIXED. As registered, early fires show the drop (-0.061 [-0.081, -0.041], 83 % negative, n=54), but late fires show it too (-0.082, n=29) and it does not grow with overlap (rho +0.05 [-0.20, +0.30]). A control added after registration -- the same pixels at the same place in the confuser year -- takes both to about 0 (early -0.005 [-0.033, +0.023], late +0.005): the drop is the seasonal change of what later burns, not the burn. At most a weak leak in the longest overlaps (41+ days: -0.029). The legacy imagery's fault is snow and season, not a visible burn.

*Blocked on:* the v1 band searches have to be re-run on the v2 pack to see what their results were worth

### Index baselines

**E-11 — Greenness vs moisture indices**

*Hypothesis:* `both` beats `greenness` by a small but fold-consistent margin, because direct water absorption at 1610 nm carries information a greenness proxy cannot; and `moisture` (2 bands) draws with `greenness` (5 bands). WRONG IF `both` does not beat `greenness`, which would say the 1610 nm moisture signal adds nothing this label can see -- a publishable null, and one that would weaken the case for the SWIR chain considerably.

THE MISSION'S CENTRAL CLAIM. FWI2025 accepts grassland curing from remote sensing and its current option is NDVI-based GREENNESS -- a proxy for dryness. Greenness tracks moisture only while they co-vary seasonally, and a conifer stand stays green as it dries. If moisture beats greenness on a burn outcome, that is a concrete, quantified recommendation to the operational system. If `both` does not beat `greenness`, the 1610 nm moisture signal adds nothing this label can see -- also publishable.

*Note:* Primary contrast is `both` vs `greenness`: a strict superset, so a positive result is unambiguous. Tests ONE moisture index at 1610 nm -- NDWI_Gao needs 1240 nm and NMDI/NDTI/NBR need SWIR2, none of which Sentinel-2 carries.

*CFFDRS gap:* FWI2025 curing input

**E-12 — Index baseline vs learned bands**

*Hypothesis:* The learned model on raw bands beats every index family, because an index is a fixed projection that discards information a model could use. WRONG IF indices match it, which would be a strong argument for shipping indices -- cheap on an FPGA and interpretable to an operational user.

If the learned model beats every index family by a wide margin, the recommendation to CFFDRS is to take BANDS rather than indices — a finding about the system's interface, not only about our sensor. The heritage baseline rule 4 asks for.

### Covariates

**E-13 — Weather representation**

*Hypothesis:* BOTH is within noise of CODES. The FWI codes already integrate the same 91 days through a recursion tuned over decades, so our 12 features are unlikely to extract much the codes have not. WRONG IF BOTH wins clearly -- then check DIMENSIONLESS, because a gain that disappears there came from absolute level, which at 45-70 N is latitude wearing a weather costume.

Does our compression of 91 days beat the FWI System's? CODES is CFFDRS as it stands and is the baseline. If BOTH beats CODES but DIMENSIONLESS does not, the gain came from absolute level, which at 45-70 N is latitude -- geography wearing a weather costume.

*Note:* No repack: the pack carries weather_arm=both, the union, so each arm is a column mask.

**E-14 — Fusion architecture**

*Hypothesis:* Both fusion variants beat rasters_only, and two_head is within noise of bottleneck. The CFFDRS-shaped separation is expected to cost little; if it costs a lot, the architecture argument has to give way to the measurement. WRONG IF rasters_only matches both, which would say the weather scalars add nothing at this label and sample size -- and would make E-13 moot.

What the CFFDRS-shaped separation of fuel and weather costs or buys against early fusion. rasters_only is the no-weather floor and is also the configuration the band ranking is read from, which ties the two together.

*Note:* two_head is submitted once, as wx_both, and report_arms.py aliases it into the fusion family; without that alias the main contrast was never produced. The second baseline, bottleneck, tests the hypothesis's other clause.

**E-15 — Imagery vs the FBP formula**

*Hypothesis:* Imagery plus the FMC scalar beats the scalar alone, substantially. The FBP equation is a function of latitude, longitude, elevation and date only -- it carries no information about the stand -- so a null here would be surprising, and would cast doubt on the imagery rather than vindicate the formula.

G1 restated into something testable: does imagery carry foliar-moisture information the FBP equation does not? It CANNOT say our spectral estimate beats theirs -- that needs an LFMC label (E-29).

*Note:* The imagery-free floor that ran (6/6 folds, auc_px 0.5396 to 0.7660) was trained and scored on the dNBR pack, so it does NOT count: both halves must be rerun on the NBAC pack. The spread is still a fair picture of fold-to-fold variance.

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

*Note:* Measured 2026-10-23: fire patches sit a median 37 km from the nearest reporting CWFIS station (IQR 23-63, max 191); terciles at 30 and 54 km. Provincial agency stations are not in the CWFIS export, so true density is higher than this says. P3 (E-52): ERA5 vs station disagreement does not grow with distance (rho about 0), so the premise is AT RISK before the imagery increment is measured.

*Blocked on:* station data now held (CWFIS fwi_obs: 2020s daily FWI with coordinates, station list); stations.py and the stratified readout are not written, and 2019 fires need the 2010s file

*CFFDRS gap:* G3 station density

**E-18 — Snow-off startup**

*Hypothesis:* Correcting the start date changes DC and DMC materially above 55 N and improves skill there, with little effect in the south. Our flat 90-day spinup starts around 1 April into frozen, snow-covered ground, so the spurious drying should scale with latitude.

Fixes our own defect first: the spinup starts ~1 April, which at 55-67 N is frozen and snow-covered, so the recursion accumulates weeks of spurious drying and the error scales with latitude. Then it tests whether a per-pixel snow-off date beats the regional rule.

*Note:* P3 (E-51): the operational start-up moves DC by +38 at >=60 N and lifts DC AUC 0.77 -> 0.91 there; ERA5 melts snow late, which is the error an S2 snow-off date could fix.

*Blocked on:* an Earth Engine NDSI reduction over the S2 collection; no new imagery. Moved to P6 with the other imagery estimators (James, 2026-10-24); the operational-rule half is E-51 (P3)

*CFFDRS gap:* G4 snow-off keyed by regional rule

**E-19 — Latitude-banded weather**

*Hypothesis:* History beats codes at high latitude specifically, and not in the south. The day-length factors are tabulated for ~46 N, so the codes should be least trustworthy where that assumption is furthest from the truth. WRONG IF the gain is uniform across bands, which would make the mechanism something other than day length.

DMC and DC day-length factors are tabulated for ~46 N while Canada spans 42-83. A pooled number cannot distinguish 'history is better' from 'history is better at high latitude', which is the actual claim -- so the test is the interaction, not either band alone.

*Note:* Bands hold 745 / 594 / 495 of the 1834 training tiles, so ~80-125 per band per validation fold -- above the 25-tile floor below which a band is skipped rather than scored.

*CFFDRS gap:* G5 day-length tabulated for ~46 N

**E-20 — Weather staleness**

*Hypothesis:* Skill decays with weather age, fastest for CODES and slowest for the dimensionless history. This is the testable half of a claim fwi.py already makes from input drift alone (DC 8.2% over three days against ISI's 89.9%). WRONG IF decay is flat, which would mean a daily uplink costs nothing and the slow-code argument is unnecessary.

Every FWI code is defined on a same-day noon observation and a daily uplink cannot supply one. The input drift is already measured (DC 8.2% over three days against ISI's 89.9%) and fwi.py reasons from it to a recommendation -- BUI best, FWI worst. Drift in a feature is not loss in a prediction, and this measures the half nobody has.

*Note:* Train once, score at each lag: one model, five scores. The leakage guard makes an earlier target date strictly safer. P3 (E-53, no learning): FFMC and ISI lose about 0.10 AUC from D-1 to D-7 with ERA5, DC and BUI about 0.03-0.04. P5: r2_lag7 trains R2 on 7-day-old codes; the train-once-score-at-each-lag design still needs a scoring mode in run_slots. P7: r2_lag7 within -0.024 [-0.039, -0.011], between -0.052 [-0.101, -0.010]: decay is not flat (PARTIAL; per-code ordering and score-at-lag not run).

*Blocked on:* lagged FWI sidecars: an ERA5 pass over data already held, then a repack

*CFFDRS gap:* G7 CFFDRS assumes same-day observations

**E-21 — Fuel-layer refresh**

*Hypothesis:* A positive slope: the advantage of a refreshed estimate grows with the staleness gap. At gap 0 our estimate should LOSE, because it is a noisy copy of its own training target -- which is why the slope and not the level is the estimator. WRONG IF the slope is flat or negative. (This clause restates the prediction's negation; it was written 2026-10-24, after P2's inventory-half result, and changes nothing it predicts.)

FBP consumes a fixed-vintage fuel grid while fuel type changes with harvest, insects, fire and regrowth. The slope is the estimator because at gap 0 our estimate is a noisy copy of its own training target and would lose on noise alone.

*Note:* P2 (docs/results/p2_r0): inventory half done under R0. Within-patch HFI AUC moves -0.005 per decade of SCANFI age [-0.015, +0.007] (patch fixed effects, 79 fire patches, ages 1-13 y). No staleness cost to recover on this sample, so the prediction is at risk before E-22 runs. Pre-fire steps only: the 2020 step already shows the 2019-2020 fires (A-25). P3, dated design: -0.009 per decade [-0.017, +0.001]; a cost of age of at most about 0.02 AUC per decade.

*Blocked on:* the refreshed-estimate half needs E-22; the 2005 SCANFI step and 2010 for half the fires are still being fetched

*CFFDRS gap:* G2 fuel-type layer is a fixed vintage

**E-22 — Ecology arm**

*Hypothesis:* The ranking from dense SCANFI labels differs from the fire-outcome ranking, and SWIR ranks higher in it. Structure and biomass retrieval leans on SWIR more than a burn outcome does, because the outcome is diluted by ignition and weather. If the two rankings agree, that is a strong convergent result for whichever bands win.

THE PRIMARY BAND RANKING. Dense per-pixel labels rather than one sparse outcome per patch, so it has orders of magnitude more signal per scene than the fire arm and measures what the bands actually retrieve rather than what correlates with ignition.

*Blocked on:* 279 patches on disk, never tiled or packed; needs a pack and a second transfer

**E-50 — Latitude-correct day length (R0)**

*Hypothesis:* Scaling the DMC day-length factors from 46 N to each patch's latitude raises DMC more at >=60 N than at <55 N (longer summer days), and raises R0's between-patch AUC of DMC and BUI more in the north. WRONG IF the DMC shift is uniform across bands. The AUC half rests on 19 northern fire patches and is read only beside the shift.

Whether the fixed 46 N day length (gap G5) costs CFFDRS skill where Canada burns most.

*Note:* cffdrs lat.adjust is NOT the variant: in cffdrs 1.9.2 it only changes the factors at or south of 30 N, so it is a no-op for every patch here. FWI2025's sunrise-to-sunset hourly DMC changes far more than day length and may not feed FBP1992. DC's monthly factor is a seasonal adjustment, not a day length, and is left. P3 (docs/results/p3_dated): SUPPORTED. DMC shift +1.4 / +3.8 / +6.4 by band; AUC moves by 0.006 or less: a calibration gap, not a skill gap, under R0.

*Blocked on:* needs the frozen test set (P10)

*CFFDRS gap:* G5 day-length tabulated for ~46 N

**E-51 — Operational start-up (R0)**

*Hypothesis:* The GLC-X-42 Appendix C-2 start-up (codes begin 3 days after ERA5-Land snow cover is gone, or after 3 days at or above 12 C at 13:00 where snow is absent) with an overwintered DC moves DC and DMC at D-1 more at >=60 N than at <55 N, compared with a flat 90-day spin-up from the default start values, and its effect on R0's between-patch AUC is larger in the north. WRONG IF the code shift does not grow with latitude. This is E-18's mechanism under the operational rule; E-18's imagery arm is P6.

How much the operational start-up matters before imagery tries to improve on it (G4).

*Note:* P3 (docs/results/p3_dated): MIXED. DC shift -19.8 / +30.1 / +38.4 by band (grows north), DC AUC 0.77 -> 0.91 at >=60 N (19 fires); DMC shift -1.3 / -2.0 / -1.4 (flat).

*Blocked on:* needs the frozen test set (P10)

*CFFDRS gap:* G4 snow-off keyed by regional rule

**E-53 — Weather staleness under R0**

*Hypothesis:* R0's between-patch AUC decays with the age of the weather (D-1, D-2, D-3, D-7), fastest for FFMC and ISI and slowest for DC and BUI. WRONG IF the fast codes do not lose more than the slow ones by D-7. This is E-20's mechanism without learning: the curve E-20's learned arms are compared with.

How stale CFFDRS's own inputs can get -- the bar for a weather-dependent onboard product (A-29 rule 2).

*Note:* P3 (docs/results/p3_dated): SUPPORTED with ERA5: D-1 -> D-7, FFMC -0.10, ISI -0.11, DC -0.03, BUI -0.04. Station series: BUI -0.11 and DMC -0.12, as fast as FFMC.

*Blocked on:* needs the frozen test set (P10)

*CFFDRS gap:* G7 CFFDRS assumes same-day observations

### Hyperspectral

**E-23 — SWIR band placement**

*Hypothesis:* The best four cluster near 1240, 1610 and 1680-1730 nm, with the fourth in the 1500s. From brief hypotheses H1 and H3: resolving a dry-matter change needs two water-sensitive bands with different water-to-dry-matter absorption ratios.

THE SWIR SPECIFICATION. Sentinel-2 has one band in that window and the mode carries four: four cannot be chosen from one. Only a contiguous source can answer it.

*Note:* Grid measured from AVIRIS-NG's own bad-band list (A-22), which puts the water-vapour gap at 1364-1408 nm -- narrower than assumed, so 1300-1359 and 1414-1500 were being excluded for no reason.

*Blocked on:* 3 of 42 pre-fire lines on disk, 0 ingested

**E-24 — 1209 vs 1240 nm**

*Hypothesis:* 1240 nm is slightly better for water sensitivity and 1209 slightly better for O2 margin, with the difference small enough that the flown WorldView-3 centre is defensible. A large difference either way is the interesting outcome.

Water sensitivity traded against O2 margin. The validator flagged the conflict; nobody has measured it.

*Blocked on:* same as E-23

**E-25 — Spectral resolution: HS vs MS**

*Hypothesis:* Diminishing returns beyond roughly 10-15 well-placed bands, so the HS mode's 96 channels buy little over a well-chosen MS set. WRONG IF the curve keeps climbing, which would make the HS mode the better instrument and change the payload decision.

What spectral RESOLUTION buys, which decides the Mantis HS mode. Cannot be faked: ten Sentinel-2 bands cannot be interpolated into ninety-six, and rule 2 forbids trying.

*Blocked on:* same as E-23

### Hardware

**E-27 — Cost per input channel**

*Hypothesis:* BRAM scales roughly linearly with input channel count, so 96 channels are infeasible on the target part and 11 are affordable. Stream BRAM is ceil(width/18) x ceil(depth/1024) and width never stops paying. WRONG IF scaling is sub-linear because the first convolution dominates, which would make a wide input cheaper than the marginal-cost argument assumes.

The MARGINAL COST denominator. The brief asks for value per marginal cost, and without this the ranking has a numerator only. Stream BRAM is ceil(width/18) x ceil(depth/1024), so width never stops paying.

**E-28 — Co-registration tolerance**

*Hypothesis:* Negligible cost below a quarter pixel, material by one pixel. WRONG IF a half-pixel shift already costs materially, which would tighten the dichroic and focal-plane alignment budget; or if two pixels cost little, which would retire the registration risk.

A number for the requirements table. The dichroic makes misregistration small, not absent. This is the deployment question -- a model built on co-registered imagery meeting a misregistered instrument.

*Note:* REDESIGNED. Shifting during training too would understate the cost, because a convolution can learn to compensate a fixed offset. Rigid translation only -- not rotation, scale or pushbroom keystone -- so the tolerance is NECESSARY, not sufficient. The original hypothesis also placed the loss at snow/forest boundaries; this reports the scene-average cost and cannot localise it, so that clause was dropped rather than left untestable.

**E-48 — Hardware decision**

*Hypothesis:* The chosen model fits a Q8 at <= 80 % of every resource. WRONG IF only the Q9 fits, or none does.

The onboard hardware.

*Blocked on:* E-47 (budgets set in A-29: <= 91 s per scene, then lowest power)

### Out of reach

**E-29 — T1 live foliar moisture**

*Hypothesis:* From Jolly et al. (2014), the brief's lead hypothesis H1: dry matter, not water content, drives seasonal conifer LFMC, so water-only bands will return EWT rather than LFMC and a two-band water contrast is required. Untestable here until an LFMC label exists.

Would make G1's STRONG claim testable -- that a spectral estimate beats the FBP equation -- and unblock E-16. Globe-LFMC 2.0 is fetched and measured: 2,884 usable records at 83 sites, no Canadian ones, and C-2 black spruce has 51. It carries no spectra, so each record must be paired with a Sentinel-2 acquisition.

*Blocked on:* Globe-LFMC held; the S2 pairing pipeline is unwritten (Phase 6a), and PROSAIL for simulated labels is not installed (Phase 1)

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
| **E-1** | VNIR band selection | `sweep_arms.sh ARMS=vnir` | 49 fits/task x 6 tasks; est 2:05; --time=4:30:00 --mem=16G --cpus-per-task=12 --gpus=a100:1 |
| **E-2** | All-11 greedy | `sweep_arms.sh ARMS=all11` | 60 fits/task x 6 tasks; est 2:32; --time=5:30:00 --mem=16G --cpus-per-task=12 --gpus=a100:1 |
| **E-3** | Forced-SWIR delta | `sweep_arms.sh ARMS=vnir_swir` | 51 fits/task x 6 tasks; est 2:10; --time=4:30:00 --mem=16G --cpus-per-task=12 --gpus=a100:1 |
| **E-4** | SWIR-only floor | `sweep_arms.sh ARMS=swir_only` | 1 fit/task x 6 tasks; est 0:05; --time=0:30:00 --mem=16G --cpus-per-task=12 --gpus=a100:1 |
| **E-5** | Leave-one-out band value | `sweep_bands.py --leave-one-out (rides in E-1..E-4)` | no separate job: rides inside E-1 to E-3 |
| **E-6** | Selection stability | `pool_bands.py (after E-1..E-4)` | no job: pool_bands.py, minutes, on a login node |
| **E-7** | Resolution requirement | `sweep_axes.sh SETS=gsd` | 1 fit/task x 18 tasks; est 0:05; --time=0:30:00 --mem=16G --cpus-per-task=12 --gpus=a100:1 |
| **E-10** | Negative control | `sweep_axes.sh SETS=neg` | 1 fit/task x 12 tasks; est 0:05; --time=0:30:00 --mem=16G --cpus-per-task=12 --gpus=a100:1 |
| **E-11** | Greenness vs moisture indices | `sweep_indices.sh` | 1 fit/task x 24 tasks; est 0:05; --time=0:30:00 --mem=16G --cpus-per-task=12 --gpus=a100:1 |
| **E-12** | Index baseline vs learned bands | `sweep_indices.sh ARMS=raw,both` | shares E-11's runs |
| **E-13** | Weather representation | `sweep_covariates.sh SETS=weather` | 1 fit/task x 24 tasks; est 0:05; --time=0:30:00 --mem=16G --cpus-per-task=12 --gpus=a100:1 |
| **E-14** | Fusion architecture | `sweep_covariates.sh SETS=fusion` | 1 fit/task x 12 tasks (+ wx_both from E-13); est 0:05; --time=0:30:00 --mem=16G --cpus-per-task=12 --gpus=a100:1 |
| **E-15** | Imagery vs the FBP formula | `sweep_covariates.sh SETS=g1` | 1 fit/task x 12 tasks; est 0:05; --time=0:30:00 --mem=16G --cpus-per-task=12 --gpus=a100:1 |
| **E-19** | Latitude-banded weather | `sweep_covariates.sh SETS=weather` | shares E-13's runs; latitude scoring adds seconds |
| **E-21** | Fuel-layer refresh | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` | -- |
| **E-26** | Within-fire burn pattern | `sweep_axes.sh SETS=cond` | 1 fit/task x 12 tasks; est 0:05; --time=0:30:00 --mem=16G --cpus-per-task=12 --gpus=a100:1 |
| **E-27** | Cost per input channel | `sweep_architecture.py --widths` | CPU only: model conversion, no Narval GPU allocation |
| **E-28** | Co-registration tolerance | `sweep_axes.sh SETS=shift` | 1 fit + 5 evaluations/task x 6 tasks; est 0:06; --time=0:30:00 --mem=16G --cpus-per-task=12 --gpus=a100:1 |
| **E-32** | CFFDRS as is (R0) | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` | -- |
| **E-33** | Fuel inventory comparison | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` | -- |
| **E-34** | Learned CFFDRS (R1/R2) | `Fire_Risk_FW/scripts/shell/sweep_slots.sh CONFIGS=r0_scanfi,r0_cwfis,r1,r2,r2_cwfis` | --time=0:30:00 --gpus=a100:1 --cpus-per-task=12 --mem=16G per task of 3 fits (measured on slots_v2: 3.4 min median, 4.1 min max per fit; A-35) |
| **E-36** | Percent-conifer slot | `Fire_Risk_FW/scripts/shell/sweep_slots.sh CONFIGS=r3_pc,r3_pc_shuffled` | --time=0:30:00 --gpus=a100:1 --cpus-per-task=12 --mem=16G per task of 3 fits (measured on slots_v2: 3.4 min median, 4.1 min max per fit; A-35) |
| **E-37** | Crown-base-height slot | `Fire_Risk_FW/scripts/shell/sweep_slots.sh CONFIGS=r3_cbh,r3_cbh_shuffled` | --time=0:30:00 --gpus=a100:1 --cpus-per-task=12 --mem=16G per task of 3 fits (measured on slots_v2: 3.4 min median, 4.1 min max per fit; A-35) |
| **E-38** | Curing slot | `Fire_Risk_FW/scripts/shell/sweep_slots.sh CONFIGS=r3_curing,r3_curing_shuffled` | --time=0:30:00 --gpus=a100:1 --cpus-per-task=12 --mem=16G per task of 3 fits (measured on slots_v2: 3.4 min median, 4.1 min max per fit; A-35) |
| **E-43** | Date-only control | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` | -- |
| **E-49** | Dating the weather (R0) | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` | -- |
| **E-50** | Latitude-correct day length (R0) | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` | -- |
| **E-51** | Operational start-up (R0) | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` | -- |
| **E-52** | Weather source: station vs ERA5 (R0) | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` | -- |
| **E-53** | Weather staleness under R0 | `Fire_Risk_Model/scripts/python/eval_cffdrs_reference.py` | -- |
| **E-54** | Legacy composite leakage | `Fire_Risk_Model/scripts/python/build_prefire.py` | -- |

All of these read the **`stage2_fire_11band_nbac`** pack. It replaces the one already in `~/scratch`, which the sweep now refuses.

### How the resources were derived

From the only completed runs (the imagery-free G1 floor, six folds): every 35-epoch fit took **122 s**, identical across folds, with the GPU at **0.2-0.6% utilisation** and 0.6 GB of GPU memory; venv build and staging took under 45 s; sacct MaxRSS 1.04 GB. Identical times on a 337-parameter model is an input-bound signature -- the cost is h5py decompressing tiles in the DataLoader, not the GPU.

- **`--time`** is 2 x (fits x 2.5 min) + 2 min, rounded up to 30 min. 2.5 min is the measured 122 s plus a margin, because no CNN fit has completed yet. The old request was 11:00:00 for every job, including two-minute ones; jobs of 3 h or less can start on far more of Narval.
- **`--cpus-per-task=12`**: one A100's share of a 48-core, 4-GPU node, so free in billing -- and since the job is CPU-bound, the workers are where speed comes from. Ten DataLoader workers, kept alive across epochs.
- **`--mem=16G`**: 1.04 GB measured at load plus ten workers' buffers.
- **Fit counts are simulated** by running each search through the real greedy and leave-one-out code with a counting scorer. Memoisation made the old formula wrong: it said 63 fits for `vnir_swir`, which is 51.

The whole programme is about **50 GPU-hours**. Recalibrate once real CNN fits exist: every fit now appends its wall time to `fits.jsonl`, and `narval_resources.py --runs` re-derives every request from them. If a fit takes under ~1.4 min, the band arms fit the 3 h bin.

Two standing caveats on every number they produce. The 35-epoch budget is a **ranking** budget, so the output is an order and not an accuracy until the top sets are re-run at full budget. And the fold spread is large -- the one arm that has completed spanned 0.5396 to 0.7660 across six folds from a single model on a single input -- so results must be read as **paired** per-fold contrasts via `report_arms.py`, never as two means compared by eye.

