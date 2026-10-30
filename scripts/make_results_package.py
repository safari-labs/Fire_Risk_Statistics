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
sys.path.insert(0, str(_ROOT / "src"))

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
                                                    "w": [], "s": [], "wf": {}})
                    d["w"].append(float(row["auc_within"]))
                    d["s"].append(float(row["mean_score"]))
                    for fam in "CDMO":
                        if f"auc_within_{fam}" in row:
                            d["wf"].setdefault(fam, []).append(float(row[f"auc_within_{fam}"]))
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

    def within_fuel(self, c, fam) -> np.ndarray:
        """Within-patch AUC on one fuel family's pixels, per fire patch
        (NaN where the patch lacks burned or unburned pixels of that family)."""
        P = self.patch[c]
        out = np.full(len(self.pat), np.nan)
        for i, p in enumerate(self.pat):
            if p in P and P[p]["kind"] == "fire" and P[p]["wf"].get(fam):
                v = np.array(P[p]["wf"][fam], float)
                if np.isfinite(v).any():
                    out[i] = float(np.nanmean(v))
        return out

    def paired_on(self, a, b, fam=None) -> dict:
        """Paired within-patch delta, all pixels (fam None) or one family's."""
        wa = self.within(a) if fam is None else self.within_fuel(a, fam)
        wb = self.within(b) if fam is None else self.within_fuel(b, fam)
        d = wa - wb
        reps = [np.nanmean(d[i]) for i in self.boots]
        return {"a": a, "b": b, "fam": fam or "all", "d": float(np.nanmean(d)),
                "ci": list(np.nanpercentile(reps, [2.5, 97.5])),
                "n_fire": int(np.isfinite(d).sum())}

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
    rows.append(("Operational input products swapped under R2, vs R2", None, None))
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
        axes[1].text(op - 0.003, len(LADDER) - 0.5, f"ISSUED by CWFIS (actual FWI) {op:.3f}",
                     color=AMBER, fontsize=7.5, ha="right")
    axes[0].legend(loc="lower left", frameon=False, labelcolor=INK, fontsize=7.5)
    fig.suptitle(f"E-34  The reference ladder on {lv[0]['n_fire']} held-out fires "
                 f"({W.n_groups} fire/block groups, 5 folds x 3 seeds)", color=INK_BRIGHT,
                 x=0.01, y=1.04, ha="left", fontsize=12)
    _caption(fig, "Every development patch is scored by the fold model that never saw it. "
             "Within-patch: mean over fire patches of the AUC among that patch's pixels. "
             "Between-patch: per-fold AUC of patch mean score, averaged over folds. R0 is not "
             "trained (its three seeds are identical). Amber line: the FWI CWFIS actually issued "
             "for D-1 (not our reconstruction), on the 188 patches its 2018+ archive covers "
             "(paired comparison: P7b, E-55). Every rung is our model; within-patch has no "
             "issued counterpart: CWFIS grids are 2 km.",
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


# ── P7b: the CFFDRS values CWFIS actually issued (E-55) ─────────────────────
# The FWI grid CWFIS issued for D-1 (fetch_cwfis_grids.py sidecars), set
# against our reconstruction and against every rung of the sweep. 2 km grids:
# between-patch comparisons only.

PATCHES = _ROOT.parent / "Fire_Risk_Model" / "data" / "stage2_fire" / "patches_11band"
#: (key, label) for the per-patch FWI sources compared in E-55.
FWI_SRC = [("op", "ISSUED by CWFIS: FWI grid (patch mean)"),
           ("op_c", "ISSUED by CWFIS: FWI grid (patch centre)"),
           ("era5", "Reconstructed (ours): ERA5-Land FWI, R0's weather"),
           ("station", "ISSUED by CWFIS: FWI at the nearest station"),
           ("fdr", "ISSUED by CWFIS: fire danger class (majority)")]


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
    for ax, k, lab in ((axes[0], "era5", "reconstructed FWI (ours, ERA5)"),
                       (axes[1], "station", "station FWI (issued by CWFIS)")):
        _axes(ax, f"{lab} vs the issued grid (rho {agree[k]['rho']:.2f}, n {agree[k]['n']})",
              "FWI ISSUED by CWFIS for D-1 (patch mean, 2 km grid)", lab)
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
    fig.suptitle("E-55  What CWFIS actually issued against what we reconstruct, per patch",
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
            col = BLUE if r["source"] == "era5" else AMBER
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
    _caption(fig, "Amber = ISSUED by CWFIS (values it actually published: the gridded FWI, "
             "the danger class, and the codes it computed at the nearest station); blue = "
             "reconstructed by us. Filled = patches where every source exists; ring = the same "
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
    rows = [("op", "ISSUED by CWFIS: FWI", op),
            ("era5", "Reconstructed (ours): ERA5 FWI", ops["era5"])]
    for c, lab in LADDER:
        rows.append((c, "Reconstructed (ours): " + lab.split("  ")[0], W._score(c)[0]))
    res = []
    for c, lab, s in rows:
        est = per_fold(s)
        d = [per_fold(s, b) - per_fold(op, b) for b in W.boots[:500]]
        res.append({"config": c, "label": lab, "between": est,
                    "d_vs_op": est - per_fold(op),
                    "d_vs_op_ci": list(np.nanpercentile(d, [2.5, 97.5]))})
    fig, ax = plt.subplots(figsize=(8.5, 3.8), facecolor=FIG_BG)
    _axes(ax, "Between-patch AUC minus that of the FWI CWFIS actually issued",
          "difference in between-patch AUC (right = better than what CWFIS issued)")
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
    fig.suptitle(f"P7b  Every rung against the FWI CWFIS actually issued "
                 f"({res[0]['between']:.3f})", color=INK_BRIGHT, x=0.01, y=1.04, ha="left",
                 fontsize=12)
    _caption(fig, "Same 5 folds as the slots_v2 sweep, AUC per fold then averaged; patches "
             "dated before the grid's 2018 start are left out, and not-issued patches count as "
             "FWI 0. Numbers at right are each rung's own between-patch AUC on these patches. "
             "Within-patch skill has no issued counterpart: the grid is 2 km.", y=-0.05)
    _save(fig, out, "ladder_vs_operational.png")
    return res


def p7b_tables(rows, rows0, agree, lad, ops, keep, out):
    L = ["# P7b tables: against the CFFDRS values CWFIS actually issued (E-55)\n",
         "Rows marked ISSUED by CWFIS are values CWFIS published; 'reconstructed' rows "
         "are ours.\n",
         f"Development patches with a CWFIS FWI value and both reconstructed sources: "
         f"{rows[0]['n']} ({rows[0]['n_fire']} fire). Not covered (dated before 2018): "
         f"{int((~ops['covered']).sum())}; covered but not issued: "
         f"{int((ops['covered'] & ~ops['op_issued']).sum())}.\n",
         "## T-auc: between-patch AUC by FWI source\n",
         "| source | n | AUC | 95 % CI | same-year pairs | minus issued grid | 95 % CI | "
         "AUC, not-issued as 0 |", "|---|---|---|---|---|---|---|---|"]
    for r, r0 in zip(rows, rows0, strict=True):
        L.append(f"| {r['label']} | {r['n']} | {r['auc']:.3f} | {_ci(r['auc_ci'], 3)} | "
                 f"{r['auc_same_year']:.3f} | {r['d_vs_op']:+.3f} | {_ci(r['d_vs_op_ci'], 3)} | "
                 f"{r0['auc']:.3f} |")
    _csv(out / "T_auc.csv", rows)
    L += ["", "## T-agree: agreement with the FWI grid ISSUED by CWFIS (patch mean)\n",
          "| source | n | Spearman rho | 95 % CI | median (source - issued grid) | median "
          "absolute difference |", "|---|---|---|---|---|---|"]
    names = {"era5": "Reconstructed (ours): ERA5 FWI",
             "station": "ISSUED by CWFIS: FWI at the nearest station",
             "op_c": "ISSUED by CWFIS: grid centre cell (check)"}
    for k, a in agree.items():
        L.append(f"| {names[k]} | {a['n']} | {a['rho']:.2f} | {_ci(a['rho_ci'], 2)} | "
                 f"{a['median_diff']:+.1f} | {a['mad']:.1f} |")
    L += ["", "## T-ladder: our rungs against the FWI ISSUED by CWFIS (per fold, between "
          "patches)\n",
          "| rung | between-patch AUC | minus issued FWI | 95 % CI |", "|---|---|---|---|"]
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


# ── P7c: the second slot sweep (slots_v3; Q29 arms) ─────────────────────────
# E-58 (R2's gap to R1), E-57 (percent conifer with an offset), E-38 (curing
# on CWFIS fuel). Every number is our reconstruction unless marked ISSUED by
# CWFIS (A-36).

GAP = [("r1", "R1  learned on CFFDRS inputs"), ("r2", "R2  zero start (rerun)"),
       ("r2_warm", "R2  residual started from R1"), ("r2_lr10", "R2  residual at 10x rate")]


def p7c_gap(W, out):
    plt = _plt()
    lv = [W.level(c) for c, _ in GAP]
    comps = [("r2", "r1"), ("r2_warm", "r1"), ("r2_lr10", "r1"), ("r2_warm", "r2"),
             ("r2_lr10", "r2")]
    pr = {(a, b): W.paired(a, b) for a, b in comps}
    names = dict(GAP)
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 3.9), facecolor=FIG_BG,
                             gridspec_kw={"wspace": 0.08})
    for ax, key, title in ((axes[0], "within", "Change in within-patch AUC"),
                           (axes[1], "between", "Change in between-patch AUC")):
        _axes(ax, title)
        ax.axvline(0, color=INK, lw=0.8, zorder=1)
        for x in (-0.01, 0.01):
            ax.axvline(x, color=AMBER, lw=1, ls="--", zorder=1)
        for i, (a, b) in enumerate(comps):
            y = len(comps) - 1 - i
            d = pr[(a, b)]
            lo, hi = d[f"d_{key}_ci"]
            col = BLUE if b == "r1" else GREEN
            ax.plot([lo, hi], [y, y], color=col, lw=2, zorder=2, solid_capstyle="round")
            ax.scatter([d[f"d_{key}"]], [y], s=56, color=col, edgecolor=FIG_BG, lw=1.4,
                       zorder=3)
            ax.text(hi + 0.002, y + 0.2, f"{d[f'd_{key}']:+.3f}", color=INK, fontsize=8,
                    bbox={"facecolor": AX_BG, "edgecolor": "none", "pad": 1})
        ax.set_yticks(range(len(comps)))
        ax.set_yticklabels([f"{names[a].split('  ')[1]}  minus  {names[b].split('  ')[0]}"
                            for a, b in comps][::-1] if ax is axes[0] else [],
                           color=INK_BRIGHT, fontsize=8.5)
        ax.set_ylim(-0.6, len(comps) - 0.4)
    fig.suptitle("E-58  Does R2's within-patch gap to R1 close? (slots_v3, paired by fire, "
                 "95 % CI)", color=INK_BRIGHT, x=0.01, y=1.03, ha="left", fontsize=12)
    _caption(fig, "Blue = against R1 (the target); green = against R2 at its usual zero start. "
             "Dashed = the registered 0.01 margins: an arm closes the gap if it sits within "
             "0.01 of R1 inside patches and loses no more than 0.01 to R2 between patches. "
             "All rungs are ours (reconstructed). r2_warm lacks fold 4 seeds 1-2 (killed at "
             "16G); its fold-4 patches use seed 0.", y=-0.05)
    _save(fig, out, "gap.png")
    return lv, pr


def _imagery_part(run, c, name="pc"):
    pts = []
    for f in sorted((run / c).glob("f*s*/samples.npz")):
        z = np.load(f)
        if f"delta_{name}" not in z.files:
            continue
        for k in range(len(z["stems"])):
            ok = z["label"][k, 0] >= 0
            v = z[f"delta_{name}"][k, 0][ok]
            if v.size:
                pts.append((float(v.mean()), float(v.std())))
    return np.array(pts)


def p7c_offset(W, out):
    plt = _plt()
    rows = []
    for fam, lab in ((None, "all pixels"), ("M", "M-1/M-2 pixels")):
        for a, b in (("r3_pc_offset", "r3_pc_offset_shuffled"), ("r3_pc_offset", "r2"),
                     ("r3_pc_offset_shuffled", "r2")):
            d = W.paired_on(a, b, fam)
            d["label"] = lab
            rows.append(d)
    offs = {c: [r["learned"]["offsets"]["pc"] for r in W.fits[c]]
            for c in ("r3_pc_offset", "r3_pc_offset_shuffled")}
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.9), facecolor=FIG_BG,
                             gridspec_kw={"wspace": 0.35, "width_ratios": [1.5, 1, 1]})
    ax = axes[0]
    _axes(ax, "Paired within-patch change (95 % CI)")
    ax.axvline(0, color=INK, lw=0.8, zorder=1)
    lbl = {("r3_pc_offset", "r3_pc_offset_shuffled"): "offset arm minus its twin",
           ("r3_pc_offset", "r2"): "offset arm minus R2",
           ("r3_pc_offset_shuffled", "r2"): "twin minus R2"}
    for i, d in enumerate(rows):
        y = len(rows) - 1 - i
        col = ORANGE if d["fam"] == "M" else BLUE
        lo, hi = d["ci"]
        ax.plot([lo, hi], [y, y], color=col, lw=2, zorder=2, solid_capstyle="round")
        ax.scatter([d["d"]], [y], s=50, color=col, edgecolor=FIG_BG, lw=1.3, zorder=3)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f"{lbl[(d['a'], d['b'])]}, {d['label']} (n {d['n_fire']})"
                        for d in rows][::-1], color=INK_BRIGHT, fontsize=8)
    ax = axes[1]
    _axes(ax, "Learned offset (points)", "", "percent-conifer offset")
    for i, (c, col, face) in enumerate((("r3_pc_offset", BLUE, BLUE),
                                        ("r3_pc_offset_shuffled", MUTED, FIG_BG))):
        v = offs[c]
        ax.scatter(i + np.random.default_rng(i).uniform(-0.12, 0.12, len(v)), v, s=28,
                   color=face, edgecolor=col, lw=1.2, zorder=3)
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["real imagery", "shuffled twin"], color=INK, fontsize=8.5)
    ax = axes[2]
    _axes(ax, "Imagery part on seeded tiles", "tile mean (points)", "SD within tile")
    stats = {}
    for c, col, face, tag in (("r3_pc_offset", BLUE, BLUE, "real imagery"),
                              ("r3_pc_offset_shuffled", MUTED, FIG_BG, "shuffled twin")):
        q = _imagery_part(W.run, c)
        ax.scatter(q[:, 0], q[:, 1], s=20, color=face, edgecolor=col, lw=1, alpha=0.85,
                   label=tag, zorder=3)
        stats[c] = {"median_mean": float(np.median(q[:, 0])),
                    "median_sd": float(np.median(q[:, 1])), "tiles": len(q)}
    for b in (-30, 30):
        ax.axvline(b, color=AMBER, lw=1, ls="--")
    ax.set_xlim(-33, 33)
    ax.legend(loc="lower right", frameon=False, labelcolor=INK, fontsize=8)
    fig.suptitle("E-57  Percent conifer with an imagery-free offset", color=INK_BRIGHT,
                 x=0.01, y=1.04, ha="left", fontsize=12)
    _caption(fig, "Orange = M-1/M-2 pixels (E-57's registered outcome); blue = all pixels. "
             "The offset is a learned constant per fit; the imagery part is what the head adds "
             "on top. All values are our reconstruction.", y=-0.05)
    _save(fig, out, "offset.png")
    return rows, offs, stats


def p7c_curing(W, out):
    plt = _plt()
    rows = []
    for fam, lab in (("O", "O-1 pixels"), (None, "all pixels")):
        for a, b in (("r3_curing_cwfis", "r3_curing_cwfis_shuffled"),
                     ("r3_curing_cwfis", "r2_cwfis"), ("r3_curing_cwfis_shuffled", "r2_cwfis")):
            d = W.paired_on(a, b, fam)
            d["label"] = lab
            rows.append(d)
    pooled = {}
    for c in ("r2_cwfis", "r3_curing_cwfis", "r3_curing_cwfis_shuffled"):
        v = [r["metrics"]["score"]["by_fuel"]["O"] for r in W.fits[c]]
        pooled[c] = {"auc_pooled_O": float(np.nanmean([x["auc_pooled"] for x in v])),
                     "n_px_O": int(np.median([x["n_px"] for x in v]))}
    fig, ax = plt.subplots(figsize=(8.5, 3.9), facecolor=FIG_BG)
    _axes(ax, "Paired within-patch change (95 % CI)")
    ax.axvline(0, color=INK, lw=0.8)
    lbl = {("r3_curing_cwfis", "r3_curing_cwfis_shuffled"): "curing arm minus its twin",
           ("r3_curing_cwfis", "r2_cwfis"): "curing arm minus R2 (CWFIS fuel)",
           ("r3_curing_cwfis_shuffled", "r2_cwfis"): "twin minus R2 (CWFIS fuel)"}
    for i, d in enumerate(rows):
        y = len(rows) - 1 - i
        col = ORANGE if d["fam"] == "O" else BLUE
        lo, hi = d["ci"]
        ax.plot([lo, hi], [y, y], color=col, lw=2, solid_capstyle="round", zorder=2)
        ax.scatter([d["d"]], [y], s=50, color=col, edgecolor=FIG_BG, lw=1.3, zorder=3)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f"{lbl[(d['a'], d['b'])]}, {d['label']} (n {d['n_fire']})"
                        for d in rows][::-1], color=INK_BRIGHT, fontsize=8)
    fig.suptitle("E-38  Curing corrected from imagery, on CWFIS fuel (which has O-1)",
                 color=INK_BRIGHT, x=0.01, y=1.04, ha="left", fontsize=12)
    _caption(fig, "Orange = O-1 grass pixels (E-38's registered outcome), within-patch on fire "
             "patches that have burned and unburned O-1; blue = all pixels. Compared with the "
             "80 % FBP default, not the CWFIS curing product (not held). Ours throughout.",
             y=-0.05)
    _save(fig, out, "curing.png")
    return rows, pooled


