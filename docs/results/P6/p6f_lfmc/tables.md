# P6f tables: LFMC retrievals against Globe-LFMC (E-64, E-29)

Run: `narval_results\lfmc_v1\20261103-2123`, 3 seeds. Development sites only; the frozen 15 % of sites (`lfmc_test_sites_v1.json`) was not read. Squared errors and predictions are averaged over seeds per record. CIs: 2,000 bootstrap draws over sites. All values are Reconstructed (ours).

## Registered contrasts (RMSE difference, LFMC points)

| contrast | records | sites | difference | 95 % CI |
|---|---|---|---|---|
| E-64a sim GP - FBP (conifer) | 1,584 | 31 | +26.01 | [22.42, 29.32] |
| E-64a best empirical - FBP (conifer) | 1,584 | 31 | +0.56 | [-0.09, 1.16] |
| E-64b sim GP - best empirical (conifer) | 1,584 | 31 | +25.45 | [22.08, 28.39] |
| E-29 sim GP: no B12 - all 10 (jack, red pine) | 1,469 | 24 | +1.68 | [0.36, 3.21] |
| E-29 sim MLP: no B12 - all 10 (jack, red pine) | 1,469 | 24 | +7.42 | [1.70, 15.58] |
| E-29 sim GP, April-June | 992 | 23 | +1.74 | [0.06, 3.72] |
| E-29 sim GP, July-September | 427 | 24 | +1.35 | [0.01, 2.84] |
| sim MLP - FBP (conifer) | 1,584 | 31 | +18.42 | [12.62, 24.66] |

## all (1,739 records, 37 sites)

| model | RMSE | bias | R2 |
|---|---|---|---|
| FBP foliar moisture equation | 20.6 | -8.2 | -0.00 |
| simulation GP, 10 bands (of record) | 42.3 | +32.0 | -2.91 |
| simulation MLP, 10 bands | 37.8 | +17.5 | -2.33 |
| simulation GP, no B12 | 44.6 | +33.5 | -3.31 |
| simulation MLP, no B12 | 43.1 | +18.8 | -3.35 |
| simulation GP, VNIR only | 50.3 | +46.6 | -4.85 |
| simulation MLP, VNIR only | 49.5 | +46.3 | -4.75 |
| simulation GP, trained noise-free | 263.4 | +98.3 | -158.26 |
| NDMI, calibrated | 18.4 | -1.0 | 0.26 |
| MSI, calibrated | 19.1 | -1.1 | 0.23 |
| NMDI, calibrated | 17.7 | -0.3 | 0.27 |
| GP on the 10 bands | 17.7 | -1.0 | 0.28 |
| best empirical, chosen in inner folds | 18.6 | -1.2 | 0.21 |

## conifer (1,584 records, 31 sites)

| model | RMSE | bias | R2 |
|---|---|---|---|
| FBP foliar moisture equation | 14.0 | -5.6 | 0.15 |
| simulation GP, 10 bands (of record) | 40.0 | +31.0 | -5.46 |
| simulation MLP, 10 bands | 32.4 | +14.0 | -3.53 |
| simulation GP, no B12 | 41.7 | +31.7 | -5.97 |
| simulation MLP, no B12 | 39.3 | +15.2 | -5.70 |
| simulation GP, VNIR only | 50.1 | +47.2 | -9.76 |
| simulation MLP, VNIR only | 49.6 | +47.1 | -9.71 |
| simulation GP, trained noise-free | 273.6 | +98.4 | -317.14 |
| NDMI, calibrated | 14.6 | +0.1 | 0.08 |
| MSI, calibrated | 14.5 | +0.1 | 0.08 |
| NMDI, calibrated | 15.3 | -0.0 | -0.02 |
| GP on the 10 bands | 15.2 | -0.6 | 0.01 |
| best empirical, chosen in inner folds | 14.6 | +0.1 | 0.08 |

## deciduous (155 records, 6 sites)

| model | RMSE | bias | R2 |
|---|---|---|---|
| FBP foliar moisture equation | 52.7 | -35.5 | -1.96 |
| simulation GP, 10 bands (of record) | 61.3 | +42.6 | -2.74 |
| simulation MLP, 10 bands | 72.5 | +53.6 | -4.60 |
| simulation GP, no B12 | 67.5 | +50.9 | -3.50 |
| simulation MLP, no B12 | 70.9 | +54.9 | -4.36 |
| simulation GP, VNIR only | 52.3 | +41.1 | -1.84 |
| simulation MLP, VNIR only | 48.4 | +37.3 | -1.49 |
| simulation GP, trained noise-free | 117.8 | +97.1 | -13.19 |
| NDMI, calibrated | 40.5 | -12.3 | -0.47 |
| MSI, calibrated | 44.1 | -13.9 | -0.64 |
| NMDI, calibrated | 33.4 | -3.4 | -0.18 |
| GP on the 10 bands | 33.8 | -5.5 | -0.21 |
| best empirical, chosen in inner folds | 41.6 | -14.4 | -0.71 |

## jack and red pine (1,469 records, 24 sites)

