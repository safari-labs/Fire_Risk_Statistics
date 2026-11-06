"""The P6a-HS candidate grid (E-61, E-62) and its noise table.

The AVIRIS-NG band searches run in Fire_Risk_FW on Narval, which has no
checkout of this repo, so everything they need about a candidate band --
where it is, how wide, which detector it sits on, and its A-37 noise -- is
exported once from here as one JSON table (`safari-bands hs-grid --json`).
The table has the same "bands" layout as the `snr --json` export, so
Fire_Risk_FW's SensorNoise reads it unchanged.

REFERENCES AND FIXED SETS name a band set ('<set>' or '<set>/VNIR'), or are a
mapping (config/grids/p12_sensors.yaml, E-66):
    {name, vendor, list, include?, detector, rule7_exception?}  bands from a
        vendor catalogue (config/vendors/); forbidden bands are dropped unless
        rule7_exception records James's leave to score them as published;
    {name, range_nm, step_nm, fwhm_nm, detector}  a contiguous set (an HS mode).
Either may add `with: [ref, ...]`: those sets' bands first (MS block + SWIR filters).
A fixed set may also name a mapping reference by its name.

ARMS search a regular grid (range_nm, fwhm_nm, the grid's step_nm or the
arm's own), or an explicit vendor list: candidates: {vendor, list}.

WHAT KEEPS A CANDIDATE (config/grids/p6_hs.yaml, A-40):
    * its FWHM extent lies inside the arm's range and the detector's range;
    * it overlaps no forbidden region at the error multiplier (rule 7, the
      test `validate` applies to every band set);
    * for an arm with exclude_overlap_nm, its extent misses that interval.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from safari_bands.config.loader import (
    config_dir,
    load_atmospheric_windows,
    load_band_set,
    load_yaml,
)
from safari_bands.config.schemas import AtmosphericWindows, Band, Detector


@dataclass(frozen=True)
class Candidate:
    cid: str
    centre_nm: float
    fwhm_nm: float
    detector: str


def load_grid(name: str = "p6_hs") -> dict:
    return load_yaml(config_dir() / "grids" / f"{name}.yaml")


def _overlaps(lo: float, hi: float, a: float, b: float) -> bool:
    return lo < b and hi > a


def _suffix(detector: str) -> str:
    return {"silicon_cmos": "", "ingaas_std": "@std", "ingaas_ext": "@ext"}.get(
        detector, f"@{detector}")


def arm_candidates(arm: dict, detector: Detector, windows: AtmosphericWindows,
                   step_nm: float) -> list[Candidate]:
    lo, hi = arm["range_nm"]
    dlo, dhi = detector.spectral_range_nm
    excl = arm.get("exclude_overlap_nm")
    mult = windows.error_fwhm_multiplier
    out = []
    for c in np.arange(lo, hi + 1e-9, step_nm):
        for w in arm["fwhm_nm"]:
            a, b = c - 0.5 * w, c + 0.5 * w
            if a < max(lo, dlo) or b > min(hi, dhi):
                continue
            ea, eb = c - 0.5 * w * mult, c + 0.5 * w * mult
            if any(r.overlaps(ea, eb) for r in windows.forbidden_regions):
                continue
            if excl and _overlaps(a, b, *excl):
                continue
            out.append(Candidate(f"{c:g}/{w:g}{_suffix(arm['detector'])}", float(c),
                                 float(w), arm["detector"]))
    return out


def load_vendor(vendor: str) -> dict:
    return load_yaml(config_dir() / "vendors" / f"{vendor}.yaml")


def _vendor_list(spec: dict) -> list[dict]:
    """The band records of a vendor catalogue list, optionally a named subset."""
    v = load_vendor(spec["vendor"])[spec["list"]]
    rows = v.get("bands") or v.get("filters") or []
    want = spec.get("include")
    if want:
        missing = set(want) - {r["name"] for r in rows}
        if missing:
            raise ValueError(f"{spec['vendor']}/{spec['list']} has no band {sorted(missing)}")
        rows = [r for r in rows if r["name"] in want]
    return rows


def _clear(centre: float, fwhm: float, windows: AtmosphericWindows,
           detector: Detector | None = None) -> bool:
    """Rule 7 at the error multiplier, and inside the detector's range."""
    m = windows.error_fwhm_multiplier
    if any(r.overlaps(centre - 0.5 * fwhm * m, centre + 0.5 * fwhm * m)
           for r in windows.forbidden_regions):
        return False
    if detector is not None:
        lo, hi = detector.spectral_range_nm
        if centre - 0.5 * fwhm < lo or centre + 0.5 * fwhm > hi:
            return False
    return True


