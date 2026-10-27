# Open questions for James

Seeded from section 9 of the brief. None of these block Phase 0; each names
what is currently assumed instead, and what it blocks downstream.

Answer format: edit the **Answer** line, change **Status** to ANSWERED, and
update the matching entry in [ASSUMPTIONS.md](ASSUMPTIONS.md).

---

### Q1 — Priority weights across targets T1–T4

**Status:** OPEN
**Blocks:** the combined (weighted) ranking in Phase 4. Per-target rankings are
unaffected.
**Assumed meanwhile:** equal weights, per the brief's instruction, with
per-target results always reported separately.

T1 live foliar/canopy moisture · T2 curing / NPV · T3 mortality and defoliation
· T4 fuel type and percent conifer.

**Answer:**

---

### Q2 — Orbit altitude, local overpass time, target GSD and swath

**Status:** OPEN
**Blocks:** Phase 2 radiometry, Phase 5 SNR requirements.
**Assumed meanwhile:** A-4 — 550 km sun-synchronous, 10:30 local, 30 m GSD,
60 km swath.

Overpass time is not just an engineering parameter: it sets solar zenith angle,
and the spring high-SZA case at 45–60° N is the hardest retrieval case in the
study.

**Answer:**

---

### Q3 — Optics: aperture, f-number, transmission; integration time; TDI

**Status:** OPEN
**Blocks:** Phase 2 radiometry, Phase 5 SNR requirements.
**Assumed meanwhile:** A-3 — 70 mm aperture, f/4, 0.75 transmission, 4 ms, no TDI.

**Answer:**

---

### Q4 — Candidate detectors with datasheets

**Status:** OPEN — the most consequential of these
**Blocks:** every SNR number, and therefore every noisy retrieval result.
Rule 6 requires noise in every evaluation, so Phase 4 wrapper results are
provisional until this lands.
**Assumed meanwhile:** A-2 — representative COTS values for silicon CMOS,
standard InGaAs and extended InGaAs.

Needed per part: QE curve, dark current at operating temperature, read noise,
full well, pixel pitch, TEC capability.

The extended-InGaAs numbers matter most, because the A/B/C trade turns on what
the SWIR2 band actually costs in dark current and cooling.

**Answer:**

---

### Q5 — Filter architecture

**Status:** OPEN
**Blocks:** Phase 5 co-registration requirements.
**Assumed meanwhile:** A-3 — unset; separate VNIR and SWIR chains assumed.

Strip filters on one area array, filter wheel, or separate cameras? This drives
band-to-band registration, already flagged as an engineering risk at snow/forest
boundaries. It is also the reason configuration B is attractive: sharing a focal
plane with SWIR1 adds no new cross-chain registration problem.

**Answer:**

---

### Q6 — Cost/SWaP proxies for configurations A, B and C

**Status:** OPEN
**Blocks:** ranking bands by marginal retrieval value *per marginal cost*,
which the brief asks for explicitly. Without this the study can only report
marginal value.
**Assumed meanwhile:** nothing quantitative. The qualitative ordering from the
brief is used: VNIR bands are cheap, standard InGaAs is moderate, extended
InGaAs is the main cost/SWaP driver.

Even rough relative numbers (2×, 5×, 10×?) would make the ranking decision-ready.

**Answer:**

---

### Q7 — Accuracy targets per variable

**Status:** OPEN
**Blocks:** the "traced to a target accuracy" column of the Phase 5
requirements table.
**Assumed meanwhile:** none. Full error distributions are reported instead, per
brief section 7.

The brief's principle: tie each target's required accuracy to a CFFDRS threshold
that changes a fire-behaviour prediction. FBP crown-fire initiation depends on
foliar moisture, which is the natural hook for T1.

**Answer:**

---

### Q8 — Priority regions and fuel types

**Status:** OPEN
**Blocks:** nothing yet; shapes Phase 1 scenario priors and Phase 6 data choices.
**Assumed meanwhile:** the full fuel type list from brief section 4, with the
snowmelt-to-green-up window first.

**Answer:**

---

### Q9 — Confirmation of the three-stage architecture

**Status:** OPEN
**Blocks:** nothing in Stage 1. Asked because Stage 1's scope depends on it.
**Assumed meanwhile:** the proposed architecture (1 band design, 2 retrieval,
3 danger synthesis) holds, and this repo is Stage 1 only.

