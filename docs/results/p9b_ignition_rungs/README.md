# P9b: ignition learned rungs (E-45), partial

Run on Nibi: `narval_results/ignition_v1/20261105-1625`, **36 of 100 fits so far**. Pack `ignition_v1_pack` (Model `a5d6f49`): 7,194 points in 1,298 matched sets, development blocks only. The ignition freeze (test blocks and 2025) is unread. Imagery is noise-free (A-48). All values are Reconstructed (ours).

**At a glance:** [experiments.md](experiments.md). Tables: [tables.md](tables.md).

Generated with:

```bash
python scripts/make_results_package.py --phase P9b --run narval_results/ignition_v1/20261105-1625
python scripts/make_phase_docs.py --phase P9b
```

| configuration | fits | status |
|---|---|---|
| r0_scanfi, r0_cwfis | 5 each | complete |
| r1 | 15 | complete |
| r2 | 10 | fold 4 missing |
| r2_cwfis | 1 | fold 0 only |
| r2_leaf_ablated, r4, r4_shuffled | 0 | not in yet |

![rungs](ignition_rungs.png)

## What it shows so far

- **Learning on the CFFDRS inputs alone lifts ignition ranking.**
  - R0 (P(sustained flaming) by fuel) ranks the start above its own controls at 0.533.
  - R1, learned on the same inputs with no imagery, reaches 0.586: **+0.052 [+0.033, +0.072]** on all 1,292 sets.
  - R2 (physics + residual) is at the same level: +0.056 on folds 0–3, and −0.000 against R1.
- **What R1 can use.** Within a set the weather is shared (A-46), so the gain comes from what differs between the start and its controls:
  - the fuel code;
  - the SCANFI structure slots (percent conifer, closure, height);
  - the leaf state.
- **Registered prediction 2 fails, provisionally.** It said "r2 within ±0.01 of r0" and the gain is five times that. The verdict waits for R2's fold 4.
- **The bar for imagery moves.** r4 has to beat r4_shuffled (prediction 1) and, to be worth flying, R1's 0.586, not R0's 0.533.
- **CWFIS fuel:** one fit only (+0.009 over r2 on fold 0, CI spans 0). It is not read yet.

## Still to come

- r4 against r4_shuffled (prediction 1), and r2_leaf_ablated against r2 (prediction 3).
- Rerun this package when the sweep completes. The verdicts then lose their "provisional" tag.

## Limits

- Controls hold the weather and the ERA5 cell fixed but not lightning strike density (A-46).
- 1-degree block bootstrap: 394 blocks for the complete configurations.

<!-- qual:start -->
## Qualitative view per experiment

- **E-45** Ignition slot value (set map): [qual_E-45_sets_map.png](qual_E-45_sets_map.png)
<!-- qual:end -->
