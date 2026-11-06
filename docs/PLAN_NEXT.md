# Plan: what's next now the November runs have landed (2026-11-04, updated 2026-11-05)

**Status:** a plan for approval. Nothing in sections 2-4 runs before James says so. Section 1 records what arrived today and how it was treated.

## 1. What arrived, and what it decided

| Run on Nibi | Package | Verdicts | What it decides |
|---|---|---|---|
| `eco_v3`, all 15 tasks, maps in three input modes | [P6/p6a_ecology_v3](results/P6/p6a_ecology_v3/README.md), phase P6a-v3 | E-22 SUPPORTED, E-59 MIXED, E-62 (Sentinel-2 half) REFUTED | SWIR leads closure and the combined path; red edge leads percent conifer, but dropping it costs under 1 % at k = 6. Deciduous (recall 0.38) and mixedwood (0.30) are mostly called conifer. |
| `lfmc_v1`, 3 seeds | [P6/p6f_lfmc](results/P6/p6f_lfmc/README.md) (new packager), phase P6f | E-64 REFUTED, E-29 SUPPORTED (weakly) | On conifers, neither spectral route beats FBP's equation: simulation GP +26 RMSE, empirical +0.6 (tie). The simulation retrieval is biased +31. B12 helps it, but that retrieval is worse than a constant. |
| `hs_v4`, `hs_lidar_v2` (copied again this morning) | `P6/p6a_hs_v4`, `P6/p6a_external_labels_v2` | unchanged | Rebuilt both: tables and summaries identical. |

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
1. Running on Nibi. First 36 of 100 fits packaged ([P9/p9b_ignition_rungs](results/P9/p9b_ignition_rungs/README.md)): R1 beats R0 by +0.052, so prediction 2 fails provisionally; the imagery rungs are not in yet. Rerun `make_results_package.py --phase P9b` when the sweep completes.
2. Write the P9b packager.
   - Paired deltas against r2 and r0, by fold x seed, with a bootstrap over 1-degree blocks.
   - The qualitative view: the E-44 matched sets with the R4 map and the shuffled twin's map.
3. Fuel slot, replace form. Run the final eco_v3 model on the ignition chips (`predict_eco_fire.py` on the point pack), then add `r3_fuel_replace` and its twin to the sweep.
4. Closure stays blocked on Q26 (in-stand moisture coefficients).

## 3. LFMC (T1): fixing the forward model (A-51, E-65)

**Decided (James, 2026-11-05): option a, try to fix the forward model.**

1. **Reference check: done** ([P6/p6f_reference](results/P6/p6f_reference/README.md)). PROSPECT-D + 4SAIL match Féret's R packages to 5e-15 with the same leaf-angle classes. The code is not the cause of the +31 bias.
2. **Narrowed priors: built, on the cluster next** (E-65). Inside each outer site fold, the simulation pool is cut to the training records' LFMC range by species and season, with `prior_mean_fold` as the control to beat. Same `lfmc_v1` bundle, no transfer:
   ```bash
   EXP_NAME=lfmc_v2 SEEDS="0 1 2" SUBMIT=1 bash scripts/shell/sweep_lfmc.sh
   ```
3. **Moss and lichen backgrounds** and 4. **a discontinuous-canopy model**: decided after E-65. If the GP cannot beat `prior_mean_fold`, the spectra carry no LFMC beyond the prior under 4SAIL, and these are the remaining physics to try.

## 4. Then the synthesis (P11, P12, P10)

**Decided 2026-11-05 (A-49).** Every P12 decision is an option table with pros and cons, and James chooses. The four structure heads weigh equally. Sentinel-2 decides VNIR and whether SWIR is in; AVIRIS-NG decides the SWIR centres. The weighting check (`results/P12/p12_weights`) shows the choice barely depends on the weights. Stability clause (Q38): option 1, a consensus set by region, re-scored.

1. **Value map (P11).** Add Stage C's row (E-44 floor, E-45 deltas), the Stage A fuel-slot row (E-35) and E-20's weather-age row. Regenerate `figures/value_map.png`.
2. **E-46, band and index options (P12).** The combiner is built and the consensus sets are counted ([P12/p12_bands](results/P12/p12_bands/README.md)). Sentinel-2 consensus is stable at k = 1 and k = 5; no AVIRIS-NG SWIR consensus is stable. Next, on Nibi, the commands in [rescore_commands.md](results/P12/p12_bands/rescore_commands.md): 8 `sweep_eco_arch.sh` runs and one `sweep_hs.sh` references run. Then `make_band_options.py --eco-rescore ... --hs-rescore ...` writes the option table with every fixed set's own paired score.
3. **E-47, architecture options.** The hypothesis was restated 2026-11-05, before any result: the onboard model is the ecology estimator. The ladder sweep is built:
   ```bash
   BANDS=<E-46 set> SUBMIT=1 bash scripts/shell/sweep_eco_arch.sh     # 12 sizes x 15 tasks
   ```
   It can run now at a candidate set as a provisional reading. The rungs pair with eco_v3 by fold and seed.
4. **E-20, weather age: done** ([P7/p7d_weather_age](results/P7/p7d_weather_age/README.md), PARTIAL). Between patches R2 loses about 0.05 AUC from 3 days; training on stale weather does not help. Weather-dependent products stay on the ground (A-41). The original plan text follows for the record.
   (Was: E-20, weather age, rebuilt pack, A-50.) After the commit, rebuild and bundle `stage2_fire_cffdrs_v2_lags`, transfer it, then:
   ```bash
   SUBMIT=1 EXP_NAME=lags_v1 CONFIGS=r0_scanfi,r2,r2_age7 SCORE_LAGS=1,2,3,7      SCRATCH_DATA=$HOME/scratch/stage2_fire_cffdrs_v2_lags bash scripts/shell/sweep_slots.sh
   ```
