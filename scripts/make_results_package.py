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

P5 (the CFFDRS-structured network; checks, no registered result):
    python scripts/make_results_package.py --phase P5 --run runs/<ts>_p5_smoke \
        --p3-run runs/<ts>_cffdrs_r0_dated
    r0_agreement.png  network R0 vs the P3 evaluator, per fire (fold 0)
    tiles.png         true colour, label and R0 maps on the seeded sample tiles
    tables.md         T-r0, T-agree, T-smoke (+ CSVs)
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


def _tile_grid(S, run, out, cols, title, caption, name="tiles.png", heat_from=None):
    """Seeded qualitative tiles, one row per tile. Column one is always the
    Sentinel-2 true-colour view of the patch, so every map beside it can be
    read against the ground it describes; the caption names its composite."""
    from matplotlib.colors import LinearSegmentedColormap, ListedColormap, LogNorm
    plt = _plt()
    stems = S["config"]["qual_stems"]
    cols = [("rgb", "Sentinel-2 true colour")] + list(cols)
    fam_of = {f: i for i, (_, fs, _) in enumerate(FAMILY) for f in fs}
    fam_cmap = ListedColormap([c for _, _, c in FAMILY] + [AX_BG])
    heat = LinearSegmentedColormap.from_list("heat", ["#241a17", "#8a3a1c", ORANGE, "#ffd2a6"])
    fig, axes = plt.subplots(len(stems), len(cols), figsize=(2.35 * len(cols), 2.45 * len(stems)),
                             facecolor=FIG_BG, gridspec_kw={"wspace": 0.04, "hspace": 0.2,
                                                            "top": 0.86, "bottom": 0.04})
    im, sources = None, set()
    for r, stem in enumerate(stems):
        z = np.load(run / "qual" / f"{stem}.npz")
        if "rgb_source" in z:
            sources.add(str(z["rgb_source"]))
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
            if k == "rgb":
                ax.imshow(a, interpolation="nearest")
            elif k in ("nbac", "leaf"):
                ax.imshow(a, cmap=ListedColormap([AX_BG, INK_BRIGHT if k == "nbac" else GREEN]),
                          vmin=0, vmax=1, interpolation="nearest")
            elif k.endswith("_fuel"):
                idx = np.vectorize(lambda f: fam_of.get(f, len(FAMILY)))(a)
                ax.imshow(idx, cmap=fam_cmap, vmin=-0.5, vmax=len(FAMILY) + 0.5,
                          interpolation="nearest")
            else:
                im = ax.imshow(np.clip(a, 10, None), cmap=heat, norm=LogNorm(10, 30000),
                               interpolation="nearest")
            if r == 0:
                ax.set_title(lab, color=INK, fontsize=8.5, loc="left")
            if c == 0:
                ax.set_ylabel(stem.replace("_fire", ""), color=INK, fontsize=7.5)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c, label=nm) for nm, _, c in FAMILY]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.01, 0.955), ncol=4,
               frameon=False, labelcolor=INK, fontsize=8)
    if im is not None:
        first = heat_from or next(i for i, (k, _) in enumerate(cols) if k.endswith("_hfi"))
        cb = fig.colorbar(im, ax=axes[:, first:], fraction=0.025, pad=0.01)
        cb.set_label("head fire intensity (kW/m, log)", color=INK, fontsize=8)
        cb.ax.tick_params(colors=INK, labelsize=7.5)
    fig.suptitle(title, color=INK_BRIGHT, x=0.01, y=0.99, ha="left", fontsize=12)
    rgb_note = ("True colour: " + "; ".join(sorted(sources)) + ". ") if sources else ""
    _caption(fig, rgb_note + caption, y=0.0)
    _save(fig, out, name)


def p2_tiles(S, run, out):
    _tile_grid(
        S, run, out,
        [("nbac", "NBAC burned"), ("cwfis_2019_fuel", "fuel: CWFIS 2019"),
         ("scanfi_tree_prefire_fuel", "fuel: SCANFI pre-fire"),
         ("cwfis_2019_hfi", "HFI: CWFIS 2019"),
         ("scanfi_tree_prefire_hfi", "HFI: SCANFI pre-fire"),
         ("cwfis_2024_hfi", "HFI: CWFIS 2024 (post-fire)")],
        "E-32/E-33  Four development fire tiles, chosen by seed before scoring",
        "White = burned (NBAC). Fuel families from each inventory; HFI from the same "
        "patch-level 30-June weather, so within a tile only fuel and slope vary. The "
        "CWFIS 2024 column shows how a post-fire layer rewrites the burned ground.")


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


# ── P3 ──────────────────────────────────────────────────────────────────────

CODE_LABEL = {"ffmc": "FFMC", "dmc": "DMC", "dc": "DC", "isi": "ISI", "bui": "BUI",
              "fwi": "FWI"}
#: E-49's prediction splits the codes: fast (FFMC, ISI) should gain, slow
#: (DC, BUI) should lose. DMC and FWI are in between and predicted nothing.
CODE_GROUP = {"ffmc": ("fast", BLUE), "isi": ("fast", BLUE), "dc": ("slow", ORANGE),
              "bui": ("slow", ORANGE), "dmc": ("no prediction", MUTED),
              "fwi": ("no prediction", MUTED)}
CHAIN = [("legacy@1", "legacy\n30 June"), ("daily_flat@1", "D-1\ndaily\nflat"),
         ("flat@1", "D-1\n13:00\nflat"), ("c2@1", "D-1\n13:00\nC-2")]
BAND_COL = (BLUE, GREEN, AMBER)
#: Latitude bands, as eval_cffdrs_reference.dated_analysis keys them.
BANDS = ("<55 N", "55-60 N", ">=60 N")


def p3_chain(W, out):
    plt = _plt()
    ch = W["E49_chain"]
    fig, axes = plt.subplots(2, 3, figsize=(13.5, 7.6), sharey=True, facecolor=FIG_BG,
                             gridspec_kw={"hspace": 0.6, "wspace": 0.12})
    x = np.arange(len(CHAIN))
    for ax, k in zip(axes.ravel(), CODE_LABEL, strict=True):
        grp, col = CODE_GROUP[k]
        m = [ch[c][k]["auc"] for c, _ in CHAIN]
        lo = [ch[c][k]["ci"][0] for c, _ in CHAIN]
        hi = [ch[c][k]["ci"][1] for c, _ in CHAIN]
        ax.vlines(x, lo, hi, color=col, lw=2)
        ax.plot(x, m, "-o", color=col, ms=7, mec=AX_BG, mew=2, lw=1.5)
        for xi, mi in zip(x, m, strict=True):
            ax.annotate(f"{mi:.2f}", (xi, mi), xytext=(9, 0), textcoords="offset points",
                        color=INK, fontsize=7.5, va="center")
        ax.axhline(0.5, color=MUTED, lw=1, ls=":")
        ax.set_xticks(x, [lab for _, lab in CHAIN], fontsize=7)
        ax.set_ylim(0.3, 1.0)
        d = m[-1] - m[0]
        _axes(ax, f"{CODE_LABEL[k]}  ({grp})   legacy -> dated: {d:+.2f}",
              "", "between-patch AUC" if k in ("ffmc", "dc") else "")
    handles = [plt.Line2D([], [], marker="o", color=c, label=lab, ms=7)
               for lab, c in (("fast codes: predicted to GAIN", BLUE),
                              ("slow codes: predicted to LOSE", ORANGE),
                              ("no prediction", MUTED))]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.01, 1.0), ncol=3,
               frameon=False, labelcolor=INK, fontsize=8.5)
    fig.suptitle("E-49  Dating the weather: what each design step does to each code",
                 color=INK_BRIGHT, x=0.01, y=1.04, ha="left", fontsize=12)
    n = ch["c2@1"]["fwi"]
    _caption(fig, f"Fire vs non-fire patches (n = {n['n_fire']} vs {n['n_nonfire']}), 95 % "
             "fire/block-group bootstrap CI. Left to right: the pre-P3 design; the same "
             "daily-aggregate weather read the day before each patch's date; 13:00 LDT "
             "hourly weather with the same flat 90-day spin-up; and the operational Appendix "
             "C-2 start-up with an overwintered DC. Registered prediction: fast codes rise, "
             "slow codes fall.")
    _save(fig, out, "chain.png")


def p3_startup(W, out):
    plt = _plt()
    s51 = W["E51_startup"]["shift_c2_minus_flat"]
    s50 = W["E50_daylength"]["shift_daylat_minus_c2"]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.4), facecolor=FIG_BG,
                             gridspec_kw={"wspace": 0.3})
    panels = [(axes[0], s51["dc"], "E-51  DC: C-2 start-up minus flat spin-up"),
              (axes[1], s51["dmc"], "E-51  DMC: C-2 start-up minus flat spin-up"),
              (axes[2], s50["dmc"], "E-50  DMC: latitude day length minus 46 N")]
    for ax, sh, title in panels:
        for i, (bn, col) in enumerate(zip(BANDS, BAND_COL, strict=True)):
            r = sh[bn]
            ax.bar(i, r["mean"], color=col, width=0.6)
            if r["ci"]:
                ax.vlines(i, *r["ci"], color=INK_BRIGHT, lw=1.5)
            ax.annotate(f"{r['mean']:+.1f}\nn={r['n']}", (i + 0.3, r["mean"] / 2),
                        xytext=(4, 0), textcoords="offset points", ha="left", va="center",
                        color=INK, fontsize=7.5)
        ax.axhline(0, color=MUTED, lw=1)
        ax.set_xticks(range(3), BANDS)
        ax.set_xlim(-0.6, 2.9)
        _axes(ax, title, "latitude band", "mean shift at D-1 (code units)")
    fig.suptitle("Start-up and day length: do they matter more in the north?",
                 color=INK_BRIGHT, x=0.01, y=1.04, ha="left", fontsize=12)
    _caption(fig, "Mean shift per patch at D-1 by latitude band, 95 % group-bootstrap CI; "
             "measured on every development patch. Registered predictions: both shifts grow "
             "with latitude (E-51: WRONG IF the start-up shift does not; E-50: WRONG IF the "
             "day-length shift is uniform).")
    _save(fig, out, "startup_daylength.png")


def p3_station(W, out):
    plt = _plt()
    e = W["E52_station"]
    pts = e["points"]
    fig, axes = plt.subplots(1, 5, figsize=(17, 3.9), facecolor=FIG_BG,
                             gridspec_kw={"wspace": 0.32})
    for ax, k in zip(axes[:4], ("ffmc", "dmc", "dc", "bui"), strict=True):
        a = np.array([p[f"stn_{k}"] for p in pts])
        b = np.array([p[f"era5_{k}"] for p in pts])
        ax.scatter(a, b, s=12, color=BLUE, alpha=0.7, lw=0)
        lo, hi = np.nanmin([a.min(), b.min()]), np.nanmax([a.max(), b.max()])
        ax.plot([lo, hi], [lo, hi], color=MUTED, lw=0.8, ls=":")
        bias = e["bias"][k]["mean_era5_minus_station"]
        _axes(ax, f"{CODE_LABEL[k]}  (ERA5 - station {bias:+.1f})",
              "nearest station, reported", "ERA5-Land 13:00 LDT, C-2")
    ax = axes[4]
    km = np.array([p["km"] for p in pts])
    dd = np.abs(np.array([p["era5_dc"] - p["stn_dc"] for p in pts]))
    ax.scatter(km, dd, s=12, color=ORANGE, alpha=0.7, lw=0)
    r = e["disagreement_vs_distance"]["dc"]
    _axes(ax, f"|DC difference| vs distance\nrho {r['rho']:+.2f} {_ci(r['ci'])}",
          "distance to the station (km)", "|ERA5 - station| DC")
    fig.suptitle(f"E-52  Reanalysis against the stations CFFDRS runs on  "
                 f"({e['n_patches']} development patches with a reporting station on D-1)",
                 color=INK_BRIGHT, x=0.01, y=1.06, ha="left", fontsize=12)
    _caption(fig, "Each point a patch at D-1. Station codes are CWFIS's own, under each "
             "agency's start-up; ERA5 codes are ours (A-32). Registered prediction: the "
             "disagreement grows with distance (WRONG IF flat). Rank correlations per code "
             "are in T-station.")
    _save(fig, out, "station.png")


