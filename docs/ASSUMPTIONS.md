# Assumptions

Every value the study uses that James has not confirmed. Each entry says what
was assumed, why, what it affects, and which open question replaces it.

Placeholder configs carry `placeholder: true` and a `source:` string, so
`safari-bands validate` lists them on every run. Nothing here should survive
into a final requirements table without being replaced or explicitly accepted.

Status key: **OPEN** = still a stand-in. **RESOLVED** = replaced by a confirmed
value (keep the row, note what it became).

---

## A-1 — Atmospheric window edges are nominal, not computed

**Status:** OPEN
**File:** `config/atmospheric_windows.yaml`

The forbidden regions (O2-A 755–775, O2 1262–1288, water vapour 1330–1490 and
1780–1980, CO2/H2O above 2400 nm) come from the brief's rule 7 plus standard
atmospheric-window knowledge. They are not derived from a computed
transmittance spectrum.

The two-threshold scheme is also a judgement call: overlap within 1.0× FWHM is
an error, overlap out to 2.0× FWHM is a warning. This was calibrated so that
Sentinel-2's own 1610 nm band (90 nm FWHM) passes — a single aggressive
threshold rejected a band that demonstrably works in orbit.

**Affects:** which candidate band centres Phase 4 is allowed to consider.
**Replace with:** 6S or libRadtran transmittance in Phase 2; set the edges at a
stated transmittance threshold rather than by hand.

---

## A-2 — Detector parameters are representative, not datasheet

**Status:** OPEN — blocks meaningful Phase 2 output
**Files:** `config/detector/silicon_cmos.yaml`, `ingaas_std.yaml`, `ingaas_ext.yaml`

QE curves, dark current, read noise, full well, pixel pitch and operating
temperature are plausible values for COTS parts of each technology. No part has
been selected and no datasheet has been consulted.

The one structural claim that is *not* a placeholder is the standard-InGaAs
1.7 µm cutoff. That is a property of the material, it is what makes a ~2190 nm
band impossible on standard InGaAs, and it is enforced by
`check_detector_coverage`. The study's main cost/SWaP trade rests on it.

The extended-InGaAs dark current is set about two orders of magnitude above
standard InGaAs at the same temperature, which is the right order but not a
measured figure.

**Affects:** every SNR number, and therefore every noisy retrieval result
(rule 6 requires noise in every evaluation).
**Replace with:** answers to **Q4**.

---

## A-3 — Optics are a self-consistent guess

**Status:** OPEN
**File:** `config/optics/default.yaml`

70 mm aperture, 280 mm focal length, f/4, 0.75 transmission. Chosen only so
Phase 2 radiometry has something to run on. Filter architecture is unset, which
matters because it drives band-to-band registration — a flagged engineering
risk for the VNIR/SWIR split.

**Affects:** signal levels, hence SNR, hence Phase 5's SNR requirement line.
**Replace with:** answers to **Q3** and **Q5**.

---

## A-4 — Orbit is a conventional sun-synchronous default

**Status:** OPEN
**File:** `config/orbit/default.yaml`

550 km, sun-synchronous, 10:30 local overpass, 30 m GSD, 60 km swath, 4 ms
integration. A mid-morning descending orbit is the conventional choice for land
imaging; 30 m GSD matches SCANFI and the CFFDRS fuel type layer, which makes
comparison convenient.

Overpass time is not a free parameter scientifically: it sets the solar zenith
angle, and the spring overpasses at 45–60° N that Phase 1 must sample are
exactly the high-SZA, high-risk case.

**Affects:** illumination geometry in Phase 1 scenarios, signal level in Phase 2.
**Replace with:** answers to **Q2**.

---

## A-5 — VNIR band set is provisional

**Status:** OPEN by design — Phase 4 resolves this
**Files:** `config/bands/config_a.yaml`, `config_b.yaml`, `config_c.yaml`

All three configurations carry the same six VNIR bands at Sentinel-2 centres
(490, 560, 665, 705, 740, 865 nm). This is a starting point, not a result: the
brief has Phase 4 optimise the VNIR set, and the whole point of the study is to
replace the working priority list with a nested ranking.

FWHM values are round numbers, not derived from a filter design. One consequence
is already visible: the 740 nm band at 20 nm FWHM has skirts reaching the O2-A
band, which `safari-bands validate` reports as a warning. Sentinel-2's B6 avoids
this with 15 nm FWHM. Worth revisiting in Phase 4/5.

**Replace with:** the Phase 4 nested ranking.

---

## A-6 — Index catalogue is for baselines only

**Status:** by design, not a placeholder
**File:** `config/indices.yaml`