**Answer:**

---

## Raised during implementation

### Q10 — Is PROSPECT-PRO required, or is PROSPECT-D enough for Phase 1?

**Status:** OPEN
**Blocks:** Phase 1 scope.

The Python `prosail` package implements PROSPECT-5 and PROSPECT-D, not
PROSPECT-PRO (verified, see A-7). PROSPECT-PRO's contribution is splitting dry
matter into proteins and carbon-based constituents — which is directly relevant,
because the conifer spring dip is a dry-matter signal (Jolly et al. 2014) and
hypothesis H1 is about resolving Cm.

Using it would mean porting from Féret's R `prospect` package or calling R from
Python. Worth the effort, or start with PROSPECT-D and revisit?

**Answer:**

### Q11 — How should Phase 2 atmospheric modelling run on Windows?

**Status:** OPEN
**Blocks:** Phase 2.

Py6S needs the 6S Fortran executable built separately; libRadtran is effectively
Linux-only. Options: WSL, a container, or precomputed look-up tables. Worth
settling before Phase 2 is planned. See A-8.

**Answer:**

### Q12 — Is the 400–1750 nm ceiling final, given it cannot test H2?

**Status:** OPEN — scope decision already taken, consequence worth confirming
**Blocks:** nothing; shapes what the empirical arm can conclude.

The empirical band pool stops at 1750 nm, i.e. the standard-InGaAs cutoff
(configurations A and B). That deliberately excludes **B12 at 2190 nm**.

The consequence: **hypothesis H2 — "SWIR2 is necessary for curing and 1240 nm
is not a substitute" — cannot be tested empirically** with this data. Neither
can the SWIR1/SWIR2 contrast behind NMDI and NDTI. H2 remains a simulation
question, and the empirical arm can speak only to what configurations A and B
can do.

B12 is free to add to the Sentinel-2 download (it is a band S2 actually
measures, so rule 2 permits it) even though no SAFARI configuration under
consideration carries it. That would let the data say what the extended-InGaAs
detector would buy, which is the main cost/SWaP decision of the whole study.

**Answer:**

---

### Q13 — Does the Sentinel-2 download record its composite window per patch?

**Status:** OPEN — affects the sharpest leakage guard in the covariate set
**Blocks:** correctness of the FWI codes, not just their precision.

The FWI recursion needs the acquisition date to know where to stop, and
`compute_fwi_series` refuses a series extending past it. The assembly script
currently assumes **30 June**, matching the April–June pre-fire composite.

If the real composite end varies per patch and is later than assumed, the
spin-up window would reach into the fire period and the fire's own weather
would propagate forward into its own predictor. The guard only protects against
what it is told.

Is the composite window recorded anywhere per patch, or can the download be
changed to record it? See A-14.

**Answer:**

---

### Q14 — Which patches get the spectral FMC estimate, and from what?

**Status:** OPEN — blocks the MEASURED and AUGMENT arms
**Blocks:** two of the three foliar-moisture arms.

The BASELINE arm works today: FBP's equation from elevation, latitude/longitude
and date. The MEASURED and AUGMENT arms need an actual spectral estimate of
foliar moisture per patch, and nothing currently produces one.

Options, roughly in increasing effort: a published LFMC index from the
available bands; a regression trained on Globe-LFMC 2.0 (which the brief notes
has **no Canadian sites**, with US jack and red pine the nearest analogues); or
the simulation-trained retrieval this repo's Phases 1–4 are meant to build.

The last is the scientifically right answer and the slowest. Which one feeds
the empirical arm?

**Answer:**

---

### Q15 — Do B8 and B8A both stay in the candidate pool?

**Status:** OPEN — flagged automatically by the validator
**Blocks:** nothing; affects how the ranking should be read.

`safari-bands validate` flags two near-duplicate pairs in the Sentinel-2
candidate set: **B7/B8** (59 nm apart, mean FWHM 68) and **B8/B8A** (23 nm
apart). That is not a defect in the configuration — S2's B8 is a broad 115 nm
NIR band that genuinely overlaps both the narrow B8A and B7.

It matters because near-duplicate bands are exactly the Kanyini failure mode
the rules exist to avoid: its importance rankings picked VIIRS I2 and M7, which
share 846–885 nm. A greedy selection over this pool will face the same
situation honestly rather than by construction, but the result needs reading
with it in mind — "B8 or B8A" may be close to arbitrary.

