# Stage 1 brief: band design study for the SAFARI fuel-condition imager

This brief summarizes a planning discussion between James and Claude (claude.ai, September 2026). Items marked **hypothesis** are for this study to test. Items marked **proposed** have not yet been confirmed by James.

## 1. Mission context

SAFARI is a cubesat multispectral imaging mission for wildfire fuel-condition monitoring in Canada, being prepared for the CSA CUBICS 2026 announcement of opportunity. Known design context:

- The payload should be as COTS as possible.
- VNIR (silicon) and SWIR (InGaAs) are expected to be separate chains. Band-to-band registration between them, especially at snow/forest boundaries, is a flagged engineering risk.
- Onboard processing is planned. The SoC choice (Zynq, PolarFire SoC, SmartFusion2) is open, pending orbit and mission duration.
- A SWIR band near 1600 nm is planned. The working priority list is SWIR1, SWIR2, red edge, NIR, red, green, blue. This study replaces that list with a nested ranking of band sets weighted by marginal cost (section 5), because band value is conditional: nearly every SWIR moisture metric contrasts against NIR, and VNIR bands are far cheaper to add than SWIR ones.

**Terminology.** In fire science, "fire risk" usually means ignition probability. SAFARI measures fuel condition, which feeds *fire danger* rating (CFFDRS). Use "fuel condition" and "fire danger" in outputs.

## 2. Where Stage 1 sits (proposed three-stage architecture)

| Stage | Question | Output |
|---|---|---|
| 1. Band design study (this repo) | Which bands should exist? | Spectral requirements with traceable retrieval performance |
| 2. Retrieval model | What is the fuel condition in this pixel? | LFMC, curing/NPV, % conifer, dead fir, fuel type, each with uncertainty |
| 3. Danger synthesis | What does that mean for fire? | CFFDRS outputs using weather (outside this repo) |

Stages 1 and 2 are coupled: a band set is only "best" relative to the retrieval that uses it. Stage 1 therefore contains a provisional Stage 2 (GPR with an ARD kernel and/or a small MLP) trained on each candidate band set.

The intended Stage 2 design follows the precedent of SL2P, the SNAP Sentinel-2 biophysical processor, which CCRS runs in Earth Engine via the LEAF Toolbox: regression trained on radiative transfer simulations, then calibrated and validated with field data. SL2P is known to underestimate over forests, with bias linked to canopy clumping. That is why forest scenarios here need a discontinuous-canopy model, not a turbid-medium model alone.

## 3. Retrieval targets

Priorities between targets are an open question for James (section 9). Until he answers, weight them equally and report per-target results.

**T1: Live foliar/canopy moisture.** LFMC (%) = 100 × Cw / Cm, where Cw is equivalent water thickness and Cm is dry matter per area. Reflectance responds strongly to Cw and weakly to Cm, so bands that sense only water yield EWT, not LFMC. At canopy scale, the ratio of canopy water to canopy dry matter cancels LAI, so leverage on dry matter matters.

The key case is the conifer spring dip. Jolly et al. (2014) found that foliar density changes explained 96.7% of LFMC variation in red and jack pine, driven by starch and sugar accumulating in previous-year needles. That is a dry-matter signal that water-only bands will miss. Detecting a Cm change needs at least two water-sensitive bands with different water-to-dry-matter absorption ratios.
- **Hypothesis H1:** SWIR1 + SWIR2 resolves Cm changes; SWIR1 + 1240 nm may partially substitute.

**T2: Curing / non-photosynthetic vegetation (NPV) fraction** of grass fuels. FWI2025 accepts grassland curing as an optional input, with remote sensing as an accepted source; its current remote-sensing option is NDVI-based greenness. Cellulose/lignin absorption near 2100 nm drives NPV/soil separation.
- **Hypothesis H2:** SWIR2 is necessary for T2, and 1240 nm is not a substitute.

**T3: Mortality and defoliation.** Mainly dead balsam fir from spruce budworm (FBP fuel types M-3/M-4).

**T4: Fuel type and percent conifer** (FBP M-1/M-2). Snow-on imagery separates conifer from leafless deciduous canopy.

