"""Pydantic schemas for every configuration object in the study.

Methodological rule: no hard-coded band definitions or instrument parameters in
code. These classes define the *shape* of a configuration; the values always
come from YAML under ``config/``.

Units follow the project convention: wavelength in nm, reflectance 0-1,
radiance in W m-2 sr-1 um-1, Cw and Cm in g cm-2, LFMC in %.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Bounds of the PROSPECT/4SAIL domain the study works in.
SPECTRAL_DOMAIN_NM: tuple[float, float] = (400.0, 2500.0)


class StrictModel(BaseModel):
    """Base model that rejects unknown keys.

    A typo in a YAML key should fail loudly rather than be silently dropped and
    leave a default in place of an intended value.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)


class SRFShape(StrEnum):
    """Shape of the spectral response function."""

    GAUSSIAN = "gaussian"
    TOPHAT = "tophat"
    TABULATED = "tabulated"


class BandPurpose(StrEnum):
    """What a band is for.

    Bands with purpose ``atmospheric`` are exempt from the forbidden-region
    check in :mod:`safari_bands.config.validators`, because they exist
    precisely to sense the atmosphere (e.g. a 1375 nm cirrus band sitting
    inside the 1400 nm water vapour absorption).
    """

    SURFACE = "surface"
    ATMOSPHERIC = "atmospheric"


class Band(StrictModel):
    """One spectral band."""

    name: str
    role: str = Field(
        description=(
            "Role token used by the index catalogue, e.g. NIR, SWIR1, SWIR_1240. "
            "Indices are defined over roles so one definition resolves against "
            "any band set."
        )
    )
    centre_nm: float = Field(gt=0.0)
    fwhm_nm: float = Field(gt=0.0)
    srf_shape: SRFShape = SRFShape.GAUSSIAN
    srf_file: str | None = Field(
        default=None,
        description="Path to a tabulated SRF, required when srf_shape is 'tabulated'.",
    )
    out_of_band_leakage: float = Field(default=0.0, ge=0.0, le=1.0)
    detector: str | None = Field(
        default=None,
        description=(
            "Name of the detector config this band sits on. Optional: a reference "
            "band set describing someone else's sensor has no SAFARI detector."
        ),
    )
    purpose: BandPurpose = BandPurpose.SURFACE

    @field_validator("centre_nm")
    @classmethod
    def _centre_within_domain(cls, v: float) -> float:
        lo, hi = SPECTRAL_DOMAIN_NM
        if not lo <= v <= hi:
            raise ValueError(
                f"centre_nm {v} is outside the {lo}-{hi} nm domain the forward model covers"
            )
        return v

    @model_validator(mode="after")
    def _tabulated_needs_file(self) -> Band:
        if self.srf_shape is SRFShape.TABULATED and not self.srf_file:
            raise ValueError(f"band {self.name!r}: srf_shape 'tabulated' requires srf_file")
        return self

    def edges_nm(self, fwhm_multiplier: float = 1.0) -> tuple[float, float]:
        """Return the band's spectral extent.

        ``fwhm_multiplier`` widens the interval to account for SRF skirts; a
        multiplier of 3 covers roughly +/- 1.5 FWHM either side of centre.
        """
        half_width = 0.5 * self.fwhm_nm * fwhm_multiplier
        return (self.centre_nm - half_width, self.centre_nm + half_width)


class BandSet(StrictModel):
    """A candidate or reference set of bands."""

    name: str
    description: str = ""
    role_in_study: str = Field(
        default="candidate",
        description="candidate, positive_benchmark, negative_control or heritage.",
    )
    swir_content: str = ""
    detector_class: str = ""
    bands: list[Band] = Field(min_length=1)

    @model_validator(mode="after")
    def _names_and_roles_unique(self) -> BandSet:
        for attr in ("name", "role"):
            seen: set[str] = set()
            for band in self.bands:
                value = getattr(band, attr)
                if value in seen:
                    raise ValueError(
                        f"band set {self.name!r}: duplicate band {attr} {value!r}. "
                        "Two bands sharing a role make the index catalogue ambiguous."
                    )
                seen.add(value)
        return self

    @property
    def roles(self) -> set[str]:
        return {band.role for band in self.bands}

    def by_role(self, role: str) -> Band | None:
        for band in self.bands:
            if band.role == role:
                return band
        return None

    def sorted_bands(self) -> list[Band]:
        return sorted(self.bands, key=lambda b: b.centre_nm)


class PlaceholderMixin(BaseModel):
    """Marks a config whose values are stand-ins.

    Many instrument parameters are unanswered open questions (Q2-Q6). Rather
    than block, the study runs on labelled placeholders. This flag propagates
    into run provenance so a results note cannot silently present a placeholder
    as a real hardware number.
    """

    placeholder: bool = False
    source: str = ""


class QECurve(StrictModel):
    """Tabulated quantum efficiency, linearly interpolated between points."""

    wavelength_nm: list[float] = Field(min_length=2)
    qe: list[float] = Field(min_length=2)

    @model_validator(mode="after")
    def _consistent_and_sorted(self) -> QECurve:
        if len(self.wavelength_nm) != len(self.qe):
            raise ValueError("qe_curve: wavelength_nm and qe must have the same length")
        if any(b <= a for a, b in zip(self.wavelength_nm, self.wavelength_nm[1:], strict=False)):
            raise ValueError("qe_curve: wavelength_nm must be strictly increasing")
        if any(not 0.0 <= q <= 1.0 for q in self.qe):
            raise ValueError("qe_curve: qe values must lie in 0-1")
        return self


