"""The methodological rules, tested as executable constraints."""

from __future__ import annotations

import pytest

from safari_bands.config.schemas import Band, BandPurpose, BandSet
from safari_bands.config.validators import (
    Severity,
    ValidationFailure,
    check_atmospheric_windows,
    check_band_separation,
    check_detector_coverage,
    check_placeholders,
    errors,
    raise_on_errors,
    validate_band_set,
)


def _band_set(*bands: Band, name: str = "fixture") -> BandSet:
    return BandSet(name=name, bands=list(bands))


# --- rule 7: atmospheric windows -------------------------------------------


def test_band_in_the_1940nm_water_feature_is_rejected(windows):
    """Rule 7: the 1940 nm leaf water feature is unusable from orbit."""
    band_set = _band_set(Band(name="water", role="SWIR_1940", centre_nm=1940.0, fwhm_nm=50.0))
    findings = check_atmospheric_windows(band_set, windows)

    assert errors(findings), "a 1940 nm band must be rejected"
    assert any("water_vapour_1900" in f.message for f in errors(findings))


def test_band_in_the_1450nm_water_feature_is_rejected(windows):
    """Rule 7: the 1450 nm leaf water feature is unusable from orbit."""
    band_set = _band_set(Band(name="water", role="SWIR_1450", centre_nm=1450.0, fwhm_nm=50.0))
    assert errors(check_atmospheric_windows(band_set, windows))


def test_band_whose_fwhm_extent_reaches_a_forbidden_region_is_rejected(windows):
    """A clear centre is not enough; the FWHM extent must also stay clear.

    A wide band centred at 1500 nm is outside the 1330-1490 nm water region by
    centre, but half its FWHM extent lies inside it.
    """
    band_set = _band_set(Band(name="wide", role="SWIR_1500", centre_nm=1500.0, fwhm_nm=80.0))
    findings = check_atmospheric_windows(band_set, windows)

    assert errors(findings)
    assert any("water_vapour_1400" in f.message for f in errors(findings))


def test_skirt_only_overlap_is_a_warning_not_an_error(windows):
    """Skirt overlap is real but second-order; out_of_band_leakage covers it.

    Sentinel-2's 1610 nm band has 90 nm FWHM. A single aggressive threshold
    would reject a band that demonstrably works in orbit, so skirt overlap
    must not be fatal.
    """
    band_set = _band_set(Band(name="swir1", role="SWIR1", centre_nm=1550.0, fwhm_nm=80.0))
    findings = check_atmospheric_windows(band_set, windows)

    assert not errors(findings)
    assert any(f.rule == "rule7_srf_skirt" for f in findings)


def test_sentinel2_swir1_band_is_not_rejected(windows, band_sets):
    """Regression guard: the real S2 B11 must pass rule 7."""
    s2 = band_sets["sentinel2_msi"]
    b11 = s2.by_role("SWIR1")
    assert b11 is not None and b11.fwhm_nm == 90.0
    assert not errors(check_atmospheric_windows(_band_set(b11), windows))


def test_1240nm_band_stays_clear_of_the_o2_feature(windows, band_sets):
    """Config B's 1240 nm band is placed to avoid the 1270 nm O2 band."""
    findings = check_atmospheric_windows(band_sets["config_b"], windows)
    assert not errors(findings)


def test_atmospheric_purpose_band_is_exempt(windows):
    """The 1375 nm cirrus band sits inside a water region by design."""
    cirrus = Band(
        name="cirrus",
        role="CIRRUS",
        centre_nm=1375.0,
        fwhm_nm=30.0,
        purpose=BandPurpose.ATMOSPHERIC,
    )
    findings = check_atmospheric_windows(_band_set(cirrus), windows)

    assert not errors(findings)
    assert any(f.severity is Severity.INFO for f in findings)

    # The same band without the atmospheric purpose must be rejected.
    surface = cirrus.model_copy(update={"purpose": BandPurpose.SURFACE})
    assert errors(check_atmospheric_windows(_band_set(surface), windows))


def test_swir_band_outside_a_sanctioned_window_warns_but_does_not_fail(windows):
    """Phase 4's candidate grid may explore beyond the listed windows."""
    band_set = _band_set(Band(name="odd", role="SWIR_2050", centre_nm=2050.0, fwhm_nm=20.0))
    findings = check_atmospheric_windows(band_set, windows)

    assert not errors(findings)
    assert any(f.severity is Severity.WARNING for f in findings)


