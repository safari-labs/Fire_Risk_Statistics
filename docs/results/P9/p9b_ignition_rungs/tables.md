# P9b tables: ignition learned rungs (E-45)

Run: `narval_results\ignition_v1\20261105-1625`. Reconstructed (ours).

## Coverage

| configuration | fits | folds | sets scored |
|---|---|---|---|
| r0_scanfi | 5 | 0, 1, 2, 3, 4 | 1,292 |
| r0_cwfis | 5 | 0, 1, 2, 3, 4 | 1,292 |
| r1 | 15 | 0, 1, 2, 3, 4 | 1,292 |
| r2 | 15 | 0, 1, 2, 3, 4 | 1,292 |
| r2_cwfis | 15 | 0, 1, 2, 3, 4 | 1,292 |
| r2_leaf_ablated | 15 | 0, 1, 2, 3, 4 | 1,292 |
| r4 | 15 | 0, 1, 2, 3, 4 | 1,292 |
| r4_shuffled | 15 | 0, 1, 2, 3, 4 | 1,292 |

## Matched-set AUC

| configuration | AUC [95 % CI] | sets | blocks |
|---|---|---|---|
| R0, SCANFI fuel | 0.5332 [0.5175, 0.5492] | 1,292 | 394 |
| R0, CWFIS fuel | 0.5281 [0.5117, 0.5446] | 1,292 | 394 |
| R1, learned on the CFFDRS inputs | 0.5855 [0.5672, 0.6031] | 1,292 | 394 |
| R2, physics + residual | 0.5851 [0.5680, 0.6016] | 1,292 | 394 |
| R2, CWFIS fuel | 0.5828 [0.5668, 0.5987] | 1,292 | 394 |
| R2, leaf state ablated | 0.5876 [0.5685, 0.6063] | 1,292 | 394 |
| R4, + imagery | 0.5883 [0.5713, 0.6055] | 1,292 | 394 |
| R4, imagery shuffled | 0.5799 [0.5612, 0.5971] | 1,292 | 394 |

## Paired contrasts (sets both hold)

| a - b | difference [95 % CI] | sets | complete |
|---|---|---|---|
| r1 - r0_scanfi | +0.0524 [+0.0319, +0.0726] | 1,292 | yes |
| r2 - r0_scanfi | +0.0519 [+0.0352, +0.0679] | 1,292 | yes |
| r2 - r1 | -0.0005 [-0.0130, +0.0115] | 1,292 | yes |
| r2_cwfis - r0_cwfis | +0.0547 [+0.0366, +0.0725] | 1,292 | yes |
| r2_cwfis - r2 | -0.0023 [-0.0172, +0.0119] | 1,292 | yes |
| r2_leaf_ablated - r2 | +0.0026 [-0.0056, +0.0102] | 1,292 | yes |
| r4 - r2 | +0.0032 [-0.0104, +0.0163] | 1,292 | yes |
| r4 - r4_shuffled | +0.0084 [-0.0064, +0.0233] | 1,292 | yes |
| r4_shuffled - r2 | -0.0052 [-0.0124, +0.0025] | 1,292 | yes |

## Registered predictions (2026-11-05, before any fit)

| prediction | verdict |
|---|---|
| r4 beats r4_shuffled, paired CI above 0 | NOT SHOWN |
| r2 within +-0.01 of r0 | REFUTED |
| r2_leaf_ablated within +-0.005 of r2 | INCONCLUSIVE |
