# P7d (proposed, not started): standard and foundation models as fire danger rating

**Status:** proposal, written 2026-10-27 at James's request so it can be taken up later. Not approved, not registered, nothing built. James asked to focus on P6 first. Open question: Q31.

## Question

Can a standard model take the inputs CFFDRS uses (weather, fuel, terrain), plus a strong learned representation of the land, and rank fire danger better than:

- our reconstructed CFFDRS rungs (R0, R1, R2, R4); and
- the FWI **issued by CWFIS** (between patches only; P7b, E-55)?

It would run alongside the P7 slot experiments, on the same 194 development patches, the same five fire-aware folds, and the same paired fire-group bootstrap. Every table labels which values were issued by CWFIS and which are our reconstruction (A-36).

## Candidate models

| Model | Input | Why | Onboard? |
|---|---|---|---|
| **AlphaEarth Foundations** | Annual 64-d embedding, 10 m (Earth Engine `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`, 2017–2024; Landsat, Sentinel-1/2, LiDAR and more) | Strongest off-the-shelf land representation, cheap to fetch | No: needs sensors we won't fly. An upper bound. |
| **TESSERA** | Annual 128-d embedding, 10 m, from Sentinel-1/2 time series (`geotessera`; 2017–2025 in recent releases; vectors can be truncated to 16, 32 or 64 d) | Open alternative; truncation measures how many dimensions are needed | No: an upper bound |
| **Prithvi-EO-2.0** (300M/600M) | HLS-style 6 bands: B, G, R, NIR, SWIR1, SWIR2 | Published burn-scar fine-tune; can take our own pre-fire composites | No, too large; a ground-segment option |
| **Galileo** | Optical, radar, elevation **and weather** | The one foundation model built to ingest weather with imagery: closest to "the CFFDRS inputs" | Possibly, in its small sizes |
| **Presto** | Pixel time series: Sentinel-1/2, ERA5, DEM | Very small; a real onboard candidate if it performs | Yes |
| **DOFA** | Any band set, wavelength-conditioned | One backbone for any candidate CubeSat band set; ties into the band decision (P12) | Possibly |
| **Gradient-boosted trees** (LightGBM) | CFFDRS inputs + per-patch features | The standard workhorse of fire-occurrence modelling; the baseline a reviewer expects | Yes |

**Considered and left out:** Clay and SatMAE overlap Prithvi and DOFA; SSL4EO backbones only add weight. Any can be added on request.

## Design rules

- **No leakage from annual products.** AlphaEarth and TESSERA each summarise a whole calendar year, so the fire year's embedding contains the burn. Use **the year before the fire**: 2018–2022 for the 2019–2023 fires, and the same rule on each negative's date (A-24).
- **No leakage from our imagery.** Prithvi, DOFA and Galileo get the D−45…D−1 pre-fire composites (A-33). Galileo and Presto get ERA5 weather up to D−1 (A-32).
- **Per-model arms:**
  - embedding only (no CFFDRS inputs);
  - CFFDRS inputs plus embedding (like R1);
  - physics plus residual plus embedding (like R4);
  - a shuffled-embedding twin for every imagery arm.
- **Metrics:**
  - within-patch and between-patch AUC, plus same-year pairs;
  - paired by fire, with a group bootstrap;
  - parameter count and compute per model, for P12.
- **Training:** on Narval, including frozen-feature extraction.

## Draft predictions (to register before any data, after approval)

| ID | Model | Prediction | Wrong if |
|---|---|---|---|
| E-63 | AlphaEarth | Year-before embeddings added to R2 raise within-patch AUC by ≥ 0.02 and clear their shuffled twin | The gain is < 0.01 or its CI spans 0 |
| E-64 | TESSERA | Same as E-63; 32 dims recover ≥ 90 % of the 128-dim gain | Either part fails |
| E-65 | Prithvi-EO-2.0 | Frozen features on our pre-fire composites beat our raw-band R4 within patches | Paired CI spans 0 or is negative |
| E-66 | Galileo | Imagery + raw ERA5 weather + DEM, **without CFFDRS codes**, ranks patches at least as well as the FWI issued by CWFIS (same-year pairs) | > 0.03 below, CI excluding 0 |
| E-67 | Presto | Within 0.02 of Galileo with < 1 % of its parameters | The gap is larger |
| E-68 | DOFA | On Sentinel-2 band subsets matching candidate CubeSat sets, beats the same-size network trained from scratch | It doesn't |
| E-69 | Gradient-boosted trees | On the CFFDRS inputs, matches R1 within 0.01 | > 0.01 either way, CI excluding 0 |

The register numbers are provisional; they are taken at registration, so later experiments may claim them first.

## What it needs

1. **Fire pack with B12 (v2.1).** Prithvi needs SWIR2, and the slot runs want it anyway. Same Earth Engine recipe as `build_ecology_b12.py`.
2. **Embedding sidecars.** AlphaEarth and TESSERA for the year before each patch's date, averaged onto the 20 m patch grids: about 35 GB.
3. **Order:** AlphaEarth, TESSERA and the gradient-boosted baseline first (cheap). Then Galileo and Presto, then Prithvi and DOFA.

## Sources (checked 2026-10-27)

- [AlphaEarth Foundations (DeepMind)](https://deepmind.google/blog/alphaearth-foundations-helps-map-our-planet-in-unprecedented-detail/)
- [Satellite Embedding V1 Annual, Earth Engine catalog](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL)
- [TESSERA paper](https://arxiv.org/html/2506.20380v3)
- [GeoTessera documentation](https://geotessera.readthedocs.io/en/latest/)
- [Prithvi-EO-2.0 paper](https://arxiv.org/pdf/2412.02732)
- [Galileo paper](https://arxiv.org/abs/2502.09356v3)
- [DOFA paper](https://arxiv.org/abs/2403.15356)
- [Geo-foundation model flood benchmark (Clay, DOFA, Prithvi)](https://arxiv.org/pdf/2511.01990)
