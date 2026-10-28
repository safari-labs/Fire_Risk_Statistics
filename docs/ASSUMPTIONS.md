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

**Status:** RESOLVED 2026-10-23 — all nine steps wired in, opt-in; 2020 stays
the default for the legacy sidecars. Measured vintage leakage is in A-25.
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

---

## A-17 — Patch rasters are EPSG:3978 at a true square 20 m

**Status:** RESOLVED — was a defect, now a fixed convention
**File:** `Fire_Risk_Model/src/data/download.py` (`PATCH_CRS`)

Earth Engine's `getDownloadURL` with no `crs` returns EPSG:4326 and applies
`scale: 20` as 20/111320 **degrees on both axes**. That is 20 m north-south
but 20·cos(lat) m east-west — 11.4 m at 55° N, 7.8 m at 67° N. The first
11-band download therefore wrote 877×501 patches rather than 501×501.

Three consequences, each one defeating a decision the 20 m grid was chosen to
implement:

1. **B11, B5, B6, B7 and B8A were upsampled 1.75×–2.6× in longitude.** Those
   are exactly the bands the 20 m packing grid exists to deliver without
   interpolation. On one axis they were interpolated anyway.
2. **The stretch varies with latitude.** A 3×3 kernel spanned 34 × 60 m at a
   55° N site and 23 × 60 m at 67° N, so spatial scale became a function of
   where the patch is — the same class of geographic confound the terrain
   work had to control for with a within-region test.
3. **About a third of sites were silently lost.** The inflated requests
   exceeded the 50 MB `getDownloadURL` cap, so 82 of 120 fire sites landed
   and the shortfall was indistinguishable from missing cloud-free imagery.
   The client-side size estimate computed the pixel count for a square-metre
   grid while GEE delivered a square-degree one, so it was low by exactly the
   factor that made the request fail.

Patches are now requested in **EPSG:3978** (Canada Atlas Lambert), giving
true 20.00 × 20.00 m pixels. Verified on the 67.117° N site that previously
failed: 676 × 675 × 11 bands, square pixels, no nodata. EPSG:3978 is also the
CRS NBAC, the published CFFDRS fuel layer, SCANFI and CanLaBS already use, so
sidecar reprojection onto the patch grid is close to identity instead of
another resample.

**Side effect, accepted:** the lat/lon bounding box reprojects to a slightly
larger rectangle in Lambert, growing with latitude — 10.0 km at mid-latitude,
13.5 km at 67° N. Ground sampling is uniform 20 m everywhere, which was the
objective; the extra area is real imagery, and it means northern sites yield
somewhat more 256-px tiles. Not corrected, because cropping back to exactly
10 km would discard valid data to buy a uniformity nothing downstream needs.

The superseded patches are kept at
`data/stage2_fire/patches_11band.anisotropic_4326/` as evidence only.

---

## A-18 — The payload is one Mantis head with four modes

**Status:** CONFIRMED by James (datasheet extract)
**Supersedes:** the framing in configurations A/B/C (brief §5), and an
earlier version of this entry that read the options as two separate sensors

One imager, **<1U, TRL-9**, four modes:

| Mode | Type | Bands | Range |
|---|---|---|---|
| Snapshot | RGB or monochrome | — | — |
| Push broom | **Multispectral** | **6** MS | **400–1000 nm** |
| Push broom | **Hyperspectral** | **96** HS | **470–900 nm** |
| Push broom | **SWIR** | **4** SWIR | **1000–1750 nm** |

The three pushbroom modes are the decision. An earlier reading of this had
them as two separate sensors and costed the SWIR half against Dragonfly's
Chameleon SWIR (2.5U, 1.6 kg, 11.2 km swath) — a different product. Those
figures are withdrawn, not adjusted: Mantis SWIR is a mode of the same <1U
head.

### What this changes

**The band counts are fixed.** The nested ranking still reports every k, but
only two rungs are decisions: the best **6** of 400–1000 nm and the best **4**
of 1000–1750. Marginal gain at k=7 is unreachable, not a trade.

**HS is not a strict upgrade on MS.** It is narrower: 470–900 against
400–1000. It buys ~4.5 nm sampling by surrendering both ends, and in
Sentinel-2 terms that costs exactly **B1 (443, coastal/aerosol)** and **B9
(945, water vapour)** — ten candidate bands for MS, eight for HS.

**Five of the 96 HS bands are not surface bands.** At 4.5 nm spacing, bands
near 754, 759, 763, 768 and 772 nm fall inside the O₂-A absorption; a
contiguous dispersive sensor cannot avoid placing detector columns there.
They are marked `purpose: atmospheric`. The effective surface count is **91**.

**Configuration C is retired.** It pairs 1610 with 2190 nm on extended
InGaAs, and 2190 is outside every mode's range. Any recommendation to bring
B12 into the study is moot — including one made earlier in this project.
**H1** as written ("SWIR1 + SWIR2 resolves Cm changes") has no real option
behind it; its fallback clause, SWIR1 + 1240 nm, becomes the live question,
and four SWIR bands is exactly the budget for it. **H2** survives only as a
possible reason to reject the SWIR mode for curing, never to specify SWIR2.

### What our data can and cannot decide

| Mode | S2 bands in range | Decidable from data in hand? |
|---|---|---|
| MS, 400–1000 | **10** | **Yes** — best 6 of 10 is exactly the nested ranking |
| HS, 470–900 | 8 | **Partly** — the MS-vs-HS *reach* question is answerable; 96-band resolution is not |
| SWIR, 1000–1750 | **1** (B11) | **No** — four cannot be chosen from a pool of one |

The MS-vs-HS comparison has a sharp, cheap test that needs no new data: run
the VNIR selection over all ten S2 bands and see whether B1 or B9 earns a
place in the best six. If either does, HS forfeits something measurable. If
neither does, HS surrenders nothing and its extra bands are pure gain.

What HS cannot be judged on from Sentinel-2 is what 96 bands at 4.5 nm buy
over 6 — ten samples cannot be interpolated into ninety-six, and rule 2
forbids trying. That needs AVIRIS-NG, EnMAP or PRISMA, which also answer the
SWIR mode. One hyperspectral dataset settles both.

### Costs that are not band count

- **Downlink.** 96 bands is ~16× the per-pixel volume of 6, against a budget
  already under validation.
- **Onboard inference.** The first convolution's width scales with input
  channels, and stream BRAM is ⌈width_bits/18⌉ × ⌈depth/1024⌉ per stream, so
  96 channels widens every inter-layer FIFO. This is the input-channel axis
  the hardware sweep already measures.
- **Registration.** MS and SWIR are different focal planes whether or not
  they share a housing. NDMI, NDII and NMDI all contrast NIR against SWIR, so
  cross-chain misregistration lands on exactly the products the SWIR mode is
  carried for. Any combined arm must be scored **with** a misregistration
  term.

