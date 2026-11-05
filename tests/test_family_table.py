"""Per-class fuel family results, for classes too rare to read in a mean."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def R():
    pytest.importorskip("matplotlib")
    path = ROOT / "scripts" / "make_results_package.py"
    spec = importlib.util.spec_from_file_location("make_results_package", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_recall_and_precision_read_the_label_on_the_rows(R):
    a = np.array([[8, 2], [1, 9]])
    rows = R.family_rows({0: a}, ("C", "D"))
    assert rows[0]["recall"] == pytest.approx(0.8)
    assert rows[0]["precision"] == pytest.approx(8 / 9)
    assert rows[1]["px"] == 10


def test_a_class_held_by_one_fold_says_so(R):
    a, b = np.array([[5, 5], [0, 10]]), np.array([[0, 0], [0, 10]])
    rows = R.family_rows({0: a, 1: b}, ("S", "D"))
    assert rows[0]["folds"] == 1
    assert rows[1]["folds"] == 2


def test_an_absent_class_has_no_row(R):
    rows = R.family_rows({0: np.array([[0, 0], [0, 4]])}, ("S", "D"))
    assert [r["family"] for r in rows] == ["D"]
