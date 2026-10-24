# P2 tables: R0 on the legacy design

Development patches: 196 (test groups excluded: 35 patches). Design: legacy 30-June FWI1987 codes, green leaf state, NBAC labels.

## T-inventory: fuel inventories under unchanged FBP and ignition physics (E-33)

Within-patch AUC (fire patches; fuel and terrain only), mean and 95 % group-bootstrap CI. `burned_read_nonfuel` is the share of NBAC-burned pixels the inventory calls non-fuel or water.

| inventory | status | n fire | burned→non-fuel | ROS | HFI | CFB | TFC | P(sf) | HFI, land only | between HFI | pooled HFI |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CWFIS 2019 (250 m) | pre-fire | 83 | 0.033 | 0.610 [0.59, 0.63] | 0.623 [0.60, 0.65] | 0.562 [0.54, 0.58] | 0.631 [0.61, 0.65] | 0.504 [0.48, 0.53] | 0.558 [0.54, 0.58] | 0.744 [0.67, 0.81] | 0.704 |
| CWFIS 2014b (250 m) | pre-fire | 83 | 0.054 | 0.596 [0.58, 0.62] | 0.608 [0.59, 0.63] | 0.559 [0.54, 0.58] | 0.614 [0.59, 0.64] | 0.500 [0.48, 0.52] | 0.532 [0.51, 0.55] | 0.737 [0.66, 0.81] | 0.676 |
| SCANFI v2, latest pre-fire step | pre-fire | 83 | 0.006 | 0.675 [0.65, 0.70] | 0.676 [0.65, 0.70] | 0.581 [0.56, 0.60] | 0.679 [0.66, 0.70] | 0.533 [0.50, 0.56] | 0.589 [0.57, 0.61] | 0.755 [0.68, 0.83] | 0.717 |
|   same, block-moded to 250 m | pre-fire | 83 | 0.024 | 0.660 [0.64, 0.68] | 0.662 [0.64, 0.68] | 0.579 [0.56, 0.60] | 0.665 [0.64, 0.69] | 0.523 [0.49, 0.56] | 0.590 [0.57, 0.61] | 0.758 [0.68, 0.83] | 0.709 |
| SCANFI v2 pre-fire, A-11 rules | pre-fire, judgement rules (A-11) | 83 | 0.092 | 0.629 [0.60, 0.66] | 0.628 [0.60, 0.66] | 0.582 [0.56, 0.61] | 0.629 [0.60, 0.66] | 0.503 [0.49, 0.52] | 0.508 [0.49, 0.53] | 0.741 [0.67, 0.81] | 0.718 |
| SCANFI v2 2010 | pre-fire | 44 | 0.007 | 0.697 [0.67, 0.73] | 0.696 [0.67, 0.73] | 0.582 [0.56, 0.60] | 0.700 [0.67, 0.74] | 0.545 [0.51, 0.58] | 0.592 [0.57, 0.61] | 0.714 [0.59, 0.82] | 0.711 |
| SCANFI v2 2015 | pre-fire | 83 | 0.006 | 0.675 [0.65, 0.70] | 0.677 [0.66, 0.70] | 0.581 [0.56, 0.60] | 0.681 [0.66, 0.71] | 0.538 [0.51, 0.57] | 0.590 [0.57, 0.61] | 0.752 [0.67, 0.82] | 0.713 |
| SCANFI v2 2020 | post-fire for 2019-20 fires | 83 | 0.006 | 0.654 [0.62, 0.69] | 0.654 [0.62, 0.69] | 0.568 [0.55, 0.59] | 0.657 [0.63, 0.69] | 0.522 [0.49, 0.56] | 0.563 [0.54, 0.59] | 0.749 [0.67, 0.82] | 0.708 |
| SCANFI v2 2025 | post-fire: leakage control | 83 | 0.006 | 0.490 [0.45, 0.54] | 0.488 [0.44, 0.54] | 0.447 [0.42, 0.47] | 0.487 [0.44, 0.54] | 0.453 [0.41, 0.50] | 0.352 [0.32, 0.38] | 0.730 [0.65, 0.80] | 0.630 |
| CWFIS 2024 (30 m) | post-fire: leakage control | 83 | 0.687 | 0.211 [0.17, 0.26] | 0.211 [0.17, 0.26] | 0.390 [0.37, 0.41] | 0.225 [0.18, 0.28] | 0.454 [0.41, 0.49] | 0.093 [0.07, 0.12] | 0.706 [0.63, 0.78] | 0.354 |

## T-paired: what each inventory difference is worth, all pixels (E-33)

Within-patch HFI AUC, A minus B on the same fire patches; 95 % fire/block-group bootstrap CI; share of patches where A wins.