**Ancillary requirements.** These are not targets but they constrain the band set:
- cloud/snow discrimination (green + SWIR1);
- snow-off timing (FWI season start-up is keyed to snow disappearance as a surrogate for ground thaw);
- water vapour and aerosol for atmospheric correction (dark-target aerosol retrieval pairs ~2.1 µm with blue/red).

**Out of scope.** Dead surface fuel and duff moisture (the FWI moisture codes) are weather-driven and hidden under canopy.

Reference index families, for baselines and interpretability only (band selection targets the variables above, not indices):

| Target | Indices (bands) |
|---|---|
| Canopy water / LFMC | NDMI ≡ NDII, MSI (NIR, SWIR1); Gao's NDWI (NIR, ~1240 nm); NMDI (NIR, SWIR1, SWIR2) |
| Curing, NPV, dry matter | NDTI ≡ NBR2 (SWIR1, SWIR2); CAI (narrow 2.0/2.1/2.2 µm bands, hyperspectral only) |
| Greenness, phenology, stress | NDVI, EVI, VARI (blue, green, red, NIR); NDRE (red edge, NIR) |
| Disturbance, burn history | NBR/dNBR (NIR, SWIR2) |
| Snow/cloud, winter conifer mapping | NDSI (green, SWIR1) |

Caution: in grass and shrub fuels, visible greenness indices can track LFMC deceptively well because greenness and moisture co-vary seasonally. That shortcut fails in evergreen conifers.

## 4. Scenarios to simulate

- **Fuel types:** C-2 black spruce; C-3/C-4 jack pine; M-1/M-2 mixedwood across the percent-conifer range; budworm-affected fir (M-3/M-4); D-1/D-2 aspen; O-1 grass; C-1 lichen woodland (bright lichen background).
- **Seasons:** the snowmelt-to-green-up window first, since it is high-risk and the hardest retrieval case; then midsummer drought; then autumn curing and leaf-off.
- **Confounders, varied independently of the targets:** LAI; canopy cover and clumping; background (soil, litter, moss, lichen, patchy snow); sun–view geometry, including the high solar zenith angles of spring overpasses at 45–60° N; smoke/haze (via the atmosphere); topography (optional, later).

## 5. Hardware constraints and configurations

- **VNIR on silicon (~400–1000 nm):** an extra band costs filter area and pixels, little else.
- **Standard InGaAs:** cuts off near 1.7 µm, so 1240 nm, ~1610 nm and a 1375 nm cirrus band can share one COTS detector.
- **SWIR2 (~2100–2300 nm):** needs extended-wavelength InGaAs (much higher dark current, deeper TEC cooling) or HgCdTe. This is the main cost/SWaP driver.

Configurations to compare. The VNIR set itself is optimised in Phase 4.

| Config | SWIR content | Detector |
|---|---|---|
| A | ~1610 nm | standard InGaAs |
| B | ~1240 + ~1610 nm on the same focal plane | standard InGaAs |
| C | ~1610 + ~2200 nm | extended InGaAs |

Config B shares optics and focal plane with SWIR1, so it adds no new cross-chain registration problem. The key output is the fraction of C's retrieval performance that B recovers, per target.
- **Hypothesis H3:** B recovers a good share for T1 canopy water, but little for T2 or the dry-matter side of T1.

Match Sentinel-2 band centres where it costs little (nominal 490, 560, 665, 705, 740, 865, 1610, 2190 nm). This enables cross-calibration, training on the S2 archive and filling revisit gaps. Rank bands by marginal retrieval value per marginal cost, not by value alone.

## 6. Work plan

For each phase: plan first, get approval, implement with tests, then write a results note in `docs/results/`.

### Phase 0: Scaffolding

Build the package skeleton, config schemas with validation, pytest setup and an environment file. The config schemas cover:
- **Band set:** centre, FWHM, SRF shape, out-of-band leakage.
- **Detector:** QE curve, dark current vs temperature, read noise, full well, pixel pitch.
- **Optics:** aperture, f-number, transmission.
- **Orbit:** altitude, GSD, integration time, local overpass time.

*Done when:* configs load and validate, tests pass, and a README explains the layout.

### Phase 1: Forward model (leaf + canopy)

