# P6a-HS tables: the AVIRIS-NG band searches (E-61, E-62)

**PARTIAL: arms finished different folds, and folds differ in difficulty.** vnir [0, 2, 4]; vnir_no_red_edge [1, 3]; swir_std [0, 1, 2, 3, 4]; swir_ext [1, 3]; references [0, 1, 2, 3, 4]. Do not compare arms in the first two tables below; use the same-fold tables.

Run: `narval_results\hs_v2_provisional\20261030-1755`. Tasks: vnir 9, vnir_no_red_edge 6, swir_std 15, swir_ext 6, references 15; 757,281 development pixels. The AVIRIS test set was not transferred.

## Combined skill by nested set (raw + indices, with noise; noise-free in brackets)

| arm | k = 0 (fixed VNIR) | k = 1 | k = 2 | k = 3 | k = 4 | k = 5 | k = 6 |
|---|---|---|---|---|---|---|---|
| VNIR camera alone |  | +0.135 (+0.135) | +0.266 (+0.270) | +0.280 (+0.282) | +0.285 (+0.287) | +0.289 (+0.289) | +0.294 (+0.301) |
| VNIR, nothing in 700-760 nm |  | +0.131 (+0.133) | +0.239 (+0.243) | +0.224 (+0.221) | +0.229 (+0.230) | +0.233 (+0.233) | +0.226 (+0.229) |
| SWIR on standard InGaAs, VNIR fixed | +0.279 (+0.285) | +0.284 (+0.290) | +0.287 (+0.283) | +0.288 (+0.284) | +0.290 (+0.288) |  |  |
| SWIR on extended InGaAs, VNIR fixed | +0.242 (+0.248) | +0.244 (+0.250) | +0.263 (+0.271) | +0.273 (+0.267) | +0.274 (+0.270) |  |  |

## Final nested set, per target (raw + indices, with noise)

| arm | set | RMSE percent conifer (%) | RMSE closure (%) | RMSE height (m) | fuel family skill |
|---|---|---|---|---|---|
| VNIR camera alone | k6 | 22.4 | 16.2 | 3.97 | +0.443 |
| VNIR, nothing in 700-760 nm | k6 | 22.9 | 18.0 | 4.40 | +0.419 |
| SWIR on standard InGaAs, VNIR fixed | k4 | 22.4 | 16.1 | 4.05 | +0.460 |
| SWIR on extended InGaAs, VNIR fixed | k4 | 21.9 | 17.1 | 4.17 | +0.487 |

## E-61 as registered: extended InGaAs against standard, k = 4 (RMSE removed from the fixed VNIR)

| target | standard | extended | extra from extended [95 % CI] | runs |
|---|---|---|---|---|
| percent conifer (%) | -0.13 | +0.21 | +0.35 [0.02, 0.67] | 6 |
| crown closure (%) | +0.28 | +0.80 | +0.53 [0.10, 0.95] | 6 |
| canopy height (m) | -0.01 | +0.27 | +0.28 [0.00, 0.56] | 6 |

## E-62 as registered: no red edge minus VNIR, k = 6 (RMSE, % of VNIR)

| target | difference [95 % CI] | folds worse |
|---|---|---|

A band centred in 700-760 nm is in 9/9 best 6-band VNIR sets.

## Same folds: 0, 2, 4

| set | combined skill | above fixed VNIR, same runs | runs |
|---|---|---|---|
| SWIR on standard InGaAs, VNIR fixed: k4 | +0.319 | +0.016 | 9 |
| reference: sentinel2_p6_12band | +0.318 | +0.015 | 9 |
| reference: sensor_mantis_ms_plus_swir | +0.310 | +0.006 | 9 |
| reference: config_c | +0.310 | +0.006 | 9 |
| reference: config_a | +0.306 | +0.002 | 9 |
| Fixed VNIR | +0.303 | +0.000 | 9 |
| reference: config_c/VNIR | +0.303 | +0.000 | 9 |
| reference: sensor_mantis_vnir6 | +0.303 | -0.001 | 9 |
| reference: config_b | +0.297 | -0.006 | 9 |
| VNIR camera alone: k6 | +0.294 | -0.009 | 9 |