Keep both and let the nested ranking choose, or drop B8 in favour of the
narrow B8A up front?

**Answer:**

---

### Q16 — Can a later SCANFI time step be wired in?

**Status:** OPEN
**Blocks:** isolating the vintage explanation in the fuel-type comparison, and
the staleness of every SCANFI-derived attribute.

`_select_time_step` returns 2020 for every patch year, though SCANFI v2
publishes 5-year steps to 2025. That pins the comparison against the 2024 fuel
layer to a fixed four-year gap and makes the vintage explanation untestable —
the clean experiment is to re-run SCANFI at the layer's own vintage and watch
the disagreement collapse, and that cannot currently be run.

Is 2020 a deliberate choice (the only step validated, or the only one the
ecology model was trained against), or just the step that was wired first? If
the latter, the remote reader already builds filenames by time step, so adding
2025 may be close to free.

Note it is not purely free scientifically: changing the step changes what the
ecology model was distilled from, so Stage 1 labels and any existing checkpoint
would need re-examining.

**Answer (2026-10-23, measured):** yes, and it is done. All nine steps
(1985-2025) are hosted; `scanfi.py` now takes `time_step=` (a year, or
`"pre_fire"` = latest step strictly before the fire year), writes
`*_scanfi_v2_<year>.npy` beside the untouched legacy file, and keeps 2020 as
the default so the ecology labels and checkpoints are unchanged. Measured on
the fire patches (`scanfi_vintage_leakage.py`): the 2020 step already shows
the 2019 and 2020 fires, is clean for 2021-2023 (90 of 99 fire patches), and
2025 shows every fire. See [ASSUMPTIONS.md](ASSUMPTIONS.md) A-16 and A-25.

---

### Q17 — Should fuel-type agreement be scored on unburned patches only?

**Status:** OPEN — provisional answer already acted on
**Blocks:** the threshold calibration, which is running on unburned only.

On fire and confuser patches the derived and published fuel types describe
different ground, because the patch burned between SCANFI's 2020 and the
layer's 2024. Calibrating thresholds there would tune them against
disturbance rather than against the derivation's error, so the calibration run
is restricted to unburned patches.

That is almost certainly right, but it has a cost worth naming: unburned
patches are, by selection, stable forest. Thresholds fitted there may not
transfer to the recently disturbed and regenerating stands that carry the most
fire interest — and those are exactly the stands the mission exists to watch.

Accept the restriction, or find a disturbance mask that lets burned patches be
included with their post-fire state properly accounted for?

**Answer:**

---

### Q18 — Port the FBP behaviour equations, or compare against FWI only?

**Status:** OPEN — decides how far the CFFDRS comparison reaches
**Blocks:** one rung of the comparison ladder, not the ladder itself.

The study now compares our rating against CFFDRS rung by rung: the raw weather
inputs, each FWI code individually, the FWI subsystem output, each FBP input
individually, the FBP subsystem output, and then our model with and without
those covariates.

Every rung but one is free. `src/data/fwi.py` already emits FFMC, DMC, DC, ISI,
BUI and FWI; `src/data/fbp.py` emits the FBP *inputs* (foliar moisture, wind
direction, percent slope, aspect). The **FBP subsystem outputs** — rate of
spread, head fire intensity, crown fraction burned, fire type — are **not
implemented**, and there is no Python package for them; only the CRAN `cffdrs`
R package covers both systems.

Porting means the fuel-type-specific rate-of-spread coefficients plus the
crown-fire and intensity equations. Sizeable but bounded, and the reference
implementation is open (GPL-2 -- not MPL-2.0 as first written here; checked 2026-10-23 from the installed package. The port therefore implements the published equations and uses the package only for reference outputs).

The question is whether head fire intensity is worth that, or whether FWI as
the operational danger rating is a sufficient baseline. FWI is what a duty
officer actually reads; HFI is what FBP predicts. Note also the NRCan warning
recorded in [ASSUMPTIONS.md](ASSUMPTIONS.md): **FWI2025 must not be used with
FBP1992**, so a port has to pair with the classic Van Wagner codes `fwi.py`
already implements, not with `cffdrs-ng`.

