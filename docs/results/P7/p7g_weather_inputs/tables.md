# P7g tables: weather age, one input at a time (E-20)

Run: `narval_results\lags_v2\20261111-0021`. Reconstructed (ours).

## The registered contrast: fast codes against slow codes

| configuration | metric | contrast | lag | difference [95 % CI] | folds below 0 | fits |
|---|---|---|---|---|---|---|
| R2, trained on D-1 weather | within patches | mean(FFMC, ISI aged) - mean(DC, BUI aged) | 3 | -0.0008 [-0.0047, +0.0021] | 2/5 | 15 |
| R2, trained on D-1 weather | within patches | mean(FFMC, ISI aged) - mean(DC, BUI aged) | 7 | +0.0014 [-0.0022, +0.0048] | 1/5 | 15 |
| R2, trained on D-1 weather | between patches | mean(FFMC, ISI aged) - mean(DC, BUI aged) | 3 | -0.0199 [-0.0272, -0.0117] | 5/5 | 15 |
| R2, trained on D-1 weather | between patches | mean(FFMC, ISI aged) - mean(DC, BUI aged) | 7 | -0.0120 [-0.0214, -0.0005] | 4/5 | 15 |
| R0 HFI, physics only | within patches | mean(FFMC, ISI aged) - mean(DC, BUI aged) | 3 | -0.0012 [-0.0022, +0.0001] | 4/5 | 5 |
| R0 HFI, physics only | within patches | mean(FFMC, ISI aged) - mean(DC, BUI aged) | 7 | +0.0001 [-0.0030, +0.0031] | 2/5 | 5 |
| R0 HFI, physics only | between patches | mean(FFMC, ISI aged) - mean(DC, BUI aged) | 3 | -0.0440 [-0.0566, -0.0328] | 5/5 | 5 |
| R0 HFI, physics only | between patches | mean(FFMC, ISI aged) - mean(DC, BUI aged) | 7 | -0.0268 [-0.0442, -0.0055] | 4/5 | 5 |

## Each input aged alone, minus all inputs at D-1

