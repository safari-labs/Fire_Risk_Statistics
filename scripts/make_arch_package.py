"""scripts/make_arch_package.py

E-47, P12c: the onboard model's size ladder (TinyEcologyUNet, base_ch x depth) at one
fixed band set, from a Fire_Risk_FW sweep_eco_arch run. Folds, split seed and pack
are eco_v3's, so every rung pairs by (outer fold, seed) with eco_v3 and with the
E-46 consensus re-scores.

    python scripts/make_arch_package.py --run narval_results/arch_mantis_std/<id>

Writes docs/results/P12/p12_arch/: T_arch.csv, T_compare.csv, arch.png,
qual_E-47_family_confusion.png, summary.json. Each rung's FPGA cost is looked up in
P12/p12_convert/T_convert.csv (22 inputs there, so a conservative bound).
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_band_options import HEADS, mean_se, paired  # noqa: E402

from safari_bands.config.loader import project_root  # noqa: E402

ROOT = project_root()
CONVERT = ROOT / "docs" / "results" / "P12" / "p12_convert" / "T_convert.csv"
#: E-46's fixed sets, scored at 8x2 on the same folds (for the band comparison).
COMPARE = {
    "stable consensus k=5 (B4 B5 B8A B11 B12)": ROOT / "narval_results" / "bands_consensus_v2"
    / "k5",
    "consensus k=8 (tied with the best)": ROOT / "narval_results" / "bands_consensus_v2" / "k8",
}
BUDGET_S = 43.0                                    # A-29: s per 1000 x 1000 px scene

FIG_BG, AX_BG = "#0f1117", "#1a1d27"
SPINE, INK, INK_BRIGHT, MUTED = "#333344", "#cccccc", "#eeeeee", "#8b8b9a"
BLUE, ORANGE, GREEN = "#3987e5", "#d95926", "#199e70"
DEPTH_COLOUR = {1: BLUE, 2: ORANGE, 3: GREEN}


def load(root: Path) -> tuple[dict, dict]:
    """{size: {(fold, seed): row}} and the run's metadata."""
    out, meta = {}, {}
    for f in sorted(root.glob("**/f*s*/result.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        meta = meta or {k: r[k] for k in ("bands", "mode", "pack", "tiles", "noise")}
        for row in r["rows"]:
            out.setdefault(row["size"], {})[(r["fold"], r["seed"])] = row
    return out, meta


def skill(row: dict) -> float:
    return float(np.mean([row["noisy"][f"skill_{h}"] for h in HEADS]))


def fpga() -> dict:
    """{size: {...}} from the conversion pre-check: DPU on the Q8, FINN W4A4 on both."""
    out: dict[str, dict] = {}
    for r in csv.DictReader(CONVERT.open(encoding="utf-8")):
        if r["mode"] != "raw+indices" or r["tile"] != "64":
            continue
        d = out.setdefault(r["size"], {})
        if r["flow"] == "DPU":
            d["q8_dpu_s"] = float(r["s_per_scene"])
        elif r["flow"] == "FINN" and r["precision"] == "W4A4":
            d["finn_s"] = float(r["s_per_scene"])
            d["finn_q7_share"] = float(r["Q7_share"])
            d["finn_q8_share"] = float(r["Q8_share"])
    return out


def build(run: Path) -> dict:
    arch, meta = load(run)
    per = {s: {t: skill(r) for t, r in d.items()} for s, d in arch.items()}
    best = max(per, key=lambda s: mean_se(per[s])[0])
    hw = fpga()
    rows = []
    for s, d in arch.items():
        m, se = mean_se(per[s])
        g, gse, n = paired(per[s], per[best])
        any_row = next(iter(d.values()))
        heads = {h: float(np.mean([r["noisy"][f"rmse_{h}"] for r in d.values()]))
                 for h in ("pc", "closure", "height")}
        heads["family_ba"] = float(np.mean([r["noisy"]["balanced_acc_family"]
                                            for r in d.values()]))
        h = hw.get(s, {})
        q7_ok = h.get("finn_s", np.inf) <= BUDGET_S and h.get("finn_q7_share", 1) <= 0.8
        rows.append({
            "size": s, "base_ch": any_row["base_ch"], "depth": any_row["depth"],
            "params": any_row["params"], "gmacs_per_scene": any_row["gmacs_per_scene"],
            "skill": m, "se": se, "gap": g, "gap_se": gse, "n_tasks": n,
            "tied": s == best or abs(g) <= gse,
            "rmse_pc": heads["pc"], "rmse_closure": heads["closure"],
            "rmse_height": heads["height"], "family_ba": heads["family_ba"],
            "q8_dpu_s": h.get("q8_dpu_s"), "finn_s": h.get("finn_s"),
            "finn_q7_share": h.get("finn_q7_share"), "q7_meets_budget": bool(q7_ok),
        })
    rows.sort(key=lambda r: (r["params"], r["size"]))
    compare = []
    for name, root in COMPARE.items():
        other, _ = load(root)
        if "8x2" in other and "8x2" in per:
            o = {t: skill(r) for t, r in other["8x2"].items()}
            d, se, n = paired(per["8x2"], o)
            compare.append({"against": name, "d": d, "se": se, "n_pairs": n})
    confusion = {s: np.sum([np.array(r["noisy"]["confusion_family"], float)
                            for r in arch[s].values()], axis=0).tolist()
                 for s in ("4x1", "8x2", "16x1", best) if s in arch}
    classes = next(iter(arch[best].values()))["noisy"]["family_classes"]
    return {"meta": meta, "best": best, "rows": rows, "compare": compare,
            "confusion": confusion, "classes": classes}


def _axes(ax):
    ax.set_facecolor(AX_BG)
    for s in ax.spines.values():
        s.set_color(SPINE)
    ax.tick_params(colors=INK, labelsize=8.5)


def figure(res, out: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 5.4), facecolor=FIG_BG)
    _axes(ax)
    ax.grid(True, color=SPINE, lw=0.6, alpha=0.6)
    for r in res["rows"]:
        c = DEPTH_COLOUR[r["depth"]]
        ax.errorbar(r["gmacs_per_scene"], r["gap"], yerr=1.96 * r["gap_se"], fmt="o", color=c,
                    ms=8 if r["tied"] else 6, mfc=c if r["tied"] else AX_BG, mew=2,
                    capsize=0, lw=1.5)
        ax.annotate(f"{r['size']}\n{r['params'] / 1e3:.0f}k", (r["gmacs_per_scene"], r["gap"]),
                    textcoords="offset points", xytext=(6, -14), color=INK, fontsize=7.5)
    ax.axhline(0, color=MUTED, lw=1, ls="--")
    ax.set_xscale("log")
    ax.set_xlabel("multiply-accumulates per 1000 x 1000 px scene (GMAC, log scale); "
                  "label: rung and parameters", color=INK, fontsize=9)
    ax.set_ylabel("combined skill minus the best rung (paired, 95 % CI)", color=INK,
                  fontsize=9)
    for d, c in DEPTH_COLOUR.items():
        ax.plot([], [], "o", color=c, label=f"depth {d}")
    ax.legend(facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK, fontsize=8, loc="lower right")
    bands = " ".join(res["meta"]["bands"])
    ax.set_title(f"E-47  Model size against skill at {bands} (Mantis standard-block "
                 f"stand-in); filled: tied with the best ({res['best']})", color=INK_BRIGHT,
                 fontsize=10, loc="left")
    fig.text(0.01, -0.03, "Sentinel-2 (eco_v3 pack, SCANFI labels), raw + indices, placeholder "
             "noise (A-37); 5 outer folds x 3 seeds, paired with eco_v3. Reconstructed (ours).",
             color=MUTED, fontsize=8.5, ha="left", va="top")
    fig.tight_layout()
    fig.savefig(out, dpi=150, facecolor=FIG_BG, bbox_inches="tight")
    plt.close(fig)


def figure_confusion(res, out: Path):
    """Qualitative view: where each rung confuses the fuel families (row-normalised)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    sizes = list(res["confusion"])
    cls = res["classes"]
    keep = [i for i in range(len(cls))
            if any(np.asarray(res["confusion"][s])[i].sum() > 0 for s in sizes)]
    fig, axes = plt.subplots(1, len(sizes), figsize=(3.3 * len(sizes), 3.6), facecolor=FIG_BG)
    for ax, s in zip(np.atleast_1d(axes), sizes, strict=True):
        _axes(ax)
        m = np.asarray(res["confusion"][s])[np.ix_(keep, keep)]
        m = m / np.maximum(m.sum(axis=1, keepdims=True), 1)
        ax.imshow(m, cmap="Blues", vmin=0, vmax=1)
        for i in range(len(keep)):
            for j in range(len(keep)):
                ax.text(j, i, f"{m[i, j]:.2f}", ha="center", va="center", fontsize=6.5,
                        color="white" if m[i, j] > 0.5 else "#0f1117")
        labels = [cls[i] for i in keep]
        ax.set_xticks(range(len(keep)), labels)
        ax.set_yticks(range(len(keep)), labels)
        ax.set_title(f"{s}", color=INK_BRIGHT, fontsize=9.5)
        ax.set_xlabel("predicted", color=INK, fontsize=8)
    np.atleast_1d(axes)[0].set_ylabel("true (SCANFI)", color=INK, fontsize=8)
    fig.suptitle("E-47  Fuel-family confusion by rung (rows sum to 1; all folds and seeds)",
                 color=INK_BRIGHT, fontsize=10.5, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(out, dpi=150, facecolor=FIG_BG, bbox_inches="tight")
    plt.close(fig)


def ladders(runs: dict[str, Path], primary: str) -> dict:
    """Every band set's ladder, and each set's best rung and same-size rungs against the
    primary set's (paired by fold and seed: all ladders share eco_v3's folds)."""
    per = {}
    for name, root in runs.items():
        arch, meta = load(root)
        per[name] = {"bands": meta["bands"],
                     "sizes": {s: {t: skill(r) for t, r in d.items()} for s, d in arch.items()},
                     "gmacs": {s: next(iter(d.values()))["gmacs_per_scene"]
                               for s, d in arch.items()},
                     "depth": {s: next(iter(d.values()))["depth"] for s, d in arch.items()}}
    rows, contrasts = [], []
    p = per[primary]
    p_best = max(p["sizes"], key=lambda s: mean_se(p["sizes"][s])[0])
    for name, d in per.items():
        best = max(d["sizes"], key=lambda s: mean_se(d["sizes"][s])[0])
        for s, v in d["sizes"].items():
            m, se = mean_se(v)
            g, gse, _ = paired(v, d["sizes"][best])
            rows.append({"band_set": name, "bands": " ".join(d["bands"]), "size": s,
                         "gmacs_per_scene": d["gmacs"][s], "skill": m, "se": se,
                         "gap_to_own_best": g, "gap_se": gse, "best": s == best})
        if name == primary:
            continue
        for label, a, b in (("best rung vs best rung", best, p_best), ("at 8x2", "8x2", "8x2"),
                            ("at 16x1", "16x1", "16x1"), ("at 32x1", "32x1", "32x1")):
            dd, se, n = paired(d["sizes"][a], p["sizes"][b])
            contrasts.append({"band_set": name, "against": primary, "comparison": label,
                              "a_size": a, "b_size": b, "d": dd, "se": se,
                              "ci": [dd - 1.96 * se, dd + 1.96 * se], "n_pairs": n})
    return {"per": per, "rows": rows, "contrasts": contrasts}


def figure_ladders(L, out: Path):
    """Skill against compute for every band set: width-only (depth 1) rungs joined."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    cols = [BLUE, ORANGE, GREEN, "#c98500", "#d55181"]
    fig, ax = plt.subplots(figsize=(10, 5.2), facecolor=FIG_BG)
    _axes(ax)
    ax.grid(True, color=SPINE, lw=0.6, alpha=0.6)
    for (name, d), c in zip(L["per"].items(), cols, strict=False):
        xs, ys = [], []
        for s, v in d["sizes"].items():
            m, se = mean_se(v)
            ax.plot(d["gmacs"][s], m, "o", color=c, ms=5, alpha=0.9)
            if d["depth"][s] == 1:
                xs.append(d["gmacs"][s])
                ys.append(m)
        o = np.argsort(xs)
        ax.plot(np.array(xs)[o], np.array(ys)[o], "-", color=c, lw=1.6,
                label=f"{name}: {' '.join(d['bands'])}")
    ax.set_xscale("log")
    ax.set_xlabel("GMAC per 1000 x 1000 px scene (log); line joins the depth-1 rungs",
                  color=INK, fontsize=9)
    ax.set_ylabel("combined skill (with noise)", color=INK, fontsize=9)
    ax.legend(facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK, fontsize=8, loc="lower right")
    ax.set_title("E-47 / E-67  Size ladders by band set (Sentinel-2, eco_v3 folds)",
                 color=INK_BRIGHT, fontsize=10.5, loc="left")
    fig.text(0.01, -0.02, "Each point: mean over 5 folds x 3 seeds. Paired contrasts in "
             "T_bandsets.csv. Reconstructed (ours).", color=MUTED, fontsize=8.5, ha="left",
             va="top")
    fig.tight_layout()
    fig.savefig(out, dpi=150, facecolor=FIG_BG, bbox_inches="tight")
    plt.close(fig)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--others", nargs="*", default=[],
                    help="NAME=PATH: further sweep_eco_arch runs at other band sets, "
                         "compared with --run")
    ap.add_argument("--out", type=Path, default=ROOT / "docs" / "results" / "P12" / "p12_arch")
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    res = build(args.run)
    if args.others:
        runs = {"mantis_std": args.run}
        runs.update(dict(o.split("=", 1) for o in args.others))
        runs = {k: Path(v) for k, v in runs.items()}
        L = ladders(runs, "mantis_std")
        figure_ladders(L, args.out / "ladders.png")
        with (args.out / "T_ladders.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(L["rows"][0]))
            w.writeheader()
            w.writerows(L["rows"])
        with (args.out / "T_bandsets.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(L["contrasts"][0]))
            w.writeheader()
            w.writerows(L["contrasts"])
        res["ladders"] = {"runs": {k: str(v) for k, v in runs.items()},
                          "contrasts": L["contrasts"],
                          "best": {k: max(d["sizes"], key=lambda s, d=d: mean_se(d["sizes"][s])[0])
                                   for k, d in L["per"].items()}}
        for c in L["contrasts"]:
            print(f"  {c['band_set']} {c['comparison']}: {c['d']:+.4f} "
                  f"[{c['ci'][0]:+.4f}, {c['ci'][1]:+.4f}]")
    figure(res, args.out / "arch.png")
    figure_confusion(res, args.out / "qual_E-47_family_confusion.png")
    with (args.out / "T_arch.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(res["rows"][0]))
        w.writeheader()
        w.writerows(res["rows"])
    with (args.out / "T_compare.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["against", "d", "se", "n_pairs"])
        w.writeheader()
        w.writerows(res["compare"])
    (args.out / "summary.json").write_text(json.dumps(
        {"run": str(args.run), "meta": res["meta"], "best": res["best"], "rows": res["rows"],
         "compare": res["compare"], "ladders": res.get("ladders")}, indent=1, default=str),
        encoding="utf-8")
    for r in res["rows"]:
        print(f"  {r['size']:5s} {r['params']:8d} p {r['gmacs_per_scene']:7.2f} GMAC "
              f"{r['skill']:.4f}  gap {r['gap']:+.4f} +- {r['gap_se']:.4f}"
              f"{'  TIED' if r['tied'] else ''}  Q8 {r['q8_dpu_s']}  FINN {r['finn_s']}"
              f"  Q7 ok {r['q7_meets_budget']}")
    for c in res["compare"]:
        print(f"  8x2 minus {c['against']}: {c['d']:+.4f} +- {c['se']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
