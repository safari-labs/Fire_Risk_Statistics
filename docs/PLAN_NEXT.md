# Plan: what's next now the November runs have landed (2026-11-04, updated 2026-11-05)

**Status:** a plan for approval. Nothing in sections 2-4 runs before James says so. Section 1 records what arrived today and how it was treated.

## 1. What arrived, and what it decided

| Run on Nibi | Package | Verdicts | What it decides |
|---|---|---|---|
| `eco_v3`, all 15 tasks, maps in three input modes | [p6a_ecology_v3](results/p6a_ecology_v3/README.md), phase P6a-v3 | E-22 SUPPORTED, E-59 MIXED, E-62 (Sentinel-2 half) REFUTED | SWIR leads closure and the combined path; red edge leads percent conifer, but dropping it costs under 1 % at k = 6. Deciduous (recall 0.38) and mixedwood (0.30) are mostly called conifer. |
| `lfmc_v1`, 3 seeds | [p6f_lfmc](results/p6f_lfmc/README.md) (new packager), phase P6f | E-64 REFUTED, E-29 SUPPORTED (weakly) | On conifers, neither spectral route beats FBP's equation: simulation GP +26 RMSE, empirical +0.6 (tie). The simulation retrieval is biased +31. B12 helps it, but that retrieval is worse than a constant. |
| `hs_v4`, `hs_lidar_v2` (copied again this morning) | `p6a_hs_v4`, `p6a_external_labels_v2` | unchanged | Rebuilt both: tables and summaries identical. |

The four "truncated" map files seen mid-morning were copies still in progress; all 15 are complete now.

**Still out:** E-35, the fuel-type slot, replace form. eco_v3 is done, so it can launch (on Nibi, in `Fire_Risk_FW` after `git pull`):

```bash
RUN_ID=20261102-1959 SUBMIT=1 bash scripts/shell/sweep_eco_fire.sh
# when it ends: read ~/scratch/eco_fire_v1/agreement.json (how often deciduous and mixedwood become conifer)
SUBMIT=1 EXP_NAME=slots_e35 ECO_DATA=$HOME/scratch/eco_fire_v1   CONFIGS=r2,r3_fuel_replace,r3_fuel_replace_shuffled,r3_fuel_pc_replace,r3_fuel_pc_replace_shuffled,r3_pc_replace,r3_pc_replace_shuffled   bash scripts/shell/sweep_slots.sh
```

105 fits in 6 tasks of 18. Then the P7e package. The prediction to watch: the eco fuel's conifer bias should raise ignition and spread where the inventory says aspen.

## 2. Stage C next: E-45 (P9b)

**Built and tested (2026-11-04):**
- `Fire_Risk_Model/src/data/pack_ignition.py` and `scripts/python/pack_ignition_v1.py` build the point pack: 7,194 tiles, 1,298 sets, development only.
- `Fire_Risk_FW/scripts/run_ignition.py` and `scripts/shell/sweep_ignition.sh` hold the runner: 8 configurations x 5 folds x 3 seeds, 100 fits.
- R0 through the pack reproduces E-44's evaluator to 5e-5. The tests pass.
- 37 points have no clear pixel in their 5 x 5 centre. Every rung leaves them out, and with them any set whose start they are.
- Tiles read at 242/s on one core, so a fit should take about 12-15 min on a GPU: 17 tasks of 6 fits, 3 h each.
- The design is in A-48.

**Decided (James, 2026-11-05; A-48).** Conditional logistic loss; R2 starts as logit P(sustained flaming); the best epoch is picked on the 15 % inner split of the training groups (rule 5; James asked about the test fold, then confirmed the inner split, A-48); noise-free for now. The three predictions are registered in E-45. The pack was rebuilt at Model `a5d6f49` and bundled as `ignition_v1_pack`.

**Then:**
1. Running on Nibi. First 36 of 100 fits packaged ([p9b_ignition_rungs](results/p9b_ignition_rungs/README.md)): R1 beats R0 by +0.052, so prediction 2 fails provisionally; the imagery rungs are not in yet. Rerun `make_results_package.py --phase P9b` when the sweep completes.
2. Write the P9b packager.
   - Paired deltas against r2 and r0, by fold x seed, with a bootstrap over 1-degree blocks.
   - The qualitative view: the E-44 matched sets with the R4 map and the shuffled twin's map.
3. Fuel slot, replace form. Run the final eco_v3 model on the ignition chips (`predict_eco_fire.py` on the point pack), then add `r3_fuel_replace` and its twin to the sweep.
4. Closure stays blocked on Q26 (in-stand moisture coefficients).

