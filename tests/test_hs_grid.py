"""The P6a-HS candidate grid: rule 7, detector limits, the red-edge exclusion."""
from __future__ import annotations

import json

import pytest

from safari_bands.cli import main
from safari_bands.config.loader import load_study_config
from safari_bands.hs_grid import build_table, load_grid


@pytest.fixture(scope="module")
def table():
    c = load_study_config()
    return build_table(load_grid(), c.detectors, c.optics, c.orbit, c.windows)


@pytest.fixture(scope="module")
def windows():
    return load_study_config().windows


def _extent(b, mult=1.0):
    h = 0.5 * b["fwhm_nm"] * mult
    return b["centre_nm"] - h, b["centre_nm"] + h


def test_no_candidate_sits_in_a_forbidden_region(table, windows):
    """Rule 7: the extent of every searched band misses every absorption feature."""
    for arm, ids in table["arms"].items():
        for i in ids:
            lo, hi = _extent(table["bands"][i], windows.error_fwhm_multiplier)
            hits = [r.name for r in windows.forbidden_regions if r.overlaps(lo, hi)]
            assert not hits, f"{arm} {i} overlaps {hits}"


def test_candidates_fit_their_detector():
    c = load_study_config()
    t = build_table(load_grid(), c.detectors, c.optics, c.orbit, c.windows)
    for arm, ids in t["arms"].items():
        for i in ids:
            b = t["bands"][i]
            lo, hi = c.detectors[b["detector"]].spectral_range_nm
            a, z = _extent(b)
            assert lo <= a and z <= hi, (arm, i)


def test_standard_ingaas_never_reaches_swir2(table):
    assert max(table["bands"][i]["centre_nm"] for i in table["arms"]["swir_std"]) < 1750
    assert max(table["bands"][i]["centre_nm"] for i in table["arms"]["swir_ext"]) > 2000


def test_no_red_edge_arm_has_no_response_in_700_760(table):
    for i in table["arms"]["vnir_no_red_edge"]:
        a, z = _extent(table["bands"][i])
        assert z <= 700 or a >= 760, i
    assert set(table["arms"]["vnir_no_red_edge"]) < set(table["arms"]["vnir"])


def test_swir_searches_fix_the_vnir_and_vnir_searches_fix_nothing(table):
    assert table["fixed"]["vnir"] == [] and table["fixed"]["vnir_no_red_edge"] == []
    fixed = table["fixed"]["swir_std"]
    assert fixed and all(table["bands"][i]["detector"] == "silicon_cmos" for i in fixed)


def test_every_band_has_noise_parameters(table):
    for i, b in table["bands"].items():
        assert b["gain_e_per_rho"] > 0 and b["var0_e2"] > 0, i


def test_cli_writes_the_table(tmp_path, capsys):
    out = tmp_path / "grid.json"
    assert main(["hs-grid", "--json", str(out)]) == 0
    t = json.loads(out.read_text(encoding="utf-8"))
    assert t["placeholder"] is True and "statistics_commit" in t
    assert set(t["arms"]) == {"vnir", "vnir_no_red_edge", "swir_std", "swir_ext"}
