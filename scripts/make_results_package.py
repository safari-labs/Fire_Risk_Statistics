"""scripts/make_results_package.py

The interpretation package for a result-producing phase (plan P11): figures
(PNG), tables (Markdown and CSV) into docs/results/<phase>/, read straight
from the run directory the phase's evaluator wrote. Every figure states the
experiment, what it tests and the n behind it.

    python scripts/make_results_package.py --phase P2 --run runs/<ts>_cffdrs_r0

P2 (R0, the CFFDRS reference without learning; E-32, E-33, E-21):
    inventories.png   within-patch AUC by fuel inventory, per R0 output
    weather.png       between-patch AUC and paired win rate of each FWI code
    vintage.png       within-patch AUC against inventory age (E-21)
    fuel_types.png    burn rate vs FBP intensity by fuel type
    tiles.png         NBAC, fuel and intensity maps on four seeded fire tiles
    tables.md         T-inventory, T-weather, T-fuel, T-vintage (+ CSVs)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent

# House surfaces and ink (make_result_figures.py); categorical slots are the
# reference palette's dark steps, validated against this surface for the P1
# figures (worst adjacent CVD delta-E above 8).
FIG_BG, AX_BG = "#0f1117", "#1a1d27"
SPINE, INK, INK_BRIGHT, MUTED = "#333344", "#cccccc", "#eeeeee", "#8b8b9a"
BLUE, ORANGE, GREEN, AMBER, PINK = "#3987e5", "#d95926", "#199e70", "#c98500", "#d55181"
DPI = 150

OUT_LABEL = {"ros": "ROS (spread)", "hfi": "HFI (intensity)", "cfb": "CFB (crowning)",
             "tfc": "TFC (consumption)", "p_sf": "P(sustained flaming)"}
OUTPUTS = ("ros", "hfi", "cfb", "tfc", "p_sf")

#: (variant, label, status). Status: pre = pre-fire for every fire scored;
#: mixed = post-fire for some; post = post-fire (leakage control).
VARIANTS = [
    ("cwfis_2019", "CWFIS 2019 (250 m)", "pre"),
    ("cwfis_2014b", "CWFIS 2014b (250 m)", "pre"),
    ("scanfi_tree_prefire", "SCANFI v2, latest pre-fire step", "pre"),
    ("scanfi_tree_prefire_250m", "  same, block-moded to 250 m", "pre"),
    ("scanfi_a11_prefire", "SCANFI v2 pre-fire, A-11 rules", "rules"),
    ("scanfi_tree_2005", "SCANFI v2 2005", "pre"),
    ("scanfi_tree_2010", "SCANFI v2 2010", "pre"),
    ("scanfi_tree_2015", "SCANFI v2 2015", "pre"),
    ("scanfi_tree_2020", "SCANFI v2 2020", "mixed"),
    ("scanfi_tree_2025", "SCANFI v2 2025", "post"),
    ("cwfis_2024", "CWFIS 2024 (30 m)", "post"),
]
STATUS = {"pre": (BLUE, "pre-fire"),
          "rules": (GREEN, "pre-fire, judgement rules (A-11)"),
          "mixed": (AMBER, "post-fire for 2019-20 fires"),
          "post": (ORANGE, "post-fire: leakage control")}
WEATHER = [("ffmc", "FFMC"), ("dmc", "DMC"), ("dc", "DC"), ("isi", "ISI"), ("bui", "BUI"),
           ("fwi", "FWI"), ("ffmc_class", "FFMC ignition class (GLC-X-42)"),
           ("dmc_class", "DMC lightning class (GLC-X-42)")]

#: Fuel families for the maps (more than five FBP types would exhaust the
#: validated categorical slots; the family is what the eye can separate).
FAMILY = [("C-1 lichen woodland", ("C1",), PINK), ("C-2 boreal spruce", ("C2",), GREEN),
          ("C-3 to C-7 pine", ("C3", "C4", "C5", "C6", "C7"), AMBER),
          ("M mixedwood", ("M1", "M2", "M3", "M4"), BLUE), ("D aspen", ("D1", "D2"), ORANGE),
          ("O grass, S slash", ("O1A", "O1B", "S1", "S2", "S3"), "#b9b9c6"),
          ("non-fuel, water", ("NF", "WA"), "#3a3d4a")]


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _axes(ax, title="", xlabel="", ylabel=""):
    ax.set_facecolor(AX_BG)
    for s in ax.spines.values():
        s.set_color(SPINE)
    ax.tick_params(colors=INK, labelsize=8.5)
    ax.grid(True, color=SPINE, lw=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    if title:
        ax.set_title(title, color=INK_BRIGHT, fontsize=10.5, pad=8, loc="left")
    if xlabel:
        ax.set_xlabel(xlabel, color=INK, fontsize=9)
    if ylabel:
        ax.set_ylabel(ylabel, color=INK, fontsize=9)


def _caption(fig, text, y=-0.02):
    fig.text(0.01, y, text, color=MUTED, fontsize=8.5, ha="left", va="top", wrap=True)


def _rel(p: Path) -> Path:
    return p.relative_to(_ROOT) if p.is_relative_to(_ROOT) else p


def _save(fig, out: Path, name: str):
    p = out / name
    fig.savefig(p, dpi=DPI, facecolor=FIG_BG, bbox_inches="tight")
    print(f"  wrote {_rel(p)}")
    _plt().close(fig)


def _f(x, nd=3):
    return "" if x is None or not np.isfinite(x) else f"{x:.{nd}f}"


def _ci(c, nd=2):
    return "" if not c else f"[{c[0]:.{nd}f}, {c[1]:.{nd}f}]"


# ── P2 ──────────────────────────────────────────────────────────────────────

def p2_inventories(S, out):
    plt = _plt()
    rows = [v for v in VARIANTS if v[0] in S["variants"]]
    panels = [(o, f"within_{o}", OUT_LABEL[o]) for o in OUTPUTS]
    panels.append(("hfi", "withinland_hfi", "HFI, land pixels only"))
    fig, axes = plt.subplots(1, len(panels), figsize=(17.5, 0.42 * len(rows) + 1.8), sharey=True,
                             facecolor=FIG_BG, gridspec_kw={"wspace": 0.08})
    ys = np.arange(len(rows))[::-1]
    for ax, (_o, key, title) in zip(axes, panels, strict=True):
        for y, (v, _lab, st) in zip(ys, rows, strict=True):
            w = S["variants"][v].get(key)
            if w is None:
                continue
            col = STATUS[st][0]
            if w["ci"]:
                ax.plot(w["ci"], [y, y], color=col, lw=2, solid_capstyle="round")
            ax.plot([w["mean"]], [y], "o", ms=7, color=col, mec=AX_BG, mew=2)
        ax.axvline(0.5, color=MUTED, lw=1, ls=":")
        ax.set_xlim(0.0, 0.9)
        _axes(ax, title, "within-patch AUC")
    axes[0].set_yticks(ys, [f"{lab}  (n={S['variants'][v]['within_hfi']['n']})"
                            for v, lab, _ in rows])
    handles = [plt.Line2D([], [], marker="o", ls="", color=c, ms=7, label=name)
               for c, name in STATUS.values()]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.01, 1.04), ncol=4,
               frameon=False, labelcolor=INK, fontsize=8.5)
    fig.suptitle("E-33  Which fuel inventory lets the unchanged FBP physics find the burned "
                 "pixels inside a fire?", color=INK_BRIGHT, x=0.01, y=1.11, ha="left", fontsize=12)
    _caption(fig, "Mean within-patch AUC over development fire patches (test groups never read), "
             "95 % CI from a fire/block-group bootstrap. Weather is one value per patch, so this "
             "scores fuel and terrain alone. The last panel scores every inventory on the same "
             "pixels, those all three main pre-fire inventories call burnable, so lakes and "
             "rock no longer count. 0.5 (dotted) = no ranking. Post-fire inventories are "
             "shown as leakage controls, not as baselines. Legacy 30-June codes, green leaf state.")
    _save(fig, out, "inventories.png")


def p2_weather(S, out):
    plt = _plt()
    fig, (a, b) = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True, facecolor=FIG_BG,
                               gridspec_kw={"wspace": 0.06})
    ys = np.arange(len(WEATHER))[::-1]
    for y, (k, _lab) in zip(ys, WEATHER, strict=True):
        w = S["weather_between"][k]
        a.plot(w["ci"], [y, y], color=BLUE, lw=2)
        a.plot([w["auc"]], [y], "o", ms=7, color=BLUE, mec=AX_BG, mew=2)
        p = S["weather_paired"][k]
        b.plot([p["win_rate"]], [y], "o", ms=7, color=GREEN, mec=AX_BG, mew=2)
        b.annotate(f"{p['win_rate']:.2f}", (p["win_rate"], y), xytext=(7, 0),
                   textcoords="offset points", color=INK, fontsize=8, va="center")
    for ax in (a, b):
        ax.axvline(0.5, color=MUTED, lw=1, ls=":")
        ax.set_xlim(0.3, 1.0)
    a.set_yticks(ys, [lab for _, lab in WEATHER])
    w0 = S["weather_between"]["fwi"]
    _axes(a, f"Fire vs non-fire patches  (n = {w0['n_fire']} vs {w0['n_nonfire']})",
          "between-patch AUC")
    n_pairs = S["weather_paired"]["fwi"]["n_pairs"]
    _axes(b, f"Fire vs its own confuser, same place  ({n_pairs} pairs)",
          "share of pairs where the fire year scores higher")
    fig.suptitle("E-32  Do the 30-June FWI codes separate fire patches from non-fire ones?",
                 color=INK_BRIGHT, x=0.01, y=1.03, ha="left", fontsize=12)
    _caption(fig, "Left: AUC over patches, 95 % group-bootstrap CI. It is year-confounded "
             "(72 of 99 fires are 2023; A-24). Right: each fire against the confuser at the "
             "same location in an earlier year, which holds place and fuel fixed. Legacy "
             "30-June codes: 66 of 99 fires had already started (A-24).")
    _save(fig, out, "weather.png")


def p2_vintage(S, out):
    plt = _plt()
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), facecolor=FIG_BG,
                             gridspec_kw={"wspace": 0.18})
    for ax, o in zip(axes, ("hfi", "ros"), strict=True):
        V = S["vintage_E21"][o]
        by = {}
        for stem, g, a in V["points"]:
            by.setdefault(stem, []).append((g, a))
        # Patch fixed effects, drawn: each patch's AUC minus its own mean, so
        # the plot shows exactly the variation the slope is fitted to.
        allg, alld = [], []
        for v in by.values():
            if len(v) < 2:
                continue
            g, a = np.array(sorted(v)).T
            d = a - a.mean()
            ax.plot(g, d, color=MUTED, lw=0.7, alpha=0.4)
            allg += list(g)
            alld += list(d)
        allg, alld = np.array(allg), np.array(alld)
        for g in np.unique(allg):
            m = alld[allg == g]
            ax.plot([g], [m.mean()], "o", ms=6, color=BLUE, mec=AX_BG, mew=1.5, zorder=3)
        sl = V["slope_per_decade"]
        xs = np.array([allg.min(), allg.max()])
        ax.plot(xs, (xs - allg.mean()) * sl / 10.0, color=ORANGE, lw=2, zorder=4)
        ax.axhline(0, color=MUTED, lw=1, ls=":")
        _axes(ax, f"{OUT_LABEL[o]}:  {sl:+.3f} AUC per decade  {_ci(V['ci'], 3)}",
              "inventory age at the fire (fire year - SCANFI step, years)",
              "within-patch AUC minus the patch's own mean")
    fig.suptitle("E-21  Does an older fuel inventory cost skill?  (SCANFI v2 steps through "
                 "the CFS tree)", color=INK_BRIGHT, x=0.01, y=1.04, ha="left", fontsize=12)
    n2 = S["vintage_E21"]["hfi"]["n_patches_with_2plus_steps"]
    _caption(fig, f"Grey: one fire patch across its pre-fire SCANFI steps, centred on its own "
             f"mean. Blue: mean of the centred values at each age. Orange: the fixed-effects "
             f"slope over the {n2} patches seen at two or more pre-fire steps, with a 95 % CI "
             "from a fire/block-group bootstrap. A flat line means an older inventory finds "
             "the burned pixels as well as a newer one.")
    _save(fig, out, "vintage.png")


def _fuel_rows(S, v):
    t = S["variants"][v]["fuel_tally_fire_patches"]
    rows = []
    for ft, c in t.items():
        if ft in ("none",) or c["n"] == 0:
            continue
        rows.append({"fuel": ft, "n": c["n"], "burned": c["burned"] / c["n"],
                     "hfi": c["hfi_sum"] / c["n"], "psf": c["psf_sum"] / c["n"]})
    return sorted(rows, key=lambda r: -r["n"])


def _declutter(fig, ax, labels):
    """Put each point label at the first corner of its point (right-up,
    right-down, left-up, left-down) that overlaps no label already placed and
    no other point's marker. Runs after a draw, so positions are final."""
    from matplotlib.transforms import Bbox
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    px = fig.dpi / 72.0
    # Scatter collections report no usable extent; build each marker's box
    # from its centre and its point-size radius.
    marks = []
    for t, off in labels:
        cx, cy = ax.transData.transform(t.xy)
        r = (off - 3) * px
        marks.append(Bbox.from_extents(cx - r, cy - r, cx + r, cy + r))
    placed = []
    for i, (t, off) in enumerate(labels):
        others = marks[:i] + marks[i + 1:]
        for dx, dy, ha, va in ((off, 0.6 * off, "left", "bottom"), (off, -0.6 * off, "left", "top"),
                               (-off, 0.6 * off, "right", "bottom"),
                               (-off, -0.6 * off, "right", "top")):
            t.set_position((dx, dy))
            t.set_ha(ha)
            t.set_va(va)
            bb = t.get_window_extent(rend).padded(3 * px)
            if not any(bb.overlaps(p) for p in placed + others):
                break
        placed.append(bb)


