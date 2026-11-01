# P6a-HS, corrected pack, partial sweep: first band evidence from AVIRIS-NG

Run on Nibi, 2026-10-31: `narval_results/hs_v2_provisional/20261030-1755`. Pack `aviris_v2`: 31 of the 42 lines, labels from SCANFI 2020, with rotation fixed. 51 of 75 tasks finished; the rest hit the 3 h limit. The AVIRIS test set was not transferred.

**This is a partial, provisional result. E-61 and E-62 have no verdict. The final sweep needs all 42 lines, all folds, and the new open-ground classes.**

Generated with:

```bash
python scripts/make_results_package.py --phase P6hs --run narval_results/hs_v2_provisional/20261030-1755 \
    --out docs/results/p6a_hs_v2_provisional
python scripts/make_phase_docs.py --phase P6a-HS-v2
```

## Read this first: which folds each arm has

| Arm | Runs | Folds |
|---|---|---|
| References | 15 | all |
| SWIR, standard InGaAs | 15 | all |
| VNIR camera alone | 9 | 0, 2, 4 |
| VNIR, nothing in 700–760 nm | 6 | 1, 3 |
| SWIR, extended InGaAs | 6 | 1, 3 |

Folds differ in difficulty: the fixed VNIR set scores 0.303 on folds 0, 2, 4 and 0.242 on folds 1, 3. So `curves.png`, `selection.png` and the first two tables in `tables.md` must not be used to compare arms. Compare only inside one panel of `same_folds.png`, or one same-fold table.

## What it found

All skills are combined skill, with noise, against SCANFI labels (0 = training mean). "Gain" is above the fixed VNIR set on the same runs.

- **The fix worked.** Every set now beats the training mean, against −0.05 to −0.01 in the void first run.

| Set | Gain, folds 0, 2, 4 (9 runs) | Gain, folds 1, 3 (6 runs) |
|---|---|---|
| Searched extended InGaAs, 4 bands | not finished | +0.032 |
| Config C | +0.006 | +0.034 |
| Sentinel-2, 12 bands | +0.015 | +0.031 |
| Mantis MS + SWIR | +0.006 | +0.027 |
| Searched standard InGaAs, 4 bands | +0.016 | +0.005 |
| Config B | −0.006 | +0.015 |
| Config A | +0.002 | +0.012 |
| Searched VNIR, 6 bands | −0.009 | not finished |
| VNIR, nothing in 700–760 nm, 6 bands | not finished | −0.016 |

- **SWIR adds a small amount, and it depends on the fold.** The largest gains are about 0.03 on a score near 0.25. Fold 4 gives Sentinel-2's +0.032 and fold 0 only +0.005. Fold range is wider than most gaps, so the order of the sets near the top is not settled.
- **Extended InGaAs looks better than standard on folds 1 and 3 only.** Config C leads config A by 0.021 and the searched sets differ by 0.027. Standard catches up on folds 0, 2, 4, where extended's search did not finish. Paired E-61 numbers: extra RMSE removed by extended is +0.35 % conifer, +0.53 % closure and +0.28 m height, on 6 runs from two folds. Two folds are too few for those intervals to mean much, so this is a lead for the final sweep, not a result.
- **The searched VNIR set does not beat the fixed one.** The fixed six bands, close to Sentinel-2's, score the same or better, which suggests the search has little left to find in VNIR with these labels. It could also be search noise.
- **Red edge matters to the search.** A band in 700–760 nm is in all 9 best 6-band VNIR sets. The set without red edge is 0.016 below fixed VNIR, which contains red edge. E-62's own paired test could not run, because those two arms share no fold.

## What this does not answer

- **Whether SWIR is favoured.** These labels are SCANFI's, mapped from Landsat SWIR. The test is `hs_plots` and `hs_lidar` (Q35, A-44).
- **Anything about the 42-line pack or open-ground classes.** Shrub as grass and slash from harvest records came later.

## Options

Each same-fold section of `tables.md` lists the options with cost, pros and cons (A-41). They sit in two lists on purpose, because scores from different folds are not comparable. With 2 or 3 folds, "tied with the best" is a weak statement. Treat these as a preview of the final list.

## Resources

| Arm | Minutes per task, median |
|---|---|
| References | 28 |
| Standard InGaAs | 79 |
| No red edge | 121 |
| VNIR | 132 |
| Extended InGaAs | 155 |

Eight of the 13 jobs timed out at 3 h. Three tasks at a time over two rounds needs up to about 5 h, so `sweep_hs.sh` now asks for 6 h. The earlier note that 3 h would hold (`P6hs-M1`) was wrong: tasks took two to three times the first run's.

The package code now finds unequal folds itself, splits the options and adds `same_folds.png`. A complete sweep builds as before.
