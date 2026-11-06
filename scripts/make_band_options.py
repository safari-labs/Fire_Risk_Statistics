"""scripts/make_band_options.py

E-46, P12's first decision: band options for James to choose from (A-49).

Sentinel-2 (eco_v3) decides the VNIR bands and whether SWIR is in; AVIRIS-NG
(hs_v4) decides where the SWIR bands sit. Every search runs inside a training
fold, so 15 searches (5 outer folds x 3 seeds) return 15 sets per k. Q38
(option 1, James 2026-11-05): count them by region, take the consensus set,
and re-score that exact set on the same folds, so the set that would fly is
the set that was scored.

    python scripts/make_band_options.py                      # consensus + provisional
    python scripts/make_band_options.py \\
        --eco-rescore narval_results/bands_consensus \\
        --hs-rescore narval_results/hs_consensus/<run>          # with the re-scores

Regions. Sentinel-2: the band's role in config/bands (RED_EDGE1-3 -> red edge,
NIR_NARROW -> NIR). AVIRIS-NG SWIR: 50 nm bins, as the hs packager counts them;
A-40's role windows leave out 1000-1550 and 1750-2080 nm, where searched SWIR
bands do land.

Writes docs/results/p12_bands/: T_consensus.csv, T_options_s2.csv,
T_options_swir.csv, consensus.png, skill.png, summary.json, options.md and
rescore_commands.md; and the re-score grid
Fire_Risk_FW/configs/noise/p12_consensus_grid.json.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

import numpy as np

from safari_bands.band_options import COST_ORDER, Option, assess, consensus
from safari_bands.config.loader import load_all_detectors, load_band_set, project_root

ROOT = project_root()
FW = ROOT.parent / "Fire_Risk_FW"
ECO = ROOT / "narval_results" / "eco_v3" / "20261102-1959"
HS = ROOT / "narval_results" / "hs_v4" / "20261102-1959"
HS_GRID = FW / "configs" / "noise" / "p6_hs_grid_placeholder.json"
OUT_GRID = FW / "configs" / "noise" / "p12_consensus_grid.json"
MODE = "raw+indices"
HEADS = ("pc", "closure", "height", "family")          # A-49: equal weights
PATHS = ("combined", "pc", "closure", "height", "family")
SWIR_ARMS = ("swir_std", "swir_ext")
RESCORE_SIZE = "8x2"                                    # the size bands were ranked with
BIN_NM = 50

FIG_BG, AX_BG = "#0f1117", "#1a1d27"
SPINE, INK, INK_BRIGHT, MUTED = "#333344", "#cccccc", "#eeeeee", "#8b8b9a"
BLUE, ORANGE = "#3987e5", "#d95926"


# ---------------------------------------------------------------- names
def s2_bands():
    bs = load_band_set("sentinel2_p6_12band")
    return [b.name for b in bs.bands], {b.name: b for b in bs.bands}


def s2_region(role: str) -> str:
    """Q38's regions: the three red-edge bands are one region, B8 and B8A are
    NIR; SWIR1 and SWIR2 stay apart (different detectors)."""
    role = re.sub(r"^RED_EDGE\d$", "RED_EDGE", role).replace("NIR_NARROW", "NIR")
    return role.lower().replace("_", " ")


def option_name(band) -> str:
    """band_options' naming: centre, with @std / @ext off the silicon chain."""
    det = load_all_detectors()
    c = band.centre_nm
    if det["silicon_cmos"].spectral_range_nm[0] <= c <= det["silicon_cmos"].spectral_range_nm[1]:
        return f"{c:g}"
    for name, tag in (("ingaas_std", "std"), ("ingaas_ext", "ext")):
        lo, hi = det[name].spectral_range_nm
        if lo <= c <= hi:
            return f"{c:g}@{tag}"
    raise ValueError(f"no detector covers {band.name} at {c} nm")


def hs_centre(band_id: str) -> float:
    return float(band_id.split("/")[0])


def hs_region(band_id: str) -> str:
    return f"{round(hs_centre(band_id) / BIN_NM) * BIN_NM} nm"


# ---------------------------------------------------------------- loading
TASK = re.compile(r"^f(\d+)s(\d+)$")


