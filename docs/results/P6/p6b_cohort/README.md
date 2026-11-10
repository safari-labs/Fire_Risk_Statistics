# P6b: the 2024–2025 cohort, and what CWFIS issued (E-56, 2024 half)

The cohort is 240 patches: 60 fire and 60 unburned per year. No model was trained here: E-56 compares two physics outputs, scored locally in `runs/20261030-e56_cohort_2024`. **2025 is frozen and was not opened.** E-63 reads it once, in P10. The design is in A-42.

Generated with:

```bash
cd ../../Fire_Risk_Model
python scripts/python/build_cohort_2024_25.py --stage leaf
python scripts/python/build_dated_weather.py --patch-dir data/cohort_2024_25/patches --only weather
python scripts/python/pack_cohort_2024_25.py --freeze-only
python scripts/python/eval_cffdrs_reference.py --design dated --cohort \
    --patch-dir data/cohort_2024_25/patches --freeze data/cohort_2024_25/eval_freeze_2024.json \
    --n-qual 0 --out ../../Fire_Risk_Statistics/runs/20261030-e56_cohort_2024
python scripts/python/eval_e56_fire_type_fmc.py --run ../../Fire_Risk_Statistics/runs/20261030-e56_cohort_2024 \
    --out ../../Fire_Risk_Statistics/runs/20261110-e56_fire_type_fmc
cd ../../Fire_Risk_Statistics
python scripts/make_results_package.py --phase P6b --run runs/20261030-e56_cohort_2024 \
    --ft-fmc-run runs/20261110-e56_fire_type_fmc
python scripts/make_phase_docs.py --phase P6b
```

## What it found

- **On 2024, E-56's prediction holds, so its verdict is PARTIAL until 2025 runs.** The HFI ISSUED by CWFIS ranks fire above unburned patches with AUC 0.834. Reconstructed (ours) with the CWFIS 2024 fuel layer gives 0.837. The gap is −0.003 [−0.060, +0.057], against the registered 0.03, and the two agree across patches (Spearman ρ 0.82 [0.74, 0.88], registered ≥ 0.7).
- **The other fuel source agrees too.** With SCANFI 2020 fuel, R0 gives 0.829, a gap of +0.005 [−0.055, +0.066], ρ 0.84.
- **ROS and crown fraction behave the same way.** ROS: 0.830 ISSUED, 0.832 ours, ρ 0.79. CFB: 0.783 ISSUED, 0.801 ours, ρ 0.77.
- **Our reconstruction matches operational FBP closely enough to stand in for it on ranking.** This is the first direct check against what operational FBP issued.
- **FMC matches what CWFIS issued** (added 2026-11-10). On 101 patches the median difference is 0.00 points, the MAE 0.83 and ρ 0.989; 5–95 % of differences lie within −2.0 to +3.5 points. Both sides run FBP eqs 1–8, so this checks the implementation, latitude, longitude and elevation inputs, not a different FMC. The remaining differences come from elevation (our patch-centre value against CWFIS's 2 km cell).
- **Fire type agrees on 70 % of the burnable area** (0.703 [0.646, 0.757] with CWFIS 2024 fuel, 0.687 with SCANFI 2020). Our R0 calls less intermittent crown fire than CWFIS issued (18 % of the area against 28 %) and about the same share of crown fire (4–6 % against 5 %). Across patches the crowning share agrees at ρ 0.74 [0.62, 0.82]. Part of the gap is scale: the issued value is one 2 km cell, ours is a 40 m pixel.

## Correction (2026-11-10): CWFIS does not issue a fuel-type grid

The archived `ft` layer is the **FBP fire type**, not the fuel type: its codes 1, 2 and 3 split exactly at CFB 0.1 and 0.9 on every 2024 cell. The earlier line, "the issued grid and the 30 m layer agree on the majority family on 79 of 111 patches", was wrong. Every issued code mapped to conifer, so 79 was just the number of patches whose 30 m majority is conifer. **E-56's registered fuel-type comparison (share of area) cannot be made from the archive.** It is replaced by two things the archive does carry:
- fire type, share of area (above);
- fuel/non-fuel agreement from the grid's non-fuel codes: 89 % of the area, with 11 % non-fuel issued against 12 % in the CWFIS 2024 layer and 9 % in SCANFI.

## Limits

- **The CI is wider than the threshold.** A gap of up to about ±0.06 can't be excluded, so this says "no detectable difference", not "proven within 0.03". The registered test is a difference above 0.03 with a CI excluding 0, and that did not occur.
- **The two sides share inputs.** R0 here uses CWFIS's own fuel layer and CWFIS's issued green-up, so part of the agreement is built in. The SCANFI row is the more independent one, though it shares the green-up.
- **The negatives are unburned patches, not same-place confusers.** These AUCs read higher than a location-matched test would, and shouldn't be compared with the 2019–2023 confuser results.
- **111 of the 120 patches are paired.** The other 9 have no issued value (non-fuel cells).
- **No fuel-type comparison is possible** (see the correction above). Fire type and fuel/non-fuel are substitutes, not the registered measure.
- **Fire type compares a 2 km cell with a 40 m pixel**, so share-of-area agreement is capped below 1 even if both sides were identical at the same scale.

## Cohort status

- **Leaf state:** all 240 patches, from the issued green-up grid.
- **Weather:** all 240. Two patch centres fall on sea, so they use the nearest ERA5-Land point, 0.1° east, and the record says so.
- **Pack:** `data/cohort_2024_25_v2/`, with `year2024.h5` for the cluster and `time_test.h5` (2025) refused by `bundle.py` and by the training code.

## Files

| File | What it shows |
|---|---|
| `experiments.png`, `experiments.md` | phase sheet: E-56, E-63's status, the cohort checks |
| `issued_vs_r0.png` | HFI ISSUED against Reconstructed (ours), and AUC per output |
| `tables.md`, `T_e56.csv`, `T_e56_fire_type.csv`, `summary.json` | the numbers |

<!-- qual:start -->
## Qualitative view per experiment

- **E-56** Operational FBP outputs on a 2024-2025 cohort (tiles and patch map): [qual_E-56_cohort_tiles.png](qual_E-56_cohort_tiles.png), [qual_E-56_patch_map.png](qual_E-56_patch_map.png)
<!-- qual:end -->
