"""The options table of a band sweep's report: cost is shown, never chooses."""
from __future__ import annotations

from safari_bands.band_options import Option, assess, chain_of, load_chains, markdown

VNIR = ["490/40", "560/35", "665/30", "705/20", "740/20", "865/30"]


def _opt(name, bands, skill, se=0.01, **kw):
    return Option(name, bands, skill, se, rmse=kw.pop("rmse", {"pc": 20.0}), **kw)


def _by(records):
    return {r["option"]: r for r in records}


def test_chain_follows_the_detector_tags():
    assert chain_of(VNIR) == "vnir"
    assert chain_of([*VNIR, "1610/90@std"]) == "std"
    assert chain_of([*VNIR, "1610/90@ext", "2190/180@ext"]) == "ext"
    assert chain_of(["1610/90@std", "2190/180@ext"]) == "std+ext"
    assert set(load_chains()["chains"]) >= {"vnir", "std", "ext", "std+ext"}


def test_the_costliest_option_can_rank_first():
    r = assess([_opt("cheap", VNIR, 0.40), _opt("dear", [*VNIR, "2190/180@ext"], 0.45)])
    assert r[0]["option"] == "dear" and r[0]["cost"] == "high"
    assert any("best combined score" in p for p in r[0]["pros"])
    assert any("main cost/SWaP driver" in c for c in r[0]["cons"])


def test_a_cheaper_option_is_not_dropped_for_scoring_lower():
    r = _by(assess([_opt("cheap", VNIR, 0.40), _opt("dear", [*VNIR, "2190/180@ext"], 0.45)]))
    assert r["cheap"]["dominated_by"] is None
    assert any("below the best" in c for c in r["cheap"]["cons"])


def test_an_option_beaten_at_no_extra_cost_leaves_the_table_but_not_the_records():
    recs = assess([_opt("a", VNIR, 0.45), _opt("b", VNIR, 0.40)])
    assert _by(recs)["b"]["dominated_by"] == "a"
    table = "\n".join(markdown(recs))
    assert "| **a** |" in table and "| b |" not in table and "1 useful options of 2" in table


def test_a_score_within_one_se_counts_as_tied():
    r = _by(assess([_opt("a", VNIR, 0.450, se=0.02),
                    _opt("b", [*VNIR, "1610/90@std"], 0.435)]))
    assert r["b"]["tied_with_best"] and r["b"]["dominated_by"] is None


def test_pros_and_cons_read_the_bands():
    r = _by(assess([_opt("swir", [*VNIR, "1610/90@std"], 0.45),
                    _opt("full", [*VNIR, "1610/90@ext", "2190/180@ext"], 0.44),
                    _opt("vnir", VNIR, 0.40)]))
    assert any("no SWIR1" in c for c in r["vnir"]["cons"])
    assert any("no SWIR2" in c for c in r["swir"]["cons"])
    assert any("SWIR2 present" in p for p in r["full"]["pros"])
    assert any("registration" in c for c in r["swir"]["cons"])
    assert not any("registration" in c for c in r["vnir"]["cons"])


def test_noise_sensitivity_and_stability_are_reported():
    r = assess([_opt("a", VNIR, 0.40, skill_clean=0.45, stable="unstable: searches disagree")])[0]
    assert any("sensitive to noise" in c for c in r["cons"])
    assert "unstable: searches disagree" in r["cons"]
