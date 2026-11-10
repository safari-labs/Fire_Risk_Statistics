"""scripts/make_vnir_swir_package.py

E-67, P12d: the Mantis VNIR camera's model against the Mantis SWIR camera's model (and
both together) at every model size, on AVIRIS-NG (Fire_Risk_FW run_hs_arch.py, hs_v4's
folds and seeds). Prediction (4), the Sentinel-2 half, is read from the P12c package
(make_arch_package.py --others mantis_both=...).

    python scripts/make_vnir_swir_package.py --run narval_results/hs_arch/<id>

Writes docs/results/P12/p12_vnir_swir/: T_ladder.csv, T_contrasts.csv, T_predictions.csv,
vnir_swir.png, qual_E-67_family_confusion.png, summary.json.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_band_options import mean_se, paired  # noqa: E402

from safari_bands.config.loader import project_root  # noqa: E402

ROOT = project_root()
SENSORS_FIXED = ROOT / "narval_results" / "sensors_fixed" / "20261106-1645" / "references"
ARCH = ROOT / "docs" / "results" / "P12" / "p12_arch" / "summary.json"
CAMERAS = [("dfa_ms_standard", "VNIR (standard block)", "#3987e5"),
           ("dfa_swir_nearest_alone", "SWIR (L4 L6 L9 L11)", "#199e70"),
           ("dfa_standard_nearest", "VNIR + SWIR", "#d95926")]
VNIR, SWIR, BOTH = (c for c, _, _ in CAMERAS)
REF_SIZE = "64x2"
FIG_BG, AX_BG = "#0f1117", "#1a1d27"
SPINE, INK, INK_BRIGHT, MUTED = "#333344", "#cccccc", "#eeeeee", "#8b8b9a"


def load(run: Path):
    """{(set, size, noisy): {(fold, seed): metrics}} and {(set, size): cost}."""
    rows, cost = {}, {}
    for f in sorted(run.glob("f*s*/eval.jsonl")):
        r0 = json.loads((f.parent / "result.json").read_text(encoding="utf-8"))
        t = (r0["fold"], r0["seed"])
        for line in f.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r["mode"] != "raw+indices":
                continue
            rows.setdefault((r["set"], r["size"], r["noisy"]), {})[t] = r["metrics"]
            cost[(r["set"], r["size"])] = {"params": r["params"], "macs_per_px": r["macs_per_px"],
                                           "in_channels": r["in_channels"]}
    return rows, cost


def anchor(rows) -> dict:
    """The 64x2 rows must reproduce sensors_fixed's references exactly."""
    ref = {}
    for f in SENSORS_FIXED.glob("f*s*/eval.jsonl"):
        r0 = json.loads((f.parent / "result.json").read_text(encoding="utf-8"))
        t = (r0["fold"], r0["seed"])
        for line in f.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r["mode"] == "raw+indices" and r["noisy"]:
                ref.setdefault(r["set"], {})[t] = r["metrics"]["skill_combined"]
    out = {}
    for s, _, _ in CAMERAS:
        a = {t: m["skill_combined"] for t, m in rows[(s, REF_SIZE, True)].items()}
        common = set(a) & set(ref.get(s, {}))
        out[s] = max((abs(a[t] - ref[s][t]) for t in common), default=float("nan"))
    return out


