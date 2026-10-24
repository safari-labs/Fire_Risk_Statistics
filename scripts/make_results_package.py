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


PHASES = {"P2": (p2, "p2_r0"), "P3": (p3, "p3_dated")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--phase", required=True, choices=sorted(PHASES))
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--legacy-run", type=Path, default=None, help="P3: the P2 legacy run")
    ap.add_argument("--station-run", type=Path, default=None, help="P3: the station-weather run")
    args = ap.parse_args(argv)
    fn, sub = PHASES[args.phase]

    def resolve(p):
        return None if p is None else (p if p.is_absolute() else _ROOT / p).resolve()
    extra = {}
    if args.phase == "P3":
        extra = {"legacy": resolve(args.legacy_run), "station": resolve(args.station_run)}
    fn(resolve(args.run), args.out or _ROOT / "docs" / "results" / sub, **extra)
    return 0


if __name__ == "__main__":
    sys.exit(main())
