# P6a-HS tables: the AVIRIS-NG band searches (E-61, E-62)

Run: `narval_results\hs_v4\20261102-1959`. Tasks: vnir 15, vnir_no_red_edge 15, swir_std 15, swir_ext 15, references 15; 1,087,281 development pixels. The AVIRIS test set was not transferred.

## Combined skill by nested set (raw + indices, with noise; noise-free in brackets)

| arm | k = 0 (fixed VNIR) | k = 1 | k = 2 | k = 3 | k = 4 | k = 5 | k = 6 |
|---|---|---|---|---|---|---|---|
| VNIR camera alone |  | +0.131 (+0.132) | +0.247 (+0.250) | +0.248 (+0.253) | +0.250 (+0.254) | +0.259 (+0.262) | +0.261 (+0.266) |
| VNIR, nothing in 700-760 nm |  | +0.125 (+0.126) | +0.246 (+0.247) | +0.244 (+0.245) | +0.253 (+0.261) | +0.255 (+0.262) | +0.258 (+0.264) |
| SWIR on standard InGaAs, VNIR fixed | +0.272 (+0.281) | +0.275 (+0.283) | +0.279 (+0.282) | +0.275 (+0.279) | +0.279 (+0.281) |  |  |
| SWIR on extended InGaAs, VNIR fixed | +0.272 (+0.281) | +0.275 (+0.281) | +0.279 (+0.288) | +0.288 (+0.292) | +0.287 (+0.289) |  |  |

## Final nested set, per target (raw + indices, with noise)

| arm | set | RMSE percent conifer (%) | RMSE closure (%) | RMSE height (m) | fuel family skill |
|---|---|---|---|---|---|
| VNIR camera alone | k6 | 25.0 | 15.8 | 3.88 | +0.362 |
| VNIR, nothing in 700-760 nm | k6 | 24.7 | 16.1 | 3.91 | +0.362 |
| SWIR on standard InGaAs, VNIR fixed | k4 | 24.2 | 15.5 | 3.83 | +0.386 |
| SWIR on extended InGaAs, VNIR fixed | k4 | 24.5 | 15.1 | 3.75 | +0.388 |

## E-61 as registered: extended InGaAs against standard, k = 4 (RMSE removed from the fixed VNIR)

| target | standard | extended | extra from extended [95 % CI] | runs |
|---|---|---|---|---|
| percent conifer (%) | +0.22 | -0.04 | -0.26 [-0.59, 0.04] | 15 |
| crown closure (%) | +0.28 | +0.70 | +0.42 [-0.08, 1.24] | 15 |
| canopy height (m) | -0.01 | +0.07 | +0.09 [0.01, 0.23] | 15 |

## E-62 as registered: no red edge minus VNIR, k = 6 (RMSE, % of VNIR)

| target | difference [95 % CI] | folds worse |
|---|---|---|
| percent conifer | -1.1 % [-2.1, -0.3] | 1/5 |
| crown closure | +2.1 % [0.9, 3.3] | 5/5 |
| canopy height | +1.0 % [0.2, 1.9] | 5/5 |

A band centred in 700-760 nm is in 15/15 best 6-band VNIR sets.

## The options

29 useful options of 29 scored; the rest are beaten by an option that costs no more and has no more bands (all are in `T_options.csv`). Bands are chosen on performance; cost is shown for information only (A-41).
Cost is qualitative: Q6 is open, so there are no figures yet.