def _task(name: str) -> tuple[int, int] | None:
    m = TASK.match(name)
    return (int(m[1]), int(m[2])) if m else None


def load_eco(run: Path) -> dict:
    """{'paths': {path: {k: {task: (value, bands)}}}, 'all': {task: value}}."""
    out = {"paths": {}, "all": {}}
    for d in sorted(run.glob("f*s*")):
        ev = d / "eval.jsonl"
        t = _task(d.name)
        if t is None or not ev.exists():
            continue
        for line in ev.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r["mode"] != MODE or not r["noisy"] or r["metrics"] is None:
                continue
            v = float(np.mean([r["metrics"][f"skill_{h}"] for h in HEADS]))
            if r["selector"] == "all_bands":
                out["all"][t] = v
            elif r["selector"] in PATHS:
                out["paths"].setdefault(r["selector"], {}).setdefault(r["k"], {})[t] = \
                    (v, list(r["bands"]))
    return out


def load_hs(run: Path) -> dict:
    """{'sets': {(arm, set): {task: (value, bands)}}, 'paths': {arm: {task: steps}}}."""
    out = {"sets": {}, "paths": {}}
    for arm_dir in sorted(p for p in run.iterdir() if p.is_dir() and not p.name.startswith("_")):
        for d in sorted(arm_dir.glob("f*s*")):
            t = _task(d.name)
            if t is None:
                continue
            ev = d / "eval.jsonl"
            if ev.exists():
                for line in ev.read_text(encoding="utf-8").splitlines():
                    r = json.loads(line)
                    if r["mode"] != MODE or not r["noisy"] or r["metrics"] is None:
                        continue
                    out["sets"].setdefault((arm_dir.name, r["set"]), {})[t] = \
                        (float(r["metrics"]["skill_combined"]), list(r["bands"]))
            rj = d / "result.json"
            if rj.exists():
                out.setdefault("pixels", {})[t] = json.loads(
                    rj.read_text(encoding="utf-8")).get("pixels")
            sj = d / "search.json"
            if sj.exists():
                for arm, p in json.loads(sj.read_text(encoding="utf-8")).items():
                    out["paths"].setdefault(arm, {})[t] = p
    return out


def load_eco_rescore(root: Path, wanted: dict[int, list[str]]) -> dict[int, dict]:
    """{k: {task: value}} from sweep_eco_arch runs, one directory per k."""
    out = {}
    for k, bands in wanted.items():
        for res in sorted((root / f"k{k}").glob("**/f*s*/result.json")):
            r = json.loads(res.read_text(encoding="utf-8"))
            if sorted(r["bands"]) != sorted(bands):
                print(f"  skip {res}: bands {r['bands']} are not the k={k} consensus")
                continue
            row = next((x for x in r["rows"] if x["size"] == RESCORE_SIZE), None)
            if row:
                out.setdefault(k, {})[(r["fold"], r["seed"])] = float(
                    np.mean([row["noisy"][f"skill_{h}"] for h in HEADS]))
    return out


# ---------------------------------------------------------------- statistics
def mean_se(per_task: dict) -> tuple[float, float]:
    """Mean over tasks; SE over outer folds, seeds averaged within a fold first."""
    by_fold: dict[int, list[float]] = {}
    for (f, _), v in per_task.items():
        by_fold.setdefault(f, []).append(v)
    per = np.array([np.mean(v) for v in by_fold.values()])
    se = float(per.std(ddof=1) / np.sqrt(len(per))) if len(per) > 1 else float("nan")
    return float(np.mean(list(per_task.values()))), se


def paired(a: dict, b: dict) -> tuple[float, float, int]:
    """a - b on the tasks both hold: mean and SE over folds (A-49's tie test)."""
    common = {t: a[t] - b[t] for t in set(a) & set(b)}
    if not common:
        return float("nan"), float("nan"), 0
    m, se = mean_se(common)
    return m, se, len(common)


# ---------------------------------------------------------------- consensus
def s2_consensus(eco: dict, order, info) -> list[dict]:
    rows = []
    paths = eco["paths"]["combined"]
    for k in sorted(paths):
        sets = [b for _, b in paths[k].values()]
        c = consensus(sets, lambda b: s2_region(info[b].role), k, order)
        rows.append({"source": "Sentinel-2 (eco_v3)", "arm": "combined", "k": k, **c})
    return rows


