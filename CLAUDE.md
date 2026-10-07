# SAFARI — Stage 1 band design study

This repository holds Stage 1 of the SAFARI cubesat payload design: a study that decides which spectral bands the multispectral camera should carry for retrieving wildland fuel condition (inputs to Canadian fire danger rating). The product of this repo is a set of spectral requirements (band centres and widths, SNR, calibration and co-registration specs) backed by quantified retrieval performance. It is not the operational retrieval model; a provisional one is built here only to evaluate candidate band sets.

Project owner: James (safari-labs). Scientific context, decisions to date and the phased work plan are in the brief below, which loads with this file:

@docs/STAGE1_BRIEF.md

## Methodological rules

These come from the planning discussion (reasons in section 8 of the brief). Do not relax them without asking James.

1. Rank nested band sets, never individual bands. Report the best k-band set for each k, with its retrieval error, per target and combined.
2. Candidate spectra come only from radiative transfer simulation or real hyperspectral data. Never synthesize candidate bands by interpolating or duplicating a multispectral sensor (Sentinel-2, Landsat, VIIRS, MODIS); that only rediscovers the source sensor's bands. Multispectral archives may be used only for bands they actually measure (e.g. fire-outcome tests in Phase 6).
3. Targets must be physically defined (radiative transfer input parameters) or independently measured (gravimetric LFMC, field curing). Never use CFFDRS outputs or spectral-index thresholds as labels.
4. Judge a band set by training the provisional retrieval model on it (wrapper evaluation). Importance scores are exploratory only, and PCA loadings are never evidence of relevance.
5. Split train/test by scenario (fuel type, season, geometry) for simulations and by scene/region for real data, never by random rows. Keep a final test set that band selection and model training never touch, and do selection inside training folds.
6. Every evaluation includes the sensor noise model. Report noise-free results only alongside noisy ones.
7. Respect atmospheric windows: leaf water features at 1450 and 1940 nm are unusable from orbit. Candidate SWIR bands sit near 1230–1250 nm (clear of the 1270 nm O2 band), 1550–1750 nm and 2100–2300 nm.

## Working agreement

- Before starting any phase, write a short plan (approach, files, validation, open questions) and wait for approval.
- Record assumptions in `docs/ASSUMPTIONS.md` and questions for James in `docs/OPEN_QUESTIONS.md`. Use clearly labelled placeholder values rather than blocking.
- Keep established results separate from hypotheses. The brief marks hypotheses; the study's job is to test them, not to confirm them.
- After each phase, write a short results note in `docs/results/`.

## Conventions

- Python 3.11 or later; package in `src/safari_bands/`; tests in `tests/` with pytest.
- Configuration in YAML under `config/` (band sets, parameter priors, detector and optics models, scenarios). No hard-coded band definitions or instrument parameters in code.
- Units: wavelength in nm; reflectance 0–1; radiance in W m⁻² sr⁻¹ µm⁻¹; Cw and Cm in g cm⁻²; LFMC in %.
- Seed every stochastic step. Each run writes its outputs, resolved config and git commit hash to `runs/<YYYYMMDD-HHMM>_<name>/`.
- Large generated data (simulated spectra, look-up tables) go in `data/` and are git-ignored; keep the scripts that regenerate them.

## Commands

Environment (Windows paths; use `.venv/bin/` on POSIX):

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"      # Phase 0
.venv/Scripts/python -m pip install -e ".[dev,sim]"  # adds prosail, scipy (Phase 1-2)
```

The `analysis` extra (scikit-learn, SALib, pandas, pyarrow, matplotlib) is for
Phase 3 onward. `prosail` needs numba, which caps numpy below 2.6 — see
`docs/ASSUMPTIONS.md` (A-7). Do not install into the system Python; its
numpy/scipy pair is already inconsistent.

```bash
.venv/Scripts/python -m pytest          # tests
.venv/Scripts/python -m ruff check .    # lint
safari-bands validate                   # load every config, run the rule checks
safari-bands validate --run             # ... and write runs/<timestamp>_validate/
safari-bands indices                    # index feasibility matrix
safari-bands indices --band-set config_b
safari-bands bands config_c
```

`safari-bands validate` exits non-zero on any error and must stay clean.
Warnings are expected: placeholder hardware values (Q2–Q6) and the negative
control band set, which is meant to look bad.

Add a new band set by dropping a YAML file in `config/bands/`; it is picked up
automatically by the loader, the CLI and the parametrised tests.
