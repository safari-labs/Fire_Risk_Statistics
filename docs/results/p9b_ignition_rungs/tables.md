# P9b tables: ignition learned rungs (E-45)

Run: `narval_results\ignition_v1\20261105-1625`. Reconstructed (ours).

## Coverage

| configuration | fits | folds | sets scored |
|---|---|---|---|
| r0_scanfi | 5 | 0, 1, 2, 3, 4 | 1,292 |
| r0_cwfis | 5 | 0, 1, 2, 3, 4 | 1,292 |
| r1 | 15 | 0, 1, 2, 3, 4 | 1,292 |
| r2 | 10 | 0, 1, 2, 3 | 1,057 |
| r2_cwfis | 1 | 0 | 278 |

Not in the run yet: r2_leaf_ablated, r4, r4_shuffled.

## Matched-set AUC

| configuration | AUC [95 % CI] | sets | blocks |
|---|---|---|---|
| R0, SCANFI fuel | 0.5332 [0.5175, 0.5492] | 1,292 | 394 |
| R0, CWFIS fuel | 0.5281 [0.5117, 0.5446] | 1,292 | 394 |
| R1, learned on the CFFDRS inputs | 0.5855 [0.5672, 0.6031] | 1,292 | 394 |
| R2, physics + residual | 0.5876 [0.5679, 0.6067] | 1,057 | 316 |
| R2, CWFIS fuel | 0.6020 [0.5679, 0.6338] | 278 | 79 |

## Paired contrasts (sets both hold)

| a - b | difference [95 % CI] | sets | complete |
|---|---|---|---|
| r1 - r0_scanfi | +0.0524 [+0.0331, +0.0724] | 1,292 | yes |
| r2 - r0_scanfi | +0.0564 [+0.0382, +0.0749] | 1,057 | no |
| r2 - r1 | -0.0002 [-0.0149, +0.0147] | 1,057 | no |
| r2_cwfis - r0_cwfis | +0.0754 [+0.0364, +0.1172] | 278 | no |
| r2_cwfis - r2 | +0.0089 [-0.0250, +0.0438] | 278 | no |

## Registered predictions (2026-11-05, before any fit)

| prediction | verdict |
|---|---|
| r4 beats r4_shuffled, paired CI above 0 | PENDING (not in the run yet) |
| r2 within +-0.01 of r0 | REFUTED (provisional: fits missing) |
| r2_leaf_ablated within +-0.005 of r2 | PENDING (not in the run yet) |
