"""The sensor noise model (rule 6): physics checks, not just smoke."""
from __future__ import annotations

import math

import numpy as np
import pytest

from safari_bands.config.loader import (
    load_all_band_sets,
    load_all_detectors,
    load_optics,
    load_orbit,
)
from safari_bands.sensor import (
    BandNoise,
    band_noise,
    noise_for,
    noise_model,
    pick_detector,
    solar_irradiance,
)


@pytest.fixture(scope="module")
def inst():
    return load_all_detectors(), load_optics(), load_orbit()


def test_solar_irradiance_is_close_to_the_measured_spectrum():
    """Blackbody at 5778 K, 1 AU: within 25 % of the measured solar spectrum
    (about 1950, 960, 240 and 85 W m-2 um-1 at 500, 865, 1610, 2190 nm)."""
    got = solar_irradiance([500, 865, 1610, 2190])
    for g, want in zip(got, (1950, 960, 240, 85), strict=True):
        assert abs(g - want) / want < 0.25


def test_gain_matches_a_hand_calculation(inst):
    """A narrow band at a flat QE reduces to the textbook photon budget."""
    dets, optics, orbit = inst
    det = dets["silicon_cmos"]
    bn = noise_for(650.0, 2.0, dets, optics, orbit, detector="silicon_cmos")
    lam = 650e-9
    qe = float(np.interp(650, det.qe_curve.wavelength_nm, det.qe_curve.qe))
    rad = float(solar_irradiance([650])[0]) * math.cos(math.radians(55)) * 0.8 / math.pi
    sigma = 2.0 / (2 * math.sqrt(2 * math.log(2)))
    band_um = sigma * math.sqrt(2 * math.pi) * 1e-3          # integral of a peak-1 Gaussian
    flux = rad * band_um * qe * lam / (6.62607015e-34 * 2.99792458e8)
    area = math.pi * (optics.aperture_diameter_mm * 1e-3 / 2) ** 2
    omega = (det.pixel_pitch_um / optics.focal_length_mm * 1e-3) ** 2
    want = flux * area * omega * optics.transmission * orbit.integration_time_ms * 1e-3
    assert bn.gain_e_per_rho == pytest.approx(want, rel=0.02)


def test_noise_shrinks_with_bandwidth_and_signal(inst):
    dets, optics, orbit = inst
    narrow = noise_for(865, 10, dets, optics, orbit)
    wide = noise_for(865, 60, dets, optics, orbit)
    assert wide.snr(0.2) > narrow.snr(0.2)
    assert narrow.snr(0.4) > narrow.snr(0.1)                  # shot noise: SNR ~ sqrt(rho)


def test_band_outside_its_detector_is_refused(inst):
    dets, optics, orbit = inst
    with pytest.raises(ValueError, match="outside detector"):
        noise_for(1610, 40, dets, optics, orbit, detector="silicon_cmos")


def test_detector_follows_wavelength(inst):
    dets = inst[0]
    assert pick_detector(665, dets) == "silicon_cmos"
    assert pick_detector(1610, dets) == "ingaas_std"
    assert pick_detector(2190, dets) == "ingaas_ext"


def test_added_noise_has_the_stated_spread():
    bn = BandNoise("x", gain_e_per_rho=2.0e4, var0_e2=400.0, saturates_at_rho=1.5)
    rho = np.full(200_000, 0.2)
    from safari_bands.sensor import NoiseModel
    nm = NoiseModel({"x": bn}, 55.0, 0.8, True)
    got = nm.add(rho[None], ["x"], np.random.default_rng(0))[0]
    assert np.std(got - rho) == pytest.approx(float(bn.sigma(0.2)), rel=0.01)


@pytest.mark.parametrize("name", ["sentinel2_msi", "config_a", "config_b", "config_c",
                                  "sensor_mantis_vnir6", "sensor_mantis_swir4"])
def test_every_band_set_gets_a_finite_positive_snr(inst, name):
    dets, optics, orbit = inst
    nm = noise_model(load_all_band_sets()[name], dets, optics, orbit)
    assert nm.placeholder                                      # Q2-Q4 unanswered
    for bn in nm.bands.values():
        s = float(bn.snr(0.2))
        assert np.isfinite(s) and s > 1


def test_band_noise_uses_the_named_detector(inst):
    dets, optics, orbit = inst
    b = load_all_band_sets()["config_c"].bands[-1]            # swir2, extended InGaAs
    assert band_noise(b, dets[b.detector], optics, orbit).gain_e_per_rho > 0
