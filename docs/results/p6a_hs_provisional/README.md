# P6a-HS, provisional run: void for bands; the cause found and fixed

Run on Nibi, 2026-10-29: `narval_results/hs_v1_provisional/20261029-1705`. Arms: VNIR (15 tasks), VNIR without red edge (15), SWIR on standard InGaAs (15), SWIR on extended InGaAs (12 of 15; fold 4 is missing). The `references` arm was not run. Pack v1: 21 of the 42 lines. The design is in A-40. The AVIRIS test set was not transferred.

**Do not use this run's skills or band paths. E-61 and E-62 are still untested.**

Generated with:

```bash
cd ../Fire_Risk_Model
python scripts/python/aviris_georef_diag.py --north-up data/aviris_v1 --rotated data/aviris_v2
cd ../Fire_Risk_Statistics
python scripts/make_results_package.py --phase P6hs --run narval_results/hs_v1_provisional/20261029-1705 \
    --out docs/results/p6a_hs_provisional --diag ../Fire_Risk_Model/data/aviris/georef_diag.json \
    --void "..."
python scripts/make_phase_docs.py --phase P6a-HS-prov
```

## What it found

- **No band set beat the training mean.** Combined skill sits between −0.05 and −0.01 in every arm at every k, against 0.46 for the Sentinel-2 search on the same targets. No set beat predicting the average (`curves.png`). The chosen bands differ from fold to fold, as noise would (`selection.png`).
- **The cause is ours: every label came from the wrong ground.** AVIRIS-NG products are rotated rasters. The ENVI map info ends in `rotation=<deg>`, the flight heading, and the ingest ignored it. Pixels were placed as if north-up, up to tens of kilometres from their true position (`placement.png`). The pack then sampled SCANFI at those wrong positions.
- **Two independent checks confirm it:**

  | Check | First pack (north-up) | Corrected pack |
  |---|---|---|
  | Pixels inside the line's ABoVE flight outline | 0.1–38 % | 95–100 % |
  | NDVI vs SCANFI closure, median within a line (Spearman ρ) | −0.03 | +0.44 |
  | NDVI vs SCANFI height, median within a line | −0.04 | +0.35 |
  | NDVI vs percent conifer, median within a line | −0.01 | −0.38 |

  The conifer sign is the expected one: conifers are darker in the NIR than broadleaf canopy.
- **The corrected pack is built.** `data/aviris_v2` holds 31 of the 42 lines: 757,281 development pixels in 12 groups (26 lines). The frozen test split is unchanged (same hash, 3 groups, 5 lines, 150,000 pixels) and stays on this machine.
- **Every line's rotation is its own header's.** 30 of the 31 headers are read directly, from the last 256 KB or the first 20 MB of each archive, and each reproduces the table's stored origin. One line (`ang20180811t205747`) takes a tight fit to its outline, snapped to +9°. The 2022 outlines alone would not have done: fits to them miss by up to 2.5°.
- **The packer now refuses this failure.** It stops if under 90 % of a line's pixels fall inside its outline, and leaves out any table without a rotation.

## Reading the corrected pack

- **Agreement is not uniform (`label_agreement.png`).** Two 2018 lines near 68° N stay low (ρ about 0.07) because they are open tundra: closure there averages 6 %, so there is little to rank. Lines `ang20180811t205747` and `t210811` are also low (0.12–0.15).
- **`ang20180811t190237` falls from +0.17 to −0.08.** Its bright filter removes 703,633 of about 711,000 pixels (cloud or snow), leaving 7,281. Those few should not be read as a placement failure, but the line adds little.
- **This is a check on the data, not a retrieval result.** It shows that labels and spectra now describe the same ground. Whether bands can retrieve the targets is what the rerun tests.

## What is needed next

The sweep has to be rerun on `aviris_v2`, with all five arms (including `references`) and all folds. Tasks took 35–72 minutes against the 3 h requested, so the request holds. Evaluation fits are a fixed 3,000 steps, so the larger pack should not lengthen them.

## Files

| File | What it shows |
|---|---|
| `experiments.png`, `experiments.md` | phase sheet: the void run, the placement check |
| `placement.png` | three lines as ingested, as placed and their ABoVE outlines; each line's share inside its outline |
| `label_agreement.png` | NDVI against SCANFI within each line, before and after |
| `curves.png` | held-out skill by nested set, marked void |
| `selection.png` | bands chosen, marked void |
| `tables.md`, `T_label_agreement.csv`, `T_targets.csv`, `summary.json` | the numbers |
