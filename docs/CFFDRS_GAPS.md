# CFFDRS gaps this study addresses, and whether we can actually test the claim

Each gap below is a weakness in the operational system that a fuel-condition
imager could plausibly fill. For each one: the claim we would make, the
experiment that tests it, and — the part that matters — an honest verdict on
whether that experiment can currently produce evidence.

Three of the six could not. Those are marked and the fix is named.

Sources: *The 2025 Update to the FWI System* (GLC-X-42) §7, the Stage 1 brief,
and the CFFDRS landing page. Where a limitation is stated by CFS rather than
inferred by us, it is quoted.

---

## G1 — Foliar moisture content is computed, never observed

**The gap.** FBP's FMC comes from latitude, longitude, elevation and date
(FCFDG eqs. 5–8). `fbp.foliar_moisture_content` carries the comment that says
it plainly: *"a function of where and when, never of what the vegetation is
doing."* Crown-fire initiation in FBP turns on FMC, so a quantity the system
never measures sits directly under one of its headline predictions.

**Claim we would like to make.** A spectral FMC estimate beats the equation.

**Verdict: NOT TESTABLE AS STATED.** `fmc_measured` is read in four places
and written in none; no sidecar on disk contains it. `FMCArm.MEASURED` falls
through `resolve_fmc` to the equation, and `AUGMENT` therefore reports
`fmc_cffdrs` and `fmc_measured` as the same number. Running the three arms
today would yield three identical results that *look* like "no difference" —
another plausible number from a path that never ran.

The reason is circular and worth stating: producing a validated spectral FMC
needs an LFMC label, and no LFMC label exists in this data (see the T1 row of
the experiment plan).

**Restated claim that IS testable.** *Imagery carries foliar-moisture
information the FBP equation does not.* That is a comparison between a model
given the bands and one given only the FBP FMC scalar — the fusion/rasters
contrast, not the FMC arm. It cannot say our estimate is better than theirs;
it can say the bands contain something the formula misses.

**To make the original claim testable:** Globe-LFMC 2.0 (Yebra et al. 2024)
paired with Sentinel-2 acquisitions, or PROSAIL simulation, or James's own
field sampling. All are outside the current data.

---

## G2 — The fuel-type layer is a fixed vintage

**The gap.** FBP consumes a published fuel-type grid — 2024 in our download,
with SCANFI pinned to its 2020 time step (A-16). Fuel type and percent
conifer change with harvest, insect damage, fire and regrowth, and the layer
does not.

**Claim.** A refreshed fuel estimate predicts fire better than the static
layer, and the advantage grows with how stale the layer is.

**Verdict: TESTABLE.** SCANFI is attached to all 292 fire patches, staleness
spans −4 to +3 years, and the contamination rule excludes the 17 patches
whose associated fire predates the SCANFI vintage. The estimator is the
*slope* against staleness rather than the level, because at gap 0 our
estimate is a noisy copy of its own training target and would lose on noise
alone.

**Blocked on:** training the Stage-1 ecology model, which needs the ecology
set tiled and packed. Re-pack tier.

---

## G3 — Weather station density is thin over most of Canada

**The gap.** Stated by CFS, not inferred: *"The relatively low fire weather
station density in much of Canada is a limitation on model accuracy"*
(GLC-X-42 §7.2). Most of the country's fire weather is interpolated from
sparse points.

**Claim.** Satellite fuel state is worth most exactly where the weather grid
is weakest, because fuel moisture is the integral of weather. That is the
north, which is also where most of the area burns.

**Verdict: NOT TESTABLE — no station data held.** We have ERA5-Land, a
reanalysis grid, which says nothing about where the observing stations are.
Stratifying the increment on distance-to-nearest-station requires the station
network itself.

**Fix, and it is small:** fetch the CWFIS fire-weather station locations and
record a distance-to-nearest-station scalar per patch. Then the existing arms
can be read stratified by it. **Added to the plan as E-1.**

---

## G4 — FWI startup is keyed to snow-off, by regional rule

**The gap.** CFFDRS starts the moisture codes at snow disappearance and
overwinters DC. Operationally that is applied by region.

**Claim.** A per-pixel snow-off date from the imager gives better drought
codes than a regional or fixed rule.

**Verdict: TESTABLE, but we are the worse offender first.** Our own
`fwi.py` has no snow logic at all — a flat 90-day spinup with fixed start
values (FFMC 85, DMC 6, DC 15). For a fire patch the spinup therefore begins
around 1 April, which at 55–67° N is frequently still frozen and snow-covered,
so the recursion accumulates weeks of spurious drying and the error scales
with latitude. DC also never overwinters, erasing the previous autumn's
drought — and 2023, which contributes 2,244 of our perimeters, followed dry
years in the west.

So this is a defect to fix before it is a contribution to offer. **Added to
the plan as E-2.**

NDSI (green + SWIR1) is computable as a server-side reduction over the
Sentinel-2 collection — first date below threshold, per pixel — without
downloading more imagery.

---

## G5 — Day-length factors are tabulated for ~46° N

**The gap.** DMC and DC day-length corrections are tabulated for roughly
46° N while Canada spans 42–83°, giving high-latitude drought codes a
systematic seasonal bias (already recorded in OPEN_QUESTIONS).

**Claim.** Raw weather history lets a model learn latitude-appropriate
weighting that the tabulated codes cannot.

**Verdict: PARTLY TESTABLE — needs a stratified readout.** The weather arms
(CODES / HISTORY / BOTH / HISTORY_DIMENSIONLESS) compare the two
compressions, but a pooled result cannot distinguish "history is better" from
"history is better *at high latitude*", which is the actual claim. The
comparison has to be read stratified by latitude band.