def hs_consensus(hs: dict) -> list[dict]:
    rows = []
    for arm in SWIR_ARMS:
        tasks = hs["paths"].get(arm, {})
        if not tasks:
            continue
        fixed = next(iter(tasks.values()))["fixed"]
        k_max = min(len(p["steps"]) for p in tasks.values())
        order = sorted({s["added"] for p in tasks.values() for s in p["steps"]},
                       key=lambda b: (hs_centre(b), b))
        for k in range(1, k_max + 1):
            sets = [[s["added"] for s in p["steps"][:k]] for p in tasks.values()]
            c = consensus(sets, hs_region, k, order)
            rows.append({"source": "AVIRIS-NG (hs_v4)", "arm": arm, "k": k, **c,
                         "fixed": fixed, "set": f"consensus/{arm}/k{k}"})
    return rows


def write_grid(hs_rows: list[dict]) -> dict:
    """The hs grid with its references swapped for the consensus sets, plus the
    anchors every hs_v4 option is read against."""
    g = json.loads(HS_GRID.read_text(encoding="utf-8"))
    keep = ("config_c/VNIR", "config_a", "config_c")
    refs = {k: g["references"][k] for k in keep}
    for r in hs_rows:
        refs[r["set"]] = [*r["fixed"], *r["bands"]]
    g["references"] = refs
    g["grid"] = "p12_consensus"
    g["note"] = ("E-46 re-score (Q38): hs_v4 consensus SWIR sets as fixed references, with "
                 "config_c/VNIR, config_a and config_c as anchors. Written by "
                 "Fire_Risk_Statistics scripts/make_band_options.py.")
    OUT_GRID.write_text(json.dumps(g, indent=1), encoding="utf-8")
    return refs


# ---------------------------------------------------------------- options
class Opt:
    def __init__(self, name, shown, bands, per_task, kind, stable=""):
        self.name, self.shown, self.bands, self.per = name, shown, bands, per_task
        self.kind, self.stable = kind, stable
        self.mean, self.se = mean_se(per_task)


def judge(opts: list[Opt]) -> list[dict]:
    """band_options' pros and cons, with A-49's PAIRED tie and dominance tests."""
    best = max(opts, key=lambda o: o.mean)
    recs = assess([Option(o.name, o.bands, o.mean, o.se, {}, None, o.stable) for o in opts])
    by = {r["option"]: r for r in recs}
    tie_text = ("best combined score", "tied with the best", "below the best combined score")
    out = []
    for o in sorted(opts, key=lambda o: -o.mean):
        r = by[o.name]
        gap, gse, n = (0.0, 0.0, len(o.per)) if o is best else paired(best.per, o.per)
        tied = o is best or gap <= gse
        pros = [p for p in r["pros"] if not p.startswith(tie_text)]
        cons = [c for c in r["cons"]
                if not c.startswith(tie_text) and "below the best combined score" not in c]
        if o is best:
            pros.insert(0, "best combined score")
        elif tied:
            pros.insert(0, f"tied with the best (paired gap {gap:.4f} +- {gse:.4f})")
        else:
            cons.insert(0, f"{gap:.4f} +- {gse:.4f} below the best (paired)")
        if o.kind == "procedure":
            cons.append("score of the search procedure (each fold's own set), not of this "
                        "fixed set: re-score pending")
        out.append({"option": o.name, "kind": o.kind, "bands": o.shown, "n_bands": len(o.bands),
                    "chain": r["chain"], "cost": r["cost"], "skill": o.mean, "se": o.se,
                    "gap_to_best": gap, "gap_se": gse, "n_paired": n, "tied_with_best": tied,
                    "pros": pros, "cons": cons, "dominated_by": None})
    for r in out:
        for b in out:
            if (b is r or b["n_bands"] > r["n_bands"]
                    or COST_ORDER[b["cost"]] > COST_ORDER[r["cost"]]):
                continue
            ob = next(o for o in opts if o.name == b["option"])
            orr = next(o for o in opts if o.name == r["option"])
            g, s, _ = paired(ob.per, orr.per)
            if g > s:
                r["dominated_by"] = b["option"]
                break
    return out