def p2_fuel_types(S, out):
    plt = _plt()
    vs = [v for v in ("cwfis_2019", "scanfi_tree_prefire") if v in S["variants"]]
    fig, axes = plt.subplots(1, len(vs), figsize=(6.2 * len(vs), 4.8), facecolor=FIG_BG,
                             squeeze=False)
    fam = {f: c for _, fs, c in FAMILY for f in fs}
    for ax, v in zip(axes[0], vs, strict=True):
        rows = [r for r in _fuel_rows(S, v) if r["n"] >= 500]
        tot = sum(r["n"] for r in rows)
        labels = []
        for r in rows:
            s = 40 + 900 * r["n"] / tot
            ax.scatter(r["burned"], max(r["hfi"], 1.0), s=s,
                       color=fam.get(r["fuel"], MUTED), edgecolor=AX_BG, lw=1.5, zorder=3)
            off = np.sqrt(s) / 2 + 3
            labels.append((ax.annotate(r["fuel"], (r["burned"], max(r["hfi"], 1.0)),
                                       xytext=(off, off * 0.6), textcoords="offset points",
                                       color=INK, fontsize=8), off))
        ax.set_yscale("log")
        ax.set_xlim(0, 1)
        lab = dict((a, b) for a, b, _ in VARIANTS)[v]
        _axes(ax, lab, "share of the type's pixels that burned (fire patches)",
              "mean FBP head fire intensity (kW/m)")
        _declutter(fig, ax, labels)
    fig.suptitle("E-32  Does FBP rank fuel types the way they burned?", color=INK_BRIGHT,
                 x=0.01, y=1.03, ha="left", fontsize=12)
    _caption(fig, "One point per FBP fuel type with at least 500 pixels on development fire "
             "patches (40 m grid); area proportional to pixel count. Physics and outcome agree "
             "when the points rise left to right. Burn share is inflated everywhere because "
             "fire patches are centred on fires, and each type's mean HFI pools patches with "
             "different weather, so compare types within a panel, not across panels.")
    _save(fig, out, "fuel_types.png")


