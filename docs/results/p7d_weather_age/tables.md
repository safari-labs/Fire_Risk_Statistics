# P7d tables: weather age (E-20)

Run: `narval_results\lags_v1\20261105-1625`. Reconstructed (ours).

## AUC at each weather age

| configuration | metric | lag (days) | AUC [95 % CI] | folds below 0 | fits |
|---|---|---|---|---|---|
| R0 HFI, physics only (SCANFI fuel) | within patches | 1 | +0.6708 [+0.6493, +0.6964] | 0/5 | 5 |
| R0 HFI, physics only (SCANFI fuel) | within patches | 2 | +0.6671 [+0.6461, +0.6925] | 0/5 | 5 |
| R0 HFI, physics only (SCANFI fuel) | within patches | 3 | +0.6671 [+0.6470, +0.6937] | 0/5 | 5 |
| R0 HFI, physics only (SCANFI fuel) | within patches | 7 | +0.6635 [+0.6451, +0.6916] | 0/5 | 5 |
| R0 HFI, physics only (SCANFI fuel) | between patches | 1 | +0.8582 [+0.8024, +0.9151] | 0/5 | 5 |
| R0 HFI, physics only (SCANFI fuel) | between patches | 2 | +0.8138 [+0.7541, +0.8768] | 0/5 | 5 |
| R0 HFI, physics only (SCANFI fuel) | between patches | 3 | +0.7655 [+0.7013, +0.8337] | 0/5 | 5 |
| R0 HFI, physics only (SCANFI fuel) | between patches | 7 | +0.7974 [+0.7503, +0.8421] | 0/5 | 5 |
| R2, trained on D-1 weather | within patches | 1 | +0.6970 [+0.6725, +0.7227] | 0/5 | 15 |
| R2, trained on D-1 weather | within patches | 2 | +0.6947 [+0.6700, +0.7221] | 0/5 | 15 |
| R2, trained on D-1 weather | within patches | 3 | +0.6965 [+0.6674, +0.7256] | 0/5 | 15 |
| R2, trained on D-1 weather | within patches | 7 | +0.6968 [+0.6720, +0.7236] | 0/5 | 15 |
| R2, trained on D-1 weather | between patches | 1 | +0.8767 [+0.8380, +0.9155] | 0/5 | 15 |
| R2, trained on D-1 weather | between patches | 2 | +0.8541 [+0.8009, +0.8984] | 0/5 | 15 |
| R2, trained on D-1 weather | between patches | 3 | +0.8216 [+0.7799, +0.8633] | 0/5 | 15 |
| R2, trained on D-1 weather | between patches | 7 | +0.8254 [+0.7959, +0.8587] | 0/5 | 15 |
| R2, trained on 7-day-old weather | within patches | 1 | +0.6794 [+0.6572, +0.7037] | 0/5 | 15 |
| R2, trained on 7-day-old weather | within patches | 2 | +0.6741 [+0.6511, +0.6970] | 0/5 | 15 |
| R2, trained on 7-day-old weather | within patches | 3 | +0.6743 [+0.6475, +0.7012] | 0/5 | 15 |
| R2, trained on 7-day-old weather | within patches | 7 | +0.6767 [+0.6563, +0.7010] | 0/5 | 15 |
| R2, trained on 7-day-old weather | between patches | 1 | +0.8564 [+0.8096, +0.9096] | 0/5 | 15 |
| R2, trained on 7-day-old weather | between patches | 2 | +0.8303 [+0.7686, +0.8920] | 0/5 | 15 |
| R2, trained on 7-day-old weather | between patches | 3 | +0.7997 [+0.7398, +0.8597] | 0/5 | 15 |
| R2, trained on 7-day-old weather | between patches | 7 | +0.8201 [+0.7896, +0.8496] | 0/5 | 15 |

## Decay: lag k minus lag 1, within the same fit

