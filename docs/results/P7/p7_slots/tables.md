# P7 tables: Stage A slot experiments (Narval sweep slots_v2)

Run: `narval_results\slots_v2\7289478`. 194 development patches (83 fire), 94 fire/block groups, 5 folds x 3 seeds per configuration. CIs: 2,000 (within) and 500 (between) bootstrap resamples of whole groups. The test split was not read.

## T-ladder

| rung | within-patch AUC | 95 % CI | between-patch AUC | 95 % CI | between, same-year pairs only |
|---|---|---|---|---|---|
| R0  physics only (HFI) | 0.669 | [0.644, 0.694] | 0.858 | [0.792, 0.912] | 0.806 |
| R1  learned on CFFDRS inputs | 0.719 | [0.689, 0.748] | 0.886 | [0.825, 0.930] | 0.840 |
| R2  physics + learned residual | 0.695 | [0.668, 0.721] | 0.880 | [0.817, 0.926] | 0.846 |
| R4  R2 + free imagery branch | 0.704 | [0.677, 0.732] | 0.881 | [0.819, 0.926] | 0.835 |

## T-contrast: paired by fire (a minus b)

| a - b | within | 95 % CI | folds won | between | 95 % CI | folds won |
|---|---|---|---|---|---|---|
| r1 - r0_scanfi | +0.0507 | [0.0336, 0.0680] | 5/5 | +0.0280 | [-0.0036, 0.0658] | 3/5 |
| r2 - r1 | -0.0246 | [-0.0343, -0.0145] | 0/5 | -0.0063 | [-0.0277, 0.0147] | 2/5 |
| r2 - r0_scanfi | +0.0261 | [0.0112, 0.0409] | 5/5 | +0.0217 | [-0.0083, 0.0553] | 4/5 |
| r0_cwfis - r0_scanfi | -0.0484 | [-0.0659, -0.0320] | 0/5 | -0.0112 | [-0.0318, 0.0088] | 1/5 |
| r3_pc - r2 | -0.0012 | [-0.0035, 0.0009] | 2/5 | +0.0014 | [-0.0061, 0.0080] | 3/5 |
| r3_fmc - r2 | +0.0022 | [-0.0010, 0.0053] | 3/5 | -0.0008 | [-0.0055, 0.0033] | 0/5 |
| r3_cbh - r2 | -0.0005 | [-0.0029, 0.0017] | 2/5 | -0.0011 | [-0.0069, 0.0039] | 1/5 |
| r3_curing - r2 | +0.0000 | [0.0000, 0.0000] | 0/5 | +0.0000 | [0.0000, 0.0000] | 0/5 |
| r3_pc_fmc_cbh - r2 | -0.0011 | [-0.0043, 0.0025] | 2/5 | -0.0014 | [-0.0101, 0.0047] | 0/5 |
| r4 - r2 | +0.0096 | [-0.0020, 0.0213] | 2/5 | +0.0012 | [-0.0208, 0.0227] | 3/5 |
| r2_cwfis - r2 | -0.0070 | [-0.0171, 0.0031] | 2/5 | +0.0060 | [-0.0094, 0.0241] | 3/5 |
| r2_station - r2 | -0.0171 | [-0.0341, -0.0007] | 1/5 | +0.0240 | [-0.0269, 0.0763] | 3/5 |
| r2_lag7 - r2 | -0.0244 | [-0.0385, -0.0112] | 0/5 | -0.0524 | [-0.1008, -0.0097] | 0/5 |
| r2_leaf_ablated - r2 | +0.0008 | [-0.0022, 0.0037] | 3/5 | +0.0003 | [-0.0097, 0.0092] | 2/5 |
| r3_pc_shuffled - r2 | -0.0002 | [-0.0029, 0.0028] | 2/5 | -0.0005 | [-0.0073, 0.0081] | 0/5 |
| r3_fmc_shuffled - r2 | +0.0015 | [-0.0008, 0.0036] | 3/5 | +0.0012 | [-0.0053, 0.0085] | 2/5 |
| r3_cbh_shuffled - r2 | +0.0000 | [-0.0024, 0.0024] | 3/5 | -0.0002 | [-0.0063, 0.0075] | 1/5 |
| r3_curing_shuffled - r2 | +0.0000 | [0.0000, 0.0000] | 0/5 | +0.0000 | [0.0000, 0.0000] | 0/5 |
| r3_pc_fmc_cbh_shuffled - r2 | -0.0022 | [-0.0067, 0.0018] | 2/5 | +0.0015 | [-0.0015, 0.0061] | 3/5 |
| r4_shuffled - r2 | -0.0000 | [-0.0023, 0.0023] | 4/5 | -0.0015 | [-0.0093, 0.0053] | 1/5 |