def p3_staleness(W, out):
    plt = _plt()
    st = W["E53_staleness"]
    lags = ["1", "2", "3", "7"]
    fig, axes = plt.subplots(1, 6, figsize=(17, 3.6), sharey=True, facecolor=FIG_BG,
                             gridspec_kw={"wspace": 0.08})
    for ax, k in zip(axes, CODE_LABEL, strict=True):
        for src, col, lab in (("c2", BLUE, "ERA5"), ("station", GREEN, "station")):
            m = [st[src][k][lag]["auc"] for lag in lags]
            ci = [st[src][k][lag]["ci"] for lag in lags]
            xs = [int(lag) for lag in lags]
            ax.fill_between(xs, [c[0] for c in ci], [c[1] for c in ci], color=col, alpha=0.12, lw=0)
            ax.plot(xs, m, "-o", color=col, ms=5, mec=AX_BG, mew=1.5, label=lab)
        ax.axhline(0.5, color=MUTED, lw=1, ls=":")
        ax.set_xticks([1, 2, 3, 7])
        _axes(ax, f"{CODE_LABEL[k]}  ({CODE_GROUP[k][0]})", "days before D",
              "between-patch AUC" if k == "ffmc" else "")
    axes[0].legend(fontsize=8, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK)
    fig.suptitle("E-53  How stale can CFFDRS's own inputs get?", color=INK_BRIGHT,
                 x=0.01, y=1.06, ha="left", fontsize=12)
    _caption(fig, "Between-patch AUC of each code read 1, 2, 3 or 7 days before D, 95 % "
             "group-bootstrap band. Registered prediction: the fast codes (FFMC, ISI) lose "
             "more than the slow ones (DC, BUI) by D-7.")
    _save(fig, out, "staleness.png")


def p3_dates(W, out):
    plt = _plt()
    sd = W["start_dates"]
    e43 = W["E43_date_only"]
    fig, (a, b) = plt.subplots(1, 2, figsize=(13, 4.2), facecolor=FIG_BG,
                               gridspec_kw={"wspace": 0.3, "width_ratios": (1.4, 1)})
    bins = np.arange(90, 260, 7)
    for kind, col in (("fire", ORANGE), ("confuser", BLUE), ("unburned", GREEN)):
        d = [r["doy"] for r in sd if r["kind"] == kind]
        a.hist(d, bins=bins, histtype="step", lw=2, color=col, label=f"{kind} (n={len(d)})")
    a.axvline(181, color=MUTED, lw=1, ls=":")
    a.annotate("legacy 30 June", (181, a.get_ylim()[1] * 0.92), xytext=(4, 0),
               textcoords="offset points", color=MUTED, fontsize=8)
    a.legend(fontsize=8, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK, loc="upper left")
    _axes(a, "Each patch's date D (day of year)", "day of year", "patches")
    names = list(e43)
    ys = np.arange(len(names))[::-1]
    for y, nme in zip(ys, names, strict=True):
        r = e43[nme]
        col = MUTED if "confound" in nme else BLUE
        b.plot(r["ci"], [y, y], color=col, lw=2)
        b.plot([r["auc"]], [y], "o", ms=7, color=col, mec=AX_BG, mew=2)
        b.annotate(f"{r['auc']:.2f}", (r["auc"], y), xytext=(8, 6), textcoords="offset points",
                   color=INK, fontsize=8)
    b.axvline(0.5, color=MUTED, lw=1, ls=":")
    b.set_yticks(ys, [nme.split(" (")[0] + (" (confound)" if "confound" in nme else "")
                      for nme in names])
    b.set_xlim(0.2, 1.0)
    _axes(b, "E-43  Date-only control", "between-patch AUC (fire vs non-fire)")
    fig.suptitle("Dates: fires, matched confusers and pseudo-dated negatives",
                 color=INK_BRIGHT, x=0.01, y=1.05, ha="left", fontsize=12)
    _caption(fig, "Left: D by patch kind (A-32). Right: each date feature alone as a score; "
             "the registered prediction is about 0.5 for each. Year is shown as the known "
             "confound (72 of 99 fires are 2023), not as a design feature.")
    _save(fig, out, "dates.png")


def p3_tiles(S, run, out):
    _tile_grid(
        S, run, out,
        [("nbac", "NBAC burned"), ("leaf", "leaf-on on D (CWFIS): green"),
         ("scanfi_tree_prefire_fuel", "fuel: SCANFI pre-fire"),
         ("scanfi_tree_prefire_hfi", "HFI: SCANFI, dated weather"),
         ("cwfis_2019_hfi", "HFI: CWFIS 2019, dated weather")],
        "P3  The same seeded tiles under the dated design",
        "White = burned (NBAC). Green = deciduous leaf-on on D per the CWFIS product "
        "(1 km), which switches D-1/D-2 and M-1/M-2 in FBP. HFI from each patch's D-1 "
        "weather at 13:00 LDT with the C-2 start-up.")


def _within_pairs(run_a: Path, run_b: Path, variants=("scanfi_tree_prefire", "cwfis_2019"),
                  output="hfi", n_boot=4000, seed=0):
    """Paired within-patch AUC, run A minus run B, same fire patches."""
    import csv

    def load(run):
        d = {}
        with (run / "per_patch.csv").open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r["kind"] == "fire" and r[f"auc_{output}"]:
                    d[(r["stem"], r["variant"])] = (float(r[f"auc_{output}"]), r["group"])
        return d
    A, B = load(run_a), load(run_b)
    rng = np.random.default_rng(seed)
    out = []
    for v in variants:
        by = {}
        for (s, vv), (a, g) in A.items():
            if vv == v and (s, v) in B:
                by.setdefault(g, []).append(a - B[(s, v)][0])
        if not by:
            continue
        keys = sorted(by)
        flat = np.array([x for k in keys for x in by[k]])
        reps = [np.mean([x for i in rng.choice(len(keys), len(keys)) for x in by[keys[i]]])
                for _ in range(n_boot)]
        out.append({"inventory": v, "delta": float(flat.mean()),
                    "ci": [float(np.percentile(reps, 2.5)), float(np.percentile(reps, 97.5))],
                    "n": len(flat)})
    return out


def _year_stratified(run: Path, codes=("ffmc", "dmc", "dc", "isi", "bui", "fwi"),
                     n_boot=2000, seed=0) -> dict:
    """Between-patch AUC counting only fire/non-fire pairs from the SAME year:
    the year confound (72 of 99 fires are 2023) removed by construction.
    CI from resampling groups."""
    import csv
    rows = {}
    with (run / "per_patch.csv").open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows[r["stem"]] = r
    rows = list(rows.values())

    def stat(rs, k):
        num = den = 0.0
        for yv in {r["year"] for r in rs}:
            sub = [r for r in rs if r["year"] == yv]
            pos = np.array([float(r[f"w_{k}"]) for r in sub if r["kind"] == "fire"])
            neg = np.array([float(r[f"w_{k}"]) for r in sub if r["kind"] != "fire"])
            if len(pos) and len(neg):
                gt = (pos[:, None] > neg[None, :]).sum()
                num += gt + 0.5 * (pos[:, None] == neg[None, :]).sum()
                den += len(pos) * len(neg)
        return (num / den if den else float("nan")), den

    by = {}
    for r in rows:
        by.setdefault(r["group"], []).append(r)
    keys = sorted(by)
    rng = np.random.default_rng(seed)
    picks = [rng.choice(len(keys), len(keys)) for _ in range(n_boot)]
    out = {}
    for k in codes:
        a, n = stat(rows, k)
        reps = [stat([r for i in pk for r in by[keys[i]]], k)[0] for pk in picks]
        out[k] = {"auc": a, "pairs": int(n),
                  "ci": [float(np.nanpercentile(reps, 2.5)), float(np.nanpercentile(reps, 97.5))]}
    return out


def p3_tables(S, W, out, legacy=None, station=None, run=None):
    lines = ["# P3 tables: the dated design\n",
             f"Development patches: {W['n_patches']} ({W['n_fire']} fire). Main design: "
             f"{S['design']}.\n"]

    rows = []
    lines += ["## T-chain: E-49, between-patch AUC per design step\n",
              "| code | " + " | ".join(lab.replace("\n", " ") for _, lab in CHAIN)
              + " | dated - legacy | paired win rate, legacy -> dated |",
              "|---" * (len(CHAIN) + 3) + "|"]
    for k in CODE_LABEL:
        cells = []
        for c, _ in CHAIN:
            r = W["E49_chain"][c][k]
            cells.append(f"{r['auc']:.3f} {_ci(r['ci'])}")
            rows.append({"code": k, "step": c, "auc": r["auc"], "ci_lo": r["ci"][0],
                         "ci_hi": r["ci"][1], "paired_win_rate": r["win_rate"],
                         "n_pairs": r["n_pairs"]})
        d = W["E49_chain"]["c2@1"][k]["auc"] - W["E49_chain"]["legacy@1"][k]["auc"]
        lines.append(f"| {CODE_LABEL[k]} ({CODE_GROUP[k][0]}) | " + " | ".join(cells)
                     + f" | {d:+.3f} | {W['E49_chain']['legacy@1'][k]['win_rate']:.2f} -> "
                     f"{W['E49_chain']['c2@1'][k]['win_rate']:.2f} |")
    _csv(out / "T_chain.csv", rows)

    if legacy is not None and run is not None:
        yl, yd = _year_stratified(legacy), _year_stratified(run)
        year_auc = next(v for n, v in W["E43_date_only"].items() if n.startswith("year"))["auc"]
        lines += ["", "## T-year: the same comparison within each year (year confound removed)\n",
                  "Only fire/non-fire pairs from the same year count; year alone separates "
                  "the classes at AUC "
                  f"{year_auc:.2f} "
                  "across years. Within-year pairs: "
                  f"{yd['ffmc']['pairs']}, most from 2023 (58 fire, 7 non-fire patches).\n",
                  "| code | legacy, within-year | dated (C-2), within-year |", "|---|---|---|"]
        for k in CODE_LABEL:
            lines.append(f"| {CODE_LABEL[k]} | {yl[k]['auc']:.3f} {_ci(yl[k]['ci'])} | "
                         f"{yd[k]['auc']:.3f} {_ci(yd[k]['ci'])} |")
        _csv(out / "T_year.csv", [{"code": k, "legacy": yl[k]["auc"], "dated": yd[k]["auc"],
                                   "dated_ci_lo": yd[k]["ci"][0], "dated_ci_hi": yd[k]["ci"][1],
                                   "pairs": yd[k]["pairs"]} for k in CODE_LABEL])

    for key, title, sub in (("E51_startup", "T-startup: E-51, C-2 start-up minus flat spin-up",
                             "shift_c2_minus_flat"),
                            ("E50_daylength", "T-daylength: E-50, latitude day length minus 46 N",
                             "shift_daylat_minus_c2")):
        lines += ["", f"## {title}\n", "| code | " + " | ".join(BANDS) + " |", "|---|---|---|---|"]
        for k, sh in W[key][sub].items():
            lines.append(f"| {CODE_LABEL[k]} | " + " | ".join(
                f"{sh[b]['mean']:+.2f} {_ci(sh[b]['ci'])} (n={sh[b]['n']})" for b in BANDS) + " |")
        lines += ["", "Between-patch AUC per band:", "",
                  "| variant:code | " + " | ".join(BANDS) + " |", "|---|---|---|---|"]
        for vk, bands in W[key]["auc_by_band"].items():
            lines.append(f"| {vk} | " + " | ".join(
                f"{bands[b]['auc']:.3f} {_ci(bands[b]['ci'])} ({bands[b]['n_fire']}/"
                f"{bands[b]['n_nonfire']})" for b in BANDS) + " |")
    ns = W["E51_startup"]["season_not_started"]
    lines += ["", f"Season not yet started at D-1 (C-2 rule): {ns}."]

    e = W["E52_station"]
    lines += ["", f"## T-station: E-52, station vs ERA5 ({e['n_patches']} patches with a "
                  "reporting station)\n",
              "| code | AUC ERA5 (C-2) | AUC station | mean ERA5 - station | median abs diff | "
              "rho(abs diff, distance) |", "|---|---|---|---|---|---|"]
    srows = []
    for k in CODE_LABEL:
        a, s_ = e["auc"][k]["era5_c2"], e["auc"][k]["station"]
        r = e["disagreement_vs_distance"][k]
        lines.append(f"| {CODE_LABEL[k]} | {a['auc']:.3f} {_ci(a['ci'])} | {s_['auc']:.3f} "
                     f"{_ci(s_['ci'])} | {e['bias'][k]['mean_era5_minus_station']:+.2f} | "
                     f"{e['bias'][k]['median_abs']:.2f} | {r['rho']:+.2f} {_ci(r['ci'])} |")
        srows.append({"code": k, "auc_era5": a["auc"], "auc_station": s_["auc"],
                      "bias": e["bias"][k]["mean_era5_minus_station"], "rho": r["rho"],
                      "rho_ci_lo": r["ci"][0], "rho_ci_hi": r["ci"][1]})
    _csv(out / "T_station.csv", srows)

    st = W["E53_staleness"]
    lines += ["", "## T-staleness: E-53, between-patch AUC by weather age\n",
              "| code | source | D-1 | D-2 | D-3 | D-7 | D-7 minus D-1 |",
              "|---|---|---|---|---|---|---|"]
    for k in CODE_LABEL:
        for src in ("c2", "station"):
            v = st[src][k]
            lines.append(f"| {CODE_LABEL[k]} | {'ERA5' if src == 'c2' else 'station'} | "
                         + " | ".join(f"{v[lag]['auc']:.3f}" for lag in ("1", "2", "3", "7"))
                         + f" | {v['7']['auc'] - v['1']['auc']:+.3f} |")

    lines += ["", "## T-dates: E-43, date-only control\n", "| feature | AUC | 95 % CI |",
              "|---|---|---|"]
    for nme, r in W["E43_date_only"].items():
        lines.append(f"| {nme} | {r['auc']:.3f} | {_ci(r['ci'])} |")

    lines += ["", "## T-inventory (dated): within-patch AUC under the dated design\n",
              "| inventory | ROS | HFI | P(sf) | HFI, land only |", "|---|---|---|---|---|"]
    for v, lab, _ in VARIANTS:
        if v not in S["variants"]:
            continue
        sv = S["variants"][v]
        lines.append(f"| {lab.strip()} | " + " | ".join(
            f"{sv[f'within_{o}']['mean']:.3f} {_ci(sv[f'within_{o}']['ci'])}"
            for o in ("ros", "hfi", "p_sf")) + f" | {sv['withinland_hfi']['mean']:.3f} |")
    if legacy is not None and run is not None:
        lines += ["", "Within-patch HFI AUC, dated minus legacy, same fire patches:", "",
                  "| inventory | delta | 95 % CI | n |", "|---|---|---|---|"]
        for r in _within_pairs(run, legacy):
            lines.append(f"| {r['inventory']} | {r['delta']:+.3f} | {_ci(r['ci'], 3)} | {r['n']} |")
    if station is not None:
        Ss = json.loads((station / "summary.json").read_text())
        lines += ["", "R0 with the station weather (E-52), between-patch AUC:", "",
                  "| score | ERA5 run | station run |", "|---|---|---|"]
        for k in ("ffmc", "dc", "bui", "fwi"):
            lines.append(f"| {CODE_LABEL[k]} | {S['weather_between'][k]['auc']:.3f} | "
                         f"{Ss['weather_between'][k]['auc']:.3f} (n={Ss['n_dev']}) |")
        for v in ("scanfi_tree_prefire", "cwfis_2019"):
            lines.append(f"| patch-mean HFI, {v} | {S['variants'][v]['between_hfi']['auc']:.3f} | "
                         f"{Ss['variants'][v]['between_hfi']['auc']:.3f} |")
    (out / "tables.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  wrote {_rel(out / 'tables.md')}")


