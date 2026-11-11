"""scripts/make_swir2_package.py

P12f: what SWIR2 (B12, 2190 nm) adds on the general track (E-68, A-55). The
Sentinel-2 consensus sets k=5 and k=8 against themselves without B12, at every
U-Net size, paired by fold and seed (all ladders share eco_v3's folds).

    python scripts/make_swir2_package.py \\
        --k5 narval_results/arch_k5/20261109-2213 \\
        --k5-no-b12 narval_results/arch_k5_no_b12/20261111-0021 \\
        --k8 narval_results/arch_k8/20261109-2213 \\
        --k8-no-b12 narval_results/arch_k8_no_b12/20261111-0021
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_arch_package as A  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "results" / "P12" / "p12_swir2"


def verdict(c) -> str:
    """Registered (E-68): B12 raises the best rung, so 'without minus with' must
    have its CI below 0; WRONG IF it reaches 0."""
    return "SUPPORTED" if c["ci"][1] < 0 else "REFUTED"


def figure(pairs, out: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.3), facecolor=A.FIG_BG, sharey=True)
    for ax, (k, L) in zip(axes, pairs.items(), strict=True):
        A._axes(ax)
        ax.grid(True, color=A.SPINE, lw=0.6, alpha=0.6)
        for (name, d), col in zip(L["per"].items(), (A.BLUE, A.ORANGE), strict=True):
            xs, ys = [], []
            for s, v in d["sizes"].items():
                m, _ = A.mean_se(v)
                ax.plot(d["gmacs"][s], m, "o", color=col, ms=5, alpha=0.9)
                if d["depth"][s] == 1:
                    xs.append(d["gmacs"][s])
                    ys.append(m)
            o = np.argsort(xs)
            ax.plot(np.array(xs)[o], np.array(ys)[o], "-", color=col, lw=1.6,
                    label=f"{name}: {' '.join(d['bands'])}")
        ax.set_xscale("log")
        ax.set_title(f"{k}: with and without B12", color=A.INK_BRIGHT, fontsize=10, loc="left")
        ax.set_xlabel("GMAC per 1000 x 1000 px scene (log)", color=A.INK, fontsize=9)
        ax.legend(facecolor=A.AX_BG, edgecolor=A.SPINE, labelcolor=A.INK, fontsize=8,
                  loc="lower right")
    axes[0].set_ylabel("combined skill (with noise)", color=A.INK, fontsize=9)
    fig.suptitle("E-68  SWIR2 on the general track (Sentinel-2, eco_v3 folds)",
                 color=A.INK_BRIGHT, x=0.01, ha="left", fontsize=11)
    fig.text(0.01, -0.03, "Each point: mean over 5 folds x 3 seeds; lines join the depth-1 "
             "rungs. Paired contrasts in T_swir2.csv. Not on the Mantis track (A-55). "
             "Reconstructed (ours).", color=A.MUTED, fontsize=8.5, ha="left", va="top")
    fig.tight_layout()
    fig.savefig(out, dpi=150, facecolor=A.FIG_BG, bbox_inches="tight")
    plt.close(fig)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    for k in ("k5", "k5-no-b12", "k8", "k8-no-b12"):
        ap.add_argument(f"--{k}", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    pairs = {"k=5": A.ladders({"k5": a.k5, "k5 without B12": a.k5_no_b12}, "k5"),
             "k=8": A.ladders({"k8": a.k8, "k8 without B12": a.k8_no_b12}, "k8")}
    rows = []
    for k, L in pairs.items():
        for c in L["contrasts"]:
            rows.append({"pair": k, **{x: c[x] for x in ("band_set", "against", "comparison",
                                                        "a_size", "b_size", "d", "se")},
                         "ci_lo": c["ci"][0], "ci_hi": c["ci"][1], "n_pairs": c["n_pairs"],
                         "verdict": verdict(c) if c["comparison"] == "best rung vs best rung"
                         else ""})
    with (a.out / "T_swir2.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with (a.out / "T_ladders.csv").open("w", newline="", encoding="utf-8") as fh:
        allrows = [r for L in pairs.values() for r in L["rows"]]
        w = csv.DictWriter(fh, fieldnames=list(allrows[0]))
        w.writeheader()
        w.writerows(allrows)
    figure(pairs, a.out / "swir2.png")
    best = {name: max(d["sizes"], key=lambda s, d=d: A.mean_se(d["sizes"][s])[0])
            for L in pairs.values() for name, d in L["per"].items()}
    (a.out / "summary.json").write_text(json.dumps(
        {"runs": {k: str(v) for k, v in vars(a).items() if k != "out"}, "best": best,
         "contrasts": rows}, indent=1, default=str), encoding="utf-8")
    for r in rows:
        print(f"{r['pair']} {r['comparison']} ({r['a_size']} vs {r['b_size']}): {r['d']:+.4f} "
              f"[{r['ci_lo']:+.4f}, {r['ci_hi']:+.4f}] {r['verdict']}")
    print("best:", best)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
