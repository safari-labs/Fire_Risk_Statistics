# P0 — CFFDRS mirror: verify and freeze (2026-10-23)

Phase 0 of the CFFDRS-mirror plan checks the data each later phase depends on. It fixes the problems that turned up and freezes the test set. No model was trained. **At a glance:** [p0_verify/experiments.md](p0_verify/experiments.md).

## What P0 established

### 1. Every fire has a start date, and two thirds of them leaked into the old design

`nbac_fire_dates.py` reads the NBAC `.dbf` directly. fiona fails on NBAC's null dates, which is why the start dates had been skipped until now. The fire patches matched as follows:

- All **99 fire patches** match an NBAC polygon, and every one has a hotspot start date (`HS_SDATE`).
- **95 of 108 confusers** match the fire they precede. The other 13 need NBAC 2024 or 2025; see Q27.
- The 99 fire patches come from **82 distinct fires**. 91 of them are cause "Natural".

**66 of the 99 fires started on or before 30 June.** For those fires, the April–June composite and the 30-June weather date both overlapped the fire. The fire-start-date design in P3 and P4 removes this overlap. Details are in A-24.

### 2. Fuel inventories: only some are pre-fire, measured on the burned pixels

| Source | Burned pixels read as non-fuel | Pre-fire? |
|---|---|---|
| CWFIS 2024 (30 m) | **73.9 %** | **no** — burn scars are written into the layer |
| CWFIS 2019, decision-tree build (250 m) | 1.0–4.5 % by fire year | yes |
| CWFIS 2014b (250 m) | 1.2–6.0 % | yes |
| SCANFI v2 2015 | no age reset, no closure drop | yes |
| SCANFI v2 2020 | already shows the 2019 and 2020 fires | yes for 2021–2023 (90 of 99 patches) |
| SCANFI v2 2025 | shows every fire | no — used as the post-fire control |

If the 2024 layer were used as the "CFFDRS as is" fuel, it would leak the outcome directly. So the operational pre-fire fuel is the **2019 CWFIS layer** (or 2014b). The SCANFI pre-fire step is `mode="pre_fire"`. The 2014b and 2019 code tables reuse code numbers for different classes than the 2024 table, so each vintage keeps its own codes. Details are in A-25.

Three findings came out of this work:

- **SCANFI's non-treed channels are post-fire for the early fires.** Channels 13–17 come from WorldCover 2021, so they are post-fire for 2019–2020 fires whichever SCANFI step is chosen.
- **The official fuel rules are now available.** The CFS decision tree that turns inventory into FBP types ships with the 2019 layer. P2 should build the SCANFI fuel reference with those rules, not with the judgement thresholds in A-11.
- **The species-semantics concern does not apply.** SCANFI v2 species layers are per-species crown closure. `percent_conifer` is a ratio, and the ecology losses normalise to a composition, so neither is affected.

### 3. SCANFI: all nine time steps, without silent vintage swaps

- `scanfi.py` now reads 1985–2025. 2020 stays the default, so the legacy sidecars rebuild bit for bit (worst |diff| 2.4e-4, which is float16 rounding).
- The 2015, 2020 and 2025 sidecars exist for all 292 patches. The 2010 and 2005 sidecars were still running when this note was written.
- **Bug fixed:** a request for a missing year silently returned the 2020 raster.

### 4. The test set is now grouped by fire

Grouping by 0.1° block alone let **8 fires sit in two splits** of the current pack, including 5 across train and test. No result has been reported on that test split, so this was fixed rather than retracted.

The new rule groups patches as connected components over a shared block *or* a shared fire. The v2 test set is the v1 test set closed under that rule: 35 patches, with 11 moved in and none moved out. It is frozen in `Fire_Risk_Model/splits/test_groups_v1.json` (sha256 `3e65e310…`). Details are in A-27.

### 5. Data that changes the plan

**CFSDS v1.1** (OSF `f48ry`, released June 2025):

