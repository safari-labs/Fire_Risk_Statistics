"""Figure labels for Sentinel-2 bands: "B5 (Red edge 1)"."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from safari_bands.band_names import ROLE_NAMES, ROLE_SOURCES, band_label, band_name, s2_roles
from safari_bands.config.loader import load_all_band_sets

FW_NAMES = (Path(__file__).resolve().parents[2] / "Fire_Risk_FW" / "src"
            / "fire_risk_fw" / "band_names.py")


def test_labels_carry_id_and_name():
    assert band_label("B2") == "B2 (Blue)"
    assert band_label("B5") == "B5 (Red edge 1)"
    assert band_label("B11") == "B11 (SWIR 1)"
    assert band_label("B12") == "B12 (SWIR 2)"
    assert band_label("B9", sep="\n") == "B9\n(Water vapour)"


def test_b8a_is_narrow_nir_not_the_benchmark_s_nir():
    """sentinel2_msi.yaml uses B8A as its NIR; the candidate pool, which
    mirrors the packed data, carries B8 as NIR and B8A as narrow NIR."""
    assert band_name("B8") == "NIR"
    assert band_name("B8A") == "Narrow NIR"


def test_unknown_names_pass_through():
    for s in ("NDMI", "(none)", ""):
        assert band_label(s) == s


def test_every_sentinel2_band_has_a_name():
    """Every band in the sets the labels come from. Sensor band sets
    (HS_00..., the Mantis modes) use their own role names and are labelled
    by those, not by this table."""
    sets = load_all_band_sets()
    for src in ROLE_SOURCES:
        for b in sets[src].bands:
            assert band_name(b.name), f"{src}: {b.name} ({b.role})"


@pytest.mark.skipif(not FW_NAMES.exists(), reason="Fire_Risk_FW not alongside")
def test_agrees_with_fire_risk_fw():
    """The two repos draw the same figures' labels; they must not differ."""
    spec = importlib.util.spec_from_file_location("_fw_band_names", FW_NAMES)
    fw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fw)
    assert fw.ROLE_NAMES == ROLE_NAMES
    for band, role in s2_roles().items():
        assert fw.S2_ROLES.get(band) == role, band
