# P6d tables: the FWI start-up from Sentinel-2 snow-off (E-18)

Run: `runs\20261030-e18_s2_startup`, with snow-off dates from `narval_results\snow_off\20261030-1126\patch_snowoff.json`. 189 development patches (83 fire; <55 N: 76, 55-60 N: 69, >=60 N: 44). Every code here is Reconstructed (ours), none ISSUED by CWFIS. The frozen test patches were not opened.

## The classifiers, chosen inside the snow training folds

| arm | bands | inner median error (d) |
|---|---|---|
| SWIR allowed | B1, B11, B4, B3 | 10.5 |
| VNIR only | B1, B9, B4 | 13.5 |

189 of 196 patches have a date.

## E-18's registered test: the imagery date against ERA5's C-2 rule

| region | start-up | median lag-1 DC (ERA5 rule) | move | patches moved 10 %+ | season start, median gap (d) | DC AUC change | FWI AUC change |
|---|---|---|---|---|---|---|---|
| >= 55 N | SWIR allowed | 192 (179) | +7.0 % | 36% | -2 | +0.015 [-0.008, 0.040] | +0.002 [-0.009, 0.013] |
| >= 55 N | VNIR only | 143 (179) | -20.2 % | 69% | +6 | -0.025 [-0.082, 0.030] | -0.042 [-0.086, -0.007] |
| < 55 N | SWIR allowed | 101 (92) | +9.6 % | 53% | -4 | +0.031 [-0.010, 0.074] | +0.006 [-0.017, 0.026] |
| < 55 N | VNIR only | 92 (92) | -0.3 % | 64% | -5 | -0.025 [-0.122, 0.045] | -0.033 [-0.101, 0.015] |
| all | SWIR allowed | 129 (124) | +4.3 % | 43% | -2 | +0.016 [-0.003, 0.035] | -0.001 [-0.009, 0.008] |
| all | VNIR only | 114 (124) | -7.6 % | 67% | -1 | -0.028 [-0.074, 0.013] | -0.044 [-0.081, -0.014] |

## Between-patch AUC by start-up

| code | start-up | all | <55 N | 55-60 N | >=60 N |
|---|---|---|---|---|---|
| DC | flat spinup (ours, the defect) | 0.788 | 0.791 | 0.793 | 0.785 |
| DC | C-2 from ERA5-Land snow | 0.840 | 0.797 | 0.850 | 0.905 |
| DC | C-2 from S2 snow-off, SWIR allowed | 0.855 | 0.828 | 0.863 | 0.905 |
| DC | C-2 from S2 snow-off, VNIR only | 0.811 | 0.772 | 0.832 | 0.863 |
| DMC | flat spinup (ours, the defect) | 0.878 | 0.859 | 0.903 | 0.874 |
| DMC | C-2 from ERA5-Land snow | 0.883 | 0.869 | 0.903 | 0.878 |
| DMC | C-2 from S2 snow-off, SWIR allowed | 0.878 | 0.875 | 0.896 | 0.854 |
| DMC | C-2 from S2 snow-off, VNIR only | 0.788 | 0.828 | 0.768 | 0.762 |
| BUI | flat spinup (ours, the defect) | 0.878 | 0.854 | 0.903 | 0.876 |
| BUI | C-2 from ERA5-Land snow | 0.889 | 0.860 | 0.913 | 0.905 |
| BUI | C-2 from S2 snow-off, SWIR allowed | 0.890 | 0.875 | 0.916 | 0.891 |
| BUI | C-2 from S2 snow-off, VNIR only | 0.810 | 0.825 | 0.805 | 0.800 |
| FWI | flat spinup (ours, the defect) | 0.851 | 0.851 | 0.868 | 0.832 |
| FWI | C-2 from ERA5-Land snow | 0.851 | 0.840 | 0.871 | 0.836 |
| FWI | C-2 from S2 snow-off, SWIR allowed | 0.851 | 0.846 | 0.875 | 0.838 |
| FWI | C-2 from S2 snow-off, VNIR only | 0.808 | 0.807 | 0.836 | 0.781 |

Patches whose season had not started at D-1: flat 0, c2 14, c2_s2_all 16, c2_s2_vnir 20.