def build(run: Path) -> dict:
    rows, cost = load(run)
    sizes = sorted({z for _, z, _ in rows}, key=lambda z: cost[(VNIR, z)]["params"])
    sk = {k: {t: m["skill_combined"] for t, m in v.items()} for k, v in rows.items()}
    ladder = []
    for s, label, _ in CAMERAS:
        best = max(sizes, key=lambda z: mean_se(sk[(s, z, True)])[0])
        for z in sizes:
            per = sk[(s, z, True)]
            m, se = mean_se(per)
            g, gse, _ = paired(per, sk[(s, REF_SIZE, True)])
            ms = rows[(s, z, True)].values()
            ladder.append({
                "camera": label, "set": s, "size": z, **cost[(s, z)],
                "skill": m, "se": se, "skill_noise_free": mean_se(sk[(s, z, False)])[0],
                "vs_64x2": g, "vs_64x2_se": gse, "best": z == best,
                "rmse_pc": float(np.mean([x["rmse_pc"] for x in ms])),
                "rmse_closure": float(np.mean([x["rmse_closure"] for x in ms])),
                "rmse_height": float(np.mean([x["rmse_height"] for x in ms])),
                "family_ba": float(np.mean([x["balanced_acc_family"] for x in ms]))})
    contrasts = []
    for z in sizes:
        for name, a, b in (("VNIR - SWIR", VNIR, SWIR), ("VNIR+SWIR - VNIR", BOTH, VNIR),
                           ("VNIR+SWIR - SWIR", BOTH, SWIR)):
            d, se, n = paired(sk[(a, z, True)], sk[(b, z, True)])
            contrasts.append({"size": z, "contrast": name, "d": d, "se": se,
                              "ci": [d - 1.96 * se, d + 1.96 * se], "n_pairs": n})
    by = {(c["size"], c["contrast"]): c for c in contrasts}
    largest = sizes[-1]
    preds = []
    lows = [by[(z, "VNIR - SWIR")]["ci"][0] for z in sizes]
    preds.append({"prediction": "1. VNIR beats SWIR alone at every size",
                  "result": f"lowest CI bound over sizes {min(lows):+.4f}",
                  "verdict": "SUPPORTED" if min(lows) > 0 else "REFUTED"})
    c = by[(largest, "VNIR+SWIR - VNIR")]
    preds.append({"prediction": f"2. VNIR + SWIR beats VNIR at the largest size ({largest})",
                  "result": f"{c['d']:+.4f} [{c['ci'][0]:+.4f}, {c['ci'][1]:+.4f}]",
                  "verdict": "SUPPORTED" if c["ci"][0] > 0 else "REFUTED"})
    parts = []
    ok = True
    for s, label, _ in CAMERAS:
        r = next(x for x in ladder if x["set"] == s and x["best"])
        parts.append(f"{label}: best {r['size']} {r['vs_64x2']:+.4f}")
        ok &= r["vs_64x2"] <= 0.005
    preds.append({"prediction": "3. each camera's best size within 0.005 of 64x2",
                  "result": "; ".join(parts), "verdict": "SUPPORTED" if ok else "REFUTED"})
    s2 = None
    if ARCH.exists():
        lad = (json.loads(ARCH.read_text(encoding="utf-8")).get("ladders") or {})
        s2 = next((x for x in lad.get("contrasts", []) if x["band_set"] == "mantis_both"
                   and x["comparison"] == "best rung vs best rung"), None)
    if s2:
        preds.append({"prediction": "4. adding B11 to the Sentinel-2 VNIR stand-in raises the "
                                    "best rung's skill",
                      "result": f"{s2['d']:+.4f} [{s2['ci'][0]:+.4f}, {s2['ci'][1]:+.4f}] "
                                f"({s2['a_size']} vs {s2['b_size']})",
                      "verdict": "SUPPORTED" if s2["ci"][0] > 0 else "REFUTED"})
    confusion = {s: np.sum([np.array(m["confusion_family"], float)
                            for m in rows[(s, REF_SIZE, True)].values()], axis=0).tolist()
                 for s, _, _ in CAMERAS}
    return {"sizes": sizes, "ladder": ladder, "contrasts": contrasts, "predictions": preds,
            "anchor": anchor(rows), "confusion": confusion}


def _axes(ax):
    ax.set_facecolor(AX_BG)
    for s in ax.spines.values():
        s.set_color(SPINE)
    ax.tick_params(colors=INK, labelsize=8.5)
    ax.grid(True, color=SPINE, lw=0.6, alpha=0.6)