### The options on folds 0, 2, 4

18 useful options of 18 scored; the rest are beaten by an option that costs no more and has no more bands (all are in `T_options.csv`). Bands are chosen on performance; cost is shown for information only (A-41).
Cost is qualitative: Q6 is open, so there are no figures yet.

| option | bands | score ± SE | RMSE closure | RMSE height | RMSE percent conifer | chain | cost | pros | cons |
|---|---|---|---|---|---|---|---|---|---|
| **SWIR on standard InGaAs, VNIR fixed: k4** | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30, 1500/20@std, 1670/40@std, 1250/20@std, 1540/20@std | 0.319 ± 0.022 | 15.02 | 3.79 | 22.49 | silicon + standard InGaAs | moderate | best combined score; lowest error on closure; SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | moderate cost: adds a SWIR chain on a COTS detector that cuts off near 1.7 um; VNIR and SWIR are separate chains: band-to-band registration risk; no SWIR2: no dark-target aerosol pairing, weak dry-matter leverage; unstable: the searches disagree (least-chosen region in 40%) |
| **reference: sentinel2_p6_12band** | 443/20, 490/65, 560/35, 665/30, 705/15, 740/15, 783/20, 842/115, 865/20, 945/20, 1610/90@std, 2190/180@ext | 0.318 ± 0.023 | 15.14 | 3.79 | 22.53 | silicon + standard and extended InGaAs | high | tied with the best (within one SE, 0.022); SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; SWIR2 present: cellulose/lignin sensitivity, dark-target aerosol; 8 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | high cost: extended InGaAs plus a further SWIR focal plane; VNIR and SWIR are separate chains: band-to-band registration risk |
| **SWIR on standard InGaAs, VNIR fixed: k3** | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30, 1500/20@std, 1670/40@std, 1680/20@std | 0.318 ± 0.024 | 15.11 | 3.78 | 22.30 | silicon + standard InGaAs | moderate | tied with the best (within one SE, 0.022); lowest error on height; SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | moderate cost: adds a SWIR chain on a COTS detector that cuts off near 1.7 um; VNIR and SWIR are separate chains: band-to-band registration risk; no SWIR2: no dark-target aerosol pairing, weak dry-matter leverage; unstable: the searches disagree (least-chosen region in 40%) |
| **SWIR on standard InGaAs, VNIR fixed: k2** | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30, 1540/20@std, 1680/20@std | 0.314 ± 0.029 | 15.22 | 3.83 | 22.32 | silicon + standard InGaAs | moderate | tied with the best (within one SE, 0.022); SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | moderate cost: adds a SWIR chain on a COTS detector that cuts off near 1.7 um; VNIR and SWIR are separate chains: band-to-band registration risk; no SWIR2: no dark-target aerosol pairing, weak dry-matter leverage; unstable: the searches disagree (least-chosen region in 33%) |
| **reference: sensor_mantis_ms_plus_swir** | 490/65, 560/35, 665/30, 705/15, 740/15, 865/20, 1240/20@std, 1550/40@std, 1610/40@std, 1680/40@std | 0.310 ± 0.033 | 15.14 | 3.82 | 22.93 | silicon + standard InGaAs | moderate | tied with the best (within one SE, 0.022); SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; 7 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | moderate cost: adds a SWIR chain on a COTS detector that cuts off near 1.7 um; VNIR and SWIR are separate chains: band-to-band registration risk; no SWIR2: no dark-target aerosol pairing, weak dry-matter leverage |
| **reference: config_c** | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30, 1610/90@ext, 2190/180@ext | 0.310 ± 0.031 | 15.07 | 3.86 | 22.85 | silicon + extended InGaAs | high | tied with the best (within one SE, 0.022); SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; SWIR2 present: cellulose/lignin sensitivity, dark-target aerosol; 8 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | high cost: main cost/SWaP driver; much higher dark current and deeper TEC cooling; VNIR and SWIR are separate chains: band-to-band registration risk |
| **reference: config_a** | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30, 1610/90@std | 0.306 ± 0.032 | 15.23 | 3.92 | 22.63 | silicon + standard InGaAs | moderate | tied with the best (within one SE, 0.022); SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; 7 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | moderate cost: adds a SWIR chain on a COTS detector that cuts off near 1.7 um; VNIR and SWIR are separate chains: band-to-band registration risk; no SWIR2: no dark-target aerosol pairing, weak dry-matter leverage |
| **SWIR on standard InGaAs, VNIR fixed: fixed_only** | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30 | 0.303 ± 0.031 | 15.58 | 3.90 | 22.30 | silicon only | low | tied with the best (within one SE, 0.022); low cost: an extra band costs filter area and pixels, little else; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | no SWIR1: weak cloud/snow discrimination (brief section 3) |
| **reference: config_c/VNIR** | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30 | 0.303 ± 0.031 | 15.58 | 3.90 | 22.30 | silicon only | low | tied with the best (within one SE, 0.022); low cost: an extra band costs filter area and pixels, little else; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | no SWIR1: weak cloud/snow discrimination (brief section 3) |
| **reference: sensor_mantis_vnir6** | 490/65, 560/35, 665/30, 705/15, 740/15, 865/20 | 0.303 ± 0.032 | 15.60 | 3.87 | 22.51 | silicon only | low | tied with the best (within one SE, 0.022); low cost: an extra band costs filter area and pixels, little else; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | no SWIR1: weak cloud/snow discrimination (brief section 3) |
| **SWIR on standard InGaAs, VNIR fixed: k1** | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30, 1680/20@std | 0.302 ± 0.029 | 15.40 | 3.93 | 22.57 | silicon + standard InGaAs | moderate | tied with the best (within one SE, 0.022); SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | moderate cost: adds a SWIR chain on a COTS detector that cuts off near 1.7 um; VNIR and SWIR are separate chains: band-to-band registration risk; no SWIR2: no dark-target aerosol pairing, weak dry-matter leverage; unstable: the searches disagree (least-chosen region in 33%) |
| reference: config_b | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30, 1240/20@std, 1375/30@std, 1610/90@std | 0.297 ± 0.027 | 15.47 | 3.95 | 23.36 | silicon + standard InGaAs | moderate | SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; 7 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | 0.022 below the best combined score; moderate cost: adds a SWIR chain on a COTS detector that cuts off near 1.7 um; VNIR and SWIR are separate chains: band-to-band registration risk; no SWIR2: no dark-target aerosol pairing, weak dry-matter leverage |
| VNIR camera alone: k6 | 710/10, 410/20, 750/10, 630/20, 990/20, 840/10 | 0.294 ± 0.026 | 16.20 | 3.97 | 22.40 | silicon only | low | low cost: an extra band costs filter area and pixels, little else | 0.025 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3); unstable: the searches disagree (least-chosen region in 44%) |
| VNIR camera alone: k5 | 710/10, 410/20, 750/10, 990/20, 630/20 | 0.289 ± 0.028 | 16.40 | 4.04 | 22.29 | silicon only | low | lowest error on percent conifer; low cost: an extra band costs filter area and pixels, little else | 0.030 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3); unstable: the searches disagree (least-chosen region in 44%) |
| VNIR camera alone: k4 | 710/10, 990/20, 410/20, 630/20 | 0.285 ± 0.025 | 16.63 | 4.09 | 22.41 | silicon only | low | low cost: an extra band costs filter area and pixels, little else | 0.034 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3); unstable: the searches disagree (least-chosen region in 33%) |
| VNIR camera alone: k3 | 710/10, 990/20, 630/20 | 0.280 ± 0.029 | 17.19 | 4.13 | 22.44 | silicon only | low | low cost: an extra band costs filter area and pixels, little else | 0.040 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3); unstable: the searches disagree (least-chosen region in 33%) |
| VNIR camera alone: k2 | 690/100, 990/20 | 0.266 ± 0.033 | 17.70 | 4.19 | 23.00 | silicon only | low | low cost: an extra band costs filter area and pixels, little else | 0.053 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3); unstable: the searches disagree (least-chosen region in 44%) |
| VNIR camera alone: k1 | 990/20 | 0.135 ± 0.004 | 22.96 | 4.93 | 25.17 | silicon only | low | low cost: an extra band costs filter area and pixels, little else | 0.184 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3); unstable: the searches disagree (least-chosen region in 44%) |