### Open

Whether MS and SWIR can run **simultaneously**, or are alternative
configurations selected per acquisition. If alternatives, "both" means two
Mantis units and the cost doubles; if simultaneous, "both" is nearly free.
This decides the shape of the whole trade and nothing else in it can be
settled first.

## A-19 — The 1750 nm top of the SWIR sensor sits past the standard InGaAs cutoff

**Status:** OPEN — a hardware question for James, surfaced by config validation
**Files:** `config/detector/ingaas_std.yaml`, `config/bands/swir4_worldview3.yaml`

The SWIR pushbroom is specified **1000–1750 nm on standard InGaAs** (A-18).
Standard InGaAs cuts off near 1.7 µm. The top ~50 nm of the stated range is
therefore past the detector's edge, and our modelled QE curve shows the
approach is not gentle:

| nm | 1500 | 1600 | 1650 | 1700 |
|---|---|---|---|---|
| QE | 0.80 | 0.78 | **0.70** | **0.40** |

Response is already halved at 1700 and falls off a cliff beyond it. A band
centred at 1730 would sit where QE is a small fraction of the plateau — and
the InGaAs cutoff wavelength shifts with temperature, so whatever response
remains is also the least thermally stable part of the range.

This surfaced when the WorldView-3 SWIR set was added as a benchmark.
WV-3's four bands below 1750 nm — 1209, 1572, 1661, 1730 — are exactly four
bands in exactly this window, which is why they are a natural benchmark. But
WV-3 carries eight SWIR bands reaching 2365 nm, so its detector is **HgCdTe,
not InGaAs**. Its placements were chosen against a far longer cutoff, and
they do not transplant: the validator rejected `swir_1730` on `ingaas_std`
outright, and warns that `swir_1661`'s SRF skirt (1621–1701 nm at 2× FWHM)
will be clipped by falling QE.

`swir4_worldview3.yaml` therefore declares `swir_1730` on `ingaas_ext`. That
is not a recommendation to fly extended InGaAs — it is the config refusing to
state something physically false, and it makes the benchmark's cost visible:
**this particular four-band set is not achievable on standard InGaAs alone.**

### What to resolve

1. Is the 1750 nm figure a nominal envelope, or is a band genuinely intended
   above 1700? If the usable top is really ~1700, the two sub-windows for
   four bands are roughly 1000–1300 and 1500–1700, which is tighter than
   A-18 assumed and changes where the four bands can sit.
2. If a band above 1700 is wanted, the detector is not standard InGaAs. A
   1.9 µm extended variant is cheaper than the 2.2 µm part configuration C
   would have needed, but it is still extended — deeper cooling, higher dark
   current, and the SWaP consequences the brief flags as the main cost driver.
3. The QE curve itself is a **placeholder** (Q4, A-2), so the exact cutoff
   shape is representative rather than a datasheet figure. The conclusion is
   robust to that — 1.7 µm is the defining property of the technology, not of
   a particular part — but the margin at 1650–1700 is not.

**Until resolved:** treat 1700 nm as the usable top for band-placement work,
and carry the WV-3 set as a benchmark that is partly out of reach rather than
as a candidate specification.

---

## A-20 — MS and SWIR run simultaneously, split by a dichroic on one aperture

**Status:** CONFIRMED by James
**Supersedes:** the misregistration argument in A-18 and in
`sensor_mantis_ms_plus_swir.yaml`, which assumed two independent instruments

The optical design is a shared fore-optic with a dichroic beamsplitter: SWIR
is **reflected** at 90° onto the InGaAs focal plane, VNIR is **transmitted**
to the silicon one. Both run at once. GSD and swath are the same for both.

### This defuses the registration risk, and I had it overweighted

A-18 argued that "both" must be scored with a misregistration term because
NDMI, NDII and NMDI all contrast NIR against SWIR, so cross-chain error would
land on exactly the products the SWIR mode is carried for. That reasoning was
right for two separate telescopes. It is largely wrong here.

A shared aperture with a dichroic means both chains see **the same scene,
through the same optics, at the same instant, from the same geometry**.
Registration is then an alignment-and-thermal-stability problem between two
focal planes on one bench — bounded, characterisable, and correctable by
calibration — rather than a parallax-and-timing problem between instruments.
Cross-chain indices are well-posed by construction.

The residual term is real but much smaller: focal-plane mounting tolerance,
dichroic wedge, and differential thermal drift across the bench. It should
still be measured in Phase 5, but as a tolerance to specify rather than a
penalty that could disqualify the combined option.

With equal GSD and swath confirmed, the combined arm also carries **no
coverage penalty**. The earlier 11.2 km versus 32 km argument came from the
Chameleon mis-identification and is withdrawn entirely.

### What the dichroic introduces instead

**The crossover is a design parameter, and a band sits in it.** A dichroic
edge is not a step; it has a transition region, typically some tens of nm.
With the split near 1000 nm:

- **B9 (945 nm, ~20 nm wide, so 935–955)** sits within ~50 nm of the
  crossover. Its transmission depends on where the edge is placed and how
  steep it is. If the VNIR selection finds B9 valuable, the dichroic
  specification becomes coupled to that result — and B9 is already one of the
  two bands that distinguishes MS from HS (A-18).
- The SWIR chain's short end at 1000 nm sits on the other side of the same
  transition, so the shortest usable SWIR band is bounded by it. Our
  provisional 1240 nm slot is comfortably clear; a band nearer 1000 would
  not be.

**A hypothesis worth confirming:** the HS mode stops at 900 nm rather than
1000. That could be silicon QE falling away, or it could be staying clear of
the dichroic crossover. If the latter, the MS mode's own 1000 nm top is
optimistic in the same way, and both edges move together if the dichroic is
re-specified.

**Throughput.** A dichroic costs a few percent in reflection and rather more
in transmission. Both chains therefore see slightly less light than a
dedicated single-chain instrument would. Small, but it belongs in the SNR
budget rather than being assumed away.

### Open

Where the dichroic edge sits, and how steep it is. It bounds the MS mode's
red end, the SWIR mode's blue end, and B9's usability at once.

## A-21 — The usable AVIRIS-NG pre-fire pool is 42 lines, not 228

**What we assume:** Phase 6's hyperspectral evidence rests on 42 AVIRIS-NG
flight lines, 12 flown in 2018 and 30 in 2022, and not on the 228 figure
quoted in earlier versions of the data inventory and experiment plan.

**Why, measured against the archive on 2026-10-16:** the per-year boundary
shapefiles describe where the aircraft flew, not what ORNL DAAC published.
Of the 574 Canadian footprints, 163 have a reflectance (`rfl`) product in
ABoVE_Airborne_AVIRIS_NG_V3, and the shortfall is structural, not scattered:

