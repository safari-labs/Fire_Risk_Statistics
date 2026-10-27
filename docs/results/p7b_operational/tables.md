# P7b tables: the operational CFFDRS reference (E-55)

Development patches with a CWFIS FWI value and both reconstructed sources: 181 (83 fire). Not covered (dated before 2018): 6; covered but not issued: 7.

## T-auc: between-patch AUC by FWI source

| source | n | AUC | 95 % CI | same-year pairs | minus operational | 95 % CI | AUC, not-issued as 0 |
|---|---|---|---|---|---|---|---|
| CWFIS operational FWI grid (patch mean) | 181 | 0.860 | [0.798, 0.915] | 0.744 | +0.000 | [0.000, 0.000] | 0.868 |
| CWFIS operational FWI grid (patch centre) | 180 | 0.860 | [0.799, 0.916] | 0.742 | +0.000 | [-0.004, 0.005] | 0.868 |
| ERA5-Land FWI, 13:00 LDT (ours, R0's weather) | 181 | 0.851 | [0.783, 0.906] | 0.799 | -0.009 | [-0.073, 0.057] | 0.853 |
| Nearest CWFIS station FWI | 181 | 0.847 | [0.782, 0.903] | 0.718 | -0.012 | [-0.063, 0.043] | 0.851 |
| CWFIS fire danger class (majority) | 181 | 0.851 | [0.788, 0.910] | 0.806 | -0.009 | [-0.035, 0.021] | 0.851 |

## T-agree: agreement with the operational grid (patch mean)

| source | n | Spearman rho | 95 % CI | median (source - operational) | median absolute difference |
|---|---|---|---|---|---|
| era5 | 181 | 0.76 | [0.63, 0.85] | -3.6 | 4.8 |
| station | 181 | 0.84 | [0.77, 0.90] | -0.0 | 2.6 |
| op_c | 180 | 1.00 | [0.99, 1.00] | -0.0 | 0.1 |

## T-ladder: rungs against the operational FWI (per fold, between patches)

| rung | between-patch AUC | minus operational | 95 % CI |
|---|---|---|---|
| CWFIS operational FWI (issued) | 0.857 | +0.000 | [0.000, 0.000] |
| ERA5 FWI (ours) | 0.849 | -0.007 | [-0.074, 0.056] |
| R0  physics only (HFI) | 0.873 | +0.016 | [-0.048, 0.077] |
| R1  learned on CFFDRS inputs | 0.899 | +0.042 | [-0.020, 0.104] |
| R2  physics + learned residual | 0.892 | +0.035 | [-0.034, 0.100] |
| R4  R2 + free imagery branch | 0.891 | +0.035 | [-0.033, 0.101] |