| configuration | metric | input | lag | change [95 % CI] | folds below 0 | fits |
|---|---|---|---|---|---|---|
| R2, trained on D-1 weather | within patches | FFMC | 2 | -0.0022 [-0.0064, +0.0020] | 3/5 | 15 |
| R2, trained on D-1 weather | within patches | FFMC | 3 | -0.0019 [-0.0082, +0.0029] | 2/5 | 15 |
| R2, trained on D-1 weather | within patches | FFMC | 7 | +0.0011 [-0.0020, +0.0040] | 1/5 | 15 |
| R2, trained on D-1 weather | within patches | ISI | 2 | +0.0000 [-0.0000, +0.0001] | 2/5 | 15 |
| R2, trained on D-1 weather | within patches | ISI | 3 | +0.0000 [-0.0001, +0.0001] | 2/5 | 15 |
| R2, trained on D-1 weather | within patches | ISI | 7 | -0.0001 [-0.0003, +0.0001] | 3/5 | 15 |
| R2, trained on D-1 weather | within patches | DMC | 2 | +0.0000 [+0.0000, +0.0001] | 1/5 | 15 |
| R2, trained on D-1 weather | within patches | DMC | 3 | +0.0001 [+0.0000, +0.0002] | 0/5 | 15 |
| R2, trained on D-1 weather | within patches | DMC | 7 | +0.0002 [+0.0001, +0.0002] | 0/5 | 15 |
| R2, trained on D-1 weather | within patches | DC | 2 | +0.0000 [-0.0000, +0.0000] | 3/5 | 15 |
| R2, trained on D-1 weather | within patches | DC | 3 | +0.0000 [+0.0000, +0.0000] | 1/5 | 15 |
| R2, trained on D-1 weather | within patches | DC | 7 | -0.0000 [-0.0000, +0.0000] | 3/5 | 15 |
| R2, trained on D-1 weather | within patches | BUI | 2 | -0.0002 [-0.0010, +0.0006] | 3/5 | 15 |
| R2, trained on D-1 weather | within patches | BUI | 3 | -0.0004 [-0.0021, +0.0011] | 2/5 | 15 |
| R2, trained on D-1 weather | within patches | BUI | 7 | -0.0018 [-0.0071, +0.0024] | 3/5 | 15 |
| R2, trained on D-1 weather | within patches | FWI | 2 | +0.0002 [-0.0001, +0.0006] | 1/5 | 15 |
| R2, trained on D-1 weather | within patches | FWI | 3 | -0.0006 [-0.0012, -0.0000] | 4/5 | 15 |
| R2, trained on D-1 weather | within patches | FWI | 7 | -0.0007 [-0.0018, +0.0000] | 4/5 | 15 |
| R2, trained on D-1 weather | within patches | wind + RH | 2 | -0.0004 [-0.0018, +0.0009] | 3/5 | 15 |
| R2, trained on D-1 weather | within patches | wind + RH | 3 | +0.0016 [+0.0006, +0.0028] | 0/5 | 15 |
| R2, trained on D-1 weather | within patches | wind + RH | 7 | -0.0011 [-0.0026, +0.0004] | 3/5 | 15 |
| R2, trained on D-1 weather | between patches | FFMC | 2 | -0.0195 [-0.0435, +0.0054] | 4/5 | 15 |
| R2, trained on D-1 weather | between patches | FFMC | 3 | -0.0349 [-0.0520, -0.0203] | 5/5 | 15 |
| R2, trained on D-1 weather | between patches | FFMC | 7 | -0.0228 [-0.0425, +0.0027] | 4/5 | 15 |
| R2, trained on D-1 weather | between patches | ISI | 2 | -0.0039 [-0.0072, -0.0003] | 4/5 | 15 |
| R2, trained on D-1 weather | between patches | ISI | 3 | -0.0033 [-0.0070, +0.0021] | 4/5 | 15 |
| R2, trained on D-1 weather | between patches | ISI | 7 | -0.0027 [-0.0082, +0.0028] | 3/5 | 15 |
| R2, trained on D-1 weather | between patches | DMC | 2 | +0.0006 [-0.0016, +0.0028] | 2/5 | 15 |
| R2, trained on D-1 weather | between patches | DMC | 3 | -0.0024 [-0.0057, +0.0006] | 3/5 | 15 |
| R2, trained on D-1 weather | between patches | DMC | 7 | +0.0034 [-0.0022, +0.0081] | 1/5 | 15 |
| R2, trained on D-1 weather | between patches | DC | 2 | -0.0005 [-0.0017, +0.0003] | 2/5 | 15 |
| R2, trained on D-1 weather | between patches | DC | 3 | -0.0009 [-0.0017, -0.0002] | 3/5 | 15 |
| R2, trained on D-1 weather | between patches | DC | 7 | -0.0019 [-0.0026, -0.0009] | 4/5 | 15 |
| R2, trained on D-1 weather | between patches | BUI | 2 | +0.0006 [-0.0075, +0.0080] | 2/5 | 15 |
| R2, trained on D-1 weather | between patches | BUI | 3 | +0.0025 [-0.0036, +0.0101] | 2/5 | 15 |
| R2, trained on D-1 weather | between patches | BUI | 7 | +0.0003 [-0.0132, +0.0142] | 3/5 | 15 |
| R2, trained on D-1 weather | between patches | FWI | 2 | -0.0026 [-0.0051, -0.0000] | 4/5 | 15 |
| R2, trained on D-1 weather | between patches | FWI | 3 | -0.0038 [-0.0092, +0.0012] | 3/5 | 15 |
| R2, trained on D-1 weather | between patches | FWI | 7 | -0.0043 [-0.0117, +0.0010] | 3/5 | 15 |
| R2, trained on D-1 weather | between patches | wind + RH | 2 | +0.0008 [-0.0023, +0.0046] | 3/5 | 15 |
| R2, trained on D-1 weather | between patches | wind + RH | 3 | -0.0045 [-0.0106, +0.0030] | 4/5 | 15 |
| R2, trained on D-1 weather | between patches | wind + RH | 7 | -0.0037 [-0.0083, +0.0006] | 3/5 | 15 |
| R0 HFI, physics only | within patches | FFMC | 2 | -0.0022 [-0.0053, +0.0017] | 4/5 | 5 |
| R0 HFI, physics only | within patches | FFMC | 3 | -0.0040 [-0.0066, -0.0009] | 4/5 | 5 |
| R0 HFI, physics only | within patches | FFMC | 7 | -0.0028 [-0.0058, +0.0002] | 4/5 | 5 |
| R0 HFI, physics only | within patches | ISI | 2 | +0.0000 [+0.0000, +0.0000] | 0/5 | 5 |
| R0 HFI, physics only | within patches | ISI | 3 | +0.0000 [+0.0000, +0.0000] | 0/5 | 5 |
| R0 HFI, physics only | within patches | ISI | 7 | +0.0000 [+0.0000, +0.0000] | 0/5 | 5 |
| R0 HFI, physics only | within patches | DMC | 2 | +0.0000 [+0.0000, +0.0000] | 0/5 | 5 |
| R0 HFI, physics only | within patches | DMC | 3 | +0.0000 [+0.0000, +0.0000] | 0/5 | 5 |
| R0 HFI, physics only | within patches | DMC | 7 | +0.0000 [+0.0000, +0.0000] | 0/5 | 5 |
| R0 HFI, physics only | within patches | DC | 2 | +0.0000 [+0.0000, +0.0000] | 0/5 | 5 |
| R0 HFI, physics only | within patches | DC | 3 | +0.0000 [+0.0000, +0.0000] | 0/5 | 5 |
| R0 HFI, physics only | within patches | DC | 7 | +0.0000 [+0.0000, +0.0000] | 0/5 | 5 |
| R0 HFI, physics only | within patches | BUI | 2 | -0.0006 [-0.0013, -0.0002] | 5/5 | 5 |
| R0 HFI, physics only | within patches | BUI | 3 | -0.0015 [-0.0032, +0.0002] | 4/5 | 5 |
| R0 HFI, physics only | within patches | BUI | 7 | -0.0031 [-0.0104, +0.0020] | 3/5 | 5 |
| R0 HFI, physics only | within patches | FWI | 2 | +0.0000 [+0.0000, +0.0000] | 0/5 | 5 |
| R0 HFI, physics only | within patches | FWI | 3 | +0.0000 [+0.0000, +0.0000] | 0/5 | 5 |
| R0 HFI, physics only | within patches | FWI | 7 | +0.0000 [+0.0000, +0.0000] | 0/5 | 5 |
| R0 HFI, physics only | within patches | wind + RH | 2 | -0.0017 [-0.0031, -0.0003] | 4/5 | 5 |
| R0 HFI, physics only | within patches | wind + RH | 3 | +0.0003 [-0.0012, +0.0017] | 2/5 | 5 |
| R0 HFI, physics only | within patches | wind + RH | 7 | -0.0016 [-0.0045, +0.0017] | 4/5 | 5 |
| R0 HFI, physics only | between patches | FFMC | 2 | -0.0296 [-0.0671, +0.0048] | 4/5 | 5 |
| R0 HFI, physics only | between patches | FFMC | 3 | -0.0762 [-0.0993, -0.0551] | 5/5 | 5 |
| R0 HFI, physics only | between patches | FFMC | 7 | -0.0359 [-0.0875, +0.0168] | 4/5 | 5 |
| R0 HFI, physics only | between patches | ISI | 2 | +0.0000 [+0.0000, +0.0000] | 0/5 | 5 |
| R0 HFI, physics only | between patches | ISI | 3 | +0.0000 [+0.0000, +0.0000] | 0/5 | 5 |
| R0 HFI, physics only | between patches | ISI | 7 | +0.0000 [+0.0000, +0.0000] | 0/5 | 5 |
| R0 HFI, physics only | between patches | DMC | 2 | +0.0000 [+0.0000, +0.0000] | 0/5 | 5 |
| R0 HFI, physics only | between patches | DMC | 3 | +0.0000 [+0.0000, +0.0000] | 0/5 | 5 |
| R0 HFI, physics only | between patches | DMC | 7 | +0.0000 [+0.0000, +0.0000] | 0/5 | 5 |
| R0 HFI, physics only | between patches | DC | 2 | +0.0000 [+0.0000, +0.0000] | 0/5 | 5 |
| R0 HFI, physics only | between patches | DC | 3 | +0.0000 [+0.0000, +0.0000] | 0/5 | 5 |
| R0 HFI, physics only | between patches | DC | 7 | +0.0000 [+0.0000, +0.0000] | 0/5 | 5 |
| R0 HFI, physics only | between patches | BUI | 2 | +0.0045 [+0.0000, +0.0095] | 0/5 | 5 |
| R0 HFI, physics only | between patches | BUI | 3 | +0.0118 [+0.0035, +0.0222] | 0/5 | 5 |
| R0 HFI, physics only | between patches | BUI | 7 | +0.0176 [-0.0007, +0.0358] | 1/5 | 5 |
| R0 HFI, physics only | between patches | FWI | 2 | +0.0000 [+0.0000, +0.0000] | 0/5 | 5 |
| R0 HFI, physics only | between patches | FWI | 3 | +0.0000 [+0.0000, +0.0000] | 0/5 | 5 |
| R0 HFI, physics only | between patches | FWI | 7 | +0.0000 [+0.0000, +0.0000] | 0/5 | 5 |
| R0 HFI, physics only | between patches | wind + RH | 2 | -0.0084 [-0.0183, +0.0002] | 3/5 | 5 |
| R0 HFI, physics only | between patches | wind + RH | 3 | +0.0025 [-0.0062, +0.0142] | 3/5 | 5 |
| R0 HFI, physics only | between patches | wind + RH | 7 | -0.0026 [-0.0143, +0.0117] | 3/5 | 5 |