| Year | Canadian footprints | With a reflectance product |
|---|---|---|
| 2017 | 244 | **0** |
| 2018 | 21 | 19 |
| 2019 | 165 | **1** |
| 2022 | 144 | 143 |

(The 2019 release holds 272 products, almost all of them Alaska. The 2021
release is Iceland.)

The pre-fire condition and the published years then pull against each other.
228 of the 574 footprints precede a burn in NBAC 2019-2023, but only 42 of
those are published, because a 2022 line can only precede a 2023 burn. The
burn years behind the 42 are {2019: 3, 2020: 2, 2021: 2, 2022: 8, 2023: 35}.

**Why this is still enough for its job:** the question is where four SWIR
band centres go, and the unit that matters is labelled spectra, not flight
lines. 42 scenes at ~5 m is tens of millions of pixels, each a contiguous
380-2510 nm spectrum, every one labellable by SCANFI and NBAC. Band
placement is limited by spectral and ecological diversity, which 42 lines
spanning 57-68 N across two seasons supplies, not by line count.

**What it does cost, and this is the real constraint:** lead time. 35 of the
42 precede a 2023 burn only, so most of the pool supports "this stand burned
the following year" and not a multi-year curve. And the geography is
unchanged and still narrow — nothing east of -93.2 degrees, so no Quebec
black spruce and no budworm fir (see Q25).

**How it was found:** `--check-auth` returned HTTP 404 where a 401 was
expected. A wrong URL announces itself as a 404 while you are braced for a
wrong password, which is why the cheap check exists: the first selection
drew all three of its lines from 2017 and would have failed on every one,
after the four-minute NBAC pass, with nothing on disk to show for it.

**Revisit if:** a V4 release publishes the 2017 and 2019 Canadian
reflectance, which would take the pool from 42 to something near 228.

## A-22 — The SWIR candidate grid is 1003-1359 and 1414-1749 nm, measured

**What we assume:** band placement for the Mantis SWIR mode searches two
sub-windows, 1003-1359 nm (72 channels) and 1414-1749 nm (68 channels), for
140 candidates in total.

**Why, read from the data rather than assumed:** the first AVIRIS-NG line
downloaded (`ang20180721t192935_rfl_v2r2`) carries the instrument team's own
bad-band list, which is a statement of which channels return no surface
signal. It flags three runs:

| Bands | Wavelengths | Cause |
|---|---|---|
| 197-206 | 1363.6-1408.6 nm | water vapour |
| 285-318 | 1804.3-1969.6 nm | water vapour |
| 424 | 2500.5 nm | detector edge |

Everything else from 376.9 to 2495 nm is marked usable. Inside the SWIR
mode's 1000-1750 nm range that leaves the two windows above.

**What this corrects:** the experiment card previously searched 1000-1300 and
1500-1750, a grid chosen from the general knowledge that water vapour sits
"around 1400" and "around 1900". The measured gap is 1364-1408 — narrower on
both sides — so 1300-1359 and 1414-1500 are usable and were being excluded
for no reason. That is roughly 25 extra candidate channels, and one of them
is 1572 nm, which is a WorldView-3 centre and part of the positive control.

**The 1270 nm O2 band is still excluded, separately.** The bad-band list does
not flag it, and that is consistent rather than contradictory: AVIRIS-NG flies
at ~20 km through a fraction of the atmospheric column an orbital instrument
looks through, so an absorption feature that is tolerable from an aircraft can
be disqualifying from orbit. Rule 7's margin around 1270 therefore stands on
its own reasoning and is imposed on top of the bad-band list, not derived from
it.

**Other instrument facts from the same header,** which the SRF convolution
needs: 425 bands, 376.9-2500.5 nm, 5.01 nm mean spacing, FWHM 5.57-6.03 nm,
float32 BIL, `data ignore value = -9999`, 5.1 m pixels on UTM/WGS-84.

**Revisit if:** a line from the 2022 campaign carries a different bad-band
list. The grid above is read from a 2018 line, and the per-year calibration
files named in the header differ between campaigns.

## A-23 — T1 external validation rests on 2,884 Globe-LFMC records, none Canadian

**What we assume:** the only real LFMC labels available to this study are
2,884 Globe-LFMC 2.0 records in Canadian-relevant tree species that fall
inside the Sentinel-2 two-satellite era, across 83 sites, all in the United
States.

**Measured from the file on 2026-10-16**, not quoted. Globe-LFMC 2.0 is one
72.5 MB xlsx, **CC0**, no login, from the figshare collection
`10.6084/m9.figshare.c.6980418` (file DOI `10.6084/m9.figshare.25413790`,
sha256 `cec5e596…`). 293,796 records, 15 countries. The brief's statement that
there are **no Canadian sites is correct** — verified directly.

Of those, 104,229 (35.5%) are from 2017 or later, which is when Sentinel-2 had
both satellites flying. Intersecting that with species that map to FBP fuel
types:

| Species | FBP type | All | ≥2017 | Sites | LFMC range |
|---|---|---|---|---|---|
| *Pinus banksiana* | C-3/C-4 jack pine | 3,993 | **1,296** | 29 | 21–220% |
| *Pinus resinosa* | red pine | 3,467 | **1,202** | 27 | 77–184% |
| *Populus tremuloides* | D-1/D-2 aspen | 273 | 177 | 6 | 74–273% |
| *Abies balsamea* | M-3/M-4 balsam fir | 126 | 82 | 5 | 74–175% |
| *Picea glauca* | white spruce | 208 | 76 | 8 | 66–163% |
| *Picea mariana* | **C-2 black spruce** | 182 | **51** | 8 | 73–120% |
| *Larix laricina* | tamarack | 0 | 0 | — | — |
| *Betula papyrifera* | white birch | 0 | 0 | — | — |
| | **total** | 8,249 | **2,884** | 83 | |

**The good news is sharper than "no Canadian sites" suggests.** Jack and red
pine supply 2,498 of the 2,884, and the dominant coordinates (46.10 N,
−86.40) are in Michigan's Upper Peninsula — the same species and region as
Jolly, Hadlow & Huguet (2014), which is the paper the spring-dip argument and
hypothesis H1 both rest on. So the one mechanism this study most needs to
test has real measurements behind it, from the study that proposed it.

**The bad news is C-2.** Black spruce is the single most important Canadian
fuel type and has **51 records at 8 sites**. Any claim about C-2 LFMC
retrieval rests on that, and 51 records across 8 sites will not support a
per-fuel-type accuracy figure.

**GLOBE-LFMC CONTAINS NO SPECTRA.** It carries LFMC, coordinates, date,
species, elevation, slope, IGBP land cover and a weather block (precipitation
at 24 h / 3 d / 1 wk / 4 wk / 12 wk, relative humidity at four times of day,
temperature, vapour pressure, wind). Using it as a label set therefore means
pairing each record with a Sentinel-2 acquisition ourselves, which is new
download work and introduces its own matching tolerance (how many days
between the sample and the overpass).