**Answer (James, 2026-10-23):** port it. FBP's own outputs (ROS, HFI, CFB,
TFC) plus the published sustained-ignition relationships become the
non-learned "CFFDRS as is" baseline (R0) that every imagery slot is measured
against; validated against the `cffdrs` R package. Paired with Van Wagner
1987 codes (A-26, which also records the NRCan warning this question cites --
it was not in fact in ASSUMPTIONS until now).

---

### Q19 — Which framing is the headline for the CFFDRS comparison?

**Status:** OPEN — affects what the study claims, not what it runs.
**Blocks:** nothing; both framings are computed either way.

Scored unconditionally ("did this pixel burn"), CFFDRS is at a structural
disadvantage: FWI and FBP predict fire *behaviour given ignition*, not where
fire starts. That is FOP, which is out of scope by decision. A low CFFDRS score
there is evidence the comparison is mis-specified, not that the operational
system is poor — and it would be easy to write up as the latter.

Scored **within fire** (given this burned, how severely), ignition is
conditioned out and CFFDRS is asked the question it was built for. That is the
fair comparison and the defensible headline.

The catch is that within-fire severity means CanLaBS, which is itself
NBR-derived and so reintroduces SWIR circularity — the reason it was kept out
of scope in the first place. Is there a severity measure that is not a
spectral index?

**Answer:**

---

### Q20 — How is the polygon product defined and scored?

**Status:** OPEN — the largest gap between the report and the experiments
**Blocks:** substantiating the mission's stated PRIMARY product.

The report names wildfire-risk polygons as the primary scientific and
operational product. Every metric in this study is per-pixel: `auc_px`, AP,
IoU, ECE. Nothing in any of the three repos produces a polygon or scores one —
the only polygon code reads NBAC perimeters *in*.

That matters because the two can diverge. A model can score well on `auc_px`
and still fragment into hundreds of unusable slivers, and no current metric
would catch it. The reverse also holds: a model that is mediocre per-pixel but
produces clean, correctly-placed polygons may be the better operational
product.

What has to be decided before it can be measured:

- **Extraction.** Threshold then contour, or something smarter? The threshold
  choice is already flagged as operational rather than statistical
  (`stage-a.md`: fix an acceptable false-alarm rate and take the best recall).
- **Metrics.** Polygon-level precision and recall against NBAC perimeters,
  plus a fragmentation measure (count and size distribution for a given burned
  area) and boundary agreement.
- **Minimum useful size.** A 20 m-grid polygon of a few pixels is noise, not a
  product. What is the floor?

**Answer:**

---

### Q21 — Measure the downlink budget rather than asserting it?

**Status:** OPEN — easy to do and easy for a reviewer to check
**Blocks:** nothing; strengthens a quantified report claim.

The report claims polygons of "a few kilobytes" replacing scenes of "hundreds
of megabytes", a reduction of "several orders of magnitude". The arithmetic
supports it: at the placeholder 30 m GSD with 9 surface bands, a 100 km scene
is ~150 MB at 12 bits, and 20 polygons of 30 vertices is ~5 KB, which is about
10^4-10^5.

But that is a calculation, not a measurement, and it is the claim a reviewer
can most easily check. Once polygons exist (Q20), the real product size should
be measured from real model output across the scene types, and reported as a
distribution rather than a single figure — a fire-heavy scene produces more
polygons than an unburned one, and the worst case is what sizes a downlink.

Note the GSD and swath are still placeholders pending **Q2**, so the scene-size
half of the ratio moves with that answer.

**Answer:**

---

### Q22 — Which Essential Climate Variables, specifically?

**Status:** OPEN
**Blocks:** a secondary claim in the report, with nothing behind it yet.

The report offers preprocessed imagery for "mapping multiple Essential Climate
Variables". No ECV is currently named, produced or validated anywhere in the
project.

The nearest existing material is the SCANFI-distilled ecology head, which
already predicts above-ground biomass, canopy height and crown closure — all
ECV-adjacent (GCOS lists Above-Ground Biomass and Land Cover among the
terrestrial ECVs). Framing one or two of those as the ECV claim would make it
concrete and is largely work already done.

Which variables, and against what reference would they be validated?

**Answer:**

---

### Q23 — Is a SWIR band above 1700 nm worth an extended detector, for NDLI?

