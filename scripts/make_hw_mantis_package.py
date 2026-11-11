"""scripts/make_hw_mantis_package.py

P12e: the Mantis-track onboard model on the two boards (E-48, Mantis track,
A-55), and the cost per input channel (E-27).

Reads, from Fire_Risk_FW (local builds; estimate-only, no synthesis):
- FINN W4A4: hls_projects/_finn/<name>_w4a4[_fps6]/report/
- Vitis AI DPU (Q8): hls_projects/_vai/<name>/vai_summary.json
- hls4ml: runs/eco_convert_mantis/{std,both}_t16.json
and the E-47 size ladders (docs/results/P12/p12_arch/T_ladders.csv) for skill.

Writes docs/results/P12/p12_hw_mantis/: T_hw_mantis.csv, T_channels.csv,
hw_mantis.png, summary.json. The README is written by hand.

    python scripts/make_hw_mantis_package.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FW = ROOT.parent / "Fire_Risk_FW"
OUT = ROOT / "docs" / "results" / "P12" / "p12_hw_mantis"
TILES = 1e6 / 64 ** 2              # A-29: one 1000 x 1000 px scene in 64 px tiles
BUDGET_S, FIT = 43.0, 0.80          # A-29
DPU_OPS_PER_CYCLE, DPU_MHZ = 4096, 300
#: (pack tag, E-47 ladder name, label, input channels)
TRACKS = (("std", "mantis_std", "VNIR stand-in (B2 B3 B4 B7 B8A)", 11),
          ("both", "mantis_both", "stand-in + B11 (SWIR filters)", 16))
SIZES = ("16x1", "32x1", "32x2")
#: E-27: 32x1 at each input count, and the build that holds it
CHANNELS = {3: "e27_in3_32x1", 11: "mantis_std_32x1", 16: "mantis_both_32x1",
            22: "eco_32x1", 96: "e27_in96_32x1"}
BOARDS = ("Q7", "Q8", "Q9")
RESOURCES = ("bram18k", "uram", "lut", "dsp", "ff")
#: The DPU core's OWN footprint (DPUCZDX8G B4096, single core), which the
#: model does not change. AMD PG338 v3.4 resource tables: default block-RAM
#: build 53,540 LUT, 105,008 FF, 257 BRAM36 (= 514 BRAM18K), 562 DSP; the
#: ZCU104 UltraRAM build 52,681 LUT, 104,562 FF, 2 BRAM36, 68 URAM, 562 DSP.
#: Only the Q8 has a DPU target (Vitis AI 2.5); the platform's own logic
#: (interconnect, clocking) is not included.
DPU_B4096 = {"B4096, block RAM build": {"bram18k": 514, "uram": 0, "lut": 53540,
                                        "dsp": 562, "ff": 105008},
             "B4096, UltraRAM build": {"bram18k": 4, "uram": 68, "lut": 52681,
                                       "dsp": 562, "ff": 104562}}

FIG_BG, AX_BG = "#0f1117", "#1a1d27"
SPINE, INK, INK_BRIGHT, MUTED = "#333344", "#cccccc", "#eeeeee", "#8b8b9a"
BLUE, ORANGE, GREEN = "#3987e5", "#d95926", "#199e70"


def _finn(name):
    rep = FW / "hls_projects" / "_finn" / name / "report"
    if not (rep / "estimate_layer_resources.json").exists():
        return None
    r = json.loads((rep / "estimate_layer_resources.json").read_text())["total"]
    fps = json.loads((rep / "estimate_network_performance.json").read_text())[
        "estimated_throughput_fps"]
    return {"bram18k": r.get("BRAM_18K"), "uram": r.get("URAM"), "lut": r.get("LUT"),
            "dsp": r.get("DSP"), "ff": None, "s_per_scene": TILES / fps}


def _dpu(name):
    p = FW / "hls_projects" / "_vai" / name / "vai_summary.json"
    j = json.loads(p.read_text())
    return {"params": j["n_params"], "in_channels": j["input_shape"][1],
            "gop_per_tile": j["workload_ops"] / 1e9, "dpu_subgraphs": j["n_dpu_subgraphs"],
            "cpu_ops": ",".join(j["cpu_op_types"]),
            "s_per_scene": j["workload_ops"] * TILES / (DPU_OPS_PER_CYCLE * DPU_MHZ * 1e6)}


def _share(used, cap):
    """Largest used/capacity over every resource reported. A resource the
    board does not have (the Q7's UltraRAM) counts as infinite if used --
    it used to be skipped, which would have passed such a build silently."""
    best = (0.0, "")
    for k, v in used.items():
        if v is None or k not in cap:
            continue
        s = float("inf") if (cap[k] == 0 and v > 0) else (v / cap[k] if cap[k] else 0.0)
        best = max(best, (s, k))
    return best


def audit(caps: dict) -> list[dict]:
    """Every candidate on every board, every resource: share, and whether it
    passes A-29's 80 % rule and the hard 100 % limit."""
    out = []

    def add(design, flow, used, boards):
        for b in boards:
            for k in RESOURCES:
                v = used.get(k)
                c = caps[b][k]
                if v is None:
                    out.append({"design": design, "flow": flow, "board": b, "resource": k,
                                "used": None, "capacity": c, "share": None,
                                "status": "not estimated"})
                    continue
                s = float("inf") if (c == 0 and v > 0) else (v / c if c else 0.0)
                out.append({"design": design, "flow": flow, "board": b, "resource": k,
                            "used": v, "capacity": c, "share": s,
                            "status": "OVER 100 %" if s > 1 else
                                      ("over 80 %" if s > FIT else "ok")})

    for tag, _, _, inch in TRACKS:
        for size in SIZES:
            for suffix, fold in (("", "minimal fold"), ("_fps6", "~6 tiles/s")):
                f = _finn(f"mantis_{tag}_{size}_w4a4{suffix}")
                if f is not None:
                    add(f"{size}, {inch} inputs, {fold}", "FINN W4A4", f, BOARDS)
    for name, used in DPU_B4096.items():
        add(name + " (any model)", "Vitis AI DPU", used, ("Q8",))
    return out


def rows() -> list[dict]:
    cap = json.loads((FW / "configs" / "boards.json").read_text())["boards"]
    cap = {b: cap[b]["capacity"] for b in BOARDS}
    lad = {(r["band_set"], r["size"]): r for r in csv.DictReader(
        (ROOT / "docs/results/P12/p12_arch/T_ladders.csv").open(encoding="utf-8"))}
    out = []
    for tag, ladder, label, inch in TRACKS:
        h = json.loads((FW / "runs" / "eco_convert_mantis" / f"{tag}_t16.json").read_text())
        h = {f"{r['base_ch']}x{r['depth']}": r for r in (h["rows"] if isinstance(h, dict) else h)}
        for size in SIZES:
            L = lad[(ladder, size)]
            d = _dpu(f"mantis_{tag}_{size}")
            row = {"track": label, "inputs": inch, "size": size, "params": d["params"],
                   "skill": float(L["skill"]), "gap_to_best": float(L["gap_to_own_best"]),
                   "gap_se": float(L["gap_se"]),
                   "dpu_q8_s": d["s_per_scene"], "dpu_subgraphs": d["dpu_subgraphs"],
                   "dpu_cpu_ops": d["cpu_ops"],
                   "hls4ml_q8_bram_pct": float(h[size]["bram_pct"]) * (
                       100 if float(h[size]["bram_pct"]) < 50 else 1)}
            for fold, suffix in (("min", ""), ("fps6", "_fps6")):
                f = _finn(f"mantis_{tag}_{size}_w4a4{suffix}")
                if f is None:
                    continue
                row[f"finn_{fold}_s"] = f["s_per_scene"]
                for b in cap:
                    s, k = _share({kk: f[kk] for kk in RESOURCES}, cap[b])
                    row[f"finn_{fold}_{b}_share"], row[f"finn_{fold}_{b}_binding"] = s, k
            out.append(row)
    return out


def channels() -> list[dict]:
    out = []
    for inch, name in CHANNELS.items():
        f, d = _finn(f"{name}_w4a4"), _dpu(name)
        out.append({"inputs": inch, "params": d["params"], "finn_bram18k": f["bram18k"],
                    "finn_lut": f["lut"], "finn_s_per_scene": f["s_per_scene"],
                    "dpu_gop_per_tile": d["gop_per_tile"], "dpu_q8_s": d["s_per_scene"]})
    return out


def figure(R, C, out: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.2), facecolor=FIG_BG,
                             gridspec_kw={"width_ratios": [1.25, 1]})
    for ax in axes:
        ax.set_facecolor(AX_BG)
        for s in ax.spines.values():
            s.set_color(SPINE)
        ax.tick_params(colors=INK, labelsize=8)
    ax = axes[0]
    ax.set_title("Skill against the Q7's largest resource share", color=INK_BRIGHT,
                 fontsize=10, loc="left")
    for inch, col, lab in ((11, BLUE, "VNIR stand-in, 11 inputs"),
                           (16, ORANGE, "+ B11, 16 inputs")):
        rr = [r for r in R if r["inputs"] == inch]
        x = [100 * r.get("finn_fps6_Q7_share", r["finn_min_Q7_share"]) for r in rr]
        y = [r["skill"] for r in rr]
        ax.errorbar(x, y, yerr=[1.96 * r["gap_se"] for r in rr], fmt="o-", color=col, lw=1.4,
                    ms=7, capsize=3, label=lab)
        for r, xi, yi in zip(rr, x, y, strict=True):
            ax.annotate(r["size"].replace("x", " × "), (xi, yi), textcoords="offset points",
                        xytext=(6, -12), fontsize=7.5, color=MUTED)
    ax.axvline(FIT * 100, color=INK, lw=0.9, ls="--")
    ax.text(FIT * 100 - 1, 0.4285, "80 % rule ", color=MUTED, fontsize=7.5, ha="right")
    ax.set_xlim(0, 100)
    ax.set_ylim(0.403, 0.430)
    ax.set_xlabel("largest Q7 resource share, FINN W4A4 (%)", color=INK, fontsize=8.5)
    ax.set_ylabel("combined skill (E-47 ladder; bars: 1.96 SE of the gap)", color=INK,
                  fontsize=8.5)
    ax.legend(fontsize=7.5, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK, loc="lower right")
    ax = axes[1]
    ax.set_title("E-27: cost of input channels (32 × 1)", color=INK_BRIGHT, fontsize=10,
                 loc="left")
    x = np.array([c["inputs"] for c in C])
    base = C[0]
    for key, lab, col in (("finn_bram18k", "FINN BRAM", BLUE), ("finn_lut", "FINN LUT", GREEN),
                          ("dpu_gop_per_tile", "DPU operations", ORANGE)):
        v = np.array([c[key] for c in C]) / base[key]
        ax.plot(x, v, "o-", color=col, lw=1.8, ms=5, label=lab)
    ax.plot(x, x / x[0], ":", color=MUTED, lw=1, label="linear in inputs")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(x, [str(i) for i in x])
    ax.set_xlabel("input channels", color=INK, fontsize=8.5)
    ax.set_ylabel("cost relative to 3 inputs", color=INK, fontsize=8.5)
    ax.legend(fontsize=7.5, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK, loc="upper left")
    fig.tight_layout()
    fig.text(0.01, -0.09, "Untrained TinyEcologyUNet (four heads), 64 px tiles. Every candidate "
             "meets the 43 s budget: 34.6 s per scene on the Q7 (FINN, width 32 folded for "
             "about 6 tiles/s), 0.03-0.19 s on the Q8 DPU.\nFINN: estimate-only builds, BRAM a "
             "floor (FIFOs unsized), LUTs barely change with folding (likely understated). "
             "Skill from the Sentinel-2 E-47 ladders. Reconstructed (ours).", color=MUTED,
             fontsize=7.5)
    fig.savefig(out / "hw_mantis.png", dpi=150, bbox_inches="tight", facecolor=FIG_BG)