**This cannot validate the SWIR design.** Sentinel-2 has one band between
1000 and 1750 nm, so a Globe-LFMC pairing tests the VNIR set plus B11 and
says nothing about where four SWIR bands go. That stays with AVIRIS-NG
(A-21, A-22).

**One quality flag to resolve before use:** the jack pine minimum is 21%,
which is not a live-foliage value. The file carries both an
`Extra information/Quality Flag` and an `Isolated data point` column; these
have not been applied to the counts above, so the usable total may be lower.

**Revisit if:** Canadian field sampling becomes available, which would
replace the analogue argument with the real thing, or if Globe-LFMC 3.0 adds
Canadian sites.

---

## A-24 — Fire dates come from NBAC; negatives get matched pseudo-dates

**What we assume:** each fire patch's fire starts on the EARLIEST of the hotspot
start (`HS_SDATE`), the agency start (`AG_SDATE`) and the start of any NBAC
polygon overlapping it (amended 2026-10-24, James; was `HS_SDATE` first; see
A-32); a confuser takes the start day-of-year of the fire it
precedes, in its own year; other negatives draw a day-of-year from the
start-date distribution of their latitude band, seeded by the stem.

**Measured 2026-10-23** (`Fire_Risk_Model/scripts/python/nbac_fire_dates.py`,
reading the .dbf directly because fiona cannot iterate NBAC's null dates):
all 99 fire patches match a polygon, all with `HS_SDATE`; 95 of 108 confusers
match. The other 13 have no NBAC polygon at their location even with NBAC
2024 and 2025 unpacked (Q27): they get pseudo-dates like the other negatives,
until the NFDB fetch (Stage C) can date their source fires. The 99 patches are 82 fires; 91 are
cause "Natural". **66 of 99 fires started on or before 30 June** -- inside the
April-June composite and before the 30-June weather date every patch used.
That is the size of the early-fire leakage the fire-date design removes.

**Risk:** the pseudo-date rule is itself a possible shortcut (dates differ by
class). Control: E-43, a classifier on day-of-year and latitude alone, must
score about 0.5.

---

## A-25 — Fuel inventories: which vintage is pre-fire, measured

**What we assume:** a fuel input is usable as "CFFDRS as is" on a fire patch
only if it predates that fire, and this is checked on the burned pixels, not
inferred from the nominal year.

**Measured 2026-10-23** on NBAC-burned pixels of the 99 fire patches:

| Source | Resolution | Burned pixels read as non-fuel | Pre-fire? |
|---|---|---|---|
| CWFIS FBP layer 2024 | 30 m | **73.9 %** | **no** -- burn scars are written in |
| CWFIS 2019 (decision-tree build, v20191114) | 250 m | 1.0-4.5 % by fire year | yes, all years |
| CWFIS national grid 2014b | 250 m | 1.2-6.0 % | yes, all years |
| SCANFI v2 2015 | 30 m | no age reset or closure drop | yes, all years |
| SCANFI v2 2020 | 30 m | shows the 2019 and 2020 fires | yes for 2021-2023 only |
| SCANFI v2 2025 | 30 m | shows every fire | no -- the post-fire control |

So the operational pre-fire fuel is the 2019 CWFIS layer (or 2014b), and the
SCANFI pre-fire step is `mode="pre_fire"` (2015 for 2019-2020 fires, 2020
otherwise). The 2014b and 2019 code tables collide with the 2024 one (101 is
C-1 in 2014b and non-fuel in 2024), so each vintage keeps its own codes and
sidecar (`fbp_fuel_layer.FUEL_VINTAGES`).

**Also found:** SCANFI channels 13-17 (water, rock, shrubs, herbs, bryoids)
come from ESA WorldCover **2021** for every step -- post-fire for 2019-2020
fires and their confusers whatever SCANFI step is chosen. The 2019 archive
ships the CFS decision tree (`FuelLayer_categorize_fbp_fuel_types_from_
decision_tree.R`, Swystun 2018) whose closure and height cut points (black
spruce C-1 < 30 % closure, C-2 30-70 %, C-4 >= 70 % and < 7 m; pine C-3 vs C-4
at 7 m) are the official counterpart to A-11's judgement thresholds; the
SCANFI fuel reference should be built with it.

---

## A-26 — CFFDRS "as is" means FWI1987 codes with FBP1992, at 13:00 LDT

**What we assume:** the operational reference pairs the Van Wagner (1987) FWI
codes in `fwi.py` with FBP1992 (ST-X-3, with the Wotton et al. 2009 updates).
NRCan: **FWI2025 must not be used with FBP1992** (recorded here at last; Q18
said it was). The weather observation is the FWI1987 standard **13:00 local
daylight time** (GLC-X-42 p.6), with the 46 deg N day-length table, as the
`cffdrs` R package does. A latitude-corrected day length is a separate,
non-imagery variant (G5), not the reference.

**Validated 2026-10-23 against the `cffdrs` R package** (1.9.2;
`Fire_Risk_Model/tests/test_fwi_cffdrs.py`, `test_fbp_behaviour.py`). The FBP
port agrees to ~1e-12 on 6,000 seeded rows. `fwi.py` did not agree at first --
up to 2.8 FFMC points -- and was corrected to the reference: the FFMC rain
correction above 150 % moisture now uses the pre-rain moisture (Van Wagner
1987 eq. 3b; it had used the updated value), the FFMC constant is the exact
250 x 59.5 / 101 rather than the printed 147.2, and DMC wetting uses
280 / e^(0.023 P0) with an unrounded 43.43 x 5.6348. All six codes now agree
to ~1e-14. `_fwi.json` sidecars built before this are legacy.

**Ignition, interim:** until the continuous ignition models' coefficients are
in hand (Q26), R0's ignition branch uses the GLC-X-42 Table 1 classes (FFMC
for sustainable flaming ignition, DMC for lightning ignition) as an ordinal
score. Those thresholds are set against FBP2025/FWI2025; GLC-X-42 states an
FWI1987 FFMC of 91 corresponds to about 91 in FWI2025, which is the basis
for applying them to Van Wagner codes.

**Season start** follows GLC-X-42 Appendix C-2: DMC/DC start three days after
snow disappears, or after three days above 12 C, both "surrogates" for ground
thaw -- which is what an observed snow-off date (the imagery slot) replaces.

---

## A-27 — The final test set is grouped by fire as well as by place

**What we assume:** patches are grouped as connected components over a shared
0.1-degree block OR a shared NBAC fire, and the v2 test set is the v1 test set
closed under that grouping.