James set the terms: the 1750 nm top of the Chameleon SWIR envelope is
nominal, and a band above 1700 is **only consequential if there are relevant
indices that need it**. So: there is exactly one, and it is not a minor one.

**NDLI, the Normalized Difference Lignin Index, uses 1680 and 1754 nm.**

That matters because lignin is the curing signal. The brief routes T2 (curing
/ NPV fraction) through cellulose and lignin absorption near 2100 nm, and
hypothesis H2 says SWIR2 is *necessary* for it. SWIR2 is not on offer — the
sensor stops at 1750 and extended InGaAs is outside the two-sensor decision
(A-18). NDLI is therefore the **only in-range route to the curing target**.
Without it, T2 is unreachable by this payload at all, and the study's answer
on T2 reduces to "we cannot measure it".

What else lives up there, for completeness:

| Index | Bands | In range? |
|---|---|---|
| NDNI (nitrogen) | 1510, 1680 | **yes**, both comfortably inside |
| NDLI (lignin) | 1680, **1754** | 1754 is past both 1700 and the nominal 1750 |
| CAI (cellulose) | 2000 / 2100 / 2200 | no — needs SWIR2 |

So the question is narrow and answerable: **is T2 worth a detector that
responds at 1754 nm?**

The cost side. Standard InGaAs is ~0.40 QE at 1700 in our modelled curve
(A-19) and falls steeply beyond, so 1754 means either a part with a longer
cutoff — a 1.9 µm extended variant, cheaper than the 2.2 µm part configuration
C would have needed, but still extended, with deeper cooling and higher dark
current — or accepting a band with very low and thermally unstable response.

Three ways this could go, and the study can inform all three:

1. **Drop it.** Four bands inside 1000–1700, T2 declared out of scope for the
   payload, and the results note says so plainly rather than implying curing
   is covered.
2. **Take it on standard InGaAs anyway** and measure what the low QE costs.
   The sensor model exists to answer exactly this: convolve a 1754 band
   against the falling QE curve, propagate the SNR, and see whether NDLI
   still separates cured from green grass. If it does at realistic SNR, the
   band is nearly free.
3. **Extended detector.** Only justified if (2) fails AND NDLI turns out to
   carry T2 well in hyperspectral data where the band is noise-free.

**Note the ordering.** (2) and (3) both need an NDLI-versus-curing result
first, and no curing label exists anywhere in the current data — the ecology
set is eight treed and wetland classes with no grassland at all. So this
question cannot be settled empirically until there is either a curing label
or hyperspectral data with one. It should not block the VNIR decision, which
is independent.

**Answer:**

---

### Q24 — Use WorldView-3 for BOTH halves, not just the SWIR?

James's plan is to use WorldView-3 data to supply the SWIR bands Sentinel-2
lacks, so the Mantis SWIR mode can be analysed. That works — WV-3's four
in-range SWIR bands (1209, 1572, 1661, 1730 nm) are real measurements, which
is what rule 2 requires of a multispectral archive.

**But WV-3 also carries eight VNIR bands**, and that changes the better plan:

| | WorldView-3 | Mantis |
|---|---|---|
| VNIR | 8 bands, 400–1040 nm, 1.24 m | 6 bands, 400–1000 nm |
| SWIR in range | 4 bands, 1209–1730 nm, 3.7 m | 4 bands, 1000–1750 nm |

So WV-3 alone is a **12-band co-registered analogue of Mantis MS+SWIR** — and
co-registered in exactly the way the dichroic design is (A-20): one platform,
one instant, one geometry.

Pairing WV-3 SWIR with Sentinel-2 VNIR would instead introduce a cross-
platform registration and timing mismatch that the real instrument does not
have. It would measure a harder problem than the one being designed, and a
poor combined-mode result could be an artifact of the pairing rather than a
property of the bands.

**Recommendation:** use WV-3 for both halves when evaluating the combined
mode, and keep Sentinel-2 for the VNIR-only question, where its ten in-range
bands and wall-to-wall free coverage are the better instrument.

### Q25 — Is a 2023-burn-only lead time enough for the SWIR evidence?

**The situation.** The AVIRIS-NG pool that is both pre-fire and published is
42 lines (A-21), and 35 of them precede a burn in 2023 alone. So the
dominant design is "imaged in 2022, burned in 2023": a one-season lead time,
measured once.

