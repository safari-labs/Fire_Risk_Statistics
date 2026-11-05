"""Forward model, brief Phase 1: leaf and canopy reflectance from parameters.

Top-of-canopy reflectance at 1 nm, 400-2500 nm, from radiative transfer only
(rule 2). Behind a small interface so a discontinuous-canopy model (INFORM,
4-Scale, DART) can replace the turbid medium for conifer stands later (brief
section 2: SL2P's forest bias is a clumping problem).

    PROSPECT-D (leaf)  ->  4SAIL (canopy over a soil background)

THE TARGET
----------
LFMC (%) = 100 x Cw / Cm. Priors sample LFMC and Cm and derive Cw, so the
label is an input of the simulation, never an output or an index (rule 3).

WHAT IS PLACEHOLDER (A-47)
--------------------------
* 4SAIL is a turbid medium: every fuel, conifer stands included, is a
  horizontally homogeneous canopy.
* PROSPECT is a broadleaf model; needles are approximated by a high N.
* PROSPECT-PRO is not in the Python package (A-7), so dry matter is one Cm.
* The background is prosail's dry/wet soil mixture only; moss, lichen, litter
  and snow wait for a spectral library.
* Priors are uniform and wide (config/priors/).
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

import numpy as np

from safari_bands.config.schemas import (
    GEOMETRY_PARAMETERS,
    PRIOR_PARAMETERS,
    BandSet,
    PriorSet,
)

#: The simulation grid, nm.
WAVELENGTHS = np.arange(400, 2501)
#: Columns of a parameter table, in a fixed order.
COLUMNS = (*PRIOR_PARAMETERS, *GEOMETRY_PARAMETERS)


def cw_from(lfmc, cm):
    """Equivalent water thickness (g cm-2) from LFMC (%) and dry matter (g cm-2)."""
    return np.asarray(lfmc, float) * np.asarray(cm, float) / 100.0


class CanopyModel(Protocol):
    """Anything that turns one parameter row into 1 nm reflectance."""

    name: str

    def reflectance(self, p: Mapping[str, float]) -> np.ndarray:
        ...


class Prosail:
    """PROSPECT-D + 4SAIL (the ``prosail`` package), bidirectional reflectance
    factor, ellipsoidal leaf angles from the mean inclination ``ala``."""

    name = "prospect_d_4sail"

    def reflectance(self, p: Mapping[str, float]) -> np.ndarray:
        import prosail
        return prosail.run_prosail(
            n=p["n"], cab=p["cab"], car=p["car"], cbrown=p["cbrown"],
            cw=float(cw_from(p["lfmc"], p["cm"])), cm=p["cm"], ant=p["ant"],
            lai=p["lai"], lidfa=p["ala"], hspot=p["hspot"],
            tts=p["tts"], tto=p["tto"], psi=p["psi"],
            prospect_version="D", typelidf=2, rsoil=p["rsoil"], psoil=p["psoil"],
            factor="SDR")


CANOPY_MODELS: dict[str, type] = {Prosail.name: Prosail}


def sample(priors: PriorSet, group: str, n: int | None = None,
           seed: int | None = None) -> dict[str, np.ndarray]:
    """Scrambled Sobol points scaled to the group's uniform priors.

    Seeded from the prior set (offset by the group's position) unless a seed
    is given, so a group's sample never depends on which other groups ran.
    """
    from scipy.stats import qmc
    n = priors.samples_per_group if n is None else n
    if seed is None:
        seed = priors.seed + list(priors.groups).index(group)
    ranges = {**priors.groups[group], **priors.geometry}
    lo = np.array([ranges[c][0] for c in COLUMNS], float)
    hi = np.array([ranges[c][1] for c in COLUMNS], float)
    u = qmc.Sobol(d=len(COLUMNS), scramble=True, seed=seed).random(n)
    x = lo + u * (hi - lo)
    out = {c: x[:, i] for i, c in enumerate(COLUMNS)}
    out["cw"] = cw_from(out["lfmc"], out["cm"])
    return out


def simulate(model: CanopyModel, params: Mapping[str, np.ndarray]) -> np.ndarray:
    """(N, 2101) float32 reflectance, one model call per row."""
    n = len(params["lfmc"])
    out = np.empty((n, WAVELENGTHS.size), np.float32)
    for i in range(n):
        out[i] = model.reflectance({c: float(params[c][i]) for c in COLUMNS})
    return out


def srf_matrix(band_set: BandSet, names: list[str] | None = None) -> tuple[list[str], np.ndarray]:
    """Gaussian spectral responses on the 1 nm grid, each row summing to 1."""
    bands = [b for b in band_set.bands if names is None or b.name in names]
    if names is not None:
        order = {n: i for i, n in enumerate(names)}
        missing = set(names) - {b.name for b in bands}
        if missing:
            raise KeyError(f"{band_set.name} has no band {sorted(missing)}")
        bands.sort(key=lambda b: order[b.name])
    w = np.empty((len(bands), WAVELENGTHS.size))
    for i, b in enumerate(bands):
        sigma = b.fwhm_nm / (2 * np.sqrt(2 * np.log(2)))
        w[i] = np.exp(-0.5 * ((WAVELENGTHS - b.centre_nm) / sigma) ** 2)
        w[i] /= w[i].sum()
    return [b.name for b in bands], w


def band_reflectance(spectra: np.ndarray, band_set: BandSet,
                     names: list[str] | None = None) -> tuple[list[str], np.ndarray]:
    """Convolve (N, 2101) spectra to (N, bands) with the band set's responses."""
    names, w = srf_matrix(band_set, names)
    return names, (np.asarray(spectra, np.float64) @ w.T).astype(np.float32)


def atmospheric_sigma(rho: np.ndarray, absolute: float, relative: float) -> np.ndarray:
    """Residual atmospheric-correction error, as a standard deviation."""
    return absolute + relative * np.abs(rho)