def p7c_tiles(W, out):
    from matplotlib.colors import LinearSegmentedColormap, ListedColormap, TwoSlopeNorm
    plt = _plt()
    seq = LinearSegmentedColormap.from_list("seq", ["#151b2b", "#1f4f8f", BLUE, "#bcd8fb"])
    div = LinearSegmentedColormap.from_list("div", [ORANGE, "#5a5f70", BLUE])
    cols = [("rgb", "Sentinel-2 true colour"), ("label", "NBAC burned on/after D"),
            ("r1:pred", "R1"), ("r2:pred", "R2 zero start"), ("r2_warm:pred", "R2 from R1"),
            ("r2_lr10:pred", "R2 10x rate"), ("r3_pc_offset:delta_pc", "PC: imagery part"),
            ("r3_pc_offset_shuffled:delta_pc", "PC: twin's part")]
    Z = {c: [np.load(W.run / c / f"f{f}s0" / "samples.npz") for f in range(5)]
         for c in ("r1", "r2", "r2_warm", "r2_lr10", "r3_pc_offset", "r3_pc_offset_shuffled")}
    fig, axes = plt.subplots(5, len(cols), figsize=(2.05 * len(cols), 2.2 * 5),
                             facecolor=FIG_BG, gridspec_kw={"wspace": 0.04, "hspace": 0.16,
                                                            "top": 0.9, "bottom": 0.12})
    im_s = im_d = None
    for f in range(5):
        base = Z["r2"][f]
        stem = str(base["stems"][0])
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
                    im_d = ax.imshow(np.clip(a, -30, 30), cmap=div,
                                     norm=TwoSlopeNorm(0, -30, 30), interpolation="nearest")
                else:
                    im_s = ax.imshow(_pct(a), cmap=seq, vmin=0, vmax=1, interpolation="nearest")
            if f == 0:
                ax.set_title(lab, color=INK, fontsize=8, loc="left")
            if c == 0:
                ax.set_ylabel(f"fold {f}\n" + stem.replace("_fire_tile", "\n"), color=INK,
                              fontsize=6.5)
    for im, (c0, c1), lab in ((im_s, (2, 5), "score percentile within the tile"),
                              (im_d, (6, 7), "imagery part of the PC correction (points)")):
        if im is not None:
            a, b = axes[-1, c0].get_position(), axes[-1, c1].get_position()
            cax = fig.add_axes([a.x0 + 0.01, a.y0 - 0.028, b.x1 - a.x0 - 0.02, 0.008])
            cb = fig.colorbar(im, cax=cax, orientation="horizontal")
            cb.set_label(lab, color=INK, fontsize=8)
            cb.ax.tick_params(colors=INK, labelsize=7.5)
    fig.suptitle("P7c  The same seeded fire tile per fold, every new arm (seed 0)",
                 color=INK_BRIGHT, x=0.01, y=0.975, ha="left", fontsize=12)
    _caption(fig, "True colour: the v2 pack's pre-fire composite (S2 SR median, D-45..D-1, "
             "B4/B3/B2). White = burned on or after D; grey = ignored or invalid. Scores as "
             "percentiles within the tile. The PC columns show only the imagery part, without "
             "the learned offset. All maps are our models.", y=0.025)
    _save(fig, out, "tiles.png")


def p7c_resources(run):
    import re
    rows = []
    for f in sorted((run / "tasks").glob("*/resource_usage.csv")):
        R = _read_csv(f)
        if not R:
            continue
        def num(k, rows=R):
            return [float(r[k]) for r in rows if (r.get(k) or "").strip()]
        g, m, c = num("gpu_util_%"), num("gpu_mem_used_MiB"), num("cpu_util_%")
        log = next(f.parent.glob("job-*.out"), None)
        setup = None
        if log is not None:
            s = re.search(r"setup took (\d+)s", log.read_text(errors="ignore"))
            setup = int(s.group(1)) if s else None
        rows.append({"task": f.parent.name, "minutes": len(R) * 0.5,
                     "gpu_util_median": float(np.median(g)) if g else float("nan"),
                     "gpu_mem_peak": max(m) if m else float("nan"),
                     "cpu_util_median": float(np.median(c)) if c else float("nan"),
                     "setup_s": setup})
    return rows


def p7c_tables(W, out, lv, pr, off, offs, ostats, cur, pooled, res):
    L = ["# P7c tables: the second slot sweep (slots_v3)\n",
         f"Run: `{_rel(W.run)}`. {len(W.pat)} development patches, 5 folds x 3 seeds; "
         "r2_warm lacks fold 4 seeds 1-2 (OOM-killed at 16G). Every number is our "
         "reconstruction unless marked ISSUED by CWFIS.\n",
         "## E-58: R2's gap to R1\n",
         "| rung (ours) | within-patch AUC | 95 % CI | between-patch AUC | 95 % CI |",
         "|---|---|---|---|---|"]
    for (_c, lab), d in zip(GAP, lv, strict=True):
        L.append(f"| {lab} | {d['within']:.3f} | {_ci(d['within_ci'], 3)} | "
                 f"{d['between']:.3f} | {_ci(d['between_ci'], 3)} |")
    L += ["", "| a - b | within | 95 % CI | folds won | between | 95 % CI | folds won |",
          "|---|---|---|---|---|---|---|"]
    for (a, b), d in pr.items():
        L.append(f"| {a} - {b} | {d['d_within']:+.4f} | {_ci(d['d_within_ci'], 4)} | "
                 f"{d['folds_won_within']}/5 | {d['d_between']:+.4f} | "
                 f"{_ci(d['d_between_ci'], 4)} | {d['folds_won_between']}/5 |")
    if (PATCHES / f"{W.pat[0]}_cwfis_grid.json").exists():
        L.append(f"\nBetween-patch reference, FWI ISSUED by CWFIS for D-1 (per fold, 188 "
                 f"covered patches): {_op_between(W):.3f}.")
    _csv(out / "T_gap.csv", [dict(d, a=a, b=b) for (a, b), d in pr.items()])
    L += ["", "## E-57: percent conifer with an imagery-free offset\n",
          "| comparison | pixels | n fires | within-patch change | 95 % CI |",
          "|---|---|---|---|---|"]
    for d in off:
        L.append(f"| {d['a']} - {d['b']} | {d['label']} | {d['n_fire']} | {d['d']:+.4f} | "
                 f"{_ci(d['ci'], 4)} |")
    for c, v in offs.items():
        L.append(f"\n{c}: learned offset median {np.median(v):+.1f} points "
                 f"[{min(v):+.1f}, {max(v):+.1f}]; imagery part on seeded tiles: median tile "
                 f"mean {ostats[c]['median_mean']:+.2f}, median within-tile SD "
                 f"{ostats[c]['median_sd']:.2f} ({ostats[c]['tiles']} tiles).")
    _csv(out / "T_offset.csv", off)
    L += ["", "## E-38: curing on CWFIS fuel\n",
          "| comparison | pixels | n fires | within-patch change | 95 % CI |",
          "|---|---|---|---|---|"]
    for d in cur:
        L.append(f"| {d['a']} - {d['b']} | {d['label']} | {d['n_fire']} | {d['d']:+.4f} | "
                 f"{_ci(d['ci'], 4)} |")
    L += ["", "Pooled AUC on O-1 pixels (mean over fits): " + "; ".join(
        f"{c} {v['auc_pooled_O']:.3f} (median {v['n_px_O']:,} O-1 px per fold)"
        for c, v in pooled.items()) + "."]
    _csv(out / "T_curing.csv", cur)
    L += ["", "## Resources (A100; per task of up to 3 fits)\n",
          "| measure | median | max |", "|---|---|---|"]
    for k, lab in (("minutes", "task length (min)"), ("gpu_util_median", "GPU utilisation (%)"),
                   ("gpu_mem_peak", "peak GPU memory (MiB)"),
                   ("cpu_util_median", "node CPU utilisation (%)"), ("setup_s", "setup (s)")):
        v = [r[k] for r in res if r[k] is not None and np.isfinite(r[k])]
        L.append(f"| {lab} | {np.median(v):.0f} | {max(v):.0f} |")
    L += ["", "| configuration | fits | median wall (s) | max wall (s) |", "|---|---|---|---|"]
    for c in sorted(W.fits):
        ws = [r["wall_s"] for r in W.fits[c]]
        L.append(f"| {c} | {len(ws)} | {np.median(ws):.0f} | {max(ws):.0f} |")
    _csv(out / "T_resources.csv", res)
    (out / "tables.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"  wrote {_rel(out / 'tables.md')}")


def p7c(run: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    W = _Sweep(run)
    lv, pr = p7c_gap(W, out)
    off, offs, ostats = p7c_offset(W, out)
    cur, pooled = p7c_curing(W, out)
    p7c_tiles(W, out)
    res = p7c_resources(run)
    p7c_tables(W, out, lv, pr, off, offs, ostats, cur, pooled, res)
    (out / "summary.json").write_text(json.dumps(
        {"gap_levels": lv, "gap": {f"{a}-{b}": d for (a, b), d in pr.items()},
         "offset": off, "offsets": offs, "offset_tiles": ostats, "curing": cur,
         "curing_pooled": pooled, "resources": res,
         "issued_fwi_between": _op_between(W) if (PATCHES / f"{W.pat[0]}_cwfis_grid.json")
         .exists() else None}, indent=1, default=float))
    (out / "run.json").write_text(json.dumps({"run": str(_rel(run))}, indent=1))


# ── Supplementary: every candidate's search score, every step (P6a, P6c) ───

def _considered(paths: list[dict], sel: str, bands, to_score=lambda v: v, gain_sign=1.0):
    """Per step and band: the mean, min and max over searches of (step 1) the
    band's own score and (step >= 2) its gain over that search's previous step,
    and in how many searches it was still a candidate."""
    n_steps = max(len(p[sel]) for p in paths)
    out = {}
    for k in range(n_steps):
        for b in bands:
            vals = []
            for p in paths:
                st = p[sel][k]
                v = st["considered"].get(b)
                if v is None or not np.isfinite(v):
                    continue
                v = to_score(v)
                if k:
                    v = gain_sign * (v - to_score(p[sel][k - 1]["score"]))
                vals.append(v)
            out[(k + 1, b)] = ((float(np.mean(vals)), float(min(vals)), float(max(vals)),
                                len(vals)) if vals else None)
    return out, n_steps


def _score_heat(ax, C, n_steps, bands, n_runs, fmt, cmap, vmin, vmax, title, chosen_first=None):
    m = np.full((n_steps, len(bands)), np.nan)
    for (k, b), v in C.items():
        if v and v[3] >= n_runs / 2:
            m[k - 1, bands.index(b)] = v[0]
    ax.imshow(np.ma.masked_invalid(m), cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    _axes(ax, title, "", "")
    ax.grid(False)
    ax.set_xticks(range(len(bands)))
    ax.set_xticklabels(bands, color=INK, fontsize=7.5)
    ax.set_yticks(range(n_steps))
    ax.set_yticklabels([("1: alone" if k == 1 else f"{k}: added") for k in range(1, n_steps + 1)],
                       color=INK, fontsize=7.5)
    for i in range(n_steps):
        for j in range(len(bands)):
            if np.isfinite(m[i, j]):
                strong = abs(m[i, j]) > 0.6 * max(abs(vmin), abs(vmax))   # dark at both ends
                ax.text(j, i, fmt(m[i, j]), ha="center", va="center", fontsize=6,
                        color="#ffffff" if strong else "#0f1117")
            else:
                ax.text(j, i, "·", ha="center", va="center", fontsize=7, color=MUTED)


def supp_scores(paths: list[dict], selectors, bands, out: Path, name: str, title: str,
                unit_single: str, unit_gain: str, to_score=lambda v: v, fmt_single="{:.2f}",
                fmt_gain="{:+.3f}", single_range=None, gain_sign=1.0, low_is_good=False):
    """Two figures: every band's score alone (step 1), and every band's gain when added at
    each later step, per search target; plus the numbers as CSV."""
    plt = _plt()
    rows, cs = [], {}
    for sel, _ in selectors:
        C, n_steps = _considered(paths, sel, bands, to_score, gain_sign)
        cs[sel] = (C, n_steps)
        for (k, b), v in C.items():
            if v:
                rows.append({"search": sel, "step": k, "band": b, "mean": v[0], "min": v[1],
                             "max": v[2], "n_searches": v[3],
                             "measure": unit_single if k == 1 else unit_gain})
    _csv(out / f"{name}.csv", rows)
    # Figure 1: alone.
    single = np.array([[cs[s][0][(1, b)][0] if cs[s][0].get((1, b)) else np.nan for b in bands]
                       for s, _ in selectors])
    lo, hi = single_range or (np.nanmin(single), np.nanmax(single))
    fig, ax = plt.subplots(figsize=(11, 0.55 * len(selectors) + 1.6), facecolor=FIG_BG)
    ax.imshow(np.ma.masked_invalid(single), cmap="viridis_r" if low_is_good else "viridis",
              vmin=lo, vmax=hi, aspect="auto")
    _axes(ax, f"{title}: each band alone ({unit_single})", "", "")
    ax.grid(False)
    ax.set_xticks(range(len(bands)))
    ax.set_xticklabels(bands, color=INK, fontsize=8.5)
    ax.set_yticks(range(len(selectors)))
    ax.set_yticklabels([lab for _, lab in selectors], color=INK, fontsize=8.5)
    for i, (s, _) in enumerate(selectors):
        for j, b in enumerate(bands):
            v = cs[s][0].get((1, b))
            if v:
                frac = (v[0] - lo) / (hi - lo) if hi > lo else 0
                frac = 1 - frac if low_is_good else frac
                ax.text(j, i, fmt_single.format(v[0]) + f"\n[{fmt_single.format(v[1])}, "
                        f"{fmt_single.format(v[2])}]", ha="center", va="center", fontsize=6,
                        color="#0f1117" if frac > 0.55 else INK_BRIGHT)
    _caption(fig, f"Step 1 of every search trains one model per band, alone, and scores it on the "
             f"search's inner validation blocks. Cell: mean over {len(paths)} searches, [min, "
             "max] below. The search keeps the best and moves on; this is the score of every "
             "band it tried, not only the winner.", y=0.0)
    _save(fig, out, f"{name}_alone.png")
    # Figure 2: gain when added, per search target.
    n = len(selectors)
    cols = 2 if n > 1 else 1
    r = -(-n // cols)
    fig, axes = plt.subplots(r, cols, figsize=(7.2 * cols, 3.3 * r), facecolor=FIG_BG,
                             squeeze=False)
    gains = [v[0] for C, _ in cs.values() for (k, _), v in C.items() if v and k > 1]
    g = max(abs(min(gains)), abs(max(gains))) if gains else 1
    for ax, (s, lab) in zip(axes.flat, selectors, strict=False):
        C, n_steps = cs[s]
        C2 = {kk: v for kk, v in C.items() if kk[0] > 1}
        _score_heat(ax, {(k - 1, b): v for (k, b), v in C2.items()}, n_steps - 1, bands,
                    len(paths), lambda x: fmt_gain.format(x), "RdBu", -g, g, lab)
        ax.set_yticklabels([f"{k}: added" for k in range(2, n_steps + 1)], color=INK,
                           fontsize=7.5)
    for ax in list(axes.flat)[n:]:
        ax.set_visible(False)
    fig.tight_layout()
    _caption(fig, f"{title}: the gain ({unit_gain}) each band would have given if added at step "
             "k, over that search's own best set from step k-1, mean over searches; blue helps, "
             "red hurts. A band's gain depends on what is already in the set (rule 1), which is "
             "why the deliverable is the nested set, not a per-band ranking. '·': the band was "
             "already chosen in at least half the searches by then.")
    _save(fig, out, f"{name}_added.png")
    return rows


# ── P6a: the ecology estimator band searches (E-22, E-59, E-62 S2 half) ────

ECO_PACK = Path(_ROOT.parent / "Fire_Risk_Model" / "data" / "ecology_v2" / "dev.h5")
ECO_BANDS = ("B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B9", "B11", "B12")
ECO_PATHS = (("combined", "combined skill", BLUE), ("no_red_edge", "no red edge (B5-B7 out)",
                                                     ORANGE))
ECO_TARGETS = (("pc", "percent conifer", "rmse_pc", "RMSE (%)"),
               ("closure", "crown closure", "rmse_closure", "RMSE (%)"),
               ("height", "canopy height", "rmse_height", "RMSE (m)"),
               ("family", "fuel family", "balanced_acc_family", "balanced accuracy"))
ECO_FAMILY_COL = {"C": GREEN, "D": ORANGE, "M": BLUE, "O": AMBER, "S": PINK, "NF": "#b9b9c6",
                  "WA": "#3a3d4a"}
#: E-2's fire-outcome search: the rung at which B11 entered, per fold ("never" = 99).
E2_B11_RUNGS = (99, 3, 2, 5, 2, 7)


class _EcoRun:
    def __init__(self, run: Path):
        self.run = run
        self.tasks = sorted(p for p in run.glob("f*s*") if (p / "eval.jsonl").exists())
        self.rows, self.paths, self.results = [], {}, {}
        for t in self.tasks:
            fold, seed = (int(v) for v in t.name[1:].split("s"))
            for line in (t / "eval.jsonl").read_text().splitlines():
                r = json.loads(line)
                r["fold"], r["seed"] = fold, seed
                self.rows.append(r)
            self.paths[(fold, seed)] = json.loads((t / "search.json").read_text())
            self.results[(fold, seed)] = json.loads((t / "result.json").read_text())
        self.fits = [json.loads(x) for x in (run / "fits.jsonl").read_text().splitlines()]

    def get(self, sel, k, mode, noisy, key="skill_combined"):
        return {(r["fold"], r["seed"]): r["metrics"][key] for r in self.rows
                if r["selector"] == sel and r["k"] == k and r["mode"] == mode
                and r["noisy"] == noisy and r["metrics"]
                and r["metrics"].get(key) is not None and np.isfinite(r["metrics"][key])}

    def first_swir(self, sel="combined"):
        out = {}
        for kk, p in self.paths.items():
            r = [s["k"] for s in p[sel] if s["added"] in ("B11", "B12")]
            out[kk] = min(r) if r else 99
        return out


def p6a_curves(E, out):
    plt = _plt()
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.3), facecolor=FIG_BG, sharey=True)
    summ = {}
    n = len(E.tasks)
    for ax, (mode, mlab) in zip(axes, SNOW_MODES, strict=True):
        _axes(ax, mlab, "bands in the nested set (k)",
              "combined skill (0 = training mean, 1 = perfect)" if mode == "raw" else "")
        for sel, lab, col in ECO_PATHS:
            for noisy, ls in ((True, "-"), (False, ":")):
                ks, m, lo, hi = [], [], [], []
                for k in range(1, 9):
                    d = E.get(sel, k, mode, noisy)
                    if len(d) < n:
                        continue
                    mu, ci, _ = _fold_boot(d)
                    ks.append(k)
                    m.append(mu)
                    lo.append(ci[0])
                    hi.append(ci[1])
                    summ[(sel, k, mode, noisy)] = (mu, ci)
                if ks:
                    ax.plot(ks, m, ls, color=col, lw=2, marker="o" if noisy else None, ms=5,
                            label=f"{lab}{'' if noisy else ', noise-free'}")
                    if noisy:
                        ax.fill_between(ks, lo, hi, color=col, alpha=0.18, lw=0)
        a = E.get("all_bands", 12, mode, True)
        if a:
            mu, ci, _ = _fold_boot(a)
            summ[("all_bands", 12, mode, True)] = (mu, ci)
            ax.axhline(mu, color=MUTED, lw=1.2, ls="--")
            ax.text(8.1, mu, f"all 12 bands {mu:.3f}", color=MUTED, fontsize=7.5, ha="right",
                    va="bottom")
        ax.set_xticks(range(1, 9))
        ax.set_ylim(0.2, 0.52)
    axes[0].legend(fontsize=7.5, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK,
                   loc="lower right")
    fig.suptitle("E-22 / E-59: ecology skill (SCANFI v2 2020 labels) by nested Sentinel-2 band set",
                 color=INK_BRIGHT, fontsize=11.5, x=0.01, ha="left", y=1.03)
    _caption(fig, f"Mean over {n} runs (5 outer folds of 1-degree blocks x 3 seeds); band = 95 % "
             "CI resampling whole folds. Combined skill = mean of the skills for percent "
             "conifer, closure, height (1 - RMSE / RMSE of the training mean) and fuel family "
             "(balanced accuracy, chance = 0). Solid: with the placeholder sensor noise (rule 6); "
             "dotted: noise-free. 'Indices only' starts where every run's set forms an index.")
    _save(fig, out, "curves.png")
    return summ


def p6a_targets(E, out):
    plt = _plt()
    fig, axes = plt.subplots(2, 2, figsize=(12, 7.6), facecolor=FIG_BG)
    rows = []
    n = len(E.tasks)
    for ax, (t, tlab, key, ylab) in zip(axes.flat, ECO_TARGETS, strict=True):
        _axes(ax, tlab, "bands in the nested set (k)", ylab)
        for sel, lab, col in (*ECO_PATHS, (t, f"searched for {tlab}", GREEN)):
            ks, m, lo, hi = [], [], [], []
            for k in range(1, 9):
                d = E.get(sel, k, "raw+indices", True, key)
                if len(d) < n:
                    continue
                mu, ci, _ = _fold_boot(d)
                ks.append(k)
                m.append(mu)
                lo.append(ci[0])
                hi.append(ci[1])
                rows.append({"target": t, "path": sel, "k": k, "value": mu, "ci": ci})
            ax.plot(ks, m, "-o", color=col, lw=2, ms=4, label=lab)
            ax.fill_between(ks, lo, hi, color=col, alpha=0.15, lw=0)
        a = E.get("all_bands", 12, "raw+indices", True, key)
        if a:
            mu, ci, _ = _fold_boot(a)
            rows.append({"target": t, "path": "all_bands", "k": 12, "value": mu, "ci": ci})
            ax.axhline(mu, color=MUTED, lw=1.2, ls="--")
            ax.text(8.1, mu, "all 12 bands", color=MUTED, fontsize=7.5, ha="right", va="bottom")
        ax.set_xticks(range(1, 9))
        ax.legend(fontsize=7, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK,
                  loc="lower right" if t == "family" else "upper right")
    fig.tight_layout()
    _caption(fig, "Raw + indices, with sensor noise; mean over runs, 95 % CI resampling whole "
             "folds. Green: the nested path searched for that target alone. Lower RMSE is "
             "better; higher balanced accuracy is better. Fuel family is scored over the "
             "classes with at least 200 pixels in the outer fold (chance = 1 / classes).")
    _save(fig, out, "targets.png")
    return rows


def p6a_selection(E, out):
    plt = _plt()
    sels = [("combined", "combined skill"), ("no_red_edge", "no red edge"),
            ("pc", "percent conifer"), ("closure", "closure"), ("height", "height"),
            ("family", "fuel family")]
    fig, axes = plt.subplots(2, 3, figsize=(13.5, 8.2), facecolor=FIG_BG)
    freq = {}
    for ax, (sel, lab) in zip(axes.flat, sels, strict=True):
        m = np.zeros((len(ECO_BANDS), 8))
        for p in E.paths.values():
            for s in p[sel]:
                m[ECO_BANDS.index(s["added"]), s["k"] - 1] += 1
        m /= len(E.paths)
        freq[sel] = {b: m[i].tolist() for i, b in enumerate(ECO_BANDS)}
        ax.imshow(m, cmap="Blues", vmin=0, vmax=1, aspect="auto")
        _axes(ax, f"{lab}: band added at step k", "step k", "")
        ax.grid(False)
        ax.set_yticks(range(len(ECO_BANDS)))
        ax.set_yticklabels(ECO_BANDS, color=INK, fontsize=8)
        ax.set_xticks(range(8))
        ax.set_xticklabels(range(1, 9))
        for i in range(len(ECO_BANDS)):
            for j in range(8):
                if m[i, j] >= 0.2:
                    ax.text(j, i, f"{m[i, j]:.0%}", ha="center", va="center", fontsize=6.5,
                            color="#0f1117" if m[i, j] < 0.6 else "#ffffff")
    fig.tight_layout()
    _caption(fig, f"Share of the {len(E.paths)} searches (inner block split of each outer fold's "
             "training blocks; raw + indices, with noise) that added each band at each step. "
             "Bands in wavelength order, B11 = 1610 nm, B12 = 2190 nm.")
    _save(fig, out, "selection.png")
    return freq


def _paired(E, sel_a, mode_a, sel_b, mode_b, key, k_b=None, n=None):
    """Paired a - b per k over the runs both have."""
    rows = []
    for k in range(1, 9):
        a = E.get(sel_a, k, mode_a, True, key)
        b = E.get(sel_b, k if k_b is None else k_b, mode_b, True, key)
        keys = sorted(set(a) & set(b))
        if n and len(keys) < n:
            continue
        if len(keys) < 3:
            continue
        mu, ci, per = _fold_boot({kk: a[kk] - b[kk] for kk in keys})
        rows.append({"k": k, "d": mu, "ci": ci, "folds_positive": int((per > 0).sum()),
                     "n_folds": len(per), "runs": len(keys)})
    return rows


def p6a_indices(E, out):
    """E-59: raw + indices against raw at the same bands (the combined path)."""
    plt = _plt()
    keys = [("skill_combined", "combined"), ("skill_pc", "percent conifer"),
            ("skill_closure", "closure"), ("skill_height", "height"),
            ("skill_family", "fuel family")]
    cols = (INK_BRIGHT, GREEN, BLUE, AMBER, PINK)
    res = {}
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.4), facecolor=FIG_BG)
    _axes(a1, "raw + indices minus raw (same bands)", "bands in the nested set (k)",
          "difference in skill")
    _axes(a2, "indices only minus raw + indices (same bands)", "bands in the nested set (k)", "")
    for i, ((key, lab), col) in enumerate(zip(keys, cols, strict=True)):
        off = (i - 2) * 0.09
        r1 = _paired(E, "combined", "raw+indices", "combined", "raw", key, n=len(E.tasks))
        r2 = _paired(E, "combined", "indices", "combined", "raw+indices", key)
        res[key] = {"rawind_minus_raw": r1, "ind_minus_rawind": r2}
        for ax, rr in ((a1, r1), (a2, r2)):
            if not rr:
                continue
            ax.errorbar([r["k"] + off for r in rr], [r["d"] for r in rr],
                        yerr=[[r["d"] - r["ci"][0] for r in rr], [r["ci"][1] - r["d"] for r in rr]],
                        fmt="o", color=col, ms=4, capsize=2, lw=1.2, label=lab)
    for ax in (a1, a2):
        ax.axhline(0, color=SPINE, lw=1)
        ax.set_xticks(range(1, 9))
    a1.legend(fontsize=7.5, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK, loc="upper left")
    _caption(fig, "Paired by fold and seed on the combined path's nested sets, with sensor "
             "noise; 95 % CI resampling whole folds. Left: does adding every formable index "
             "help the network at matched bands (E-59)? Right: indices alone, against raw + "
             "indices; only sets that form an index in at least 3 runs. Above 0 favours the "
             "first named.")
    _save(fig, out, "indices.png")
    return res