The catalogue exists to support the heritage index baseline (Phase 4.3) and to
make results interpretable. Methodological rule 3 forbids using index thresholds
as retrieval labels and rule 4 requires band sets to be judged by training the
provisional retrieval model on them.

Recorded here so the distinction is not lost later: a band set that can form
more indices has **not** been shown to be better at anything.

---

## A-7 — Environment: numpy is capped below 2.6

**Status:** OPEN, technical
**File:** `pyproject.toml`

`prosail` 2.0.5 (Phase 1) depends on numba, and numba 0.67 requires
`numpy>=1.22,<2.6`. The `sim` extra pins accordingly.

Two things this confirms, checked before committing to the stack: `prosail`
ships a pure-Python universal wheel, so Phase 1 needs no Fortran toolchain on
Windows; and it implements PROSPECT-5 and PROSPECT-D with 4SAIL, but **not**
PROSPECT-PRO. The brief asks that PROSPECT-PRO availability be checked — the
answer is that it is not in the Python package, so PROSPECT-PRO would mean
porting from Féret's R `prospect` package or calling R.

The system Python (Windows Store 3.12.10) has an incompatible numpy/scipy pair
installed globally; the project uses `.venv` and does not touch it.

---

## A-8 — Phase 2 atmospheric tooling is unverified on Windows

**Status:** OPEN, technical — check before planning Phase 2
**File:** none yet

Py6S needs the 6S Fortran executable built separately, and libRadtran is
effectively Linux-only. Neither has been tested here. This may force WSL, a
container, or precomputed look-up tables for Phase 2.

---

## A-9 — Empirical arm runs on a 20 m grid, with mixed native resolutions

**Status:** OPEN — resolvable by a sensitivity check
**Files:** `Fire_Risk_Model/src/data/bands.py`, `config/bands/sentinel2_11band_candidates.yaml`

Sentinel-2's bands are native at 10 m (B2/B3/B4/B8), 20 m (B5/B6/B7/B8A/B11)
and 60 m (B1/B9). They must share one grid, and the choice is a confound for
band ranking.

20 m was chosen so the bands the study most cares about — the red edge and
**B11 SWIR1** — are never interpolated. Ranking a band on upsampled data would
judge it on an artificially smooth version of itself. The 10 m bands are
**averaged** down (what a coarser detector would integrate); the two 60 m
atmospheric bands are **bilinear** up.

Earth Engine's default differs by direction and only one direction needed an
explicit call: downsampling reads the image pyramid, which averages, while
upsampling defaults to nearest. The per-band plan is recorded in the HDF5
attrs so the confound stays checkable.

**Residual risk:** B1 and B9 remain mostly interpolation at 20 m. They are
excluded from the default surface input for that reason.
**Replace with:** a 10 m variant and a rank-stability check across the two.

---

## A-10 — NBAC perimeters carry unburned inclusions

**Status:** OPEN — bounded, not eliminated
**File:** `Fire_Risk_Model/src/data/labels.py`

The primary per-pixel label rasterises NBAC fire perimeters, which are
**filled**. Real perimeters contain unburned islands — wet depressions, rock,
open water — conventionally 5–20% of the interior. NBAC is therefore a noisy
per-pixel label and an accurate patch-level one.

This is accepted deliberately. A noisy label that is independent of the inputs
supports a band ranking; a clean label that is a *function* of the inputs (the
old dNBR threshold on B8/B11) does not. `inclusion_rate()` is recorded per
patch so the noise can later be bounded empirically.

**Replace with:** nothing available. CanLaBS severity would quantify it but is
itself NBR-derived, which reintroduces the SWIR circularity.

---

## A-11 — Fuel-type cut points are judgement, pending calibration

**Status:** OPEN — calibration script written, not yet run
**File:** `Fire_Risk_Model/src/data/fuel_type.py`

Deriving an FBP fuel type from SCANFI needs thresholds the FBP System does not
specify as hard classes: percent conifer at 0.20/0.80, crown closure 0.40 for
C-1 against C-2, canopy height 10 m for C-3 against C-4.

Two things reduce the exposure. First, the **model input is continuous**
(`fuel_vector`, percent conifer first), so no cut point enters the retrieval —
they are needed only to compare against the published layer's discrete classes,
which is a reporting step. Second, the published CFFDRS 2024 layer encodes
percent conifer in its own codes (625 = 25%, 650 = 50%, 675 = 75%, 415 = 15%),
so the comparison is a regression and `calibrate_cut_points()` can replace the
guesses with whatever best reproduces the layer.

**Replace with:** the output of `scripts/python/fuel_type_agreement.py` over
the real patch set. Needs Earth Engine credentials and SCANFI sidecars.

---

## A-12 — Leaf-on window is a fixed date rule

