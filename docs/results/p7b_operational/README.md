# P7b: The operational CFFDRS reference (E-55, 2026-10-26)

Until now "R0" meant our reconstruction of CFFDRS: FWI1987 run on ERA5-Land, and FBP on our fuel layers. This phase sets it against what CWFIS actually issued.

**The source.** The FWI and fire danger rating grids for each development patch's D−1 come from the CWFIS GeoServer's time-enabled WCS (`Fire_Risk_Model/scripts/python/fetch_cwfis_grids.py`).

**What is archived** (GetCapabilities, 2026-10-26):

| Grid | Archived from |
|---|---|
| FWI and the danger class | 2018 |
| The five codes (FFMC, DMC, DC, ISI, BUI) and every FBP output | 2024 |

That leaves:
- **FWI only.** For our 2019–2023 fires, only the FWI is available. The FBP comparison waits for E-56's 2024–2025 cohort, or for Q30.
- **Between patches only.** All grids are 2 km and a patch is about 11 km, so there is no operational counterpart to any within-patch result.

**Registration.** E-55 was registered in commit `9f76480`, before any grid value was scored. The frozen test patches were never requested.

**At a glance:** [experiments.md](experiments.md). Tables: [tables.md](tables.md). Rebuild with `python scripts/make_results_package.py --phase P7b --run narval_results/slots_v2/7289478`.

## Coverage

| Patches | n |
|---|---|
| Development patches | 194 |
| Dated before the archive (2016–2017 confusers) | 6 |
| Covered, but CWFIS issued no FWI (April to mid-May; the grid's season had not started; whole tile empty) | 7 |
| **Scored: operational, ERA5 and station FWI all present** | **181 (83 fires)** |

Not-issued patches are left out of the primary result. A sensitivity check scores them as FWI 0, which is what an operator would have seen.

## E-55: MIXED

![auc](auc.png)

| FWI source on D−1 | Between-patch AUC | Same-year pairs |
|---|---|---|
| CWFIS operational grid (patch mean) | 0.860 [0.798, 0.915] | 0.744 |
| ERA5-Land, 13:00 LDT (ours) | 0.851 [0.783, 0.906] | 0.799 |
| Nearest CWFIS station | 0.847 [0.782, 0.903] | 0.718 |
| CWFIS fire danger class | 0.851 [0.788, 0.910] | 0.806 |

- **Ranking: held.** Ours minus operational is −0.009 [−0.073, +0.057], inside the registered 0.03. Scoring not-issued patches as 0 gives operational 0.868, about the same.
- **Agreement: failed.** Spearman ρ between our FWI and the issued FWI is 0.76 [0.63, 0.85], under the registered 0.8. Ours runs a median 3.6 FWI lower. The station FWI tracks the grid more closely (ρ 0.84, median difference 0), as expected, since the grid is interpolated from stations.
- **Same-year pairs reverse the order.** Within a year, the issued FWI ranks patches worse than ours (0.744 vs 0.799). The danger class does best (0.806). Much of the operational grid's all-pairs AUC is the fire year (year alone: 0.87, E-43).

![agreement](agreement.png)

**Where the reconstruction departs (P7b-C1, added after registration).** 19 patches have operational FWI above 10 and ERA5 FWI below 3:

| Cause | Patches | Detail |
|---|---|---|
| ERA5 rain the station didn't see | 10 | More than 2 mm in the ERA5 cell against about 0 at the station. FFMC 46–75 against the station's 85–91. |
| Late season start | 4 | Our snow rule hadn't started the season; CWFIS was already issuing FWI 11–32. |
| FFMC differences | 5 | — |

So the weakness is ERA5-Land's light rain and the start-up rule, not the FWI equations, which match the `cffdrs` R package.

## Every rung against operational CFFDRS (P7b-M1)

![ladder](ladder_vs_operational.png)

Same five folds as the sweep, between patches, paired by fold and group. The operational FWI scores 0.857:

| Rung | Between-patch AUC | Minus operational |
|---|---|---|
| ERA5 FWI (ours) | 0.849 | −0.007 [−0.074, +0.056] |
| R0 HFI | 0.873 | +0.016 [−0.048, +0.077] |
| R1 | 0.899 | +0.042 [−0.020, +0.104] |
| R2 | 0.892 | +0.035 [−0.034, +0.100] |
| R4 | 0.891 | +0.035 [−0.033, +0.101] |

No rung separates from operational CFFDRS between patches at 83 fires. The P7 ladder now carries the operational FWI as a reference line.

## What this changes

- **Imagery deltas stand.** R0's weather ranks patches the way the issued FWI does, so the imagery deltas in P7 are not measured against an artificially weak baseline.
- **The station is the closer reference.** Where values matter rather than ranks (thresholds, danger classes, staleness), the station or the operational grid tracks the issued FWI better than ERA5 does.
- **Two follow-ups are worth registering:**
  - an ERA5 rain correction or a minimum-rain threshold;
  - a season start that follows CWFIS's.
- **E-56** (2024–2025 cohort) remains the only route to operational FBP outputs unless CWFIS holds older grids (Q30).
