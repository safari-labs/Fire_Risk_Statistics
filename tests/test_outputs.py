"""The register link (P11): every result has figures, and the consolidated views are current."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from safari_bands import outputs as O
from safari_bands.experiments import EXPERIMENTS, by_id
from safari_bands.phases import PHASES

REPO = Path(__file__).resolve().parent.parent


def _script(name):
    sys.path.insert(0, str(REPO / "scripts"))
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("x", O.with_results(), ids=lambda x: x.eid)
def test_an_experiment_with_a_result_has_a_figure(x):
    assert O.figures(x.eid), f"{x.eid} has a result but no PNG in {O.folders(x.eid)}"


@pytest.mark.parametrize("x", EXPERIMENTS, ids=lambda x: x.eid)
def test_a_folder_the_register_names_exists(x):
    for f in O.named_folders(x):
        assert (O.RESULTS / f).is_dir(), f"{x.eid}'s note names docs/results/{f}"


def test_latest_verdict_skips_pending():
    # E-63 went PENDING (P6b) then AT RISK (P6e)
    assert [v for _, _, v in O.phase_verdicts("E-63")][0] == "PENDING"
    assert O.latest_verdict("E-63") != "PENDING"
    assert O.latest_verdict("E-9") == ""


def test_value_map_rows_name_real_references():
    refs = {e.ref for p in PHASES for e in p.entries}
    for row in _script("make_value_map").ROWS:
        for r in row[5]:
            if r.startswith("E-"):
                by_id(r)
            else:
                assert r in refs, r


def test_value_map_resolves_from_the_saved_summaries():
    rows = _script("make_value_map").resolve()
    scored = [r for r in rows if r["est"]]
    assert scored, "no row found its summary"
    for r in scored:
        for k in ("within", "between"):
            e = r["est"][k]
            if e:
                assert e[1] <= e[0] <= e[2], (r["slot"], k, e)


def test_results_index_is_current():
    md = (O.RESULTS / "README.md").read_text(encoding="utf-8")
    assert md == _script("make_results_index").markdown(), (
        "docs/results/README.md is stale: run python scripts/make_results_index.py")
