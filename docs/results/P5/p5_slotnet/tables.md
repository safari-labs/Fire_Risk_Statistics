# P5 tables: the CFFDRS-structured network

Development fold 0 of 5 (split seed 0): 160 training / 34 held-out patches. The test split was not staged.

## T-r0: R0 through the network, fold 0

| output | pooled AUC | within-patch AUC (mean over fires) | between-patch AUC | fires |
|---|---|---|---|---|
| ROS (spread) | 0.702 | 0.656 | 0.802 | 18 |
| HFI (intensity) | 0.723 | 0.667 | 0.826 | 18 |
| CFB (crowning) | 0.616 | 0.577 | 0.833 | 18 |
| TFC (consumption) | 0.722 | 0.673 | 0.802 | 18 |
| P(sustained flaming) | 0.733 | 0.672 | 0.792 | 18 |

## T-agree: network R0 against the P3 evaluator (same fires)

| output | fires | P3 mean | P5 mean | Spearman | max gap |
|---|---|---|---|---|---|
| HFI | 18 | 0.682 | 0.667 | 0.95 | 0.10 |

## T-smoke: R3 (pc, fmc, cbh corrected) after 3 CPU batches

| pooled | within | between | HFI weight | other weights (max abs) | bias | wall (s) |
|---|---|---|---|---|---|---|
| 0.722 | 0.665 | 0.830 | 0.994 | 0.006 | -7.003 | 63 |

A smoke test, not a result: the fit is truncated by design. It shows the rung starts at R0 (pooled 0.723) and that a real-data fit runs.