**Why it matters.** The SWIR bands exist to sense fuel moisture and dry
matter, both of which vary within a season. A one-year lead says whether the
spectrum before a fire differs from the spectrum before no fire; it does not
say how far ahead that difference is readable, which is the question a
monitoring mission actually faces. The 2018 lines (12 of the 42, with burns
in 2019-2023) are the only multi-year lead available, and twelve lines is
thin for a curve.

**What we would do about it, in order of cost:**
1. Accept the one-season design and say so plainly in the Phase 6 note. The
   band-placement answer does not need a lead-time curve.
2. Add post-fire lines (`--all-lines`) for severity and recovery, which is a
   different question but uses data already paid for.
3. Extend NBAC past 2023 as perimeters are published; every new fire year
   turns some of the 143 published 2022 Canadian lines into pre-fire ones.
   This is the cheapest real improvement and needs no new imagery.

**For James:** is a single-season lead acceptable evidence for the SWIR
specification, or does the spec need the multi-year read that only option 3
can eventually give?

### What to check before committing

1. **Coverage and cost.** WV-3 is commercial. Archive holdings over boreal
   Canada — and specifically over our 292 fire and 279 ecology patches — are
   unlikely to be dense, and tasking is expensive. This is the binding
   constraint, not the science.
2. **Resolution ratio.** WV-3 is 1.24 m VNIR against 3.7 m SWIR, a 3× ratio;
   Mantis has them equal. Aggregating VNIR to 3.7 m is honest downsampling
   and matches the instrument being designed.
3. **Band placement differences.** WV-3's VNIR set is not Mantis's — it has a
   yellow band, two NIRs and one red edge, where the S2-derived candidate
   pool has three red edges. It is an analogue, not a replica, so it answers
   "does SWIR add over VNIR" better than it answers "which six VNIR bands".
4. **Labels are not the blocker.** SCANFI and NBAC are national rasters, so
   any Canadian WV-3 footprint can be labelled with the same machinery
   already running on the Sentinel-2 patches.

**The division this suggests**

| Question | Instrument |
|---|---|
| Which 6 VNIR bands | Sentinel-2 — 10 in-range bands, free, wall to wall |
| MS vs HS *reach* (B1, B9) | Sentinel-2 |
| Which 4 SWIR bands | WorldView-3 (4 real in-range), or hyperspectral to tune centres |
| Does SWIR add over VNIR | WorldView-3, both halves co-registered |
| What 96 HS bands buy over 6 | hyperspectral only — AVIRIS-NG, EnMAP, PRISMA |

**Answer:**

---

### Q26 — Library access for the two paywalled ignition papers?

**Status:** OPEN
**Blocks:** the ignition branch of R0 (plan P1), not the spread or intensity
branches.

The ignition receptivity branch needs exact coefficients from
Beverly & Wotton (2007), *IJWF* 16:161-173, doi:10.1071/WF06072 (logistic
P(sustained flaming) from FWI components by fuel category) and
Wotton & Beverly (2007), *IJWF* 16:463-472, doi:10.1071/WF06087 (FFMC adjusted
to litter moisture by forest type, season and stand density -- the canopy-
closure slot). Both are behind the CSIRO paywall. The third source,
Wotton & Wheatley (2025), *IJWF* WF24164 (DMC and lightning ignition), is open
access. Can ÉTS library supply the two PDFs, so the coefficients come from the
papers rather than from memory?

**Status (2026-10-24): PARTLY ANSWERED.**

**Answer:**
- **Beverly & Wotton (2007): obtained** from James. The Table 6 coefficients are implemented in `Fire_Risk_Model/src/data/ignition.py`, and the tests reproduce the paper's own worked probabilities (A-30).
- **Wotton & Beverly (2007): requested** by James. `instand_ffmc` keeps refusing to run until it arrives.
- **Wotton & Wheatley (2025): read.** It publishes only shape-constrained GAM curves (Figs 2–3). The table of estimates per integer DMC is "available from the authors". The paper also finds no support for the operational DMC = 20 threshold. Until the authors' table is in hand, lightning ignition stays on the GLC-X-42 DMC classes. **Optional follow-up:** James could ask Mike Wotton for that table.

---

### Q27 — Unpack NBAC 2024/2025 for the 13 unmatched confusers?