| option | bands | score ± SE | RMSE closure | RMSE height | RMSE percent conifer | chain | cost | pros | cons |
|---|---|---|---|---|---|---|---|---|---|
| **reference: config_c** | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30, 1610/90@ext, 2190/180@ext | 0.288 ± 0.014 | 14.93 | 3.71 | 24.80 | silicon + extended InGaAs | high | best combined score; lowest error on closure, height; SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; SWIR2 present: cellulose/lignin sensitivity, dark-target aerosol; 8 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | high cost: main cost/SWaP driver; much higher dark current and deeper TEC cooling; VNIR and SWIR are separate chains: band-to-band registration risk |
| **SWIR on extended InGaAs, VNIR fixed: k3** | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30, 1990/20@ext, 1580/80@ext, 2080/100@ext | 0.288 ± 0.018 | 15.08 | 3.75 | 24.40 | silicon + extended InGaAs | high | tied with the best (within one SE, 0.014); SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; SWIR2 present: cellulose/lignin sensitivity, dark-target aerosol; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | high cost: main cost/SWaP driver; much higher dark current and deeper TEC cooling; VNIR and SWIR are separate chains: band-to-band registration risk; unstable: the searches disagree (least-chosen region in 27%) |
| **SWIR on extended InGaAs, VNIR fixed: k4** | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30, 1990/20@ext, 1580/20@ext, 2080/100@ext, 2270/40@ext | 0.287 ± 0.018 | 15.07 | 3.75 | 24.48 | silicon + extended InGaAs | high | tied with the best (within one SE, 0.014); SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; SWIR2 present: cellulose/lignin sensitivity, dark-target aerosol; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | high cost: main cost/SWaP driver; much higher dark current and deeper TEC cooling; VNIR and SWIR are separate chains: band-to-band registration risk; unstable: the searches disagree (least-chosen region in 33%) |
| **reference: sentinel2_p6_12band** | 443/20, 490/65, 560/35, 665/30, 705/15, 740/15, 783/20, 842/115, 865/20, 945/20, 1610/90@std, 2190/180@ext | 0.286 ± 0.018 | 15.05 | 3.76 | 24.52 | silicon + standard and extended InGaAs | high | tied with the best (within one SE, 0.014); SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; SWIR2 present: cellulose/lignin sensitivity, dark-target aerosol; 8 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | high cost: extended InGaAs plus a further SWIR focal plane; VNIR and SWIR are separate chains: band-to-band registration risk |
| **reference: sensor_mantis_ms_plus_swir** | 490/65, 560/35, 665/30, 705/15, 740/15, 865/20, 1240/20@std, 1550/40@std, 1610/40@std, 1680/40@std | 0.285 ± 0.017 | 15.09 | 3.74 | 24.68 | silicon + standard InGaAs | moderate | tied with the best (within one SE, 0.014); SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; 7 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | moderate cost: adds a SWIR chain on a COTS detector that cuts off near 1.7 um; VNIR and SWIR are separate chains: band-to-band registration risk; no SWIR2: no dark-target aerosol pairing, weak dry-matter leverage |
| **SWIR on extended InGaAs, VNIR fixed: k2** | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30, 1990/20@ext, 1580/80@ext | 0.279 ± 0.020 | 15.22 | 3.82 | 24.62 | silicon + extended InGaAs | high | tied with the best (within one SE, 0.014); SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | high cost: main cost/SWaP driver; much higher dark current and deeper TEC cooling; VNIR and SWIR are separate chains: band-to-band registration risk; no SWIR2: no dark-target aerosol pairing, weak dry-matter leverage; unstable: the searches disagree (least-chosen region in 27%) |
| **SWIR on standard InGaAs, VNIR fixed: k2** | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30, 1500/20@std, 1570/60@std | 0.279 ± 0.018 | 15.40 | 3.85 | 24.30 | silicon + standard InGaAs | moderate | tied with the best (within one SE, 0.014); SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | moderate cost: adds a SWIR chain on a COTS detector that cuts off near 1.7 um; VNIR and SWIR are separate chains: band-to-band registration risk; no SWIR2: no dark-target aerosol pairing, weak dry-matter leverage; unstable: the searches disagree (least-chosen region in 47%) |
| **SWIR on standard InGaAs, VNIR fixed: k4** | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30, 1630/40@std, 1530/20@std, 1500/20@std, 1580/20@std | 0.279 ± 0.025 | 15.49 | 3.83 | 24.22 | silicon + standard InGaAs | moderate | tied with the best (within one SE, 0.014); lowest error on percent conifer; SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | moderate cost: adds a SWIR chain on a COTS detector that cuts off near 1.7 um; VNIR and SWIR are separate chains: band-to-band registration risk; no SWIR2: no dark-target aerosol pairing, weak dry-matter leverage; unstable: the searches disagree (least-chosen region in 60%) |
| **reference: config_b** | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30, 1240/20@std, 1375/30@std, 1610/90@std | 0.278 ± 0.021 | 15.12 | 3.77 | 24.90 | silicon + standard InGaAs | moderate | tied with the best (within one SE, 0.014); SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; 7 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | moderate cost: adds a SWIR chain on a COTS detector that cuts off near 1.7 um; VNIR and SWIR are separate chains: band-to-band registration risk; no SWIR2: no dark-target aerosol pairing, weak dry-matter leverage |
| **reference: config_a** | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30, 1610/90@std | 0.278 ± 0.018 | 15.27 | 3.83 | 24.63 | silicon + standard InGaAs | moderate | tied with the best (within one SE, 0.014); SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; 7 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | moderate cost: adds a SWIR chain on a COTS detector that cuts off near 1.7 um; VNIR and SWIR are separate chains: band-to-band registration risk; no SWIR2: no dark-target aerosol pairing, weak dry-matter leverage |
| **SWIR on standard InGaAs, VNIR fixed: k3** | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30, 1500/20@std, 1630/40@std, 1530/20@std | 0.275 ± 0.023 | 15.52 | 3.88 | 24.23 | silicon + standard InGaAs | moderate | tied with the best (within one SE, 0.014); SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | moderate cost: adds a SWIR chain on a COTS detector that cuts off near 1.7 um; VNIR and SWIR are separate chains: band-to-band registration risk; no SWIR2: no dark-target aerosol pairing, weak dry-matter leverage; unstable: the searches disagree (least-chosen region in 53%) |
| **SWIR on extended InGaAs, VNIR fixed: k1** | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30, 1580/80@ext | 0.275 ± 0.019 | 15.45 | 3.84 | 24.56 | silicon + extended InGaAs | high | tied with the best (within one SE, 0.014); SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | high cost: main cost/SWaP driver; much higher dark current and deeper TEC cooling; VNIR and SWIR are separate chains: band-to-band registration risk; no SWIR2: no dark-target aerosol pairing, weak dry-matter leverage; unstable: the searches disagree (least-chosen region in 27%) |
| **SWIR on standard InGaAs, VNIR fixed: k1** | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30, 1570/60@std | 0.275 ± 0.018 | 15.35 | 3.85 | 24.60 | silicon + standard InGaAs | moderate | tied with the best (within one SE, 0.014); SWIR1 present: cloud/snow discrimination, and the contrast SWIR moisture metrics use; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | moderate cost: adds a SWIR chain on a COTS detector that cuts off near 1.7 um; VNIR and SWIR are separate chains: band-to-band registration risk; no SWIR2: no dark-target aerosol pairing, weak dry-matter leverage; unstable: the searches disagree (least-chosen region in 33%) |
| SWIR on standard InGaAs, VNIR fixed: fixed_only | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30 | 0.272 ± 0.023 | 15.77 | 3.82 | 24.44 | silicon only | low | low cost: an extra band costs filter area and pixels, little else; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | 0.016 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3) |
| SWIR on extended InGaAs, VNIR fixed: fixed_only | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30 | 0.272 ± 0.023 | 15.77 | 3.82 | 24.44 | silicon only | low | low cost: an extra band costs filter area and pixels, little else; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | 0.016 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3) |
| reference: config_c/VNIR | 490/40, 560/35, 665/30, 705/20, 740/20, 865/30 | 0.272 ± 0.023 | 15.77 | 3.82 | 24.44 | silicon only | low | low cost: an extra band costs filter area and pixels, little else; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | 0.016 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3) |
| reference: sensor_mantis_vnir6 | 490/65, 560/35, 665/30, 705/15, 740/15, 865/20 | 0.269 ± 0.022 | 15.86 | 3.83 | 24.55 | silicon only | low | low cost: an extra band costs filter area and pixels, little else; 6 of 8 Sentinel-2 centres matched: cross-calibration, S2 archive | 0.019 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3) |
| VNIR camera alone: k6 | 710/10, 530/10, 840/20, 640/80, 990/20, 470/100 | 0.261 ± 0.021 | 15.84 | 3.88 | 25.00 | silicon only | low | low cost: an extra band costs filter area and pixels, little else | 0.028 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3); unstable: the searches disagree (least-chosen region in 40%) |
| VNIR camera alone: k5 | 710/10, 530/10, 840/20, 990/20, 470/100 | 0.259 ± 0.019 | 15.89 | 3.85 | 25.05 | silicon only | low | low cost: an extra band costs filter area and pixels, little else | 0.030 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3); unstable: the searches disagree (least-chosen region in 33%) |
| VNIR, nothing in 700-760 nm: k6 | 530/10, 690/20, 870/10, 520/10, 450/100, 780/10 | 0.258 ± 0.018 | 16.15 | 3.91 | 24.73 | silicon only | low | low cost: an extra band costs filter area and pixels, little else | 0.030 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3); unstable: the searches disagree (least-chosen region in 53%) |
| VNIR, nothing in 700-760 nm: k5 | 690/20, 530/10, 520/10, 990/10, 870/10 | 0.255 ± 0.021 | 16.17 | 3.93 | 24.81 | silicon only | low | low cost: an extra band costs filter area and pixels, little else | 0.033 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3); unstable: the searches disagree (least-chosen region in 47%) |
| VNIR, nothing in 700-760 nm: k4 | 690/20, 530/10, 520/10, 870/10 | 0.253 ± 0.020 | 16.28 | 3.92 | 24.90 | silicon only | low | low cost: an extra band costs filter area and pixels, little else | 0.035 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3); unstable: the searches disagree (least-chosen region in 47%) |
| VNIR camera alone: k4 | 710/10, 530/10, 840/60, 990/20 | 0.250 ± 0.017 | 16.06 | 3.89 | 25.16 | silicon only | low | low cost: an extra band costs filter area and pixels, little else | 0.038 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3); unstable: the searches disagree (least-chosen region in 27%) |
| VNIR camera alone: k3 | 690/20, 540/20, 870/10 | 0.248 ± 0.019 | 16.23 | 3.89 | 25.20 | silicon only | low | low cost: an extra band costs filter area and pixels, little else | 0.040 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3); unstable: the searches disagree (least-chosen region in 40%) |
| VNIR camera alone: k2 | 690/20, 990/20 | 0.247 ± 0.017 | 16.42 | 3.90 | 24.81 | silicon only | low | low cost: an extra band costs filter area and pixels, little else | 0.041 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3); unstable: the searches disagree (least-chosen region in 27%) |
| VNIR, nothing in 700-760 nm: k2 | 690/10, 650/10 | 0.246 ± 0.015 | 16.47 | 3.91 | 24.71 | silicon only | low | low cost: an extra band costs filter area and pixels, little else | 0.042 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3); unstable: the searches disagree (least-chosen region in 27%) |
| VNIR, nothing in 700-760 nm: k3 | 690/10, 870/10, 780/10 | 0.244 ± 0.022 | 16.41 | 3.94 | 25.08 | silicon only | low | low cost: an extra band costs filter area and pixels, little else | 0.044 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3); unstable: the searches disagree (least-chosen region in 40%) |
| VNIR camera alone: k1 | 690/20 | 0.131 ± 0.016 | 20.61 | 4.31 | 27.75 | silicon only | low | low cost: an extra band costs filter area and pixels, little else | 0.157 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3); unstable: the searches disagree (least-chosen region in 47%) |
| VNIR, nothing in 700-760 nm: k1 | 690/20 | 0.125 ± 0.019 | 21.10 | 4.39 | 27.25 | silicon only | low | low cost: an extra band costs filter area and pixels, little else | 0.163 below the best combined score; no SWIR1: weak cloud/snow discrimination (brief section 3); unstable: the searches disagree (least-chosen region in 27%) |