def p3(run: Path, out: Path, legacy: Path | None = None, station: Path | None = None):
    S = json.loads((run / "summary.json").read_text())
    W = S["dated_weather"]
    out.mkdir(parents=True, exist_ok=True)
    p3_tables(S, W, out, legacy, station, run)
    p3_chain(W, out)
    p3_startup(W, out)
    p3_station(W, out)
    p3_staleness(W, out)
    p3_dates(W, out)
    p3_tiles(S, run, out)
    (out / "run.json").write_text(json.dumps(
        {"run": str(_rel(run)), "legacy_run": str(_rel(legacy)) if legacy else None,
         "station_run": str(_rel(station)) if station else None,
         "git": S["git"], "written": S["written"], "config": S["config"]}, indent=1))


# ── P4 ──────────────────────────────────────────────────────────────────────

WINDOW_ORDER = (("D-45..D-1", "D-45 to D-1", BLUE), ("D-90..D-1", "D-90 to D-1", AMBER),
                ("fallback", "last summer (fallback)", ORANGE))


def _rank(x):
    x = np.asarray(x, float)
    order = np.argsort(x, kind="stable")
    r = np.empty(len(x))
    r[order] = np.arange(len(x))
    for v in np.unique(x):                      # average ties
        m = x == v
        r[m] = r[m].mean()
    return r


def _spearman(a, b):
    ra, rb = _rank(a), _rank(b)
    return float(np.corrcoef(ra, rb)[0, 1]) if len(ra) > 2 else float("nan")


def _win_key(c):
    return "fallback" if c.get("fallback") else c.get("window")


def _boot_groups(rows, stat, n=2000, seed=0):
    by = {}
    for r in rows:
        by.setdefault(r["group"], []).append(r)
    keys = sorted(by)
    rng = np.random.default_rng(seed)
    reps = [stat([r for i in rng.choice(len(keys), len(keys)) for r in by[keys[i]]])
            for _ in range(n)]
    return [float(np.nanpercentile(reps, 2.5)), float(np.nanpercentile(reps, 97.5))]


def p4_composites(S, out):
    plt = _plt()
    C = S["composites"]
    kinds = ("fire", "confuser", "unburned")
    fig, (a, b, c) = plt.subplots(1, 3, figsize=(14, 4), facecolor=FIG_BG,
                                  gridspec_kw={"wspace": 0.3})
    bottom = np.zeros(len(kinds))
    for key, lab, col in WINDOW_ORDER:
        h = np.array([sum(1 for v in C.values() if v["kind"] == k and _win_key(v) == key)
                      for k in kinds])
        a.bar(range(len(kinds)), h, bottom=bottom, color=col, width=0.6, label=lab,
              edgecolor=AX_BG, linewidth=2)
        for i, (hh, bb) in enumerate(zip(h, bottom, strict=True)):
            if hh:
                a.text(i, bb + hh / 2, str(hh), ha="center", va="center", color=FIG_BG,
                       fontsize=8, fontweight="bold")
        bottom += h
    a.set_xticks(range(len(kinds)), kinds)
    a.legend(fontsize=8, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK)
    _axes(a, "Window each composite used", "", "development patches")
    cov = [v["cover"] for v in C.values() if v.get("cover") is not None]
    b.hist(cov, bins=np.linspace(0, 1, 21), color=BLUE, edgecolor=AX_BG)
    b.axvline(0.9, color=MUTED, lw=1, ls=":")
    _axes(b, "Share of pixels with a clear observation", "coverage", "patches")
    obs = [v["median_clear_obs"] for v in C.values() if v.get("median_clear_obs") is not None]
    c.hist(obs, bins=np.arange(0, max(obs + [1]) + 2) - 0.5, color=GREEN, edgecolor=AX_BG)
    _axes(c, "Clear observations per pixel (median)", "observations", "patches")
    fig.suptitle("P4  Pre-fire composites: windows, coverage, depth", color=INK_BRIGHT,
                 x=0.01, y=1.05, ha="left", fontsize=12)
    _caption(fig, "Each development patch's Sentinel-2 median ending the day before D (A-33). "
             "The window widens from 45 to 90 days when under 90 % of pixels (dotted) have a "
             "clear observation; the fallback is the previous July-September. Cloud, shadow "
             "and snow are masked.")
    _save(fig, out, "composites.png")


def p4_leakage(S, out):
    plt = _plt()
    L = S["leakage_E54"]
    early = [r for r in L if r["overlap_days"] > 0]
    late = [r for r in L if r["overlap_days"] <= 0]
    fig, (a, b) = plt.subplots(1, 2, figsize=(13, 4.6), facecolor=FIG_BG,
                               gridspec_kw={"wspace": 0.25, "width_ratios": (2, 1)})
    for rows, col, lab in ((early, ORANGE, f"started before 30 June (n={len(early)})"),
                           (late, BLUE, f"started 30 June or later (n={len(late)})")):
        a.scatter([r["overlap_days"] for r in rows], [r["did"] for r in rows], s=22,
                  color=col, edgecolor=AX_BG, lw=0.8, label=lab, zorder=3)
    a.axhline(0, color=MUTED, lw=1, ls=":")
    a.axvline(0, color=MUTED, lw=1, ls=":")
    rho = _spearman([r["overlap_days"] for r in L], [r["did"] for r in L])
    ci = _boot_groups(L, lambda rs: _spearman([r["overlap_days"] for r in rs],
                                              [r["did"] for r in rs]))
    a.legend(fontsize=8, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK, loc="lower left")
    _axes(a, f"Burn already in the legacy imagery?  Spearman rho {rho:+.2f} {_ci(ci)}",
          "days the legacy window overlapped the fire (30 June minus D)",
          "B8/B11 index change on burned minus unburned\n(legacy minus pre-fire)")
    measures = (("did", "registered: fire patch", BLUE),
                ("did_minus_confuser", "control: minus same-place confuser", GREEN))
    for gi, rows in enumerate((early, late)):
        for mi, (key, _, col) in enumerate(measures):
            rs = [r for r in rows if np.isfinite(r.get(key, np.nan))]
            if not rs:
                continue
            x = gi + (mi - 0.5) * 0.36
            m = float(np.mean([r[key] for r in rs]))
            mci = _boot_groups(rs, lambda q, key=key: float(np.mean([r[key] for r in q])))
            b.bar(x, m, color=col, width=0.32)
            b.vlines(x, *mci, color=INK_BRIGHT, lw=1.3)
            b.annotate(f"{m:+.3f}  n={len(rs)}", (x + 0.09, 0.97),
                       xycoords=("data", "axes fraction"),
                       ha="center", va="top", color=INK, fontsize=7, rotation=90)
    b.axhline(0, color=MUTED, lw=1)
    b.set_xticks([0, 1], ["before\n30 June", "30 June\nor later"])
    b.set_xlim(-0.6, 1.6)
    b.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c, label=lab) for _, lab, c in measures],
             fontsize=7.5, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK, loc="lower left")
    _axes(b, "Mean by fire start", "", "difference-in-differences")
    fig.suptitle("E-54  Did the v1 imagery already show the burn?", color=INK_BRIGHT,
                 x=0.01, y=1.04, ha="left", fontsize=12)
    _caption(fig, "Per development fire patch: the change in (B8 - B11) / (B8 + B11) from the "
             "pre-fire composite to the legacy April-June one, on burned pixels minus unburned "
             "pixels, meant to cancel season and snow (the control shows it does not entirely: "
             "what later burns changes differently with season). Negative = the burned "
             "ground is darker in SWIR in the legacy imagery. 95 % CIs from a fire/block-group "
             "bootstrap. "
             "Registered prediction: negative for early fires, growing with overlap; about 0 "
             "for late fires. The control (added after registration, reported as a control) "
             "subtracts the same quantity at the same pixels in the confuser year, removing "
             "the phenology of whatever later burned.")
    _save(fig, out, "leakage.png")


def p4_tiles(S, run, out):
    from matplotlib.colors import LinearSegmentedColormap, ListedColormap, TwoSlopeNorm
    plt = _plt()
    stems = S["qual_stems"]
    cols = [("rgb_pre", "S2 true colour, pre-fire"),
            ("rgb_legacy", "S2 true colour, legacy"),
            ("label", "NBAC: burned on/after D"),
            ("d_index", "B8/B11 index, legacy minus pre-fire")]
    div = LinearSegmentedColormap.from_list("div", [ORANGE, "#5a5f70", BLUE])
    fig, axes = plt.subplots(len(stems), len(cols), figsize=(2.6 * len(cols), 2.55 * len(stems)),
                             facecolor=FIG_BG, gridspec_kw={"wspace": 0.05, "hspace": 0.28,
                                                            "top": 0.9, "bottom": 0.04})
    im = None
    for r, stem in enumerate(stems):
        z = np.load(run / "qual" / f"{stem}.npz")
        for c, (k, lab) in enumerate(cols):
            ax = axes[r, c]
            ax.set_xticks([])
            ax.set_yticks([])
            for s in ax.spines.values():
                s.set_color(SPINE)
            a = z[k]
            if k.startswith("rgb"):
                ax.imshow(a, interpolation="nearest")
            elif k == "label":
                ax.imshow(np.where(a == 1, 1, 0), cmap=ListedColormap([AX_BG, INK_BRIGHT]),
                          vmin=0, vmax=1, interpolation="nearest")
            else:
                im = ax.imshow(np.clip(a, -0.3, 0.3), cmap=div,
                               norm=TwoSlopeNorm(0, -0.3, 0.3), interpolation="nearest")
            if r == 0:
                ax.set_title(lab, color=INK, fontsize=8, loc="left")
            if c == 0:
                ax.set_ylabel(f"{stem.replace('_fire', '')}\nD = {z['fire_date']}\n{z['window']}",
                              color=INK, fontsize=7)
    if im is not None:
        cb = fig.colorbar(im, ax=axes[:, 3], fraction=0.05, pad=0.02)
        cb.set_label("index change (orange = darker in SWIR in legacy)", color=INK, fontsize=7.5)
        cb.ax.tick_params(colors=INK, labelsize=7)
    fig.suptitle("P4  Pre-fire against legacy imagery on seeded fire tiles (half started "
                 "before 30 June)", color=INK_BRIGHT, x=0.01, y=0.98, ha="left", fontsize=12)
    _caption(fig, "Tiles drawn by seed before viewing: half from fires that started before 30 "
             "June (inside the legacy window), half after. Orange in the last column marks "
             "ground darker in SWIR relative to NIR in the legacy composite than before the "
             "fire, which is what burned or snow-free ground looks like.", y=0.0)
    _save(fig, out, "composite_tiles.png")