| model | RMSE | bias | R2 |
|---|---|---|---|
| FBP foliar moisture equation | 13.7 | -6.2 | 0.15 |
| simulation GP, 10 bands (of record) | 39.7 | +30.8 | -5.68 |
| simulation MLP, 10 bands | 31.7 | +13.3 | -3.56 |
| simulation GP, no B12 | 41.3 | +31.6 | -6.22 |
| simulation MLP, no B12 | 39.1 | +14.6 | -5.98 |
| simulation GP, VNIR only | 49.4 | +46.7 | -10.04 |
| simulation MLP, VNIR only | 49.2 | +46.7 | -10.05 |
| simulation GP, trained noise-free | 270.0 | +89.9 | -325.10 |
| NDMI, calibrated | 14.1 | -0.6 | 0.09 |
| MSI, calibrated | 14.1 | -0.6 | 0.09 |
| NMDI, calibrated | 15.0 | -0.5 | -0.03 |
| GP on the 10 bands | 14.9 | -0.9 | 0.01 |
| best empirical, chosen in inner folds | 14.1 | -0.5 | 0.09 |

## conifer, April-June (1,051 records, 30 sites)

| model | RMSE | bias | R2 |
|---|---|---|---|
| FBP foliar moisture equation | 14.0 | -7.8 | -0.50 |
| simulation GP, 10 bands (of record) | 44.8 | +39.5 | -13.50 |
| simulation MLP, 10 bands | 34.1 | +19.1 | -7.75 |
| simulation GP, no B12 | 46.6 | +40.7 | -14.57 |
| simulation MLP, no B12 | 43.1 | +21.1 | -13.07 |
| simulation GP, VNIR only | 55.1 | +53.5 | -21.89 |
| simulation MLP, VNIR only | 54.8 | +53.5 | -21.81 |
| simulation GP, trained noise-free | 244.9 | +50.7 | -440.49 |
| NDMI, calibrated | 12.7 | +4.8 | -0.22 |
| MSI, calibrated | 12.7 | +4.8 | -0.23 |
| NMDI, calibrated | 13.0 | +5.9 | -0.29 |
| GP on the 10 bands | 13.2 | +4.4 | -0.28 |
| best empirical, chosen in inner folds | 12.7 | +4.8 | -0.23 |

## conifer, July-September (480 records, 28 sites)

| model | RMSE | bias | R2 |
|---|---|---|---|
| FBP foliar moisture equation | 14.3 | -0.9 | 0.04 |
| simulation GP, 10 bands (of record) | 27.7 | +13.0 | -1.96 |
| simulation MLP, 10 bands | 28.5 | +2.8 | -2.84 |
| simulation GP, no B12 | 29.4 | +12.5 | -2.23 |
| simulation MLP, no B12 | 29.9 | +2.2 | -3.22 |
| simulation GP, VNIR only | 38.6 | +34.8 | -5.82 |
| simulation MLP, VNIR only | 37.8 | +34.8 | -5.76 |
| simulation GP, trained noise-free | 323.7 | +227.1 | -489.81 |
| NDMI, calibrated | 17.4 | -8.2 | -0.43 |
| MSI, calibrated | 17.3 | -8.1 | -0.42 |
| NMDI, calibrated | 19.2 | -11.2 | -0.73 |
| GP on the 10 bands | 18.8 | -9.9 | -0.64 |
| best empirical, chosen in inner folds | 17.4 | -8.1 | -0.42 |

## RMSE per seed, all records (fits.json)

| model | s0 | s1 | s2 |
|---|---|---|---|
| FBP foliar moisture equation | 20.6 | 20.6 | 20.6 |
| simulation GP, 10 bands (of record) | 42.5 | 43.2 | 41.3 |
| simulation MLP, 10 bands | 37.0 | 38.9 | 37.3 |
| simulation GP, no B12 | 45.5 | 45.3 | 43.0 |
| simulation MLP, no B12 | 43.3 | 44.0 | 41.8 |
| simulation GP, VNIR only | 51.3 | 50.7 | 48.9 |
| simulation MLP, VNIR only | 49.3 | 49.7 | 49.6 |
| simulation GP, trained noise-free | 254.9 | 248.7 | 285.3 |
| NDMI, calibrated | 19.4 | 16.3 | 19.4 |
| MSI, calibrated | 20.4 | 16.3 | 20.4 |
| NMDI, calibrated | 17.8 | 17.6 | 17.8 |
| GP on the 10 bands | 17.7 | 17.6 | 17.7 |
| best empirical, chosen in inner folds | 19.4 | 17.0 | 19.4 |

## Best empirical model, chosen inside each outer fold

| fuel group | choices over folds x seeds |
|---|---|
| conifer | MSI 11, NDMI 4 |
| deciduous | MSI 8, NDMI 4, gp 3 |

## Simulation GP band relevance (ARD, mean over seeds; higher = more used)

| group / bands | B2 | B3 | B4 | B5 | B6 | B7 | B8 | B8A | B11 | B12 |
|---|---|---|---|---|---|---|---|---|---|---|
| conifer/all10 | 1.49 | 1.53 | 1.63 | 1.24 | 1.52 | 1.67 | 1.54 | 2.11 | 3.19 | 2.07 |
| deciduous/all10 | 1.82 | 1.77 | 2.58 | 1.89 | 2.21 | 1.98 | 1.92 | 2.24 | 3.13 | 2.61 |
| conifer/no_b12 | 2.29 | 2.00 | 2.25 | 1.75 | 1.70 | 2.12 | 2.14 | 2.16 | 3.56 |  |
| deciduous/no_b12 | 2.39 | 2.73 | 2.80 | 1.96 | 2.05 | 2.43 | 2.98 | 2.27 | 2.72 |  |
| conifer/vnir | 5.04 | 4.57 | 4.55 | 4.54 | 4.33 | 4.50 | 4.55 | 4.93 |  |  |
| deciduous/vnir | 4.96 | 4.48 | 4.63 | 4.34 | 4.56 | 4.33 | 4.46 | 4.58 |  |  |
