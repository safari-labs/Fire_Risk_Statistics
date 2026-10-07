"""Every shipped config loads and validates.

This is the Phase 0 'done when' condition from the brief.
"""

from __future__ import annotations

import pytest

from safari_bands.config.loader import (
    ConfigError,
    available,
    load_band_set,
    load_detector,
    load_optics,
    load_orbit,
)
from safari_bands.config.schemas import Band, BandSet, SRFShape

# Nominal Sentinel-2 centres the brief asks SAFARI to match where it costs
# little (section 5). Cross-calibration and training on the S2 archive depend
# on these staying put, so a drift here should fail loudly.
SENTINEL2_NOMINAL_CENTRES_NM = [490.0, 560.0, 665.0, 705.0, 740.0, 865.0, 1610.0, 2190.0]


def test_at_least_the_expected_band_sets_ship():
    names = available("bands")
    for expected in ("config_a", "config_b", "config_c", "sentinel2_msi", "negative_control"):
        assert expected in names


@pytest.mark.parametrize("name", available("bands"))
def test_every_band_set_loads(name):
    band_set = load_band_set(name)
    assert band_set.bands
    assert band_set.name


@pytest.mark.parametrize("name", available("detector"))
def test_every_detector_loads(name):
    detector = load_detector(name)
    lo, hi = detector.spectral_range_nm
    assert lo < hi
    assert detector.qe_curve.wavelength_nm[0] < detector.qe_curve.wavelength_nm[-1]


def test_optics_and_orbit_load():
    assert load_optics("default").aperture_diameter_mm > 0
    assert load_orbit("default").altitude_km > 0


def test_index_catalogue_loads(catalogue):
    assert catalogue.indices
    assert catalogue.by_name("NDMI") is not None
    # NDII is an alias of NDMI and must resolve to the same definition.
    assert catalogue.by_name("NDII") is catalogue.by_name("NDMI")


def test_sentinel2_centres_match_the_brief(band_sets):
    centres = [b.centre_nm for b in band_sets["sentinel2_msi"].sorted_bands()]
    assert centres == SENTINEL2_NOMINAL_CENTRES_NM


def test_safari_configs_reuse_sentinel2_centres_where_they_overlap(band_sets):
    """Matching S2 centres is a stated design goal, not an accident."""
    s2_centres = set(SENTINEL2_NOMINAL_CENTRES_NM)
    for key in ("config_a", "config_b", "config_c"):
        for band in band_sets[key].bands:
            # 1240 and 1375 nm have no S2 counterpart in the nominal list.
            if band.role in {"SWIR_1240", "CIRRUS"}:
                continue
            assert band.centre_nm in s2_centres, (
                f"{key}/{band.name} at {band.centre_nm} nm does not match an S2 centre"
            )


def test_unknown_key_is_rejected():
    """A typo in a YAML key must fail rather than be silently dropped."""
    with pytest.raises(ConfigError):
        from pathlib import Path

        from safari_bands.config.loader import parse_as

        parse_as(
            BandSet,
            {
                "name": "typo",
                "bands": [{"name": "b", "role": "NIR", "centre_nm": 865.0, "fwhm_nm": 30.0}],
                "descrption": "misspelled",
            },
            Path("test"),
        )


def test_duplicate_role_is_rejected():
    """Two bands sharing a role would make index resolution ambiguous."""
    with pytest.raises(ValueError, match="duplicate band role"):
        BandSet(
            name="dupe",
            bands=[
                Band(name="a", role="NIR", centre_nm=865.0, fwhm_nm=30.0),
                Band(name="b", role="NIR", centre_nm=870.0, fwhm_nm=30.0),
            ],
        )


def test_band_outside_forward_model_domain_is_rejected():
    with pytest.raises(ValueError, match="outside the 400.0-2500.0 nm domain"):
        Band(name="thermal", role="TIR", centre_nm=10500.0, fwhm_nm=100.0)


def test_tabulated_srf_requires_a_file():
    with pytest.raises(ValueError, match="requires srf_file"):
        Band(
            name="tab",
            role="NIR",
            centre_nm=865.0,
            fwhm_nm=30.0,
            srf_shape=SRFShape.TABULATED,
        )


def test_band_edges_widen_with_the_fwhm_multiplier():
    band = Band(name="b", role="SWIR1", centre_nm=1610.0, fwhm_nm=90.0)
    assert band.edges_nm(1.0) == (1565.0, 1655.0)
    assert band.edges_nm(3.0) == (1475.0, 1745.0)


def test_dark_current_doubles_per_doubling_temperature(detectors):
    detector = detectors["ingaas_std"]
    dc = detector.dark_current
    at_reference = dc.at_temperature(dc.reference_temperature_k)
    one_doubling_up = dc.at_temperature(
        dc.reference_temperature_k + dc.doubling_temperature_k
    )
    assert at_reference == pytest.approx(dc.reference_e_per_s)
    assert one_doubling_up == pytest.approx(2.0 * at_reference)
