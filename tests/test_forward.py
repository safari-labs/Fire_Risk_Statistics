"""Phase 1 forward model: physically sensible behaviour (brief Phase 1, 'done when')."""
from __future__ import annotations

import numpy as np
import pytest

from safari_bands.config.loader import load_band_set, load_priors

prosail = pytest.importorskip("prosail")
from safari_bands import forward as F  # noqa: E402

BASE = {"n": 2.0, "cab": 40.0, "car": 8.0, "cbrown": 0.1, "ant": 0.5, "cm": 0.02,
        "lfmc": 120.0, "lai": 3.0, "ala": 55.0, "hspot": 0.1, "rsoil": 0.8, "psoil": 0.5,
        "tts": 45.0, "tto": 5.0, "psi": 90.0}


def at(spectrum: np.ndarray, nm: float) -> float:
    return float(spectrum[int(nm) - 400])


def run(**change) -> np.ndarray:
    return F.Prosail().reflectance({**BASE, **change})


def test_spectrum_spans_the_grid_and_is_a_reflectance():
    r = run()
    assert r.shape == F.WAVELENGTHS.shape
    assert np.all(r >= 0) and np.all(r < 1)


def test_more_water_lowers_swir_and_spares_the_visible():
    wet, dry = run(lfmc=200.0), run(lfmc=70.0)
    for nm in (1240, 1610, 2190):
        assert at(wet, nm) < at(dry, nm), nm
    assert abs(at(wet, 560) - at(dry, 560)) < 0.002


def test_more_dry_matter_at_fixed_lfmc_darkens_swir():
    # Cw follows Cm at fixed LFMC, so both absorbers rise together.
    lo, hi = run(cm=0.012), run(cm=0.035)
    d1610 = at(lo, 1610) - at(hi, 1610)
    d2190 = at(lo, 2190) - at(hi, 2190)
    assert d1610 > 0 and d2190 > 0


def test_chlorophyll_darkens_red_and_lai_brightens_nir():
    assert at(run(cab=60.0), 665) < at(run(cab=20.0), 665)
    assert at(run(lai=5.0, rsoil=0.3), 865) > at(run(lai=0.5, rsoil=0.3), 865)


def test_cw_is_derived_from_lfmc_and_cm():
    assert F.cw_from(150.0, 0.02) == pytest.approx(0.03)


def test_sample_respects_bounds_and_seed():
    pr = load_priors("lfmc_v1")
    a = F.sample(pr, "conifer", n=256)
    b = F.sample(pr, "conifer", n=256)
    for c in F.COLUMNS:
        lo, hi = {**pr.groups["conifer"], **pr.geometry}[c]
        assert a[c].min() >= lo and a[c].max() <= hi, c
        assert np.array_equal(a[c], b[c])
    assert np.allclose(100 * a["cw"] / a["cm"], a["lfmc"])
    assert not np.array_equal(F.sample(pr, "deciduous", n=256)["lai"], a["lai"])


def test_srf_rows_sum_to_one_and_keep_a_flat_spectrum_flat():
    bs = load_band_set("sentinel2_p6_12band")
    names, w = F.srf_matrix(bs, ["B4", "B11", "B12"])
    assert names == ["B4", "B11", "B12"]
    assert np.allclose(w.sum(1), 1)
    _, x = F.band_reflectance(np.full((2, F.WAVELENGTHS.size), 0.3), bs, names)
    assert np.allclose(x, 0.3)
    with pytest.raises(KeyError):
        F.srf_matrix(bs, ["B99"])


def test_simulate_matches_one_call_per_row():
    pr = load_priors("lfmc_v1")
    p = F.sample(pr, "deciduous", n=4)
    s = F.simulate(F.Prosail(), p)
    one = F.Prosail().reflectance({c: float(p[c][2]) for c in F.COLUMNS})
    assert s.shape == (4, F.WAVELENGTHS.size)
    assert np.allclose(s[2], one, atol=1e-6)
