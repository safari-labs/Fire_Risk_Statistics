# First NBAC band searches (E-1, E-2, E-3, E-10), 2026-10-23

Narval jobs: vnir 6844532, all11 6844530, vnir_swir 6844531, neg_noise 6844515.
All 24 folds finished; every run records `pack_label: nbac`. Preset
tier2-small, 35 epochs (ranking budget), seed 0, six location-grouped folds.

These runs predate the per-fit artefacts and the deterministic full-tile
evaluation, so everything here comes from `nesting.json`: scores per rung,
every candidate at every step, and leave-one-out. There are no ROC curves,
scene breakdowns or maps yet. The replay below produces them.

## What the runs establish

1. **The pipeline does not leak.** The noise control (same width, bands
   replaced by Gaussian noise) scores 0.5022 ± 0.0007. That is above 0.5 in
   6/6 folds, but the positional prior it measures is 0.002, about 1% of any
   real arm's skill above chance. Every real-band arm sits at 0.70–0.88.
2. **Fold difficulty is larger than any band effect.** Per-fold scores span
   0.67–0.88 for the same arm. The fold SD (~0.07) is about ten times the
   median greedy margin (0.005–0.008).
3. **Under this budget, adding bands does not measurably help.** Mean
   score is flat from k=1 to k=7 in every arm (vnir 0.766 at k=1, 0.758 at
   k=6). In 14–19 of 36–42 greedy steps per arm, the winner beat the
   runner-up by under 0.005. At k=6 in vnir fold 0, removing any one of the
   six bands *raised* the score. See `rungs_nbac.png` and `steps_*.png`.
4. **The dNBR label flattered SWIR.** Taking SWIR's gain over vnir at
   matched k, it fell after the NBAC relabel in 11 of 12 cells (mean about
   −0.025; three cells clear 2 SE with folds disagreeing). Under dNBR, B11
   entered all11 at k=1 in two folds; under NBAC it never entered first.
   The dNBR runs were unseeded, so this is consistent evidence, not a
   measurement. See `label.png`.

## What they do not establish yet

| Exp. | Hypothesis | Reading so far |
|---|---|---|
| E-1 | Red edge in the best six, no B1/B9 | B5 is in 6/6 folds and B7 in 5/6 at k=6, but B9 is in 4/6. The k=6 set is no better than k=1, so its membership is not yet reliable. **Open.** |
| E-2 | B11 enters by k=3 | Entry rungs: never, 3, 2, 5, 2, 7. **Open.** |
| E-3 | Forced-B11 gain positive, under +0.02 | Within noise at every k from 2 to 6 (2-SE intervals about ±0.02). At k=1, B11 alone is 0.059 below vnir's best single band, but that compares one pinned band with the best of ten picked on the same fold, so it favours vnir. **Open.** |
| E-10 | Noise arm within noise of 0.5; real arm clearly above | The noise half holds in practice (0.002). The real-band twin (`neg_real`) was not submitted. |

Exploratory only (rule 1 ranks nested sets): with each band alone,
fold-centred, B8A and B7 are above the fold mean in 6/6 and 5/6 folds, and
B1 is below it in 6/6 (`singletons.png`).

## Why the ranking is not yet readable, and the fix already built

Validation used a random 64 × 64 crop of each tile with spectral jitter,
redrawn every epoch, and only one seed was run. A margin of 0.005 cannot be
told apart from either source of noise. The sweep now validates on the
full, unaugmented tile and writes artefacts. `--replay` refits only each
fold's chosen rung sets (6–7 fits instead of 49–60):

```bash
cd ~/projects/def-rlandry/jfullum/Fire_Risk_FW && git pull
SUBMIT=1 REPLAY_JOBS=vnir=6844532,all11=6844530,vnir_swir=6844531 bash scripts/shell/sweep_replay.sh
SUBMIT=1 SEED=1 REPLAY_JOBS=vnir=6844532,all11=6844530,vnir_swir=6844531 bash scripts/shell/sweep_replay.sh
SUBMIT=1 SETS=neg bash scripts/shell/sweep_axes.sh       # neg_real + neg_noise, with artefacts
```

Seed 0 tells us whether the rung order survives a clean evaluation. The
seed 0 vs seed 1 difference is the noise floor the margins have to clear;
`report_search.py` reports it next to them. If most margins fall under it,
the next step is a larger epoch budget or more seeds, not more arms.

## Regenerating this folder

```bash
P=../Fire_Risk_FW/.venv/Scripts/python; O=docs/results/band_search_nbac; R=narval_results
$P ../Fire_Risk_FW/scripts/report_search.py $R --out $O
$P ../Fire_Risk_FW/scripts/report_arms.py $R/sweep_bands_tier2-small_baseline_{all11/6844530,vnir/6844532,vnir_swir/6844531,neg_noise/6844515} --figure $O --json-out $O/arms.json
$P ../Fire_Risk_FW/scripts/pool_bands.py $R/sweep_bands_tier2-small_baseline_{all11/6844530,vnir/6844532,vnir_swir/6844531} --figure $O
# after the replays are copied back:
$P ../Fire_Risk_FW/scripts/report_results.py $R --out docs/results/replay_nbac
```

| File | Content |
|---|---|
| `results.md` | Rung tables, matched-k contrasts, step margins, single bands, label contrast |
| `rungs_nbac.png`, `rungs_dnbr.png` | Score against k, one line per fold |
| `steps_<arm>.png` | Every candidate's gain at every step, winner outlined |
| `singletons.png` | Each band alone, fold-centred (exploratory) |
| `label.png` | SWIR's gain over vnir, NBAC minus dNBR |
| `band_matched_k.png` | all11 and vnir_swir against vnir, rung by rung |
| `band_selection_*.png`, `pool_bands.txt` | Selection frequency per k and LOO, per arm |
| `arm_comparison*.png`, `report_arms.txt` | Noise control against chance |