def p6a_red_edge(E, out):
    """E-62, Sentinel-2 half: the no-red-edge path against the combined path, in RMSE."""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(9, 4.3), facecolor=FIG_BG)
    _axes(ax, "No red edge (B5, B6, B7 excluded) minus combined path, at matched k",
          "bands in the nested set (k)", "RMSE difference (% of the combined path's)")
    res = {}
    for i, ((t, lab, key, _), col) in enumerate(zip(ECO_TARGETS[:3], (GREEN, BLUE, AMBER),
                                                    strict=True)):
        rows = []
        for k in range(1, 9):
            a, b = E.get("no_red_edge", k, "raw+indices", True, key), \
                E.get("combined", k, "raw+indices", True, key)
            keys = sorted(set(a) & set(b))
            if len(keys) < len(E.tasks):
                continue
            mu, ci, per = _fold_boot({kk: 100 * (a[kk] - b[kk]) / b[kk] for kk in keys})
            rows.append({"k": k, "d_pct": mu, "ci": ci, "folds_worse": int((per > 0).sum()),
                         "n_folds": len(per)})
        res[t] = rows
        off = (i - 1) * 0.12
        ax.errorbar([r["k"] + off for r in rows], [r["d_pct"] for r in rows],
                    yerr=[[r["d_pct"] - r["ci"][0] for r in rows],
                          [r["ci"][1] - r["d_pct"] for r in rows]],
                    fmt="o", color=col, ms=5, capsize=3, lw=1.3, label=lab)
    ax.axhline(5, color=MUTED, lw=1, ls="--")
    ax.axhline(0, color=SPINE, lw=1)
    ax.text(0.7, 5.15, "E-62: at least 5 % worse without red edge", color=MUTED, fontsize=7.5,
            va="bottom")
    ax.set_xticks(range(1, 9))
    ax.legend(fontsize=7.5, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK, loc="upper right")
    _caption(fig, "Raw + indices, with sensor noise; paired by fold and seed, 95 % CI resampling "
             "whole folds. Above 0: the set without red edge has the larger error. Both paths may "
             "use SWIR, so this is E-62's Sentinel-2 half only; the VNIR-camera question (no "
             "SWIR) waits for the AVIRIS-NG search.", y=-0.03)
    _save(fig, out, "red_edge.png")
    return res


def p6a_tiles(out, n=4, seed=0):
    """Qualitative: true colour and the SCANFI labels the estimators learn, on seeded
    development tiles. The runner saves no predictions, so there is no model map."""
    import h5py
    plt = _plt()
    from matplotlib.colors import ListedColormap
    with h5py.File(ECO_PACK, "r") as f:
        order = [str(b) for b in f.attrs["band_order"]]
        fams = [str(x) for x in f.attrs["families"]]
        valid_share = f["valid"][:, ::16, ::16].reshape(len(f["valid"]), -1).mean(axis=1)
        cand = np.flatnonzero(valid_share > 0.8)
        pick = np.sort(np.random.default_rng(seed).choice(cand, n, replace=False))
        bands = f["bands"][pick].astype(np.float32)
        tg = f["targets"][pick]
        fam = f["fuel_family"][pick]
        meta = [json.loads(m) for m in f["meta"][pick]]
    cols = [("true colour (B4, B3, B2)", None), ("percent conifer (%)", 0),
            ("crown closure (%)", 1), ("canopy height (m)", 2), ("fuel family", "fam")]
    fig, axes = plt.subplots(n, len(cols), figsize=(15, 3.1 * n), facecolor=FIG_BG)
    fcmap = ListedColormap([ECO_FAMILY_COL[x] for x in fams])
    for i in range(n):
        for j, (lab, c) in enumerate(cols):
            ax = axes[i, j]
            ax.set_facecolor(AX_BG)
            ax.set_xticks([])
            ax.set_yticks([])
            for s in ax.spines.values():
                s.set_color(SPINE)
            if c is None:
                ax.imshow(_stretch(np.stack([bands[i, order.index(b)]
                                             for b in ("B4", "B3", "B2")])))
            elif c == "fam":
                fm = np.ma.masked_less(fam[i].astype(float), 0)
                ax.imshow(fm, cmap=fcmap, vmin=-0.5, vmax=len(fams) - 0.5, interpolation="nearest")
            else:
                vmax = {0: 100, 1: 100, 2: 30}[c]
                im = ax.imshow(np.ma.masked_invalid(tg[i, c]), cmap="viridis", vmin=0, vmax=vmax)
                if i == n - 1:
                    cb = fig.colorbar(im, ax=ax, orientation="horizontal", fraction=0.05,
                                      pad=0.04)
                    cb.ax.tick_params(colors=INK, labelsize=7)
            if i == 0:
                ax.set_title(lab, color=INK_BRIGHT, fontsize=9.5, loc="left")
            if j == 0:
                kind = meta[i]["patch"].split("_ecology_")[-1].replace("_", " ")
                ax.set_ylabel(f"{kind}\nblock {meta[i]['block']}", color=MUTED, fontsize=8)
    handles = [plt.Rectangle((0, 0), 1, 1, color=ECO_FAMILY_COL[x]) for x in fams]
    fig.legend(handles, fams, loc="lower right", ncol=len(fams), fontsize=8, facecolor=AX_BG,
               edgecolor=SPINE, labelcolor=INK, bbox_to_anchor=(0.99, -0.005))
    _caption(fig, "Four seeded development tiles (256 x 256 px at 20 m), Sentinel-2 June-August "
              "2020 composite and the SCANFI v2 2020 labels the estimators were trained on (fuel "
              "family from the CFS decision tree; C conifer, D deciduous, M mixedwood, O open, S "
              "slash, NF non-fuel, WA water). The tree gives every open pixel (closure < 10 %) "
              "the D-1/2 code, so glacier, rock and tundra read as D (rows 2 and 4): 82 % of D "
              "pixels in the pack. Row labels are the patch's sampling stratum, not its SCANFI "
              "class. Data only: the sweep saves no prediction maps.",
             y=-0.01)
    _save(fig, out, "tiles.png")
    return [m["patch"] for m in meta]


ECO_MAP_SETS = (("combined_k1", "k = 1"), ("combined_k3", "k = 3"), ("combined_k6", "k = 6"),
                ("no_red_edge_k6", "k = 6, no red edge"), ("all_bands", "all 12 bands"))
ECO_MAP_TARGETS = (("pc", 0, "percent conifer (%)", 100, "%"),
                   ("closure", 1, "crown closure (%)", 100, "%"),
                   ("height", 2, "canopy height (m)", 30, "m"))


def _load_eco_maps(maps_dir: Path, per_fold: int = 1):
    """One or more held-out tiles per fold from predict_eco_maps.py outputs."""
    tiles = []
    for d in sorted(p for p in maps_dir.glob("f*s*") if (p / "maps.npz").exists()):
        z = np.load(d / "maps.npz")
        meta = json.loads((d / "maps.json").read_text())
        for i in range(min(per_fold, z["label"].shape[0])):
            t = {"fold": meta["fold"], "patch": meta["tiles"][i]["patch"],
                 "block": meta["tiles"][i]["block"], "rgb": z["bands_rgb"][i].astype(np.float32),
                 "label": z["label"][i], "family": z["family"][i], "valid": z["valid"][i],
                 "families": meta["families"], "sets": {}}
            for s, info in meta["sets"].items():
                t["sets"][s] = {"bands": info["bands"], "err": info["tile_errors"][i],
                                **{k: z[f"{s}__{k}"][i] for k in
                                   ("pc", "closure", "height", "family", "family_p")}}
            tiles.append(t)
    return tiles