def vendor_candidates(arm: dict, detector: Detector,
                      windows: AtmosphericWindows) -> list[Candidate]:
    """An arm whose candidates are a vendor's filters, rule 7 and detector range applied."""
    return [Candidate(f"{r['centre_nm']:g}/{r['fwhm_nm']:g}{_suffix(arm['detector'])}",
                      float(r["centre_nm"]), float(r["fwhm_nm"]), arm["detector"])
            for r in _vendor_list(arm["candidates"])
            if _clear(r["centre_nm"], r["fwhm_nm"], windows, detector)]


def _bands_of(ref: str, detectors: dict[str, Detector]) -> list[tuple[str, Band]]:
    """'<set>' -> every band; '<set>/VNIR' or '<set>/SWIR' -> one chain."""
    from safari_bands.sensor import pick_detector

    name, _, chain = ref.partition("/")
    bs = load_band_set(name)
    out = []
    for b in bs.sorted_bands():
        det = b.detector or pick_detector(b.centre_nm, detectors)
        on_si = det == "silicon_cmos"
        if chain == "VNIR" and not on_si or chain == "SWIR" and on_si:
            continue
        out.append((det, b))
    return out


def build_table(grid: dict, detectors: dict[str, Detector], optics, orbit,
                windows: AtmosphericWindows | None = None) -> dict:
    """The exported table: bands (noise), arms, fixed sets, references, roles."""
    from safari_bands.sensor import noise_for

    windows = windows or load_atmospheric_windows()
    bands: dict[str, dict] = {}
    placeholder = bool(optics.placeholder or orbit.placeholder)

    def add(cid, centre, fwhm, det):
        nonlocal placeholder
        if cid in bands:
            return cid
        placeholder |= bool(detectors[det].placeholder)
        bn = noise_for(centre, fwhm, detectors, optics, orbit, detector=det)
        bands[cid] = {"centre_nm": centre, "fwhm_nm": fwhm, "detector": det,
                      "gain_e_per_rho": bn.gain_e_per_rho, "var0_e2": bn.var0_e2,
                      "saturates_at_rho": bn.saturates_at_rho}
        return cid

    named = {r["name"]: r for r in grid.get("references", []) if isinstance(r, dict)}
    exceptions: dict[str, str] = {}

    def spec_ids(spec: dict) -> list[str]:
        det = spec["detector"]
        if "vendor" in spec:
            rows = [(r["centre_nm"], r["fwhm_nm"]) for r in _vendor_list(spec)]
            if spec.get("rule7_exception"):
                kept = rows
                dropped = [r for r in rows if not _clear(*r, windows)]
                if dropped:
                    exceptions[spec["name"]] = spec["rule7_exception"]
            else:
                kept = [r for r in rows if _clear(*r, windows)]
        else:
            lo, hi = spec["range_nm"]
            w = float(spec["fwhm_nm"])
            kept = [(float(c), w) for c in np.arange(lo, hi + 1e-9, spec["step_nm"])
                    if _clear(float(c), w, windows)]
        base = [i for ref in spec.get("with", []) for i in ref_ids(ref)]
        return base + [add(f"{c:g}/{w:g}{_suffix(det)}", float(c), float(w), det)
                       for c, w in kept]

    def ref_ids(ref):
        if isinstance(ref, dict):
            return spec_ids(ref)
        if ref in named:
            return spec_ids(named[ref])
        return [add(f"{b.centre_nm:g}/{b.fwhm_nm:g}{_suffix(det)}", b.centre_nm, b.fwhm_nm, det)
                for det, b in _bands_of(ref, detectors)]

    arms, fixed, k_max = {}, {}, {}
    for name, arm in grid["arms"].items():
        det = detectors[arm["detector"]]
        cands = (vendor_candidates(arm, det, windows) if "candidates" in arm else
                 arm_candidates(arm, det, windows, arm.get("step_nm", grid["step_nm"])))
        if not cands:
            raise ValueError(f"arm {name} has no candidate")
        arms[name] = [add(c.cid, c.centre_nm, c.fwhm_nm, c.detector) for c in cands]
        fixed[name] = [i for ref in arm.get("fixed", []) for i in ref_ids(ref)]
        k_max[name] = int(arm["k_max"])
    refs = {(r["name"] if isinstance(r, dict) else r): ref_ids(r)
            for r in grid.get("references", [])}
    return {"grid": grid["name"], "placeholder": placeholder,
            "model": "sigma(rho) = sqrt(rho / gain + var0 / gain^2) (A-37)",
            "rule7": f"{windows.name}, error multiplier {windows.error_fwhm_multiplier}",
            "bands": bands, "arms": arms, "fixed": fixed, "k_max": k_max,
            "references": refs, "role_windows_nm": grid["role_windows_nm"],
            "rule7_exceptions": exceptions}


def write_table(path: Path | str, table: dict, commit: str) -> None:
    import json

    Path(path).write_text(json.dumps({**table, "statistics_commit": commit}, indent=1),
                          encoding="utf-8")