- **Leaf:** PROSPECT-D or PROSPECT-PRO (Cw; Cm, or proteins + carbon-based constituents; Cab, Car, Cbrown, N).
- **Canopy:** 4SAIL first, for grass and open fuels and as a baseline. Put it behind an interface so a discontinuous-canopy model (INFORM, 4-Scale or DART) can be swapped in for conifer stands.
- **Backgrounds:** from spectral libraries (soil, litter, moss, lichen, snow).
- **Priors:** per fuel type and season, sampled with Sobol or LHS.
- **Output:** 1 nm top-of-canopy reflectance, 400–2500 nm, with parameters (parquet or zarr).

*Done when:* spectra reproduce a reference implementation within tolerance, and unit tests confirm physically sensible behaviour (e.g. increasing Cw lowers SWIR reflectance).

*Implementation notes:* the Python `prosail` package implements PROSPECT-5/D with 4SAIL. Check PROSPECT-PRO availability (Féret's R `prospect` package) before porting. ARTMO (MATLAB) bundles radiative transfer models, global sensitivity analysis and a GPR band-analysis tool, and can serve as a cross-check.

### Phase 2: Atmosphere and sensor

- **Atmosphere:** top-of-atmosphere radiance with 6S (Py6S) or libRadtran, varying water vapour and aerosol.
- **Sensor model:** SRF convolution; photon, dark and read noise → per-band SNR.
- **Perturbations:** filter centre shift (angle of incidence, temperature) and out-of-band leakage.
- **Surface reflectance:** assume a standard atmospheric correction, with its residual error treated as a noise term.

*Done when:* `simulate_measurement(scene, band_set, sensor, geometry)` returns noisy radiance/reflectance, with SNR documented at reference radiances.

### Phase 3: Global sensitivity analysis

Compute Sobol first-order and total indices (SALib) per wavelength, for each target against the nuisance parameters, per scenario.

*Done when:* plots and a note identify where Cw, Cm, NPV and pigments dominate, and where LAI, cover and background swamp them.

### Phase 4: Band selection

1. **Information content.** Use Jacobians from the forward model, prior covariance from the parameter priors and noise covariance from the sensor model. From these, compute posterior error and degrees of freedom for signal per target. Then run greedy forward selection over a candidate grid (centre × FWHM, within atmospheric windows and detector limits) to produce a nested ranking.
2. **Wrapper check.** Train the provisional retrieval model on each top-ranked set. Report RMSE, bias and uncertainty calibration on scenario-held-out data.
3. **Controls and baselines.** Positive benchmark: a Sentinel-2-equivalent band set. Negative control: a deliberately poor set. Heritage baseline: an index-based retrieval.

*Done when:* nested ranking tables exist (per target and weighted), with and without noise, and any disagreement between the information-content and wrapper results is explained.

### Phase 5: Hardware trade and spec derivation

Evaluate configurations A/B/C with realistic detector models. Measure how retrieval error responds to:
- FWHM;
- SNR;
- band-to-band relative calibration;
- filter centre shift;
- VNIR/SWIR misregistration (inject sub-pixel shifts across synthetic forest/snow and forest/clearcut edges).

*Done when:* a requirements table exists (centre ± tolerance, FWHM, minimum SNR at reference radiance, relative calibration, co-registration), with each line traced to a target accuracy.

### Phase 6: Empirical checks (later; needs data access)

- **Real spectra:** convolve real hyperspectral data with the candidate SRFs. Sources: EnMAP, PRISMA, EMIT (south of ~52° N only), and AVIRIS-NG from NASA's ABoVE campaign over boreal Canada and Alaska.
- **Ground truth:** James's own LFMC and curing sampling, plus lab dry-down spectra.
- **Fire-outcome relevance tests:** these use archive sensors (e.g. HLS), so they only cover bands those sensors measure. Use within-fire designs (CFSDS daily progression, CanLaBS v2 severity), which control for ignition and weather.

## 7. Accuracy targets

To be set with James. Principle: tie each target's required accuracy to a CFFDRS threshold that changes a fire-behaviour prediction. FWI2025 proposes rating classes tied to physical processes, and FBP crown-fire initiation depends on foliar moisture. Until targets are set, report full error distributions.

## 8. Why the rules in CLAUDE.md exist

They come from a review of Kanyini's onboard smoke-detection band selection (Lu et al. 2024).

What went wrong there:
- The HS2 training data were synthesized from VIIRS, which overlaps only 11 HS2 bands. The rest were filled by duplicating or averaging VIIRS bands, so every selection method "found" the real bands by construction.
- Labels came from a threshold rule on the same bands.
- Importance rankings picked near-duplicate bands (VIIRS I2 and M7 share 846–885 nm).
- Random splits of tiles that overlapped by 50% risked leakage between training and test sets.

Practices worth keeping:
- retraining the real model on each band set;
- positive and negative controls;
- doing selection on training data only;
- repeated runs with error bars.

## 9. Open questions for James (seed `docs/OPEN_QUESTIONS.md`)

1. Priority weights across T1–T4.
2. Orbit altitude, local overpass time, target GSD and swath.
3. Optics: aperture, f-number, transmission; integration time; TDI availability.
4. Candidate detectors with datasheets for silicon CMOS, standard InGaAs and extended InGaAs (QE, dark current at operating temperature, read noise, full well, pitch, TEC capability).
5. Filter architecture (strip filters on one area array, filter wheel, separate cameras); this affects registration.
6. Cost/SWaP proxies for configurations A–C.
7. Accuracy targets per variable.
8. Priority regions and fuel types.
9. Confirmation of the proposed three-stage architecture.

## 10. Key references and datasets

Verified during planning:

- Jolly, Hadlow & Huguet (2014), IJWF 23(4):480–489, doi:10.1071/WF13127. Dry matter drives seasonal conifer LFMC.
- Jolly et al. (2014), spring dip in red and jack pine, *Advances in Forest Fire Research* (Coimbra), hdl:10316.2/34114.
- Yebra et al. (2024), Globe-LFMC 2.0, *Sci. Data* 11:332, doi:10.1038/s41597-024-03159-6. No Canadian sites; US jack and red pine are the nearest analogues.
- Lu et al. (2024), Kanyini onboard smoke detection, IEEE JSTARS, doi:10.1109/JSTARS.2024.3394574.
- CFS Fire Danger Group (2025), *The 2025 Update to the FWI System*, Information Report GLC-X-42. Code: https://github.com/nrcan-cfs-fire/cffdrs-ng
- SCANFI v1 (2020, 30 m): doi:10.23687/18e6a919-53fd-41ce-b4e2-44a9707c52dc; paper doi:10.1139/cjfr-2023-0118. SCANFI v2 (5-year steps, 1985–2025): doi:10.23687/07653869-f303-46c2-a04e-9ab479b73cbf.
- CFFDRS FBP Fuel Types 2024, 30 m: https://open.canada.ca/data/en/dataset/4e66dd2f-5cd0-42fd-b82c-a430044b31de
- Barber et al. (2024), Canadian Fire Spread Dataset, *Sci. Data* 11:764, doi:10.1038/s41597-024-03436-4.
- CanLaBS v2 burn severity (NBAC perimeters 1985–2024, 30 m): doi:10.23687/2af751e7-79f9-4da8-9b45-14688818dca3.
- SNAP biophysical processor ATBD: https://step.esa.int/docs/extra/ATBD_S2ToolBox_L2B_V1.1.pdf
- LEAF Toolbox (CCRS; SL2P in Earth Engine): https://github.com/rfernand387/LEAF-Toolbox
- Fernandes et al., validation of SL2P Sentinel-2 fCOVER, fAPAR and LAI products over North American forests (CCRS).

From background knowledge; citation details not verified, so check before citing:

- Yebra et al. (2013), global review of remote sensing of LFMC for fire danger (*Remote Sens. Environ.*).
- Ceccato et al. (2001), detecting leaf water content in the optical domain.
- Féret et al. (2021), PROSPECT-PRO.
- Verrelst et al. (2016), spectral band selection with Gaussian process regression.
- Somers et al. (2010), Instability Index (ISI) band selection for spectral unmixing.
- Rodgers, information-content channel selection for atmospheric sounders.