## Same folds: 1, 3

| set | combined skill | above fixed VNIR, same runs | runs |
|---|---|---|---|
| reference: config_c | +0.276 | +0.034 | 6 |
| SWIR on extended InGaAs, VNIR fixed: k4 | +0.274 | +0.032 | 6 |
| reference: sentinel2_p6_12band | +0.273 | +0.031 | 6 |
| reference: sensor_mantis_ms_plus_swir | +0.269 | +0.027 | 6 |
| reference: config_b | +0.257 | +0.015 | 6 |
| reference: config_a | +0.255 | +0.012 | 6 |
| SWIR on standard InGaAs, VNIR fixed: k4 | +0.247 | +0.005 | 6 |
| Fixed VNIR | +0.242 | +0.000 | 6 |
| reference: config_c/VNIR | +0.242 | +0.000 | 6 |
| reference: sensor_mantis_vnir6 | +0.240 | -0.002 | 6 |
| VNIR, nothing in 700-760 nm: k6 | +0.226 | -0.016 | 6 |

### The options on folds 1, 3

15 useful options of 23 scored; the rest are beaten by an option that costs no more and has no more bands (all are in `T_options.csv`). Bands are chosen on performance; cost is shown for information only (A-41).
Cost is qualitative: Q6 is open, so there are no figures yet.