**Why:** the 99 fire patches are 82 fires; grouping by block alone let 8 fires
sit in two splits of the current pack, 5 across train and test. Nothing has
been reported on the test split yet, so it is fixed rather than retracted.
Frozen in `Fire_Risk_Model/splits/test_groups_v1.json` (35 patches, 15 groups,
sha256 `3e65e310...`). Cross-validation folds for v2 use the same groups.

---

## A-28 — Ignition receptivity is in scope; fire occurrence prediction is not

**What we assume:** the mirror rates three CFFDRS processes (GLC-X-42 p.32 and
Table 1): ignition, spread, intensity. Ignition means the probability of
*sustained* ignition given a firebrand -- a fuel and moisture property.
FOP (expected fires per 20 km cell from ignition-source density) stays out.

**Stage C's limitation, stated:** the ignition outcome is NFDB/NBAC
lightning-caused starts against controls matched on date and weather cell.
Lightning strike locations are not held (CLDN is commercial), so controls hold
weather fixed but not strike density. GOES GLM is a partial filter where it
reaches.

---

## A-29 — The CubeSat decision rules, fixed before the results

**What we assume:** the study's three decisions are made by these rules,
written down on 2026-10-23 before any CFFDRS-mirror result exists.

1. **Bands and indices.** Per-slot nested band-set rankings are weighted by
   that slot's measured value to CFFDRS (its paired delta per process);
   processes weigh equally until Q1/Q28 says otherwise. Whole nested sets are
   combined, never single-band scores (rule 1). Choose the smallest k within
   one SE of the best combined score, with every chosen band selected in at
   least 4 of 6 folds; ties go to the cheaper chain (VNIR before SWIR). Keep an
   index onboard only if the index front end matches raw bands at matched k.
2. **Architecture.** At the chosen bands, the smallest preset within one SE of
   the best. A weather-dependent process runs onboard only if its skill at the
   expected uplink age is within one SE of fresh weather; otherwise ground.
3. **Hardware.** The lowest-power Xiphos board (Q7, Q8, Q9) on which the
   chosen model fits at <= 80 % of every resource and meets the per-scene
   latency budget; otherwise report the accuracy-resource Pareto step that
   fits. James (Q28): meet the latency, then minimise power.

   **Budgets, from `CubeSat_Sensors_and_Lenses.xlsx` (Main sheet, Mantis MS
   6 bands, 500-620 km, 2,000 km imaged per orbit):** a scene is
   1000 x 1000 px x 6 bands (12 MB); 63 scenes per orbit at 500 km (51 at
   620 km); orbital period 95.3 min.
   - **Required -- buffered:** every orbit's scenes processed within that
     orbit, which the sheet sizes storage for (0.76 GB/orbit): **<= 91 s per
     scene** (500 km, the binding case; 114 s at 620 km).
   - **Reported -- real-time:** keeping up while imaging (2.63 MB/s): <= 4.6 s
     per scene. Met or not is stated, not required.
   - **Power:** no processor cap in the sheet (cameras draw 6 W imaging); the
     rule minimises board power among boards that meet the latency.
   The selected sheet configuration has no SWIR camera; if the band
   decision adds one, the data rate and these budgets are re-derived from the
   sheet with that camera selected.


---

## A-30: Ignition receptivity from Beverly & Wotton (2007), mapped onto FBP fuel types

**Assumption.** Until the canopy-closure model arrives (Q26), R0's ignition branch is P(sustained flaming) from Beverly & Wotton (2007), *IJWF* 16:161–173, Table 6. Their ten categories come from test-fire sites at Fort Smith and 100 Mile House (1958–61). The FBP fuel types map onto them as follows:

| FBP fuel | Category | Predictors |
|---|---|---|
| C-1 | FC3, pine–lichen | FFMC |
| C-2 | FC8, spruce–moss | FFMC, DMC |
| C-3, C-4 | FC4, pine–moss | FWI |
| C-5, C-6, C-7 | FC5, pine–needles (analogue) | DMC, ISI |
| M-1 to M-4 | FC6, mixedwood–moss | FFMC, DMC |
| D-1, D-2 | FC10, aspen–leaf, FWI-System model | DMC |
| O-1a/b, before leaf flush | FC1 | RH |
| O-1a/b, after leaf flush | FC2 | FFMC |
| S-1 to S-3 | none (NaN) | — |

**Why each choice:**

- **Pine (C-3, C-4).** FC3, FC4 and FC5 come from one jack pine stand and differ only in the ground fuel that was lit. The site description names moss and lichen as predominant, so moss is the default. Ground fuel is an explicit argument, which makes it a candidate imagery slot: lichen is spectrally distinct.
- **Aspen (D-1, D-2).** FC10's FWI-System model has "considerably less support" than its site model. The site model needs measured litter moisture, which we do not have.
- **Seasons.** The paper's spring/summer split is leaf flush, so leaf state selects the grass category.
- **Inputs.** The fits used diurnally adjusted FFMC and ISI. R0 uses the daily 13:00 LDT codes in their place, and the FWI System ISI rather than FBP's slope-adjusted one. Below FFMC 70 the curves are extrapolations, because test fires were only run at FFMC ≥ 70.

**Check.** Our implementation reproduces the paper's own reading of its curves: about 90 % for FC3 at FFMC 86, and about 90 % and 96 % for FC6 and FC8 at DMC 80, FFMC 89.

---

## A-31: The CFS fuel decision tree, run on SCANFI

**Assumption.** The SCANFI fuel reference is the CFS decision tree that built the 2019 CWFIS layer (Swystun 2018, shipped with that layer), run on each SCANFI v2 time step. It is implemented in `Fire_Risk_Model/src/data/fuel_tree.py` and outputs the 2019 code space. The A-11 judgement rules (`fuel_type_from_ecology`) are kept only as a rule-set comparison.

SCANFI cannot feed the tree everything it expects. The deviations:

- **Non-fuel.** The kNN layer splits fuel from non-fuel at 60 % vegetated; SCANFI has no such layer. Only WorldCover water is used as non-fuel, because WorldCover 2021 is post-fire for the 2019–2020 fires: a burn scar reads as bare ground. Rock outcrops therefore fall to the open-ground rule (D-1/2).
- **Layers not held.** Ecozone, NALCMS, cropland and urban are not held. The open-ground refinements (O-1, non-fuel, D-2) are skipped, and the taiga branches take their non-taiga side (C-2 instead of C-1).
- **Species.** SCANFI's species channels stand in for the kNN leading species:
  - OtherCon (white spruce, lodgepole and Douglas-fir, merged when sidecars are aligned) takes the spruce/subalpine-fir rules.
  - WRPine takes the white-pine rules.
  - Poplar takes the broadleaf-fill rules.
  - Tamarack counts as broadleaf, as in the tree.
- **A-11 comparison arm.** The same post-fire concern applies, so its non-treed channels are restricted to water.