def p4_tables(S, out):
    C, L = S["composites"], S["leakage_E54"]
    lines = ["# P4 tables: pre-fire imagery, dated labels, the v2 pack\n",
             f"Development patches: {S['n_dev']} (test patches excluded: "
             f"{S['n_test_excluded']}).\n", "## T-composite: window used, by patch kind\n",
             "| kind | D-45..D-1 | D-90..D-1 | fallback | median coverage | median clear obs |",
             "|---|---|---|---|---|---|"]
    rows = []
    for k in ("fire", "confuser", "unburned"):
        vs = [v for v in C.values() if v["kind"] == k]
        n = {key: sum(1 for v in vs if _win_key(v) == key) for key, _, _ in WINDOW_ORDER}
        cv = [v["cover"] for v in vs if v.get("cover") is not None]
        oo = [v["median_clear_obs"] for v in vs if v.get("median_clear_obs") is not None]
        cov = float(np.median(cv)) if cv else float("nan")
        ob = float(np.median(oo)) if oo else float("nan")
        lines.append(f"| {k} | {n['D-45..D-1']} | {n['D-90..D-1']} | {n['fallback']} | "
                     f"{cov:.3f} | {ob:.0f} |")
        rows.append({"kind": k, **n, "median_cover": cov, "median_obs": ob})
    _csv(out / "T_composite.csv", rows)
    early = [r for r in L if r["overlap_days"] > 0]
    late = [r for r in L if r["overlap_days"] <= 0]
    rho = _spearman([r["overlap_days"] for r in L], [r["did"] for r in L])
    ci = _boot_groups(L, lambda rs: _spearman([r["overlap_days"] for r in rs],
                                              [r["did"] for r in rs]))
    lines += ["", "## T-leak: E-54\n",
              "| fires | n | mean diff-in-diff | 95 % CI | share negative |",
              "|---|---|---|---|---|"]
    for lab, rs in (("started before 30 June", early), ("started 30 June or later", late)):
        if rs:
            m = float(np.mean([r["did"] for r in rs]))
            mci = _boot_groups(rs, lambda x: float(np.mean([r["did"] for r in x])))
            neg = float(np.mean([r["did"] < 0 for r in rs]))
            lines.append(f"| {lab} | {len(rs)} | {m:+.4f} | {_ci(mci, 4)} | {neg:.2f} |")
    lines += ["", "Control (added after registration): the same, minus the same-place confuser "
              "at the same pixels.", "", "| fires | n | mean | 95 % CI | share negative |",
              "|---|---|---|---|---|"]
    for lab, rs in (("started before 30 June", early), ("started 30 June or later", late)):
        rs = [r for r in rs if np.isfinite(r.get("did_minus_confuser", np.nan))]
        if rs:
            m = float(np.mean([r["did_minus_confuser"] for r in rs]))
            mci = _boot_groups(rs, lambda x: float(np.mean([r["did_minus_confuser"] for r in x])))
            neg = float(np.mean([r["did_minus_confuser"] < 0 for r in rs]))
            lines.append(f"| {lab} | {len(rs)} | {m:+.4f} | {_ci(mci, 4)} | {neg:.2f} |")
    lines.append(f"\nSpearman rho (overlap days, diff-in-diff): {rho:+.3f} {_ci(ci, 3)}, "
                 f"{len(L)} fire patches.")
    _csv(out / "T_leak.csv", L)
    lab = S["labels"]
    lines += ["", "## T-labels: dated NBAC labels\n",
              "| kind | patches | mean burned on/after D | mean ignored |", "|---|---|---|---|"]
    for k in ("fire", "confuser", "unburned"):
        vs = [v for s, v in lab.items() if s.endswith(k)]
        if vs:
            lines.append(f"| {k} | {len(vs)} | {np.mean([v['burned_after_D'] for v in vs]):.3f} | "
                         f"{np.mean([v['ignored'] for v in vs]):.4f} |")
    if S.get("pack"):
        p = S["pack"]
        lines += ["", "## T-pack: the v2 pack\n", "| split | patches | tiles |", "|---|---|---|"]
        for sp in ("train", "val", "test"):
            lines.append(f"| {sp} | {p['n_patches'].get(sp, 0)} | {p['counts'].get(sp, 0)} |")
    (out / "tables.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  wrote {_rel(out / 'tables.md')}")


def p4(run: Path, out: Path):
    S = json.loads((run / "summary.json").read_text())
    out.mkdir(parents=True, exist_ok=True)
    p4_tables(S, out)
    p4_composites(S, out)
    p4_leakage(S, out)
    p4_tiles(S, run, out)
    (out / "run.json").write_text(json.dumps({"run": str(_rel(run)), "seed": S["seed"],
                                              "qual_stems": S["qual_stems"]}, indent=1))


# ── P5 ──────────────────────────────────────────────────────────────────────


def _read_csv(path: Path) -> list[dict]:
    import csv
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _p5_pairs(run: Path, p3_run: Path, variant="scanfi_tree_prefire"):
    """Per fire on fold 0: (P3 evaluator, network R0) within-patch HFI AUC.
    R0's patches.csv carries its first output, HFI."""
    net = {r["patch"]: float(r["auc_within"])
           for r in _read_csv(run / "r0_scanfi" / "f0s0" / "patches.csv") if r["kind"] == "fire"}
    p3 = {r["stem"]: r["auc_hfi"] for r in _read_csv(p3_run / "per_patch.csv")
          if r["variant"] == variant}
    return [(float(p3[k]), net[k], k) for k in sorted(net) if p3.get(k)]


def p5_agreement(run, p3_run, out):
    plt = _plt()
    pairs = _p5_pairs(run, p3_run)
    x, y = np.array([p[0] for p in pairs]), np.array([p[1] for p in pairs])
    rho = _spearman(list(x), list(y))
    fig, ax = plt.subplots(figsize=(5.2, 4.8), facecolor=FIG_BG)
    _axes(ax, f"R0 HFI, within-patch AUC per fire (n = {len(pairs)}, Spearman {rho:.2f})",
          "P3 evaluator (SCANFI pre-fire, stride 2)", "P5 network R0 (v2 pack, full tiles)")
    lo = min(x.min(), y.min()) - 0.03
    ax.plot([lo, 1], [lo, 1], color=MUTED, lw=1, ls="--", zorder=1)
    ax.scatter(x, y, s=46, color=BLUE, edgecolor=FIG_BG, linewidth=1.5, zorder=3)
    ax.set_xlim(lo, 1)
    ax.set_ylim(lo, 1)
    ax.text(0.98, 0.04, f"mean {x.mean():.3f} (P3) vs {y.mean():.3f} (P5)\nmax gap "
            f"{np.abs(x - y).max():.2f}", transform=ax.transAxes, ha="right", va="bottom",
            color=INK, fontsize=8.5)
    fig.suptitle("P5-M1  R0 carries over into the network", color=INK_BRIGHT, x=0.01, y=1.0,
                 ha="left", fontsize=12)
    _caption(fig, "Development fold 0 (split seed 0), fire patches only; dashed = equal. "
             "Differences come from the pack's 256 px tiles and valid mask against P3's "
             "stride-2 sampling of the whole patch. No hypothesis was registered: this is a "
             "carry-over check.", y=-0.02)
    _save(fig, out, "r0_agreement.png")
    return pairs


def _stretch(rgb):
    """(3, H, W) reflectance -> (H, W, 3), one 2-98 % stretch shared by the
    channels and gamma 0.8, as display_rgb.patch_true_colour does."""
    a = np.moveaxis(rgb.astype(np.float32), 0, -1)
    ok = a.sum(-1) > 0
    if not ok.any():
        return np.zeros_like(a)
    lo, hi = np.percentile(a[ok], [2, 98])
    return np.clip((a - lo) / max(hi - lo, 1e-6), 0, 1) ** 0.8 * ok[..., None]


def p5_tiles(run, out):
    from matplotlib.colors import LinearSegmentedColormap, ListedColormap, LogNorm
    plt = _plt()
    z = np.load(run / "r0_scanfi" / "f0s0" / "samples.npz")
    stems = list(z["stems"])
    cols = [("rgb", "Sentinel-2 true colour"), ("label", "NBAC burned on/after D"),
            ("r0_hfi", "R0 HFI"), ("r0_cfb", "R0 CFB"), ("r0_p_sf", "R0 P(sust. flaming)")]
    heat = LinearSegmentedColormap.from_list("heat", ["#241a17", "#8a3a1c", ORANGE, "#ffd2a6"])
    seq = LinearSegmentedColormap.from_list("seq", ["#151b2b", "#1f4f8f", BLUE, "#bcd8fb"])
    fig, axes = plt.subplots(len(stems), len(cols), figsize=(2.35 * len(cols), 2.4 * len(stems)),
                             facecolor=FIG_BG, gridspec_kw={"wspace": 0.04, "hspace": 0.18,
                                                            "top": 0.93, "bottom": 0.04})
    im_h = im_s = None
    for r, stem in enumerate(stems):
        for c, (k, lab) in enumerate(cols):
            ax = axes[r, c]
            ax.set_xticks([])
            ax.set_yticks([])
            for s in ax.spines.values():
                s.set_color(SPINE)
            if k == "rgb":
                ax.imshow(_stretch(z["rgb"][r]), interpolation="nearest")
            elif k == "label":
                a = z["label"][r, 0]
                ax.imshow(np.where(a < 0, 2, a), cmap=ListedColormap([AX_BG, INK_BRIGHT, MUTED]),
                          vmin=0, vmax=2, interpolation="nearest")
            elif k == "r0_hfi":
                im_h = ax.imshow(np.clip(z[k][r, 0], 10, None), cmap=heat, norm=LogNorm(10, 30000),
                                 interpolation="nearest")
            else:
                im_s = ax.imshow(z[k][r, 0], cmap=seq, vmin=0, vmax=1, interpolation="nearest")
            if r == 0:
                ax.set_title(lab, color=INK, fontsize=8.5, loc="left")
            if c == 0:
                ax.set_ylabel(stem.replace("_fire_tile", "\n"), color=INK, fontsize=7)
    # Colour bars in their own axes under the grid, so no map column shrinks
    # out of line with the true-colour column.
    for im, (c0, c1), lab in ((im_h, (2, 2), "HFI (kW/m, log)"),
                              (im_s, (3, 4), "CFB, P(sustained flaming) (0-1)")):
        if im is not None:
            a, b = axes[-1, c0].get_position(), axes[-1, c1].get_position()
            cax = fig.add_axes([a.x0, a.y0 - 0.022, b.x1 - a.x0, 0.006])
            cb = fig.colorbar(im, cax=cax, orientation="horizontal")
            cb.set_label(lab, color=INK, fontsize=8)
            cb.ax.tick_params(colors=INK, labelsize=7.5)
    fig.suptitle("P5  R0 inside the network on six fold-0 fire tiles (drawn by seed from "
                 "stems)", color=INK_BRIGHT, x=0.01, y=0.985, ha="left", fontsize=12)
    _caption(fig, "True colour: the v2 pack's pre-fire composite (S2 SR median, D-45..D-1, "
             "B4/B3/B2). White = burned on or after D; grey = ignored or invalid. Every "
             "configuration on fold 0 saves these same tiles, so P7 can set each rung beside "
             "this R0 start. Water and non-fuel are 0 in every R0 map (A-34).", y=-0.025)
    _save(fig, out, "tiles.png")
    return stems