def figure(res, out: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.8), facecolor=FIG_BG,
                                 gridspec_kw={"width_ratios": [1.2, 1]})
    for ax in (a1, a2):
        _axes(ax)
    for s, label, col in CAMERAS:
        rr = [r for r in res["ladder"] if r["set"] == s]
        rr.sort(key=lambda r: r["params"])
        x = [r["params"] for r in rr]
        y = np.array([r["skill"] for r in rr])
        a1.plot(x, y, "-o", color=col, lw=1.8, ms=5, label=label)
        for r in rr:
            a1.annotate(r["size"], (r["params"], r["skill"]), textcoords="offset points",
                        xytext=(3, 5), fontsize=6.5, color=MUTED)
    a1.set_xscale("log")
    a1.set_xlabel("model parameters (log)", color=INK, fontsize=9)
    a1.set_ylabel("combined skill (with noise)", color=INK, fontsize=9)
    a1.legend(facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK, fontsize=8, ncol=3,
              loc="upper center", bbox_to_anchor=(0.5, -0.15))
    a1.set_title("Skill at every model size", color=INK_BRIGHT, fontsize=10, loc="left")
    names = [("VNIR - SWIR", "#3987e5"), ("VNIR+SWIR - VNIR", "#d95926")]
    for k, (name, col) in enumerate(names):
        cc = [c for c in res["contrasts"] if c["contrast"] == name]
        for i, c in enumerate(cc):
            y = i + (k - 0.5) * 0.25
            a2.plot(c["ci"], [y, y], color=col, lw=2)
            a2.plot(c["d"], y, "o", color=col, ms=5, label=name if i == 0 else None)
    a2.axvline(0, color=MUTED, lw=1, ls="--")
    a2.set_yticks(range(len(res["sizes"])), res["sizes"])
    a2.set_xlabel("paired difference in combined skill, 95 % CI", color=INK, fontsize=9)
    a2.legend(facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK, fontsize=8, loc="lower right")
    a2.set_title("Paired contrasts by size", color=INK_BRIGHT, fontsize=10, loc="left")
    fig.suptitle("E-67  The Mantis VNIR and SWIR cameras' models at every size (AVIRIS-NG, "
                 "hs_v4 folds and seeds)", color=INK_BRIGHT, fontsize=11, x=0.01, ha="left")
    fig.text(0.01, -0.03, "Per-pixel networks, raw + indices, placeholder noise (A-37), SCANFI "
             "labels, 5 outer folds x 3 seeds. 64x2 reproduces sensors_fixed exactly. "
             "Reconstructed (ours).", color=MUTED, fontsize=8.5, ha="left", va="top")
    fig.tight_layout()
    fig.savefig(out, dpi=150, facecolor=FIG_BG, bbox_inches="tight")
    plt.close(fig)


def figure_confusion(res, out: Path):
    """Qualitative view: where each camera's model confuses the fuel families (64x2)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    cls = ["C", "D", "M", "O", "S", "NF", "WA"]
    keep = [i for i in range(len(cls))
            if any(np.asarray(res["confusion"][s])[i].sum() > 0 for s, _, _ in CAMERAS)]
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.7), facecolor=FIG_BG)
    for ax, (s, label, _) in zip(axes, CAMERAS, strict=True):
        ax.set_facecolor(AX_BG)
        m = np.asarray(res["confusion"][s])
        k = min(m.shape[0], len(cls))
        idx = [i for i in keep if i < k]
        m = m[np.ix_(idx, idx)]
        m = m / np.maximum(m.sum(axis=1, keepdims=True), 1)
        ax.imshow(m, cmap="Blues", vmin=0, vmax=1)
        for i in range(len(idx)):
            for j in range(len(idx)):
                ax.text(j, i, f"{m[i, j]:.2f}", ha="center", va="center", fontsize=6.5,
                        color="white" if m[i, j] > 0.5 else "#0f1117")
        ax.set_xticks(range(len(idx)), [cls[i] for i in idx])
        ax.set_yticks(range(len(idx)), [cls[i] for i in idx])
        ax.tick_params(colors=INK, labelsize=8)
        ax.set_title(label, color=INK_BRIGHT, fontsize=9.5)
        ax.set_xlabel("predicted", color=INK, fontsize=8)
    axes[0].set_ylabel("true (SCANFI)", color=INK, fontsize=8)
    fig.suptitle("E-67  Fuel-family confusion by camera (64x2, rows sum to 1)",
                 color=INK_BRIGHT, fontsize=10.5, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(out, dpi=150, facecolor=FIG_BG, bbox_inches="tight")
    plt.close(fig)


def _csv(path: Path, rows: list[dict]):
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--out", type=Path,
                    default=ROOT / "docs" / "results" / "P12" / "p12_vnir_swir")
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    res = build(args.run)
    figure(res, args.out / "vnir_swir.png")
    figure_confusion(res, args.out / "qual_E-67_family_confusion.png")
    _csv(args.out / "T_ladder.csv", res["ladder"])
    _csv(args.out / "T_contrasts.csv", res["contrasts"])
    _csv(args.out / "T_predictions.csv", res["predictions"])
    (args.out / "summary.json").write_text(json.dumps(
        {"run": str(args.run), **{k: v for k, v in res.items() if k != "confusion"}},
        indent=1, default=str), encoding="utf-8")
    print("anchor (max |64x2 - sensors_fixed|):", res["anchor"])
    for p in res["predictions"]:
        print(f"  {p['prediction']}: {p['verdict']}  ({p['result']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
