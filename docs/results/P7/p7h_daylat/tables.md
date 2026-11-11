# P7h tables: latitude-correct day length under R2 (E-19)

Run: `narval_results\slots_e19\20261111-0021`. Reconstructed (ours).

| | within | between |
|---|---|---|
| r2_daylat - r2, all development patches | -0.0007 [-0.0024, 0.0010] | -0.0034 [-0.0123, 0.0064] |
| interaction: (60-90 N) - (0-55 N) | +0.0034 [-0.0005, 0.0076] | -0.0033 [-0.0126, 0.0053] |

| metric | band | patches | r2_daylat - r2 [95 % CI] |
|---|---|---|---|
| between | 0-55 N | 78 | -0.0032 [-0.0096, 0.0026] |
| between | 55-60 N | 71 | -0.0014 [-0.0062, 0.0036] |
| between | 60-90 N | 45 | -0.0065 [-0.0145, -0.0006] |
| within | 0-55 N | 30 | -0.0034 [-0.0061, -0.0009] |
| within | 55-60 N | 34 | +0.0013 [-0.0016, 0.0042] |
| within | 60-90 N | 19 | -0.0001 [-0.0030, 0.0032] |