def p5_tables(run, out, pairs):
    r0 = json.loads((run / "r0_scanfi" / "f0s0" / "result.json").read_text())
    r3 = json.loads((run / "r3_pc_fmc_cbh" / "f0s0" / "result.json").read_text())
    lines = ["# P5 tables: the CFFDRS-structured network\n",
             f"Development fold 0 of {r0['n_folds']} (split seed {r0['split_seed']}): "
             f"{r0['n_train_patches']} training / {r0['n_val_patches']} held-out patches. "
             "The test split was not staged.\n",
             "## T-r0: R0 through the network, fold 0\n",
             "| output | pooled AUC | within-patch AUC (mean over fires) | between-patch AUC | "
             "fires |", "|---|---|---|---|---|"]
    rows = []
    for k in OUTPUTS:
        m = r0["metrics"][k]
        lines.append(f"| {OUT_LABEL[k]} | {_f(m['auc_pooled'])} | {_f(m['auc_within_mean'])} | "
                     f"{_f(m['auc_between'])} | {m['n_fire']} |")
        rows.append({"output": k, **m})
    _csv(out / "T_r0.csv", rows)
    x, y = [p[0] for p in pairs], [p[1] for p in pairs]
    lines += ["", "## T-agree: network R0 against the P3 evaluator (same fires)\n",
              "| output | fires | P3 mean | P5 mean | Spearman | max gap |",
              "|---|---|---|---|---|---|",
              f"| HFI | {len(pairs)} | {np.mean(x):.3f} | {np.mean(y):.3f} | "
              f"{_spearman(x, y):.2f} | {np.max(np.abs(np.subtract(x, y))):.2f} |"]
    _csv(out / "T_agree.csv", [{"patch": k, "p3_auc_hfi": a, "p5_auc_hfi": b} for a, b, k in pairs])
    m = r3["metrics"]["score"]
    lines += ["", "## T-smoke: R3 (pc, fmc, cbh corrected) after 3 CPU batches\n",
              "| pooled | within | between | HFI weight | other weights (max abs) | bias | "
              "wall (s) |", "|---|---|---|---|---|---|---|",
              f"| {_f(m['auc_pooled'])} | {_f(m['auc_within_mean'])} | {_f(m['auc_between'])} | "
              f"{r3['learned']['phys_w']['hfi']:.3f} | "
              f"{max(abs(v) for k, v in r3['learned']['phys_w'].items() if k != 'hfi'):.3f} | "
              f"{r3['learned']['phys_b']:.3f} | {r3['wall_s']:.0f} |",
              "", "A smoke test, not a result: the fit is truncated by design. It shows the "
              "rung starts at R0 (pooled "
              f"{_f(r0['metrics']['hfi']['auc_pooled'])}) and that a real-data fit runs."]
    (out / "tables.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  wrote {_rel(out / 'tables.md')}")


def p5(run: Path, out: Path, p3: Path | None = None):
    if p3 is None:
        raise SystemExit("P5 needs --p3-run (the dated R0 run) for the carry-over check")
    out.mkdir(parents=True, exist_ok=True)
    pairs = p5_agreement(run, p3, out)
    stems = p5_tiles(run, out)
    p5_tables(run, out, pairs)
    (out / "run.json").write_text(json.dumps({"run": str(_rel(run)), "p3_run": str(_rel(p3)),
                                              "sample_stems": stems}, indent=1))


# ── P7 ──────────────────────────────────────────────────────────────────────
# Stage A slot experiments: the Narval sweep (run_slots.py) read straight from
# its output tree, <run>/<config>/f<fold>s<seed>/{result.json, patches.csv,
# samples.npz}.

FREEZE = _ROOT.parent / "Fire_Risk_Model" / "splits" / "test_groups_v1.json"

LADDER = [("r0_scanfi", "R0  physics only (HFI)"), ("r1", "R1  learned on CFFDRS inputs"),
          ("r2", "R2  physics + learned residual"), ("r4", "R4  R2 + free imagery branch")]
#: (label, real, shuffled twin, register entry)
SLOTS = [("Percent conifer, +/-30 points", "r3_pc", "r3_pc_shuffled", "E-36"),
         ("Foliar moisture, +/-30 %", "r3_fmc", "r3_fmc_shuffled", "E-16"),
         ("Crown base height, x e^+/-0.7", "r3_cbh", "r3_cbh_shuffled", "E-37"),
         ("Curing, +/-30 points", "r3_curing", "r3_curing_shuffled", "E-38"),
         ("PC + FMC + CBH together", "r3_pc_fmc_cbh", "r3_pc_fmc_cbh_shuffled", "E-36/37"),
         ("Free imagery branch (R4)", "r4", "r4_shuffled", "R4")]
#: (label, configuration, register entry): operational-input variants of R2.
OPS = [("CWFIS 2019 fuel instead of SCANFI", "r2_cwfis", "E-35"),
       ("Station weather instead of ERA5", "r2_station", "E-52"),
       ("7-day-old codes instead of 1-day", "r2_lag7", "E-20"),
       ("Leaf state forced green", "r2_leaf_ablated", "E-40")]
CORR = [("pc", "percent conifer (points)", 30.0), ("fmc", "foliar moisture (%)", 30.0),
        ("cbh", "CBH (log factor)", 0.7)]


def _auc(s, y) -> float:
    """Rank AUC with tied ranks averaged; NaN scores dropped."""
    s, y = np.asarray(s, float), np.asarray(y, bool)
    ok = np.isfinite(s)
    s, y = s[ok], y[ok]
    n1, n0 = int(y.sum()), int((~y).sum())
    if not n1 or not n0:
        return float("nan")
    o = np.argsort(s, kind="mergesort")
    _, inv, cnt = np.unique(s[o], return_inverse=True, return_counts=True)
    e = np.cumsum(cnt)
    r = np.empty(len(s))
    r[o] = ((e - cnt + 1 + e) / 2.0)[inv]
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


class _Sweep:
    """Every fit of one sweep, indexed for paired comparisons.

    Each development patch is held out in exactly one fold, so a patch's
    within-patch AUC (averaged over seeds) comes from the models that never
    trained on it, and two configurations are paired patch by patch.
    Between-patch AUC is computed per fold -- scores from different folds'
    models are not on one scale -- and averaged over the five folds."""

    def __init__(self, run: Path, freeze: Path = FREEZE, n_boot=2000, seed=0):
        self.run = run
        self.fits: dict[str, list[dict]] = {}
        self.patch: dict[str, dict[str, dict]] = {}
        for cdir in sorted(p for p in run.iterdir() if p.is_dir() and p.name != "tasks"):
            fits, P = [], {}
            for f in sorted(cdir.glob("f*s*/result.json")):
                r = json.loads(f.read_text(encoding="utf-8"))
                fits.append(r)
                for row in _read_csv(f.parent / "patches.csv"):
                    d = P.setdefault(row["patch"], {"kind": row["kind"], "fold": r["fold"],
                                                    "w": [], "s": []})
                    d["w"].append(float(row["auc_within"]))
                    d["s"].append(float(row["mean_score"]))
            if fits:
                self.fits[cdir.name], self.patch[cdir.name] = fits, P
        groups = {s: g for g, ss in json.loads(freeze.read_text())["groups"].items() for s in ss}
        self.pat = sorted(self.patch["r2"])
        grp = np.array([groups.get(p, p) for p in self.pat])
        ug = np.unique(grp)
        gi = {g: np.where(grp == g)[0] for g in ug}
        rng = np.random.default_rng(seed)
        self.boots = [np.concatenate([gi[g] for g in rng.choice(ug, len(ug))])
                      for _ in range(n_boot)]
        self.n_groups = len(ug)
        self.year = np.array([int(p.split("_")[2]) for p in self.pat])

    def within(self, c) -> np.ndarray:
        P = self.patch[c]
        return np.array([np.nanmean(P[p]["w"]) if p in P and P[p]["kind"] == "fire"
                         else np.nan for p in self.pat])

    def _score(self, c):
        P = self.patch[c]
        s = np.array([np.mean(P[p]["s"]) if p in P else np.nan for p in self.pat])
        fold = np.array([P[p]["fold"] if p in P else -1 for p in self.pat])
        fire = np.array([p in P and P[p]["kind"] == "fire" for p in self.pat])
        return s, fold, fire

    def between(self, c, idx=None) -> float:
        s, fold, fire = self._score(c)
        idx = np.arange(len(self.pat)) if idx is None else idx
        per = [_auc(s[idx][fold[idx] == f], fire[idx][fold[idx] == f]) for f in range(5)]
        return float(np.nanmean(per))

    def between_folds(self, c) -> list[float]:
        s, fold, fire = self._score(c)
        return [_auc(s[fold == f], fire[fold == f]) for f in range(5)]

    def within_folds(self, c) -> list[float]:
        w = self.within(c)
        _, fold, _ = self._score("r2")
        return [float(np.nanmean(w[fold == f])) for f in range(5)]

    def within_year_between(self, c) -> float:
        """Fire vs non-fire AUC over same-year pairs only (the year confound:
        year alone ranks patches at 0.87, P3 E-43). Scores are ranked within
        their fold first, so the folds' models share one scale."""
        s, fold, fire = self._score(c)
        q = np.full(len(s), np.nan)
        for f in range(5):
            m = (fold == f) & np.isfinite(s)
            q[m] = _rank(s[m]) / max(m.sum() - 1, 1)
        num = den = 0.0
        for y in np.unique(self.year):
            m = self.year == y
            n1, n0 = int((fire & m).sum()), int((~fire & m).sum())
            if n1 and n0:
                num += _auc(q[m], fire[m]) * n1 * n0
                den += n1 * n0
        return num / den if den else float("nan")

    def level(self, c) -> dict:
        w = self.within(c)
        cw = np.nanpercentile([np.nanmean(w[i]) for i in self.boots], [2.5, 97.5])
        cb = np.nanpercentile([self.between(c, i) for i in self.boots[:500]], [2.5, 97.5])
        return {"config": c, "within": float(np.nanmean(w)), "within_ci": list(cw),
                "between": self.between(c), "between_ci": list(cb),
                "within_year_between": self.within_year_between(c),
                "n_fire": int(np.isfinite(w).sum()), "n_fits": len(self.fits[c])}

    def paired(self, a, b) -> dict:
        d = self.within(a) - self.within(b)
        cw = np.nanpercentile([np.nanmean(d[i]) for i in self.boots], [2.5, 97.5])
        db = [self.between(a, i) - self.between(b, i) for i in self.boots[:500]]
        fw = np.subtract(self.within_folds(a), self.within_folds(b))
        fb = np.subtract(self.between_folds(a), self.between_folds(b))
        return {"a": a, "b": b, "d_within": float(np.nanmean(d)), "d_within_ci": list(cw),
                "d_between": self.between(a) - self.between(b),
                "d_between_ci": list(np.nanpercentile(db, [2.5, 97.5])),
                "folds_won_within": int((fw > 0).sum()), "folds_won_between": int((fb > 0).sum()),
                "n_fire": int(np.isfinite(d).sum())}


def _p7_forest_rows(W):
    rows = [("Imagery corrections through the physics (R3) and R4, vs R2", None, None)]
    for lab, real, twin, eid in SLOTS:
        rows.append((f"{lab}  [{eid}]", W.paired(real, "r2"), W.paired(twin, "r2")))
    rows.append(("Operational inputs swapped under R2, vs R2", None, None))
    for lab, c, eid in OPS:
        rows.append((f"{lab}  [{eid}]", W.paired(c, "r2"), None))
    return rows


