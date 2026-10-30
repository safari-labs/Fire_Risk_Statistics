# P6a-HS tables: the AVIRIS-NG band searches (E-61, E-62)

**VOID FOR BANDS.** This run used pack v1, which placed rotated flight lines north-up, so its labels came from the wrong ground (A-40 amendment). Its skills and band paths must not be used.

Run: `narval_results\hs_v1_provisional\20261029-1705`. Tasks: vnir 15, vnir_no_red_edge 15, swir_std 15, swir_ext 12; 547,281 development pixels. The AVIRIS test set was not transferred.

## Combined skill by nested set (raw + indices, with noise; noise-free in brackets)

| arm | k = 0 (fixed VNIR) | k = 1 | k = 2 | k = 3 | k = 4 | k = 5 | k = 6 |
|---|---|---|---|---|---|---|---|
| VNIR camera alone |  | -0.018 (-0.018) | -0.018 (-0.013) | -0.015 (-0.010) | -0.019 (-0.018) | -0.015 (-0.013) | -0.024 (-0.024) |
| VNIR, nothing in 700-760 nm |  | -0.017 (-0.017) | -0.015 (-0.009) | -0.015 (-0.009) | -0.016 (-0.015) | -0.014 (-0.011) | -0.022 (-0.025) |
| SWIR on standard InGaAs, VNIR fixed | -0.046 (-0.054) | -0.037 (-0.048) | -0.024 (-0.036) | -0.029 (-0.033) | -0.021 (-0.033) |  |  |
| SWIR on extended InGaAs, VNIR fixed | -0.047 (-0.056) | -0.044 (-0.050) | -0.038 (-0.044) | -0.032 (-0.043) | -0.029 (-0.035) |  |  |

## Final nested set, per target (raw + indices, with noise)

| arm | set | RMSE percent conifer (%) | RMSE closure (%) | RMSE height (m) | fuel family skill |
|---|---|---|---|---|---|
| VNIR camera alone | k6 | 27.4 | 28.8 | 5.41 | +0.006 |
| VNIR, nothing in 700-760 nm | k6 | 27.5 | 28.6 | 5.38 | +0.004 |
| SWIR on standard InGaAs, VNIR fixed | k4 | 27.6 | 28.3 | 5.46 | +0.013 |
| SWIR on extended InGaAs, VNIR fixed | k4 | 29.3 | 30.1 | 5.78 | +0.019 |

## E-61 as registered: extended InGaAs against standard, k = 4 (RMSE removed from the fixed VNIR)

| target | standard | extended | extra from extended [95 % CI] | runs |
|---|---|---|---|---|
| percent conifer (%) | +2.49 | +2.01 | -0.48 [-1.37, 0.41] | 12 |
| crown closure (%) | +0.29 | -0.53 | -0.82 [-1.49, -0.27] | 12 |
| canopy height (m) | +0.04 | +0.01 | -0.04 [-0.10, 0.02] | 12 |

## E-62 as registered: no red edge minus VNIR, k = 6 (RMSE, % of VNIR)

| target | difference [95 % CI] | folds worse |
|---|---|---|
| percent conifer | +0.3 % [-1.0, 1.7] | 2/5 |
| crown closure | -0.7 % [-2.3, 0.4] | 2/5 |
| canopy height | -0.5 % [-1.8, 0.4] | 2/5 |

A band centred in 700-760 nm is in 8/15 best 6-band VNIR sets.

## Do the labels describe the pixels? NDVI against SCANFI (Spearman rho)

| | first pack (north-up) | rotated pack |
|---|---|---|
| development pixels | 547,281 | 757,281 |
| lines | 19 | 26 |
| crown closure: pooled | +0.159 | +0.571 |
| crown closure: median within a line | -0.025 | +0.436 |
| canopy height: pooled | +0.110 | +0.500 |
| canopy height: median within a line | -0.037 | +0.348 |
| percent conifer: pooled | +0.019 | -0.415 |
| percent conifer: median within a line | -0.014 | -0.381 |

Pixels inside their flight-line outline: north-up 0.1-38.2 %, placed 95.1-100.0 %. Rotation sources: boundary_fit_snapped 1, header 30.

## Resources

| arm | tasks | minutes, median | minutes, max | fits per task |
|---|---|---|---|---|
| vnir | 15 | 46 | 48 | 1773 |
| vnir_no_red_edge | 15 | 42 | 43 | 1587 |
| swir_std | 15 | 35 | 37 | 780 |
| swir_ext | 12 | 69 | 72 | 1680 |
