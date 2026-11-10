# P6b tables: what CWFIS issued against our R0, 2024 (E-56)

Run: `runs\20261030-e56_cohort_2024`. 120 patches of 2024 (60 fire). 2025 is frozen (splits/time_test_v1.json) and was not opened.

## E-56 as registered: ISSUED by CWFIS against Reconstructed (ours)

| output | R0 fuel | n (fire) | AUC ISSUED | AUC ours | ISSUED minus ours [95 % CI] | Spearman rho [95 % CI] |
|---|---|---|---|---|---|---|
| HFI (kW/m) | CWFIS 2024 fuel | 111 (55) | 0.834 | 0.837 | -0.003 [-0.060, 0.057] | 0.82 [0.74, 0.88] |
| HFI (kW/m) | SCANFI 2020 fuel | 111 (55) | 0.834 | 0.829 | +0.005 [-0.055, 0.066] | 0.84 [0.75, 0.89] |
| ROS (m/min) | CWFIS 2024 fuel | 111 (55) | 0.830 | 0.832 | -0.003 [-0.066, 0.059] | 0.79 [0.68, 0.86] |
| ROS (m/min) | SCANFI 2020 fuel | 111 (55) | 0.830 | 0.825 | +0.005 [-0.054, 0.068] | 0.82 [0.73, 0.87] |
| CFB (fraction) | CWFIS 2024 fuel | 111 (55) | 0.783 | 0.801 | -0.018 [-0.083, 0.046] | 0.77 [0.67, 0.84] |
| CFB (fraction) | SCANFI 2020 fuel | 111 (55) | 0.783 | 0.802 | -0.020 [-0.089, 0.056] | 0.74 [0.63, 0.83] |

Patches using an earlier issued day: 1 of 120.

## Fire type, share of area (the issued `ft` grid is fire type, not fuel type)

Over pixels burnable in both: the issued 2 km cell at each 40 m pixel centre against our R0's fire type (CFB < 0.1 surface, 0.1-0.9 intermittent crown, > 0.9 crown).

| R0 fuel | n | agreement, share of area [95 % CI] | surface ours / issued | intermittent ours / issued | crown ours / issued | crowning share, Spearman rho [95 % CI] | fuel/non-fuel agreement | non-fuel ours / issued |
|---|---|---|---|---|---|---|---|---|
| CWFIS 2024 fuel | 111 | 0.703 [0.646, 0.757] | 0.776 / 0.663 | 0.180 / 0.285 | 0.044 / 0.052 | 0.74 [0.62, 0.82] | 0.891 | 0.124 / 0.106 |
| SCANFI 2020 fuel | 111 | 0.687 [0.627, 0.742] | 0.778 / 0.664 | 0.162 / 0.284 | 0.060 / 0.052 | 0.72 [0.59, 0.82] | 0.885 | 0.087 / 0.106 |

## FMC: ISSUED by CWFIS against Reconstructed (ours)

101 patches with an issued FMC at the patch centre (range 85-120 %). Ours is FBP eqs 1-8 at the patch centre and its elevation, on the issued day.

| median difference | mean (bias) | MAE | 5th-95th percentile | max abs | within 0.05 points | Spearman rho | MAE at R0's day (D) |
|---|---|---|---|---|---|---|---|
| -0.00 | +0.19 | 0.83 | -2.04 to +3.48 | 6.38 | 54% | 0.989 | 1.22 |
