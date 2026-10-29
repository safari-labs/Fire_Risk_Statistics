"""The P6a-HS candidate grid (E-61, E-62) and its noise table.

The AVIRIS-NG band searches run in Fire_Risk_FW on Narval, which has no
checkout of this repo, so everything they need about a candidate band --
where it is, how wide, which detector it sits on, and its A-37 noise -- is
exported once from here as one JSON table (`safari-bands hs-grid --json`).
The table has the same "bands" layout as the `snr --json` export, so
Fire_Risk_FW's SensorNoise reads it unchanged.

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

    def ref_ids(ref):
        return [add(f"{b.centre_nm:g}/{b.fwhm_nm:g}{_suffix(det)}", b.centre_nm, b.fwhm_nm, det)
                for det, b in _bands_of(ref, detectors)]

    arms, fixed, k_max = {}, {}, {}
    for name, arm in grid["arms"].items():
        cands = arm_candidates(arm, detectors[arm["detector"]], windows, grid["step_nm"])
        if not cands:
            raise ValueError(f"arm {name} has no candidate")
        arms[name] = [add(c.cid, c.centre_nm, c.fwhm_nm, c.detector) for c in cands]
        fixed[name] = [i for ref in arm.get("fixed", []) for i in ref_ids(ref)]
        k_max[name] = int(arm["k_max"])
    refs = {ref: ref_ids(ref) for ref in grid.get("references", [])}
    return {"grid": grid["name"], "placeholder": placeholder,
            "model": "sigma(rho) = sqrt(rho / gain + var0 / gain^2) (A-37)",
            "rule7": f"{windows.name}, error multiplier {windows.error_fwhm_multiplier}",
            "bands": bands, "arms": arms, "fixed": fixed, "k_max": k_max,
            "references": refs, "role_windows_nm": grid["role_windows_nm"]}


def write_table(path: Path | str, table: dict, commit: str) -> None:
    import json

    Path(path).write_text(json.dumps({**table, "statistics_commit": commit}, indent=1),
                          encoding="utf-8")