def p7_ladder(W, out):
    plt = _plt()
    lv = [W.level(c) for c, _ in LADDER]
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.9), facecolor=FIG_BG,
                             gridspec_kw={"wspace": 0.08})
    for ax, key, title in ((axes[0], "within", "Within-patch AUC (which pixels burn)"),
                           (axes[1], "between", "Between-patch AUC (which patches burn)")):
        _axes(ax, title)
        for i, ((c, _lab), L) in enumerate(zip(LADDER, lv, strict=True)):
            y = len(LADDER) - 1 - i
            per = W.within_folds(c) if key == "within" else W.between_folds(c)
            ax.scatter(per, [y] * len(per), s=26, color=MUTED, alpha=0.8, zorder=2,
                       label="one fold (mean of 3 seeds)" if i == 0 else None)
            lo, hi = L[f"{key}_ci"]
            ax.plot([lo, hi], [y, y], color=BLUE, lw=2.2, zorder=3, solid_capstyle="round")
            ax.scatter([L[key]], [y], s=70, color=BLUE, edgecolor=FIG_BG, linewidth=1.5,
                       zorder=4, label="all folds, 95 % CI (fire-group bootstrap)" if i == 0
                       else None)
            ax.text(hi + 0.006, y + 0.18, f"{L[key]:.3f}", color=INK, fontsize=8.5, va="center")
        ax.set_yticks(range(len(LADDER)))
        ax.set_yticklabels([lab for _, lab in LADDER][::-1] if ax is axes[0] else [],
                           color=INK_BRIGHT, fontsize=9)
        ax.set_ylim(-1.0, len(LADDER) - 0.4)
    axes[0].set_xlim(0.55, 0.82)
    axes[1].set_xlim(0.70, 0.98)
    axes[1].axvline(0.87, color=MUTED, lw=1, ls="--", zorder=1)
    axes[1].text(0.872, -0.85, "fire year alone (P3, E-43)", color=MUTED, fontsize=7.5)
    if (PATCHES / f"{W.pat[0]}_cwfis_grid.json").exists():
        op = _op_between(W)
        axes[1].axvline(op, color=AMBER, lw=1.4, zorder=1)
        axes[1].text(op - 0.003, len(LADDER) - 0.5, f"operational CWFIS FWI {op:.3f}",
                     color=AMBER, fontsize=7.5, ha="right")
    axes[0].legend(loc="lower left", frameon=False, labelcolor=INK, fontsize=7.5)
    fig.suptitle(f"E-34  The reference ladder on {lv[0]['n_fire']} held-out fires "
                 f"({W.n_groups} fire/block groups, 5 folds x 3 seeds)", color=INK_BRIGHT,
                 x=0.01, y=1.04, ha="left", fontsize=12)
    _caption(fig, "Every development patch is scored by the fold model that never saw it. "
             "Within-patch: mean over fire patches of the AUC among that patch's pixels. "
             "Between-patch: per-fold AUC of patch mean score, averaged over folds. R0 is not "
             "trained (its three seeds are identical). Amber line: the FWI CWFIS issued for "
             "D-1, on the 188 patches its 2018+ archive covers (paired comparison: P7b, "
             "E-55). Within-patch has no operational counterpart: CWFIS grids are 2 km.",
             y=-0.04)
    _save(fig, out, "ladder.png")
    return lv


def p7_forest(W, out):
    plt = _plt()
    rows = _p7_forest_rows(W)
    fig, axes = plt.subplots(1, 2, figsize=(12, 0.42 * len(rows) + 1.4), facecolor=FIG_BG,
                             gridspec_kw={"wspace": 0.06})
    for ax, key, title in ((axes[0], "within", "Change in within-patch AUC vs R2"),
                           (axes[1], "between", "Change in between-patch AUC vs R2")):
        _axes(ax, title)
        ax.axvline(0, color=INK, lw=0.8, zorder=1)
        labels = []
        for i, (lab, real, twin) in enumerate(rows):
            y = len(rows) - 1 - i
            labels.append(lab)
            if real is None:
                continue
            for d, off, col, face, name in ((real, 0.12, BLUE, BLUE, "real imagery or input"),
                                            (twin, -0.14, MUTED, FIG_BG, "shuffled-imagery twin")):
                if d is None:
                    continue
                lo, hi = d[f"d_{key}_ci"]
                ax.plot([lo, hi], [y + off] * 2, color=col, lw=2, zorder=3,
                        solid_capstyle="round")
                ax.scatter([d[f"d_{key}"]], [y + off], s=46, color=face, edgecolor=col,
                           linewidth=1.6, zorder=4,
                           label=name if (i == 1 and ax is axes[0]) else None)
        ax.set_yticks(range(len(rows)))
        tl = ax.set_yticklabels(labels[::-1] if ax is axes[0] else [], fontsize=8.5)
        for t, (_lab, real, _) in zip(tl, rows[::-1], strict=True):
            t.set_color(MUTED if real is None else INK_BRIGHT)
            if real is None:
                t.set_fontweight("bold")
        ax.set_ylim(-0.6, len(rows) - 0.4)
    axes[0].set_xlim(-0.05, 0.035)
    axes[1].set_xlim(-0.11, 0.08)
    axes[0].legend(loc="lower left", frameon=False, labelcolor=INK, fontsize=8)
    fig.suptitle("P7  What each slot and input changes, paired by fire against R2 "
                 "(95 % CI, fire-group bootstrap)", color=INK_BRIGHT, x=0.01, y=1.0,
                 ha="left", fontsize=12)
    _caption(fig, "Right of zero = better than R2. A slot's gain counts only if it clears its "
             "shuffled twin, which sees real imagery from the wrong tiles. Curing is exactly 0: "
             "the SCANFI fuel tree assigns no O-1 grass pixel, so the correction never acts.",
             y=-0.01)
    _save(fig, out, "slots_forest.png")
    return rows


def _corr_tiles(run, c, name):
    pts = []
    for f in sorted((run / c).glob("f*s*/samples.npz")):
        z = np.load(f)
        if f"delta_{name}" not in z.files:
            continue
        for t in range(len(z["stems"])):
            ok = z["label"][t, 0] >= 0
            v = z[f"delta_{name}"][t, 0][ok]
            if v.size:
                pts.append((float(v.mean()), float(v.std())))
    return np.array(pts)


def p7_corrections(W, out):
    plt = _plt()
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.9), facecolor=FIG_BG,
                             gridspec_kw={"wspace": 0.25})
    stats = []
    for ax, (name, lab, bound) in zip(axes, CORR, strict=True):
        _axes(ax, lab, "mean correction on the tile", "spread within the tile (SD)")
        for c, col, face, tag in ((f"r3_{name}", BLUE, BLUE, "real imagery"),
                                  (f"r3_{name}_shuffled", MUTED, FIG_BG, "shuffled twin")):
            p = _corr_tiles(W.run, c, name)
            ax.scatter(p[:, 0], p[:, 1], s=22, color=face, edgecolor=col, linewidth=1.1,
                       alpha=0.85, label=tag, zorder=3)
            stats.append({"slot": name, "config": c, "tiles": len(p),
                          "median_mean": float(np.median(p[:, 0])),
                          "median_sd": float(np.median(p[:, 1])),
                          "share_at_bound": float(np.mean(np.abs(p[:, 0]) > 0.9 * bound))})
        for b in (-bound, bound):
            ax.axvline(b, color=AMBER, lw=1, ls="--", zorder=1)
        ax.set_xlim(-bound * 1.12, bound * 1.12)
        ax.set_ylim(bottom=0)
    h, lab = axes[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="upper right", bbox_to_anchor=(0.99, 1.05), ncol=2, frameon=False,
               labelcolor=INK, fontsize=8.5)
    fig.suptitle("P7  The learned corrections are mostly one shift per tile, pinned near "
                 "their bounds", color=INK_BRIGHT, x=0.01, y=1.04, ha="left", fontsize=12)
    _caption(fig, "Each point is one seeded fire tile of one fit (6 tiles x 15 fits per "
             "configuration; dashed = the correction's bound). A correction that only moves "
             "the whole tile cannot reorder its pixels, so it cannot change within-patch AUC. "
             "Real imagery leaves some spread inside tiles; the shuffled twin learns a "
             "constant.", y=-0.04)
    _save(fig, out, "corrections.png")
    return stats


def p7_weights(W, out):
    plt = _plt()
    keys = list(OUTPUTS)
    fig, ax = plt.subplots(figsize=(7.5, 3.8), facecolor=FIG_BG)
    _axes(ax, "Weights R2 learned on the physics outputs (15 fits)", "",
          "weight on the physics term")
    ax.axhline(0, color=INK, lw=0.8, zorder=1)
    rows = []
    rng = np.random.default_rng(0)
    for i, k in enumerate(keys):
        w = np.array([r["learned"]["phys_w"][k] for r in W.fits["r2"]])
        ax.scatter(i + rng.uniform(-0.12, 0.12, len(w)), w, s=26, color=BLUE, alpha=0.85,
                   zorder=3, label="one fit" if i == 0 else None)
        ax.scatter([i + 0.3], [1.0 if k == "hfi" else 0.0], s=60, facecolor=FIG_BG,
                   edgecolor=AMBER, linewidth=1.6, zorder=3,
                   label="starting value (R2 = R0)" if i == 0 else None)
        rows.append({"output": k, "median": float(np.median(w)),
                     "q25": float(np.percentile(w, 25)), "q75": float(np.percentile(w, 75))})
    ax.set_xticks(range(len(keys)))
    ax.set_xticklabels([OUT_LABEL[k].replace(" (", "\n(") for k in keys], color=INK,
                       fontsize=8.5)
    ax.legend(loc="upper right", frameon=False, labelcolor=INK, fontsize=8)
    fig.suptitle("P7  R2 keeps intensity and leans against spread and crowning",
                 color=INK_BRIGHT, x=0.01, y=1.03, ha="left", fontsize=12)
    _caption(fig, "R2's logit is a weighted sum of log1p(ROS), log1p(HFI), CFB, log1p(TFC) and "
                  "logit P(sustained flaming), plus a residual. "
                  "The outputs are strongly correlated, so a negative weight means 'less, at "
                  "equal intensity', not 'protective'.", y=-0.06)
    _save(fig, out, "weights.png")
    return rows


def p7_curves(W, out):
    plt = _plt()
    fig, ax = plt.subplots(figsize=(7.5, 3.9), facecolor=FIG_BG)
    _axes(ax, "Validation pixel AUC by epoch (median and IQR over 15 fits)", "epoch",
          "pooled pixel AUC, held-out fold")
    for c, lab, col in (("r1", "R1", GREEN), ("r2", "R2", BLUE), ("r4", "R4", ORANGE),
                        ("r2_lag7", "R2, 7-day-old codes", PINK)):
        cu = np.array([[h["auc_px"] for h in r["history"]] for r in W.fits[c]])
        x = np.arange(1, cu.shape[1] + 1)
        med = np.median(cu, 0)
        ax.fill_between(x, np.percentile(cu, 25, 0), np.percentile(cu, 75, 0), color=col,
                        alpha=0.18, lw=0)
        ax.plot(x, med, color=col, lw=2, label=lab)
        ax.text(x[-1] + 0.6, med[-1], lab, color=INK, fontsize=8, va="center")
    ax.set_xlim(1, 41)
    ax.legend(loc="lower right", frameon=False, labelcolor=INK, fontsize=8)
    be = {c: int(np.median([r["best_epoch"] for r in W.fits[c]])) for c in ("r1", "r2", "r4")}
    fig.suptitle("P7  Training converges inside 35 epochs", color=INK_BRIGHT, x=0.01, y=1.03,
                 ha="left", fontsize=12)
    _caption(fig, f"Median best epoch: R1 {be['r1']}, R2 {be['r2']}, R4 {be['r4']}. The model "
             "kept is the best epoch on this curve (pooled pixel AUC of the held-out fold), so "
             "selection used the fold the scores are read on; the paired comparisons share "
             "that bias.", y=-0.06)
    _save(fig, out, "curves.png")
    return be


def _pct(a):
    """Within-tile percentile of each pixel's score: what within-patch AUC sees."""
    v = a.astype(np.float64)
    ok = np.isfinite(v)
    q = np.full(v.shape, np.nan)
    q[ok] = _rank(v[ok]) / max(ok.sum() - 1, 1)
    return q


