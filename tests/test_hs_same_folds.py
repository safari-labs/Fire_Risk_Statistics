"""make_results_package P6hs: arms that finished different folds are compared
only on folds they share."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def M():
    pytest.importorskip("matplotlib")
    spec = importlib.util.spec_from_file_location(
        "make_results_package", ROOT / "scripts" / "make_results_package.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run(folds: dict) -> SimpleNamespace:
    """A fake sweep: *folds* maps each arm to its folds; fold 1 is 0.1 harder."""
    arms = ("vnir", "vnir_no_red_edge", "swir_std", "swir_ext", "references")
    tasks = {a: [Path(f"f{f}s0") for f in folds.get(a, ())] for a in arms}

    def get(arm, name, **_):
        base = {"fixed_only": 0.3, "k4": 0.4, "k6": 0.5, "s2": 0.45}[name]
        return {(f, 0): base - 0.1 * (f == 1) for f in folds.get(arm, ())}

    def sets(arm):
        return {"vnir": ["k6"], "swir_std": ["fixed_only", "k4"], "swir_ext": ["fixed_only", "k4"],
                "references": ["s2"]}.get(arm, ["k6"])

    return SimpleNamespace(tasks=tasks, get=get, sets=sets)


def test_every_arm_on_every_fold_needs_no_split(M):
    all_ = {a: (0, 1) for a in ("vnir", "vnir_no_red_edge", "swir_std", "swir_ext", "references")}
    assert M.p6hs_fold_sets(_run(all_)) == []


def test_fold_sets_follow_what_finished(M):
    H = _run({"vnir": (0,), "swir_ext": (1,), "swir_std": (0, 1), "references": (0, 1)})
    assert [sorted(f) for f in M.p6hs_fold_sets(H)] == [[0], [1]]


def test_a_set_is_scored_only_on_the_shared_folds(M):
    H = _run({"vnir": (0,), "swir_ext": (1,), "swir_std": (0, 1), "references": (0, 1)})
    rows = {r["label"]: r for r in M.p6hs_same_folds(H, frozenset({1}))}
    assert not any(k.startswith("VNIR camera alone") for k in rows)     # no fold 1
    fixed = rows["Fixed VNIR"]
    assert fixed["score"] == pytest.approx(0.2)                         # not the all-fold 0.25
    assert rows["reference: s2"]["gain"] == pytest.approx(0.15)
    assert fixed["runs"] == 1


def test_stability_breaks_a_tie_the_same_way_every_build(M):
    """Two bands chosen equally often: set order follows the string hash, which
    Python seeds per process, so the option table changed between builds."""
    H = SimpleNamespace(paths={("swir_std", 0, 0): {"steps": [{"added": "1690/20@std"}]},
                               ("swir_std", 0, 1): {"steps": [{"added": "1680/20@std"}]}})
    picks, _ = M._hs_stability(H, "swir_std", 1)
    assert picks == ["1680/20@std"]