def p2_tiles(S, run, out):
    from matplotlib.colors import LinearSegmentedColormap, ListedColormap, LogNorm
    plt = _plt()
    stems = S["config"]["qual_stems"]
    cols = [("nbac", "NBAC burned"), ("cwfis_2019_fuel", "fuel: CWFIS 2019"),
            ("scanfi_tree_prefire_fuel", "fuel: SCANFI pre-fire"),
            ("cwfis_2019_hfi", "HFI: CWFIS 2019"),
            ("scanfi_tree_prefire_hfi", "HFI: SCANFI pre-fire"),
            ("cwfis_2024_hfi", "HFI: CWFIS 2024 (post-fire)")]
    fam_of = {f: i for i, (_, fs, _) in enumerate(FAMILY) for f in fs}
    fam_cmap = ListedColormap([c for _, _, c in FAMILY] + [AX_BG])
    heat = LinearSegmentedColormap.from_list("heat", ["#241a17", "#8a3a1c", ORANGE, "#ffd2a6"])
    norm = LogNorm(10, 30000)
    fig, axes = plt.subplots(len(stems), len(cols), figsize=(2.3 * len(cols), 2.4 * len(stems)),
                             facecolor=FIG_BG, gridspec_kw={"wspace": 0.04, "hspace": 0.18,
                                                            "top": 0.86, "bottom": 0.04})
    im = None
    for r, stem in enumerate(stems):
        z = np.load(run / "qual" / f"{stem}.npz")
        for c, (k, lab) in enumerate(cols):
            ax = axes[r, c]
            ax.set_facecolor(AX_BG)
            ax.set_xticks([])
            ax.set_yticks([])
            for s in ax.spines.values():
                s.set_color(SPINE)
            if k not in z:
                ax.text(0.5, 0.5, "not held", color=MUTED, ha="center", transform=ax.transAxes)
                continue
            a = z[k]
            if k == "nbac":
                ax.imshow(a, cmap=ListedColormap([AX_BG, INK_BRIGHT]), vmin=0, vmax=1,
                          interpolation="nearest")
            elif k.endswith("_fuel"):
                idx = np.vectorize(lambda f: fam_of.get(f, len(FAMILY)))(a)
                ax.imshow(idx, cmap=fam_cmap, vmin=-0.5, vmax=len(FAMILY) + 0.5,
                          interpolation="nearest")
            else:
                im = ax.imshow(np.clip(a, 10, None), cmap=heat, norm=norm, interpolation="nearest")
            if r == 0:
                ax.set_title(lab, color=INK, fontsize=8.5, loc="left")
            if c == 0:
                ax.set_ylabel(stem.replace("_fire", ""), color=INK, fontsize=7.5)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c, label=name) for name, _, c in FAMILY]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.01, 0.955),
               ncol=4, frameon=False, labelcolor=INK, fontsize=8)
    if im is not None:
        cb = fig.colorbar(im, ax=axes[:, 3:], fraction=0.025, pad=0.01)
        cb.set_label("head fire intensity (kW/m, log)", color=INK, fontsize=8)
        cb.ax.tick_params(colors=INK, labelsize=7.5)
    fig.suptitle("E-32/E-33  Four development fire tiles, chosen by seed before scoring",
                 color=INK_BRIGHT, x=0.01, y=0.99, ha="left", fontsize=12)
    _caption(fig, "White = burned (NBAC). Fuel families from each inventory; HFI from the same "
             "patch-level 30-June weather, so within a tile only fuel and slope vary. The "
             "CWFIS 2024 column shows how a post-fire layer rewrites the burned ground.", y=0.0)
    _save(fig, out, "tiles.png")