def s2_options(eco, cons_rows, rescore, info) -> list[Opt]:
    name = {b: option_name(info[b]) for b in info}
    opts = []
    for k, d in sorted(eco["paths"]["combined"].items()):
        sets = [tuple(sorted(b)) for _, b in d.values()]
        modal = max(set(sets), key=sets.count)
        opts.append(Opt(f"equal-weight search, k={k}", list(modal), [name[b] for b in modal],
                        {t: v for t, (v, _) in d.items()}, "procedure",
                        f"unstable: the {len(sets)} searches chose {len(set(sets))} distinct "
                        f"sets (modal set in {sets.count(modal)})"))
    for path in PATHS[1:]:
        best_k = max(eco["paths"][path],
                     key=lambda k: np.mean([v for v, _ in eco["paths"][path][k].values()]))
        d = eco["paths"][path][best_k]
        sets = [tuple(sorted(b)) for _, b in d.values()]
        modal = max(set(sets), key=sets.count)
        opts.append(Opt(f"{path} search, k={best_k}", list(modal), [name[b] for b in modal],
                        {t: v for t, (v, _) in d.items()}, "procedure",
                        f"unstable: {len(set(sets))} distinct sets in {len(sets)} searches"))
    all12 = list(info)
    opts.append(Opt("all 12 bands", all12, [name[b] for b in all12], eco["all"], "reference"))
    for c in cons_rows:
        per = rescore.get(c["k"])
        if per:
            text = (f"stable: every region slot in at least {c['min_support']} of "
                    f"{c['n_searches']} searches" if c["stable"] else
                    f"unstable: a slot in only {c['min_support']} of {c['n_searches']} searches")
            opts.append(Opt(f"consensus, k={c['k']}", c["bands"], [name[b] for b in c["bands"]],
                            per, "consensus (re-scored)", text))
    return opts


def swir_options(hs, cons_rows, hs_rescore) -> list[Opt]:
    opts = []
    for (arm, s), d in sorted(hs["sets"].items()):
        if arm in SWIR_ARMS and s.startswith("k"):
            sets = [tuple(b) for _, b in d.values()]
            opts.append(Opt(f"{arm} search, {s}", list(sets[0])[:6] + ["(searched)"],
                            list(max(set(sets), key=sets.count)),
                            {t: v for t, (v, _) in d.items()}, "procedure",
                            f"unstable: {len(set(sets))} distinct sets in {len(sets)} searches"))
        elif arm == "references" and s in ("config_c/VNIR", "config_a", "config_b", "config_c",
                                            "sensor_mantis_ms_plus_swir"):
            b = next(iter(d.values()))[1]
            opts.append(Opt(f"reference: {s}", b, b, {t: v for t, (v, _) in d.items()},
                            "reference"))
    for c in cons_rows:
        d = hs_rescore.get(("references", c["set"])) if hs_rescore else None
        if d:
            b = [*c["fixed"], *c["bands"]]
            text = (f"stable: every 50 nm slot in at least {c['min_support']} of "
                    f"{c['n_searches']} searches" if c["stable"] else
                    f"unstable: a slot in only {c['min_support']} of {c['n_searches']} searches")
            opts.append(Opt(f"consensus {c['arm']}, k={c['k']}", b, b,
                            {t: v for t, (v, _) in d.items()}, "consensus (re-scored)", text))
    for o in opts:
        if o.shown and o.shown[-1] == "(searched)":
            o.shown = o.bands
    return opts


# ---------------------------------------------------------------- outputs
def write_csv(path: Path, rows: list[dict]) -> None:
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: ("; ".join(map(str, v)) if isinstance(v, list) and k != "slots"
                            else json.dumps(v) if k == "slots" else v) for k, v in r.items()})