| comparison (A vs B) | delta | 95 % CI | A wins | n |
|---|---|---|---|---|
| SCANFI (CFS tree) vs operational CWFIS 2019 | +0.053 | [+0.037, +0.071] | 0.75 | 83 |
| same at 250 m: the inventory, resolution removed | +0.039 | [+0.024, +0.054] | 0.76 | 83 |
| 30 m vs 250 m: the resolution alone | +0.014 | [+0.005, +0.024] | 0.59 | 83 |
| CFS tree vs A-11 judgement rules, same SCANFI step | +0.048 | [+0.030, +0.067] | 0.69 | 83 |
| CWFIS 2019 vs 2014b | +0.016 | [-0.006, +0.036] | 0.52 | 83 |
| pre-fire vs post-fire SCANFI (leak size) | +0.188 | [+0.160, +0.217] | 0.99 | 83 |
| pre-fire vs post-fire CWFIS (leak size) | +0.413 | [+0.371, +0.451] | 0.99 | 83 |

## T-paired-land: what each inventory difference is worth, land pixels only (E-33)

Within-patch HFI AUC, A minus B on the same fire patches; 95 % fire/block-group bootstrap CI; share of patches where A wins.

| comparison (A vs B) | delta | 95 % CI | A wins | n |
|---|---|---|---|---|
| SCANFI (CFS tree) vs operational CWFIS 2019 | +0.031 | [+0.014, +0.050] | 0.57 | 83 |
| same at 250 m: the inventory, resolution removed | +0.032 | [+0.014, +0.051] | 0.65 | 83 |
| 30 m vs 250 m: the resolution alone | -0.001 | [-0.009, +0.008] | 0.49 | 83 |
| CFS tree vs A-11 judgement rules, same SCANFI step | +0.081 | [+0.060, +0.104] | 0.83 | 83 |
| CWFIS 2019 vs 2014b | +0.026 | [-0.000, +0.053] | 0.54 | 83 |
| pre-fire vs post-fire SCANFI (leak size) | +0.237 | [+0.211, +0.263] | 0.99 | 83 |
| pre-fire vs post-fire CWFIS (leak size) | +0.465 | [+0.430, +0.497] | 0.99 | 83 |

## T-weather: FWI codes between patches (E-32)

| code | between-patch AUC | 95 % CI | paired win rate | pairs |
|---|---|---|---|---|
| FFMC | 0.695 | [0.62, 0.77] | 0.574 | 68 |
| DMC | 0.741 | [0.67, 0.81] | 0.662 | 68 |
| DC | 0.828 | [0.77, 0.88] | 0.882 | 68 |
| ISI | 0.701 | [0.62, 0.77] | 0.603 | 68 |
| BUI | 0.765 | [0.70, 0.83] | 0.706 | 68 |
| FWI | 0.738 | [0.66, 0.81] | 0.691 | 68 |
| FFMC ignition class (GLC-X-42) | 0.684 | [0.61, 0.76] | 0.610 | 68 |
| DMC lightning class (GLC-X-42) | 0.730 | [0.66, 0.79] | 0.662 | 68 |

## T-fuel: CWFIS 2019 (250 m), development fire patches

| fuel | pixels | burned share | mean HFI (kW/m) | mean P(sf) |
|---|---|---|---|---|
| C2 | 2,000,312 | 0.752 | 3,896 | 0.350 |
| M2 | 1,278,337 | 0.666 | 1,454 | 0.268 |
| D2 | 1,114,527 | 0.596 | 128 | 0.119 |
| C3 | 822,969 | 0.687 | 10,627 | 0.594 |
| C1 | 495,918 | 0.689 | 484 | 0.698 |
| C4 | 436,986 | 0.800 | 4,802 | 0.455 |
| C7 | 393,001 | 0.645 | 4,650 | 0.536 |
| WA | 379,201 | 0.138 | 0 | 0.000 |
| O1B | 319,965 | 0.548 | 3,004 | 0.790 |
| NF | 203,371 | 0.465 | 0 | 0.000 |
| D1 | 155,683 | 0.715 | 411 | 0.103 |
| M1 | 123,532 | 0.595 | 1,374 | 0.443 |
| C5 | 3,003 | 0.325 | 3,572 | 0.573 |

## T-fuel: SCANFI v2, latest pre-fire step, development fire patches

| fuel | pixels | burned share | mean HFI (kW/m) | mean P(sf) |
|---|---|---|---|---|
| C2 | 2,742,797 | 0.728 | 12,400 | 0.433 |
| D2 | 1,476,070 | 0.564 | 152 | 0.144 |
| M2 | 1,332,310 | 0.689 | 1,879 | 0.341 |
| C3 | 533,991 | 0.856 | 677 | 0.533 |
| WA | 508,174 | 0.056 | 0 | 0.000 |
| C4 | 425,414 | 0.794 | 3,615 | 0.412 |
| C1 | 399,653 | 0.707 | 269 | 0.618 |
| D1 | 247,594 | 0.568 | 1,372 | 0.244 |
| C7 | 60,566 | 0.754 | 700 | 0.319 |
| C5 | 139 | 0.986 | 124 | 0.384 |
| M1 | 97 | 0.794 | 737 | 0.426 |

## T-vintage: inventory age (E-21)

| output | slope (AUC per decade) | 95 % CI | patches with 2+ pre-fire steps |
|---|---|---|---|
| HFI (intensity) | -0.0048 | [-0.0148, 0.0073] | 79 |
| ROS (spread) | -0.0045 | [-0.0148, 0.0079] | 79 |
