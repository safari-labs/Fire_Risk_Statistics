# SAFARI — Stage 1 band design study

Which spectral bands should the SAFARI cubesat multispectral camera carry for
retrieving wildland fuel condition?

The product of this repo is a set of spectral requirements — band centres and
widths, SNR, calibration and co-registration specs — backed by quantified
retrieval performance. It is **not** the operational retrieval model; a
provisional one is built here only to evaluate candidate band sets.

Scientific context and the phased work plan: [docs/STAGE1_BRIEF.md](docs/STAGE1_BRIEF.md).
Methodological rules that govern how this work is done: [CLAUDE.md](CLAUDE.md).

> **Terminology.** In fire science "fire risk" means ignition probability.
> SAFARI measures *fuel condition*, which feeds *fire danger* rating (CFFDRS).
> Outputs use those terms.

## Status

**Phase 0 complete** — configuration schemas, validation and provenance.

There is no forward model and no simulated spectra yet, so nothing here
computes an index value or a retrieval error. What does work is the
configuration layer: candidate band sets, detectors, optics, orbit and the
index catalogue all load, validate against the study's methodological rules,
and can be resolved against each other.

| Phase | State |
|---|---|
| 0 Scaffolding | done |
| 1 Forward model (PROSPECT-D + 4SAIL) | not started |
| 2 Atmosphere and sensor model | not started |
| 3 Global sensitivity analysis | not started |
| 4 Band selection | not started |
| 5 Hardware trade and spec derivation | not started |
| 6 Empirical checks | needs data access |

## Setup

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"     # Windows
# source .venv/bin/activate && pip install -e ".[dev]"   # POSIX
```

Phase 1 and later add optional extras, not installed yet:

```bash
pip install -e ".[dev,sim]"        # prosail, scipy       (Phase 1-2)
pip install -e ".[dev,analysis]"   # sklearn, SALib, ...   (Phase 3-5)
```

## Commands

```bash
pytest                                  # run the test suite
safari-bands validate                   # load every config, run the rule checks
safari-bands validate --run             # ... and write a run directory
safari-bands indices                    # index feasibility matrix, all band sets
safari-bands indices --band-set config_b   # one band set in detail
safari-bands bands config_c             # print a band set and its findings
```

`safari-bands validate` exits non-zero on any error. Warnings are expected:
placeholder hardware values pending open questions Q2–Q6, and the negative
control band set, which is meant to look bad.

## Layout

```
config/            all band, instrument and index definitions (no values in code)
  bands/           candidate and reference band sets
  detector/        silicon CMOS, standard InGaAs, extended InGaAs
  optics/ orbit/   telescope and sampling geometry
  indices.yaml     reference vegetation index catalogue
  atmospheric_windows.yaml   methodological rule 7, as data
src/safari_bands/
  config/          pydantic schemas, YAML loading, cross-config validators
  indices.py       which band sets can form which indices
  provenance.py    run directories with resolved config, git hash and seed
  cli.py           the safari-bands command
tests/             pytest
docs/
  STAGE1_BRIEF.md  scientific context and work plan
  ASSUMPTIONS.md   every unconfirmed value, traced to the question that fixes it
  OPEN_QUESTIONS.md   questions for James
  results/         one short note per phase
data/              generated spectra and look-up tables (git-ignored)
runs/              per-run outputs (git-ignored)
```

## Candidate band sets

The three configurations differ only in SWIR content. The VNIR set is shared
and provisional — Phase 4 optimises it.

| Set | SWIR | Detector | Role |
|---|---|---|---|
| `config_a` | ~1610 | standard InGaAs | candidate |
| `config_b` | ~1240 + ~1610 (+1375 cirrus) | standard InGaAs, one focal plane | candidate |
| `config_c` | ~1610 + ~2190 | extended InGaAs | candidate |
| `sentinel2_msi` | 1610 + 2190 | — | positive benchmark |
| `negative_control` | none | — | negative control |

The key question the study answers: **what fraction of configuration C's
retrieval performance does B recover, per target?** C needs
extended-wavelength InGaAs, which is the main cost and SWaP driver; B shares a
focal plane with SWIR1 and so adds no new cross-chain registration problem.

## What the configuration layer already settles

Some of the trade is decided by band placement alone, before any physics:

```
index     config_a  config_b  config_c  sentinel2_msi
NDMI        yes       yes       yes        yes          T1 canopy water
NDWI_Gao     -        yes        -          -           T1, the point of config B
NMDI         -         -        yes        yes          T1, needs SWIR1-SWIR2
NDTI         -         -        yes        yes          T2 curing / NPV
```

Configuration A and B can form no curing index at any SNR, because NDTI needs a
SWIR1/SWIR2 contrast they do not have. That is hypothesis H2 expressed as a fact
about the hardware. Run `safari-bands indices` for the full matrix.

**This is not a result.** Indices are baselines and interpretability aids only
(rules 3 and 4): band selection targets the physical variables, and band sets
are judged by training the provisional retrieval model on them. A band set that
forms more indices has not been shown to be better at anything.

## Methodological rules in force

The rules in [CLAUDE.md](CLAUDE.md) exist because of specific failure modes in
prior band-selection work (brief section 8). Where a rule can be made
executable, it is:

| Rule | Enforced by |
|---|---|
| 7 — respect atmospheric windows | `check_atmospheric_windows`, against `config/atmospheric_windows.yaml` |
| detector physics (1.7 µm InGaAs cutoff) | `check_detector_coverage` |
| near-duplicate bands are a known trap | `check_band_separation` |
| placeholders must stay visible | `check_placeholders`, surfaced on every `validate` |
| runs must be reproducible | `provenance.py` — resolved config, git hash, seed |

The rest — nested rankings, wrapper evaluation, scenario-wise splits, noise in
every evaluation — apply from Phase 3 onward and are not yet exercised.