- 90 m resolution, fires larger than 500 ha, years **2002–2024**. The paper's description was 180 m, fires larger than 1,000 ha, 2002–2021.
- **All 99 fire patches are covered**: 7,835 fire-days.
- Stage B can therefore use the same fires; no separate chips are needed.
- Each fire-day row includes spread distance, every FWI code, closure and percent conifer.

**CWFIS downloads**, the operational sources for the slots:

| Data | Years | Use |
|---|---|---|
| Green-up | 2020–2025 | green-up slot (held) |
| Percent curing | 2020–2025 | curing slot (not fetched; 2 GB a year) |
| Station FWI observations with coordinates | 2020s | G3 |
| NBAC | 2024–2025 | the 13 unmatched confusers (held) |

The interpolated FWI/FBP rasters on the WCS start in 2024, so they can't serve as a reference for our fire years.

**G3 is now testable.** Fire patches sit a median **37 km** from the nearest reporting CWFIS station (IQR 23–63 km, maximum 191 km). Provincial agency stations are excluded from the CWFIS export, so these distances overstate the real gap to the nearest station.

**Ignition sources are confirmed:**

- Beverly & Wotton 2007 (*IJWF* 16:161): P(sustained flaming).
- Wotton & Beverly 2007 (*IJWF* 16:463): stand-specific FFMC by forest type, season and density.
- Wotton & Wheatley 2025 (*IJWF* WF24164, open access): DMC and lightning ignition.

The first two are paywalled (Q26).

## Register changes

- **New "CFFDRS mirror" group, E-32 to E-48.** The register test requires sequential IDs, so the plan's later numbers moved:
  - Stage C is E-44/E-45 (the plan said E-47/E-48).
  - The CubeSat decisions are E-46/E-47/E-48 (the plan said E-49/E-50/E-51).
- **E-43** is the date-only control, under Controls.
- **E-17** moves from NEEDS_DATA to NEEDS_CODE, because the station data is now held.
- **E-21** moves to NEEDS_CODE: the inventory half can run as soon as R0 exists.
- **New assumptions and questions:** A-24 to A-29, including the CubeSat decision rules, which are pre-registered in A-29. Q16 and Q18 are answered. Q26–Q28 are new.

## Still open in P0

- **SCANFI fetch:** the 2010 and 2005 sidecars, plus the end-of-run legacy check.
- **NBAC 2024/2025:** unzip into `data/nbac/` and rerun `nbac_fire_dates.py` (Q27).
- **SCANFI v1:** the 2020 adapter isn't written (needed for E-33).
- **Fuel counts:** per-type pixel counts on the pre-fire inventories.
  - From the 2019 CWFIS layer, burned pixels are 28% C-2, 11% C-3, 9% C-1, 6% C-4, 16% M-1/M-2 and 14% D-1/D-2.
  - O-1 is 3% and M-3/M-4 doesn't appear. The dead-fir slot therefore has no operational presence in our data, and the curing slot will probably report "n insufficient".
- **GOES GLM coverage** for Stage C hasn't been checked.

## Code (Fire_Risk_Model)

All of this is committed in Fire_Risk_Model:

- `src/data/scanfi.py`: time steps, vintage-named sidecars and strict mode.
- `src/data/labels.py`: `read_nbac_dates`, plus the year-token fix in `resolve_nbac_for_year`.
- `src/data/fbp_fuel_layer.py`: 2014b and 2019 vintages, each with its own code table.
- New scripts in `scripts/python/`: `fetch_scanfi_steps.py`, `nbac_fire_dates.py`, `freeze_test_groups.py`, `attach_fuel_vintages.py`, `scanfi_vintage_leakage.py`.
- New tests: `tests/test_scanfi_steps.py`, `tests/test_freeze_groups.py`, and two additions to `tests/test_labels.py`.
- Test status: 281 tests pass. The one failure, `test_deploy_parity::test_gsd_matching_present`, predates this work.
