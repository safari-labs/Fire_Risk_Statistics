"""E-48 pre-check: does TinyEcologyUNet convert through the three FPGA flows?

Reads what Fire_Risk_FW wrote locally (nothing here trains or synthesises):

- hls4ml: `runs/eco_convert/*.json` from `scripts/check_eco_convert.py`
  (conversion, C simulation, the validated stream-BRAM law);
- Vitis AI DPU: `hls_projects/_vai/eco_<size>/vai_summary.json` from
  `scripts/vitis_ai.sh inspect --model ecology`;
- FINN: `hls_projects/_finn/eco_<size>_w<b>a<b>/report/` from
  `scripts/export_eco_qonnx.py` + `finn_flow/build_finn.py` (estimate only).

Writes `docs/results/P12/p12_convert/`: T_convert.csv, convert.png, summary.json.

    python scripts/make_convert_package.py --fw ../Fire_Risk_FW
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIZES = ("4x1", "4x2", "4x3", "8x1", "8x2", "8x3",
         "16x1", "16x2", "16x3", "32x1", "32x2", "32x3")
RANKED_SIZE = "8x2"                 # the size eco_v3 ranked bands with (E-47)
SCENE_PX = 1000 * 1000              # A-29: one Mantis scene
TILE = 64                           # DPU and FINN builds
BUDGET_S = 43.0                     # A-29: <= 43 s per scene
FIT_SHARE = 0.80                    # A-29: <= 80 % of every resource
DPU_OPS_PER_CYCLE, DPU_MHZ = 4096, 300   # B4096 on the ZCU104 arch, as make_record

FIG_BG, AX_BG = "#0f1117", "#1a1d27"
SPINE, INK, INK_BRIGHT, MUTED = "#333344", "#cccccc", "#eeeeee", "#8b8b9a"
BLUE, ORANGE, GREEN, AMBER = "#3987e5", "#d95926", "#199e70", "#c98500"
SERIES = {"hls4ml <19,7>, tile 16": BLUE, "FINN W8A8": ORANGE,
          "FINN W4A4": GREEN, "DPU B4096 (peak bound)": AMBER}


def _share(used: dict, cap: dict) -> tuple[float | None, str | None]:
    """Largest used/capacity over the resources both report, and which one."""
    best = (None, None)
    for k, v in used.items():
        if v is None or not cap.get(k):
            continue
        s = v / cap[k]
        if best[0] is None or s > best[0]:
            best = (s, k)
    return best


def load(fw: Path) -> list[dict]:
    boards = json.loads((fw / "configs" / "boards.json").read_text(encoding="utf-8"))["boards"]
    cap = {b: boards[b]["capacity"] for b in ("Q7", "Q8")}
    tiles = SCENE_PX / TILE ** 2
    rows = []

    for path in sorted((fw / "runs" / "eco_convert").glob("*.json")):
        j = json.loads(path.read_text(encoding="utf-8"))
        for r in j["rows"]:
            size = f"{r['base_ch']}x{r['depth']}"
            used = {"bram18k": r.get("bram_total")}
            row = {"flow": "hls4ml", "precision": r["precision"], "mode": j["mode"],
                   "size": size, "params": r["params"], "in_channels": r["in_channels"],
                   "tile": r["tile"], "converted": r["converted"],
                   "bram18k": r.get("bram_total"), "lut": None, "dsp": None,
                   "csim_max_abs_err": r.get("max_abs_err"),
                   "s_per_scene": None, "dpu_subgraphs": None, "cpu_ops": None,
                   "bram_note": "stream law (exact on TinyFireUNet) + ROM estimate"}
            for b in cap:
                row[f"{b}_share"], row[f"{b}_binding"] = _share(used, cap[b])
            rows.append(row)

    for size in SIZES:
        p = fw / "hls_projects" / "_vai" / f"eco_{size}" / "vai_summary.json"
        if not p.exists():
            continue
        j = json.loads(p.read_text(encoding="utf-8"))
        gop = j["workload_ops"]
        rows.append({
            "flow": "DPU", "precision": "INT8", "mode": "raw+indices", "size": size,
            "params": j["n_params"], "in_channels": j["input_shape"][1], "tile": TILE,
            "converted": True, "bram18k": None, "lut": None, "dsp": None,
            "csim_max_abs_err": None,
            "s_per_scene": gop * tiles / (DPU_OPS_PER_CYCLE * DPU_MHZ * 1e6),
            "dpu_subgraphs": j["n_dpu_subgraphs"], "cpu_ops": ",".join(j["cpu_op_types"]),
            "Q7_share": None, "Q7_binding": "no DPU target for Zynq-7000",
            "Q8_share": None, "Q8_binding": "fixed B4096 overlay",
            "bram_note": f"{gop / 1e9:.3f} GOP per {TILE} px tile; DDR "
                         f"{sum(j['ddr_bytes_by_context'].values()) / 1e6:.2f} MB"})

    for size in SIZES:
        for b in (8, 4):
            rep = fw / "hls_projects" / "_finn" / f"eco_{size}_w{b}a{b}" / "report"
            if not (rep / "estimate_layer_resources.json").exists():
                continue
            res = json.loads((rep / "estimate_layer_resources.json")
                             .read_text(encoding="utf-8")).get("total", {})
            perf = json.loads((rep / "estimate_network_performance.json")
                              .read_text(encoding="utf-8"))
            used = {"bram18k": res.get("BRAM_18K"), "lut": res.get("LUT"),
                    "dsp": res.get("DSP")}
            fps = perf.get("estimated_throughput_fps")
            row = {"flow": "FINN", "precision": f"W{b}A{b}", "mode": "raw+indices",
                   "size": size, "params": None, "in_channels": None, "tile": TILE,
                   "converted": True, "bram18k": used["bram18k"], "lut": used["lut"],
                   "dsp": used["dsp"], "csim_max_abs_err": None,
                   "s_per_scene": tiles / fps if fps else None,
                   "dpu_subgraphs": None, "cpu_ops": None,
                   "bram_note": "FLOOR: estimate-only, FIFOs (skip buffers) unsized"}
            for bd in cap:
                row[f"{bd}_share"], row[f"{bd}_binding"] = _share(used, cap[bd])
            rows.append(row)
    params = {r["size"]: r["params"] for r in rows if r["flow"] == "DPU"}
    for r in rows:
        if r["params"] is None:
            r["params"] = params.get(r["size"])
    return rows


def _series(rows, label):
    if label.startswith("hls4ml"):
        pick = [r for r in rows if r["flow"] == "hls4ml" and r["tile"] == 16
                and r["mode"] == "raw+indices"]
    elif label.startswith("FINN"):
        pick = [r for r in rows if r["flow"] == "FINN" and r["precision"] == label[5:]]
    else:
        pick = [r for r in rows if r["flow"] == "DPU"]
    return {r["size"]: r for r in pick}


def figure(rows: list[dict], out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(13, 5.2), facecolor=FIG_BG, sharex=True)
    x = range(len(SIZES))
    panels = (("Q8_share", "Q8 (ZU7EG): share of its binding resource",
               [(FIT_SHARE, "80 % rule"), (1.0, "100 %")], 100.0, "%"),
              ("s_per_scene", "Seconds per 1000 x 1000 px scene",
               [(BUDGET_S, "43 s budget")], 1.0, "s"))
    for ax, (key, title, refs, scale, unit) in zip(axs, panels, strict=True):
        ax.set_facecolor(AX_BG)
        for s in ax.spines.values():
            s.set_color(SPINE)
        ax.tick_params(colors=INK, labelsize=8.5)
        ax.grid(True, color=SPINE, lw=0.6, alpha=0.6)
        ax.set_axisbelow(True)
        ax.set_yscale("log")
        for label, col in SERIES.items():
            s = _series(rows, label)
            pts = [(i, s[z][key] * scale) for i, z in enumerate(SIZES)
                   if z in s and s[z].get(key) is not None]
            if not pts:
                continue
            ax.plot([p[0] for p in pts], [p[1] for p in pts], color=col, lw=2,
                    marker="o", ms=5, label=label)
        for v, lab in refs:
            ax.axhline(v * scale, color=MUTED, lw=1, ls="--")
            ax.text(len(SIZES) - 0.6, v * scale, lab, color=MUTED, fontsize=8,
                    va="bottom" if v >= 1 or len(refs) == 1 else "top", ha="right")
        ax.axvline(SIZES.index(RANKED_SIZE), color=SPINE, lw=6, alpha=0.5, zorder=0)
        ax.set_xticks(list(x), SIZES)
        ax.set_xlabel("TinyEcologyUNet rung (base_ch x depth); shaded: the size bands "
                      "were ranked with", color=INK, fontsize=8.5)
        ax.set_ylabel(unit, color=INK, fontsize=9)
        ax.set_title(title, color=INK_BRIGHT, fontsize=10.5, loc="left", pad=6)
    h, lab = axs[0].get_legend_handles_labels()
    h2, lab2 = axs[1].get_legend_handles_labels()
    for hh, ll in zip(h2, lab2, strict=True):
        if ll not in lab:
            h.append(hh)
            lab.append(ll)
    leg = fig.legend(h, lab, loc="upper center", ncol=4, frameon=False, fontsize=9,
                     bbox_to_anchor=(0.5, 1.04))
    for t in leg.get_texts():
        t.set_color(INK)
    fig.text(0.01, -0.02,
             "Untrained P6 four-head network, 8 Sentinel-2 bands in raw + indices "
             "(22 inputs; the index stage is not in these graphs). hls4ml: converted and "
             "C-simulated, BRAM from the stream law. FINN: estimate-only build, BRAM is a "
             "floor; at minimal folding W8A8 and W4A4 run at the same rate, so their seconds "
             "overlap. DPU: one subgraph per rung; seconds assume the B4096's peak, so they "
             "are a lower bound. Reconstructed (ours).",
             color=MUTED, fontsize=8.5, ha="left", va="top", wrap=True)
    fig.tight_layout()
    fig.savefig(out, dpi=150, facecolor=FIG_BG, bbox_inches="tight")
    plt.close(fig)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--fw", type=Path, default=ROOT.parent / "Fire_Risk_FW")
    ap.add_argument("--out", type=Path, default=ROOT / "docs" / "results" / "P12/p12_convert")
    args = ap.parse_args(argv)
    rows = load(args.fw)
    if not rows:
        raise SystemExit(f"nothing to read under {args.fw}")
    args.out.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with (args.out / "T_convert.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 6) if isinstance(v, float) and math.isfinite(v)
                            else v) for k, v in r.items()})
    figure(rows, args.out / "convert.png")
    summary = {}
    for flow in ("hls4ml", "FINN", "DPU"):
        f = [r for r in rows if r["flow"] == flow]
        summary[flow] = {
            "converted": f"{sum(bool(r['converted']) for r in f)}/{len(f)}",
            "fits_q8_80pct": sorted({f"{r['size']} {r['precision']} t{r['tile']}"
                                     for r in f if (r.get("Q8_share") or 9) <= FIT_SHARE}),
            "fits_q7_80pct": sorted({f"{r['size']} {r['precision']} t{r['tile']}"
                                     for r in f if (r.get("Q7_share") or 9) <= FIT_SHARE}),
            "within_budget": sorted({f"{r['size']} {r['precision']}" for r in f
                                     if r.get("s_per_scene") is not None
                                     and r["s_per_scene"] <= BUDGET_S})}
    (args.out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    for flow, s in summary.items():
        print(flow, s["converted"], "| Q8<=80%:", len(s["fits_q8_80pct"]),
              "| Q7<=80%:", len(s["fits_q7_80pct"]), "| <=43 s:", len(s["within_budget"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
