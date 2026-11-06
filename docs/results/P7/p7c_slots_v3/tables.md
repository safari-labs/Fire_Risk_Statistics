# P7c tables: the second slot sweep (slots_v3)

Run: `narval_results\slots_v3\20261026-2121`. 194 development patches, 5 folds x 3 seeds; r2_warm lacks fold 4 seeds 1-2 (OOM-killed at 16G). Every number is our reconstruction unless marked ISSUED by CWFIS.

## E-58: R2's gap to R1

| rung (ours) | within-patch AUC | 95 % CI | between-patch AUC | 95 % CI |
|---|---|---|---|---|
| R1  learned on CFFDRS inputs | 0.719 | [0.689, 0.748] | 0.886 | [0.825, 0.930] |
| R2  zero start (rerun) | 0.695 | [0.668, 0.721] | 0.880 | [0.817, 0.926] |
| R2  residual started from R1 | 0.687 | [0.662, 0.712] | 0.892 | [0.836, 0.936] |
| R2  residual at 10x rate | 0.663 | [0.638, 0.690] | 0.877 | [0.816, 0.924] |

| a - b | within | 95 % CI | folds won | between | 95 % CI | folds won |
|---|---|---|---|---|---|---|
| r2 - r1 | -0.0246 | [-0.0343, -0.0145] | 0/5 | -0.0063 | [-0.0277, 0.0147] | 2/5 |
| r2_warm - r1 | -0.0327 | [-0.0479, -0.0191] | 0/5 | +0.0058 | [-0.0136, 0.0243] | 3/5 |
| r2_lr10 - r1 | -0.0561 | [-0.0746, -0.0380] | 0/5 | -0.0093 | [-0.0270, 0.0068] | 1/5 |
| r2_warm - r2 | -0.0081 | [-0.0227, 0.0048] | 2/5 | +0.0121 | [-0.0040, 0.0268] | 3/5 |
| r2_lr10 - r2 | -0.0315 | [-0.0470, -0.0157] | 0/5 | -0.0030 | [-0.0194, 0.0126] | 2/5 |

Between-patch reference, FWI ISSUED by CWFIS for D-1 (per fold, 188 covered patches): 0.857.

## E-57: percent conifer with an imagery-free offset

| comparison | pixels | n fires | within-patch change | 95 % CI |
|---|---|---|---|---|
| r3_pc_offset - r3_pc_offset_shuffled | all pixels | 83 | +0.0007 | [-0.0018, 0.0031] |
| r3_pc_offset - r2 | all pixels | 83 | -0.0003 | [-0.0038, 0.0032] |
| r3_pc_offset_shuffled - r2 | all pixels | 83 | -0.0010 | [-0.0034, 0.0012] |
| r3_pc_offset - r3_pc_offset_shuffled | M-1/M-2 pixels | 83 | +0.0065 | [0.0003, 0.0131] |
| r3_pc_offset - r2 | M-1/M-2 pixels | 83 | +0.0009 | [-0.0077, 0.0086] |
| r3_pc_offset_shuffled - r2 | M-1/M-2 pixels | 83 | -0.0056 | [-0.0107, -0.0008] |

r3_pc_offset: learned offset median -6.4 points [-9.1, -2.9]; imagery part on seeded tiles: median tile mean -23.72, median within-tile SD 6.16 (90 tiles).

r3_pc_offset_shuffled: learned offset median -0.8 points [-2.2, +1.1]; imagery part on seeded tiles: median tile mean -29.82, median within-tile SD 0.39 (90 tiles).

## E-38: curing on CWFIS fuel

| comparison | pixels | n fires | within-patch change | 95 % CI |
|---|---|---|---|---|
| r3_curing_cwfis - r3_curing_cwfis_shuffled | O-1 pixels | 60 | +0.0206 | [0.0072, 0.0335] |
| r3_curing_cwfis - r2_cwfis | O-1 pixels | 60 | +0.0129 | [0.0015, 0.0244] |
| r3_curing_cwfis_shuffled - r2_cwfis | O-1 pixels | 60 | -0.0077 | [-0.0163, -0.0002] |
| r3_curing_cwfis - r3_curing_cwfis_shuffled | all pixels | 83 | -0.0002 | [-0.0044, 0.0037] |
| r3_curing_cwfis - r2_cwfis | all pixels | 83 | +0.0000 | [-0.0039, 0.0037] |
| r3_curing_cwfis_shuffled - r2_cwfis | all pixels | 83 | +0.0002 | [-0.0023, 0.0026] |

Pooled AUC on O-1 pixels (mean over fits): r2_cwfis 0.782 (median 906,554 O-1 px per fold); r3_curing_cwfis 0.797 (median 906,554 O-1 px per fold); r3_curing_cwfis_shuffled 0.786 (median 906,554 O-1 px per fold).

## Resources (A100; per task of up to 3 fits)

| measure | median | max |
|---|---|---|
| task length (min) | 10 | 17 |
| GPU utilisation (%) | 25 | 47 |
| peak GPU memory (MiB) | 1125 | 1547 |
| node CPU utilisation (%) | 32 | 46 |
| setup (s) | 38 | 75 |

| configuration | fits | median wall (s) | max wall (s) |
|---|---|---|---|
| r1 | 15 | 153 | 169 |
| r2 | 15 | 198 | 217 |
| r2_cwfis | 15 | 197 | 217 |
| r2_lr10 | 15 | 199 | 222 |
| r2_warm | 13 | 338 | 373 |
| r3_curing_cwfis | 15 | 224 | 245 |
| r3_curing_cwfis_shuffled | 15 | 215 | 233 |
| r3_pc_offset | 15 | 222 | 243 |
| r3_pc_offset_shuffled | 15 | 217 | 253 |
