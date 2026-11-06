# P12a: band options, the consensus sets (E-46, Q38)

The first stage of P12's band decision. Each band search runs inside a training fold, so eco_v3 (Sentinel-2) and hs_v4 (AVIRIS-NG) return 15 sets per k (5 outer folds × 3 seeds), and the sets differ. Q38 (James, 2026-11-05, option 1): count them by region, form the consensus set, and score that exact set on the same folds. **The re-scores are not run yet.** Until they are, the option table carries the search scores, labelled as such. All values are Reconstructed (ours).

**At a glance:** [experiments.md](experiments.md). Generated tables: [options.md](options.md), [T_consensus.csv](T_consensus.csv), [T_options_s2.csv](T_options_s2.csv), [T_options_swir.csv](T_options_swir.csv). Re-score commands: [rescore_commands.md](rescore_commands.md).

```bash
python scripts/make_band_options.py      # now; add --eco-rescore / --hs-rescore when they return
python scripts/make_phase_docs.py --phase P12a
```

## How the consensus is formed (A-49, fixed before any re-score)

- **Regions.**
  - Sentinel-2: by band role. B5–B7 are one red-edge region and B8/B8A one NIR region. SWIR1 and SWIR2 stay apart because they sit on different detectors.
  - AVIRIS-NG SWIR: 50 nm bins, as the hs packager counts them. A-40's role windows leave out 1000–1550 and 1750–2080 nm, where searched bands do land.
- **Slots.** A k-band set can hold two bands of one region, so a region's second slot is supported by searches that put two bands there. The k best-supported slots form the set, and each region takes its most-chosen bands.
- **Stable** means every slot is supported by at least 10 of 15 searches.
- **The set is not forced to nest across k.** Each k's consensus stands on its own and is re-scored as a fixed set.

![consensus](consensus.png)

## What the counting shows

**Sentinel-2 (equal-weight search):**

| k | consensus set | weakest slot | stable |
|---|---|---|---|
| 1 | B12 | 11 / 15 | yes |
| 2 | B4, B12 | 6 / 15 | no |
| 3 | B4, B11, B12 | 8 / 15 | no |
| 4 | B4, B6, B8A, B12 | 9 / 15 | no |
| 5 | **B4, B5, B8A, B11, B12** | 10 / 15 | **yes** |
| 6 | B4, B5, B6, B8A, B11, B12 | 8 / 15 | no |
| 7 | B3, B4, B5, B6, B8, B11, B12 | 8 / 15 | no |
| 8 | B3, B4, B5, B6, B8, B8A, B11, B12 | 9 / 15 | no |

- **SWIR is in at every k.** How many of the 15 searches' sets hold each region:

  | region | k = 1 | k = 4 | k = 5–8 |
  |---|---|---|---|
  | SWIR2 (B12) | 11 | 12 | 12–13 |
  | SWIR1 (B11) | 0 | 8 | 10–12 |
  | red edge (B5–B7) | 0 | 9 | 15 |
  | red (B4) | 0 | 11 | 12–14 |
  | NIR (B8, B8A) | 4 | 11 | 12–15 |

  From k = 5 these five regions are each chosen by at least 10 searches. What the searches disagree on is the extra band or two (green, blue, a second NIR or red-edge band) and which band within a region.
- **k = 5 is the only multi-band set that passes Q38's rule.** It is red, one red edge, narrow NIR, SWIR1 and SWIR2.

**AVIRIS-NG SWIR:** no consensus set is stable. The weakest 50 nm slot is in 5–8 of 15 standard-InGaAs searches and 4–5 of 15 extended ones. The searches agree on a broad window (around 1500–1650 nm, and around 2000 nm in the extended arm) but not on a 50 nm placement. The fixed configurations then remain the clearer SWIR options: config C (1610 + 2190 nm) is the best score in hs_v4.

## The option tables (provisional)

`options.md` has both tables, with A-49's paired ties.
- **Sentinel-2:** the best option is still the percent-conifer search at k = 8 (0.4158). The equal-weight search at k = 7–8 ties with it, and k = 5–6 sit about 0.008 below. All of these are *search procedure* scores: each fold scored its own set, which no single fixed set reproduces. Each row says so under its cons.
- **The consensus sets are listed below each table with no score.** They enter the option table, with pros and cons, only once re-scored.

## The first re-score (2026-11-06)

`narval_results/bands_consensus`, 8 × 15 tasks, completed on Narval. **Only k = 1 is valid.**
- `sweep_eco_arch.sh` passed `BANDS` inside sbatch's comma-separated `--export` list, so `BANDS=B4,B12` reached the jobs as `BANDS=B4`. Every k ≥ 2 run trained on its first band only. The combiner rejects them because their bands don't match the consensus.
- Fixed in FW `6b1499a`, with a test. The k = 2–8 sets are rerun as `bands_consensus_v2`.
- **k = 1 (B12 alone), scored as a fixed set:** 0.2693 ± 0.0104. That is 0.009 above the equal-weight search's own k = 1 procedure score (0.2602), because 4 of the 15 searches chose another band first.

## The AVIRIS-NG re-score (2026-11-06)

`narval_results/hs_consensus/20261106-1202`: 15 of 15 tasks, every task's pixels matching hs_v4's (`aviris_v4`). A duplicate submission, `20261106-1201`, is ignored. Each consensus SWIR set is scored as a fixed set:
- **Best overall:** the extended-InGaAs consensus at k = 4 (1530, 1690, 1990, 2270 nm), 0.2895, tied with config C (0.2881). No Dragonfly mode reaches these (A-18).
- **Best on standard InGaAs, which Mantis SWIR is:** the configured slots 1240, 1550, 1610, 1680 (`sensor_mantis_ms_plus_swir`), 0.2853, 0.0042 ± 0.0009 below the best. They are ahead of every standard-InGaAs consensus (best: k = 4, 0.2796) and searched set. A short band near 1240 plus three across the 1550-1680 shoulder beats the placements the searches converge on.
- DFA's nearest filters to those slots are scored as fixed sets next ([P12/p12_sensors](../p12_sensors/README.md)).

## Next

1. **Re-score k = 2–8 on Narval** ([rescore_commands.md](rescore_commands.md), now `EXP_NAME=bands_consensus_v2`). The 8 AVIRIS-NG sets run in one `sweep_hs.sh` references job with `configs/noise/p12_consensus_grid.json` (running as `hs_consensus`).
2. Rerun `make_band_options.py` with both re-scores. The option table then puts each fixed set's own paired score beside the search scores, and James chooses (A-49).
3. E-47's size ladder at the chosen set.

## Limits

- SCANFI labels, mapped from Landsat (Q35), and placeholder noise (A-37).
- Cost is qualitative (Q6 open) and never chooses (A-41).

<!-- qual:start -->
## Qualitative view per experiment

- **E-46** Band and index decision (band placement): [qual_E-46_band_placement.png](qual_E-46_band_placement.png)
<!-- qual:end -->
