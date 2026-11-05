"""Where each experiment's results are on disk (plan P11, the register link).

Derived, not typed in: an experiment's results are the folders of the phases
that report it (src/safari_bands/phases.py) plus any `docs/results/<folder>`
its register note names. Its figures are the PNGs in those folders. A
hand-kept `figures` field on each of 60 experiments would drift the first time
a phase was repackaged; this cannot.

tests/test_outputs.py fails when an experiment with a result has no figure, or
when a note names a folder that does not exist.
"""
from __future__ import annotations

import re
from pathlib import Path

from safari_bands.experiments import EXPERIMENTS, Experiment, by_id
from safari_bands.phases import PHASES

REPO = Path(__file__).resolve().parents[2]
RESULTS = REPO / "docs" / "results"

_NAMED = re.compile(r"docs/results/\s*([A-Za-z0-9_\-]+)")

#: Verdicts that say a result exists. PENDING says the opposite.
RESULT_VERDICTS = ("SUPPORTED", "REFUTED", "AT RISK", "MIXED", "PARTIAL", "MEASURED", "PASS",
                   "FIXED")


def phase_verdicts(eid: str) -> list[tuple[str, str, str]]:
    """(phase id, phase date, verdict) for every phase reporting *eid*, oldest first."""
    out = [(p.pid, p.date, e.verdict) for p in PHASES for e in p.entries if e.ref == eid]
    return sorted(out, key=lambda r: r[1])


def latest_verdict(eid: str) -> str:
    """The newest verdict that is not PENDING, else PENDING, else '' (never reported)."""
    v = phase_verdicts(eid)
    done = [r for r in v if r[2] != "PENDING"]
    return done[-1][2] if done else (v[-1][2] if v else "")


def named_folders(x: Experiment) -> list[str]:
    """Results folders the register note names, in the order named."""
    seen: list[str] = []
    for m in _NAMED.finditer(x.note):
        if m.group(1) != "figures" and m.group(1) not in seen:
            seen.append(m.group(1))
    return seen


def folders(eid: str) -> list[str]:
    """Every results folder for *eid*: its phases' folders, then those its note names."""
    x = by_id(eid)
    out: list[str] = []
    for p in sorted(PHASES, key=lambda p: p.date):
        if any(e.ref == eid for e in p.entries) and p.folder not in out:
            out.append(p.folder)
    out += [f for f in named_folders(x) if f not in out]
    return out


def figures(eid: str) -> list[Path]:
    """The PNGs in *eid*'s folders. Its own qualitative views come first."""
    own, rest = [], []
    for f in folders(eid):
        for p in sorted((RESULTS / f).glob("*.png")):
            if p.name.startswith("qual_"):
                (own if p.name.startswith(f"qual_{eid}_") else rest).append(p)
            elif p.name != "experiments.png":
                rest.append(p)
    return own + rest


def has_result(x: Experiment) -> bool:
    """A phase gave it a verdict, or the register says part of it ran."""
    return x.state == "PARTIAL" or latest_verdict(x.eid) in RESULT_VERDICTS


def with_results() -> list[Experiment]:
    return [x for x in EXPERIMENTS if has_result(x)]