def options_md(title: str, recs: list[dict], pending: list[dict]) -> list[str]:
    keep = [r for r in recs if not r["dominated_by"]]
    L = [f"### {title}", "",
         f"{len(keep)} options shown of {len(recs)} scored; the rest are beaten (paired, beyond "
         "one SE) by an option with no more bands and no higher cost class. **Bold**: tied "
         "with the best. Cost is qualitative (Q6 open) and never chooses (A-41).", "",
         "| option | bands | score ± SE | gap to best (paired) | chain, cost | pros | cons |",
         "|---|---|---|---|---|---|---|"]
    for r in keep:
        name = f"**{r['option']}**" if r["tied_with_best"] else r["option"]
        L.append(f"| {name} | {', '.join(r['bands'])} | {r['skill']:.4f} ± {r['se']:.4f} | "
                 f"{r['gap_to_best']:.4f} ± {r['gap_se']:.4f} | {r['chain']}, {r['cost']} | "
                 f"{'; '.join(r['pros'])} | {'; '.join(r['cons'])} |")
    if pending:
        L += ["", "Consensus sets awaiting their re-score (no score until then):", "",
              "| set | bands | weakest slot | stable (≥ need) |", "|---|---|---|---|"]
        for c in pending:
            name = c.get("set") or f"consensus, k={c['k']}"
            bands = [*c.get("fixed", []), *c["bands"]] if c.get("fixed") else c["bands"]
            L.append(f"| {name} | {', '.join(bands)} | {c['min_support']} of "
                     f"{c['n_searches']} | {'yes' if c['stable'] else 'no'} ({c['need']}) |")
    return L + [""]


def support_matrix(rows: list[dict], sets_of) -> tuple[list[str], list[int], np.ndarray, set]:
    """Rows: region slots; columns: k; cell: searches supporting the slot at k."""
    ks = [r["k"] for r in rows]
    cells, taken = {}, set()
    for r in rows:
        sets = sets_of(r["k"])
        counts = [{} for _ in sets]
        for c, s in zip(counts, sets, strict=True):
            for b in s:
                c[r["region_of"](b)] = c.get(r["region_of"](b), 0) + 1
        for reg in {g for c in counts for g in c}:
            for j in range(1, max(c.get(reg, 0) for c in counts) + 1):
                cells[(reg, j, r["k"])] = sum(c.get(reg, 0) >= j for c in counts)
        for s in r["slots"]:
            taken.add((s["region"], s["slot"], r["k"]))
    labels = sorted({(g, j) for g, j, _ in cells},
                    key=lambda x: (-max(v for (g, j, _), v in cells.items() if (g, j) == x), x[1]))
    m = np.array([[cells.get((g, j, k), 0) for k in ks] for g, j in labels], float)
    nth = {2: "2nd", 3: "3rd"}
    names = [g if j == 1 else f"{g} ({nth.get(j, f'{j}th')})" for g, j in labels]
    return names, ks, m, {(names[i], k) for i, (g, j) in enumerate(labels)
                          for k in ks if (g, j, k) in taken}


def figure_consensus(panels, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("seq", [AX_BG, BLUE])
    fig, axs = plt.subplots(1, len(panels), figsize=(5.2 * len(panels), 6.2), facecolor=FIG_BG,
                            gridspec_kw={"width_ratios": [max(3, len(p[2])) for p in panels]})
    axs = np.atleast_1d(axs)
    for ax, (title, names, ks, m, taken, n) in zip(axs, panels, strict=True):
        ax.set_facecolor(AX_BG)
        ax.imshow(m, cmap=cmap, vmin=0, vmax=n, aspect="auto")
        for i, name in enumerate(names):
            for j, k in enumerate(ks):
                v = int(m[i, j])
                if v:
                    ax.text(j, i, str(v), ha="center", va="center", fontsize=7.5,
                            color=INK_BRIGHT if v > n / 2 else MUTED)
                if (name, k) in taken:
                    ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False,
                                               ec=ORANGE, lw=1.6))
        ax.set_xticks(range(len(ks)), [str(k) for k in ks])
        ax.set_yticks(range(len(names)), names)
        ax.tick_params(colors=INK, labelsize=8)
        for s in ax.spines.values():
            s.set_color(SPINE)
        ax.set_xlabel("bands searched (k)", color=INK, fontsize=9)
        ax.set_title(title, color=INK_BRIGHT, fontsize=10, loc="left")
    fig.text(0.01, -0.01,
             f"Cell: how many of the searches put at least that many bands in the region at k "
             f"(blue darker = more). Orange frame: the slot is in the consensus set at that k. "
             f"Stable needs {int(np.ceil(2 / 3 * panels[0][5]))} of {panels[0][5]} (Q38). "
             "Reconstructed (ours).", color=MUTED, fontsize=8.5, ha="left", va="top", wrap=True)
    fig.tight_layout()
    fig.savefig(out, dpi=150, facecolor=FIG_BG, bbox_inches="tight")
    plt.close(fig)


