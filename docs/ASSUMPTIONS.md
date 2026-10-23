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

**What we assume:** each fire patch's fire starts on the hotspot start date
(`HS_SDATE`) of the NBAC polygon covering most of it, falling back to the
agency date (`AG_SDATE`); a confuser takes the start day-of-year of the fire it
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

