"""Sensor noise model (brief Phase 2; CLAUDE.md rule 6).

Turns the detector, optics and orbit configurations into per-band noise in
REFLECTANCE units, so every P6 evaluation can add the noise a candidate
CubeSat band would carry.

THE MODEL
---------
For a band with spectral response S(lambda) (Gaussian, centre and FWHM from
the band set), a Lambertian surface of reflectance rho seen through the
atmosphere gives an at-sensor radiance

    L(lambda) = rho * E_sun(lambda) * cos(SZA) * T_atm / pi

and a pixel collects, in one integration,

    N_e = t_int * TDI * A_pupil * Omega_pixel * tau_optics
          * integral( L(lambda) * QE(lambda) * S(lambda) * lambda / (h c) ) dlambda

which is linear in rho: N_e = g * rho, g in electrons per unit reflectance.
Shot noise on the signal, dark current over the integration and read noise
(once per TDI stage, the conservative digital-TDI case) give

    sigma_e^2 = g * rho + dark_e_per_s * t + TDI * read_e^2
    sigma_rho = sigma_e / g = sqrt(rho / g + (dark + TDI read^2) / g^2)

E_sun is a 5778 K blackbody scaled to 1 AU (within ~10-20 % of measured
solar spectra away from the strongest Fraunhofer lines -- adequate while
every instrument number is a placeholder). T_atm is one scalar for the
two-way path; bands sit in windows (rule 7), so it is not modelled per
wavelength.

WHAT IS IGNORED, ON PURPOSE
---------------------------
Sentinel-2's and AVIRIS-NG's own noise is not subtracted. The P6 inputs are
medians of 5-20 clear Sentinel-2 observations, or 4 x 4 block means of
AVIRIS-NG pixels, so their noise is already well below a single CubeSat
acquisition's; adding the full CubeSat noise on top slightly overstates the
total, which errs toward penalising a band rather than flattering it.
Quantisation, PRNU, stray light and residual atmospheric-correction error
are not modelled yet (Phase 5).

PLACEHOLDERS
------------
The detector, optics and orbit configurations are labelled placeholders
(Q2-Q4; A-2 to A-4). Every result computed with this module inherits that
label, and ``NoiseModel.placeholder`` carries it.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from safari_bands.config.schemas import Band, BandSet, Detector, Optics, Orbit

H = 6.62607015e-34          # J s
C = 2.99792458e8            # m / s
K_B = 1.380649e-23          # J / K
T_SUN = 5778.0              # K
R_SUN = 6.957e8             # m
AU = 1.495978707e11         # m

#: Solar zenith angle for the reference case: spring overpasses at 45-60 N
#: (brief section 4). 55 degrees, so cos = 0.57.
DEFAULT_SZA_DEG = 55.0
#: Two-way atmospheric transmittance in a window (placeholder).
DEFAULT_T_ATM = 0.8


def solar_irradiance(wavelength_nm: np.ndarray) -> np.ndarray:
    """Top-of-atmosphere solar spectral irradiance, W m^-2 um^-1 (blackbody)."""
    lam = np.asarray(wavelength_nm, float) * 1e-9
    radiance = 2 * H * C**2 / lam**5 / np.expm1(H * C / (lam * K_B * T_SUN))  # W m^-2 sr^-1 m^-1
    return math.pi * radiance * (R_SUN / AU) ** 2 * 1e-6


def gaussian_srf(centre_nm: float, fwhm_nm: float, step_nm: float = 1.0):
    """(wavelengths, normalised peak-1 response) over +/- 3 sigma."""
    sigma = fwhm_nm / (2 * math.sqrt(2 * math.log(2)))
    lam = np.arange(centre_nm - 3 * sigma, centre_nm + 3 * sigma + step_nm, step_nm)
    return lam, np.exp(-0.5 * ((lam - centre_nm) / sigma) ** 2)


@dataclass(frozen=True)
class BandNoise:
    """One band's noise: sigma(rho) = sqrt(rho / g + var0 / g^2)."""

    name: str
    gain_e_per_rho: float          # g: electrons per unit reflectance
    var0_e2: float                 # dark + read variance, electrons^2
    saturates_at_rho: float        # reflectance that fills the well

    def sigma(self, rho):
        rho = np.clip(np.asarray(rho, float), 0.0, None)
        return np.sqrt(rho / self.gain_e_per_rho + self.var0_e2 / self.gain_e_per_rho**2)

    def snr(self, rho):
        rho = np.asarray(rho, float)
        return rho / self.sigma(rho)


