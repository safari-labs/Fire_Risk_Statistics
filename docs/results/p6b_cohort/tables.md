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

## Fuel: majority family per patch

The 2 km grid CWFIS issued and the 30 m CWFIS 2024 layer agree on the majority family on 79 of 111 patches (71%). This compares families by majority, not the registered share of area, which needs the issued rasters.

Patches using an earlier issued day: 1 of 120.