**Status:** OPEN — the zips are held (downloaded 2026-10-23)
**Blocks:** fire dates for 13 of 108 confusers.

Thirteen confusers precede fires dated 2022-2026 with no NBAC polygon at
their location in the years matched so far; most need NBAC 2024 or 2025.
Unpack them into `data/nbac/` and re-run `nbac_fire_dates.py`, or drop those
confusers from the fire-date design?

**Answer (James, 2026-10-23): unpack.** Done -- and it did not help: none of
the 13 has an NBAC polygon at its location in 2022-2025 (three would need
2026, which NBAC does not yet cover). They are most likely NFDB sites whose
fires were too small or off-centre for NBAC to map at the patch. They take
latitude-band pseudo-dates like the other negatives (A-24); the Stage C NFDB
fetch can recover their real dates.

---

### Q28 — Process weights and the hardware budgets for the CubeSat decision

**Status:** OPEN — placeholders written into A-29 so the rules exist before
results do
**Blocks:** nothing until plan P12; the rules are pre-registered regardless.

The decision synthesis (A-29) combines evidence across ignition, spread and
intensity (equal weights until set -- Q1 restated per process) and picks the
board against a per-scene latency budget and a power budget that are not yet
known. What latency per scene and what orbit-average power can the onboard
model have?

**Answer (James, 2026-10-23):** derive them from
`CubeSat_Sensors_and_Lenses.xlsx`; meet the latency, then minimise power.
Derived: <= 91 s per 1000 x 1000 x 6-band scene (buffered, 500 km),
real-time 4.6 s reported as a bonus, no processor power cap. Process weights
stay equal (Q1). Recorded in A-29.


---

### Q29 — Three design choices before the second slot sweep

**Status:** OPEN (raised by P7, 2026-10-26)
**Blocks:** a meaningful E-38, and any imagery-correction result that is more than a recalibration.

1. **Curing on CWFIS fuel.** The SCANFI fuel tree assigns no O-1 pixel, so `r3_curing` changed nothing: its delta was exactly 0. CWFIS 2019 fuel has O-1b on 4.6 % of pixels. Should the curing run, and its twin, move to CWFIS fuel? This adds two configurations and leaves SCANFI as the fuel source everywhere else.
2. **Corrections that carry only a shift.** Every bounded correction learned a near-uniform shift toward less crown fire and sat near its bound (P7-C1). The shuffled twin learned the same shift, so nothing spatial reached the score.
   - Proposed: give each slot a learned, imagery-free offset, so the imagery head models only the deviation from it, and widen the bound or move it off the tanh's flat part.
   - This changes what "correct form" means for E-36 and E-37, so it would be registered as a new arm, not swapped in.
3. **R2's within-patch gap to R1** (−0.025). R2's residual is the same network as R1, so capacity is not the difference. What differs is the zero start and the physics terms alongside it, so R2 settles in a worse place inside patches. Should a variant try warm-starting the residual from R1, or a higher learning rate for the residual? Or is the gap the cost of keeping the physics, to be reported as such?

---

### Q30 — The CWFIS archive: as issued, or reprocessed? And is older FBP held anywhere?

**Status:** OPEN (raised 2026-10-26, with E-55 and E-56)
**Blocks:** how E-55 is read; whether E-56 needs a new 2024–2025 cohort at all.

The CWFIS GeoServer (`cwfis.cfs.nrcan.gc.ca/geoserver`, WCS, `time=YYYY-MM-DD`) archives these daily 2 km grids:

| Grid | Archived from |
|---|---|
| FWI (`public:fwi`) | 2018-01-01 |
| Fire danger class (`public:fdr`) | 2018-01-01 |
| FFMC, DMC, DC, ISI, BUI | 2024-01-01 |
| HFI, ROS, CFB, SFC, TFC, FMC, fuel type | 2024-01-01 |
| Green-up, grass curing | 2024 |

Two things the documentation does not say:

1. Are the archived grids the values CWFIS published on the day, or later reprocessing (for example, with late station reports or a changed interpolation)? E-55 compares against "what operations used", which only the as-issued values are.
2. Does CWFIS or the CFS hold FBP grids before 2024 that are not served? If so, E-56 could run on the existing 2019–2023 cohort instead of a new one.

Both are questions for CWFIS (cwfisitnotify-scifvtinotification@nrcan-rncan.gc.ca, from their data-services guide).