def figure_skill(eco, rescore, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 4.6), facecolor=FIG_BG)
    ax.set_facecolor(AX_BG)
    for s in ax.spines.values():
        s.set_color(SPINE)
    ax.tick_params(colors=INK, labelsize=8.5)
    ax.grid(True, color=SPINE, lw=0.6, alpha=0.6)
    ks = sorted(eco["paths"]["combined"])
    ms = [mean_se({t: v for t, (v, _) in eco["paths"]["combined"][k].items()}) for k in ks]
    m, se = np.array([x[0] for x in ms]), np.array([x[1] for x in ms])
    ax.fill_between(ks, m - se, m + se, color=BLUE, alpha=0.15, lw=0)
    ax.plot(ks, m, color=BLUE, lw=2, marker="o", ms=4,
            label="equal-weight search (each fold's own set)")
    if rescore:
        kk = sorted(rescore)
        cm = [mean_se(rescore[k]) for k in kk]
        ax.errorbar(kk, [x[0] for x in cm], yerr=[x[1] for x in cm], color=ORANGE, marker="s",
                    ms=6, lw=0, elinewidth=1.4, capsize=3, label="consensus set, re-scored")
    a, ase = mean_se(eco["all"])
    ax.axhline(a, color=MUTED, lw=1, ls="--")
    ax.text(ks[0], a, f" all 12 bands {a:.3f}", color=MUTED, fontsize=8, va="bottom")
    ax.set_xlabel("bands (k)", color=INK, fontsize=9)
    ax.set_ylabel("equal-weight skill, with sensor noise", color=INK, fontsize=9)
    ax.set_title("Sentinel-2: skill by band count", color=INK_BRIGHT, fontsize=10.5, loc="left")
    leg = ax.legend(frameon=False, fontsize=8.5, loc="lower right")
    for t in leg.get_texts():
        t.set_color(INK)
    fig.text(0.01, -0.02, "eco_v3, raw + indices, placeholder noise (A-37). Mean over 15 tasks, "
             "band and bars one SE over the 5 outer folds. Reconstructed (ours).",
             color=MUTED, fontsize=8.5, ha="left", va="top", wrap=True)
    fig.tight_layout()
    fig.savefig(out, dpi=150, facecolor=FIG_BG, bbox_inches="tight")
    plt.close(fig)


