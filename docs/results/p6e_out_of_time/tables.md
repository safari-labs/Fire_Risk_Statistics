# P6e tables: out-of-time generalisation (E-63)

Runs: `narval_results\e63_regime_b\20261101-2054` (regime B), `narval_results\e63_regime_a\20261101-2054` (regime A). All values are Reconstructed (ours). 15 fits per rung, none truncated. 2025 is frozen and was not opened; regime A has no 2024 score, because 2024 is its training data.

## Regime B, cross-validated against 2024

| rung | within CV | within 2024 | change [95 % CI] | between CV | between 2024 | change [95 % CI] |
|---|---|---|---|---|---|---|
| R0 | 0.681 | 0.617 | -0.064 [-0.096, -0.028] | 0.859 | 0.814 | -0.046 [-0.138, 0.060] |
| R1 | 0.719 | 0.642 | -0.077 [-0.119, -0.032] | 0.886 | 0.779 | -0.108 [-0.199, -0.008] |
| R2 | 0.695 | 0.632 | -0.063 [-0.101, -0.020] | 0.880 | 0.795 | -0.085 [-0.172, 0.013] |

For scale: the HFI ISSUED by CWFIS on 2024 ranks patches at between-patch AUC 0.834 (111 patches paired, E-56). Issued grids are 2 km, so they have no within-patch counterpart.

## Learned rung minus R0

| rung | within 2024 | between 2024 | within CV | between CV |
|---|---|---|---|---|
| R1 | +0.025 [0.009, 0.041] | -0.035 [-0.095, 0.021] | +0.038 [0.022, 0.052] | +0.027 [-0.003, 0.065] |
| R2 | +0.015 [0.001, 0.028] | -0.019 [-0.068, 0.029] | +0.013 [0.001, 0.026] | +0.021 [-0.008, 0.058] |

## The change net of R0's change

R0 has no training, so what it loses comes from the cohort. This is not registered.

| rung | within | between |
|---|---|---|
| R1 | -0.013 [-0.035, 0.012] | -0.062 [-0.136, -0.000] |
| R2 | +0.001 [-0.018, 0.021] | -0.039 [-0.102, 0.018] |

## Same-year between-patch AUC, 2019-2023

Year alone ranks these patches at 0.87 (E-43), so this reads closer to one year's ranking than the headline figure.

| rung | same-year pairs | 2024 |
|---|---|---|
| R1 | 0.840 | 0.779 |
| R2 | 0.846 | 0.795 |

## Within-patch AUC inside one fuel family (CV, then 2024)

The all-pixel figure also counts telling one family from another. These count only ranking inside a family.

| rung | C | D | M |
|---|---|---|---|
| R0 | 0.522, 0.502 | 0.518, 0.512 | 0.541, 0.496 |
| R1 | 0.630, 0.537 | 0.627, 0.596 | 0.593, 0.527 |
| R2 | 0.593, 0.517 | 0.566, 0.570 | 0.564, 0.534 |

## Regime A minus regime B, on the same 2019-2023 folds and seeds

Hypothesis (b) is read on 2025, in P10. This only says whether 2024 in training changes the 2019-2023 folds.

| rung | A within | A between | within, A - B | between, A - B |
|---|---|---|---|---|
| R1 | 0.711 | 0.879 | -0.008 [-0.018, 0.001] | -0.007 [-0.021, 0.006] |
| R2 | 0.689 | 0.877 | -0.005 [-0.018, 0.006] | -0.003 [-0.027, 0.015] |
