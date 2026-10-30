# P6d: the FWI start-up from Sentinel-2 snow-off (E-18)

The snow classifiers were fitted and applied on Nibi, 2026-10-30: `narval_results/snow_off/20261030-1126`, with the cloud fix (`Fire_Risk_FW` 52382be). The two earlier runs in that folder predate the fix and are not used. The codes were then computed and scored locally: `runs/20261030-e18_s2_startup`. No model was trained for the scoring. The frozen test patches were not opened.

Every code here is Reconstructed (ours); none is ISSUED by CWFIS.

Generated with:

```bash
cd ../Fire_Risk_Model
python scripts/python/build_s2_startup.py --overwrite \
    --snowoff ../Fire_Risk_Statistics/narval_results/snow_off/20261030-1126/patch_snowoff.json
python scripts/python/eval_cffdrs_reference.py --design dated \
    --out ../Fire_Risk_Statistics/runs/20261030-e18_s2_startup
cd ../Fire_Risk_Statistics
python scripts/make_results_package.py --phase P6d --run runs/20261030-e18_s2_startup \
    --snowoff narval_results/snow_off/20261030-1126/patch_snowoff.json
python scripts/make_phase_docs.py --phase P6d
```

## What it found

- **E-18 is REFUTED: a Sentinel-2 snow-off date does not beat the ERA5-Land rule.** Above 55° N the SWIR-allowed date moves median lag-1 DC by +7.0 %, under the registered 10 %. Its AUC changes are DC +0.015 [−0.008, +0.040] and FWI +0.002 [−0.009, +0.013], so neither CI clears 0. The registered falsifier fires.
- **The VNIR-only date does move DC, the wrong way.** Median DC falls 20.2 % above 55° N, so the falsifier's "moves DC" clause does not fire. But the move loses skill: FWI −0.042 [−0.086, −0.007], DMC −0.126 [−0.221, −0.055], BUI −0.108 [−0.194, −0.045]. The hypothesis says the correction improves skill, and here it does the reverse.
- **The effect is not concentrated in the north.** The SWIR-allowed date moves median DC +9.6 % below 55° N, more than above it, so "little effect in the south" fails too.
- **The two date sources mostly agree.** SWIR-allowed starts a median 2 days before ERA5 (10–90 %: −11 to +12 days). So ERA5's late melt, the error this experiment hoped to fix, is small on these patches. VNIR-only has a long late tail (10–90 %: −14 to +33 days), the classifier's late misses from E-60, which starts the season late and removes drying from the codes.
- **Our own defect stays fixed.** The flat spinup against the C-2 rule gives DC AUC 0.788 → 0.840, and 0.785 → 0.905 at or above 60° N. That gain came from the rule (E-51), not from imagery.

## What this means for the mission

- Keep the operational start-up: ERA5-Land snow, or the CWFIS issued codes. Neither needs SAFARI.
- This agrees with the Q37 decision (A-41). SAFARI is not asked for snow-off dates, and this result says little is lost, even with Sentinel-2's 5-day cadence, far denser than SAFARI's. E-60's "SWIR1 is worth about 4 days" stands as a measurement, and it shows up here: the VNIR-only date loses to ERA5 while the SWIR-allowed date ties it. Neither beats the rule, so that SWIR value doesn't argue for a SAFARI band.

## Limits

- 189 development patches (83 fire); the CIs are wide above 60° N (44 patches). A gain of about 0.04 in DC AUC can't be excluded.
- Fires are dominated by 2023, as in every fire-outcome result here.
- AUC scores the fire versus non-fire ranking, not whether DC itself is right. Ground-thaw truth is not held.
- The 189 dated patches are those with a date in both arms; 7 of 196 had no clear date.

## Files

| File | What it shows |
|---|---|
| `experiments.png`, `experiments.md` | phase sheet: E-18 and the date agreement |
| `paired.png` | the deciding comparison: each imagery date's AUC minus the ERA5 rule's, same patches |
| `auc.png` | AUC of DC, DMC, BUI and FWI under all four start-ups, by latitude band |
| `dates.png` | each patch's season start against ERA5's, and the DC move by latitude |
| `tables.md`, `T_falsifier.csv`, `summary.json` | the numbers |
