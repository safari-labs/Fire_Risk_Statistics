"""scripts/make_sensor_options.py

E-66, P12b: what each Dragonfly Mantis mode would offer (PLAN_NEXT section 6).

Reads the sensors_v1 run (Fire_Risk_FW sweep_hs.sh on the P12/p12_sensors grid) and
hs_v4, which ran on the same pack, folds and seeds, so every row pairs with
every other by (outer fold, seed). Rows from sensors_v1 are preferred; until
its references arm lands, hs_v4's scores of the same band sets stand in,
labelled "(hs_v4)". Partial runs are read as they are: each row says how many
tasks it holds, and a paired contrast uses only the tasks both rows hold.

    python scripts/make_sensor_options.py --run narval_results/sensors_v1/<id>

Writes docs/results/P12/p12_sensors/: T_sensors.csv, T_predictions.csv,
T_fixed_filters.csv (with --fixed), sensors.png, qual_E-66_sensor_bands.png, summary.json.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_band_options import load_hs, mean_se, paired  # noqa: E402

from safari_bands.config.loader import load_atmospheric_windows, project_root  # noqa: E402

ROOT = project_root()
HS = ROOT / "narval_results" / "hs_v4" / "20261102-1959"
GRID = ROOT.parent / "Fire_Risk_FW" / "configs" / "noise" / "p12_sensors_grid.json"
VENDOR = ROOT / "config" / "vendors" / "dragonfly.yaml"

FIG_BG, AX_BG = "#0f1117", "#1a1d27"
SPINE, INK, INK_BRIGHT, MUTED = "#333344", "#cccccc", "#eeeeee", "#8b8b9a"
BLUE, ORANGE, GREEN, AMBER, PINK = "#3987e5", "#d95926", "#199e70", "#c98500", "#d55181"

#: (row key, label, mode for the datasheet columns, colour, sources in order of
#: preference: (run, arm, set); run "s" = sensors_v1, "h" = hs_v4).
ROWS = [
    ("rgb", "RGB snapshot (DFA blue, green, red)", "rgb", MUTED,
     [("s", "references", "dfa_rgb")]),
    ("ms_std", "MS, DFA standard block as published", "multispectral", AMBER,
     [("s", "references", "dfa_ms_standard")]),
    ("ms_std_clean", "MS, standard block, rule-7-clean bands", "multispectral", AMBER,
     [("s", "references", "dfa_ms_standard_clean")]),
    ("ms_custom", "MS, custom block (490-865 nm)", "multispectral", BLUE,
     [("s", "references", "sensor_mantis_vnir6"), ("h", "references", "sensor_mantis_vnir6")]),
    ("hs_all", "HS, all 81 surface channels", "hyperspectral", PINK,
     [("s", "references", "dfa_hs_all")]),
    ("hs_select6", "HS, best 6 chosen in orbit", "hyperspectral", PINK,
     [("s", "dfa_hs_select", "k6")]),
    ("swir_alone", "SWIR alone, best 4 DFA filters", "swir", GREEN,
     [("s", "dfa_swir_alone", "k4")]),
    ("ms_custom_swir", "MS custom + best 4 DFA SWIR filters", "multispectral+swir", BLUE,
     [("s", "dfa_swir_on_custom", "k4")]),
    ("ms_std_swir", "MS standard + best 4 DFA SWIR filters", "multispectral+swir", AMBER,
     [("s", "dfa_swir_on_standard", "k4")]),
    ("ms_custom_swir_cfg", "MS custom + SWIR at configured slots (1240-1680)",
     "multispectral+swir", BLUE, [("h", "references", "sensor_mantis_ms_plus_swir")]),
    ("std_nearest", "MS standard + DFA L4 L6 L9 L11 (fixed)", "multispectral+swir", AMBER,
     [("f", "references", "dfa_standard_nearest")]),
    ("custom_nearest", "MS custom + DFA L4 L6 L9 L11 (fixed)", "multispectral+swir", BLUE,
     [("f", "references", "dfa_custom_nearest")]),
    ("custom_consensus", "MS custom + DFA L2 L6 L9 L11 (fixed)", "multispectral+swir", BLUE,
     [("f", "references", "dfa_custom_consensus")]),
    ("swir_nearest_alone", "DFA L4 L6 L9 L11 alone (fixed)", "swir", GREEN,
     [("f", "references", "dfa_swir_nearest_alone")]),
    ("fixed_vnir", "anchor: fixed six VNIR bands", None, MUTED,
     [("s", "references", "config_c/VNIR"), ("h", "references", "config_c/VNIR")]),
    ("s2", "anchor: Sentinel-2, 12 bands", None, MUTED,
     [("s", "references", "sentinel2_p6_12band"), ("h", "references", "sentinel2_p6_12band")]),
]

#: E-66's registered predictions (2026-11-06): (a, b, kind). "above": a - b CI
#: above 0; "within": |a - b| within one paired SE (HS no better than MS).
#: The follow-up's contrasts (sensors_fixed, 2026-11-06): DFA's SWIR filters as FIXED sets.
#: Not registered predictions; reported with their paired 95 % CI.
FOLLOWUP = [
    ("SWIR on the standard block", "std_nearest", "ms_std"),
    ("SWIR on the custom block", "custom_nearest", "ms_custom"),
    ("DFA nearest filters vs the configured slots", "custom_nearest", "ms_custom_swir_cfg"),
    ("consensus filters vs nearest filters", "custom_consensus", "custom_nearest"),
    ("custom vs standard block, both with SWIR", "custom_nearest", "std_nearest"),
    ("fixed vs searched filters, custom block", "custom_nearest", "ms_custom_swir"),
    ("fixed vs searched filters, standard block", "std_nearest", "ms_std_swir"),
    ("MS standard alone vs fixed SWIR alone", "ms_std", "swir_nearest_alone"),
]

PREDICTIONS = [
    ("1 custom MS beats standard MS", "ms_custom", "ms_std", "above"),
    ("2 MS custom beats SWIR alone", "ms_custom", "swir_alone", "above"),
    ("3 HS all within one SE of MS custom", "hs_all", "ms_custom", "within"),
    ("4 MS custom + SWIR beats MS custom", "ms_custom_swir", "ms_custom", "above"),
    ("5 RGB below every MS row", "rgb", "ms_std_clean", "below"),
]


def _row_data(sources, runs):
    for run, arm, name in sources:
        d = runs[run]["sets"].get((arm, name))
        if d:
            return {t: v for t, (v, _) in d.items()}, run, next(iter(d.values()))[1]
    return None, None, None


def _datasheet(mode):
    ds = yaml.safe_load(VENDOR.read_text(encoding="utf-8"))["mantis_datasheet"]
    if mode is None:
        return {}
    m = ds["modes"].get(mode.split("+")[0], {})
    gsd = m.get("gsd_m_at_500km", "")
    if isinstance(gsd, dict):
        gsd = gsd.get("ms", "")
    return {"gsd_m": gsd, "swath_km": m.get("swath_km_at_500km", ""),
            "power_w": ds["power_w"]["imaging_max"], "size": "1U", "trl": ds["trl"],
            "simultaneous": "MS + SWIR on one head (A-20)" if "+" in mode else ""}


SOURCE = {"s": "sensors_v1", "h": "hs_v4", "f": "sensors_fixed"}


def build(run: Path, fixed: Path | None = None) -> dict:
    runs = {"s": load_hs(run), "h": load_hs(HS)}
    if fixed is not None:
        runs["f"] = load_hs(fixed)
    for key in [k for k in runs if k != "h"]:
        bad = {t for t, px in runs[key].get("pixels", {}).items()
               if px != runs["h"].get("pixels", {}).get(t)}
        if bad:
            print(f"  {len(bad)} {SOURCE[key]} tasks ran on other pixels than hs_v4, "
                  f"dropped: {sorted(bad)}")
            runs[key]["sets"] = {k: {t: v for t, v in d.items() if t not in bad}
                                 for k, d in runs[key]["sets"].items()}
    rows = []
    for key, label, mode, col, sources in ROWS:
        per, src, bands = _row_data(sources, runs)
        if per is None:
            rows.append({"key": key, "label": label, "n_tasks": 0, "source": "pending",
                         "colour": col})
            continue
        m, se = mean_se(per)
        rows.append({"key": key, "label": label + (" (hs_v4)" if src == "h" else ""),
                     "n_tasks": len(per), "folds": sorted({f for f, _ in per}),
                     "mean": m, "se": se, "bands": bands, "colour": col,
                     "source": SOURCE[src], "per": per,
                     **_datasheet(mode)})
    by = {r["key"]: r for r in rows}
    preds = []
    for text, a, b, kind in PREDICTIONS:
        ra, rb = by[a], by[b]
        if not ra.get("per") or not rb.get("per"):
            preds.append({"prediction": text, "verdict": "PENDING", "n_pairs": 0})
            continue
        d, se, n = paired(ra["per"], rb["per"])
        nf = len({f for f, _ in set(ra["per"]) & set(rb["per"])})
        if n == 0:
            preds.append({"prediction": text, "verdict": "PENDING (no shared tasks)",
                          "n_pairs": 0})
            continue
        lo, hi = d - 1.96 * se, d + 1.96 * se
        if kind == "above":
            v = "SUPPORTED" if lo > 0 else "REFUTED"      # registered: CI reaching 0 refutes
        elif kind == "below":
            v = "SUPPORTED" if hi < 0 else "REFUTED"
        else:
            v = "SUPPORTED" if d <= se else "REFUTED"
        if nf < 5:
            v += f" (provisional: {nf} of 5 folds)"
        preds.append({"prediction": text, "a": a, "b": b, "d": d, "se": se,
                      "ci": [lo, hi], "n_pairs": n, "n_folds": nf, "verdict": v})
    follow = []
    for text, a, b in FOLLOWUP:
        if by[a].get("per") and by[b].get("per"):
            d, se, n = paired(by[a]["per"], by[b]["per"])
            follow.append({"contrast": text, "a": a, "b": b, "d": d, "se": se,
                           "ci": [d - 1.96 * se, d + 1.96 * se], "n_pairs": n})
    repro = []
    if "f" in runs:
        for name in ("sensor_mantis_vnir6", "dfa_ms_standard", "sensor_mantis_ms_plus_swir"):
            new = runs["f"]["sets"].get(("references", name))
            old = (runs["s"]["sets"].get(("references", name))
                   or runs["h"]["sets"].get(("references", name)))
            if new and old:
                a = {t: v for t, (v, _) in new.items()}
                b = {t: v for t, (v, _) in old.items()}
                d, se, n = paired(a, b)
                repro.append({"set": name, "d": d, "max_abs": max(abs(a[t] - b[t]) for t in
                              set(a) & set(b)), "n_pairs": n})
    return {"rows": rows, "predictions": preds, "followup": follow, "repro": repro}


def filter_choices(run: Path) -> dict:
    """Per search arm: how many of its searches hold each band in the final set,
    and how often each band was picked first."""
    out = {}
    for arm_dir in sorted(p for p in run.iterdir() if p.is_dir() and p.name.startswith("dfa_")):
        sets, first = [], {}
        for f in sorted(arm_dir.glob("f*s*/search.json")):
            steps = json.loads(f.read_text(encoding="utf-8"))[arm_dir.name]["steps"]
            sets.append({s["added"] for s in steps})
            first[steps[0]["added"]] = first.get(steps[0]["added"], 0) + 1
        count = {}
        for s in sets:
            for b in s:
                count[b] = count.get(b, 0) + 1
        out[arm_dir.name] = {"n": len(sets),
                             "count": dict(sorted(count.items(), key=lambda x: -x[1])),
                             "first": first}
    return out


def figure(res, out: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rows = [r for r in res["rows"] if r.get("per")]
    ref = next((r for r in rows if r["key"] == "ms_custom"), None)
    fig, ax = plt.subplots(figsize=(10, 0.45 * len(rows) + 1.6), facecolor=FIG_BG)
    ax.set_facecolor(AX_BG)
    for s in ax.spines.values():
        s.set_color(SPINE)
    ax.tick_params(colors=INK, labelsize=8.5)
    ax.grid(True, axis="x", color=SPINE, lw=0.6, alpha=0.6)
    for i, r in enumerate(rows):
        y = len(rows) - 1 - i
        if ref is not None and r is not ref:
            d, se, n = paired(r["per"], ref["per"])
            if n:
                ax.plot([d - 1.96 * se, d + 1.96 * se], [y, y], color=r["colour"], lw=2)
                ax.plot(d, y, "o", color=r["colour"], ms=7)
                ax.text(d + 1.96 * se + 0.002, y, f"{d:+.3f}  ({n} tasks)", color=INK,
                        fontsize=7.5, va="center")
                continue
        ax.plot(0, y, "s" if r is ref else "x", color=r["colour"], ms=7)
        ax.text(0.002, y, f"{r['mean']:.3f} ({r['n_tasks']} tasks)"
                if r is ref else "no shared task yet", color=INK, fontsize=7.5, va="center")
    ax.axvline(0, color=MUTED, lw=1, ls="--")
    ax.set_yticks(range(len(rows)), [r["label"] for r in rows][::-1])
    ax.set_xlabel("combined skill minus MS custom (paired by fold and seed), 95 % CI",
                  color=INK, fontsize=9)
    ax.set_title("E-66  Each Mantis mode against the custom MS block", color=INK_BRIGHT,
                 fontsize=10.5, loc="left")
    fig.text(0.01, -0.02, "AVIRIS-NG (aviris_v4), SCANFI labels, raw + indices, placeholder "
             "noise (A-37), so spectral content only. Rows marked (hs_v4) are hs_v4's score of "
             "the same band set on the same folds. Partial runs: each point uses only the "
             "tasks both rows hold. Reconstructed (ours).", color=MUTED, fontsize=8.5,
             ha="left", va="top", wrap=True)
    fig.tight_layout()
    fig.savefig(out, dpi=150, facecolor=FIG_BG, bbox_inches="tight")
    plt.close(fig)


def figure_bands(res, out: Path):
    """Qualitative view: each row's bands on the spectrum, rule 7's regions shaded."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rows = [r for r in res["rows"] if r.get("bands")]
    fig, ax = plt.subplots(figsize=(12, 0.42 * len(rows) + 1.6), facecolor=FIG_BG)
    ax.set_facecolor(AX_BG)
    for s in ax.spines.values():
        s.set_color(SPINE)
    ax.tick_params(colors=INK, labelsize=8)
    for reg in load_atmospheric_windows().forbidden_regions:
        ax.axvspan(*reg.range_nm, color=MUTED, alpha=0.18, lw=0)
    for i, r in enumerate(rows):
        y = len(rows) - 1 - i
        for b in r["bands"]:
            c, w = (float(x) for x in b.split("@")[0].split("/"))
            ax.add_patch(plt.Rectangle((c - w / 2, y - 0.35), w, 0.7, color=r["colour"],
                                       lw=0, alpha=0.9))
    ax.set_yticks(range(len(rows)), [r["label"] for r in rows][::-1])
    ax.set_xlim(400, 2500)
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.set_xlabel("wavelength (nm); bar width = band FWHM; grey: forbidden atmospheric "
                  "regions (rule 7)", color=INK, fontsize=9)
    ax.set_title("E-66  The bands each Mantis mode carries (search rows: the most common "
                 "set)", color=INK_BRIGHT, fontsize=10.5, loc="left")
    fig.tight_layout()
    fig.savefig(out, dpi=150, facecolor=FIG_BG, bbox_inches="tight")
    plt.close(fig)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--fixed", type=Path, default=None,
                    help="the sensors_fixed run (DFA filters as fixed sets)")
    ap.add_argument("--out", type=Path, default=ROOT / "docs" / "results" / "P12/p12_sensors")
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    res = build(args.run, args.fixed)
    figure(res, args.out / "sensors.png")
    figure_bands(res, args.out / "qual_E-66_sensor_bands.png")
    keys = ["key", "label", "source", "n_tasks", "mean", "se", "gsd_m", "swath_km",
            "power_w", "size", "trl", "simultaneous", "bands"]
    with (args.out / "T_sensors.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in res["rows"]:
            w.writerow({**r, "bands": " ".join(r.get("bands") or [])})
    with (args.out / "T_predictions.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["prediction", "verdict", "d", "se", "ci",
                                           "n_pairs", "n_folds"], extrasaction="ignore")
        w.writeheader()
        w.writerows(res["predictions"])
    summ = {"run": str(args.run), "hs_v4": str(HS),
            "rows": [{k: v for k, v in r.items() if k not in ("per", "colour")}
                     for r in res["rows"]],
            "predictions": res["predictions"], "followup": res["followup"],
            "fixed_run": str(args.fixed) if args.fixed else None,
            "anchor_reproduction": res["repro"], "choices": filter_choices(args.run)}
    with (args.out / "T_fixed_filters.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["contrast", "a", "b", "d", "se", "ci", "n_pairs"])
        w.writeheader()
        w.writerows(res["followup"])
    with (args.out / "T_filters.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["arm", "band", "searches_holding_it", "searches", "chosen_first"])
        for arm, c in summ["choices"].items():
            for band, n in c["count"].items():
                w.writerow([arm, band, n, c["n"], c["first"].get(band, 0)])
    (args.out / "summary.json").write_text(json.dumps(summ, indent=1, default=str),
                                           encoding="utf-8")
    for r in res["rows"]:
        print(f"  {r['label'][:52]:52s} {r['n_tasks']:>2} tasks "
              + (f"{r['mean']:.4f} +- {r['se']:.4f}" if r.get("per") else "pending"))
    for f in res["followup"]:
        print(f"  {f['contrast']}: {f['d']:+.4f} [{f['ci'][0]:+.4f}, {f['ci'][1]:+.4f}]")
    for r in res["repro"]:
        print(f"  anchor {r['set']}: rerun - original {r['d']:+.5f}, max |diff| {r['max_abs']:.5f}")
    for p in res["predictions"]:
        extra = (f" d {p['d']:+.4f} [{p['ci'][0]:+.4f}, {p['ci'][1]:+.4f}], {p['n_pairs']} "
                 f"pairs" if "d" in p else "")
        print(f"  {p['prediction']}: {p['verdict']}{extra}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
