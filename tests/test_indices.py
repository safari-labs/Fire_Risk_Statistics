"""Index feasibility across candidate band sets.

These tests encode, as facts about the hardware, the structural claims behind
hypotheses H1-H3. They do not test the hypotheses themselves -- that needs the
forward model and the retrieval, in Phases 1-4. What they pin down is the part
that is already decided by band placement alone: configuration A cannot form
NDTI at any SNR, because NDTI needs a SWIR1/SWIR2 contrast that A does not have.
"""

from __future__ import annotations

import pytest

from safari_bands.indices import (
    coverage_by_target,
    feasibility_matrix,
    feasible_indices,
    infeasible_indices,
    render_matrix,
    resolve_index,
)


def _feasible(catalogue, band_sets, index_name, band_set_key) -> bool:
    index = catalogue.by_name(index_name)
    assert index is not None, f"index {index_name} missing from the catalogue"
    return resolve_index(index, band_sets[band_set_key]).feasible


# --- H2: SWIR2 is necessary for curing; 1240 nm is not a substitute ---------


def test_ndti_needs_swir2_so_only_config_c_can_form_it(catalogue, band_sets):
    """NDTI/NBR2 is central to target T2 (curing / NPV)."""
    assert _feasible(catalogue, band_sets, "NDTI", "config_c")
    assert _feasible(catalogue, band_sets, "NDTI", "sentinel2_msi")
    assert not _feasible(catalogue, band_sets, "NDTI", "config_a")
    assert not _feasible(catalogue, band_sets, "NDTI", "config_b")


def test_nbr2_alias_resolves_to_ndti(catalogue):
    assert catalogue.by_name("NBR2") is catalogue.by_name("NDTI")


def test_adding_1240nm_does_not_unlock_any_swir2_index(catalogue, band_sets):
    """The config-level form of H2: 1240 nm is not a substitute for SWIR2.

    Everything configuration A can form, B can form, and B adds exactly one
    index -- Gao's NDWI. No SWIR2-dependent index becomes available.
    """
    a = {i.name for i in feasible_indices(catalogue, band_sets["config_a"])}
    b = {i.name for i in feasible_indices(catalogue, band_sets["config_b"])}

    assert a < b, "config B should be a strict superset of config A"
    assert b - a == {"NDWI_Gao"}

    swir2_indices = {
        i.name for i in catalogue.indices if "SWIR2" in i.requires_roles
    }
    assert swir2_indices, "expected some indices to depend on SWIR2"
    assert not (b & swir2_indices)


# --- H1/H3: what configuration B recovers -----------------------------------


def test_config_b_gains_gao_ndwi_over_config_a(catalogue, band_sets):
    """The 1240 nm water band is the point of configuration B."""
    assert _feasible(catalogue, band_sets, "NDWI_Gao", "config_b")
    assert not _feasible(catalogue, band_sets, "NDWI_Gao", "config_a")
    assert not _feasible(catalogue, band_sets, "NDWI_Gao", "config_c")


def test_nmdi_needs_both_swir_bands(catalogue, band_sets):
    """NMDI uses the SWIR1/SWIR2 difference H1 calls for."""
    assert _feasible(catalogue, band_sets, "NMDI", "config_c")
    assert not _feasible(catalogue, band_sets, "NMDI", "config_a")
    assert not _feasible(catalogue, band_sets, "NMDI", "config_b")


def test_every_config_can_form_the_basic_moisture_index(catalogue, band_sets):
    """NDMI needs only NIR and SWIR1, which all three configurations carry."""
    for key in ("config_a", "config_b", "config_c"):
        assert _feasible(catalogue, band_sets, "NDMI", key)
        assert _feasible(catalogue, band_sets, "MSI", key)


def test_ndmi_and_ndii_are_the_same_index(catalogue):
    assert catalogue.by_name("NDII") is catalogue.by_name("NDMI")


# --- controls ----------------------------------------------------------------


def test_negative_control_can_form_nothing(catalogue, band_sets):
    """Four near-duplicate red bands should support no index at all.

    If a later phase reports skill for this set, the evaluation is broken.
    """
    assert feasible_indices(catalogue, band_sets["negative_control"]) == []


def test_sentinel2_benchmark_forms_every_multispectral_index(catalogue, band_sets):
    """The positive benchmark should be limited only by 1240 nm, CAI, and --
    since the P6 index extension -- IRECI, whose 783 nm band (B7) is not among
    the brief's eight nominal Sentinel-2 centres this set carries."""
    missing = {i.name for i in infeasible_indices(catalogue, band_sets["sentinel2_msi"])}
    assert missing == {"NDWI_Gao", "CAI", "IRECI"}


def test_cai_is_infeasible_for_every_multispectral_set(catalogue, band_sets):
    """CAI needs three narrow bands across 2.0-2.2 um; it is a hyperspectral bound."""
    cai = catalogue.by_name("CAI")
    assert cai is not None and cai.hyperspectral_only
    for key, band_set in band_sets.items():
        result = resolve_index(cai, band_set)
        assert not result.feasible, f"{key} unexpectedly forms CAI"
        assert result.status == "n/a (hyperspectral)"


# --- ancillary requirements ---------------------------------------------------


def test_ndsi_is_available_wherever_snow_discrimination_is_needed(catalogue, band_sets):
    """Cloud/snow discrimination and snow-off timing need green + SWIR1."""
    for key in ("config_a", "config_b", "config_c", "sentinel2_msi"):
        assert _feasible(catalogue, band_sets, "NDSI", key)


# --- mechanics ----------------------------------------------------------------


def test_missing_roles_are_reported(catalogue, band_sets):
    result = resolve_index(catalogue.by_name("NDTI"), band_sets["config_a"])
    assert result.missing_roles == ("SWIR2",)
    assert "SWIR2" in result.explain()


def test_matrix_covers_every_index_and_band_set(catalogue, band_sets):
    matrix = feasibility_matrix(catalogue, band_sets)
    assert set(matrix) == {i.name for i in catalogue.indices}
    for row in matrix.values():
        assert set(row) == set(band_sets)


def test_coverage_by_target_totals_match_the_catalogue(catalogue, band_sets):
    coverage = coverage_by_target(catalogue, band_sets["config_c"])
    assert sum(total for _, total in coverage.values()) == len(catalogue.indices)
    for feasible, total in coverage.values():
        assert 0 <= feasible <= total


def test_config_c_has_curing_coverage_where_a_and_b_do_not(catalogue, band_sets):
    """Target T2 is where the extended-InGaAs cost is supposed to buy something."""
    t2_feasible = {
        key: coverage_by_target(catalogue, band_sets[key]).get("T2", (0, 0))[0]
        for key in ("config_a", "config_b", "config_c")
    }
    assert t2_feasible["config_a"] == 0
    assert t2_feasible["config_b"] == 0
    assert t2_feasible["config_c"] > 0


@pytest.mark.parametrize("key", ["config_a", "config_b", "config_c"])
def test_render_matrix_mentions_every_band_set(catalogue, band_sets, key):
    rendered = render_matrix(catalogue, band_sets)
    assert key in rendered
    assert "NDMI" in rendered