def _csv(path: Path, rows: list[dict]):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, keys)
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    R, C = rows(), channels()
    caps = json.loads((FW / "configs" / "boards.json").read_text())["boards"]
    A = audit({b: caps[b]["capacity"] for b in BOARDS})
    _csv(OUT / "T_resource_audit.csv", A)
    bad = [a for a in A if a["status"] == "OVER 100 %"]
    print(f"audit: {len(A)} rows; over 100 %: {len(bad)}; over 80 %: "
          f"{sum(a['status'] == 'over 80 %' for a in A)}")
    for a in A:
        if a["status"] in ("OVER 100 %", "over 80 %"):
            print("  ", a["status"], a["design"], a["flow"], a["board"], a["resource"],
                  f"{a['share'] * 100:.0f} %")
    _csv(OUT / "T_hw_mantis.csv", R)
    _csv(OUT / "T_channels.csv", C)
    figure(R, C, OUT)
    (OUT / "summary.json").write_text(json.dumps(
        {"candidates": R, "channels": C,
         "audit": {"rows": len(A), "over_100": len(bad),
                   "over_80": [f"{a['design']} | {a['flow']} | {a['board']} | {a['resource']}"
                               for a in A if a["status"] == "over 80 %"]}},
        indent=1, default=float), encoding="utf-8")
    for r in R:
        print(f"{r['inputs']:3} {r['size']}: skill {r['skill']:.4f} ({r['gap_to_best']:+.4f}) | "
              f"DPU {r['dpu_q8_s']:.3f} s | FINN min {r['finn_min_s']:.1f} s Q7 "
              f"{r['finn_min_Q7_share'] * 100:.0f}% | fps6 "
              f"{r.get('finn_fps6_s', float('nan')):.1f} s | hls4ml Q8 BRAM "
              f"{r['hls4ml_q8_bram_pct']:.0f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