@dataclass(frozen=True)
class NoiseModel:
    """Per-band noise for one band set, with its provenance."""

    bands: dict[str, BandNoise]
    sza_deg: float
    t_atm: float
    placeholder: bool
    notes: list[str] = field(default_factory=list)

    def sigma(self, name: str, rho):
        return self.bands[name].sigma(rho)

    def add(self, refl: np.ndarray, names: list[str], rng: np.random.Generator,
            axis: int = 0) -> np.ndarray:
        """Add independent Gaussian noise to reflectance (bands along ``axis``)."""
        out = np.array(refl, float, copy=True)
        moved = np.moveaxis(out, axis, 0)
        for i, n in enumerate(names):
            moved[i] = moved[i] + rng.standard_normal(moved[i].shape) * self.sigma(n, moved[i])
        return out


def band_noise(band: Band, detector: Detector, optics: Optics, orbit: Orbit,
               sza_deg: float = DEFAULT_SZA_DEG, t_atm: float = DEFAULT_T_ATM) -> BandNoise:
    lam, srf = gaussian_srf(band.centre_nm, band.fwhm_nm)
    qe = np.interp(lam, detector.qe_curve.wavelength_nm, detector.qe_curve.qe, left=0.0, right=0.0)
    lo, hi = detector.spectral_range_nm
    qe = np.where((lam >= lo) & (lam <= hi), qe, 0.0)
    e_sun = solar_irradiance(lam)                                         # W m^-2 um^-1
    # W m^-2 sr^-1 um^-1 per unit reflectance
    radiance_per_rho = e_sun * math.cos(math.radians(sza_deg)) * t_atm / math.pi
    photons = radiance_per_rho * qe * srf * (lam * 1e-9) / (H * C)       # e- s^-1 m^-2 sr^-1 um^-1
    flux = np.trapezoid(photons, lam * 1e-3)                              # e- s^-1 m^-2 sr^-1
    area = math.pi * (optics.aperture_diameter_mm * 1e-3 / 2) ** 2
    omega = (detector.pixel_pitch_um * 1e-6 / (optics.focal_length_mm * 1e-3)) ** 2
    t = orbit.integration_time_ms * 1e-3 * orbit.tdi_stages
    g = flux * area * omega * optics.transmission * t
    if g <= 0:
        raise ValueError(f"band {band.name} ({band.centre_nm} nm) is outside detector "
                         f"{detector.name}'s response {detector.spectral_range_nm}")
    dark = detector.dark_current.at_temperature(detector.operating_temperature_k) * t
    var0 = dark + orbit.tdi_stages * detector.read_noise_e**2
    return BandNoise(band.name, float(g), float(var0), float(detector.full_well_e / g))


#: When a band names no detector, the cheapest one that covers its centre:
#: silicon, then standard InGaAs (to 1.7 um), then extended InGaAs (brief s5).
DETECTOR_PREFERENCE = ("silicon_cmos", "ingaas_std", "ingaas_ext")


def pick_detector(centre_nm: float, detectors: dict[str, Detector]) -> str:
    for key in DETECTOR_PREFERENCE:
        if key in detectors and detectors[key].covers(centre_nm):
            return key
    raise ValueError(f"no detector covers {centre_nm} nm")


def noise_for(centre_nm: float, fwhm_nm: float, detectors: dict[str, Detector],
              optics: Optics, orbit: Orbit, sza_deg: float = DEFAULT_SZA_DEG,
              t_atm: float = DEFAULT_T_ATM, detector: str | None = None) -> BandNoise:
    """Noise for an arbitrary candidate band (the P6 broad grids, E-61/E-62)."""
    key = detector or pick_detector(centre_nm, detectors)
    band = Band(name=f"{centre_nm:g}/{fwhm_nm:g}", role="CANDIDATE", centre_nm=centre_nm,
                fwhm_nm=fwhm_nm)
    return band_noise(band, detectors[key], optics, orbit, sza_deg, t_atm)


def noise_model(band_set: BandSet, detectors: dict[str, Detector], optics: Optics,
                orbit: Orbit, sza_deg: float = DEFAULT_SZA_DEG,
                t_atm: float = DEFAULT_T_ATM) -> NoiseModel:
    """Noise for every band in ``band_set``. A band uses the detector it
    names, else the cheapest detector covering its centre."""
    out, notes = {}, []
    placeholder = bool(optics.placeholder or orbit.placeholder)
    for b in band_set.bands:
        key = b.detector or pick_detector(b.centre_nm, detectors)
        if key not in detectors:
            raise KeyError(f"band {b.name}: no detector {key!r} (have {sorted(detectors)})")
        det = detectors[key]
        placeholder |= bool(det.placeholder)
        bn = band_noise(b, det, optics, orbit, sza_deg, t_atm)
        if bn.saturates_at_rho < 1.0:
            notes.append(f"{b.name}: the well fills at reflectance {bn.saturates_at_rho:.2f}")
        out[b.name] = bn
    return NoiseModel(out, sza_deg, t_atm, placeholder, notes)