def p7_tiles(W, out):
    from matplotlib.colors import LinearSegmentedColormap, ListedColormap, TwoSlopeNorm
    plt = _plt()
    seq = LinearSegmentedColormap.from_list("seq", ["#151b2b", "#1f4f8f", BLUE, "#bcd8fb"])
    div = LinearSegmentedColormap.from_list("div", [ORANGE, "#5a5f70", BLUE])
    cols = [("rgb", "Sentinel-2 true colour"), ("label", "NBAC burned on/after D"),
            ("r0_scanfi:r0_hfi", "R0 HFI"), ("r1:pred", "R1"), ("r2:pred", "R2"),
            ("r4:pred", "R4"), ("r3_pc_fmc_cbh:delta_pc", "R3 PC correction"),
            ("r3_pc_fmc_cbh:delta_fmc", "R3 FMC correction")]
    Z = {c: [np.load(W.run / c / f"f{f}s0" / "samples.npz") for f in range(5)]
         for c in ("r0_scanfi", "r1", "r2", "r4", "r3_pc_fmc_cbh")}
    fig, axes = plt.subplots(5, len(cols), figsize=(2.05 * len(cols), 2.2 * 5),
                             facecolor=FIG_BG, gridspec_kw={"wspace": 0.04, "hspace": 0.16,
                                                            "top": 0.9, "bottom": 0.12})
    im_s = im_d = None
    stems = []
    for f in range(5):
        base = Z["r2"][f]
        stem = str(base["stems"][0])
        stems.append(stem)
        for c, (k, lab) in enumerate(cols):
            ax = axes[f, c]
            ax.set_xticks([])
            ax.set_yticks([])
            for s in ax.spines.values():
                s.set_color(SPINE)
            if k == "rgb":
                ax.imshow(_stretch(base["rgb"][0]), interpolation="nearest")
            elif k == "label":
                a = base["label"][0, 0]
                ax.imshow(np.where(a < 0, 2, a), cmap=ListedColormap([AX_BG, INK_BRIGHT, MUTED]),
                          vmin=0, vmax=2, interpolation="nearest")
            else:
                cfg, key = k.split(":")
                z = Z[cfg][f]
                assert str(z["stems"][0]) == stem, (cfg, f)
                a = z[key][0, 0]
                if key.startswith("delta_"):
                    im_d = ax.imshow(np.clip(a, -30, 30), cmap=div, norm=TwoSlopeNorm(0, -30, 30),
                                     interpolation="nearest")
                else:
                    im_s = ax.imshow(_pct(a), cmap=seq, vmin=0, vmax=1, interpolation="nearest")
            if f == 0:
                ax.set_title(lab, color=INK, fontsize=8, loc="left")
            if c == 0:
                ax.set_ylabel(f"fold {f}\n" + stem.replace("_fire_tile", "\n"), color=INK,
                              fontsize=6.5)
    for im, (c0, c1), lab in ((im_s, (2, 5), "score percentile within the tile"),
                              (im_d, (6, 7), "correction (points / %)")):
        if im is not None:
            a, b = axes[-1, c0].get_position(), axes[-1, c1].get_position()
            cax = fig.add_axes([a.x0 + 0.01, a.y0 - 0.028, b.x1 - a.x0 - 0.02, 0.008])
            cb = fig.colorbar(im, cax=cax, orientation="horizontal")
            cb.set_label(lab, color=INK, fontsize=8)
            cb.ax.tick_params(colors=INK, labelsize=7.5)
    fig.suptitle("P7  One seeded fire tile per fold, every rung on the same pixels (seed 0)",
                 color=INK_BRIGHT, x=0.01, y=0.975, ha="left", fontsize=12)
    _caption(fig, "True colour: the v2 pack's pre-fire composite (S2 SR median, D-45..D-1, "
             "B4/B3/B2). White = burned on or after D; grey = ignored or invalid. Scores are shown "
             "as percentiles within the tile, which is what within-patch AUC ranks. Corrections: "
             "orange = lower than the operational value, blue = higher.", y=0.025)
    _save(fig, out, "tiles.png")
    return stems


def _cfb_engagement(run):
    v = []
    for f in sorted((run / "r0_scanfi").glob("f*s0/samples.npz")):
        z = np.load(f)
        ok = (z["label"] >= 0) & (z["r0_hfi"] > 0)
        v.append(z["r0_cfb"][ok])
    v = np.concatenate(v)
    return {"pixels": int(v.size), "cfb_pos": float((v > 0).mean()),
            "cfb_over_0.1": float((v > 0.1).mean())}


def p7_tables(W, out, lv, rows, corr, weights, best):
    L = ["# P7 tables: Stage A slot experiments (Narval sweep slots_v2)\n",
         f"Run: `{_rel(W.run)}`. {len(W.pat)} development patches ({lv[0]['n_fire']} fire), "
         f"{W.n_groups} fire/block groups, 5 folds x 3 seeds per configuration. CIs: 2,000 "
         "(within) and 500 (between) bootstrap resamples of whole groups. The test split was "
         "not read.\n", "## T-ladder\n",
         "| rung | within-patch AUC | 95 % CI | between-patch AUC | 95 % CI | "
         "between, same-year pairs only |", "|---|---|---|---|---|---|"]
    for (_c, lab), d in zip(LADDER, lv, strict=True):
        L.append(f"| {lab} | {d['within']:.3f} | {_ci(d['within_ci'], 3)} | {d['between']:.3f} | "
                 f"{_ci(d['between_ci'], 3)} | {d['within_year_between']:.3f} |")
    _csv(out / "T_ladder.csv", [{k: v for k, v in d.items()} for d in lv])
    lad = [W.paired("r1", "r0_scanfi"), W.paired("r2", "r1"), W.paired("r2", "r0_scanfi"),
           W.paired("r0_cwfis", "r0_scanfi")]
    L += ["", "## T-contrast: paired by fire (a minus b)\n",
          "| a - b | within | 95 % CI | folds won | between | 95 % CI | folds won |",
          "|---|---|---|---|---|---|---|"]
    flat = lad + [r for _, r, _ in rows if r] + [t for *_, t in rows if t]
    for d in flat:
        L.append(f"| {d['a']} - {d['b']} | {d['d_within']:+.4f} | {_ci(d['d_within_ci'], 4)} | "
                 f"{d['folds_won_within']}/5 | {d['d_between']:+.4f} | "
                 f"{_ci(d['d_between_ci'], 4)} | {d['folds_won_between']}/5 |")
    _csv(out / "T_contrast.csv", flat)
    L += ["", "Real minus shuffled twin, within-patch:\n", "| slot | real - twin | 95 % CI |",
          "|---|---|---|"]
    for lab, real, twin, _ in SLOTS:
        d = W.paired(real, twin)
        L.append(f"| {lab} | {d['d_within']:+.4f} | {_ci(d['d_within_ci'], 4)} |")
    L += ["", "## T-corrections: the learned correction on the seeded tiles\n",
          "| configuration | tiles | median tile mean | median within-tile SD | share of tiles "
          "within 10 % of the bound |", "|---|---|---|---|---|"]
    for s in corr:
        L.append(f"| {s['config']} | {s['tiles']} | {s['median_mean']:+.2f} | "
                 f"{s['median_sd']:.3f} | {s['share_at_bound']:.2f} |")
    _csv(out / "T_corrections.csv", corr)
    cf = _cfb_engagement(W.run)
    L += ["", f"CFB engagement (E-37's falsifier), R0 on the 30 seeded tiles: CFB > 0 on "
          f"{cf['cfb_pos']:.1%} of {cf['pixels']:,} burnable valid pixels, > 0.1 on "
          f"{cf['cfb_over_0.1']:.1%}.", "", "## T-weights: R2's learned physics weights\n",
          "| output | median | IQR |", "|---|---|---|"]
    for w in weights:
        L.append(f"| {OUT_LABEL[w['output']]} | {w['median']:+.2f} | "
                 f"[{w['q25']:+.2f}, {w['q75']:+.2f}] |")
    L += ["", "## T-time: what the fits took (A100, Narval)\n",
          "| configuration | fits | median wall (s) | max wall (s) | median best epoch |",
          "|---|---|---|---|---|"]
    for c in sorted(W.fits):
        ws = [r["wall_s"] for r in W.fits[c]]
        be = [r["best_epoch"] for r in W.fits[c] if r.get("trained")]
        L.append(f"| {c} | {len(ws)} | {np.median(ws):.0f} | {max(ws):.0f} | "
                 f"{int(np.median(be)) if be else '-'} |")
    (out / "tables.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"  wrote {_rel(out / 'tables.md')}")
    return lad, cf


def p7(run: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    W = _Sweep(run)
    lv = p7_ladder(W, out)
    rows = p7_forest(W, out)
    corr = p7_corrections(W, out)
    weights = p7_weights(W, out)
    best = p7_curves(W, out)
    stems = p7_tiles(W, out)
    lad, cf = p7_tables(W, out, lv, rows, corr, weights, best)
    (out / "run.json").write_text(json.dumps({"run": str(_rel(run)), "tile_stems": stems,
                                              "freeze": str(FREEZE.name)}, indent=1))
    (out / "summary.json").write_text(json.dumps(
        {"ladder": lv, "contrasts": lad, "slots": [r for _, r, _ in rows if r],
         "twins": [t for *_, t in rows if t], "corrections": corr, "weights": weights,
         "cfb": cf}, indent=1, default=float))


# ── P7b: the operational CFFDRS reference (E-55) ───────────────────────────
# The FWI grid CWFIS issued for D-1 (fetch_cwfis_grids.py sidecars), set
# against our reconstruction and against every rung of the sweep. 2 km grids:
# between-patch comparisons only.

PATCHES = _ROOT.parent / "Fire_Risk_Model" / "data" / "stage2_fire" / "patches_11band"
#: (key, label) for the per-patch FWI sources compared in E-55.
FWI_SRC = [("op", "CWFIS operational FWI grid (patch mean)"),
           ("op_c", "CWFIS operational FWI grid (patch centre)"),
           ("era5", "ERA5-Land FWI, 13:00 LDT (ours, R0's weather)"),
           ("station", "Nearest CWFIS station FWI"),
           ("fdr", "CWFIS fire danger class (majority)")]


def _ops(W) -> dict:
    """Per development patch (W.pat order): each FWI source on D-1, NaN where
    absent. 'op_issued' is False where CWFIS issued no FWI for the patch."""
    out = {k: np.full(len(W.pat), np.nan) for k, _ in FWI_SRC}
    issued = np.zeros(len(W.pat), bool)
    for i, p in enumerate(W.pat):
        g = PATCHES / f"{p}_cwfis_grid.json"
        if g.exists():
            L = json.loads(g.read_text())["layers"]
            fw = L.get("fwi") or {}
            if fw.get("mean") is not None:
                out["op"][i], issued[i] = fw["mean"], True
            if fw.get("centre") is not None:
                out["op_c"][i] = fw["centre"]
            if (L.get("fdr") or {}).get("majority") is not None:
                out["fdr"][i] = L["fdr"]["majority"]
        f = json.loads((PATCHES / f"{p}_fwi_v2.json").read_text())
        out["era5"][i] = f["variants"]["c2"]["lags"]["1"]["fwi"]
        s = PATCHES / f"{p}_station.json"
        if s.exists():
            v = (json.loads(s.read_text()).get("lags") or {}).get("1") or {}
            if v.get("fwi") is not None:
                out["station"][i] = v["fwi"]
    out["op_issued"] = issued
    out["covered"] = np.array([json.loads((PATCHES / f"{p}_date.json").read_text())["date"]
                               >= "2018-01-02" for p in W.pat])
    return out


def _fire(W):
    return np.array([W.patch["r2"][p]["kind"] == "fire" for p in W.pat])


def _same_year_auc(s, fire, year):
    num = den = 0.0
    for y in np.unique(year):
        m = (year == y) & np.isfinite(s)
        n1, n0 = int((fire & m).sum()), int((~fire & m).sum())
        if n1 and n0:
            num += _auc(s[m], fire[m]) * n1 * n0
            den += n1 * n0
    return num / den if den else float("nan")


def p7b_compare(W, ops, keep):
    """Pooled between-patch AUC per source on the patches in ``keep``, and
    paired group-bootstrap deltas against the operational grid."""
    fire = _fire(W)
    idx = np.where(keep)[0]
    pos = {j: k for k, j in enumerate(idx)}
    boots = [np.array([pos[j] for j in b if j in pos]) for b in W.boots]
    rows = []
    for k, lab in FWI_SRC:
        s, f, y = ops[k][idx], fire[idx], W.year[idx]
        auc = _auc(s, f)
        reps = [_auc(s[b], f[b]) for b in boots[:1000]]
        d = [_auc(s[b], f[b]) - _auc(ops["op"][idx][b], f[b]) for b in boots[:1000]]
        rows.append({"source": k, "label": lab, "n": int(np.isfinite(s).sum()),
                     "n_fire": int((np.isfinite(s) & f).sum()), "auc": auc,
                     "auc_ci": list(np.nanpercentile(reps, [2.5, 97.5])),
                     "auc_same_year": _same_year_auc(s, f, y),
                     "d_vs_op": auc - _auc(ops["op"][idx], f),
                     "d_vs_op_ci": list(np.nanpercentile(d, [2.5, 97.5]))})
    return rows


def p7b_agreement(W, ops, keep):
    out = {}
    for k in ("era5", "station", "op_c"):
        m = keep & np.isfinite(ops[k]) & np.isfinite(ops["op"])
        idx = np.where(m)[0]
        pos = {j: q for q, j in enumerate(idx)}
        a, b = ops["op"][idx], ops[k][idx]
        reps = []
        for bb in W.boots[:1000]:
            sel = np.array([pos[j] for j in bb if j in pos])
            reps.append(_spearman(a[sel], b[sel]))
        out[k] = {"n": int(m.sum()), "rho": _spearman(a, b),
                  "rho_ci": list(np.nanpercentile(reps, [2.5, 97.5])),
                  "median_diff": float(np.median(b - a)),
                  "mad": float(np.median(np.abs(b - a)))}
    return out


def p7b_scatter(W, ops, keep, agree, out):
    plt = _plt()
    fire = _fire(W)
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.6), facecolor=FIG_BG,
                             gridspec_kw={"wspace": 0.22})
    for ax, k, lab in ((axes[0], "era5", "ERA5-Land FWI (ours)"),
                       (axes[1], "station", "nearest-station FWI")):
        _axes(ax, f"{lab} vs the CWFIS grid (rho {agree[k]['rho']:.2f}, n {agree[k]['n']})",
              "CWFIS operational FWI on D-1 (patch mean, 2 km grid)", lab)
        m = keep & np.isfinite(ops[k]) & np.isfinite(ops["op"])
        hi = float(np.nanmax([ops["op"][m].max(), ops[k][m].max()])) * 1.05
        ax.plot([0, hi], [0, hi], color=MUTED, lw=1, ls="--", zorder=1)
        for sel, col, name in ((~fire, BLUE, "non-fire patch"), (fire, ORANGE, "fire patch")):
            q = m & sel
            ax.scatter(ops["op"][q], ops[k][q], s=26, color=col, edgecolor=FIG_BG, linewidth=1,
                       alpha=0.9, zorder=3, label=name)
        ax.set_xlim(0, hi)
        ax.set_ylim(0, hi)
    axes[0].legend(loc="upper left", frameon=False, labelcolor=INK, fontsize=8.5)
    fig.suptitle("E-55  What CWFIS issued against what we reconstruct, per development patch",
                 color=INK_BRIGHT, x=0.01, y=1.02, ha="left", fontsize=12)
    _caption(fig, "Dashed = equal. FWI on D-1. The CWFIS grid interpolates station reports "
             "to 2 km; ours runs FWI1987 on ERA5-Land at the patch centre. Patches where "
             "CWFIS issued no FWI (the season had not started in the grid) are left out.",
             y=-0.04)
    _save(fig, out, "agreement.png")


