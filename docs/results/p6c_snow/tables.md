# P6c tables: the snow-off estimator (E-60)

Run: `narval_results\snow_v1\20261029-1426`. 15 tasks (5 outer folds of 1-degree station blocks x 3 seeds), ECCC climate-station snow on ground as truth (Q33). Errors are each fold's median |S2 - station| snow-off date over station-years, then the mean over runs; 95 % CIs resample whole folds.

## Nested sets (with sensor noise; noise-free in brackets)

| arm | input | k=1 | k=2 | k=3 | k=4 | k=5 | k=6 |
|---|---|---|---|---|---|---|---|
| any band (SWIR allowed) | raw bands | 23.4 (23.4) | 19.7 (19.9) | 17.9 (18.2) | 17.1 (17.1) | 16.8 (16.8) | 16.8 (16.8) |
| any band (SWIR allowed) | indices only |  |  |  |  |  |  |
| any band (SWIR allowed) | raw + indices | 23.4 (23.4) | 19.6 (19.7) | 16.9 (17.1) | 16.2 (16.2) | 15.8 (15.6) | 15.7 (15.4) |
| VNIR only (no B11, B12) | raw bands | 23.4 (23.4) | 23.0 (23.0) | 22.6 (22.5) | 22.4 (21.5) | 21.3 (21.3) | 21.1 (20.9) |
| VNIR only (no B11, B12) | indices only |  |  |  |  |  | 24.8 (23.3) |
| VNIR only (no B11, B12) | raw + indices | 23.4 (23.4) | 22.4 (23.6) | 22.4 (22.8) | 22.4 (21.9) | 21.4 (20.5) | 19.5 (19.2) |

Sampling floor, a perfect per-observation classifier: median 7.5 d, p90 33.9 d, within 7 d 49% (913 development station-years).

## VNIR-only minus SWIR-allowed (with noise)

| input | k | difference (d) | 95 % CI | folds VNIR worse |
|---|---|---|---|---|
| raw | 1 | +0.00 | [0.00, 0.00] | 0/5 |
| raw | 2 | +3.33 | [0.43, 6.33] | 3/5 |
| raw | 3 | +4.70 | [3.17, 6.63] | 5/5 |
| raw | 4 | +5.27 | [3.97, 6.58] | 5/5 |
| raw | 5 | +4.52 | [2.96, 6.07] | 5/5 |
| raw | 6 | +4.33 | [2.33, 6.20] | 5/5 |
| raw+indices | 1 | +0.00 | [0.00, 0.00] | 0/5 |
| raw+indices | 2 | +2.72 | [0.40, 5.08] | 3/5 |
| raw+indices | 3 | +5.53 | [3.43, 7.63] | 5/5 |
| raw+indices | 4 | +6.12 | [4.45, 7.78] | 5/5 |
| raw+indices | 5 | +5.63 | [3.53, 7.73] | 5/5 |
| raw+indices | 6 | +3.80 | [1.27, 5.97] | 4/5 |
| raw+indices | best | +3.80 | [2.00, 5.60] | 5/5 |

## First two bands chosen (share of searches)

| arm | step 1 | step 2 |
|---|---|---|
| any band (SWIR allowed) | B4 53%, B3 33%, B2 13% | B11 60%, B12 20%, B9 7%, B8A 7%, B5 7% |
| VNIR only (no B11, B12) | B4 53%, B3 33%, B2 13% | B8A 73%, B9 7%, B8 7%, B5 7%, B4 7% |

## Early or late (raw + indices, with noise; estimate - station)

| arm | k | median signed (d) | 95 % CI | early | late | early > 7 d | late > 7 d |
|---|---|---|---|---|---|---|---|
| any band (SWIR allowed) | 1 | -7.2 | [-9.6, -4.6] | 60% | 39% | 49% | 29% |
| any band (SWIR allowed) | 2 | -2.8 | [-5.6, 0.1] | 55% | 44% | 42% | 32% |
| any band (SWIR allowed) | 3 | -2.5 | [-5.4, 0.7] | 54% | 45% | 41% | 30% |
| any band (SWIR allowed) | 4 | -1.6 | [-4.7, 1.5] | 53% | 46% | 40% | 30% |
| any band (SWIR allowed) | 5 | -2.0 | [-4.9, 1.3] | 53% | 46% | 40% | 30% |
| any band (SWIR allowed) | 6 | -1.8 | [-4.5, 1.3] | 52% | 47% | 39% | 30% |
| VNIR only (no B11, B12) | 1 | -7.2 | [-9.6, -4.6] | 60% | 39% | 49% | 29% |
| VNIR only (no B11, B12) | 2 | -5.4 | [-6.8, -3.9] | 58% | 41% | 47% | 31% |
| VNIR only (no B11, B12) | 3 | -1.4 | [-3.9, 1.0] | 52% | 46% | 42% | 36% |
| VNIR only (no B11, B12) | 4 | -0.8 | [-2.5, 1.0] | 51% | 47% | 40% | 37% |
| VNIR only (no B11, B12) | 5 | +1.5 | [-2.0, 4.9] | 47% | 51% | 37% | 39% |
| VNIR only (no B11, B12) | 6 | +1.8 | [-1.3, 5.4] | 47% | 52% | 36% | 39% |
| perfect classifier | - | -5.0 | | 70% | 27% | 44% | 7% |

From 15 runs of the signed-error rerun; the absolute errors in that run match the first run exactly on every task both finished.

Resources: CPU tasks, 4.6 min median, 6.1 min max (2 h requested).
