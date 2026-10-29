# P6a: ecology estimator band searches on Sentinel-2 (E-22, E-59, E-62 S2 half)

Run on Nibi (H100), 2026-10-29: `narval_results/eco_v2/20261029-1410`, 15 tasks (5 outer folds of 1-degree blocks x 3 seeds). 226 development patches (904 tiles) with SCANFI v2 2020 labels. The design is in A-38. The frozen 45-patch test set was not opened.

Generated with:

```bash
python scripts/make_results_package.py --phase P6a --run narval_results/eco_v2/20261029-1410
python scripts/make_phase_docs.py --phase P6a
```

## What it found

- **E-22 is SUPPORTED: SWIR comes first for vegetation structure.** The first band chosen is SWIR in 13 of 15 searches (B12 60 %, B11 27 %); in E-2's fire-outcome search B11 entered around step 4. Closure and fuel family open with SWIR in every run. The fire outcome and the structure labels rank bands differently, as predicted.
- **Three bands get most of the way.** Combined skill is 0.30 with one band, 0.43 with three and 0.455 with six; all 12 bands reach 0.463. Three bands reach 93 % of the all-band skill.
- **Per target, the bands differ.** Percent conifer opens with the red edge (B7 60 %, then B5 73 %); height with B5 or B12; closure always with B12; fuel family always with B11.
- **E-59 is MIXED: indices help a little, and only with many bands.** Adding every formable index to the raw bands changes nothing at k = 1–4 and adds about 0.006 skill (about 1 %) at k = 5–8, CIs above 0. The prediction said the gain would be largest at small k; it is the reverse. Indices alone are always worse than raw + indices. For P12: computing indices on board buys almost nothing for structure.
- **E-62 (Sentinel-2 half) is AT RISK.** The red edge is in 13 of 15 best 6-band sets, but dropping B5–B7 costs under 1 % on percent conifer and closure at k = 6, because SWIR bands substitute. The registered refutation (within 5 % on both) fired. Both paths here may use SWIR, so whether a VNIR-only camera needs the red edge is still open: the AVIRIS-NG search answers it.
- **Sensor noise barely matters** for structure at these SNRs: noisy and noise-free skill differ by under 0.005.

## Two caveats (Q35)

- **SCANFI is mapped from Landsat, SWIR included,** so the labels may favour Landsat-like bands. The SWIR-first ranking is not independent of that.
- **The fuel family "D" class is mostly open ground.** The CFS tree codes every pixel under 10 % closure as D-1/2 (A-11): 82 % of D pixels are tundra, rock or glacier (`tiles.png`, rows 2 and 4). Family skill mostly measures forest vs open ground vs water.

## Files

| File | What it shows |
|---|---|
| `experiments.png`, `experiments.md` | phase sheet: E-22, E-59, E-62, the family label, resources |
| `curves.png` | combined skill vs k, both paths, three input modes, noisy and noise-free |
| `targets.png` | RMSE / balanced accuracy per target vs k, with each target's own search |
| `selection.png` | which band each search added at each step, six searches |
| `indices.png` | E-59: raw + indices vs raw, and indices alone, paired |
| `red_edge.png` | E-62: no-red-edge path vs combined path, RMSE % |
| `tiles.png` | true colour and the SCANFI labels on four seeded tiles (data only) |
| `maps_pc.png`, `maps_closure.png`, `maps_height.png`, `maps_family.png` | labelled images: SCANFI label against each nested set's prediction (k = 1, 3, 6, no red edge, all 12) on one held-out tile per fold, with tile RMSE and the k = 6 error map. Built once `sweep_eco_maps.sh` has run (`<run>/maps/`) |
| `scores_alone.png`, `scores_added.png`, `scores.csv` | supplementary: every band's search score alone (step 1), and its gain if added at each later step, per search target |
| `tables.md`, `T_*.csv`, `summary.json` | the numbers |

## Resources

Tasks took 47 minutes median (52 max) of the 3 hours requested, with 343–460 fits each. GPU 92 % busy, 12.6 GB peak of 80; job memory 5.8 GB of 32. The first submission failed on A100 nodes ("Illegal instruction": the login node's software architecture), fixed in `make_env`.
