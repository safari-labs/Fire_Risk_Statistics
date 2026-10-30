"""The options table of a band sweep's report (James, 2026-10-30, A-41).

Bands are chosen on retrieval performance, disregarding cost; the choice is
James's, so a report lists every useful option with its cost and its pros and
cons rather than a single winner. Everything here comes from measured scores
and the band list. Cost is qualitative (config/cost/chains.yaml, Q6 open).

An option is useful unless another scores clearly better (beyond one standard
error) at no higher cost class and with no more bands. Dominated options stay in
the CSV, marked, and leave the table.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
COST_ORDER = {"low": 0, "moderate": 1, "high": 2}
TARGET_LABELS = {"pc": "percent conifer", "closure": "closure", "height": "height"}
#: Bands the ancillary needs read (brief section 3): SWIR1 for cloud/snow, ~2.1
#: um for dark-target aerosol.
SWIR1_NM, SWIR2_NM = (1550.0, 1750.0), (2080.0, 2350.0)
#: Sentinel-2 centres the brief asks to match where it costs little.
S2_CENTRES = (490, 560, 665, 705, 740, 865, 1610, 2190)
#: A noise-free score this far above the noisy one means SNR is limiting.
NOISE_GAP = 0.02


@dataclass
class Option:
    name: str
    bands: list[str]
    skill: float            # combined skill, with sensor noise (rule 6)
    se: float
    rmse: dict[str, float] = field(default_factory=dict)
    skill_clean: float | None = None
    stable: str = ""        # how far the searches agree, for a searched set


def load_chains(path: Path = ROOT / "config" / "cost" / "chains.yaml") -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def centre(band: str) -> float:
    return float(band.split("@")[0].split("/")[0])


def chain_of(bands: list[str]) -> str:
    kinds = {b.split("@")[1] for b in bands if "@" in b}
    return "vnir" if not kinds else "+".join(k for k in ("std", "ext") if k in kinds)


def _has(bands, window) -> bool:
    return any(window[0] <= centre(b) <= window[1] for b in bands)


def _s2_matches(bands) -> int:
    return sum(any(abs(centre(b) - c) <= 10 for b in bands) for c in S2_CENTRES)


def assess(options: list[Option], chains: dict | None = None) -> list[dict]:
    """One record per option, best first: status, cost, pros and cons."""
    chains = (chains or load_chains())["chains"]
    best = max(options, key=lambda o: o.skill)
    tol = best.se
    best_rmse = {t: min(o.rmse[t] for o in options if t in o.rmse)
                 for t in {t for o in options for t in o.rmse}}
    out = []
    for o in sorted(options, key=lambda o: -o.skill):
        c = chains[chain_of(o.bands)]
        tied = best.skill - o.skill <= tol
        pros, cons = [], []
        if o is best:
            pros.append("best combined score")
        elif tied:
            pros.append(f"tied with the best (within one SE, {tol:.3f})")
        else:
            cons.append(f"{best.skill - o.skill:.3f} below the best combined score")
        lead = [TARGET_LABELS.get(t, t) for t, v in o.rmse.items() if v == best_rmse[t]]
        if lead:
            pros.append("lowest error on " + ", ".join(lead))
        pros.append(f"{c['cost']} cost: {c['note']}" if c["cost"] == "low" else "")
        if c["cost"] != "low":
            cons.append(f"{c['cost']} cost: {c['note']}")
        if chain_of(o.bands) != "vnir":
            cons.append("VNIR and SWIR are separate chains: band-to-band registration risk")
        if _has(o.bands, SWIR1_NM):
            pros.append("SWIR1 present: cloud/snow discrimination, and the contrast SWIR "
                        "moisture metrics use")
        else:
            cons.append("no SWIR1: weak cloud/snow discrimination (brief section 3)")
        if _has(o.bands, SWIR2_NM):
            pros.append("SWIR2 present: cellulose/lignin sensitivity, dark-target aerosol")
        elif chain_of(o.bands) != "vnir":
            cons.append("no SWIR2: no dark-target aerosol pairing, weak dry-matter leverage")
        s2 = _s2_matches(o.bands)
        if s2 >= 4:
            pros.append(f"{s2} of 8 Sentinel-2 centres matched: cross-calibration, S2 archive")
        if o.skill_clean is not None and o.skill_clean - o.skill > NOISE_GAP:
            cons.append(f"sensitive to noise: {o.skill_clean - o.skill:.3f} better noise-free, "
                        "so its SNR requirement is tighter")
        if o.stable:
            (pros if o.stable.startswith("stable") else cons).append(o.stable)
        out.append({"option": o.name, "bands": o.bands, "n_bands": len(o.bands),
                    "chain": c["label"], "cost": c["cost"], "skill": o.skill, "se": o.se,
                    "rmse": o.rmse, "tied_with_best": tied,
                    "pros": [p for p in pros if p], "cons": cons, "dominated_by": None})
    for r in out:
        for b in out:
            if (b["skill"] - r["skill"] > b["se"] and b["n_bands"] <= r["n_bands"]
                    and COST_ORDER[b["cost"]] <= COST_ORDER[r["cost"]]):
                r["dominated_by"] = b["option"]
                break
    return out


def markdown(records: list[dict], placeholder: bool = True) -> list[str]:
    """The report's section: every useful option, with cost, pros and cons."""
    keep = [r for r in records if not r["dominated_by"]]
    targets = sorted({t for r in keep for t in r["rmse"]})
    L = [f"{len(keep)} useful options of {len(records)} scored; the rest are beaten by an option "
         "that costs no more and has no more bands (all are in `T_options.csv`). Bands are "
         "chosen on performance; cost is shown for information only (A-41)."]
    if placeholder:
        L.append("Cost is qualitative: Q6 is open, so there are no figures yet.")
    L += ["", "| option | bands | score ± SE | "
          + " | ".join(f"RMSE {TARGET_LABELS.get(t, t)}" for t in targets)
          + " | chain | cost | pros | cons |",
          "|---|---|---|" + "---|" * len(targets) + "---|---|---|---|"]
    for r in keep:
        name = f"**{r['option']}**" if r["tied_with_best"] else r["option"]
        L.append(f"| {name} | {', '.join(r['bands'])} | {r['skill']:.3f} ± {r['se']:.3f} | "
                 + " | ".join(f"{r['rmse'][t]:.2f}" if t in r["rmse"] else "" for t in targets)
                 + f" | {r['chain']} | {r['cost']} | {'; '.join(r['pros'])} | "
                 f"{'; '.join(r['cons'])} |")
    return L
