# E-46 re-score commands (Q38: the consensus set is scored as a fixed set)

Written by `scripts/make_band_options.py`. On Nibi, in `Fire_Risk_FW` after `git pull`.

## Sentinel-2 consensus sets (eco_v3 folds and seeds, size 8x2, with noise)

```bash
BANDS=B12 SIZES=8x2 EXP_NAME=bands_consensus RUN_ID=k1 SUBMIT=1 bash scripts/shell/sweep_eco_arch.sh
BANDS=B4,B12 SIZES=8x2 EXP_NAME=bands_consensus RUN_ID=k2 SUBMIT=1 bash scripts/shell/sweep_eco_arch.sh
BANDS=B4,B11,B12 SIZES=8x2 EXP_NAME=bands_consensus RUN_ID=k3 SUBMIT=1 bash scripts/shell/sweep_eco_arch.sh
BANDS=B4,B6,B8A,B12 SIZES=8x2 EXP_NAME=bands_consensus RUN_ID=k4 SUBMIT=1 bash scripts/shell/sweep_eco_arch.sh
BANDS=B4,B5,B8A,B11,B12 SIZES=8x2 EXP_NAME=bands_consensus RUN_ID=k5 SUBMIT=1 bash scripts/shell/sweep_eco_arch.sh
BANDS=B4,B5,B6,B8A,B11,B12 SIZES=8x2 EXP_NAME=bands_consensus RUN_ID=k6 SUBMIT=1 bash scripts/shell/sweep_eco_arch.sh
BANDS=B4,B8,B5,B3,B6,B11,B12 SIZES=8x2 EXP_NAME=bands_consensus RUN_ID=k7 SUBMIT=1 bash scripts/shell/sweep_eco_arch.sh
BANDS=B4,B8,B5,B3,B6,B8A,B11,B12 SIZES=8x2 EXP_NAME=bands_consensus RUN_ID=k8 SUBMIT=1 bash scripts/shell/sweep_eco_arch.sh
```

Copy back `~/scratch/fw_experiments/bands_consensus/` to `narval_results/bands_consensus/` (plain copy).

## AVIRIS-NG consensus SWIR sets (hs_v4 folds and seeds, references arm)

```bash
ARMS=references GRID=configs/noise/p12_consensus_grid.json SCRATCH_DATA=$HOME/scratch/aviris_v4 EXP_NAME=hs_consensus SUBMIT=1 bash scripts/shell/sweep_hs.sh
```

`SCRATCH_DATA` must be `aviris_v4`, the pack hs_v4 ran on (`sweep_hs.sh` defaults to aviris_v2). The combiner rejects any task whose pixel counts differ from hs_v4's.

It scores 8 consensus sets plus three anchors (config_c/VNIR, config_a, config_c). Copy back to `narval_results/hs_consensus/`.

Then: `python scripts/make_band_options.py --eco-rescore narval_results/bands_consensus --hs-rescore narval_results/hs_consensus/<run>`.
