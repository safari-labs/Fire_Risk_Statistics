# P1 — Physics port: FBP, FWI and ignition (2026-10-23)

P1 builds the non-learned "CFFDRS as is" baseline (R0, register E-32/E-41/E-44). It is validated against the CFS reference implementation, the `cffdrs` R package (version 1.9.2, run on R 4.6.1).

## Results

### FBP ported and exact

`Fire_Risk_Model/src/data/fbp_behaviour.py` computes the FBP1992 primary outputs for every fuel type:

- **Outputs:** rate of spread, crown fraction burned, surface/crown/total fuel consumption, head fire intensity and fire type.
- **Intermediates:** ISI from the slope-adjusted wind, net effective wind (WSV), spread azimuth, build-up effect, critical surface intensity, critical spread rate (RSO) and FMC.

**Validation.** We ran 6,000 seeded rows covering all 17 reference fuel types and the full input ranges. Every output agrees with `cffdrs` to a relative error of about 1e-12, and fire type agrees on all 6,000 rows (`validation.png`).

**D-2 (green aspen)** is not in the package. ST-X-3 gives it 0.2 × D-1, the same factor the package applies to the deciduous share of M-2 and M-4. It is tested separately.

**The FWI2025 rule is enforced.** `fbp()` refuses any FWI source except Van Wagner (1987), because NRCan says FWI2025 must not be paired with FBP1992.

### `fwi.py` corrected

The first comparison against `cffdrs` disagreed by up to 2.8 FFMC points. Three things were fixed:

- **A bug in the FFMC rain correction.** Above 150 % moisture the correction used the moisture value already updated for rain. Van Wagner (1987) eq. 3b uses the pre-rain moisture for both terms.
- **The FFMC constant.** The printed 147.2 is now the exact 250 × 59.5 / 101.
- **DMC wetting.** It now uses the operational code's form, with the constant 43.43 × 5.6348 left unrounded.

All six codes now agree to about 1e-14. The `_fwi.json` sidecars built before this change are legacy; P3 rebuilds them.

### Ignition: interim classes; continuous models waiting on sources

`Fire_Risk_Model/src/data/ignition.py` gives an ordinal ignition score now, using the GLC-X-42 Table 1 classes:

- FFMC → sustainable flaming ignition
- DMC → lightning ignition

R0 needs only a ranking, so this score is enough for it.

The continuous models exist in the module but refuse to run until their coefficients are obtained (Q26):

| Model | Source | Status |
|---|---|---|
| P(sustained flaming) | Beverly & Wotton (2007) | paywalled |
| In-stand FFMC by stand density (the canopy-closure slot) | Wotton & Beverly (2007) | paywalled |
| P(lightning ignition) | Wotton & Wheatley (2025) | open access, but the paper publishes only GAM curves; the numeric table is "available from the authors" |

### What the physics says the imagery slots can move (`responses.png`)

- **Fuel type sets the spread curve.** At ISI 30, ROS is about 75 m/min for O-1a grass at 90 % cure, about 50 for C-2/C-3, 31 for M-1 at 50 % conifer and 11 for D-1. A fuel-type error moves the prediction more than most weather errors do.
- **Foliar moisture (FMC) and crown base height (CBH) set the crowning threshold.** On C-3:
  - Raising FMC from 85 % to 120 % delays crowning by about 4 km/h of wind.
  - Lowering CBH from 8 m to 3 m makes it crown partly with no wind at all.
- **Percent conifer and leaf state set mixedwood spread.** With no conifer, M-1 (leafless) spreads about 5× faster than M-2 (green). The gap closes to nothing at 100 % conifer. So the green-up and percent-conifer slots matter most in deciduous-leaning stands.

## Decisions recorded

- **Q26:** the paywalled ignition papers are listed in the summary to James.
- **Q27:** NBAC 2024/2025 are unpacked. The 13 unmatched confusers still have no NBAC polygon, so they take pseudo-dates (A-24).
- **Q28:** budgets taken from `CubeSat_Sensors_and_Lenses.xlsx` (A-29). Each 1000 × 1000 × 6-band scene must finish within 91 s (buffered processing at 500 km). The 4.6 s real-time figure is reported, not required. With latency met, power is minimised.
- **Licence:** `cffdrs` is GPL-2, not MPL-2.0 as Q18 had stated (now corrected). The port implements the published equations and uses the package only to generate reference outputs.

## Files (Fire_Risk_Model)

- **Code:** `src/data/fbp_behaviour.py` and `src/data/ignition.py` (new), `src/data/fwi.py` (corrected).
- **Reference outputs:** `scripts/r/make_cffdrs_fixtures.R` generates `tests/fixtures/fbp_cffdrs_R.csv` and `tests/fixtures/fwi_cffdrs_R.csv`.
- **Tests:** `test_fbp_behaviour.py`, `test_fwi_cffdrs.py` and `test_ignition.py`. The full suite has 342 passing tests; the one failure, `test_deploy_parity::test_gsd_matching_present`, predates this work.
- **Figures:** `scripts/python/plot_fbp_validation.py`.

**Next:** P2, the first result. Compute R0 for every fuel-inventory variant on the sidecars already held, then build the interpretation package for it.