| option | bands | score ± SE | RMSE closure | RMSE height | RMSE percent conifer | chain | cost | pros | cons |
|---|---|---|---|---|---|---|---|---|---|
| **reference: config_c** | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30, 1610/90@ext, 2190/180@ext | 0.276 ± 0.012 | 16.64 | 4.18 | 21.85 | silicon + extended InGaAs | high | best combined score; lowest error on percent conifer; SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; SWIR2 present: cellulose/lignin sensitivity, dark-target aerosol; 8 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | high cost: main cost/SWaP driver; much higher dark current and deeper TEC cooling; VNIR and SWIR are separate chains: band-to-band registration risk |
| **SWIR on extended InGaAs, VNIR fixed: k4** | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30, 1990/20@ext, 2240/100@ext, 1650/20@ext, 1580/60@ext | 0.274 ± 0.007 | 17.10 | 4.17 | 21.87 | silicon + extended InGaAs | high | tied with the best (within one SE, 0.012); SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; SWIR2 present: cellulose/lignin sensitivity, dark-target aerosol; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | high cost: main cost/SWaP driver; much higher dark current and deeper TEC cooling; VNIR and SWIR are separate chains: band-to-band registration risk; unstable: the searches disagree (least-chosen region in 33%) |
| **reference: sentinel2_p6_12band** | 443/20, 490/65, 560/35, 665/30, 705/15, 740/15, 783/20, 842/115, 865/20, 945/20, 1610/90@std, 2190/180@ext | 0.273 ± 0.003 | 16.44 | 4.31 | 22.18 | silicon + standard and extended InGaAs | high | tied with the best (within one SE, 0.012); lowest error on closure; SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; SWIR2 present: cellulose/lignin sensitivity, dark-target aerosol; 8 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | high cost: extended InGaAs plus a further SWIR focal plane; VNIR and SWIR are separate chains: band-to-band registration risk |
| **SWIR on extended InGaAs, VNIR fixed: k3** | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30, 1990/20@ext, 1580/60@ext, 1550/100@ext | 0.273 ± 0.004 | 17.26 | 4.13 | 22.11 | silicon + extended InGaAs | high | tied with the best (within one SE, 0.012); lowest error on height; SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | high cost: main cost/SWaP driver; much higher dark current and deeper TEC cooling; VNIR and SWIR are separate chains: band-to-band registration risk; no SWIR2: no dark-target aerosol pairing, weak dry-matter leverage; unstable: the searches disagree (least-chosen region in 33%) |
| **reference: sensor_mantis_ms_plus_swir** | 490/65, 560/35, 665/30, 705/15, 740/15, 865/20, 1240/20@std, 1550/40@std, 1610/40@std, 1680/40@std | 0.269 ± 0.003 | 16.63 | 4.25 | 22.10 | silicon + standard InGaAs | moderate | tied with the best (within one SE, 0.012); SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; 7 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | moderate cost: adds a SWIR chain on a COTS detector that cuts off near 1.7 um; VNIR and SWIR are separate chains: band-to-band registration risk; no SWIR2: no dark-target aerosol pairing, weak dry-matter leverage |
| reference: config_b | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30, 1240/20@std, 1375/30@std, 1610/90@std | 0.257 ± 0.003 | 16.85 | 4.28 | 22.39 | silicon + standard InGaAs | moderate | SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; 7 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | 0.019 below the best combined score; moderate cost: adds a SWIR chain on a COTS detector that cuts off near 1.7 um; VNIR and SWIR are separate chains: band-to-band registration risk; no SWIR2: no dark-target aerosol pairing, weak dry-matter leverage |
| SWIR on standard InGaAs, VNIR fixed: k1 | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30, 1680/20@std | 0.257 ± 0.003 | 17.28 | 4.28 | 22.33 | silicon + standard InGaAs | moderate | SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | 0.020 below the best combined score; moderate cost: adds a SWIR chain on a COTS detector that cuts off near 1.7 um; VNIR and SWIR are separate chains: band-to-band registration risk; no SWIR2: no dark-target aerosol pairing, weak dry-matter leverage; unstable: the searches disagree (least-chosen region in 33%) |
| reference: config_a | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30, 1610/90@std | 0.255 ± 0.004 | 17.36 | 4.38 | 22.23 | silicon + standard InGaAs | moderate | SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; 7 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | 0.022 below the best combined score; moderate cost: adds a SWIR chain on a COTS detector that cuts off near 1.7 um; VNIR and SWIR are separate chains: band-to-band registration risk; no SWIR2: no dark-target aerosol pairing, weak dry-matter leverage |
| SWIR on standard InGaAs, VNIR fixed: fixed_only | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30 | 0.242 ± 0.010 | 17.90 | 4.45 | 22.08 | silicon only | low | low cost: an extra band costs filter area and pixels, little else; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | 0.034 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3) |
| SWIR on extended InGaAs, VNIR fixed: fixed_only | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30 | 0.242 ± 0.010 | 17.90 | 4.45 | 22.08 | silicon only | low | low cost: an extra band costs filter area and pixels, little else; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | 0.034 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3) |
| reference: config_c/VNIR | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30 | 0.242 ± 0.010 | 17.90 | 4.45 | 22.08 | silicon only | low | low cost: an extra band costs filter area and pixels, little else; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | 0.034 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3) |
| reference: sensor_mantis_vnir6 | 490/65, 560/35, 665/30, 705/15, 740/15, 865/20 | 0.240 ± 0.013 | 17.99 | 4.44 | 22.28 | silicon only | low | low cost: an extra band costs filter area and pixels, little else; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | 0.036 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3) |
| VNIR, nothing in 700-760 nm: k2 | 990/20, 690/20 | 0.239 ± 0.008 | 17.30 | 4.32 | 22.40 | silicon only | low | low cost: an extra band costs filter area and pixels, little else | 0.038 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3); unstable: the searches disagree (least-chosen region in 50%) |
| VNIR, nothing in 700-760 nm: k5 | 590/20, 530/20, 870/20, 990/20, 780/10 | 0.233 ± 0.010 | 18.24 | 4.41 | 22.54 | silicon only | low | low cost: an extra band costs filter area and pixels, little else | 0.044 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3); unstable: the searches disagree (least-chosen region in 50%) |
| VNIR, nothing in 700-760 nm: k1 | 990/20 | 0.131 ± 0.014 | 20.80 | 4.70 | 25.30 | silicon only | low | low cost: an extra band costs filter area and pixels, little else | 0.145 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3); unstable: the searches disagree (least-chosen region in 50%) |

## Resources

| arm | tasks | minutes, median | minutes, max | fits per task |
|---|---|---|---|---|
| vnir | 9 | 132 | 135 | 1773 |
| vnir_no_red_edge | 6 | 121 | 123 | 1587 |
| swir_std | 15 | 79 | 80 | 780 |
| swir_ext | 6 | 155 | 156 | 1680 |