Real minus shuffled twin, within-patch:

| slot | real - twin | 95 % CI |
|---|---|---|
| Percent conifer, +/-30 points | -0.0010 | [-0.0042, 0.0019] |
| Foliar moisture, +/-30 % | +0.0006 | [-0.0018, 0.0032] |
| Crown base height, x e^+/-0.7 | -0.0005 | [-0.0022, 0.0012] |
| Curing, +/-30 points | +0.0000 | [0.0000, 0.0000] |
| PC + FMC + CBH together | +0.0011 | [-0.0032, 0.0057] |
| Free imagery branch (R4) | +0.0096 | [-0.0016, 0.0211] |

## T-corrections: the learned correction on the seeded tiles

| configuration | tiles | median tile mean | median within-tile SD | share of tiles within 10 % of the bound |
|---|---|---|---|---|
| r3_pc | 90 | -24.43 | 5.964 | 0.42 |
| r3_pc_shuffled | 90 | -29.86 | 0.321 | 1.00 |
| r3_fmc | 90 | +24.38 | 7.867 | 0.42 |
| r3_fmc_shuffled | 90 | +29.98 | 0.113 | 1.00 |
| r3_cbh | 90 | +0.69 | 0.036 | 0.73 |
| r3_cbh_shuffled | 90 | +0.70 | 0.004 | 0.97 |

CFB engagement (E-37's falsifier), R0 on the 30 seeded tiles: CFB > 0 on 47.2% of 1,817,056 burnable valid pixels, > 0.1 on 46.1%.

## T-weights: R2's learned physics weights

| output | median | IQR |
|---|---|---|
| ROS (spread) | -0.42 | [-0.43, -0.41] |
| HFI (intensity) | +0.67 | [+0.66, +0.69] |
| CFB (crowning) | -0.37 | [-0.41, -0.36] |
| TFC (consumption) | -0.23 | [-0.25, -0.22] |
| P(sustained flaming) | -0.04 | [-0.05, -0.02] |

## T-time: what the fits took (A100, Narval)

| configuration | fits | median wall (s) | max wall (s) | median best epoch |
|---|---|---|---|---|
| r0_cwfis | 15 | 13 | 16 | - |
| r0_scanfi | 15 | 13 | 16 | - |
| r1 | 15 | 146 | 158 | 17 |
| r2 | 15 | 194 | 218 | 27 |
| r2_cwfis | 15 | 193 | 214 | 23 |
| r2_lag7 | 15 | 194 | 216 | 15 |
| r2_leaf_ablated | 15 | 191 | 218 | 28 |
| r2_station | 15 | 187 | 213 | 27 |
| r3_cbh | 15 | 208 | 227 | 29 |
| r3_cbh_shuffled | 15 | 206 | 236 | 29 |
| r3_curing | 15 | 208 | 228 | 27 |
| r3_curing_shuffled | 15 | 207 | 234 | 27 |
| r3_fmc | 15 | 203 | 231 | 29 |
| r3_fmc_shuffled | 15 | 212 | 231 | 29 |
| r3_pc | 15 | 210 | 236 | 27 |
| r3_pc_fmc_cbh | 15 | 215 | 237 | 30 |
| r3_pc_fmc_cbh_shuffled | 15 | 215 | 246 | 29 |
| r3_pc_shuffled | 15 | 211 | 242 | 29 |
| r4 | 15 | 204 | 227 | 20 |
| r4_shuffled | 15 | 205 | 235 | 29 |