**Leaf state for the legacy R0.** The legacy R0 uses 30-June weather (A-24), so leaf state is "green": D-1/2 resolves to D-2, M-1/2 to M-2, and an unresolved O-1 to O-1b. Codes a layer names explicitly (D-1, M-1 at 15 or 25 %) keep their name. P3 replaces this with the green-up date.

---

## A-32: The dated design, which supplies P3's weather, start-up and leaf state

**Assumption.** From P3 on, each patch is scored on its own date D (A-24), with inputs built the way operational CFFDRS builds them. The P3 decisions were made by James on 2026-10-24.

- **Fire date.** D is the earliest of NBAC's `HS_SDATE`, its `AG_SDATE`, and the start of any other NBAC polygon overlapping the patch. This amends A-24, which used `HS_SDATE` first. An earlier D can only make every input more strictly pre-fire. Confusers take their target fire's day of year in their own year. Unburned patches, and the 13 confusers with no target polygon, draw a day of year from the development fires in their latitude band (<55, 55–60, ≥60 °N), seeded by the stem. Test-group fires are excluded from that pool.
- **Weather is read on D−1**, from ERA5-Land *hourly* at 13:00 LDT:
  - **Observation time.** 13:00 LDT equals 12:00 LST, the FWI1987 observation time. The UTC hour uses the nominal standard zone round(lon/15). Across our patches this sits within an hour of the legal zone.
  - **Variables.** Temperature, RH (Magnus, over water) and 10 m wind speed and direction at that hour.
  - **Rain** is the 24 h ending then. It comes from ERA5-Land's accumulated `total_precipitation` as acc(d, h) + acc(d, 00) − acc(d−1, h), checked against `total_precipitation_hourly`.
  - **Previous scheme.** The pre-P3 daily-aggregate scheme (daily maximum temperature, daily-mean dewpoint and wind, UTC-day rain) is kept as the variant `daily_flat`.
- **Start-up (GLC-X-42 Appendix C-2), operationalised:**
  - A day is snow-covered when ERA5-Land snow cover is at least 50 %.
  - **Snowy winters.** If any day from 1 January to 1 March is snow-covered, the season starts on the third consecutive snow-free day on or after 1 March.
  - **Snowless winters.** Otherwise it starts on the third consecutive day at or above 12 °C at 13:00.
  - **Season end.** The season ends the day before the first run of three snow-covered days on or after 1 August, or on 31 December if there is none.
  - **Previous season.** It starts from the default values (FFMC 85, DMC 6, DC 15).
- **Overwintered DC** (Lawson & Armitage 2008) uses `cffdrs`'s coefficients, a = b = 0.75 (James).
  - Winter precipitation is ERA5's total precipitation, rain plus the water equivalent of snow, from the fall end to the spring start.
  - Overwintering often returns the floor of 15 after wet boreal winters. That is the formula working, not a missing value.
- **Before the season starts.** If the season has not started by a lag day, the codes there are the start values, flagged `season_started = False`.
- **Day length (E-50).** The variant scales Van Wagner's 46 °N DMC factors by astronomical day length at the patch latitude over that at 46 °N, mid-month. This is our construction:
  - `cffdrs`'s `lat.adjust` only changes latitudes at or south of 30 °N.
  - FWI2025's hourly sunrise-to-sunset DMC changes more than day length.
- **Leaf state on D** comes from the CWFIS daily green-up product (1 km, 1 = green, held for 2020–2023), per pixel.
  - **Fallback.** For 2019, or dates outside 1 April–31 October, each pixel takes the majority of its 2020–2023 values on the same calendar day, and is leafless outside that window.
  - **FBP and ignition.** Green resolves D-1/2 to D-2, M-1/2 to M-2, O-1 to O-1b, and Beverly & Wotton grass to FC2.
  - **FMC.** It is computed for day of year D.
- **Second "cffdrs" weather source (E-52).** It is the nearest CWFIS station reporting all six codes on D−1 (2010s and 2020s exports), kept for every lag.
  - Those codes are CWFIS's own, under each agency's start-up.
  - Provincial agency stations are not in the export.
  - **Distance cap.** A station more than 300 km away is not one CFFDRS would use for the patch. One 2018 confuser's nearest reporting station was in Nebraska, 1,062 km away. Such patches get no station weather. The median distance is 56 km (90th percentile 132 km).
- **Imagery estimators move to P6.** Sentinel-2 snow-off and green-up (E-18's and E-40's imagery arms) go to P6, so P3 uses no imagery (James).

---

## A-33: Pre-fire imagery, dated labels and the v2 pack (P4)

**Assumption.** From P4 on, the imagery the models see ends the day before D, and the labels count only what burned from D on.

- **Pre-fire composite** (`Fire_Risk_Model/src/data/prefire.py`). It is a Sentinel-2 SR median over D−45 to D−1, built on the exact grid of each patch's existing `_bands.tif`, so every sidecar stays aligned.
  - **Widening.** If fewer than 90 % of the patch's pixels have at least one clear observation, the window widens to D−90 to D−1.
  - **Fallback.** If it is still too thin, the composite comes from the previous year's 1 July to 30 September. That is leaf-on and pre-fire, but a season early, and it is flagged (`composite_fallback`).
  - **Clear observation.** s2cloudless probability below 40, as in the existing pipeline, and Scene Classification not cloud shadow, cloud, cirrus or snow.
  - **Masking snow and shadow is new.** The legacy pipeline masked cloud only. Its April–June composites therefore carry spring snow: on one 55 °N patch, B4 is 750 against 339 and B11 937 against 1,382.
  - **Unchanged legacy.** The legacy `_bands.tif` is untouched.
- **Dated labels** (`labels.rasterize_dated`).
  - **1:** inside an NBAC polygon whose fire (earliest of HS/AG start) began on or after D.
  - **255 (ignore):** inside one that began before D, or has no start date.
  - **0:** elsewhere.
  - **Current effect.** Because D is the earliest start of any polygon overlapping a fire patch, no development or test pixel is currently ignored. Every burned pixel carries over from the legacy label.
  - **NBAC 2016–2018** were fetched so the 19 confusers from those years are labelled too.
- **v2 pack** (`src/data/pack_v2.py`, `scripts/python/pack_cffdrs_v2.py`).
  - **Contents.** Fire, confuser and unburned patches, as 256 px tiles on the v1 grid rule. The bands are reflectance from the pre-fire composite. Alongside them: the dated label, CWFIS 2019 and SCANFI-tree fuel codes, eight per-pixel slots (percent conifer from each source, closure, height, slope, aspect, leaf state on D), and a per-patch scalar vector. The scalars hold:
    - the operational codes at lags 1, 2, 3 and 7;
    - the start-up, day-length and daily-aggregate variants;
    - the station codes and station distance;
    - FMC on D, day of year, place, and the composite window and fallback.
  - **Excluded.** The bare, cloud and water patches are spectral hard negatives without dates or weather. They stay in the v1 line.
  - **Splits.** The test set is the frozen v1 test set exactly (asserted). Every other group goes whole to train or val by its members' v1 split (majority, ties to train), so no fire or 0.1° block straddles train and val.
  - **Radiometry** is left to the loader (P5), unlike v1's pre-normalised tiles.
