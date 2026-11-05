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

**Decisions for James before the sweep:**
1. **The A-48 choices.**
   - The loss is conditional logistic over each matched set (alternative: BCE).
   - R2 starts as logit P(sustained flaming).
   - The best epoch is picked on a 15 % inner split of the training groups.
2. **Sensor noise (rule 6).** Neither this runner nor the Stage A slot runner applies the noise model.
   - Option a: run E-45 noise-free now, as Stage A was, and add noise when bands are searched.
   - Option b: add the placeholder noise model (A-37) to `make_step` in both runners first. That costs about a day and reruns nothing already done.
   - Recommended: a. E-45's first question is whether imagery carries any ignition signal at all.
3. **Predictions to register before any fit** (proposed):
   - r4 beats r4_shuffled, with the paired CI above 0.
   - r2 vs r0 is within +-0.01 (learning on fuel and slots barely moves a fuel-only floor).
   - r2_leaf_ablated vs r2 is within +-0.005. Leaf state moves P only for grass. The SCANFI tree puts no point on grass; CWFIS puts 275 of 7,194 (3.8 %) there. So under SCANFI fuel, green-up can reach the score only through the residual.

**Then:**
1. Commit the pack and runner code in Model and FW, and rebuild the pack (about 10 min). The local pack records Model `0c3aeb0`, which predates `pack_ignition.py`. Then bundle `ignition_v1_pack` as tar.gz + sha256 and send it to scratch.
2. `SUBMIT=1 bash scripts/shell/sweep_ignition.sh`.
3. Write the P9b packager.
   - Paired deltas against r2 and r0, by fold x seed, with a bootstrap over 1-degree blocks.
   - The qualitative view: the E-44 matched sets with the R4 map and the shuffled twin's map.
4. Fuel slot, replace form. Run the final eco_v3 model on the ignition chips (`predict_eco_fire.py` on the point pack), then add `r3_fuel_replace` and its twin to the sweep.
5. Closure stays blocked on Q26 (in-stand moisture coefficients).

## 3. A decision on LFMC (T1), after E-64

E-64 says the simulation route, as built, is not a usable LFMC retrieval on Sentinel-2: biased +31, worse than a constant. Two ways on:

- **a. Fix the forward model (a P6f-v2 plan).**
  1. The PROSPECT/4SAIL reference check owed under A-47.
  2. Priors narrowed by species and season to the measured range (80-149 % on conifers, not 60-250 %).
  3. Moss and lichen backgrounds.
  4. Then a discontinuous-canopy model for conifers.
  
  Steps 1-2 are cheap and test whether the bias is the priors. Step 4 is weeks.
- **b. Park T1's simulation route until James's own LFMC and dry-matter sampling exists.** Report P6f as is. In the band decision, T1 then rests on E-29's weak B12 line.

Recommended: a, steps 1-2 only, then decide on 3-4. This is James's call, since it reopens brief Phase 1.

## 4. Then the synthesis (P11, P12, P10)

**Decided 2026-11-05 (A-49).** Every P12 decision is an option table with pros and cons, and James chooses. The four structure heads weigh equally. Sentinel-2 decides VNIR and whether SWIR is in; AVIRIS-NG decides the SWIR centres. The weighting check (`results/p12_weights`) shows the choice barely depends on the weights. Stability clause (Q38): option 1, a consensus set by region, re-scored.

1. **Value map (P11).** Add Stage C's row (E-44 floor, E-45 deltas), the Stage A fuel-slot row (E-35) and E-20's weather-age row. Regenerate `figures/value_map.png`.
2. **E-46, band and index options (P12).**
   - Build the combiner. It reads the eco_v3 and hs_v4 searches, builds candidate sets per k (each search's best and the consensus set by region, Q38), and writes the option table with scores, paired margins, band counts, cost, pros and cons.
   - Each consensus set is re-scored on the cluster: `BANDS=<set> SIZES=8x2 SUBMIT=1 bash scripts/shell/sweep_eco_arch.sh`, about 15 short fits per set.
   - Red edge: E-62 is refuted on both halves, but every best set carries a 700-760 nm band; it stays with its margin stated.
3. **E-47, architecture options.** The hypothesis was restated 2026-11-05, before any result: the onboard model is the ecology estimator. The ladder sweep is built:
   ```bash
   BANDS=<E-46 set> SUBMIT=1 bash scripts/shell/sweep_eco_arch.sh     # 12 sizes x 15 tasks
   ```
   It can run now at a candidate set as a provisional reading. The rungs pair with eco_v3 by fold and seed.
4. **E-20, weather age** (rebuilt pack, A-50). After the commit, rebuild and bundle `stage2_fire_cffdrs_v2_lags`, transfer it, then:
   ```bash
   SUBMIT=1 EXP_NAME=lags_v1 CONFIGS=r0_scanfi,r2,r2_age7 SCORE_LAGS=1,2,3,7      SCRATCH_DATA=$HOME/scratch/stage2_fire_cffdrs_v2_lags bash scripts/shell/sweep_slots.sh
   ```
5. **E-48, hardware options.** First check that `TinyEcologyUNet` (four heads) converts through the existing flows. It mirrors TinyFireUNet's structure, so `sweep_architecture.py`'s BRAM law should carry over, but that is untested. The latency budget is at most 43 s per scene (A-29); if a SWIR camera joins, the budget is re-derived.
6. **P10, the final test, once.** It reads every frozen set in one recorded run: the fire test blocks, the 2025 cohort, the AVIRIS test lines, the LFMC test sites, and the ignition test blocks and 2025.

## 5. Smaller items owed

- **The PROSPECT/4SAIL reference check** (A-47) is still owed before P6f's simulation arm is read as Phase 1 "done".
- **Stage B.** E-42 needs imagery chips for the CFSDS fire-days off our patches (805 of 4,925 on a patch). Not scheduled; it would need a plan of its own.