def figure_placement(s2c, hsc, info, out: Path) -> None:
    """Qualitative view: where each consensus set's bands sit on a canopy spectrum,
    with rule 7's forbidden regions shaded."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from safari_bands import forward as F
    from safari_bands.config.loader import load_atmospheric_windows, load_priors
    pr = load_priors("lfmc_v1")
    mid = {c: float(np.mean(v)) for c, v in {**pr.groups["conifer"], **pr.geometry}.items()}
    rho = F.Prosail().reflectance(mid)
    rows = [(f"S2 k={r['k']}", [(info[b].centre_nm, info[b].fwhm_nm) for b in r["bands"]],
             r["stable"]) for r in s2c]
    rows += [(f"{r['arm'].replace('swir_', '')} k={r['k']}",
              [tuple(float(x) for x in b.split("@")[0].split("/")) for b in r["bands"]],
              r["stable"]) for r in hsc]
    fig, (ax0, ax) = plt.subplots(2, 1, figsize=(12, 7.5), facecolor=FIG_BG, sharex=True,
                                  gridspec_kw={"height_ratios": [1, 2.6], "hspace": 0.08})
    for a in (ax0, ax):
        a.set_facecolor(AX_BG)
        for sp in a.spines.values():
            sp.set_color(SPINE)
        a.tick_params(colors=INK, labelsize=8)
        for reg in load_atmospheric_windows().forbidden_regions:
            a.axvspan(*reg.range_nm, color=MUTED, alpha=0.18, lw=0)
    ax0.plot(F.WAVELENGTHS, rho, color=INK, lw=1.2)
    ax0.set_ylabel("reflectance", color=INK, fontsize=9)
    ax0.set_title("Where the consensus bands sit (grey: forbidden atmospheric regions, rule 7)",
                  color=INK_BRIGHT, fontsize=10.5, loc="left")
    for i, (lab, bands, stable) in enumerate(rows):
        y = len(rows) - 1 - i
        col = BLUE if stable else ORANGE
        for c, w in bands:
            ax.add_patch(plt.Rectangle((c - w / 2, y - 0.35), w, 0.7, color=col, lw=0))
        ax.text(395, y, lab, color=INK, fontsize=8, ha="right", va="center")
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.set_yticks([])
    ax.set_xlim(400, 2500)
    ax.set_xlabel("wavelength (nm); bar width = band FWHM", color=INK, fontsize=9)
    ax.plot([], [], color=BLUE, lw=6, label="stable (every slot >= 10 of 15 searches)")
    ax.plot([], [], color=ORANGE, lw=6, label="not stable")
    leg = ax.legend(frameon=False, fontsize=8.5, loc="lower left")
    for t in leg.get_texts():
        t.set_color(INK)
    fig.text(0.01, 0.0, "Top: one conifer canopy from the forward model at the lfmc_v1 prior "
             "means (PROSPECT-D + 4SAIL), for orientation only. Rows: S2 = Sentinel-2 "
             "consensus (eco_v3); std / ext = AVIRIS-NG SWIR consensus on standard or extended "
             "InGaAs (hs_v4), each above the fixed six VNIR bands. Reconstructed (ours).",
             color=MUTED, fontsize=8.5, ha="left", va="top", wrap=True)
    fig.savefig(out, dpi=150, facecolor=FIG_BG, bbox_inches="tight")
    plt.close(fig)


def commands(s2_rows, hs_rows) -> list[str]:
    L = ["# E-46 re-score commands (Q38: the consensus set is scored as a fixed set)", "",
         "Written by `scripts/make_band_options.py`. On Nibi, in `Fire_Risk_FW` after "
         "`git pull`.", "",
         "## Sentinel-2 consensus sets (eco_v3 folds and seeds, size 8x2, with noise)", "",
         "```bash"]
    for r in s2_rows:
        L.append(f"BANDS={','.join(r['bands'])} SIZES={RESCORE_SIZE} EXP_NAME=bands_consensus_v2 "
                 f"RUN_ID=k{r['k']} SUBMIT=1 bash scripts/shell/sweep_eco_arch.sh")
    L += ["```", "", "Copy back `~/scratch/fw_experiments/bands_consensus_v2/` to "
          "`narval_results/bands_consensus_v2/` (plain copy). The first run, "
          "`bands_consensus`, passed only the first band at k >= 2 (fixed in FW 6b1499a).",
          "",
          "## AVIRIS-NG consensus SWIR sets (hs_v4 folds and seeds, references arm)", "",
          "```bash",
          "ARMS=references GRID=configs/noise/p12_consensus_grid.json "
          "SCRATCH_DATA=$HOME/scratch/aviris_v4 EXP_NAME=hs_consensus "
          "SUBMIT=1 bash scripts/shell/sweep_hs.sh", "```", "",
          "`SCRATCH_DATA` must be `aviris_v4`, the pack hs_v4 ran on (`sweep_hs.sh` "
          "defaults to aviris_v2). The combiner rejects any task whose pixel counts "
          "differ from hs_v4's.", "",
          f"It scores {len(hs_rows)} consensus sets plus three anchors (config_c/VNIR, config_a, "
          "config_c). Copy back to `narval_results/hs_consensus/`.", "",
          "Then: `python scripts/make_band_options.py "
          "--eco-rescore narval_results/bands_consensus_v2 "
          "--hs-rescore narval_results/hs_consensus/<run>`."]
    return L


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--eco", type=Path, default=ECO)
    ap.add_argument("--hs", type=Path, default=HS)
    ap.add_argument("--eco-rescore", type=Path, default=None)
    ap.add_argument("--hs-rescore", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=ROOT / "docs" / "results" / "p12_bands")
    ap.add_argument("--no-grid", action="store_true", help="do not write the FW grid")
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    order, info = s2_bands()
    eco, hs = load_eco(args.eco), load_hs(args.hs)
    s2c = s2_consensus(eco, order, info)
    hsc = hs_consensus(hs)
    if not args.no_grid:
        write_grid(hsc)
    rescore = (load_eco_rescore(args.eco_rescore, {r["k"]: r["bands"] for r in s2c})
               if args.eco_rescore else {})
    hs_rescore = {}
    if args.hs_rescore:
        rs = load_hs(args.hs_rescore)
        bad = {t for t, px in rs.get("pixels", {}).items()
               if px != hs.get("pixels", {}).get(t)}
        if bad:
            print(f"  hs re-score: {len(bad)} tasks ran on other pixels than hs_v4 "
                  f"(wrong pack?), dropped: {sorted(bad)}")
        hs_rescore = {k: {t: v for t, v in d.items() if t not in bad}
                      for k, d in rs["sets"].items()}

    s2_recs = judge(s2_options(eco, s2c, rescore, info))
    sw_recs = judge(swir_options(hs, hsc, hs_rescore))
    write_csv(args.out / "T_consensus.csv",
              [{k: v for k, v in r.items() if k != "region_of"} for r in s2c + hsc])
    write_csv(args.out / "T_options_s2.csv", s2_recs)
    write_csv(args.out / "T_options_swir.csv", sw_recs)

    s2_sets = {k: [b for _, b in d.values()] for k, d in eco["paths"]["combined"].items()}
    panels = [("Sentinel-2, equal-weight search", *support_matrix(
        [{**r, "region_of": lambda b: s2_region(info[b].role)} for r in s2c],
        lambda k: s2_sets[k]), len(next(iter(s2_sets.values()))))]
    for arm in SWIR_ARMS:
        rows = [r for r in hsc if r["arm"] == arm]
        if rows:
            tasks = hs["paths"][arm]
            panels.append((f"AVIRIS-NG {arm}, 50 nm bins", *support_matrix(
                [{**r, "region_of": hs_region} for r in rows],
                lambda k, t=tasks: [[s["added"] for s in p["steps"][:k]] for p in t.values()]),
                len(tasks)))
    figure_consensus(panels, args.out / "consensus.png")
    figure_skill(eco, rescore, args.out / "skill.png")
    figure_placement(s2c, hsc, info, args.out / "qual_E-46_band_placement.png")

    pend_s2 = [r for r in s2c if r["k"] not in rescore]
    pend_hs = [r for r in hsc if ("references", r["set"]) not in hs_rescore]
    md = ["# E-46 option tables (generated)", ""]
    md += options_md("Sentinel-2: VNIR bands, and whether SWIR is in", s2_recs, pend_s2)
    md += options_md("AVIRIS-NG: where the SWIR bands sit", sw_recs, pend_hs)
    (args.out / "options.md").write_text("\n".join(md), encoding="utf-8")
    (args.out / "rescore_commands.md").write_text("\n".join(commands(s2c, hsc)) + "\n",
                                                  encoding="utf-8")
    summary = {"eco": str(args.eco), "hs": str(args.hs), "eco_rescore": str(args.eco_rescore),
               "hs_rescore": str(args.hs_rescore),
               "consensus": [{k: v for k, v in r.items() if k != "region_of"}
                             for r in s2c + hsc],
               "best_s2": s2_recs[0]["option"], "best_swir": sw_recs[0]["option"],
               "pending": {"s2": [r["k"] for r in pend_s2], "swir": [r["set"] for r in pend_hs]}}
    (args.out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    for r in s2c + hsc:
        bands = [*r.get("fixed", []), *r["bands"]] if r.get("fixed") else r["bands"]
        print(f"{r['source'][:10]:10s} {r['arm']:9s} k={r['k']}: {' '.join(r['bands'])}  "
              f"weakest slot {r['min_support']}/{r['n_searches']} "
              f"{'stable' if r['stable'] else 'UNSTABLE'}; exact in {r['exact_matches']}"
              + ("" if bands == r["bands"] else ""))
    print(f"best S2 option: {s2_recs[0]['option']}; best SWIR option: {sw_recs[0]['option']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