def _csv(path: Path, rows: list[dict]):
    import csv
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


#: Paired within-patch comparisons that answer E-33's questions, each a
#: difference on the same fire patches: inventory, resolution, rule set,
#: vintage, and the size of the post-fire leak.
PAIRS = [("scanfi_tree_prefire", "cwfis_2019", "SCANFI (CFS tree) vs operational CWFIS 2019"),
         ("scanfi_tree_prefire_250m", "cwfis_2019",
          "  same at 250 m: the inventory, resolution removed"),
         ("scanfi_tree_prefire", "scanfi_tree_prefire_250m",
          "  30 m vs 250 m: the resolution alone"),
         ("scanfi_tree_prefire", "scanfi_a11_prefire",
          "CFS tree vs A-11 judgement rules, same SCANFI step"),
         ("cwfis_2019", "cwfis_2014b", "CWFIS 2019 vs 2014b"),
         ("scanfi_tree_prefire", "scanfi_tree_2025", "pre-fire vs post-fire SCANFI (leak size)"),
         ("cwfis_2019", "cwfis_2024", "pre-fire vs post-fire CWFIS (leak size)")]


def p2_paired(run: Path, output="hfi", prefix="auc", n_boot=4000, seed=0) -> list[dict]:
    """Paired within-patch AUC differences with a fire/block-group bootstrap."""
    import csv
    d = {}
    with (run / "per_patch.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["kind"] != "fire":
                continue
            v = r.get(f"{prefix}_{output}", "")
            d.setdefault(r["stem"], {"group": r["group"]})[r["variant"]] = float(v) if v else np.nan
    rng = np.random.default_rng(seed)
    out = []
    for a, b, lab in PAIRS:
        by = {}
        for v in d.values():
            if np.isfinite(v.get(a, np.nan)) and np.isfinite(v.get(b, np.nan)):
                by.setdefault(v["group"], []).append(v[a] - v[b])
        if not by:
            continue
        keys = sorted(by)
        flat = np.array([x for k in keys for x in by[k]])
        reps = [np.mean([x for i in rng.choice(len(keys), len(keys)) for x in by[keys[i]]])
                for _ in range(n_boot)]
        lo, hi = np.percentile(reps, [2.5, 97.5])
        out.append({"comparison": lab.strip(), "a": a, "b": b, "delta": float(flat.mean()),
                    "ci_lo": float(lo), "ci_hi": float(hi), "n": len(flat),
                    "share_a_wins": float((flat > 0).mean())})
    return out


def p2_tables(S, out, run=None):
    lines = ["# P2 tables: R0 on the legacy design\n",
             f"Development patches: {S['n_dev']} (test groups excluded: "
             f"{S['n_test_excluded']} patches). Design: {S['design']}.\n"]

    rows = []
    for v, lab, st in VARIANTS:
        if v not in S["variants"]:
            continue
        sv = S["variants"][v]
        row = {"inventory": lab, "status": STATUS[st][1], "n_patches": sv["n_patches"],
               "n_fire": sv["n_fire"], "coverage": sv["coverage"],
               "burned_read_nonfuel": sv["burned_nonfuel"]}
        for o in OUTPUTS:
            w = sv[f"within_{o}"]
            row[f"within_{o}"] = w["mean"]
            row[f"within_{o}_ci"] = _ci(w["ci"])
        wl = sv.get("withinland_hfi", {})
        row["within_land_hfi"] = wl.get("mean", float("nan"))
        row["within_land_hfi_ci"] = _ci(wl.get("ci"))
        row["between_hfi"] = sv["between_hfi"]["auc"]
        row["between_hfi_ci"] = _ci(sv["between_hfi"]["ci"])
        row["pooled_hfi"] = sv["pooled_hfi"]
        rows.append(row)
    _csv(out / "T_inventory.csv", rows)
    lines += ["## T-inventory: fuel inventories under unchanged FBP and ignition physics (E-33)\n",
              "Within-patch AUC (fire patches; fuel and terrain only), mean and 95 % group-"
              "bootstrap CI. `burned_read_nonfuel` is the share of NBAC-burned pixels the "
              "inventory calls non-fuel or water.\n",
              "| inventory | status | n fire | burned→non-fuel | ROS | HFI | CFB | TFC "
              "| P(sf) | HFI, land only | between HFI | pooled HFI |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| " + " | ".join([
            r["inventory"], r["status"], str(r["n_fire"]), _f(r["burned_read_nonfuel"], 3)]
            + [f"{_f(r[f'within_{o}'])} {r[f'within_{o}_ci']}" for o in OUTPUTS]
            + [f"{_f(r['within_land_hfi'])} {r['within_land_hfi_ci']}",
               f"{_f(r['between_hfi'])} {r['between_hfi_ci']}", _f(r["pooled_hfi"])]) + " |")

    if run is not None:
        for prefix, name, what in (("auc", "T_paired", "all pixels"),
                                   ("aucland", "T_paired_land", "land pixels only")):
            pr = p2_paired(run, prefix=prefix)
            if not pr:
                continue
            _csv(out / f"{name}.csv", pr)
            lines += ["", f"## {name.replace('_', '-')}: what each inventory difference is "
                          f"worth, {what} (E-33)\n",
                      "Within-patch HFI AUC, A minus B on the same fire patches; 95 % "
                      "fire/block-group bootstrap CI; share of patches where A wins.\n",
                      "| comparison (A vs B) | delta | 95 % CI | A wins | n |",
                      "|---|---|---|---|---|"]
            for r in pr:
                lines.append(f"| {r['comparison']} | {r['delta']:+.3f} | [{r['ci_lo']:+.3f}, "
                             f"{r['ci_hi']:+.3f}] | {r['share_a_wins']:.2f} | {r['n']} |")

    wrows = []
    for k, lab in WEATHER:
        w, p = S["weather_between"][k], S["weather_paired"][k]
        wrows.append({"code": lab, "between_auc": w["auc"], "ci": _ci(w["ci"]),
                      "paired_win_rate": p["win_rate"], "n_pairs": p["n_pairs"]})
    _csv(out / "T_weather.csv", wrows)
    lines += ["", "## T-weather: FWI codes between patches (E-32)\n",
              "| code | between-patch AUC | 95 % CI | paired win rate | pairs |",
              "|---|---|---|---|---|"]
    for r in wrows:
        lines.append(f"| {r['code']} | {_f(r['between_auc'])} | {r['ci']} | "
                     f"{_f(r['paired_win_rate'])} | {r['n_pairs']} |")

    for v in ("cwfis_2019", "scanfi_tree_prefire"):
        if v not in S["variants"]:
            continue
        fr = _fuel_rows(S, v)
        _csv(out / f"T_fuel_{v}.csv", fr)
        lab = dict((a, b) for a, b, _ in VARIANTS)[v]
        lines += ["", f"## T-fuel: {lab}, development fire patches\n",
                  "| fuel | pixels | burned share | mean HFI (kW/m) | mean P(sf) |",
                  "|---|---|---|---|---|"]
        for r in fr:
            lines.append(f"| {r['fuel']} | {r['n']:,} | {r['burned']:.3f} | {r['hfi']:,.0f} | "
                         f"{_f(r['psf'], 3)} |")

    lines += ["", "## T-vintage: inventory age (E-21)\n",
              "| output | slope (AUC per decade) | 95 % CI | patches with 2+ pre-fire steps |",
              "|---|---|---|---|"]
    for o, V in S["vintage_E21"].items():
        lines.append(f"| {OUT_LABEL[o]} | {V['slope_per_decade']:+.4f} | {_ci(V['ci'], 4)} | "
                     f"{V['n_patches_with_2plus_steps']} |")
    (out / "tables.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  wrote {_rel(out / 'tables.md')}")


def p2(run: Path, out: Path):
    S = json.loads((run / "summary.json").read_text())
    out.mkdir(parents=True, exist_ok=True)
    p2_tables(S, out, run)
    p2_inventories(S, out)
    p2_weather(S, out)
    p2_vintage(S, out)
    p2_fuel_types(S, out)
    p2_tiles(S, run, out)
    (out / "run.json").write_text(json.dumps(
        {"run": str(run.relative_to(_ROOT)) if run.is_relative_to(_ROOT) else str(run),
         "git": S["git"], "written": S["written"], "config": S["config"]}, indent=1))


PHASES = {"P2": (p2, "p2_r0")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--phase", required=True, choices=sorted(PHASES))
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)
    fn, sub = PHASES[args.phase]
    run = args.run if args.run.is_absolute() else _ROOT / args.run
    fn(run.resolve(), args.out or _ROOT / "docs" / "results" / sub)
    return 0


if __name__ == "__main__":
    sys.exit(main())
