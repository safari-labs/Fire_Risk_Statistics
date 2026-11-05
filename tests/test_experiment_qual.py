"""Every experiment with a result has a qualitative view, or says why not."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

from safari_bands.phases import PHASES

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def Q():
    pytest.importorskip("matplotlib")
    path = ROOT / "scripts" / "make_experiment_qual.py"
    spec = importlib.util.spec_from_file_location("make_experiment_qual", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["make_experiment_qual"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_every_experiment_with_a_phase_entry_is_listed(Q):
    listed = {(eid, folder) for eid, folder, _, _ in Q.QUAL}
    missing = [(e.ref, p.folder) for p in PHASES for e in p.entries
               if e.kind == "experiment" and e.verdict != "PENDING"
               and (e.ref, p.folder) not in listed
               # the same experiment read again in a later phase keeps its one view
               and not any(eid == e.ref for eid, _ in listed)]
    assert missing == []


def test_listed_files_exist_and_a_none_gives_its_reason(Q):
    for eid, folder, kind, what in Q.QUAL:
        if kind == "none":
            assert isinstance(what, str) and len(what) > 20, eid
        else:
            for f in what:
                assert (Q.RESULTS / folder / f).exists(), (eid, f)


def test_results_scripts_never_redefine_a_top_level_name():
    """make_experiment_qual calls make_results_package helpers by name, so a
    second definition silently changes what older figures draw."""
    import ast
    for name in ("make_results_package.py", "make_experiment_qual.py"):
        tree = ast.parse((ROOT / "scripts" / name).read_text(encoding="utf-8"))
        defs = [n.name for n in tree.body
                if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
        assert len(defs) == len(set(defs)), name


def test_every_built_view_is_listed(Q):
    assert set(Q.BUILD) | set(Q.HS_SETS) <= {q[0] for q in Q.QUAL}


def test_strip_grid_follows_a_rotated_line(Q):
    t = np.linspace(0, 1, 2000)
    lon = -110 + t * 2 + np.random.default_rng(0).normal(0, 0.002, 2000)
    lat = 55 + t
    r, c = Q.strip_grid(Q.strip_axes(lon, lat), lon, lat, height=100, width=10)
    assert abs(np.corrcoef(r, t)[0, 1]) > 0.99          # along track
    assert abs(np.corrcoef(c, t)[0, 1]) < 0.2           # across track
    assert r.max() == 99 and c.max() <= 9


def test_strays_do_not_squeeze_a_filtered_line(Q):
    t = np.linspace(0, 1, 2000)
    lon = -110 + t * 0.2 + np.random.default_rng(0).normal(0, 0.002, 2000)
    lat = 55 + t * 0.1
    lon, lat = np.r_[lon, -100.0, -100.1], np.r_[lat, 60.0, 60.1]       # two far strays
    r, _ = Q.strip_grid(Q.strip_axes(lon, lat), lon, lat, height=100, width=10)
    assert np.ptp(r[:2000]) > 90                        # the real pixels still fill the strip


def test_every_panel_of_a_line_shares_its_bins(Q):
    t = np.linspace(0, 1, 500)
    lon, lat = -110 + t, 55 + t * 0.5 + np.random.default_rng(0).normal(0, 0.003, 500)
    axes = Q.strip_axes(lon, lat)
    order = np.random.default_rng(1).permutation(500)
    r, c = Q.strip_grid(axes, lon, lat)
    r2, c2 = Q.strip_grid(axes, lon[order], lat[order])
    assert (r[order] == r2).all() and (c[order] == c2).all()


def test_strip_bins_average_and_vote(Q):
    r, c = np.array([0, 0, 0, 1]), np.array([0, 0, 0, 1])
    mean = Q.strip_mean(r, c, np.array([1.0, 2.0, 3.0, 8.0]), (2, 2))
    assert mean[0, 0] == 2 and mean[1, 1] == 8 and np.isnan(mean[0, 1])
    mode = Q.strip_mode(r, c, np.array([2, 2, 1, 0]), (2, 2), 3)
    assert mode[0, 0] == 2 and mode[1, 1] == 0 and np.isnan(mode[1, 0])


def test_symmetric_scale_is_never_zero(Q):
    assert Q._symmetric_max(np.zeros(4)) == 1.0
    assert Q._symmetric_max(np.array([-3.0, 1.0])) > 0


def test_every_phase_has_a_qualitative_figure(Q):
    """Each phase folder gets at least one picture, not only a reason (P11)."""
    drawn = {folder for _, folder, kind, what in Q.QUAL if kind != "none" and what}
    assert [p.pid for p in PHASES if p.folder not in drawn] == []


def test_a_phase_entry_can_name_a_view(Q):
    assert Q._ref_name("P0-3") == "SCANFI time step on burned ground"
    assert Q._ref_name("E-41")