def _blank(ax):
    ax.set_facecolor(AX_BG)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(SPINE)


def p6a_maps(maps_dir: Path, out: Path):
    """Labelled images: SCANFI label against each nested set's prediction on
    held-out tiles, one figure per target (E-22, E-62)."""
    plt = _plt()
    from matplotlib.colors import ListedColormap
    tiles = _load_eco_maps(maps_dir)
    if not tiles:
        return []
    made = []
    sets = [s for s in ECO_MAP_SETS if s[0] in tiles[0]["sets"]]
    for name, j, lab, vmax, unit in ECO_MAP_TARGETS:
        cols = 3 + len(sets)
        fig, axes = plt.subplots(len(tiles), cols, figsize=(2.35 * cols, 2.55 * len(tiles)),
                                 facecolor=FIG_BG, squeeze=False)
        for r, t in enumerate(tiles):
            v = t["valid"]
            y = np.where(v, t["label"][j], np.nan)
            panels = [("true colour", None), ("SCANFI label", y)] + [
                (slab, np.where(v, t["sets"][s][name], np.nan)) for s, slab in sets]
            for c, (title, img) in enumerate(panels):
                ax = axes[r, c]
                _blank(ax)
                if img is None:
                    ax.imshow(_stretch(t["rgb"]))
                    ax.set_ylabel(f"fold {t['fold']}\nblock {t['block']}", color=MUTED,
                                  fontsize=7.5)
                else:
                    im = ax.imshow(np.ma.masked_invalid(img), cmap="viridis", vmin=0, vmax=vmax)
                if c >= 2:
                    s = sets[c - 2][0]
                    e = t["sets"][s]["err"].get(f"rmse_{name}")
                    ax.text(0.02, 0.02, f"RMSE {e:.1f} {unit}" if e is not None else "",
                            transform=ax.transAxes, color=INK_BRIGHT, fontsize=7,
                            bbox={"facecolor": FIG_BG, "alpha": 0.7, "lw": 0, "pad": 1.5})
                    if len(t["sets"][s]["bands"]) <= 6:
                        ax.text(0.02, 0.98, " ".join(t["sets"][s]["bands"]),
                                transform=ax.transAxes, color=INK_BRIGHT, fontsize=6, va="top",
                                bbox={"facecolor": FIG_BG, "alpha": 0.7, "lw": 0, "pad": 1.5})
                if r == 0:
                    ax.set_title(title, color=INK_BRIGHT, fontsize=8.5, loc="left")
            # error of the k = 6 set (or the last set present)
            ref = "combined_k6" if "combined_k6" in t["sets"] else sets[-1][0]
            d = np.where(v, t["sets"][ref][name] - t["label"][j], np.nan)
            ax = axes[r, cols - 1]
            _blank(ax)
            em = ax.imshow(np.ma.masked_invalid(d), cmap="RdBu_r", vmin=-vmax / 2, vmax=vmax / 2)
            if r == 0:
                ax.set_title(f"error, {dict(sets).get(ref, ref)}", color=INK_BRIGHT, fontsize=8.5,
                             loc="left")
        cb = fig.colorbar(im, ax=axes[:, 1:cols - 1], orientation="horizontal", fraction=0.025,
                          pad=0.02, aspect=60)
        cb.set_label(lab, color=INK, fontsize=8)
        cb.ax.tick_params(colors=INK, labelsize=7)
        cb2 = fig.colorbar(em, ax=axes[:, cols - 1], orientation="horizontal", fraction=0.025,
                           pad=0.02)
        cb2.set_label(f"prediction - label ({unit})", color=INK, fontsize=8)
        cb2.ax.tick_params(colors=INK, labelsize=7)
        fig.suptitle(f"P6a, {lab}: SCANFI label and each nested set's prediction on HELD-OUT "
                     "tiles", color=INK_BRIGHT, fontsize=11, x=0.01, ha="left", y=1.0)
        _caption(fig, "One held-out tile per outer fold (never seen in training or band "
                 "selection). Each set refitted on its fold's training tiles as the sweep did "
                 "(raw + indices, with sensor noise); bands top-left, tile RMSE bottom-left. "
                 "Last column: the k = 6 set's error, red over-predicted, blue under.",
                 y=0.0)
        _save(fig, out, f"maps_{name}.png")
        made.append(f"maps_{name}.png")
    # fuel family
    fams = tiles[0]["families"]
    fcmap = ListedColormap([ECO_FAMILY_COL[x] for x in fams])
    cols = 3 + len(sets)
    fig, axes = plt.subplots(len(tiles), cols, figsize=(2.35 * cols, 2.55 * len(tiles)),
                             facecolor=FIG_BG, squeeze=False)
    for r, t in enumerate(tiles):
        v = t["valid"]
        lab_f = np.where(v & (t["family"] >= 0), t["family"], -1).astype(float)
        panels = [("true colour", None), ("SCANFI fuel family", lab_f)] + [
            (slab, np.where(v, t["sets"][s]["family"], -1).astype(float)) for s, slab in sets]
        for c, (title, img) in enumerate(panels):
            ax = axes[r, c]
            _blank(ax)
            if img is None:
                ax.imshow(_stretch(t["rgb"]))
                ax.set_ylabel(f"fold {t['fold']}\nblock {t['block']}", color=MUTED, fontsize=7.5)
            else:
                ax.imshow(np.ma.masked_less(img, 0), cmap=fcmap, vmin=-0.5,
                          vmax=len(fams) - 0.5, interpolation="nearest")
            if c >= 2:
                acc = t["sets"][sets[c - 2][0]]["err"].get("family_acc")
                ax.text(0.02, 0.02, f"agreement {acc:.0%}" if acc is not None else "",
                        transform=ax.transAxes, color=INK_BRIGHT, fontsize=7,
                        bbox={"facecolor": FIG_BG, "alpha": 0.7, "lw": 0, "pad": 1.5})
            if r == 0:
                ax.set_title(title, color=INK_BRIGHT, fontsize=8.5, loc="left")
        ref = "combined_k6" if "combined_k6" in t["sets"] else sets[-1][0]
        ok = v & (t["family"] >= 0)
        agree = np.where(ok, (t["sets"][ref]["family"] == t["family"]).astype(float), np.nan)
        ax = axes[r, cols - 1]
        _blank(ax)
        ax.imshow(np.ma.masked_invalid(agree), cmap=ListedColormap(["#ffffff", "#2b2f3a"]),
                  vmin=0, vmax=1, interpolation="nearest")
        if r == 0:
            ax.set_title("disagreement, k = 6", color=INK_BRIGHT, fontsize=8.5, loc="left")
    handles = [plt.Rectangle((0, 0), 1, 1, color=ECO_FAMILY_COL[x]) for x in fams]
    handles.append(plt.Rectangle((0, 0), 1, 1, color="#ffffff"))
    fig.legend(handles, [*fams, "k = 6 disagrees"], loc="lower right", ncol=len(fams) + 1,
               fontsize=7.5, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK,
               bbox_to_anchor=(0.99, -0.01))
    fig.suptitle("P6a, fuel family: SCANFI (CFS tree) and each nested set's prediction on "
                 "HELD-OUT tiles", color=INK_BRIGHT, fontsize=11, x=0.01, ha="left", y=1.0)
    _caption(fig, "As the regression maps. D includes all open ground under 10 % closure "
             "(P6a-M1). Pixel agreement bottom-left; last column marks where the k = 6 set "
             "disagrees with SCANFI.", y=-0.02)
    _save(fig, out, "maps_family.png")
    made.append("maps_family.png")
    return made


def p6a_resources(E):
    rows = []
    # A packed sweep logs per job, under <run>/_jobs (A-43).
    for t in [x for x in E.tasks if (x / "resource_usage.csv").exists()] or sorted(
            (E.run / "_jobs").glob("*")):
        R = _read_csv(t / "resource_usage.csv")

        def num(k, rows=R):
            return [float(r[k]) for r in rows if (r.get(k) or "").strip() not in ("", "N/A")]
        g, m = num("gpu_util_%"), num("gpu_mem_used_MiB")
        rows.append({"task": t.name, "gpu_util_median": float(np.median(g)) if g else float("nan"),
                     "gpu_mem_peak": max(m) if m else float("nan"),
                     "job_mem_peak": max(num("job_mem_MiB") or [float("nan")])})
    return rows


def p6a_tables(E, out, summ, trows, freq, idx, red, res):
    L = ["# P6a tables: the ecology estimator band searches (E-22, E-59, E-62 S2 half)\n",
         f"Run: `{_rel(E.run)}` (Nibi, H100). {len(E.tasks)} tasks: 5 outer folds of 1-degree "
         "blocks x 3 seeds, 226 development patches (904 tiles), SCANFI v2 2020 labels, "
         "placeholder sensor noise. The frozen test set (45 patches) was not opened.\n",
         "## Combined skill by nested set (with noise; noise-free in brackets)\n",
         "| path | input | " + " | ".join(f"k={k}" for k in range(1, 9)) + " |",
         "|---|---|" + "---|" * 8]
    for sel, lab, _ in ECO_PATHS:
        for mode, mlab in SNOW_MODES:
            cells = []
            for k in range(1, 9):
                a, b = summ.get((sel, k, mode, True)), summ.get((sel, k, mode, False))
                cells.append("" if a is None else f"{a[0]:.3f} ({b[0]:.3f})" if b else
                             f"{a[0]:.3f}")
            L.append(f"| {lab} | {mlab} | " + " | ".join(cells) + " |")
    L.append("\nAll 12 bands, with noise: " + "; ".join(
        f"{mlab} {summ[('all_bands', 12, m, True)][0]:.3f}" for m, mlab in SNOW_MODES
        if ("all_bands", 12, m, True) in summ) + ".")
    fs = E.first_swir()
    v = sorted(fs.values())
    L += ["", "## E-22: where SWIR enters the combined path\n",
          f"First SWIR band (B11 or B12) at step: {', '.join(str(x) for x in v)} (median "
          f"{np.median(v):g}); step 1 in {sum(x == 1 for x in v)}/{len(v)} runs. E-2's "
          "fire-outcome search had B11 at "
          f"{', '.join('never' if x == 99 else str(x) for x in E2_B11_RUNGS)} "
          f"(median {np.median(E2_B11_RUNGS):g} counting 'never' as last; E-22's clause quotes "
          "3.5).", "",
          "## Per target, combined path (raw + indices, with noise)\n",
          "| target | metric | k=1 | k=2 | k=4 | k=6 | k=8 | all 12 |",
          "|---|---|---|---|---|---|---|---|"]
    for t, tlab, _, ylab in ECO_TARGETS:
        g = {r["k"]: r["value"] for r in trows if r["target"] == t and r["path"] == "combined"}
        a = next((r["value"] for r in trows if r["target"] == t and r["path"] == "all_bands"),
                 float("nan"))
        L.append(f"| {tlab} | {ylab} | " + " | ".join(_f(g.get(k), 2) for k in (1, 2, 4, 6, 8))
                 + f" | {_f(a, 2)} |")
    _csv(out / "T_targets.csv", trows)
    L += ["", "## E-59: raw + indices minus raw, same bands (skill, with noise)\n",
          "| k | combined | percent conifer | closure | height | fuel family |",
          "|---|---|---|---|---|---|"]
    keys = ("skill_combined", "skill_pc", "skill_closure", "skill_height", "skill_family")
    for k in range(1, 9):
        cells = []
        for key in keys:
            r = next((x for x in idx[key]["rawind_minus_raw"] if x["k"] == k), None)
            cells.append("" if r is None else f"{r['d']:+.4f} {_ci(r['ci'], 4)}")
        L.append(f"| {k} | " + " | ".join(cells) + " |")
    _csv(out / "T_indices.csv", [dict(r, metric=key) for key in keys
                                 for r in idx[key]["rawind_minus_raw"]])
    L += ["", "## E-62, Sentinel-2 half: no red edge minus combined (RMSE, % of combined)\n",
          "| k | percent conifer | closure | height |", "|---|---|---|---|"]
    for k in range(1, 9):
        cells = []
        for t in ("pc", "closure", "height"):
            r = next((x for x in red[t] if x["k"] == k), None)
            cells.append("" if r is None else f"{r['d_pct']:+.1f} % {_ci(r['ci'], 1)}")
        L.append(f"| {k} | " + " | ".join(cells) + " |")
    _csv(out / "T_red_edge.csv", [dict(r, target=t) for t, rr in red.items() for r in rr])
    L += ["", "## First three bands chosen (most common, share of searches)\n",
          "| path | step 1 | step 2 | step 3 |", "|---|---|---|---|"]
    for sel, v in freq.items():
        def top(j, v=v):
            s = sorted(((p[j], b) for b, p in v.items()), reverse=True)[:3]
            return ", ".join(f"{b} {p:.0%}" for p, b in s if p > 0)
        L.append(f"| {sel} | {top(0)} | {top(1)} | {top(2)} |")
    walls = [f["wall_s"] / 60 for f in E.fits]
    nf = [f["fits"]["search"] + f["fits"]["eval"] for f in E.fits]
    gpu = [r["gpu_util_median"] for r in res if np.isfinite(r["gpu_util_median"])]
    gm = [r["gpu_mem_peak"] for r in res if np.isfinite(r["gpu_mem_peak"])]
    jm = [r["job_mem_peak"] for r in res if np.isfinite(r["job_mem_peak"])]
    L += ["", "## Resources\n",
          f"Tasks {np.median(walls):.0f} min median, {max(walls):.0f} max (3 h requested); "
          f"{min(nf)}-{max(nf)} fits each. GPU utilisation median {np.median(gpu):.0f} %, peak "
          f"GPU memory {max(gm) / 1024:.1f} GB of 80; peak job memory "
          f"{max(jm) / 1024:.1f} GB of 32."]
    _csv(out / "T_resources.csv", res)
    (out / "tables.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"  wrote {_rel(out / 'tables.md')}")
    return {"walls_min": walls, "fits": nf, "gpu_median": gpu, "gpu_mem_peak": gm,
            "job_mem_peak": jm}


def p6a(run: Path, out: Path, maps: Path | None = None):
    out.mkdir(parents=True, exist_ok=True)
    maps = maps or run / "maps"
    if maps.exists():
        p6a_maps(maps, out)
    E = _EcoRun(run)
    summ = p6a_curves(E, out)
    trows = p6a_targets(E, out)
    freq = p6a_selection(E, out)
    idx = p6a_indices(E, out)
    red = p6a_red_edge(E, out)
    tiles = p6a_tiles(out) if ECO_PACK.exists() else []
    supp_scores(list(E.paths.values()),
                (("combined", "combined skill"), ("no_red_edge", "no red edge"),
                 ("pc", "percent conifer"), ("closure", "closure"), ("height", "height"),
                 ("family", "fuel family")),
                ECO_BANDS, out, "scores", "Ecology searches", "skill", "skill")
    res = p6a_resources(E)
    usage = p6a_tables(E, out, summ, trows, freq, idx, red, res)
    (out / "summary.json").write_text(json.dumps(
        {"curves": {f"{a}|{k}|{m}|{'noisy' if n else 'clean'}": v
                    for (a, k, m, n), v in summ.items()},
         "targets": trows, "selection": freq, "indices": idx, "red_edge": red,
         "first_swir": {f"f{f}s{s}": v for (f, s), v in E.first_swir().items()},
         "tiles": tiles, "resources": usage}, indent=1, default=float))
    (out / "run.json").write_text(json.dumps({"run": str(_rel(run))}, indent=1))


# ── P6c: the snow-off estimator (E-60) ──────────────────────────────────────

SNOW = Path(_ROOT.parent / "Fire_Risk_Model" / "data")
SNOW_ARMS = (("all", "any band (SWIR allowed)", BLUE), ("vnir", "VNIR only (no B11, B12)", ORANGE))
SNOW_MODES = (("raw", "raw bands"), ("indices", "indices only"), ("raw+indices", "raw + indices"))
SNOW_BANDS = ("B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B9", "B11", "B12")


class _SnowRun:
    """One snow sweep: eval rows and search paths per (fold, seed) task."""

    def __init__(self, run: Path):
        self.run = run
        self.tasks = sorted(p for p in run.glob("f*s*") if (p / "eval.jsonl").exists())
        self.rows, self.paths, self.results = [], {}, {}
        for t in self.tasks:
            fold, seed = (int(v) for v in t.name[1:].split("s"))
            for line in (t / "eval.jsonl").read_text().splitlines():
                r = json.loads(line)
                r["fold"], r["seed"] = fold, seed
                self.rows.append(r)
            self.paths[(fold, seed)] = json.loads((t / "search.json").read_text())
            self.results[(fold, seed)] = json.loads((t / "result.json").read_text())
        self.folds = sorted({f for f, _ in self.paths})

    def err(self, arm, k, mode, noisy, key="median_abs_err_days"):
        """{(fold, seed): value} for one nested set."""
        return {(r["fold"], r["seed"]): r["metrics"][key] for r in self.rows
                if r["arm"] == arm and r["k"] == k and r["mode"] == mode
                and r["noisy"] == noisy and r["metrics"]}


def _fold_boot(d: dict, n=4000, seed=0):
    """Mean over runs, and a CI from resampling whole folds (seeds averaged in a fold)."""
    folds = sorted({f for f, _ in d})
    per = np.array([np.mean([v for (f, _), v in d.items() if f == fo]) for fo in folds])
    rng = np.random.default_rng(seed)
    boots = per[rng.integers(0, len(per), (n, len(per)))].mean(axis=1)
    return float(np.mean(list(d.values()))), (float(np.percentile(boots, 2.5)),
                                              float(np.percentile(boots, 97.5))), per


def snow_oracle() -> dict:
    """The sampling floor: the snow-off estimate a PERFECT per-observation classifier
    (the station's own same-day snow on ground) gets, per dev station-year."""
    import csv
    import datetime as dt

    def doy(s):
        return dt.date.fromisoformat(s[:10]).timetuple().tm_yday
    sy = {(r["aes"], int(r["year"])): r for r in
          csv.DictReader(open(SNOW / "snow_v1" / "dev_station_years.csv", encoding="utf-8"))}
    obs: dict = {}
    for r in csv.DictReader(open(SNOW / "snow_v1" / "dev_obs.csv", encoding="utf-8")):
        k = (r["aes"], int(r["year"]))
        if k in sy and r["sog"] not in ("", "nan"):
            obs.setdefault(k, []).append((doy(r["date"]), float(r["sog"]) > 0, float(r["B3"])))
    out = {}
    for k, o in obs.items():
        o.sort()
        d = np.array([x[0] for x in o])
        s = np.array([x[1] for x in o])
        end = dt.date(k[1], 6, 30).timetuple().tm_yday
        snowy = np.where(s & (d <= end))[0]
        if not len(snowy):
            est = float(d[0])
        else:
            i = snowy[-1]
            est = float(d[i]) if i == len(d) - 1 else (d[i] + d[i + 1]) / 2.0
        out[k] = {"err": abs(est - doy(sy[k]["snow_off"])), "est": est,
                  "truth": doy(sy[k]["snow_off"]), "doy": d, "snow": s,
                  "green": np.array([x[2] for x in o]), "lon": float(sy[k]["lon"]),
                  "lat": float(sy[k]["lat"])}
    return out


def p6c_curves(R, oracle, out):
    plt = _plt()
    floor = float(np.median([v["err"] for v in oracle.values()]))
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.3), facecolor=FIG_BG, sharey=True)
    summ = {}
    for ax, (mode, mlab) in zip(axes, SNOW_MODES, strict=True):
        _axes(ax, mlab, "bands in the nested set (k)",
              "median |S2 - station| snow-off (days)" if mode == "raw" else "")
        for arm, lab, col in SNOW_ARMS:
            for noisy, ls in ((True, "-"), (False, ":")):
                ks, m, lo, hi = [], [], [], []
                for k in range(1, 7):
                    d = R.err(arm, k, mode, noisy)
                    if len(d) < len(R.tasks):            # a set with no formable index
                        continue
                    mu, ci, _ = _fold_boot(d)
                    ks.append(k)
                    m.append(mu)
                    lo.append(ci[0])
                    hi.append(ci[1])
                    summ[(arm, k, mode, noisy)] = (mu, ci)
                if not ks:
                    continue
                ax.plot(ks, m, ls, color=col, lw=2, marker="o" if noisy else None, ms=5,
                        label=f"{lab}{'' if noisy else ', noise-free'}")
                if noisy:
                    ax.fill_between(ks, lo, hi, color=col, alpha=0.18, lw=0)
        ax.axhline(7, color=MUTED, lw=1, ls="--")
        ax.axhline(floor, color=GREEN, lw=1.2)
        ax.text(6.05, floor, f"sampling floor {floor:.1f} d", color=GREEN, fontsize=7.5,
                va="bottom", ha="right")
        ax.text(6.05, 7, "E-60 threshold 7 d", color=MUTED, fontsize=7.5, va="top", ha="right")
        ax.set_xticks(range(1, 7))
        ax.set_ylim(0, 32)
    axes[0].legend(fontsize=7.5, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK,
                   loc="upper right")
    fig.suptitle("E-60: snow-off error against ECCC station snow on ground, by nested band set",
                 color=INK_BRIGHT, fontsize=11.5, x=0.01, ha="left", y=1.03)
    _caption(fig, f"Mean over {len(R.tasks)} runs (5 outer folds of station blocks x 3 seeds) of "
             "each fold's median |error| over station-years; band = 95 % CI from resampling "
             "whole folds. Solid: with sensor noise (rule 6, placeholder instrument, A-37); "
             "dotted: noise-free. Missing points: sets that form no index. The green line is "
             "the error a PERFECT per-observation classifier gets (the station's own same-day "
             "snow on ground), so no band set can beat it.")
    _save(fig, out, "curves.png")
    return summ, floor


