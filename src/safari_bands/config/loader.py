"""Loading configuration from YAML under ``config/``.

Nothing in this module hard-codes a band, a detector parameter or a wavelength;
it only finds and parses files. The study's numbers live in YAML so they can be
versioned, diffed and swapped per run.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TypeVar

import yaml
from pydantic import BaseModel, ValidationError

from safari_bands.config.schemas import (
    AtmosphericWindows,
    BandSet,
    Detector,
    IndexCatalogue,
    Optics,
    Orbit,
)

M = TypeVar("M", bound=BaseModel)

#: Environment variable that overrides config discovery, mainly for tests.
CONFIG_DIR_ENV = "SAFARI_CONFIG_DIR"


class ConfigError(Exception):
    """Raised when a config file is missing or malformed."""


@lru_cache(maxsize=1)
def project_root() -> Path:
    """Locate the repository root by walking up for a marker file."""
    for candidate in [Path(__file__).resolve(), *Path(__file__).resolve().parents]:
        if (candidate / "pyproject.toml").is_file():
            return candidate
    raise ConfigError("could not locate the project root (no pyproject.toml found above this file)")


def config_dir() -> Path:
    """Return the configuration directory.

    Honours ``SAFARI_CONFIG_DIR`` so tests can point at a fixture tree.
    """
    override = os.environ.get(CONFIG_DIR_ENV)
    root = Path(override) if override else project_root() / "config"
    if not root.is_dir():
        raise ConfigError(f"configuration directory not found: {root}")
    return root


def load_yaml(path: Path) -> dict:
    """Read a YAML file into a dict."""
    if not path.is_file():
        raise ConfigError(f"config file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ConfigError(f"config file must contain a YAML mapping at the top level: {path}")
    return data


def parse_as(model: type[M], data: dict, path: Path) -> M:
    """Validate ``data`` against ``model``, reporting the source file on failure."""
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise ConfigError(f"invalid {model.__name__} in {path}:\n{exc}") from exc


def _load_one(model: type[M], path: Path) -> M:
    return parse_as(model, load_yaml(path), path)


def load_band_set(name_or_path: str | Path) -> BandSet:
    """Load a band set by name (``config_b``) or by path."""
    path = _resolve(name_or_path, config_dir() / "bands")
    return _load_one(BandSet, path)


def load_detector(name_or_path: str | Path) -> Detector:
    """Load a detector config by name (``ingaas_std``) or by path."""
    path = _resolve(name_or_path, config_dir() / "detector")
    return _load_one(Detector, path)


def load_optics(name_or_path: str | Path = "default") -> Optics:
    path = _resolve(name_or_path, config_dir() / "optics")
    return _load_one(Optics, path)


def load_orbit(name_or_path: str | Path = "default") -> Orbit:
    path = _resolve(name_or_path, config_dir() / "orbit")
    return _load_one(Orbit, path)


def load_atmospheric_windows() -> AtmosphericWindows:
    return _load_one(AtmosphericWindows, config_dir() / "atmospheric_windows.yaml")


def load_index_catalogue() -> IndexCatalogue:
    return _load_one(IndexCatalogue, config_dir() / "indices.yaml")


def _resolve(name_or_path: str | Path, default_dir: Path) -> Path:
    """Turn a bare name into a path inside ``default_dir``."""
    candidate = Path(name_or_path)
    if candidate.suffix in {".yaml", ".yml"}:
        if candidate.is_absolute() or candidate.exists():
            return candidate
        return default_dir / candidate
    return default_dir / f"{candidate}.yaml"


def available(kind: str) -> list[str]:
    """List config names of a given kind (``bands``, ``detector``, ...)."""
    directory = config_dir() / kind
    if not directory.is_dir():
        return []
    return sorted(p.stem for p in directory.glob("*.yaml"))


def load_all_detectors() -> dict[str, Detector]:
    """Load every detector config, keyed by its declared name."""
    detectors: dict[str, Detector] = {}
    for stem in available("detector"):
        detector = load_detector(stem)
        detectors[detector.name] = detector
    return detectors


def load_all_band_sets() -> dict[str, BandSet]:
    """Load every band set config, keyed by its declared name."""
    return {stem: load_band_set(stem) for stem in available("bands")}


@dataclass(frozen=True)
class StudyConfig:
    """Everything needed to evaluate candidate band sets.

    Bundled so a run records one object, and so later phases take a single
    argument rather than six.
    """

    band_sets: dict[str, BandSet]
    detectors: dict[str, Detector]
    windows: AtmosphericWindows
    indices: IndexCatalogue
    optics: Optics
    orbit: Orbit

    @property
    def placeholder_configs(self) -> dict[str, object]:
        """Named configs that may carry placeholder values."""
        named: dict[str, object] = {
            f"optics/{self.optics.name}": self.optics,
            f"orbit/{self.orbit.name}": self.orbit,
            f"atmospheric_windows/{self.windows.name}": self.windows,
        }
        for name, detector in self.detectors.items():
            named[f"detector/{name}"] = detector
        return named


def load_study_config(optics: str = "default", orbit: str = "default") -> StudyConfig:
    """Load the full configuration set."""
    return StudyConfig(
        band_sets=load_all_band_sets(),
        detectors=load_all_detectors(),
        windows=load_atmospheric_windows(),
        indices=load_index_catalogue(),
        optics=load_optics(optics),
        orbit=load_orbit(orbit),
    )
