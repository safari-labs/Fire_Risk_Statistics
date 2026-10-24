"""The per-phase experiment sheets: valid references, and in sync on disk."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from safari_bands.experiments import by_id
from safari_bands.phases import KINDS, PHASES, VERDICTS

REPO = Path(__file__).resolve().parent.parent


def _generator():
    spec = importlib.util.spec_from_file_location(
        "make_phase_docs", REPO / "scripts" / "make_phase_docs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_phase_ids_are_unique():
    ids = [p.pid for p in PHASES]
    assert len(set(ids)) == len(ids)


@pytest.mark.parametrize("phase", PHASES, ids=lambda p: p.pid)
def test_entries_are_well_formed(phase):
    refs = [e.ref for e in phase.entries]
    assert len(set(refs)) == len(refs)
    for e in phase.entries:
        assert e.kind in KINDS and e.verdict in VERDICTS
        assert e.result and e.conclusion
        if e.kind == "experiment":
            by_id(e.ref)           # raises if the register has no such entry
            assert not (e.question or e.independent or e.dependent), (
                f"{e.ref}: an experiment's hypothesis and variables come from "
                f"the register, never restated here")
        else:
            assert e.title and e.question and e.independent and e.dependent
            assert e.verdict in ("MEASURED", "PASS", "FIXED", "PENDING"), (
                f"{e.ref}: a {e.kind} has no registered hypothesis, so it cannot "
                f"be SUPPORTED or REFUTED")


@pytest.mark.parametrize("phase", PHASES, ids=lambda p: p.pid)
def test_sheet_is_on_disk_and_current(phase):
    folder = REPO / "docs" / "results" / phase.folder
    assert (folder / "experiments.png").exists(), (
        f"run python scripts/make_phase_docs.py --phase {phase.pid}")
    md = (folder / "experiments.md").read_text(encoding="utf-8")
    assert md == _generator().markdown(phase), (
        f"{phase.pid}'s experiments.md is stale: rerun make_phase_docs.py")
    assert (folder / phase.note).exists()