- **As built (2026-10-25).**
  - **Best window.** When no window reaches 90 % coverage and last summer has no scenes, the composite is the best-covered window, recorded `accepted: false`. This affects three 2016–2017 confusers, from before Sentinel-2 surface reflectance covered these areas well.
  - **Excluded from the pack.** Development patches whose composite covers under half the patch are left out of the pack (2 patches).
  - **Memory limit.** High-latitude 90-day windows exceed Earth Engine's per-request memory; those are fetched four bands at a time, giving the same composite.
  - **Test set.** It is the 33 frozen test patches of the cohort's kinds. The other 2 frozen test patches are bare, cloud or water, outside the cohort.
  - **Pack size.** Train 162 patches (1,388 tiles), val 32 (283), test 33 (287). The bundle is `Fire_Risk_Model/data/stage2_fire_cffdrs_v2.tar`, sha256 `177717f1…`.

---

## A-34: The CFFDRS-structured network (P5)

**Assumption.** The learned rungs (`Fire_Risk_FW/src/fire_risk_fw/cffdrs_net.py`) are built and trained as follows.

- **The physics in the network** is a torch copy of the validated NumPy port.
  - **Parity.** The torch FBP matches the NumPy port to 1e-9 on the 6,000-row `cffdrs` fixture, and gradients are finite everywhere.
  - **Non-fuel convention.** Non-fuel and water get intensity 0 *and* P(sustained flaming) 0, where the P2/P3 evaluator excluded them from the ignition score. Within-patch ignition AUC therefore reads higher under the network (fold 0, same 18 fires: 0.672 against 0.573).
- **Starting point.** R2's logit starts as log1p(HFI) − 7, so HFI ≈ 1,100 kW/m maps to 0.5. Its residual on the CFFDRS inputs, every imagery correction and R4's free imagery branch start at exactly zero. R2 begins as R0, R3 and R4 begin as R2, and anything they add is learned.
- **Imagery corrections** pass through the unchanged physics:
  - percent conifer ± 30 points;
  - foliar moisture ± 30 % (clamped to 60–140);
  - crown base height × e^(±0.7);
  - curing ± 30 points.
  
  Leaf state has no correction form: its imagery arm is a replacement (Sentinel-2 green-up, P6).
- **Operational ("cffdrs") values:**
  - percent conifer from the fuel source (CWFIS code, or SCANFI continuous);
  - FMC on D from the FBP equations;
  - CBH from the ST-X-3 defaults;
  - curing 80 %, the FBP default, because the CWFIS curing product is not held;
  - leaf state from the CWFIS green-up product.
- **Weather.** Codes come from the configured source, variant and lag. Wind, RH and FMC are packed at lag 1 from ERA5 only, so lagged and station configurations pair their codes with those.
- **Scalars never broadcast as inputs.** They enter only through the physics and one per-patch danger term in the logit, as in `fusion.TwoHeadFusion`.
- **Training.**
  - **Crops.** Random 128 px crops, with no flips or rotations: aspect and wind are bearings, so rotating a tile changes the fire FBP computes. Evaluation uses full 256 px tiles.
  - **Loss.** Masked BCE: ignored and invalid pixels drop out.
  - **Selection.** Pooled pixel AUC on the held-out fold. Pooled, within-patch and between-patch AUC are all reported.
- **Folds.** 5 folds of whole groups (fire / 0.1° block, from the frozen file) over train plus val, split seed 0, and 3 training seeds. Contrasts are paired by fold and seed. The test split is never staged to the node.
- **Data handling.**
  - A patch missing any scalar a configuration reads is dropped (the one station-capped patch).
  - R0 is evaluated, not trained.
  - Configurations are JSON, so the cluster environment needs no YAML wheel.
- **Resources** are a first guess: 3 h, one A100, 12 CPUs, 24 GB per fit. They get recalibrated from `fits.jsonl` after the first array.

---

## A-35: How the slot sweep runs on Narval, and what it scores (after P7)

**Assumption.** From the second sweep on, `Fire_Risk_FW/scripts/shell/sweep_slots.sh` and `run_slots.py` work as follows. The first sweep (slots_v2, job 7289478) ran under A-34's first-guess request.

- **Measured on slots_v2** (300 fits, A100):
  - R0: 13–16 s per fit.
  - Trained fits: median 3.4 min, max 4.1 min (35 epochs at about 5 s each).
  - Median best epoch: 17 (R1) to 30.
  - Total about 15 GPU-hours.
  - That sweep ran no resource monitor, so GPU and RAM use are not measured for these fits.
- **The request per task** is 0:30:00, one A100, 12 CPUs and 16G:
  - Each task runs 3 fits, so the worst case is 3 × 4.1 min × 2 (safety) plus setup. That rounds up to `narval_resources.py`'s 30-minute floor.
  - 16G follows the v1 measurement on the same input path (1.04 GB MaxRSS).
  - The GPU stays a full A100. A MIG slice would fit in memory but carries its own CPU limit, and the job is input-bound.
- **How the sweep is cut:**
  - The fit list is written once at submission.
  - Tasks are grouped into sub-arrays of 20 (`CHUNK`). Each sub-array waits for the previous one with `afterany`, so a failed task does not stall the chain.
  - `PARALLEL` optionally caps running tasks within a sub-array.
  - R0 runs at seed 0 only, because its three seeds are identical.
  - Results go to `$EXP_NAME/$RUN_ID/<config>/f<fold>s<seed>/`, with task logs and `resource_usage.csv` under `tasks/`.
  - `SKIP_DONE=1` resubmits only the missing fits.
- **Per-fuel-family scores.** Each fit also reports pooled AUC per fuel family (C, D, M, O) and, per patch, within-patch AUC on that family's pixels. These are the outcomes E-36 (M-1/M-2) and E-38 (O-1) registered, which slots_v2 could not provide. The family comes from the fuel layer and leaf state the configuration's physics uses.

---

## A-36: The operational CFFDRS reference (E-55)

**Assumption.** Wherever CWFIS archived what it issued, results are also set against that, not only against our reconstruction. James asked for this on 2026-10-26.

- **Source.** The CWFIS GeoServer's time-enabled WCS (`public:<layer>`, `time=YYYY-MM-DD`), fetched by `Fire_Risk_Model/scripts/python/fetch_cwfis_grids.py`.
- **What is archived:**
  - FWI and the danger class from 2018-01-01;
  - FFMC, DMC, DC, ISI, BUI and the FBP outputs (HFI, ROS, CFB, SFC, TFC, FMC, fuel type) from 2024-01-01.
  - All grids are 2 km in EPSG:3978.