| configuration | metric | lag (days) | change [95 % CI] | folds below 0 | fits |
|---|---|---|---|---|---|
| R0 HFI, physics only (SCANFI fuel) | within patches | 2 | -0.0037 [-0.0067, +0.0009] | 4/5 | 5 |
| R0 HFI, physics only (SCANFI fuel) | within patches | 3 | -0.0037 [-0.0070, -0.0009] | 5/5 | 5 |
| R0 HFI, physics only (SCANFI fuel) | within patches | 7 | -0.0073 [-0.0165, -0.0008] | 4/5 | 5 |
| R0 HFI, physics only (SCANFI fuel) | between patches | 2 | -0.0443 [-0.0751, -0.0148] | 4/5 | 5 |
| R0 HFI, physics only (SCANFI fuel) | between patches | 3 | -0.0927 [-0.1130, -0.0746] | 5/5 | 5 |
| R0 HFI, physics only (SCANFI fuel) | between patches | 7 | -0.0608 [-0.1342, +0.0159] | 4/5 | 5 |
| R2, trained on D-1 weather | within patches | 2 | -0.0023 [-0.0059, +0.0011] | 2/5 | 15 |
| R2, trained on D-1 weather | within patches | 3 | -0.0006 [-0.0066, +0.0043] | 2/5 | 15 |
| R2, trained on D-1 weather | within patches | 7 | -0.0003 [-0.0023, +0.0017] | 2/5 | 15 |
| R2, trained on D-1 weather | between patches | 2 | -0.0226 [-0.0561, +0.0120] | 4/5 | 15 |
| R2, trained on D-1 weather | between patches | 3 | -0.0550 [-0.0745, -0.0339] | 5/5 | 15 |
| R2, trained on D-1 weather | between patches | 7 | -0.0512 [-0.0911, -0.0111] | 4/5 | 15 |
| R2, trained on 7-day-old weather | within patches | 2 | -0.0053 [-0.0099, -0.0008] | 4/5 | 15 |
| R2, trained on 7-day-old weather | within patches | 3 | -0.0050 [-0.0126, +0.0003] | 4/5 | 15 |
| R2, trained on 7-day-old weather | within patches | 7 | -0.0027 [-0.0084, +0.0018] | 3/5 | 15 |
| R2, trained on 7-day-old weather | between patches | 2 | -0.0260 [-0.0655, +0.0129] | 4/5 | 15 |
| R2, trained on 7-day-old weather | between patches | 3 | -0.0566 [-0.0878, -0.0305] | 5/5 | 15 |
| R2, trained on 7-day-old weather | between patches | 7 | -0.0362 [-0.0896, +0.0217] | 4/5 | 15 |

## Training on stale weather: r2_age7 minus r2, same fold and seed

| contrast | metric | scored at lag | difference [95 % CI] | folds below 0 | pairs |
|---|---|---|---|---|---|
| r2_age7 minus r2 (same fold and seed) | within patches | 1 | -0.0176 [-0.0256, -0.0092] | 5/5 | 15 |
| r2_age7 minus r2 (same fold and seed) | within patches | 2 | -0.0206 [-0.0302, -0.0098] | 5/5 | 15 |
| r2_age7 minus r2 (same fold and seed) | within patches | 3 | -0.0221 [-0.0335, -0.0093] | 5/5 | 15 |
| r2_age7 minus r2 (same fold and seed) | within patches | 7 | -0.0200 [-0.0268, -0.0108] | 5/5 | 15 |
| r2_age7 minus r2 (same fold and seed) | between patches | 1 | -0.0203 [-0.0498, -0.0036] | 5/5 | 15 |
| r2_age7 minus r2 (same fold and seed) | between patches | 2 | -0.0238 [-0.0547, +0.0028] | 4/5 | 15 |
| r2_age7 minus r2 (same fold and seed) | between patches | 3 | -0.0219 [-0.0434, -0.0034] | 4/5 | 15 |
| r2_age7 minus r2 (same fold and seed) | between patches | 7 | -0.0053 [-0.0275, +0.0177] | 2/5 | 15 |