**Status:** OPEN
**File:** `Fire_Risk_Model/src/data/fuel_type.py`

D-1/D-2, M-1/M-2 and O-1a/O-1b differ *only* by broadleaf phenology, so the
derivation needs a leaf-on flag. It defaults to day of year 140–275, bracketing
the boreal green season.

Deliberately a crude explicit rule rather than something inferred from the
imagery: inferring the season from reflectance would make the fuel-type label
depend on the same data the label is meant to be compared against.

Note the published layer declines to choose at all — its codes are "D-1/D-2"
and "M-1/M-2" — because a static annual map cannot know an acquisition date.
Its one grass class is labelled "O-1a Matted Grass", asserting a season it
cannot vary; that is handled as a named interpretation in
`fuel_agreement.LAYER_SEASON_AMBIGUOUS` rather than edited into the
transcribed code table.

**Replace with:** a per-patch green-up date, if one can be sourced
independently of the imagery.

---

## A-13 — Foliar moisture is a per-patch scalar, never a raster

**Status:** by design, not a placeholder
**Files:** `Fire_Risk_Model/src/data/cffdrs_features.py`, `terrain.py`

FBP computes FMC from elevation, latitude/longitude and date. Elevation is the
only one of those that varies within a patch, so a per-**pixel** FMC raster
would vary *solely* with elevation — it would be an elevation channel under
another name, reintroducing precisely the geography shortcut `terrain.py`
excludes it to avoid ("1200 m means Cordillera").

FMC is therefore a scalar computed from patch-mean elevation. That is also what
FBP itself assumes (a stand-level value) and matches how the weather features
enter.

---

## A-14 — FWI spin-up ends at the composite end date

**Status:** OPEN, and load-bearing
**Files:** `Fire_Risk_Model/src/data/fwi.py`, `scripts/python/build_cffdrs_dataset.py`

The FWI codes are recursive and DC carries ~53 days of memory, so a value for
an acquisition needs a long preceding window. The assembly script uses **30
June** as the composite end, matching the April–June pre-fire S2 window.

This is the sharpest leakage surface in the whole covariate set. If the window
overruns the acquisition by even a few days into the fire period, the fire's
own weather propagates forward through the recursion into its own predictor,
and the model would score spectacularly while meaning nothing.
`compute_fwi_series` therefore **refuses** rather than warns.

**Replace with:** the true per-patch composite end, if the download records it.
The composite window is not currently stored per patch.

---

## A-15 — O2-A forbidden region narrowed to clear Sentinel-2 B7

**Status:** OPEN, same provenance as A-1
**File:** `config/atmospheric_windows.yaml`

The O2-A region was 755–775 nm. Adding Sentinel-2's B7 (783 nm, 20 nm FWHM)
as a candidate rejected it by 2 nm: its FWHM extent is 773–793.

B7 is an operational band returning usable surface reflectance, so the edge was
wrong rather than the band. Narrowed to 755–**772**. The physical justification
is that the O2-A rotational lines end near 771 nm and transmittance recovers
quickly above that; the empirical one is that B7 works in orbit.

This is the second time a hand-set region edge rejected a demonstrably working
band — the first set the two-threshold scheme after it rejected S2's 1610 nm.
Both point the same way: **replace these edges with a computed transmittance
threshold in Phase 2** rather than continuing to adjust them one band at a time.

---

## A-16 — SCANFI is pinned to the 2020 time step

**Status:** OPEN — affects every use of SCANFI, not just the fuel comparison
**File:** `Fire_Risk_Model/src/data/scanfi.py` (`_select_time_step`)

`_select_time_step` returns **2020 for every patch year**: 2018, 2021, 2023
and 2024 all resolve to the same product. SCANFI v2 publishes 5-year steps
from 1985 to 2025, so later steps exist and are simply not wired in.

Two consequences, and the second is the serious one.

A patch imaged in 2023 is described by 2020 ecology, so stand attributes are
up to several years stale — tolerable for slow-changing structure, not for
anything disturbance-sensitive.

More importantly it makes the vintage mismatch against the published CFFDRS
fuel layer **fixed and uncorrectable**. The layer is 2024, SCANFI is 2020, and
any ground that burned between them has the two sources describing different
stands. Measured on fire and confuser patches that is a percent-conifer MAE of
0.79–0.88, against 0.22–0.30 on unburned ground. See
`docs/results/fuel_type_agreement.md`.

It also blocks the decisive test of that explanation: re-running SCANFI at the
layer's own vintage is impossible while the selector is pinned, so the
explanation stays inferred rather than isolated.

**Replace with:** the nearest available SCANFI step per patch year, if the
later products are published in the same layout the remote reader expects.
