# Phase 0 results — scaffolding

**Date:** 2026-09-19
**Scope:** package skeleton, config schemas with validation, pytest, README.
No forward model, no spectra, no computed index values.

## Done-when, checked

The brief's condition for Phase 0 is: *configs load and validate, tests pass,
and a README explains the layout.*

| Check | Result |
|---|---|
| `pytest` | 85 passed |
| `safari-bands validate` | 0 errors, 12 warnings, 1 info |
| `safari-bands indices` | matrix renders for 12 indices × 5 band sets |
| `safari-bands validate --run` | writes resolved config, findings, provenance |
| README | written |

Config schemas cover the four families the brief names — band set, detector,
optics, orbit — plus two added here: the index catalogue and the atmospheric
window definition.

## What was built

Five band sets ship: configurations A, B and C from brief section 5, a
Sentinel-2 equivalent as positive benchmark, and a negative control. Three
detector models (silicon CMOS, standard InGaAs, extended InGaAs), one optics
and one orbit config. Twelve indices from brief section 3, defined over band
*roles* rather than wavelengths so one definition resolves against any band set.

Four methodological rules are now executable rather than advisory:

- **Rule 7** (atmospheric windows) — `config/atmospheric_windows.yaml` holds the
  forbidden regions; bands overlapping one within their FWHM extent are
  rejected.
- **Detector physics** — a band whose centre falls outside its detector's
  spectral range is rejected. This is the 1.7 µm standard-InGaAs cutoff, the
  single constraint the A/B/C cost trade rests on.
- **Near-duplicate bands** — flagged, after the Kanyini failure mode where
  importance rankings picked bands sharing a wavelength range.
- **Placeholder visibility** — every config with unconfirmed values is listed
  on each `validate`, so a placeholder cannot be quietly reported as hardware.

## Findings worth carrying forward

**1. Rule 7 needs two thresholds, not one.** The first implementation rejected
any band whose SRF reached a forbidden region within 3× FWHM. That rejected
Sentinel-2's own 1610 nm band, which has 90 nm FWHM and works in orbit. The
rule now separates the FWHM extent (error — the measurement itself sits in an
absorption feature) from the skirts (warning — real but second-order, and
separately accounted for by `out_of_band_leakage`). Thresholds are config, not
code, so Phase 2 can replace them with computed transmittance.

**2. The provisional 740 nm band clips the O2-A band.** `validate` warns that
red_edge2 at 740 nm / 20 nm FWHM has skirts reaching 755–775 nm. Sentinel-2's
B6 avoids this at 15 nm FWHM. The VNIR set is provisional and Phase 4 optimises
it, but this is a concrete FWHM constraint to carry into Phase 5.

**3. Index feasibility already separates the configurations.** Purely from band
placement, before any physics:

| | config_a | config_b | config_c | S2 |
|---|---|---|---|---|
| T1 canopy water | 2/4 | 3/4 | 3/4 | 3/4 |
| T2 curing / NPV | 0/2 | 0/2 | 1/2 | 1/2 |
| T3 mortality | 1/2 | 1/2 | 2/2 | 2/2 |
| T4 fuel type | 3/3 | 3/3 | 3/3 | 3/3 |

Configurations A and B can form no curing index at any SNR, because NDTI needs
a SWIR1/SWIR2 contrast they lack. Adding the 1240 nm band to A unlocks exactly
one index — Gao's NDWI — and no SWIR2-dependent index.

That is the structural half of **hypothesis H2** (SWIR2 is necessary for T2 and
1240 nm is not a substitute). It is not a test of H2. Feasibility says what can
be computed, not what can be retrieved: the retrieval model works on bands, not
indices, and it may extract curing information from a band set that cannot form
a curing index. Testing H2 needs Phases 1–4.

The T2 column is also where the extended-InGaAs cost has to justify itself, so
it is the number to watch.

**4. `prosail` will work on Windows, but there is no PROSPECT-PRO.** Checked
before committing to the stack: `prosail` 2.0.5 ships a pure-Python universal
wheel, so Phase 1 needs no Fortran toolchain. It implements PROSPECT-5 and
PROSPECT-D with 4SAIL only. The brief asks that PROSPECT-PRO availability be
checked — it is not available in Python, and PROSPECT-PRO is the version that
splits dry matter into proteins and carbon-based constituents, which is
directly relevant to the conifer spring dip and hypothesis H1. Raised as
**Q10**.

**5. Phase 2 atmospheric tooling is not verified on Windows.** Py6S needs the
6S Fortran executable built separately and libRadtran is effectively
Linux-only. Neither was tested. Raised as **Q11**; worth settling before
Phase 2 is planned.

## Deliberately not built

- Scenario priors and fuel-type parameter distributions — Phase 1.
- SRF convolution and any spectral resampling — Phase 1/2.
- Index *evaluation*. `indices.py` resolves roles and reports feasibility; it
  never computes a value, because there are no spectra to compute one from.
- Any sensor noise model. Rule 6 requires noise in every evaluation, so this
  arrives with the first evaluation, in Phase 2.

## State of the open questions

All nine from brief section 9 remain open, seeded in
[OPEN_QUESTIONS.md](../OPEN_QUESTIONS.md) with what is assumed instead. Two new
ones (Q10 PROSPECT-PRO, Q11 atmospheric tooling) came out of implementation.

**Q4 (detector datasheets) is the binding one.** Every SNR number depends on
it, rule 6 requires noise in every evaluation, so Phase 4 wrapper results stay
provisional until it is answered. Phase 1 does not depend on it and can proceed.

## Next

Phase 1, the forward model — plan and approval first, per the working
agreement.
