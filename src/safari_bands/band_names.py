"""Display labels for Sentinel-2 band IDs in figures: "B5 (Red edge 1)".

Each band's role comes from the band-set YAMLs, not from code (CLAUDE.md:
no hard-coded band definitions). Only role -> display name lives here,
which is wording, not an instrument parameter.

The 11-band candidate set is read first because it mirrors
Fire_Risk_Model's src/data/bands.py, which builds the packed data. The
Sentinel-2 benchmark set only fills in bands the candidates lack (B12).
The two disagree on purpose about B8A: the benchmark uses it as its NIR,
while the candidates carry both B8 (NIR) and B8A (narrow NIR).
"""
from __future__ import annotations

from functools import cache

#: Role -> short display name. Fire_Risk_FW's fire_risk_fw.band_names holds
#: the same table; tests in both repos check it against the band roles.
ROLE_NAMES: dict[str, str] = {
    "COASTAL": "Coastal",
    "BLUE": "Blue",
    "GREEN": "Green",
    "RED": "Red",
    "RED_EDGE1": "Red edge 1",
    "RED_EDGE2": "Red edge 2",
    "RED_EDGE3": "Red edge 3",
    "NIR": "NIR",
    "NIR_NARROW": "Narrow NIR",
    "WATER_VAPOUR": "Water vapour",
    "CIRRUS": "Cirrus",
    "SWIR1": "SWIR 1",
    "SWIR2": "SWIR 2",
}

#: Read in order; the first set to name a band decides its role.
ROLE_SOURCES = ("sentinel2_11band_candidates", "sentinel2_msi")


@cache
def s2_roles() -> dict[str, str]:
    """Sentinel-2 band ID -> role, from the band-set YAMLs."""
    from safari_bands.config.loader import load_band_set

    roles: dict[str, str] = {}
    for name in ROLE_SOURCES:
        for band in load_band_set(name).bands:
            roles.setdefault(band.name, band.role)
    return roles


def band_name(band: str) -> str | None:
    """"Red edge 1" for "B5"; None for anything that is not a known band."""
    role = s2_roles().get(band)
    return ROLE_NAMES.get(role) if role else None


def band_label(band: str, sep: str = " ") -> str:
    """"B5 (Red edge 1)", or with sep="\\n" a two-line label. Anything
    unrecognised comes back unchanged."""
    name = band_name(band)
    return f"{band}{sep}({name})" if name else band