## 3. LFMC (T1): fixing the forward model (A-51, E-65)

**Decided (James, 2026-11-05): option a, try to fix the forward model.**

1. **Reference check: done** ([p6f_reference](results/p6f_reference/README.md)). PROSPECT-D + 4SAIL match Féret's R packages to 5e-15 with the same leaf-angle classes. The code is not the cause of the +31 bias.
2. **Narrowed priors: built, on the cluster next** (E-65). Inside each outer site fold, the simulation pool is cut to the training records' LFMC range by species and season, with `prior_mean_fold` as the control to beat. Same `lfmc_v1` bundle, no transfer:
   ```bash
   EXP_NAME=lfmc_v2 SEEDS="0 1 2" SUBMIT=1 bash scripts/shell/sweep_lfmc.sh
   ```
3. **Moss and lichen backgrounds** and 4. **a discontinuous-canopy model**: decided after E-65. If the GP cannot beat `prior_mean_fold`, the spectra carry no LFMC beyond the prior under 4SAIL, and these are the remaining physics to try.

## 4. Then the synthesis (P11, P12, P10)

**Decided 2026-11-05 (A-49).** Every P12 decision is an option table with pros and cons, and James chooses. The four structure heads weigh equally. Sentinel-2 decides VNIR and whether SWIR is in; AVIRIS-NG decides the SWIR centres. The weighting check (`results/p12_weights`) shows the choice barely depends on the weights. Stability clause (Q38): option 1, a consensus set by region, re-scored.

1. **Value map (P11).** Add Stage C's row (E-44 floor, E-45 deltas), the Stage A fuel-slot row (E-35) and E-20's weather-age row. Regenerate `figures/value_map.png`.
2. **E-46, band and index options (P12).** The combiner is built and the consensus sets are counted ([p12_bands](results/p12_bands/README.md)). Sentinel-2 consensus is stable at k = 1 and k = 5; no AVIRIS-NG SWIR consensus is stable. Next, on Nibi, the commands in [rescore_commands.md](results/p12_bands/rescore_commands.md): 8 `sweep_eco_arch.sh` runs and one `sweep_hs.sh` references run. Then `make_band_options.py --eco-rescore ... --hs-rescore ...` writes the option table with every fixed set's own paired score.
3. **E-47, architecture options.** The hypothesis was restated 2026-11-05, before any result: the onboard model is the ecology estimator. The ladder sweep is built:
   ```bash
   BANDS=<E-46 set> SUBMIT=1 bash scripts/shell/sweep_eco_arch.sh     # 12 sizes x 15 tasks
   ```
   It can run now at a candidate set as a provisional reading. The rungs pair with eco_v3 by fold and seed.
4. **E-20, weather age: done** ([p7d_weather_age](results/p7d_weather_age/README.md), PARTIAL). Between patches R2 loses about 0.05 AUC from 3 days; training on stale weather does not help. Weather-dependent products stay on the ground (A-41). The original plan text follows for the record.
   (Was: E-20, weather age, rebuilt pack, A-50.) After the commit, rebuild and bundle `stage2_fire_cffdrs_v2_lags`, transfer it, then:
   ```bash
   SUBMIT=1 EXP_NAME=lags_v1 CONFIGS=r0_scanfi,r2,r2_age7 SCORE_LAGS=1,2,3,7      SCRATCH_DATA=$HOME/scratch/stage2_fire_cffdrs_v2_lags bash scripts/shell/sweep_slots.sh
   ```
5. **E-48, hardware options.** The conversion check is done (2026-11-05, [p12_convert](results/p12_convert/README.md)): the four-head `TinyEcologyUNet` goes through hls4ml, the DPU and FINN at every E-47 rung. What is left is the option table at E-47's chosen size, on the boards each flow can reach, with power. The latency budget is at most 43 s per scene (A-29); if a SWIR camera joins, the budget is re-derived.
6. **P10, the final test, once.** It reads every frozen set in one recorded run: the fire test blocks, the 2025 cohort, the AVIRIS test lines, the LFMC test sites, and the ignition test blocks and 2025.

## 5. Smaller items owed

- **The PROSPECT/4SAIL reference check** (A-47) is still owed before P6f's simulation arm is read as Phase 1 "done".
- **Stage B.** E-42 needs imagery chips for the CFSDS fire-days off our patches (805 of 4,925 on a patch). Not scheduled; it would need a plan of its own.