5. **E-48, hardware options.** The conversion check is done (2026-11-05, [P12/p12_convert](results/P12/p12_convert/README.md)): the four-head `TinyEcologyUNet` goes through hls4ml, the DPU and FINN at every E-47 rung. What is left is the option table at E-47's chosen size, on the boards each flow can reach, with power. The latency budget is at most 43 s per scene (A-29); if a SWIR camera joins, the budget is re-derived.
6. **P10, the final test, once.** It reads every frozen set in one recorded run: the fire test blocks, the 2025 cohort, the AVIRIS test lines, the LFMC test sites, and the ignition test blocks and 2025.

## 5. Smaller items owed

- **The PROSPECT/4SAIL reference check** (A-47) is still owed before P6f's simulation arm is read as Phase 1 "done".
- **Stage B.** E-42 needs imagery chips for the CFSDS fire-days off our patches (805 of 4,925 on a patch). Not scheduled; it would need a plan of its own.

## 6. Sensor comparison: what each Dragonfly Mantis mode would offer (E-66)

**Approved (James, 2026-11-06)** without Chameleon and Caiman; the standard MS block is scored as published (Q39). Built, and ready to launch on Narval (command at the end of this section).

**Question (James, 2026-11-06).** For each Dragonfly sensor in the inventory, what retrieval performance would it offer, alone and in combination? The vendor data is in A-52 and `config/vendors/dragonfly.yaml`.

**Approach.** Score every sensor's real band set on AVIRIS-NG, the only data here that covers 400-2500 nm at 5 nm (rule 2). The data is the `aviris_v4` pack with SCANFI labels: percent conifer, closure, height and fuel family. The folds, seeds and noise model are hs_v4's, so every row pairs with hs_v4 and with the other rows, fold by fold.
- **Fixed sets** go through the `references` arm.
- **Sets the vendor lets us choose** are searched, nested (rule 1):
  - the 4 SWIR filters, picked from DFA's catalogue;
  - the in-orbit HS selection, picked from the 470-900 nm channels.

| Row | Sensor | Bands |
|---|---|---|
| 1 | Snapshot RGB (Gecko, Mantis, Chameleon, Caiman) | DFA's blue, green and red (480/69, 545/70, 660/60) as the RGB proxy |
| 2 | Mantis MS, standard block | as published (Q39), and the rule-7-clean subset 480, 545, 660, 900 |
| 3 | Mantis MS, custom block | 490, 560, 665, 705, 740, 865 (`sensor_mantis_vnir6`) |
| 4 | Mantis or Chameleon HS, all channels | the 470-900 nm channels at AVIRIS-NG's 5 nm (about 87; the camera's 96 at 4.5 nm is slightly finer) |
| 5 | Mantis HS, 6 chosen in orbit | best k <= 6 searched from the 470-900 nm channels |
| 7 | Mantis SWIR alone | best k <= 4 of DFA's 11 rule-7-clean filters (L5 excluded), no VNIR |
| 8 | Mantis MS custom + SWIR | best k <= 4 DFA filters with row 3 fixed (one head, simultaneous; A-20) |
| 9 | Mantis MS standard + SWIR | the same with row 2 fixed |
| 10 | Anchors | config_c/VNIR, config_a, sentinel2_p6_12band, for pairing with hs_v4 |

**Reported per row:**
- combined skill, and RMSE per head;
- paired gap to the best row (A-49);
- the bands chosen;
- beside each row, unscored: size, mass, power, TRL, GSD and swath (from DFA where stated, else the spreadsheet, labelled).

The result is P12's sensor option table, with pros and cons. Cost never ranks (A-41).

**Not modelled, and stated:**
- GSD and swath: the pack is at 20 m.
- Per-band SNR beyond the placeholder model (A-37; the same model for all rows, so the comparison is spectral).
- Focal-plane misregistration (E-28).

**Proposed predictions** (registered in E-66 once approved):
1. The custom MS block beats the standard one (paired CI above 0): red edge matters.
2. MS custom alone beats SWIR alone (paired CI above 0): James's MS-or-SWIR question.
3. All HS channels are within one paired SE of MS custom: more bands buy little beyond 6 well-placed ones.
4. MS custom + SWIR beats MS custom alone (CI above 0): the SWIR mode earns its place with DFA's real filters.
5. RGB scores below every MS row.

**Code (no training locally):**
- Statistics:
  - a `config/grids/p12_sensors.yaml` grid;
  - `hs_grid.py` arms that take an explicit candidate list (DFA's catalogue) instead of a regular grid;
  - band sets for the DFA standard block and the RGB proxy;
  - a P12b packager.
- FW: `run_hs_search.py` accepts the arms the grid names, instead of a fixed list.
- Tests for each piece.
- Cluster: one `sweep_hs.sh` run on `aviris_v4`. It is about 75 tasks; the DFA search arms are small (11 candidates), and the HS search is the size of hs_v4's VNIR arm. A lidar-height cross-check on `aviris_lidar_v2` follows for the leading rows.

**Open before running:**
- Q39: score the standard block as published?
- Q40: DFA confirmations. Without them, row 6 stays a placeholder and is labelled so.

**Launch** (Narval, in `Fire_Risk_FW` after `git pull`; `aviris_v4` on scratch):

```bash
ARMS="references dfa_swir_alone dfa_swir_on_custom dfa_swir_on_standard dfa_hs_select"   GRID=configs/noise/p12_sensors_grid.json SCRATCH_DATA=$HOME/scratch/aviris_v4   EXP_NAME=sensors_v1 SUBMIT=1 bash scripts/shell/sweep_hs.sh
```