def p6c_paired(R, out):
    plt = _plt()
    rows = []
    for mode, _ in SNOW_MODES:
        for k in range(1, 7):
            a, v = R.err("all", k, mode, True), R.err("vnir", k, mode, True)
            keys = sorted(set(a) & set(v))
            if len(keys) < len(R.tasks):
                continue
            d = {kk: v[kk] - a[kk] for kk in keys}
            mu, ci, per = _fold_boot(d)
            rows.append({"mode": mode, "k": k, "d": mu, "ci": ci,
                         "folds_vnir_worse": int((per > 0).sum()), "n_folds": len(per)})
    # Each arm at its own best k (noisy, raw + indices), paired by run.
    best = {}
    for arm, _, _ in SNOW_ARMS:
        best[arm] = {kk: min(R.err(arm, k, "raw+indices", True).get(kk, np.inf)
                             for k in range(1, 7)) for kk in R.paths}
    d = {kk: best["vnir"][kk] - best["all"][kk] for kk in R.paths}
    mu, ci, per = _fold_boot(d)
    best_row = {"mode": "raw+indices", "k": "best", "d": mu, "ci": ci,
                "folds_vnir_worse": int((per > 0).sum()), "n_folds": len(per)}
    fig, ax = plt.subplots(figsize=(8.5, 4.2), facecolor=FIG_BG)
    _axes(ax, "VNIR-only minus SWIR-allowed, paired by fold and seed (with noise)",
          "bands in the nested set (k)", "difference in median |error| (days)")
    for (mode, lab), col, off in zip(SNOW_MODES, (MUTED, AMBER, BLUE), (-0.15, 0, 0.15),
                                     strict=True):
        rr = [r for r in rows if r["mode"] == mode]
        if not rr:                                  # indices alone: no set formed one in every run
            continue
        ax.errorbar([r["k"] + off for r in rr], [r["d"] for r in rr],
                    yerr=[[r["d"] - r["ci"][0] for r in rr], [r["ci"][1] - r["d"] for r in rr]],
                    fmt="o", color=col, ms=5, capsize=3, lw=1.4, label=lab)
    ax.axhline(3, color=MUTED, lw=1, ls="--")
    ax.axhline(0, color=SPINE, lw=1)
    ax.text(0.65, 3.08, "E-60: no more than 3 d worse", color=MUTED, fontsize=7.5, ha="left",
            va="bottom")
    ax.set_xticks(range(1, 7))
    ax.legend(fontsize=8, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK, loc="upper right")
    _caption(fig, f"Above 0: the VNIR-only camera's date is worse. Each arm at its own best k "
             f"(raw + indices): {mu:+.1f} d [{ci[0]:+.1f}, {ci[1]:+.1f}], VNIR worse in "
             f"{best_row['folds_vnir_worse']}/{best_row['n_folds']} folds. 95 % CIs resample "
             "whole folds.", y=-0.03)
    _save(fig, out, "paired.png")
    return rows + [best_row]


def p6c_selection(R, out):
    plt = _plt()
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), facecolor=FIG_BG)
    freq = {}
    for ax, (arm, lab, _) in zip(axes, SNOW_ARMS, strict=True):
        bands = [b for b in SNOW_BANDS if arm == "all" or b not in ("B11", "B12")]
        m = np.zeros((len(bands), 6))
        for p in R.paths.values():
            for s in p[arm]:
                m[bands.index(s["added"]), s["k"] - 1] += 1
        m /= len(R.paths)
        freq[arm] = {b: m[i].tolist() for i, b in enumerate(bands)}
        ax.imshow(m, cmap="Blues", vmin=0, vmax=1, aspect="auto")
        _axes(ax, f"{lab}: band added at step k", "step k", "")
        ax.grid(False)
        ax.set_yticks(range(len(bands)))
        ax.set_yticklabels(bands, color=INK, fontsize=8)
        ax.set_xticks(range(6))
        ax.set_xticklabels(range(1, 7))
        for i in range(len(bands)):
            for j in range(6):
                if m[i, j] >= 0.2:
                    ax.text(j, i, f"{m[i, j]:.0%}", ha="center", va="center", fontsize=7,
                            color="#0f1117" if m[i, j] < 0.6 else "#ffffff")
    _caption(fig, f"Share of the {len(R.paths)} searches (inner block split of each outer "
             "fold's training stations, raw + indices, with noise) that added each band at "
             "each step. With SWIR allowed, a visible band comes first and SWIR (B11 or B12) "
             "second: the NDSI contrast, found rather than given.")
    _save(fig, out, "selection.png")
    return freq


