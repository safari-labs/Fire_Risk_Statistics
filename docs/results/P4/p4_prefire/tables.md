# P4 tables: pre-fire imagery, dated labels, the v2 pack

Development patches: 196 (test patches excluded: 35).

## T-composite: window used, by patch kind

| kind | D-45..D-1 | D-90..D-1 | fallback | median coverage | median clear obs |
|---|---|---|---|---|---|
| fire | 82 | 0 | 1 | 1.000 | 7 |
| confuser | 67 | 6 | 18 | 1.000 | 5 |
| unburned | 16 | 0 | 6 | 1.000 | 9 |

## T-leak: E-54

| fires | n | mean diff-in-diff | 95 % CI | share negative |
|---|---|---|---|---|
| started before 30 June | 54 | -0.0605 | [-0.0809, -0.0410] | 0.83 |
| started 30 June or later | 29 | -0.0822 | [-0.1222, -0.0494] | 0.79 |

Control (added after registration): the same, minus the same-place confuser at the same pixels.

| fires | n | mean | 95 % CI | share negative |
|---|---|---|---|---|
| started before 30 June | 41 | -0.0051 | [-0.0326, 0.0232] | 0.56 |
| started 30 June or later | 25 | +0.0049 | [-0.0311, 0.0435] | 0.56 |

Spearman rho (overlap days, diff-in-diff): +0.054 [-0.203, 0.302], 83 fire patches.

## T-labels: dated NBAC labels

| kind | patches | mean burned on/after D | mean ignored |
|---|---|---|---|
| fire | 83 | 0.656 | 0.0000 |
| confuser | 91 | 0.005 | 0.0000 |
| unburned | 22 | 0.000 | 0.0000 |

## T-pack: the v2 pack

| split | patches | tiles |
|---|---|---|
| train | 162 | 1388 |
| val | 32 | 283 |
| test | 33 | 287 |
