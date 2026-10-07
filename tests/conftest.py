"""Shared fixtures."""

from __future__ import annotations

import pytest

from safari_bands.config.loader import (
    load_all_band_sets,
    load_all_detectors,
    load_atmospheric_windows,
    load_index_catalogue,
    load_study_config,
)


@pytest.fixture(scope="session")
def study_config():
    return load_study_config()


@pytest.fixture(scope="session")
def band_sets():
    return load_all_band_sets()


@pytest.fixture(scope="session")
def detectors():
    return load_all_detectors()


@pytest.fixture(scope="session")
def windows():
    return load_atmospheric_windows()


@pytest.fixture(scope="session")
def catalogue():
    return load_index_catalogue()
