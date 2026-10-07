"""Cross-config checks that encode the study's methodological rules.

Pydantic validates each config in isolation. These functions check the things
that only make sense across configs -- a band against the detector it sits on,
a band against the atmosphere -- and they are where CLAUDE.md's rules become
executable rather than advisory.

Every check returns :class:`Finding` objects rather than raising, so a single
pass can report everything wrong with a configuration instead of stopping at
the first problem. :func:`raise_on_errors` turns findings into an exception
where fail-fast is wanted.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from safari_bands.config.schemas import (
    AtmosphericWindows,
    BandPurpose,
    BandSet,
    Detector,
)


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class Finding:
    """One validation result."""

    severity: Severity
    rule: str
    subject: str
    message: str

    def __str__(self) -> str:
        return f"[{self.severity.value.upper():7s}] {self.rule}: {self.subject} -- {self.message}"


class ValidationFailure(Exception):
    """Raised when findings contain at least one error."""

    def __init__(self, findings: list[Finding]) -> None:
        self.findings = findings
        errors = [f for f in findings if f.severity is Severity.ERROR]
        detail = "\n".join(f"  {f}" for f in errors)
        super().__init__(f"{len(errors)} configuration error(s):\n{detail}")


def check_atmospheric_windows(
    band_set: BandSet,
    windows: AtmosphericWindows,
) -> list[Finding]:
    """Methodological rule 7: respect atmospheric windows.

    Two thresholds, because a band's FWHM extent and its skirts are not the
    same kind of problem:

    * overlap within ``error_fwhm_multiplier`` (default 1.0, the nominal FWHM
      extent) is an ERROR -- the part of the response that carries the
      measurement sits in an absorption feature;
    * overlap only out in the skirts, within ``warn_fwhm_multiplier``, is a
      WARNING -- real but second-order, and separately accounted for by each
      band's ``out_of_band_leakage``.

    The distinction matters: Sentinel-2's own 1610 nm band has 90 nm FWHM, so
    a single aggressive skirt threshold would reject a band that demonstrably
    works in orbit.

    Bands declared ``purpose: atmospheric`` are exempt -- they exist to sense
    the atmosphere. The exemption is reported as INFO so it stays visible.

    SWIR bands outside the sanctioned windows produce a WARNING, not an error,
    so Phase 4's candidate grid can explore beyond them with the deviation
    on the record.
    """
    findings: list[Finding] = []
    error_mult = windows.error_fwhm_multiplier
    warn_mult = max(windows.warn_fwhm_multiplier, error_mult)

    for band in band_set.bands:
        core_low, core_high = band.edges_nm(error_mult)
        skirt_low, skirt_high = band.edges_nm(warn_mult)
        subject = f"{band_set.name}/{band.name} ({band.centre_nm:.0f} nm)"

        core_hits = [r for r in windows.forbidden_regions if r.overlaps(core_low, core_high)]
        skirt_hits = [
            r
            for r in windows.forbidden_regions
            if r.overlaps(skirt_low, skirt_high) and r not in core_hits
        ]

        if band.purpose is BandPurpose.ATMOSPHERIC:
            for region in core_hits + skirt_hits:
                findings.append(
                    Finding(
                        Severity.INFO,
                        "rule7_atmospheric_windows",
                        subject,
                        f"sits in {region.name} by design (purpose: atmospheric); "
                        "exempt from the forbidden-region check",
                    )
                )
            continue

        for region in core_hits:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "rule7_atmospheric_windows",
                    subject,
                    f"FWHM extent ({core_low:.0f}-{core_high:.0f} nm) overlaps forbidden "
                    f"region {region.name} {region.range_nm}. {region.reason.strip()}",
                )
            )

        for region in skirt_hits:
            findings.append(
                Finding(
                    Severity.WARNING,
                    "rule7_srf_skirt",
                    subject,
                    f"SRF skirt ({skirt_low:.0f}-{skirt_high:.0f} nm at {warn_mult:g}x FWHM) "
                    f"reaches into {region.name} {region.range_nm}; out-of-band rejection "
                    "needs to be specified with this in mind.",
                )
            )

        # Advisory: is a SWIR band inside one of the sanctioned windows?
        if band.centre_nm >= 1000.0 and not core_hits:
            in_window = any(
                w.range_nm[0] <= band.centre_nm <= w.range_nm[1]
                for w in windows.permitted_swir_windows
            )
            if not in_window:
                allowed = ", ".join(
                    f"{w.name} {w.range_nm}" for w in windows.permitted_swir_windows
                )
                findings.append(
                    Finding(
                        Severity.WARNING,
                        "rule7_permitted_swir_windows",
                        subject,
                        f"outside the sanctioned SWIR windows ({allowed}). "
                        "Allowed, but justify the placement in the results note.",
                    )
                )

    return findings


def check_detector_coverage(
    band_set: BandSet,
    detectors: dict[str, Detector],
) -> list[Finding]:
    """Check each band against the detector it is assigned to.

    This is what catches a configuration A/B/C mixup at load time rather than
    in the results: a ~2190 nm SWIR2 band cannot sit on standard InGaAs, whose
    response dies near 1.7 um. That single constraint is the reason
    configuration C needs extended-wavelength InGaAs, and it is the main
    cost/SWaP driver of the whole study.

    Bands with no detector assigned are skipped -- a reference band set
    describing someone else's sensor has no SAFARI detector.
    """
    findings: list[Finding] = []

    for band in band_set.bands:
        if band.detector is None:
            continue

        subject = f"{band_set.name}/{band.name} ({band.centre_nm:.0f} nm)"
        detector = detectors.get(band.detector)

        if detector is None:
            findings.append(
                Finding(
                    Severity.ERROR,
                    "detector_reference",
                    subject,
                    f"references unknown detector {band.detector!r}. "
                    f"Known: {', '.join(sorted(detectors)) or 'none'}",
                )
            )
            continue

        if not detector.covers(band.centre_nm):
            lo, hi = detector.spectral_range_nm
            findings.append(
                Finding(
                    Severity.ERROR,
                    "detector_spectral_range",
                    subject,
                    f"centre lies outside detector {detector.name!r} range "
                    f"({lo:.0f}-{hi:.0f} nm, {detector.technology}). "
                    "A band cannot sit on a detector that is blind to it.",
                )
            )
            continue

        # The band centre is covered but a skirt may fall off the edge, where
        # QE collapses and the effective SRF is no longer the nominal one.
        low, high = band.edges_nm(2.0)
        lo, hi = detector.spectral_range_nm
        if low < lo or high > hi:
            findings.append(
                Finding(
                    Severity.WARNING,
                    "detector_spectral_range",
                    subject,
                    f"SRF skirt ({low:.0f}-{high:.0f} nm at 2x FWHM) extends beyond "
                    f"detector {detector.name!r} range ({lo:.0f}-{hi:.0f} nm); "
                    "the effective SRF will be clipped by falling QE.",
                )
            )

    return findings


def check_placeholders(
    named_configs: dict[str, object],
) -> list[Finding]:
    """Report every config carrying placeholder values.

    Open questions Q2-Q6 (orbit, optics, detectors, filter architecture) are
    unanswered, so the study runs on labelled stand-ins. Surfacing them on
    every load is what stops a placeholder being quietly reported as a real
    hardware number. See docs/ASSUMPTIONS.md.
    """
    findings: list[Finding] = []
    for label, config in sorted(named_configs.items()):
        if getattr(config, "placeholder", False):
            source = getattr(config, "source", "") or "no source recorded"
            findings.append(
                Finding(
                    Severity.WARNING,
                    "placeholder_values",
                    label,
                    f"contains placeholder values -- {source}",
                )
            )
    return findings


def check_band_separation(band_set: BandSet, min_gap_fwhm: float = 1.0) -> list[Finding]:
    """Flag near-duplicate bands.

    The Kanyini study's importance rankings picked near-duplicate bands (VIIRS
    I2 and M7 share 846-885 nm), which is one of the failure modes this study
    is built to avoid. Bands whose centres are closer than ``min_gap_fwhm``
    times their mean FWHM have responses that overlap above half maximum, so
    they carry nearly the same information.

    The default of 1.0 is calibrated to pass real band sets: Sentinel-2's
    closest neighbours are B5/B6 (705 and 740 nm, 15 nm FWHM), which clear it
    comfortably.

    This is a WARNING, and deliberately so: the negative control band set is
    *supposed* to trip it.
    """
    findings: list[Finding] = []
    ordered = band_set.sorted_bands()

    for left, right in zip(ordered, ordered[1:], strict=False):
        gap = right.centre_nm - left.centre_nm
        mean_fwhm = 0.5 * (left.fwhm_nm + right.fwhm_nm)
        if gap < min_gap_fwhm * mean_fwhm:
            findings.append(
                Finding(
                    Severity.WARNING,
                    "near_duplicate_bands",
                    f"{band_set.name}/{left.name}+{right.name}",
                    f"centres {left.centre_nm:.0f} and {right.centre_nm:.0f} nm are "
                    f"{gap:.0f} nm apart, under {min_gap_fwhm:g}x the mean FWHM "
                    f"({mean_fwhm:.0f} nm); these bands are near-duplicates.",
                )
            )

    return findings


def validate_band_set(
    band_set: BandSet,
    windows: AtmosphericWindows,
    detectors: dict[str, Detector],
) -> list[Finding]:
    """Run every band-set check and return the combined findings."""
    return [
        *check_atmospheric_windows(band_set, windows),
        *check_detector_coverage(band_set, detectors),
        *check_band_separation(band_set),
    ]


def errors(findings: list[Finding]) -> list[Finding]:
    return [f for f in findings if f.severity is Severity.ERROR]


def raise_on_errors(findings: list[Finding]) -> None:
    """Raise :class:`ValidationFailure` if any finding is an error."""
    if errors(findings):
        raise ValidationFailure(findings)
