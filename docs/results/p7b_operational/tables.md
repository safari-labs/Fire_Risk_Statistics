# P7b tables: against the CFFDRS values CWFIS actually issued (E-55)

Rows marked ISSUED by CWFIS are values CWFIS published; 'reconstructed' rows are ours.

Development patches with a CWFIS FWI value and both reconstructed sources: 181 (83 fire). Not covered (dated before 2018): 6; covered but not issued: 7.

## T-auc: between-patch AUC by FWI source

| source | n | AUC | 95 % CI | same-year pairs | minus issued grid | 95 % CI | AUC, not-issued as 0 |
|---|---|---|---|---|---|---|---|
| ISSUED by CWFIS: FWI grid (patch mean) | 181 | 0.860 | [0.798, 0.915] | 0.744 | +0.000 | [0.000, 0.000] | 0.868 |
| ISSUED by CWFIS: FWI grid (patch centre) | 180 | 0.860 | [0.799, 0.916] | 0.742 | +0.000 | [-0.004, 0.005] | 0.868 |
| Reconstructed (ours): ERA5-Land FWI, R0's weather | 181 | 0.851 | [0.783, 0.906] | 0.799 | -0.009 | [-0.073, 0.057] | 0.853 |
| ISSUED by CWFIS: FWI at the nearest station | 181 | 0.847 | [0.782, 0.903] | 0.718 | -0.012 | [-0.063, 0.043] | 0.851 |
| ISSUED by CWFIS: fire danger class (majority) | 181 | 0.851 | [0.788, 0.910] | 0.806 | -0.009 | [-0.035, 0.021] | 0.851 |

## T-agree: agreement with the FWI grid ISSUED by CWFIS (patch mean)

| source | n | Spearman rho | 95 % CI | median (source - issued grid) | median absolute difference |
|---|---|---|---|---|---|
| Reconstructed (ours): ERA5 FWI | 181 | 0.76 | [0.63, 0.85] | -3.6 | 4.8 |
| ISSUED by CWFIS: FWI at the nearest station | 181 | 0.84 | [0.77, 0.90] | -0.0 | 2.6 |
| ISSUED by CWFIS: grid centre cell (check) | 180 | 1.00 | [0.99, 1.00] | -0.0 | 0.1 |

## T-ladder: our rungs against the FWI ISSUED by CWFIS (per fold, between patches)

| rung | between-patch AUC | minus issued FWI | 95 % CI |
|---|---|---|---|
| ISSUED by CWFIS: FWI | 0.857 | +0.000 | [0.000, 0.000] |
| Reconstructed (ours): ERA5 FWI | 0.849 | -0.007 | [-0.074, 0.056] |
| Reconstructed (ours): R0 | 0.873 | +0.016 | [-0.048, 0.077] |
| Reconstructed (ours): R1 | 0.899 | +0.042 | [-0.020, 0.104] |
| Reconstructed (ours): R2 | 0.892 | +0.035 | [-0.034, 0.100] |
| Reconstructed (ours): R4 | 0.891 | +0.035 | [-0.033, 0.101] |
