"""How much the P12 band choice depends on how the four structure heads are
weighted (A-49; James, 2026-11-05: equal weights, other schemes tried where
feasible).

eco_v3 ran five greedy searches per outer fold and seed: one on the
equal-weight combined skill and one per head (pc, closure, height, family).
Each searched set was then scored on the outer fold for all four heads. This
script re-scores those sets under each weighting scheme of A-49 and reports,
per scheme, which search's sets score best at each k and by how much.

What it can and cannot show: it ranks the five searched paths under each
scheme. A scheme-specific search could find a set none of the five paths
holds, so a non-equal scheme's best here is a lower bound on what its own
search would reach. If the scheme ranks the combined path first or tied, the
equal-weight choice is robust to it.

    python scripts/compare_head_weights.py --run narval_results/eco_v3/20261102-1959
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
HEADS = ("pc", "closure", "height", "family")
PATHS = ("combined", "pc", "closure", "height", "family")
MODE = "raw+indices"           # the mode every eco_v3 path was searched in
SWIR, RED_EDGE = {"B11", "B12"}, {"B5", "B6", "B7"}

#: A-49, fixed before this script's output was read. Weights sum to 1;
#: "maximin" is the worst head's skill as a fraction of its all-band skill.
SCHEMES = {
    "equal (the rule)": {"pc": 0.25, "closure": 0.25, "height": 0.25, "family": 0.25},
    "regression heads only": {"pc": 1 / 3, "closure": 1 / 3, "height": 1 / 3, "family": 0.0},
    "fuel type first": {"pc": 1 / 6, "closure": 1 / 6, "height": 1 / 6, "family": 0.5},
    "percent conifer first": {"pc": 0.5, "closure": 1 / 6, "height": 1 / 6, "family": 1 / 6},
    "canopy first": {"pc": 1 / 6, "closure": 1 / 3, "height": 1 / 3, "family": 1 / 6},
    "maximin": None,
}

FIG_BG, AX_BG = "#0f1117", "#1a1d27"
SPINE, INK, INK_BRIGHT, MUTED = "#333344", "#cccccc", "#eeeeee", "#8b8b9a"
BLUE, ORANGE, GREEN, AMBER, PINK = "#3987e5", "#d95926", "#199e70", "#c98500", "#d55181"
PATH_COL = dict(zip(PATHS, (BLUE, ORANGE, GREEN, AMBER, PINK), strict=True))
PATH_LABEL = {"combined": "equal-weight search", "pc": "percent-conifer search",
              "closure": "closure search", "height": "height search",
              "family": "fuel-family search"}


def load(run: Path) -> list[dict]:
    """One record per task: {path: {k: (skills, bands)}, 'all': skills}."""
    tasks = []
    for d in sorted(run.glob("f*s*")):
        ev = d / "eval.jsonl"
        if not ev.exists():
            continue
        t = {"task": d.name, "fold": int(d.name[1:].split("s")[0]), "paths": {}}
        for line in ev.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r["mode"] != MODE or not r["noisy"] or r["metrics"] is None:
                continue
            sk = {h: r["metrics"][f"skill_{h}"] for h in HEADS}
            if r["selector"] == "all_bands":
                t["all"] = sk
            elif r["selector"] in PATHS:
                t["paths"].setdefault(r["selector"], {})[r["k"]] = (sk, r["bands"])
        tasks.append(t)
    return tasks


def value(scheme: str, sk: dict, all_sk: dict) -> float:
    w = SCHEMES[scheme]
    if w is None:
        return min(sk[h] / all_sk[h] for h in HEADS if all_sk[h] > 0)
    return sum(w[h] * sk[h] for h in HEADS)


def summarise(tasks: list[dict]) -> list[dict]:
    """Mean over tasks and an SE over outer folds (seeds averaged within a
    fold first: seeds share their blocks, so they are not independent)."""
    rows = []
    ks = sorted({k for t in tasks for p in t["paths"].values() for k in p})
    for scheme in SCHEMES:
        for path in PATHS:
            for k in ks:
                by_fold: dict[int, list[float]] = {}
                bands = []
                for t in tasks:
                    if k in t["paths"].get(path, {}):
                        sk, b = t["paths"][path][k]
                        by_fold.setdefault(t["fold"], []).append(value(scheme, sk, t["all"]))
                        bands.append(tuple(sorted(b)))
                if not by_fold:
                    continue
                f = np.array([np.mean(v) for v in by_fold.values()])
                allv = [x for v in by_fold.values() for x in v]
                modal, n_modal = Counter(bands).most_common(1)[0]
                rows.append({"scheme": scheme, "path": path, "k": k, "mean": float(np.mean(allv)),
                             "se": float(f.std(ddof=1) / np.sqrt(len(f))) if len(f) > 1 else 0.0,
                             "n_tasks": len(allv), "n_folds": len(f),
                             "share_swir": float(np.mean([bool(SWIR & set(x)) for x in bands])),
                             "share_red_edge": float(np.mean([bool(RED_EDGE & set(x))
                                                              for x in bands])),
                             "modal_set": " ".join(modal), "modal_share": n_modal / len(bands)})
    return rows


def _per_task(tasks: list[dict], scheme: str, path: str, k: int) -> dict[str, tuple[int, float]]:
    return {t["task"]: (t["fold"], value(scheme, t["paths"][path][k][0], t["all"]))
            for t in tasks if k in t["paths"].get(path, {})}


def paired_gap(tasks, scheme, a: tuple[str, int], b: tuple[str, int]) -> tuple[float, float]:
    """Mean of a - b over tasks holding both, and its SE over outer folds
    (seeds averaged within a fold first)."""
    va, vb = _per_task(tasks, scheme, *a), _per_task(tasks, scheme, *b)
    by_fold: dict[int, list[float]] = {}
    for t in set(va) & set(vb):
        by_fold.setdefault(va[t][0], []).append(va[t][1] - vb[t][1])
    f = np.array([np.mean(v) for v in by_fold.values()])
    se = float(f.std(ddof=1) / np.sqrt(len(f))) if len(f) > 1 else float("nan")
    return float(np.mean([x for v in by_fold.values() for x in v])), se


def decisions(rows: list[dict], tasks: list[dict]) -> list[dict]:
    """Per scheme, the A-41 rule over every (path, k): the best mean wins, and
    a set is tied when its paired gap to the best (same fold and seed) is
    within one SE of that gap (A-49)."""
    out = []
    for scheme in SCHEMES:
        r = [x for x in rows if x["scheme"] == scheme]
        best = max(r, key=lambda x: x["mean"])
        tied = []
        for x in r:
            if x is best:
                continue
            gap, se = paired_gap(tasks, scheme, (best["path"], best["k"]), (x["path"], x["k"]))
            x_gap = (x["path"], x["k"], gap, se)
            if gap <= se:
                tied.append(x_gap)
        eq = max((x for x in r if x["path"] == "combined"), key=lambda x: x["mean"])
        top = (best["path"], best["k"])
        eq_gap, eq_se = ((0.0, 0.0) if eq is best
                         else paired_gap(tasks, scheme, top, ("combined", eq["k"])))
        cands = [(best["path"], best["k"])] + [(p, k) for p, k, _, _ in tied]
        small = min(cands, key=lambda c: (c[0] != "combined", c[1]))
        small_eq = min((c for c in cands if c[0] == "combined"), key=lambda c: c[1], default=None)
        out.append({"scheme": scheme, "best_path": best["path"], "best_k": best["k"],
                    "best_mean": best["mean"], "best_modal_set": best["modal_set"],
                    "best_modal_share": best["modal_share"],
                    "best_share_swir": best["share_swir"],
                    "best_share_red_edge": best["share_red_edge"],
                    "n_tied": len(tied),
                    "tied": "; ".join(f"{p} k={k} (-{g:.4f} +- {e:.4f})" for p, k, g, e in tied),
                    "equal_search_best_k": eq["k"], "equal_search_gap": eq_gap,
                    "equal_search_gap_se": eq_se,
                    "equal_search_tied": eq is best or eq_gap <= eq_se,
                    "smallest_tied_equal_k": small_eq[1] if small_eq else None,
                    "first_choice": f"{small[0]} k={small[1]}"})
    return out


def figure(rows: list[dict], out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    schemes = list(SCHEMES)
    fig, axs = plt.subplots(2, 3, figsize=(13, 7.2), facecolor=FIG_BG, sharex=True)
    for ax, scheme in zip(axs.flat, schemes, strict=True):
        ax.set_facecolor(AX_BG)
        for s in ax.spines.values():
            s.set_color(SPINE)
        ax.tick_params(colors=INK, labelsize=8.5)
        ax.grid(True, color=SPINE, lw=0.6, alpha=0.6)
        ax.set_axisbelow(True)
        for path in PATHS:
            r = sorted((x for x in rows if x["scheme"] == scheme and x["path"] == path),
                       key=lambda x: x["k"])
            k = np.array([x["k"] for x in r])
            m = np.array([x["mean"] for x in r])
            se = np.array([x["se"] for x in r])
            ax.fill_between(k, m - se, m + se, color=PATH_COL[path], alpha=0.15, lw=0)
            ax.plot(k, m, color=PATH_COL[path], lw=2.4 if path == "combined" else 1.6,
                    marker="o", ms=4, label=PATH_LABEL[path])
        ylabel = ("worst head, share of its all-band skill" if SCHEMES[scheme] is None
                  else "weighted skill")
        ax.set_title(scheme, color=INK_BRIGHT, fontsize=10.5, loc="left", pad=6)
        ax.set_ylabel(ylabel, color=INK, fontsize=8.5)
    for ax in axs[-1]:
        ax.set_xlabel("bands in the set (k)", color=INK, fontsize=9)
    h, lab = axs.flat[0].get_legend_handles_labels()
    leg = fig.legend(h, lab, loc="upper center", ncol=5, frameon=False, fontsize=9,
                     bbox_to_anchor=(0.5, 1.02))
    for t in leg.get_texts():
        t.set_color(INK)
    fig.text(0.01, -0.01,
             "eco_v3 searched sets (raw + indices, with placeholder sensor noise), scored on "
             "the outer fold. Mean over 15 tasks; band = one SE over the 5 outer folds. "
             "A-49 schemes fixed before this figure was made. Reconstructed (ours).",
             color=MUTED, fontsize=8.5, ha="left", va="top", wrap=True)
    fig.tight_layout()
    fig.savefig(out, dpi=150, facecolor=FIG_BG, bbox_inches="tight")
    plt.close(fig)


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=ROOT / "docs" / "results" / "p12_weights")
    args = ap.parse_args(argv)
    tasks = load(args.run)
    if not tasks:
        raise SystemExit(f"no eval.jsonl under {args.run}")
    rows = summarise(tasks)
    dec = decisions(rows, tasks)
    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "T_weights.csv", rows)
    write_csv(args.out / "T_weight_decisions.csv", dec)
    figure(rows, args.out / "weights.png")
    (args.out / "summary.json").write_text(json.dumps(
        {"run": str(args.run), "n_tasks": len(tasks), "mode": MODE,
         "schemes": {k: v for k, v in SCHEMES.items()}, "decisions": dec}, indent=1))
    for d in dec:
        print(f"{d['scheme']:24s} best {d['best_path']:8s} k={d['best_k']} {d['best_mean']:.4f}; "
              f"{d['n_tied']} tied; equal search k={d['equal_search_best_k']} "
              f"gap {d['equal_search_gap']:.4f} +- {d['equal_search_gap_se']:.4f} "
              f"(tied: {d['equal_search_tied']}); smallest tied equal-search k="
              f"{d['smallest_tied_equal_k']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