**Fix:** report the weather-arm contrast by latitude band in `pool_bands`.
**Added to the plan as E-3.**

---

## G6 — FOP runs on 20 km cells and cannot see within them

**The gap.** Fire occurrence prediction is cell-based at 20 × 20 km
(GLC-X-42 §7.2). A cell that is 10% tinder-dry grass and 90% wet bog has the
same mean fuel state as one uniformly moderate, and a very different fire
probability.

**Claim.** A 20 m imager supplies the within-cell *distribution* — receptive
fraction, variance, connectivity — which a coarse model structurally cannot
have. 10⁶ pixels per voxel.

**Verdict: OUT OF SCOPE.** FOP is parked by decision. Recorded because the
argument is strong and the product definition it implies (a distribution
summary, not a mean) is worth having if FOP is ever revisited.

---

## G7 — CFFDRS assumes same-day noon observations; a cubesat has yesterday's

**The gap.** Every FWI code is defined on a **noon local standard time
observation of the same day**. A satellite product is not that. Uplink to a
cubesat is daily at best, so an operational danger rating computed onboard, or
computed on the ground from the last uplink, runs on weather that is 24 to 72
hours old. The quantity being produced is therefore not the quantity CFFDRS
defines, and the size of that difference has never been measured against a
fire outcome.

**What we already know, and what we do not.** `era5.py` and `fwi.py` record
the INPUT drift: DC moves 8.2% over a three-day lag while ISI moves 89.9%, and
`fwi.py` argues from that split to a recommendation — BUI is the best single
feature for an uplink-constrained platform, FWI the worst, because FWI
inherits ISI's volatility.

That is an argument about feature values. It is not a measurement of what
staleness costs a **prediction**, and the two can differ: a feature can drift
a long way and still rank fires correctly, or drift slightly in exactly the
direction that matters. Nothing in the study currently tests it.

**Claim.** Fire-danger skill decays with weather age, and it decays at a rate
that depends on which weather representation is used — slowest for the slow
codes and our compressed history, fastest for the fast codes.

**Verdict: TESTABLE, and cheaply, with one wrinkle.**

The design is an EVALUATION-time perturbation, so it needs no retraining per
lag: train once, then score the same model with weather as of
`composite_end − L` for L in {0, 24, 48, 72 h, 7 d}. One trained model, five
scores.

The wrinkle is that the sidecars currently store the codes at
`composite_end` only, so the lagged values have to be computed — an ERA5 pass
over data already held, no new imagery. Once computed they pack as extra
columns, which makes each lag a **column mask** exactly like the weather arms
(see E-4), rather than five packs.

**A pleasant consequence of the leakage guard:** `compute_fwi_series` refuses
a series that runs past its target date, so asking for the codes at an
*earlier* date is strictly safer than asking for them at
`composite_end`. Staleness cannot introduce a leakage path; it can only
remove one.

**Two readings, and they answer different questions:**

| Design | Question |
|---|---|
| train fresh, test stale | what does operational staleness COST a model built on good data? The deployment question, and the primary one |
| train stale, test stale | if staleness is accepted up front, can the model adapt to it? The design question |

**Why it matters beyond our own product:** if the decay is steep for the fast
codes and flat for the slow ones, that is a concrete recommendation to the
operational system about which codes a satellite-fed danger rating should be
built on — and it is the kind of claim this study is well placed to make,
because it needs exactly the fire outcomes and weather history we hold.

**Added to the plan as E-4.**

---

## Gaps we identify and cannot close

**Grassland curing.** FWI2025 accepts curing as an optional input and names
remote sensing as an accepted source; its current option is NDVI-based
greenness. The brief warns greenness tracks moisture deceptively in grass and
shrub because the two co-vary seasonally. So the gap is real — and we cannot
fill it. NDLI needs 1754 nm, past the standard-InGaAs cutoff (A-19); there is
no curing label anywhere in our data; and the ecology set is eight treed and
wetland classes with no grassland at all.

**Duff moisture.** DMC governs lightning holdover, and the brief rules duff
out explicitly: weather-driven and hidden under canopy. Canopy closure, which
we do retrieve, modulates how shielded the duff is — a modifier at best, and
currently speculation.

**The moisture codes generally.** FFMC, DMC and DC are weather-driven and
partly subsurface. No optical sensor reaches them. This bounds the whole
claim and belongs in the results note: the imager contributes **fuel state**,
not fuel moisture codes.

---

## Experiments added or changed by this audit

| | What | Why |
|---|---|---|
| **E-1** | distance-to-nearest-weather-station per patch, and a stratified readout | G3 was unfalsifiable without it — we hold no station locations |
| **E-2** | per-pixel snow-off from NDSI, as the FWI start date, against the flat 90-day spinup | G4, and it fixes a latitude-dependent bias in our own codes first |
| **E-3** | weather-arm contrast reported by latitude band | G5's claim is about high latitude specifically; a pooled number cannot test it |
| **E-4** | weather STALENESS at 0/24/48/72 h and 7 d, per weather arm | G7. The input drift is measured (DC 8.2% vs ISI 89.9% over 3 days); the effect on a PREDICTION is not, and `fwi.py` makes a recommendation that rests on the untested half |

And one claim withdrawn rather than tested: **G1 as originally stated**. The
FMC arms cannot compare a spectral estimate against the equation, because no
spectral estimate exists and none can be produced without an LFMC label. The
restated version — imagery carries moisture information the formula misses —
is testable through the fusion contrast and is what the results note should
say.