class DarkCurrent(StrictModel):
    """Dark current that doubles every ``doubling_temperature_k`` above reference."""

    reference_temperature_k: float = Field(gt=0.0)
    reference_e_per_s: float = Field(ge=0.0)
    doubling_temperature_k: float = Field(gt=0.0)

    def at_temperature(self, temperature_k: float) -> float:
        """Dark current in e-/s at ``temperature_k``."""
        exponent = (temperature_k - self.reference_temperature_k) / self.doubling_temperature_k
        return self.reference_e_per_s * 2.0**exponent


class Detector(StrictModel, PlaceholderMixin):
    """Detector model. Phase 2 turns this into a per-band SNR."""

    name: str
    technology: str
    spectral_range_nm: tuple[float, float]
    qe_curve: QECurve
    dark_current: DarkCurrent
    read_noise_e: float = Field(ge=0.0)
    full_well_e: float = Field(gt=0.0)
    pixel_pitch_um: float = Field(gt=0.0)
    operating_temperature_k: float = Field(gt=0.0)
    tec_cooled: bool = False
    tec_stages: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def _range_ordered(self) -> Detector:
        lo, hi = self.spectral_range_nm
        if lo >= hi:
            raise ValueError(f"detector {self.name!r}: spectral_range_nm must be [low, high]")
        return self

    def covers(self, wavelength_nm: float) -> bool:
        lo, hi = self.spectral_range_nm
        return lo <= wavelength_nm <= hi


class Optics(StrictModel, PlaceholderMixin):
    """Telescope and foreoptics."""

    name: str
    aperture_diameter_mm: float = Field(gt=0.0)
    focal_length_mm: float = Field(gt=0.0)
    f_number: float = Field(gt=0.0)
    transmission: float = Field(gt=0.0, le=1.0)
    filter_architecture: str = ""
    separate_vnir_swir_chains: bool = True


class Orbit(StrictModel, PlaceholderMixin):
    """Orbit and sampling geometry."""

    name: str
    altitude_km: float = Field(gt=0.0)
    orbit_type: str = "sun_synchronous"
    local_solar_overpass_time: str = ""
    gsd_m: float = Field(gt=0.0)
    swath_km: float = Field(gt=0.0)
    integration_time_ms: float = Field(gt=0.0)
    tdi_stages: int = Field(default=1, ge=1)
    target_latitude_range_deg: tuple[float, float] = (45.0, 60.0)


class SpectralRegion(StrictModel):
    """A named wavelength interval with a stated reason."""

    name: str
    range_nm: tuple[float, float]
    reason: str = ""
    note: str = ""

    @model_validator(mode="after")
    def _range_ordered(self) -> SpectralRegion:
        lo, hi = self.range_nm
        if lo >= hi:
            raise ValueError(f"region {self.name!r}: range_nm must be [low, high]")
        return self

    def overlaps(self, low_nm: float, high_nm: float) -> bool:
        lo, hi = self.range_nm
        return low_nm < hi and high_nm > lo


class AtmosphericWindows(StrictModel, PlaceholderMixin):
    """Machine-readable form of methodological rule 7."""

    name: str
    #: Overlap within this multiple of the FWHM is an error. 1.0 is the band's
    #: nominal FWHM extent -- the part of the response that actually carries
    #: the measurement.
    error_fwhm_multiplier: float = Field(default=1.0, gt=0.0)
    #: Overlap only out in the SRF skirts is a warning. Out-of-band response is
    #: separately accounted for by each band's out_of_band_leakage.
    warn_fwhm_multiplier: float = Field(default=2.0, gt=0.0)
    forbidden_regions: list[SpectralRegion] = Field(default_factory=list)
    permitted_swir_windows: list[SpectralRegion] = Field(default_factory=list)
    atmospheric_purpose_exemptions: list[SpectralRegion] = Field(default_factory=list)


class IndexDef(StrictModel):
    """One vegetation index, defined over band roles rather than wavelengths.

    Phase 0 does not evaluate ``formula``; it is documentation and a
    forward-compatible field. ``requires_roles`` is what drives the feasibility
    matrix.
    """

    name: str
    aliases: list[str] = Field(default_factory=list)
    long_name: str = ""
    target: str = ""
    family: str = ""
    requires_roles: list[str] = Field(min_length=1)
    formula: str
    hyperspectral_only: bool = False
    notes: str = ""


class IndexCatalogue(StrictModel):
    """The reference index catalogue.

    Indices are baselines and interpretability aids only. Rule 3 forbids using
    index thresholds as retrieval labels, and rule 4 requires band sets to be
    judged by training the provisional retrieval model on them.
    """

    name: str
    indices: list[IndexDef] = Field(min_length=1)

    @model_validator(mode="after")
    def _names_unique(self) -> IndexCatalogue:
        seen: set[str] = set()
        for index in self.indices:
            if index.name in seen:
                raise ValueError(f"duplicate index name {index.name!r}")
            seen.add(index.name)
        return self

    def by_name(self, name: str) -> IndexDef | None:
        for index in self.indices:
            if index.name == name or name in index.aliases:
                return index
        return None
