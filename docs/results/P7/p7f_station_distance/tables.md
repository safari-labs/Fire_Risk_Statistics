# P7f tables: station-distance stratification (E-17)

Run: `narval_results\slots_v2\7289478`. Station distance from the development pack (`station_km`). Terciles over 83 fire patches: < 32 km, 32-58 km, > 58 km. All values are Reconstructed (ours).

Between: each patch's share of its fold's between-patch AUC (a fire patch: the share of the fold's non-fire patches scored below it; a non-fire patch: the share of fire patches scored above it), arm minus R2. Within: within-patch AUC, arm minus R2 (fire patches only).

Verdict: SUPPORTED if rho (between-patch difference against distance) has its 95 % CI above 0, otherwise REFUTED (the phase sheets' vocabulary).

| arm | fits | rho, between [95 % CI] | verdict | rho, within | near: between | middle: between | far: between | near: within | middle: within | far: within |
|---|---|---|---|---|---|---|---|---|---|---|
| Free imagery branch (R4) | 15 | +0.04 [-0.10, 0.17] | REFUTED | -0.10 [-0.33, 0.14] | -0.001 [-0.020, 0.022] | +0.004 [-0.015, 0.024] | +0.000 [-0.015, 0.015] | +0.010 [-0.013, 0.032] | +0.017 [-0.002, 0.037] | +0.002 [-0.015, 0.020] |
| its twin (r4_shuffled) | 15 | -0.07 [-0.19, 0.06] | - | +0.10 [-0.13, 0.34] | -0.002 [-0.008, 0.004] | +0.003 [-0.003, 0.008] | -0.004 [-0.009, -0.001] | -0.002 [-0.006, 0.001] | +0.004 [-0.000, 0.007] | -0.001 [-0.006, 0.003] |
| PC + FMC + CBH slots from imagery | 15 | -0.03 [-0.16, 0.09] | REFUTED | +0.15 [-0.07, 0.37] | -0.001 [-0.005, 0.004] | +0.001 [-0.004, 0.007] | -0.003 [-0.007, -0.000] | -0.003 [-0.008, 0.001] | +0.001 [-0.005, 0.009] | -0.001 [-0.007, 0.004] |
| its twin (r3_pc_fmc_cbh_shuffled) | 15 | -0.01 [-0.16, 0.15] | - | +0.10 [-0.12, 0.32] | +0.000 [-0.003, 0.004] | +0.003 [0.000, 0.008] | +0.001 [0.000, 0.002] | -0.004 [-0.011, 0.002] | -0.004 [-0.011, 0.002] | +0.001 [-0.004, 0.008] |

Patches per tercile (all / fire): 55 / 28, 48 / 27, 90 / 28.