@pytest.mark.parametrize("key", ["config_a", "config_b", "config_c", "sentinel2_msi"])
def test_shipped_band_sets_respect_rule_7(band_sets, windows, key):
    assert not errors(check_atmospheric_windows(band_sets[key], windows))


# --- detector coverage ------------------------------------------------------


def test_swir2_band_on_standard_ingaas_is_rejected(detectors):
    """The 1.7 um cutoff is why configuration C needs extended InGaAs.

    This is the single constraint behind the study's main cost/SWaP trade, so
    a config that violates it must fail at load time, not in the results.
    """
    band_set = _band_set(
        Band(
            name="swir2",
            role="SWIR2",
            centre_nm=2190.0,
            fwhm_nm=180.0,
            detector="ingaas_std",
        )
    )
    findings = check_detector_coverage(band_set, detectors)

    assert errors(findings)
    assert any("detector_spectral_range" == f.rule for f in errors(findings))


def test_swir2_band_on_extended_ingaas_is_accepted(detectors):
    band_set = _band_set(
        Band(
            name="swir2",
            role="SWIR2",
            centre_nm=2190.0,
            fwhm_nm=180.0,
            detector="ingaas_ext",
        )
    )
    assert not errors(check_detector_coverage(band_set, detectors))


def test_unknown_detector_reference_is_rejected(detectors):
    band_set = _band_set(
        Band(name="b", role="NIR", centre_nm=865.0, fwhm_nm=30.0, detector="nonexistent")
    )
    findings = check_detector_coverage(band_set, detectors)
    assert errors(findings)
    assert any("unknown detector" in f.message for f in errors(findings))


def test_band_without_a_detector_is_skipped(detectors):
    """A reference band set has no SAFARI detector assignment."""
    band_set = _band_set(Band(name="b", role="NIR", centre_nm=865.0, fwhm_nm=30.0))
    assert check_detector_coverage(band_set, detectors) == []


def test_config_c_swir_bands_sit_on_extended_ingaas(band_sets):
    """Guards against a configuration A/B/C mixup in the shipped configs."""
    config_c = band_sets["config_c"]
    for role in ("SWIR1", "SWIR2"):
        band = config_c.by_role(role)
        assert band is not None
        assert band.detector == "ingaas_ext"


@pytest.mark.parametrize("key", ["config_a", "config_b", "config_c"])
def test_shipped_configs_have_valid_detector_assignments(band_sets, detectors, key):
    assert not errors(check_detector_coverage(band_sets[key], detectors))


# --- near-duplicate bands ---------------------------------------------------


def test_negative_control_trips_the_near_duplicate_check(band_sets):
    """The negative control is built to look bad; it must actually look bad."""
    findings = check_band_separation(band_sets["negative_control"])
    assert findings
    assert all(f.severity is Severity.WARNING for f in findings)


@pytest.mark.parametrize("key", ["config_a", "config_b", "config_c", "sentinel2_msi"])
def test_real_band_sets_have_no_near_duplicates(band_sets, key):
    assert check_band_separation(band_sets[key]) == []


# --- placeholders -----------------------------------------------------------


def test_placeholder_configs_are_reported(study_config):
    """Unanswered Q2-Q6 must stay visible on every load."""
    findings = check_placeholders(study_config.placeholder_configs)
    subjects = {f.subject for f in findings}

    assert any(s.startswith("detector/") for s in subjects)
    assert any(s.startswith("optics/") for s in subjects)
    assert any(s.startswith("orbit/") for s in subjects)
    assert all(f.severity is Severity.WARNING for f in findings)


# --- aggregation ------------------------------------------------------------


@pytest.mark.parametrize(
    "key", ["config_a", "config_b", "config_c", "sentinel2_msi", "negative_control"]
)
def test_every_shipped_band_set_validates(band_sets, windows, detectors, key):
    """The Phase 0 'done when': configs load and validate."""
    findings = validate_band_set(band_sets[key], windows, detectors)
    assert not errors(findings), "\n".join(str(f) for f in errors(findings))


def test_raise_on_errors_raises_only_for_errors(windows):
    bad = _band_set(Band(name="water", role="SWIR_1940", centre_nm=1940.0, fwhm_nm=50.0))
    with pytest.raises(ValidationFailure):
        raise_on_errors(check_atmospheric_windows(bad, windows))

    warning_only = _band_set(Band(name="odd", role="SWIR_2050", centre_nm=2050.0, fwhm_nm=20.0))
    raise_on_errors(check_atmospheric_windows(warning_only, windows))