def p7b_auc(rows, rows0, out):
    plt = _plt()
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 3.6), facecolor=FIG_BG,
                             gridspec_kw={"wspace": 0.12})
    for ax, key, title in ((axes[0], "auc", "Between-patch AUC, all pairs"),
                           (axes[1], "auc_same_year", "Between-patch AUC, same-year pairs")):
        _axes(ax, title)
        for i, r in enumerate(rows):
            y = len(rows) - 1 - i
            col = AMBER if r["source"].startswith("op") or r["source"] == "fdr" else BLUE
            if key == "auc":
                lo, hi = r["auc_ci"]
                ax.plot([lo, hi], [y, y], color=col, lw=2, zorder=2, solid_capstyle="round")
            ax.scatter([r[key]], [y], s=60, color=col, edgecolor=FIG_BG, lw=1.4, zorder=3)
            r0 = next(q for q in rows0 if q["source"] == r["source"])
            ax.scatter([r0[key]], [y - 0.22], s=34, facecolor=FIG_BG, edgecolor=col, lw=1.3,
                       zorder=3, label="not-issued counted as FWI 0" if (i == 0 and key == "auc")
                       else None)
            ax.text(r[key] + 0.006, y + 0.18, f"{r[key]:.3f}", color=INK, fontsize=8)
        ax.set_yticks(range(len(rows)))
        ax.set_yticklabels([r["label"] for r in rows][::-1] if ax is axes[0] else [],
                           color=INK_BRIGHT, fontsize=8.5)
        ax.set_ylim(-0.7, len(rows) - 0.4)
        ax.set_xlim(0.55, 1.0)
    axes[0].legend(loc="lower left", frameon=False, labelcolor=INK, fontsize=8)
    fig.suptitle(f"E-55  Fire vs non-fire ranking by FWI source ({rows[0]['n']} development "
                 f"patches, {rows[0]['n_fire']} fires; 95 % CI, group bootstrap)",
                 color=INK_BRIGHT, x=0.01, y=1.04, ha="left", fontsize=12)
    _caption(fig, "Amber = issued by CWFIS; blue = reconstructed (ERA5) or reported at the "
             "nearest station. Filled = patches where every source exists; ring = the same "
             "with CWFIS's not-issued patches scored as FWI 0. Fire year alone gives 0.87 "
             "(E-43), so the same-year column is the fairer one.", y=-0.05)
    _save(fig, out, "auc.png")


def _op_between(W, ops=None) -> float:
    """Per-fold between-patch AUC of the FWI CWFIS issued for D-1 (patches the
    2018+ grid covers; not-issued counts as 0) -- the operational reference
    line on the P7 ladder. The paired comparison is P7b's."""
    ops = _ops(W) if ops is None else ops
    _, fold, _ = W._score("r2")
    fire = _fire(W)
    op = np.where(ops["op_issued"], ops["op"], 0.0)
    m = ops["covered"]
    return float(np.nanmean([_auc(op[m & (fold == f)], fire[m & (fold == f)])
                             for f in range(5)]))


def p7b_ladder(W, ops, out):
    """The sweep's rungs against the operational FWI, per fold, between patches."""
    plt = _plt()
    fire = _fire(W)
    _, fold, _ = W._score("r2")
    op = np.where(ops["op_issued"], ops["op"], 0.0)
    op[~ops["covered"]] = np.nan
    have = np.isfinite(op)

    def per_fold(s, idx=None):
        idx = np.arange(len(W.pat)) if idx is None else idx
        m = have[idx]
        return float(np.nanmean([_auc(s[idx][m & (fold[idx] == f)], fire[idx][m & (fold[idx] == f)])
                                 for f in range(5)]))
    rows = [("op", "CWFIS operational FWI (issued)", op), ("era5", "ERA5 FWI (ours)", ops["era5"])]
    for c, lab in LADDER:
        rows.append((c, lab, W._score(c)[0]))
    res = []
    for c, lab, s in rows:
        est = per_fold(s)
        d = [per_fold(s, b) - per_fold(op, b) for b in W.boots[:500]]
        res.append({"config": c, "label": lab, "between": est,
                    "d_vs_op": est - per_fold(op),
                    "d_vs_op_ci": list(np.nanpercentile(d, [2.5, 97.5]))})
    fig, ax = plt.subplots(figsize=(8.5, 3.8), facecolor=FIG_BG)
    _axes(ax, "Between-patch AUC minus the operational FWI's, paired by fold and group",
          "difference in between-patch AUC (right = better than operational CFFDRS)")
    ax.axvline(0, color=AMBER, lw=1.2, zorder=1)
    for i, r in enumerate(res[1:]):
        y = len(res) - 2 - i
        lo, hi = r["d_vs_op_ci"]
        ax.plot([lo, hi], [y, y], color=BLUE, lw=2, zorder=2, solid_capstyle="round")
        ax.scatter([r["d_vs_op"]], [y], s=56, color=BLUE, edgecolor=FIG_BG, lw=1.4, zorder=3)
        ax.text(hi + 0.004, y, f"{r['between']:.3f}", color=INK, fontsize=8, va="center")
    ax.set_yticks(range(len(res) - 1))
    ax.set_yticklabels([r["label"] for r in res[1:]][::-1], color=INK_BRIGHT, fontsize=8.5)
    ax.set_ylim(-0.6, len(res) - 1.4)
    fig.suptitle(f"P7b  Every rung against operational CFFDRS (operational FWI: "
                 f"{res[0]['between']:.3f})", color=INK_BRIGHT, x=0.01, y=1.04, ha="left",
                 fontsize=12)
    _caption(fig, "Same 5 folds as the slots_v2 sweep, AUC per fold then averaged; patches "
             "dated before the grid's 2018 start are left out, and not-issued patches count as "
             "FWI 0. Numbers at right are each rung's own between-patch AUC on these patches. "
             "Within-patch skill has no operational counterpart: the grid is 2 km.", y=-0.05)
    _save(fig, out, "ladder_vs_operational.png")
    return res


def p7b_tables(rows, rows0, agree, lad, ops, keep, out):
    L = ["# P7b tables: the operational CFFDRS reference (E-55)\n",
         f"Development patches with a CWFIS FWI value and both reconstructed sources: "
         f"{rows[0]['n']} ({rows[0]['n_fire']} fire). Not covered (dated before 2018): "
         f"{int((~ops['covered']).sum())}; covered but not issued: "
         f"{int((ops['covered'] & ~ops['op_issued']).sum())}.\n",
         "## T-auc: between-patch AUC by FWI source\n",
         "| source | n | AUC | 95 % CI | same-year pairs | minus operational | 95 % CI | "
         "AUC, not-issued as 0 |", "|---|---|---|---|---|---|---|---|"]
    for r, r0 in zip(rows, rows0, strict=True):
        L.append(f"| {r['label']} | {r['n']} | {r['auc']:.3f} | {_ci(r['auc_ci'], 3)} | "
                 f"{r['auc_same_year']:.3f} | {r['d_vs_op']:+.3f} | {_ci(r['d_vs_op_ci'], 3)} | "
                 f"{r0['auc']:.3f} |")
    _csv(out / "T_auc.csv", rows)
    L += ["", "## T-agree: agreement with the operational grid (patch mean)\n",
          "| source | n | Spearman rho | 95 % CI | median (source - operational) | median "
          "absolute difference |", "|---|---|---|---|---|---|"]
    for k, a in agree.items():
        L.append(f"| {k} | {a['n']} | {a['rho']:.2f} | {_ci(a['rho_ci'], 2)} | "
                 f"{a['median_diff']:+.1f} | {a['mad']:.1f} |")
    L += ["", "## T-ladder: rungs against the operational FWI (per fold, between patches)\n",
          "| rung | between-patch AUC | minus operational | 95 % CI |", "|---|---|---|---|"]
    for r in lad:
        L.append(f"| {r['label']} | {r['between']:.3f} | {r['d_vs_op']:+.3f} | "
                 f"{_ci(r['d_vs_op_ci'], 3)} |")
    _csv(out / "T_ladder_vs_operational.csv", lad)
    (out / "tables.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"  wrote {_rel(out / 'tables.md')}")


def p7b(run: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    W = _Sweep(run)
    ops = _ops(W)
    keep = (ops["covered"] & ops["op_issued"] & np.isfinite(ops["era5"])
            & np.isfinite(ops["station"]))
    rows = p7b_compare(W, ops, keep)
    ops0 = dict(ops)
    ops0["op"] = np.where(ops["covered"] & ~ops["op_issued"], 0.0, ops["op"])
    ops0["op_c"] = np.where(ops["covered"] & ~ops["op_issued"], 0.0, ops["op_c"])
    keep0 = ops["covered"] & np.isfinite(ops["era5"]) & np.isfinite(ops["station"])
    rows0 = p7b_compare(W, ops0, keep0)
    agree = p7b_agreement(W, ops, keep)
    p7b_scatter(W, ops, keep, agree, out)
    p7b_auc(rows, rows0, out)
    lad = p7b_ladder(W, ops, out)
    p7b_tables(rows, rows0, agree, lad, ops, keep, out)
    (out / "summary.json").write_text(json.dumps(
        {"auc": rows, "auc_not_issued_as_0": rows0, "agreement": agree, "ladder": lad,
         "n_keep": int(keep.sum()), "not_covered": int((~ops["covered"]).sum()),
         "not_issued": int((ops["covered"] & ~ops["op_issued"]).sum())}, indent=1, default=float))
    (out / "run.json").write_text(json.dumps({"run": str(_rel(run)), "patches": str(PATCHES),
                                              "freeze": FREEZE.name}, indent=1))


PHASES = {"P2": (p2, "p2_r0"), "P3": (p3, "p3_dated"), "P4": (p4, "p4_prefire"),
          "P5": (p5, "p5_slotnet"), "P7": (p7, "p7_slots"), "P7b": (p7b, "p7b_operational")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--phase", required=True, choices=sorted(PHASES))
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--legacy-run", type=Path, default=None, help="P3: the P2 legacy run")
    ap.add_argument("--station-run", type=Path, default=None, help="P3: the station-weather run")
    ap.add_argument("--p3-run", type=Path, default=None, help="P5: the dated R0 run")
    args = ap.parse_args(argv)
    fn, sub = PHASES[args.phase]

    def resolve(p):
        return None if p is None else (p if p.is_absolute() else _ROOT / p).resolve()
    extra = {}
    if args.phase == "P3":
        extra = {"legacy": resolve(args.legacy_run), "station": resolve(args.station_run)}
    elif args.phase == "P5":
        extra = {"p3": resolve(args.p3_run)}
    fn(resolve(args.run), args.out or _ROOT / "docs" / "results" / sub, **extra)
    return 0


if __name__ == "__main__":
    sys.exit(main())