def p6c_stations(oracle, out):
    """Qualitative: where the stations are, and four station-years over the season."""
    plt = _plt()
    fig = plt.figure(figsize=(13, 7.4), facecolor=FIG_BG)
    ax = fig.add_axes([0.0, 0.42, 0.42, 0.55])
    _axes(ax, "Development station-years: sampling floor per station", "longitude", "latitude")
    v = list(oracle.values())
    e = np.array([x["err"] for x in v])
    sc = ax.scatter([x["lon"] for x in v], [x["lat"] for x in v], c=np.minimum(e, 30),
                    cmap="viridis", s=10, vmin=0, vmax=30)
    cb = fig.colorbar(sc, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label("perfect-classifier |error| (days, capped 30)", color=INK, fontsize=8)
    cb.ax.tick_params(colors=INK, labelsize=7.5)
    keys = sorted(oracle)
    rng = np.random.default_rng(0)
    pick = [keys[i] for i in rng.choice(len(keys), 4, replace=False)]
    for j, k in enumerate(pick):
        o = oracle[k]
        a = fig.add_axes([0.5 + 0.25 * (j % 2), 0.55 - 0.47 * (j // 2), 0.22, 0.36])
        _axes(a, f"station {k[0]}, {k[1]} ({o['lat']:.1f} N)", "day of year",
              "green (B3) reflectance" if j % 2 == 0 else "")
        a.scatter(o["doy"][o["snow"]], o["green"][o["snow"]], color=BLUE, s=14,
                  label="station: snow")
        a.scatter(o["doy"][~o["snow"]], o["green"][~o["snow"]], color=AMBER, s=14,
                  label="station: none")
        a.axvline(o["truth"], color=INK_BRIGHT, lw=1.2, label="station snow-off")
        a.axvline(o["est"], color=GREEN, lw=1.2, ls="--", label="perfect-classifier estimate")
        if j == 0:
            a.legend(fontsize=6.5, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK,
                     loc="upper right")
    _caption(fig, "Left: every development station-year at its station, coloured by the error a "
             "perfect classifier would still make (gaps between clear Sentinel-2 dates, late "
             "spring snowfalls the station reports). Right: four seeded station-years; each "
             "point is a clear Sentinel-2 observation of the 30 m window, coloured by the "
             "station's snow on ground that day. Data only, no model.", y=0.02)
    _save(fig, out, "stations.png")
    return pick


def p6c_direction(Rs, oracle, out):
    """Early or late? Signed error (estimate - station; < 0 is early), raw + indices
    with noise, from a run that records it (snow_search after FW 9b82903)."""
    plt = _plt()
    sgn = np.array([v["est"] - v["truth"] for v in oracle.values()])
    ref = {"median": float(np.median(sgn)), "early_gt7": float(np.mean(sgn < -7)),
           "late_gt7": float(np.mean(sgn > 7)), "early": float(np.mean(sgn < 0)),
           "late": float(np.mean(sgn > 0))}
    rows = []
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 4.4), facecolor=FIG_BG)
    _axes(a1, "Median signed error (below 0: earlier than the station)",
          "bands in the nested set (k)", "estimate - station (days)")
    _axes(a2, "Share of station-years off by more than 7 days",
          "bands in the nested set (k)", "share of station-years")
    for arm, lab, col in SNOW_ARMS:
        ks, med, lo, hi, e7, l7 = [], [], [], [], [], []
        for k in range(1, 7):
            d = Rs.err(arm, k, "raw+indices", True, "median_signed_err_days")
            if not d:
                continue
            mu, ci, _ = _fold_boot(d)
            e = float(np.mean(list(Rs.err(arm, k, "raw+indices", True,
                                          "share_early_gt7").values())))
            late = float(np.mean(list(Rs.err(arm, k, "raw+indices", True,
                                             "share_late_gt7").values())))
            ea = float(np.mean(list(Rs.err(arm, k, "raw+indices", True,
                                           "share_early").values())))
            la = float(np.mean(list(Rs.err(arm, k, "raw+indices", True,
                                           "share_late").values())))
            ab = float(np.mean(list(Rs.err(arm, k, "raw+indices", True).values())))
            ks.append(k)
            med.append(mu)
            lo.append(ci[0])
            hi.append(ci[1])
            e7.append(e)
            l7.append(late)
            rows.append({"arm": arm, "k": k, "abs": ab, "signed": mu, "signed_ci": ci,
                         "early": ea, "late": la, "early_gt7": e, "late_gt7": late,
                         "runs": len(d)})
        a1.plot(ks, med, "-o", color=col, lw=2, ms=5, label=lab)
        a1.fill_between(ks, lo, hi, color=col, alpha=0.18, lw=0)
        a2.plot(ks, e7, "-o", color=col, lw=2, ms=5, label=f"{lab}: early > 7 d")
        a2.plot(ks, l7, "--s", color=col, lw=2, ms=5, label=f"{lab}: late > 7 d")
    a1.axhline(0, color=SPINE, lw=1)
    a1.axhline(ref["median"], color=GREEN, lw=1.2)
    a1.text(6.1, ref["median"], f"perfect classifier {ref['median']:+.1f} d", color=GREEN,
            fontsize=7.5, va="top", ha="right")
    for y, txt in ((ref["early_gt7"], "early"), (ref["late_gt7"], "late")):
        a2.axhline(y, color=GREEN, lw=1.1, ls="-" if txt == "early" else "--")
        a2.text(6.1, y, f"perfect classifier, {txt} > 7 d: {y:.0%}", color=GREEN,
                fontsize=7.5, va="bottom", ha="right")
    a2.set_ylim(0, 0.6)
    for a in (a1, a2):
        a.set_xticks(range(1, 7))
    a1.legend(fontsize=7.5, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK, loc="lower right")
    a2.legend(fontsize=7, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK, loc="upper left",
              ncol=2)
    n = len(Rs.tasks)
    todo = f"; {15 - n} task(s) still to rerun" if n < 15 else ""
    _caption(fig, f"Raw + indices, with sensor noise; mean over {n} runs ({_rel(Rs.run)}"
             f"{todo}), band = 95 % CI resampling whole folds. The "
             "green lines are the perfect classifier (the station's own same-day snow): "
             "Sentinel-2 alone runs early because the season's last snowfalls fall between "
             "clear scenes. The models are early about as often, but are also late by more "
             "than a week far more often: the classifier calling snow the station no longer "
             "reports.")
    _save(fig, out, "direction.png")
    return rows, ref


SNOW_SERIES_SETS = (("all_k6", "SWIR allowed, k = 6", BLUE), ("vnir_k6", "VNIR only, k = 6",
                                                                 ORANGE))


def _load_snow_series(maps_dir: Path):
    import csv
    obs, sy = [], []
    for d in sorted(p for p in maps_dir.glob("f*s*") if (p / "obs.csv").exists()):
        fold = json.loads((d / "series.json").read_text())["fold"]
        obs += [dict(r, fold=fold) for r in csv.DictReader(open(d / "obs.csv", encoding="utf-8"))]
        sy += [dict(r, fold=fold) for r in
               csv.DictReader(open(d / "station_years.csv", encoding="utf-8"))]
    pos = {(r["aes"], r["year"]): (float(r["lon"]), float(r["lat"])) for r in
           csv.DictReader(open(SNOW / "snow_v1" / "dev_station_years.csv", encoding="utf-8"))}
    return obs, sy, pos


def p6c_series(maps_dir: Path, out: Path, n: int = 8, seed: int = 0):
    """Labelled time series and station maps from predict_snow_series.py."""
    plt = _plt()
    obs, sy, pos = _load_snow_series(maps_dir)
    if not sy:
        return []
    sets = [s for s in SNOW_SERIES_SETS if f"est_{s[0]}" in sy[0]]
    # Station maps: signed error per held-out station-year, per set.
    fig, axes = plt.subplots(1, len(sets), figsize=(6.6 * len(sets), 4.6), facecolor=FIG_BG,
                             squeeze=False)
    for ax, (s, lab, _) in zip(axes[0], sets, strict=True):
        _axes(ax, f"{lab}: estimate - station (days)", "longitude", "latitude")
        xy = np.array([pos[(r["aes"], r["year"])] for r in sy])
        e = np.array([float(r[f"est_{s}"]) - float(r["truth_doy"]) for r in sy])
        sc = ax.scatter(xy[:, 0], xy[:, 1], c=np.clip(e, -30, 30), cmap="RdBu_r", vmin=-30,
                        vmax=30, s=12, edgecolors="none")
        ax.text(0.01, 0.02, f"median |error| {np.median(np.abs(e)):.1f} d; early "
                f"{np.mean(e < 0):.0%}, late {np.mean(e > 0):.0%}; n = {len(e)}",
                transform=ax.transAxes,
                color=INK_BRIGHT, fontsize=8)
    cb = fig.colorbar(sc, ax=list(axes[0]), fraction=0.03, pad=0.02)
    cb.set_label("days (blue early, red late; clipped at 30)", color=INK, fontsize=8)
    cb.ax.tick_params(colors=INK, labelsize=7.5)
    nf = len({r["fold"] for r in sy})
    _caption(fig, f"Every development station-year in the {nf} outer fold(s) mapped, each scored "
             "by the model from the fold that held it out (seed 0; raw + indices, with sensor "
             "noise).", y=-0.02)
    _save(fig, out, "series_map.png")
    # Time series: seeded held-out station-years.
    keys = sorted({(r["aes"], r["year"]) for r in sy})
    rng = np.random.default_rng(seed)
    pick = [keys[i] for i in sorted(rng.choice(len(keys), min(n, len(keys)), replace=False))]
    rows = -(-len(pick) // 2)
    fig, axes = plt.subplots(rows, 2, figsize=(13, 2.9 * rows), facecolor=FIG_BG, squeeze=False)
    for ax, k in zip(axes.flat, pick, strict=False):
        o = sorted((r for r in obs if (r["aes"], r["year"]) == k), key=lambda r: int(r["doy"]))
        t = next(r for r in sy if (r["aes"], r["year"]) == k)
        doy = np.array([int(r["doy"]) for r in o])
        st = np.array([int(r["station_snow"]) for r in o])
        g = np.array([float(r["green"]) for r in o])
        errs = ", ".join(f"{lab.split(',')[0]} "
                         f"{float(t['est_' + s]) - float(t['truth_doy']):+.0f} d"
                         for s, lab, _ in sets)
        _axes(ax, f"station {k[0]}, {k[1]} ({pos[k][1]:.1f} N): {errs}", "day of year",
              "green (B3)")
        for val, col, lab in ((1, INK_BRIGHT, "station: snow"), (0, MUTED, "station: none"),
                              (-1, SPINE, "no station reading")):
            m = st == val
            ax.scatter(doy[m], g[m], color=col, s=16, zorder=3, label=lab, edgecolors="none")
        a2 = ax.twinx()
        a2.set_ylim(-0.05, 1.05)
        a2.tick_params(colors=INK, labelsize=7.5)
        a2.set_ylabel("P(snow)", color=INK, fontsize=8)
        for s, lab, col in sets:
            a2.plot(doy, [float(r[f"p_{s}"]) for r in o], "-", color=col, lw=1.6, label=lab)
            ax.axvline(float(t[f"est_{s}"]), color=col, lw=1.2, ls="--")
        ax.axvline(float(t["truth_doy"]), color=GREEN, lw=1.6)
        a2.axhline(0.5, color=SPINE, lw=0.8, ls=":")
    for ax in list(axes.flat)[len(pick):]:
        ax.set_visible(False)
    h1, l1 = axes.flat[0].get_legend_handles_labels()
    h1.append(plt.Line2D([0], [0], color=GREEN, lw=1.6))
    l1.append("station snow-off")
    hs = [plt.Line2D([0], [0], color=c, lw=1.6) for _, _, c in sets]
    fig.legend(h1 + hs, l1 + [f"P(snow), {lab} (dashed: its date)" for _, lab, _ in sets],
               loc="lower center", ncol=3, fontsize=8, facecolor=AX_BG, edgecolor=SPINE,
               labelcolor=INK, bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    _caption(fig, "Seeded held-out station-years. Points: each clear Sentinel-2 observation's "
             "green reflectance, shaded by the station's own report that day. Lines: each "
             "model's snow probability; a model's date is just after its last observation above "
             "0.5 (dashed). Green line: the station's snow-off date.", y=-0.06)
    _save(fig, out, "series.png")
    return ["series_map.png", "series.png"]


def p6c_tables(R, out, summ, floor, oracle, paired, freq, direction=None):
    L = ["# P6c tables: the snow-off estimator (E-60)\n",
         f"Run: `{_rel(R.run)}`. {len(R.tasks)} tasks (5 outer folds of 1-degree station "
         "blocks x 3 seeds), ECCC climate-station snow on ground as truth (Q33). Errors are "
         "each fold's median |S2 - station| snow-off date over station-years, then the mean "
         "over runs; 95 % CIs resample whole folds.\n",
         "## Nested sets (with sensor noise; noise-free in brackets)\n",
         "| arm | input | " + " | ".join(f"k={k}" for k in range(1, 7)) + " |",
         "|---|---|" + "---|" * 6]
    for arm, lab, _ in SNOW_ARMS:
        for mode, mlab in SNOW_MODES:
            cells = []
            for k in range(1, 7):
                n, c = summ.get((arm, k, mode, True)), summ.get((arm, k, mode, False))
                cells.append("" if n is None else f"{n[0]:.1f} ({c[0]:.1f})")
            L.append(f"| {lab} | {mlab} | " + " | ".join(cells) + " |")
    e = np.array([v["err"] for v in oracle.values()])
    L += ["", f"Sampling floor, a perfect per-observation classifier: median {floor:.1f} d, "
          f"p90 {np.percentile(e, 90):.1f} d, within 7 d {np.mean(e <= 7):.0%} "
          f"({len(e)} development station-years).", "",
          "## VNIR-only minus SWIR-allowed (with noise)\n",
          "| input | k | difference (d) | 95 % CI | folds VNIR worse |", "|---|---|---|---|---|"]
    for r in paired:
        L.append(f"| {r['mode']} | {r['k']} | {r['d']:+.2f} | {_ci(r['ci'])} | "
                 f"{r['folds_vnir_worse']}/{r['n_folds']} |")
    _csv(out / "T_paired.csv", paired)
    L += ["", "## First two bands chosen (share of searches)\n", "| arm | step 1 | step 2 |",
          "|---|---|---|"]
    for arm, lab, _ in SNOW_ARMS:
        def top(j, arm=arm):
            s = sorted(((v[j], b) for b, v in freq[arm].items()), reverse=True)
            return ", ".join(f"{b} {p:.0%}" for p, b in s if p > 0)
        L.append(f"| {lab} | {top(0)} | {top(1)} |")
    if direction:
        rows, ref = direction
        L += ["", "## Early or late (raw + indices, with noise; estimate - station)\n",
              "| arm | k | median signed (d) | 95 % CI | early | late | early > 7 d | "
              "late > 7 d |", "|---|---|---|---|---|---|---|---|"]
        for r in rows:
            lab = dict((a, b) for a, b, _ in SNOW_ARMS)[r["arm"]]
            L.append(f"| {lab} | {r['k']} | {r['signed']:+.1f} | {_ci(r['signed_ci'], 1)} | "
                     f"{r['early']:.0%} | {r['late']:.0%} | {r['early_gt7']:.0%} | "
                     f"{r['late_gt7']:.0%} |")
        L.append(f"| perfect classifier | - | {ref['median']:+.1f} | | {ref['early']:.0%} | "
                 f"{ref['late']:.0%} | {ref['early_gt7']:.0%} | {ref['late_gt7']:.0%} |")
        L.append(f"\nFrom {rows[0]['runs']} runs of the signed-error rerun; the absolute "
                 "errors in that run match the first run exactly on every task both finished.")
        _csv(out / "T_direction.csv", rows)
    walls = [r["wall_s"] for r in R.results.values()]
    L += ["", f"Resources: CPU tasks, {np.median(walls) / 60:.1f} min median, "
          f"{max(walls) / 60:.1f} min max (2 h requested)."]
    (out / "tables.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"  wrote {_rel(out / 'tables.md')}")


def p6c(run: Path, out: Path, signed: Path | None = None, maps: Path | None = None):
    out.mkdir(parents=True, exist_ok=True)
    maps = maps or run / "maps"
    if maps.exists():
        p6c_series(maps, out)
    R = _SnowRun(run)
    oracle = snow_oracle()
    summ, floor = p6c_curves(R, oracle, out)
    paired = p6c_paired(R, out)
    freq = p6c_selection(R, out)
    pick = p6c_stations(oracle, out)
    supp_scores(list(R.paths.values()), (("all", "any band (SWIR allowed)"),
                                         ("vnir", "VNIR only (no B11, B12)")),
                SNOW_BANDS, out, "scores", "Snow-off searches", "median error, days",
                "days of median error removed", to_score=lambda v: -v, gain_sign=-1.0,
                fmt_single="{:.1f}", fmt_gain="{:+.1f}", low_is_good=True)
    direction = p6c_direction(_SnowRun(signed), oracle, out) if signed else None
    p6c_tables(R, out, summ, floor, oracle, paired, freq, direction)
    (out / "summary.json").write_text(json.dumps(
        {"curves": {f"{a}|{k}|{m}|{'noisy' if n else 'clean'}": v
                    for (a, k, m, n), v in summ.items()},
         "sampling_floor_median_days": floor, "paired": paired, "selection": freq,
         "direction": direction[0] if direction else None,
         "direction_perfect_classifier": direction[1] if direction else None,
         "station_years_shown": [list(k) for k in pick]}, indent=1, default=float))
    (out / "run.json").write_text(json.dumps(
        {"run": str(_rel(run)), "signed_run": str(_rel(signed)) if signed else None}, indent=1))


# ── P6b: what CWFIS issued against our R0, 2024 half (E-56) ─────────────────

COHORT = _ROOT.parent / "Fire_Risk_Model" / "data" / "cohort_2024_25" / "patches"
E56_OUT = (("hfi", "HFI (kW/m)"), ("ros", "ROS (m/min)"), ("cfb", "CFB (fraction)"))
E56_R0 = (("cwfis_2024", "Reconstructed (ours), CWFIS 2024 fuel", BLUE),
          ("scanfi_tree_prefire", "Reconstructed (ours), SCANFI 2020 fuel", GREEN))


def _fuel_family(code) -> str:
    c = int(code)
    return ("C" if c <= 7 else "D" if c <= 13 else "O" if c == 31 else
            "M" if c >= 400 else "non-fuel")


def _e56_rows(run: Path) -> list[dict]:
    """One record per scored patch: ISSUED layers and each R0 variant's means."""
    by = {}
    for r in _read_csv(run / "per_patch.csv"):
        rec = by.setdefault(r["stem"], {"stem": r["stem"], "group": r["group"],
                                        "fire": r["kind"] == "fire", "lat": float(r["lat"]),
                                        "R0": {}})
        rec["R0"][r["variant"]] = {o: float(r[f"mean_{o}"] or "nan") for o, _ in E56_OUT}
    for rec in by.values():
        L = json.loads((COHORT / f"{rec['stem']}_cwfis_grid.json").read_text())["layers"]
        rec["issued"] = {o: float("nan") if (L.get(o) or {}).get("mean") is None
                         else L[o]["mean"] for o, _ in E56_OUT}
        rec["issued_days_back"] = max((L.get(o) or {}).get("days_back") or 0 for o, _ in E56_OUT)
        ft = (L.get("ft") or {}).get("majority")
        ours = np.load(COHORT / f"{rec['stem']}_fbpfuel.npy")
        u, n = np.unique(ours, return_counts=True)
        rec["fuel_issued"] = None if ft is None else _fuel_family(ft)
        rec["fuel_ours"] = _fuel_family(u[n.argmax()])
    return sorted(by.values(), key=lambda r: r["stem"])


def p6b_compare(rows) -> list[dict]:
    """E-56 as registered: AUC per source, the paired gap, and Spearman rho."""
    out = []
    for o, olab in E56_OUT:
        for v, vlab, _ in E56_R0:
            use = [r for r in rows if v in r["R0"] and np.isfinite(r["issued"][o])
                   and np.isfinite(r["R0"][v][o])]

            def arrays(rs, o=o, v=v):
                return (np.array([r["issued"][o] for r in rs]),
                        np.array([r["R0"][v][o] for r in rs]),
                        np.array([r["fire"] for r in rs]))

            a, b, y = arrays(use)

            def gap(rs):
                x, z, f = arrays(rs)
                return _auc(x, f) - _auc(z, f)

            def rho(rs):
                x, z, _ = arrays(rs)
                return _spearman(x, z)

            out.append({"output": o, "label": olab, "r0": v, "r0_label": vlab, "n": len(use),
                        "n_fire": int(y.sum()), "auc_issued": _auc(a, y), "auc_r0": _auc(b, y),
                        "gap": _auc(a, y) - _auc(b, y), "gap_ci": _boot_groups(use, gap),
                        "rho": _spearman(a, b), "rho_ci": _boot_groups(use, rho)})
    return out


def p6b_figures(rows, cmp, out):
    plt = _plt()
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6), facecolor=FIG_BG)
    ax = axes[0]
    r0 = E56_R0[0]
    _axes(ax, "HFI on D-1, 2024 patches", "ISSUED by CWFIS (kW/m, mean over the patch)",
          f"{r0[1]} (kW/m)")
    for fire, lab, col in ((True, "fire patch", ORANGE), (False, "unburned patch", BLUE)):
        use = [r for r in rows if r["fire"] == fire and r0[0] in r["R0"]]
        x = np.array([r["issued"]["hfi"] for r in use])
        y = np.array([r["R0"][r0[0]]["hfi"] for r in use])
        ax.scatter(np.maximum(x, 1), np.maximum(y, 1), s=16, color=col, alpha=0.8, lw=0, label=lab)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.plot([1, 1e5], [1, 1e5], color=INK, lw=1)
    ax.legend(fontsize=8, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK, loc="lower right")
    ax = axes[1]
    _axes(ax, "Between-patch AUC, fire vs unburned", "", "AUC")
    use = [c for c in cmp if c["r0"] == r0[0]]
    x = np.arange(len(use))
    ax.bar(x - 0.2, [c["auc_issued"] for c in use], 0.38, color=ORANGE, label="ISSUED by CWFIS")
    ax.bar(x + 0.2, [c["auc_r0"] for c in use], 0.38, color=BLUE, label=r0[1])
    ax.set_xticks(x)
    ax.set_xticklabels([c["label"] for c in use], fontsize=8.5, color=INK)
    ax.set_ylim(0.5, 1.0)
    ax.legend(fontsize=7.5, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK, loc="upper right")
    fig.tight_layout()
    paired = sum(np.isfinite(r["issued"]["hfi"]) for r in rows)
    _caption(fig, f"E-56, 2024 only: {paired} of {len(rows)} patches have an issued value. 2025 "
             "is frozen and was not opened. "
             "Issued values are 2 km grids averaged over the patch; ours are 20 m maps averaged "
             "the same way. HFI under 1 kW/m is drawn at 1. The line is equality.")
    _save(fig, out, "issued_vs_r0.png")


def p6b_tables(rows, cmp, out, run):
    L = ["# P6b tables: what CWFIS issued against our R0, 2024 (E-56)\n",
         f"Run: `{_rel(run)}`. {len(rows)} patches of 2024 ({sum(r['fire'] for r in rows)} fire). "
         "2025 is frozen (splits/time_test_v1.json) and was not opened.\n",
         "## E-56 as registered: ISSUED by CWFIS against Reconstructed (ours)\n",
         "| output | R0 fuel | n (fire) | AUC ISSUED | AUC ours | ISSUED minus ours [95 % CI] | "
         "Spearman rho [95 % CI] |", "|---|---|---|---|---|---|---|"]
    for c in cmp:
        L.append(f"| {c['label']} | {c['r0_label'].split(', ')[1]} | {c['n']} ({c['n_fire']}) | "
                 f"{c['auc_issued']:.3f} | {c['auc_r0']:.3f} | {c['gap']:+.3f} "
                 f"{_ci(c['gap_ci'], 3)} | {c['rho']:.2f} {_ci(c['rho_ci'])} |")
    _csv(out / "T_e56.csv", cmp)
    fam = [r for r in rows if r["fuel_issued"]]
    same = sum(r["fuel_issued"] == r["fuel_ours"] for r in fam)
    L += ["", "## Fuel: majority family per patch\n",
          f"The 2 km grid CWFIS issued and the 30 m CWFIS 2024 layer agree on the majority family "
          f"on {same} of {len(fam)} patches ({same / len(fam):.0%}). This compares families by "
          "majority, not the registered share of area, which needs the issued rasters.",
          "", f"Patches using an earlier issued day: "
          f"{sum(r['issued_days_back'] > 0 for r in rows)} of {len(rows)}."]
    (out / "tables.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"  wrote {_rel(out / 'tables.md')}")


def p6b(run: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    rows = _e56_rows(run)
    cmp = p6b_compare(rows)
    p6b_figures(rows, cmp, out)
    p6b_tables(rows, cmp, out, run)
    (out / "summary.json").write_text(json.dumps({"e56_2024": cmp}, indent=1, default=float))
    (out / "run.json").write_text(json.dumps({"run": str(_rel(run))}, indent=1))


# ── P6d: the FWI start-up from Sentinel-2 snow-off (E-18) ───────────────────

E18_STARTUPS = (("flat", "flat spinup (ours, the defect)", "#b9b9c6"),
                ("c2", "C-2 from ERA5-Land snow", BLUE),
                ("c2_s2_all", "C-2 from S2 snow-off, SWIR allowed", GREEN),
                ("c2_s2_vnir", "C-2 from S2 snow-off, VNIR only", ORANGE))
E18_ARMS = (("c2_s2_all", "SWIR allowed", GREEN), ("c2_s2_vnir", "VNIR only", ORANGE))
E18_CODES = (("dc", "DC"), ("dmc", "DMC"), ("bui", "BUI"), ("fwi", "FWI"))
E18_BANDS = ("all", "<55 N", "55-60 N", ">=60 N")


def _e18_patches(stems) -> list[dict]:
    """Per patch: latitude and each start-up's season start and lag-1 DC."""
    rows = []
    for s in stems:
        p = PATCHES / f"{s}_fwi_v2.json"
        if not p.exists():
            continue
        v = json.loads(p.read_text())["variants"]
        if not all(a in v for a, _, _ in E18_ARMS):
            continue
        rec = {"stem": s, "lat": float(s.split("_")[1])}
        for a in ("c2", *(x for x, _, _ in E18_ARMS)):
            rec[f"{a}_start"] = v[a]["meta"].get("season_start")
            rec[f"{a}_dc"] = float(v[a]["lags"]["1"]["dc"])
        rows.append(rec)
    return rows


def p6d_auc(E, out):
    plt = _plt()
    fig, axes = plt.subplots(1, 4, figsize=(15, 4.2), facecolor=FIG_BG, sharey=True)
    for ax, (k, lab) in zip(axes, E18_CODES, strict=True):
        _axes(ax, lab, "", "between-patch AUC (fire vs non-fire)" if k == "dc" else "")
        for i, (a, name, col) in enumerate(E18_STARTUPS):
            off = (i - 1.5) * 0.18
            ys = [E["auc"][f"{a}:{k}"][b] for b in E18_BANDS]
            ax.errorbar([j + off for j in range(4)], [y["auc"] for y in ys],
                        yerr=[[y["auc"] - y["ci"][0] for y in ys],
                              [y["ci"][1] - y["auc"] for y in ys]],
                        fmt="o", color=col, ms=4, capsize=2, lw=1.1, label=name)
        ax.set_xticks(range(4))
        ax.set_xticklabels(E18_BANDS, fontsize=8, color=INK)
        ax.axhline(0.5, color=SPINE, lw=1)
    axes[0].legend(fontsize=7, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK, loc="lower left")
    fig.suptitle("E-18: fire danger codes under four start-ups, all Reconstructed (ours)",
                 color=INK_BRIGHT, fontsize=11.5, x=0.01, ha="left", y=1.03)
    _caption(fig, f"{E['n_patches']} development patches ({E['n_fire']} fire) that have "
            "both imagery "
             "dates; lag-1 codes at 13:00 LDT; 95 % CI resampling fires and location blocks. Each "
             "bar's CI is its own: the comparison that decides E-18 is the paired one "
             "(paired.png).")
    _save(fig, out, "auc.png")


def p6d_paired(E, out):
    plt = _plt()
    fig, axes = plt.subplots(1, 2, figsize=(12, 3.8), facecolor=FIG_BG, sharey=True, sharex=True)
    for ax, (reg, lab) in zip(axes, (("north", "at or above 55 N"), ("south", "below 55 N")),
                              strict=True):
        F = E["falsifier"][reg]
        _axes(ax, f"{lab} (n = {F['c2_s2_all']['dc_move']['n']})",
              "AUC minus the ERA5 C-2 rule's, same patches", "")
        for i, (a, name, col) in enumerate(E18_ARMS):
            rows = [F[a]["auc_minus_c2"][k] for k, _ in E18_CODES]
            y = [j + (i - 0.5) * 0.3 for j in range(4)]
            ax.errorbar([r["d"] for r in rows], y,
                        xerr=[[r["d"] - r["ci"][0] for r in rows],
                              [r["ci"][1] - r["d"] for r in rows]],
                        fmt="o", color=col, ms=5, capsize=3, lw=1.3, label=name)
        ax.axvline(0, color=INK, lw=1)
        ax.set_yticks(range(4))
        ax.set_yticklabels([lab for _, lab in E18_CODES], color=INK)
        ax.invert_yaxis()
    axes[1].legend(fontsize=8, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK, loc="lower left")
    _caption(fig, "Paired on the same patches; 95 % CI resampling fires and location "
            "blocks. E-18's "
             "falsifier reads DC and FWI above 55 N: right of 0 with a CI clear of it would be a "
             "gain. The VNIR-only date loses skill; the SWIR-allowed date neither gains nor loses.")
    _save(fig, out, "paired.png")


def p6d_dates(P, E, out):
    plt = _plt()
    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.4), facecolor=FIG_BG)

    def doy(s):
        d = s.split("-")
        return (int(d[1]) - 1) * 30.44 + int(d[2])

    bands = ((lambda la: la < 55, "<55 N", BLUE), (lambda la: 55 <= la < 60, "55-60 N", AMBER),
             (lambda la: la >= 60, ">=60 N", PINK))
    for ax, (a, name, _) in zip(axes[:2], E18_ARMS, strict=True):
        _axes(ax, f"Season start: {name} vs ERA5 snow", "ERA5 C-2 start (day of year)",
              "Sentinel-2 C-2 start (day of year)")
        for test, lab, col in bands:
            r = [x for x in P if test(x["lat"]) and x[f"{a}_start"] and x["c2_start"]]
            ax.scatter([doy(x["c2_start"]) for x in r], [doy(x[f"{a}_start"]) for x in r], s=14,
                       color=col, alpha=0.8, lw=0, label=lab)
        ax.plot([60, 200], [60, 200], color=INK, lw=1)
        ax.set_xlim(60, 200)
        ax.set_ylim(60, 200)
        ax.set_aspect("equal")
        g = E["falsifier"]["all"][a]["start_gap"]
        ax.text(0.03, 0.97, f"median {g['median_days']:+.0f} d, 10-90 % {g['p10']:+.0f} to "
                f"{g['p90']:+.0f} d, n = {g['n']}", transform=ax.transAxes, color=INK, fontsize=8,
                va="top")
    axes[0].legend(fontsize=7.5, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK,
                   loc="lower right")
    ax = axes[2]
    _axes(ax, "Lag-1 DC moved by the imagery date", "latitude (degrees N)",
          "DC, % of the ERA5 rule's")
    for a, name, col in E18_ARMS:
        r = [x for x in P if x["c2_dc"] > 0]
        ax.scatter([x["lat"] for x in r], [100 * (x[f"{a}_dc"] / x["c2_dc"] - 1) for x in r], s=12,
                   color=col, alpha=0.7, lw=0, label=name)
    ax.axhline(0, color=INK, lw=1)
    for y in (-10, 10):
        ax.axhline(y, color=MUTED, lw=1, ls="--")
    ax.set_ylim(-100, 100)
    ax.legend(fontsize=7.5, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK, loc="lower right")
    fig.tight_layout()
    _caption(fig, "Left and centre: each patch's season start; points above the line start later "
             "than ERA5. Right: dashed lines mark the 10 % move E-18 registered, read on the "
             "median; values beyond the axis are clipped from view.", y=0.0)
    _save(fig, out, "dates.png")


def p6d_tables(E, S, out, run, snow):
    L = ["# P6d tables: the FWI start-up from Sentinel-2 snow-off (E-18)\n",
         f"Run: `{_rel(run)}`, with snow-off dates from `{_rel(snow)}`. {E['n_patches']} "
         "development "
         f"patches ({E['n_fire']} fire; "
         + ", ".join(f"{k}: {v}" for k, v in E["n_by_band"].items())
         + "). Every code here is Reconstructed (ours), none ISSUED by CWFIS. The frozen test "
         "patches were not opened.\n",
         "## The classifiers, chosen inside the snow training folds\n",
         "| arm | bands | inner median error (d) |", "|---|---|---|"]
    for a, name in (("all", "SWIR allowed"), ("vnir", "VNIR only")):
        r = S["arms"][a]
        L.append(f"| {name} | {', '.join(r['bands'])} | {r['inner_err'][str(r['k'])]:.1f} |")
    L += ["", f"{sum(1 for p in S['patches'].values() if p['all'].get('date'))} of "
          f"{len(S['patches'])} patches have a date.\n",
          "## E-18's registered test: the imagery date against ERA5's C-2 rule\n",
          "| region | start-up | median lag-1 DC (ERA5 rule) | move | patches moved 10 %+ | "
          "season start, median gap (d) | DC AUC change | FWI AUC change |",
          "|---|---|---|---|---|---|---|---|"]
    rows = []
    for reg, lab in (("north", ">= 55 N"), ("south", "< 55 N"), ("all", "all")):
        for a, name, _ in E18_ARMS:
            F = E["falsifier"][reg][a]
            m, g = F["dc_move"], F["start_gap"]
            d, w = F["auc_minus_c2"]["dc"], F["auc_minus_c2"]["fwi"]
            L.append(f"| {lab} | {name} | {m['median']:.0f} ({m['median_c2']:.0f}) | "
                     f"{m['move_pct']:+.1f} % | {m['share_patches_moved_10pct']:.0%} | "
                     f"{g['median_days']:+.0f} | {d['d']:+.3f} {_ci(d['ci'], 3)} | "
                     f"{w['d']:+.3f} {_ci(w['ci'], 3)} |")
            rows.append({"region": reg, "startup": a, **m, **{f"gap_{k}": v for k, v in g.items()},
                         **{f"auc_{k}": v["d"] for k, v in F["auc_minus_c2"].items()},
                         **{f"auc_{k}_ci": v["ci"] for k, v in F["auc_minus_c2"].items()}})
    _csv(out / "T_falsifier.csv", rows)
    L += ["", "## Between-patch AUC by start-up\n",
          "| code | start-up | all | <55 N | 55-60 N | >=60 N |", "|---|---|---|---|---|---|"]
    for k, lab in E18_CODES:
        for a, name, _ in E18_STARTUPS:
            L.append(f"| {lab} | {name} | " + " | ".join(
                f"{E['auc'][f'{a}:{k}'][b]['auc']:.3f}" for b in E18_BANDS) + " |")
    L += ["", "Patches whose season had not started at D-1: " + ", ".join(
        f"{a} {E['season_not_started'][a]}" for a, _, _ in E18_STARTUPS) + "."]
    (out / "tables.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"  wrote {_rel(out / 'tables.md')}")


def p6d(run: Path, out: Path, snowoff: Path):
    out.mkdir(parents=True, exist_ok=True)
    E = json.loads((run / "summary.json").read_text())["dated_weather"]["E18_s2_startup"]
    S = json.loads(snowoff.read_text())
    P = _e18_patches(sorted(S["patches"]))
    p6d_auc(E, out)
    p6d_paired(E, out)
    p6d_dates(P, E, out)
    p6d_tables(E, S, out, run, snowoff)
    (out / "summary.json").write_text(json.dumps(
        {k: E[k] for k in ("n_patches", "n_fire", "n_by_band", "falsifier", "season_not_started")},
        indent=1, default=float))
    (out / "run.json").write_text(json.dumps(
        {"run": str(_rel(run)), "snowoff": str(_rel(snowoff))}, indent=1))


# ── P6a-HS: the AVIRIS-NG band searches (E-61, E-62) ───────────────────────

HS_ARMS = (("vnir", "VNIR camera alone", BLUE),
           ("vnir_no_red_edge", "VNIR, nothing in 700-760 nm", ORANGE),
           ("swir_std", "SWIR on standard InGaAs, VNIR fixed", GREEN),
           ("swir_ext", "SWIR on extended InGaAs, VNIR fixed", PINK))
HS_TARGETS = (("pc", "percent conifer", "%"), ("closure", "crown closure", "%"),
              ("height", "canopy height", "m"))


class _HSRun:
    """One AVIRIS sweep: eval rows and search paths per (arm, fold, seed)."""

    def __init__(self, run: Path):
        self.run = run
        self.rows, self.paths, self.results = [], {}, {}
        self.tasks = {}
        for arm in (*(a[0] for a in HS_ARMS), "references"):
            ts = sorted(p for p in (run / arm).glob("f*s*") if (p / "eval.jsonl").exists())
            self.tasks[arm] = ts
            for t in ts:
                fold, seed = (int(v) for v in t.name[1:].split("s"))
                for line in (t / "eval.jsonl").read_text().splitlines():
                    r = json.loads(line)
                    r["fold"], r["seed"] = fold, seed
                    self.rows.append(r)
                paths = json.loads((t / "search.json").read_text())
                if arm in paths:
                    self.paths[(arm, fold, seed)] = paths[arm]
                self.results[(arm, fold, seed)] = json.loads((t / "result.json").read_text())

    def get(self, arm, name, mode="raw+indices", noisy=True, key="skill_combined"):
        return {(r["fold"], r["seed"]): r["metrics"][key] for r in self.rows
                if r["arm"] == arm and r["set"] == name and r["mode"] == mode
                and r["noisy"] == noisy and r["metrics"]
                and r["metrics"].get(key) is not None and np.isfinite(r["metrics"][key])}

    def sets(self, arm):
        return list(dict.fromkeys(r["set"] for r in self.rows if r["arm"] == arm))


def _hs_x(name):
    """Bands searched: 0 for the fixed VNIR alone."""
    return 0 if name == "fixed_only" else int(name[1:])


def p6hs_curves(H, out, reference=None, void=""):
    plt = _plt()
    fig, axes = plt.subplots(1, 4, figsize=(15, 4.2), facecolor=FIG_BG, sharey=True)
    summ = {}
    for ax, (arm, lab, col) in zip(axes, HS_ARMS, strict=True):
        n = len(H.tasks[arm])
        _axes(ax, f"{lab}\n({n} tasks)", "bands searched (k)",
              "combined skill (0 = training mean)" if arm == "vnir" else "")
        for noisy, ls in ((True, "-"), (False, ":")):
            xs, m, lo, hi = [], [], [], []
            for name in H.sets(arm):
                d = H.get(arm, name, noisy=noisy)
                if not d:
                    continue
                mu, ci, per = _fold_boot(d)
                xs.append(_hs_x(name))
                m.append(mu)
                lo.append(ci[0])
                hi.append(ci[1])
                summ[(arm, name, noisy)] = (mu, ci, per.tolist())
            ax.plot(xs, m, ls, color=col, lw=2, marker="o" if noisy else None, ms=5,
                    label="with noise" if noisy else "noise-free")
            if noisy:
                ax.fill_between(xs, lo, hi, color=col, alpha=0.18, lw=0)
        ax.axhline(0, color=INK, lw=1)
        if reference is not None:
            ax.axhline(reference, color=MUTED, lw=1.2, ls="--")
            ax.text(0.02, reference, f" Sentinel-2 search, k = 6: {reference:.2f}", color=MUTED,
                    fontsize=7.5, va="bottom", transform=ax.get_yaxis_transform())
        ax.legend(fontsize=7.5, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK,
                  loc="center right")
    fig.suptitle(("VOID, labels from the wrong ground. " if void else "")
                 + "E-61 / E-62: skill on held-out AVIRIS-NG groups, by nested band set",
                 color=INK_BRIGHT, fontsize=11.5, x=0.01, ha="left", y=1.06)
    _caption(fig, "Raw + indices. Mean over runs; band = 95 % CI resampling whole folds (groups of "
             "overlapping lines). Combined skill = mean of percent conifer, closure, height and "
             "fuel family skills; 0 is the training mean. k = 0 is the fixed VNIR alone. The "
             "dashed line is the P6a Sentinel-2 search on other ground, for scale only.")
    _save(fig, out, "curves.png")
    return summ


def _hs_band(name):
    c, f = name.split("@")[0].split("/")
    return int(c), int(f)


def p6hs_selection(H, out, void=""):
    plt = _plt()
    fig, axes = plt.subplots(2, 2, figsize=(13, 6.6), facecolor=FIG_BG)
    picks = {}
    for ax, (arm, lab, col) in zip(axes.flat, HS_ARMS, strict=True):
        _axes(ax, lab, "band centre (nm)", "step")
        rows = [(s["k"], *_hs_band(s["added"])) for kk, p in H.paths.items() if kk[0] == arm
                for s in p["steps"]]
        cnt = {}
        for k, c, _ in rows:
            cnt[(k, c)] = cnt.get((k, c), 0) + 1
        ax.scatter([c for _, c in cnt], [k for k, _ in cnt], s=[18 * v for v in cnt.values()],
                   color=col, alpha=0.8, lw=0)
        ax.invert_yaxis()
        picks[arm] = [{"step": k, "centre_nm": c, "searches": v}
                      for (k, c), v in sorted(cnt.items())]
    fig.tight_layout()
    if void:
        fig.suptitle("VOID, labels from the wrong ground: these picks are noise, not band evidence",
                     color=INK_BRIGHT, fontsize=11.5, x=0.01, ha="left", y=1.03)
    _caption(fig, "Each dot: a band centre added at that step; its area counts the searches "
            "(one per "
             "fold and seed) that chose it. Agreement across folds shows as one large dot.")
    _save(fig, out, "selection.png")
    return picks


def p6hs_criteria(H):
    """E-61 and E-62 as registered, paired by fold and seed."""
    e61, e62 = {}, {}
    for t, _, _ in HS_TARGETS:
        key = f"rmse_{t}"
        f, s, x = (H.get("swir_std", "fixed_only", key=key), H.get("swir_std", "k4", key=key),
                   H.get("swir_ext", "k4", key=key))
        fx = H.get("swir_ext", "fixed_only", key=key)
        kk = sorted(set(f) & set(s) & set(x) & set(fx))
        if len(kk) >= 3:
            gain_std = {i: f[i] - s[i] for i in kk}
            gain_ext = {i: fx[i] - x[i] for i in kk}
            mu, ci, _ = _fold_boot({i: gain_ext[i] - gain_std[i] for i in kk})
            e61[t] = {"gain_std": float(np.mean(list(gain_std.values()))),
                      "gain_ext": float(np.mean(list(gain_ext.values()))),
                      "extra": mu, "ci": ci, "runs": len(kk)}
        a, b = H.get("vnir_no_red_edge", "k6", key=key), H.get("vnir", "k6", key=key)
        kk = sorted(set(a) & set(b))
        if len(kk) >= 3:
            mu, ci, per = _fold_boot({i: 100 * (a[i] - b[i]) / b[i] for i in kk})
            e62[t] = {"d_pct": mu, "ci": ci, "folds_worse": int((per > 0).sum()),
                      "n_folds": len(per)}
    e62["red_edge_in_k6"] = {
        "runs": sum(kk[0] == "vnir" for kk in H.paths),
        "with": sum(any(700 <= _hs_band(s["added"])[0] <= 760 for s in p["steps"])
                    for kk, p in H.paths.items() if kk[0] == "vnir")}
    return e61, e62


def p6hs_placement(D, out):
    """Why the first pack failed: each line's footprint, north-up and placed."""
    plt = _plt()
    L = D["lines"]
    show = [k for k in ("ang20180721t192935", "ang20180811t204110", "ang20220810t202434")
            if k in L]
    fig = plt.figure(figsize=(14, 6.4), facecolor=FIG_BG)
    gs = fig.add_gridspec(2, 3, height_ratios=(1.5, 1), hspace=0.42, wspace=0.26)
    for j, k in enumerate(show):
        ax = fig.add_subplot(gs[0, j])
        _axes(ax, f"{k}  (rotation {L[k]['rotation_deg']:+.0f} deg)", "longitude", "latitude")
        o, n, p = (np.array(L[k][s]) for s in ("outline", "north_up", "placed"))
        ax.fill(n[:, 0], n[:, 1], color=ORANGE, alpha=0.35, lw=0, label="as first ingested "
                "(north-up)")
        ax.plot(n[:, 0], n[:, 1], color=ORANGE, lw=1)
        ax.fill(p[:, 0], p[:, 1], color=BLUE, alpha=0.45, lw=0, label="placed with its rotation")
        ax.plot(o[:, 0], o[:, 1], color=INK_BRIGHT, lw=0.9, label="ABoVE flight-line outline")
        ax.set_aspect(1 / np.cos(np.radians(float(np.mean(o[:, 1])))), adjustable="datalim")
        if j == 0:
            ax.legend(fontsize=7, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK,
                      loc="lower right")
    ax = fig.add_subplot(gs[1, :])
    ids = sorted(L)
    x = np.arange(len(ids))
    before = [100 * (D["inside_north_up"].get(k) or 0) for k in ids]
    after = [100 * (L[k]["inside"] or 0) for k in ids]
    _axes(ax, "Share of each line's pixels inside its flight-line outline", "",
          "% of pixels")
    ax.bar(x - 0.2, before, 0.38, color=ORANGE, label="north-up")
    ax.bar(x + 0.2, after, 0.38, color=BLUE, label="placed")
    ax.set_xticks(x)
    ax.set_xticklabels([k[5:11] + "\n" + k[12:16] for k in ids], fontsize=5.5, color=INK)
    ax.legend(fontsize=7.5, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK, loc="center right")
    _caption(fig, "ENVI map info ends in rotation=<deg>; the first ingest ignored it. Each line's "
             "rotation comes from its own header, recovered from the tail of the archive. The "
             "outlines are the ABoVE flight-line boundaries, an independent check.", y=0.02)
    _save(fig, out, "placement.png")


def p6hs_agreement(D, out):
    """Do the labels describe the pixels? NDVI against SCANFI, within each line."""
    plt = _plt()
    a, b = D["packs"]["north_up"], D["packs"]["rotated"]
    ids = sorted(set(a["lines"]) | set(b["lines"]), key=lambda k: k[3:])
    fig, axes = plt.subplots(1, 2, figsize=(13, 0.2 * len(ids) + 2.2), facecolor=FIG_BG,
                             sharey=True)
    rows = []
    for ax, (t, lab) in zip(axes, (("closure", "crown closure"), ("height", "canopy height")),
                            strict=True):
        _axes(ax, f"NDVI vs SCANFI {lab}, within each line", "Spearman rho", "")
        for i, k in enumerate(ids):
            u, v = a["lines"].get(k, {}).get(t), b["lines"].get(k, {}).get(t)
            if u is not None and v is not None:
                ax.plot([u, v], [i, i], color=SPINE, lw=1)
            if u is not None:
                ax.plot(u, i, "o", color=ORANGE, ms=5)
            if v is not None:
                ax.plot(v, i, "o", color=BLUE, ms=5)
            rows.append({"line": k, "target": t, "north_up": u, "placed": v})
        ax.axvline(0, color=INK, lw=1)
        ax.set_yticks(range(len(ids)))
        ax.set_yticklabels([k[3:] for k in ids], fontsize=6.5, color=INK)
    h = [plt.Line2D([], [], marker="o", ls="", color=ORANGE, label="first pack (north-up)"),
         plt.Line2D([], [], marker="o", ls="", color=BLUE, label="rotated pack")]
    axes[1].legend(handles=h, fontsize=7.5, facecolor=AX_BG, edgecolor=SPINE, labelcolor=INK,
                   loc="lower right")
    fig.tight_layout()
    _caption(fig, "Development pixels only; a data check, no fitting. NDVI is 865 vs 665 nm "
            "from the "
             "measured channels. A label sampled from the right ground should rise with NDVI "
             "within a line, across forest and open ground.", y=0.0)
    _save(fig, out, "label_agreement.png")
    return rows


def _hs_stability(H, arm, k):
    """The nested set the searches agree on: top k 50 nm regions, and how far they agree."""
    paths = [p for kk, p in H.paths.items() if kk[0] == arm]
    regions = {}
    for p in paths:
        for s in p["steps"][:k]:
            regions.setdefault(round(_hs_band(s["added"])[0] / 50) * 50, []).append(s["added"])
    top = sorted(regions.items(), key=lambda x: -len(x[1]))[:k]
    picks = [max(set(v), key=v.count) for _, v in top]
    shares = [len(v) / len(paths) for _, v in top]
    worst = min(shares)
    text = (f"stable: every region chosen in at least {worst:.0%} of searches" if worst >= 4 / 6
            else f"unstable: the searches disagree (least-chosen region in {worst:.0%})")
    return picks, text


def p6hs_options(H):
    """Every set scored in the sweep, as options for James (A-41)."""
    from safari_bands.band_options import Option, assess

    def stats(arm, name):
        d = H.get(arm, name)
        if not d:
            return None
        mu, _, per = _fold_boot(d)
        return mu, float(np.std(per, ddof=1) / np.sqrt(len(per)))

    opts = []
    for arm, lab, _ in (*HS_ARMS, ("references", "reference", None)):
        names = [r for r in dict.fromkeys(x["set"] for x in H.rows if x["arm"] == arm)]
        for name in names:
            s = stats(arm, name)
            if s is None:
                continue
            row = next(x for x in H.rows if x["arm"] == arm and x["set"] == name)
            bands, stable = row["bands"], ""
            if name.startswith("k"):
                fixed = H.paths[next(kk for kk in H.paths if kk[0] == arm)]["fixed"]
                picks, stable = _hs_stability(H, arm, int(name[1:]))
                bands = [*fixed, *picks]
            rmse = {t: float(np.mean(list(H.get(arm, name, key=f"rmse_{t}").values())))
                    for t, _, _ in HS_TARGETS}
            clean = H.get(arm, name, noisy=False)
            opts.append(Option(f"{lab}: {name}", list(bands), s[0], s[1], rmse,
                               float(np.mean(list(clean.values()))) if clean else None, stable))
    return assess(opts)


def p6hs_resources(H):
    rows = []
    for arm, _, _ in HS_ARMS:
        walls = [H.results[k]["wall_s"] / 60 for k in H.results if k[0] == arm]
        fits = [H.results[k]["fits"]["search"] + H.results[k]["fits"]["eval"]
                for k in H.results if k[0] == arm]
        if walls:
            rows.append({"arm": arm, "tasks": len(walls), "min_median": float(np.median(walls)),
                         "min_max": max(walls), "fits": max(fits)})
    return rows


def p6hs_tables(H, out, summ, e61, e62, res, D, void, options=None):
    L = ["# P6a-HS tables: the AVIRIS-NG band searches (E-61, E-62)\n"]
    if void:
        L += [f"**VOID FOR BANDS.** {void}\n"]
    n = sorted({r["pixels"]["outer_train"] + r["pixels"]["outer"] for r in H.results.values()})
    L += [f"Run: `{_rel(H.run)}`. Tasks: " + ", ".join(
        f"{a} {len(t)}" for a, t in H.tasks.items()) + f"; {n[0]:,} development pixels. The AVIRIS "
        "test set was not transferred.\n",
        "## Combined skill by nested set (raw + indices, with noise; noise-free in brackets)\n",
        "| arm | k = 0 (fixed VNIR) | k = 1 | k = 2 | k = 3 | k = 4 | k = 5 | k = 6 |",
        "|---|---|---|---|---|---|---|---|"]
    for arm, lab, _ in HS_ARMS:
        cells = []
        for name in ("fixed_only", "k1", "k2", "k3", "k4", "k5", "k6"):
            a, b = summ.get((arm, name, True)), summ.get((arm, name, False))
            cells.append("" if a is None else f"{a[0]:+.3f} ({b[0]:+.3f})" if b else f"{a[0]:+.3f}")
        L.append(f"| {lab} | " + " | ".join(cells) + " |")
    L += ["", "## Final nested set, per target (raw + indices, with noise)\n",
          "| arm | set | RMSE percent conifer (%) | RMSE closure (%) | RMSE height (m) | "
          "fuel family skill |", "|---|---|---|---|---|---|"]
    rows = []
    for arm, lab, _ in HS_ARMS:
        name = [s for s in H.sets(arm) if s != "fixed_only"][-1]
        vals = {t: np.mean(list(H.get(arm, name, key=f"rmse_{t}").values()))
                for t, _, _ in HS_TARGETS}
        fam = np.mean(list(H.get(arm, name, key="skill_family").values()))
        rows.append({"arm": arm, "set": name, **vals, "skill_family": fam})
        L.append(f"| {lab} | {name} | {vals['pc']:.1f} | {vals['closure']:.1f} | "
                 f"{vals['height']:.2f} | {fam:+.3f} |")
    _csv(out / "T_targets.csv", rows)
    L += ["", "## E-61 as registered: extended InGaAs against standard, k = 4 (RMSE removed from "
          "the fixed VNIR)\n",
          "| target | standard | extended | extra from extended [95 % CI] | runs |",
          "|---|---|---|---|---|"]
    for t, lab, unit in HS_TARGETS:
        r = e61.get(t)
        if r:
            L.append(f"| {lab} ({unit}) | {r['gain_std']:+.2f} | {r['gain_ext']:+.2f} | "
                     f"{r['extra']:+.2f} {_ci(r['ci'])} | {r['runs']} |")
    L += ["", "## E-62 as registered: no red edge minus VNIR, k = 6 (RMSE, % of VNIR)\n",
          "| target | difference [95 % CI] | folds worse |", "|---|---|---|"]
    for t, lab, _ in HS_TARGETS:
        r = e62.get(t)
        if r:
            L.append(f"| {lab} | {r['d_pct']:+.1f} % {_ci(r['ci'], 1)} | "
                     f"{r['folds_worse']}/{r['n_folds']} |")
    rr = e62["red_edge_in_k6"]
    L += ["", f"A band centred in 700-760 nm is in {rr['with']}/{rr['runs']} best 6-band "
            "VNIR sets."]
    if D:
        a, b = D["packs"]["north_up"], D["packs"]["rotated"]
        L += ["", "## Do the labels describe the pixels? NDVI against SCANFI (Spearman rho)\n",
              "| | first pack (north-up) | rotated pack |", "|---|---|---|",
              f"| development pixels | {a['n']:,} | {b['n']:,} |",
              f"| lines | {len(a['lines'])} | {len(b['lines'])} |"]
        for t, lab in (("closure", "crown closure"), ("height", "canopy height"),
                       ("pc", "percent conifer")):
            med = [np.median([v[t] for v in p["lines"].values() if v[t] is not None])
                   for p in (a, b)]
            L.append(f"| {lab}: pooled | {a['pooled'][t]:+.3f} | {b['pooled'][t]:+.3f} |")
            L.append(f"| {lab}: median within a line | {med[0]:+.3f} | {med[1]:+.3f} |")
        ins = [100 * v for v in D["inside_north_up"].values() if v is not None]
        placed = [100 * v["inside"] for v in D["lines"].values() if v["inside"] is not None]
        src = {}
        for v in D["lines"].values():
            src[v["rotation_source"]] = src.get(v["rotation_source"], 0) + 1
        L += ["", f"Pixels inside their flight-line outline: north-up "
                f"{min(ins):.1f}-{max(ins):.1f} "
              f"%, placed {min(placed):.1f}-{max(placed):.1f} %. Rotation sources: "
              + ", ".join(f"{k} {v}" for k, v in sorted(src.items())) + "."]
    if options:
        from safari_bands.band_options import markdown
        L += ["", "## The options\n", *markdown(options)]
        _csv(out / "T_options.csv", options)
    L += ["", "## Resources\n", "| arm | tasks | minutes, median | minutes, max | fits per task |",
          "|---|---|---|---|---|"]
    L += [f"| {r['arm']} | {r['tasks']} | {r['min_median']:.0f} | {r['min_max']:.0f} | "
            f"{r['fits']} |"
          for r in res]
    (out / "tables.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"  wrote {_rel(out / 'tables.md')}")


def p6hs(run: Path, out: Path, diag: Path | None = None, void: str = ""):
    out.mkdir(parents=True, exist_ok=True)
    H = _HSRun(run)
    ref = None
    s2 = _ROOT / "docs" / "results" / "p6a_ecology" / "summary.json"
    if s2.exists():
        ref = json.loads(s2.read_text())["curves"]["combined|6|raw+indices|noisy"][0]
    summ = p6hs_curves(H, out, ref, void)
    picks = p6hs_selection(H, out, void)
    e61, e62 = p6hs_criteria(H)
    D = json.loads(diag.read_text()) if diag else None
    agree = None
    if D:
        p6hs_placement(D, out)
        agree = p6hs_agreement(D, out)
        _csv(out / "T_label_agreement.csv", agree)
    res = p6hs_resources(H)
    options = None if void else p6hs_options(H)
    p6hs_tables(H, out, summ, e61, e62, res, D, void, options)
    (out / "summary.json").write_text(json.dumps(
        {"void": void, "curves": {f"{a}|{n}|{'noisy' if z else 'clean'}": v
                                  for (a, n, z), v in summ.items()},
         "selection": picks, "e61": e61, "e62": e62, "resources": res,
         "s2_reference": ref}, indent=1, default=float))
    (out / "run.json").write_text(json.dumps(
        {"run": str(_rel(run)), "diag": str(diag.name) if diag else None}, indent=1))


PHASES = {"P2": (p2, "p2_r0"), "P3": (p3, "p3_dated"), "P4": (p4, "p4_prefire"),
          "P5": (p5, "p5_slotnet"), "P6a": (p6a, "p6a_ecology"), "P6c": (p6c, "p6c_snow"),
          "P6b": (p6b, "p6b_cohort"), "P6d": (p6d, "p6d_startup"), "P6hs": (p6hs, "p6a_hs"),
          "P7": (p7, "p7_slots"),
          "P7b": (p7b, "p7b_operational"), "P7c": (p7c, "p7c_slots_v3")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--phase", required=True, choices=sorted(PHASES))
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--legacy-run", type=Path, default=None, help="P3: the P2 legacy run")
    ap.add_argument("--station-run", type=Path, default=None, help="P3: the station-weather run")
    ap.add_argument("--p3-run", type=Path, default=None, help="P5: the dated R0 run")
    ap.add_argument("--maps", type=Path, default=None,
                    help="P6a/P6c: prediction maps (default <run>/maps)")
    ap.add_argument("--signed-run", type=Path, default=None,
                    help="P6c: a snow run that records the signed error")
    ap.add_argument("--snowoff", type=Path, default=None, help="P6d: patch_snowoff.json")
    ap.add_argument("--diag", type=Path, default=None,
                    help="P6hs: georef_diag.json from aviris_georef_diag.py")
    ap.add_argument("--void", default="", help="P6hs: why this run says nothing about bands")
    args = ap.parse_args(argv)
    fn, sub = PHASES[args.phase]

    def resolve(p):
        return None if p is None else (p if p.is_absolute() else _ROOT / p).resolve()
    extra = {}
    if args.phase == "P3":
        extra = {"legacy": resolve(args.legacy_run), "station": resolve(args.station_run)}
    elif args.phase == "P5":
        extra = {"p3": resolve(args.p3_run)}
    elif args.phase == "P6c":
        extra = {"signed": resolve(args.signed_run), "maps": resolve(args.maps)}
    elif args.phase == "P6a":
        extra = {"maps": resolve(args.maps)}
    elif args.phase == "P6d":
        extra = {"snowoff": resolve(args.snowoff)}
    elif args.phase == "P6hs":
        extra = {"diag": resolve(args.diag), "void": args.void}
    fn(resolve(args.run), args.out or _ROOT / "docs" / "results" / sub, **extra)
    return 0


if __name__ == "__main__":
    sys.exit(main())
