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