## Resources

| arm | tasks | minutes, median | minutes, max | fits per task |
|---|---|---|---|---|
| vnir | 15 | 133 | 139 | 1773 |
| vnir_no_red_edge | 15 | 122 | 126 | 1587 |
| swir_std | 15 | 80 | 81 | 780 |
| swir_ext | 15 | 153 | 155 | 1680 |

## Fuel family, per class

| set | family | pixels | share | recall | precision | recall, fold range | folds with the class |
|---|---|---|---|---|---|---|---|
| config_c/VNIR | C | 717,204 | 21.99% | 0.524 | 0.409 | 0.230 to 0.699 | 5 |
| config_c/VNIR | D | 491,889 | 15.08% | 0.283 | 0.346 | 0.039 to 0.630 | 5 |
| config_c/VNIR | M | 571,878 | 17.53% | 0.264 | 0.378 | 0.072 to 0.390 | 5 |
| config_c/VNIR | O | 668,208 | 20.49% | 0.605 | 0.544 | 0.254 to 0.809 | 5 |
| config_c/VNIR | S | 2,946 | 0.09% | 0.000 | nan | 0.000 to 0.000 | 4 |
| config_c/VNIR | NF | 80,625 | 2.47% | 0.420 | 0.606 | 0.118 to 0.693 | 5 |
| config_c/VNIR | WA | 729,093 | 22.35% | 0.934 | 0.917 | 0.885 to 0.960 | 5 |
| config_c | C | 717,204 | 21.99% | 0.539 | 0.428 | 0.241 to 0.698 | 5 |
| config_c | D | 491,889 | 15.08% | 0.302 | 0.387 | 0.048 to 0.594 | 5 |
| config_c | M | 571,878 | 17.53% | 0.260 | 0.385 | 0.071 to 0.402 | 5 |
| config_c | O | 668,208 | 20.49% | 0.676 | 0.576 | 0.326 to 0.835 | 5 |
| config_c | S | 2,946 | 0.09% | 0.000 | nan | 0.000 to 0.000 | 4 |
| config_c | NF | 80,625 | 2.47% | 0.447 | 0.595 | 0.137 to 0.728 | 5 |
| config_c | WA | 729,093 | 22.35% | 0.938 | 0.921 | 0.889 to 0.964 | 5 |
| sentinel2_p6_12band | C | 717,204 | 21.99% | 0.520 | 0.422 | 0.259 to 0.720 | 5 |
| sentinel2_p6_12band | D | 491,889 | 15.08% | 0.309 | 0.386 | 0.054 to 0.557 | 5 |
| sentinel2_p6_12band | M | 571,878 | 17.53% | 0.287 | 0.374 | 0.066 to 0.503 | 5 |
| sentinel2_p6_12band | O | 668,208 | 20.49% | 0.626 | 0.569 | 0.309 to 0.847 | 5 |
| sentinel2_p6_12band | S | 2,946 | 0.09% | 0.000 | nan | 0.000 to 0.000 | 4 |
| sentinel2_p6_12band | NF | 80,625 | 2.47% | 0.455 | 0.553 | 0.141 to 0.740 | 5 |
| sentinel2_p6_12band | WA | 729,093 | 22.35% | 0.939 | 0.917 | 0.893 to 0.964 | 5 |
