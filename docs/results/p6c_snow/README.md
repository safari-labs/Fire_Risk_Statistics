# P6c: snow-off without SWIR (E-60)

Run on Nibi, 2026-10-29: `narval_results/snow_v1/20261029-1200`, rerun as `20261029-1426` with the signed error recorded (band paths and errors identical on every task); 15 CPU tasks (5 outer folds of 1-degree station blocks x 3 seeds). Truth is ECCC climate-station snow on ground (Q33). The design is in A-39. The frozen test set (122 station-years) was not opened.

Generated with:

```bash
python scripts/make_results_package.py --phase P6c --run narval_results/snow_v1/20261029-1426 \
    --signed-run narval_results/snow_v1/20261029-1426
python scripts/make_phase_docs.py --phase P6c
```

## What it found

- **E-60 is REFUTED as registered.** The best VNIR-only set misses the station snow-off date by a median of 19.5 days (with sensor noise), well above the registered 7 days. It is 3.8 days [2.0, 5.6] worse than the best SWIR-allowed set at each arm's best k, worse in all 5 folds; at k = 3–5 the gap is 5.5–6.1 days.
- **The 7-day threshold could not have been met by any camera.** A perfect classifier, the station's own snow on ground on each clear Sentinel-2 date, still misses by a median of 7.5 days (p90 34). Clear dates are about 5 days apart, spring snowfalls fall between them, and some stations report bare ground while their 30 m window is still white. That should have been checked when E-60 was registered.
- **The relative result is the useful one.** With SWIR allowed, the search puts a visible band first and SWIR second (B11 60 %, B12 20 %): the NDSI contrast, found rather than given. VNIR-only takes the 865 nm NIR band second. SWIR1 is worth about 4 days of snow-off accuracy at this estimator, a cost item for the SWIR chain in P12.
- **The estimator, not the bands, holds most of the remaining error.** The best set reaches 15.7 days against the 7.5-day floor. Better use of the time series (not only the last snowy observation) is where E-18's version of the estimator should start.
- **Errors go both ways.** With SWIR allowed, the best sets are early for 52 % of station-years and late for 47 %, with a median of −1.8 days [−4.5, +1.3]. Each direction is off by more than a week often: 39 % early, 30 % late. The early misses match the perfect classifier (44 %): the season's last snowfalls fall between clear scenes. The late misses do not (perfect classifier 7 %): that is the classifier still calling snow the station no longer reports. VNIR-only sets drift later as bands are added (+1.8 d at k = 6, 39 % late by more than a week), which fits a VNIR camera confusing bright snow-free ground with snow. See `direction.png`.
- **Sensor noise barely matters here.** No set moves by more than 1.5 days between noisy and noise-free.
- **Indices add a little.** Raw + indices beats raw bands by about 1 day with SWIR (15.7 vs 16.8 at k = 6). Indices alone are worse, and form nothing for most small sets.

## Files

| File | What it shows |
|---|---|
| `experiments.png`, `experiments.md` | phase sheet: E-60, the sampling floor, resources |
| `curves.png` | error vs k per arm and input mode, noisy and noise-free, against the floor and the 7-day threshold |
| `paired.png` | VNIR-only minus SWIR-allowed, paired by fold and seed |
| `selection.png` | which band each search added at each step |
| `direction.png` | early or late: signed error and the shares off by more than a week |
| `series.png`, `series_map.png` | labelled time series of held-out station-years (station reports, Sentinel-2 green, each model's snow probability and date) and a map of every station-year's signed error, SWIR allowed vs VNIR only. Built once `sweep_snow_maps.sh` has run (`<run>/maps/`) |
| `scores_alone.png`, `scores_added.png`, `scores.csv` | supplementary: every band's search score alone (median error, step 1), and the days of error it removes if added at each later step |
| `stations.png` | the stations, their sampling floor, and four station-years over the season (data only) |
| `tables.md`, `T_paired.csv`, `summary.json` | the numbers |

## Resources

Tasks took 4.4 minutes median (5.6 max) against the 2 hours requested; `sweep_snow.sh` now asks for 0:30:00.
