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