- **Grid alignment.** Requests are snapped to the native grid (origin −2378164.08107, 3854382.22888). An unaligned box is resampled by GeoServer.
- **Per patch:**
  - **The date** is D−1, matching R0's weather.
  - **The value** is the mean of the cells whose centres fall inside the patch footprint. The centre cell is kept as a check (ρ 1.00 with the mean).
  - **The danger class** uses the majority class.
- **Not issued is not missing.** Where CWFIS issued nothing (its season had not started), the patch is left out of the primary result and scored as FWI 0 in a sensitivity check. It is never imputed from our reconstruction.
- **Between patches only.** No operational counterpart exists for within-patch results.
- **Assumed as issued.** The archive is taken to be what was issued on the day. Q30 asks CWFIS whether it was reprocessed.

**Naming (James, 2026-10-26).** Every comparison must say clearly whether its CFFDRS values were actually issued by CWFIS or reconstructed by us. Three terms are used, never interchangeably:

| Term | Meaning |
|---|---|
| **ISSUED by CWFIS** | Values CWFIS published: the archived grids, and the codes it computed at stations (`fwi_obs`). Shown in amber in figures. |
| **Reconstructed (ours)** | R0 to R4, and FWI from ERA5-Land. Every CFFDRS number in P2–P7 is reconstructed unless a line says otherwise. |
| **Operational input products** | Inputs operations also use (the CWFIS fuel layer, green-up product, station weather), fed into our reconstruction. Not issued outputs. |

"Operational" alone is not used for issued values.

**Update after slots_v3 (2026-10-27).**

- **Memory.** `--mem` is now 32G: two of fifteen `r2_warm` fits were killed at 16G at the R1→R2 hand-off. `run_slots.py` frees R1 before R2 trains.
- **Monitor.** `start_monitor` adds `job_mem_MiB`, the job's own cgroup memory. The existing RAM columns are node-wide.
- **Measured use** (45 tasks): 10 min median and 17 min max per task of 3 fits; GPU 25 % median, 1.5 GB peak; setup 38 s.

---

## A-37: The sensor noise model (rule 6; P6)

**Assumption.** Every P6 evaluation adds the noise a CubeSat band would carry, computed by `src/safari_bands/sensor.py` from the detector, optics and orbit configurations (`safari-bands snr <band_set>`). James approved using the placeholder instrument for now (2026-10-27).

- **Signal.** Electrons per unit reflectance, g. A Lambertian surface under a 5778 K blackbody sun at 1 AU (within about 15 % of measured irradiance at 500–2190 nm) is integrated over the band's Gaussian response × QE. The integral is taken through the pupil area, the pixel's solid angle, the optics transmission and the integration time × TDI.
- **Noise.** σ_ρ = √(ρ/g + (dark·t + TDI·read²)/g²): shot noise on the signal, dark current, and read noise once per TDI stage (the conservative digital-TDI case).
- **Reference geometry.** Solar zenith angle 55° (spring overpasses at 45–60°N, brief §4) and a two-way atmospheric transmittance of 0.8 in windows. Both are placeholders.
- **Detector choice.** A band uses the detector it names, else the cheapest that covers its centre: silicon to 1000 nm, standard InGaAs to 1700 nm, extended InGaAs beyond (brief §5).
- **Not subtracted: the source data's own noise.** The P6 inputs are medians of 5–20 Sentinel-2 observations, or 4 × 4 block means of AVIRIS-NG pixels, so their noise is well below one CubeSat acquisition's. The full CubeSat noise is added on top, which slightly overstates the total and errs toward penalising a band.
- **Not modelled yet (Phase 5):** saturation (reported, not clipped; with the placeholder silicon full well, the blue band fills at reflectance 0.24), quantisation, PRNU, stray light, and residual atmospheric-correction error.
- **Every result is reported twice,** noisy and noise-free (rule 6), and labelled as using a placeholder instrument until Q2–Q4 are answered.

---

## A-38: The P6a ecology estimator searches (E-22, E-59, E-62's Sentinel-2 half)

**Assumption.** The ecology band searches are built as follows (James approved the P6 plan, 2026-10-27).

- **Imagery.**
  - The 279 ecology patches are rebuilt as **12-band** Sentinel-2 composites: the 11-band registry plus B12. James approved adding B12.
  - All bands come from one recipe, P4's compositing over June–August 2020 (A-33), on each patch's own grid (`build_ecology_b12.py`). On a test patch the rebuild matched the original 11 bands at r = 0.996.
- **Labels: SCANFI v2 2020,** the imagery's own year (`pack_ecology_v2.py`).
  - **Percent conifer:** needleleaf ÷ all species cover, P0's fix. Tamarack counts as broadleaf, as in the CFS tree.
  - **Closure (%), height (m), biomass, age and land cover.**
  - **FBP fuel family:** from the CFS decision tree on SCANFI. It's an inventory classification, not a CFFDRS output (rule 3).
  - Patches whose SCANFI layers fail to stream after 5 attempts have no labels and are left out.
- **Splits.**
  - 1° blocks, and a seeded 15 % of blocks frozen as the ecology test set (`splits/ecology_test_v1.json`). Any ecology patch inside a fire test cell is forced to the test side; there are none today.
  - Only `dev.h5` reaches Narval.
  - Each task holds out one of 5 outer folds of whole blocks. Band selection runs on an inner block split of the remaining training blocks (rule 5).
- **Model.** The on-chip-sized `TinyEcologyUNet` (base 8, depth 2), with four heads: percent conifer, closure, height and a 7-way fuel family. It trains for a fixed 30 epochs on 128 px crops with no early stopping, so no evaluation fold chooses an epoch.
- **Scores are skills against the training mean** (higher is better):
  - **Regression targets:** 1 − RMSE/RMSE_mean.
  - **Fuel family:** balanced accuracy rescaled so chance = 0, over classes with ≥ 200 pixels.
  - **Combined:** the mean of the four.
  - RMSE in % and m is reported alongside.
- **Searches.**
  - Greedy nested sets up to k = 8, in the raw + indices mode with noise, for the combined skill and for each target.
  - A no-red-edge path excludes B5, B6 and B7 (E-62's Sentinel-2 half).
  - **Evaluation:** every nested set on the outer fold. The combined and no-red-edge paths and the all-bands reference are scored in raw / indices / raw + indices (E-59); every row is scored noisy and noise-free (rule 6).
- **Noise.** The placeholder instrument (A-37), exported as `Fire_Risk_FW/configs/noise/s2_p6_12band_placeholder.json`. It's added to the bands before any index is formed.
- **Indices.** Every index the selected bands can form (the `formable` mode, A-36's catalogue). ECVs are not inputs.
