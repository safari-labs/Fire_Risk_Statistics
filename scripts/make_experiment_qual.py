"""scripts/make_experiment_qual.py

One qualitative view per experiment, into that experiment's results folder, and
docs/results/QUALITATIVE_INDEX.md listing them. What the view is depends on what
the experiment varies:

    tiles       the output differs pixel by pixel, so the same seeded tiles are
                drawn for every arm
    patch map   the experiment moves one number per patch (a weather code, a
                start date). A tile would be flat, so each patch is a dot at its
                location, coloured by what the experiment changed
    line strips AVIRIS-NG packs hold sampled pixels of each flight line, not
                tiles: held-out pixels are binned along and across the track
    existing    a figure the phase's package already draws for this experiment
    none        nothing spatial to look at; QUAL says why

Reads only what the runs saved. Nothing is trained here, and only development
patches are read: every stem comes from a run's per_patch.csv or samples.npz.

    python scripts/make_experiment_qual.py
    python scripts/make_experiment_qual.py --only E-61 E-62
    python scripts/make_experiment_qual.py --only E-61 E-62 \
        --hs-run narval_results/hs_v3/<run> \
        --hs-pack ../Fire_Risk_Model/data/aviris_v3/dev.npz \
        --hs-out docs/results/p6a_hs_v3
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_results_package as R  # noqa: E402

ROOT = R._ROOT
RESULTS = ROOT / "docs" / "results"
INDEX = RESULTS / "QUALITATIVE_INDEX.md"
START, END = "<!-- qual:start -->", "<!-- qual:end -->"

P2_RUN = ROOT / "runs" / "20261024-1430_cffdrs_r0"
P3_RUN = ROOT / "runs" / "20261024-p3_cffdrs_r0_dated"
E18_RUN = ROOT / "runs" / "20261030-e18_s2_startup"
E56_RUN = ROOT / "runs" / "20261101-e56_cohort_2024_qual"
SLOTS_V2 = ROOT / "narval_results" / "slots_v2" / "7289478"
SLOTS_V3 = ROOT / "narval_results" / "slots_v3" / "20261026-2121"
HS_RUN = ROOT / "narval_results" / "hs_v2_provisional" / "20261030-1755"
HS_PACK = ROOT.parent / "Fire_Risk_Model" / "data" / "aviris_v2" / "dev.npz"
HS_OUT = RESULTS / "p6a_hs_v2_provisional"
E63_B = ROOT / "narval_results" / "e63_regime_b" / "20261101-2054"
PLOTS_RUN = ROOT / "narval_results" / "hs_plots" / "20261101-2024"
LIDAR_RUN = ROOT / "narval_results" / "hs_lidar" / "20261101-2024"
LIDAR_PACK = ROOT.parent / "Fire_Risk_Model" / "data" / "aviris_lidar_v1" / "dev.npz"
EXT_OUT = RESULTS / "p6a_external_labels"

HS_FAMILIES = ("C", "D", "M", "O", "S", "NF", "WA")
STRIP = (200, 36)       # bins along and across a line
HS_TARGETS = (("family", None, "fuel family", 0, ""), ("pc", 0, "percent conifer (%)", 100, "%"),
              ("closure", 1, "crown closure (%)", 100, "%"),
              ("height", 2, "canopy height (m)", 30, "m"))
HS_SETS = {
    "E-61": (("references", "sentinel2_p6_12band", "Sentinel-2 12 bands"),
             ("references", "config_c/VNIR", "fixed VNIR"),
             ("references", "config_a", "config A"), ("references", "config_b", "config B"),
             ("references", "config_c", "config C"), ("swir_std", "k4", "searched std, k = 4"),
             ("swir_ext", "k4", "searched ext, k = 4")),
    "E-62": (("references", "sentinel2_p6_12band", "Sentinel-2 12 bands"),
             ("references", "config_c/VNIR", "fixed VNIR"),
             ("references", "sensor_mantis_vnir6", "Mantis VNIR 6"),
             ("vnir", "k6", "searched VNIR, k = 6"),
             ("vnir_no_red_edge", "k6", "searched, no red edge, k = 6")),
}


# ---- tiles ----------------------------------------------------------------

def _qual(run: Path, stem: str):
    return np.load(run / "qual" / f"{stem}.npz")


def _seq_cmaps():
    from matplotlib.colors import LinearSegmentedColormap
    return (LinearSegmentedColormap.from_list("seq", ["#151b2b", "#1f4f8f", R.BLUE, "#bcd8fb"]),
            LinearSegmentedColormap.from_list("div", [R.ORANGE, "#5a5f70", R.BLUE]))


def _slot_value(Z, f, key):
    """'cfg:field', or 'cfg:field-cfg2:field' for a change in within-tile rank."""
    if "-" in key:
        a, b = key.split("-")
        return R._pct(_slot_value(Z, f, a)) - R._pct(_slot_value(Z, f, b))
    cfg, field = key.split(":")
    return Z[cfg][f][field][0, 0]


def slot_tiles(run: Path, cols, out: Path, name: str, title: str, caption: str,
               delta_max: float = 30.0, delta_label: str = "correction"):
    """One held-out fire tile per fold (seed 0) for the arms in cols; column
    one is the pack's true colour. cols: (key, label), key as _slot_value."""
    from matplotlib.colors import ListedColormap, TwoSlopeNorm
    plt = R._plt()
    seq, div = _seq_cmaps()
    cfgs = sorted({k.split(":")[0] for key, _ in cols for k in key.split("-")})
    Z = {c: [np.load(run / c / f"f{f}s0" / "samples.npz") for f in range(5)] for c in cfgs}
    cols = [("rgb", "Sentinel-2 true colour"), ("label", "NBAC burned on/after D"), *cols]
    fig, axes = plt.subplots(5, len(cols), figsize=(2.05 * len(cols), 2.2 * 5), facecolor=R.FIG_BG,
                             gridspec_kw={"wspace": 0.04, "hspace": 0.16, "top": 0.9,
                                          "bottom": 0.12})
    im_s = im_d = None
    seq_at, div_at = [], []
    for f in range(5):
        base = Z[cfgs[0]][f]
        stem = str(base["stems"][0])
        for c, (k, lab) in enumerate(cols):
            ax = axes[f, c]
            R._blank(ax)
            if k == "rgb":
                ax.imshow(R._stretch(base["rgb"][0]), interpolation="nearest")
            elif k == "label":
                a = base["label"][0, 0]
                ax.imshow(np.where(a < 0, 2, a),
                          cmap=ListedColormap([R.AX_BG, R.INK_BRIGHT, R.MUTED]), vmin=0, vmax=2,
                          interpolation="nearest")
            else:
                for cfg in {x.split(":")[0] for x in k.split("-")}:
                    assert str(Z[cfg][f]["stems"][0]) == stem, (cfg, f)
                a = _slot_value(Z, f, k)
                if ":delta_" in k:
                    im_d = ax.imshow(np.clip(a, -delta_max, delta_max), cmap=div,
                                     norm=TwoSlopeNorm(0, -delta_max, delta_max),
                                     interpolation="nearest")
                    div_at.append(c)
                elif "-" in k:
                    im_d = ax.imshow(np.clip(a, -0.3, 0.3), cmap=div,
                                     norm=TwoSlopeNorm(0, -0.3, 0.3), interpolation="nearest")
                    div_at.append(c)
                else:
                    im_s = ax.imshow(R._pct(a), cmap=seq, vmin=0, vmax=1, interpolation="nearest")
                    seq_at.append(c)
            if f == 0:
                ax.set_title(lab, color=R.INK, fontsize=8, loc="left")
            if c == 0:
                ax.set_ylabel(f"fold {f}\n" + stem.replace("_fire_tile", "\n"), color=R.INK,
                              fontsize=6.5)
    for im, at, lab in ((im_s, seq_at, "score percentile within the tile"),
                        (im_d, div_at, delta_label)):
        if im is not None:
            a, b = axes[-1, min(at)].get_position(), axes[-1, max(at)].get_position()
            cax = fig.add_axes([a.x0 + 0.005, a.y0 - 0.028, b.x1 - a.x0 - 0.01, 0.008])
            cb = fig.colorbar(im, cax=cax, orientation="horizontal")
            cb.set_label(lab, color=R.INK, fontsize=8)
            cb.ax.tick_params(colors=R.INK, labelsize=7.5)
    fig.suptitle(title, color=R.INK_BRIGHT, x=0.01, y=0.975, ha="left", fontsize=12)
    R._caption(fig, "True colour: the v2 pack's pre-fire composite (S2 SR median, D-45..D-1, "
               "B4/B3/B2). White = burned on or after D; grey = ignored or invalid. Scores as "
               "percentiles within the tile, which is what within-patch AUC ranks. " + caption,
               y=0.025)
    R._save(fig, out, name)


def e21_tiles(out: Path):
    S = json.loads((P3_RUN / "summary.json").read_text())
    R._tile_grid(
        S, P3_RUN, out,
        [("nbac", "NBAC burned"), ("scanfi_tree_2010_fuel", "fuel: SCANFI 2010"),
         ("scanfi_tree_2015_fuel", "fuel: SCANFI 2015"),
         ("scanfi_tree_2020_fuel", "fuel: SCANFI 2020"),
         ("scanfi_tree_2010_hfi", "HFI: SCANFI 2010"),
         ("scanfi_tree_2015_hfi", "HFI: SCANFI 2015"),
         ("scanfi_tree_2020_hfi", "HFI: SCANFI 2020")],
        "E-21  The same tiles under older and newer fuel inventories",
        "White = burned (NBAC). Same dated weather on every row, so differences across the "
        "columns are the inventory's age alone. Reconstructed (ours).",
        name="qual_E-21_inventory_age.png")


def e32_tiles(out: Path):
    S = json.loads((P2_RUN / "summary.json").read_text())
    R._tile_grid(
        S, P2_RUN, out,
        [("nbac", "NBAC burned"), ("cwfis_2019_fuel", "fuel: CWFIS 2019"),
         ("scanfi_tree_prefire_fuel", "fuel: SCANFI pre-fire"),
         ("cwfis_2019_hfi", "R0 HFI: CWFIS 2019"),
         ("scanfi_tree_prefire_hfi", "R0 HFI: SCANFI pre-fire")],
        "E-32  CFFDRS as is: R0 intensity against what burned",
        "White = burned (NBAC). R0 is the FBP equations with no learning, so within a tile only "
        "fuel and slope vary. Reconstructed (ours).", name="qual_E-32_r0.png")


def e33_tiles(out: Path):
    S = json.loads((P2_RUN / "summary.json").read_text())
    R._tile_grid(
        S, P2_RUN, out,
        [("nbac", "NBAC burned"), ("cwfis_2014b_fuel", "fuel: CWFIS 2014b"),
         ("cwfis_2019_fuel", "fuel: CWFIS 2019"), ("cwfis_2024_fuel", "fuel: CWFIS 2024"),
         ("scanfi_tree_prefire_fuel", "fuel: SCANFI pre-fire"),
         ("scanfi_a11_prefire_fuel", "fuel: SCANFI A-11")],
        "E-33  Each fuel inventory on the same tiles",
        "White = burned (NBAC). The CWFIS columns are the published layers, and the 2024 layer is "
        "post-fire on burned ground, which shows as fuel changing inside the burn. The SCANFI "
        "columns are our fuel rules applied to SCANFI.",
        name="qual_E-33_inventories.png")


def e49_tiles(out: Path):
    """Legacy (30 June) against dated weather. Two runs, so not _tile_grid."""
    from matplotlib.colors import LinearSegmentedColormap, ListedColormap, LogNorm
    plt = R._plt()
    S = json.loads((P3_RUN / "summary.json").read_text())
    stems = S["config"]["qual_stems"]
    key = "scanfi_tree_prefire_hfi"
    heat = LinearSegmentedColormap.from_list("heat", ["#241a17", "#8a3a1c", R.ORANGE, "#ffd2a6"])
    titles = ["Sentinel-2 true colour", "NBAC burned", "HFI: legacy, 30-June weather",
              "HFI: dated, D-1 weather"]
    fig, axes = plt.subplots(len(stems), 4, figsize=(2.6 * 4, 2.5 * len(stems)), facecolor=R.FIG_BG,
                             gridspec_kw={"wspace": 0.04, "hspace": 0.2, "top": 0.9,
                                          "bottom": 0.05})
    im, sources = None, set()
    for r, stem in enumerate(stems):
        a, b = _qual(P2_RUN, stem), _qual(P3_RUN, stem)
        sources.add(str(b["rgb_source"]))
        cells = (b["rgb"], b["nbac"], a[key], b[key])
        for c, x in enumerate(cells):
            ax = axes[r, c]
            R._blank(ax)
            if c == 0:
                ax.imshow(x, interpolation="nearest")
                ax.set_ylabel(stem.replace("_fire", ""), color=R.INK, fontsize=7.5)
            elif c == 1:
                ax.imshow(x, cmap=ListedColormap([R.AX_BG, R.INK_BRIGHT]), vmin=0, vmax=1,
                          interpolation="nearest")
            else:
                im = ax.imshow(np.clip(x, 10, None), cmap=heat, norm=LogNorm(10, 30000),
                               interpolation="nearest")
            if r == 0:
                ax.set_title(titles[c], color=R.INK, fontsize=8.5, loc="left")
    cb = fig.colorbar(im, ax=axes[:, 2:], fraction=0.03, pad=0.01)
    cb.set_label("head fire intensity (kW/m, log)", color=R.INK, fontsize=8)
    cb.ax.tick_params(colors=R.INK, labelsize=7.5)
    fig.suptitle("E-49  The same tiles under legacy and dated weather", color=R.INK_BRIGHT, x=0.01,
                 y=0.98, ha="left", fontsize=12)
    R._caption(fig, "True colour: " + "; ".join(sorted(sources)) + ". White = burned (NBAC). "
               "Same fuel in both HFI columns, so only the weather date moves. Reconstructed "
               "(ours).", y=0.0)
    R._save(fig, out, "qual_E-49_weather_date.png")


def e56_tiles(out: Path):
    """Reconstructed tiles beside the issued patch mean. CWFIS grids are held as
    patch statistics, so an issued map cannot be drawn."""
    from matplotlib.colors import LinearSegmentedColormap, ListedColormap, LogNorm
    plt = R._plt()
    S = json.loads((E56_RUN / "summary.json").read_text())
    stems = S["config"]["qual_stems"]
    variant = R.E56_R0[0][0]
    heat = LinearSegmentedColormap.from_list("heat", ["#241a17", "#8a3a1c", R.ORANGE, "#ffd2a6"])
    fam_of = {f: i for i, (_, fs, _) in enumerate(R.FAMILY) for f in fs}
    fam_cmap = ListedColormap([c for _, _, c in R.FAMILY] + [R.AX_BG])
    titles = ["Sentinel-2 true colour", "NBAC burned", "Fuel: CWFIS 2024 layer",
              "HFI: " + R.E56_R0[0][1]]
    fig, axes = plt.subplots(len(stems), 4, figsize=(2.6 * 4 + 1.6, 2.5 * len(stems)),
                             facecolor=R.FIG_BG,
                             gridspec_kw={"wspace": 0.04, "hspace": 0.3, "top": 0.87,
                                          "bottom": 0.07, "left": 0.06, "right": 0.86})
    rows = {r["stem"]: r for r in R._e56_rows(E56_RUN)}
    im, sources = None, set()
    for i, stem in enumerate(stems):
        z = _qual(E56_RUN, stem)
        sources.add(str(z["rgb_source"]) if "rgb_source" in z else "")
        for c in range(4):
            ax = axes[i, c]
            R._blank(ax)
            if c == 0:
                ax.imshow(z["rgb"], interpolation="nearest")
                ax.set_ylabel(stem.replace("_fire", ""), color=R.INK, fontsize=7.5)
            elif c == 1:
                ax.imshow(z["nbac"], cmap=ListedColormap([R.AX_BG, R.INK_BRIGHT]), vmin=0, vmax=1,
                          interpolation="nearest")
            elif c == 2:
                idx = np.vectorize(lambda f: fam_of.get(f, len(R.FAMILY)))(z[f"{variant}_fuel"])
                ax.imshow(idx, cmap=fam_cmap, vmin=-0.5, vmax=len(R.FAMILY) + 0.5,
                          interpolation="nearest")
            else:
                im = ax.imshow(np.clip(z[f"{variant}_hfi"], 10, None), cmap=heat,
                               norm=LogNorm(10, 30000), interpolation="nearest")
                r = rows[stem]
                issued = r["issued"]["hfi"]
                ax.set_xlabel(("no HFI ISSUED by CWFIS for this patch" if np.isnan(issued)
                               else f"ISSUED by CWFIS, patch mean: {issued:,.0f} kW/m")
                              + "\nReconstructed (ours), patch mean: "
                              f"{r['R0'][variant]['hfi']:,.0f} kW/m", color=R.INK, fontsize=7)
            if i == 0:
                ax.set_title(titles[c], color=R.INK, fontsize=8.5, loc="left")
    fig.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c, label=n) for n, _, c in R.FAMILY],
               loc="upper left", bbox_to_anchor=(0.01, 0.945), ncol=4, frameon=False,
               labelcolor=R.INK, fontsize=8)
    cb = fig.colorbar(im, cax=fig.add_axes([0.915, 0.3, 0.012, 0.4]))
    cb.set_label("head fire intensity (kW/m, log)", color=R.INK, fontsize=8)
    cb.ax.tick_params(colors=R.INK, labelsize=7.5)
    fig.suptitle("E-56  2024 fire tiles: reconstructed maps beside the issued patch mean",
                 color=R.INK_BRIGHT, x=0.01, y=0.985, ha="left", fontsize=12)
    R._caption(fig, "True colour: " + "; ".join(sorted(s for s in sources if s)) + ". White = "
               "burned (NBAC). The tiles are the evaluator's seeded 2024 fire patches. CWFIS "
               "grids are held as patch statistics, so no issued map exists to draw.", y=0.0)
    R._save(fig, out, "qual_E-56_cohort_tiles.png")


# ---- patch maps -----------------------------------------------------------

def _dev_stems(run: Path) -> list[dict]:
    """One row per development patch of a run: stem, lon, lat."""
    seen = {}
    for r in R._read_csv(run / "per_patch.csv"):
        seen.setdefault(r["stem"], {"stem": r["stem"], "lon": float(r["lon"]),
                                    "lat": float(r["lat"])})
    return list(seen.values())


def _lag(stem: str, variant: str, lag: str, code: str) -> float:
    p = R.PATCHES / f"{stem}_fwi_v2.json"
    if not p.exists():
        return float("nan")
    v = json.loads(p.read_text())["variants"].get(variant)
    x = None if v is None else v["lags"].get(lag, {}).get(code)
    return float("nan") if x is None else float(x)


def _symmetric_max(v: np.ndarray) -> float:
    m = float(np.nanpercentile(np.abs(v), 98))
    return m if m > 0 else 1.0


def patch_map(pos, panels, out: Path, name: str, title: str, caption: str,
              clip: float | None = None, what: str = "patch"):
    """Each patch a dot at its location. panels: (values, label, unit). The
    scale is the 98th percentile of the change, or *clip* when given."""
    plt = R._plt()
    fig, axes = plt.subplots(1, len(panels), figsize=(6.4 * len(panels), 4.7), facecolor=R.FIG_BG,
                             squeeze=False)
    lon, lat = np.array([p["lon"] for p in pos]), np.array([p["lat"] for p in pos])
    shared = clip
    if shared is None and len({u for _, _, u in panels}) == 1:
        shared = max(_symmetric_max(v[np.isfinite(v)]) for v, _, _ in panels)
    for ax, (v, lab, unit) in zip(axes[0], panels, strict=True):
        R._axes(ax, lab, "longitude", "latitude")
        ok = np.isfinite(v)
        m = shared or _symmetric_max(v[ok])
        sc = ax.scatter(lon[ok], lat[ok], c=np.clip(v[ok], -m, m), cmap="RdBu_r", vmin=-m, vmax=m,
                        s=14, edgecolors="none")
        plural = f"{what}es" if what.endswith("ch") else f"{what}s"
        ax.text(0.01, 0.02,
                f"median {np.median(v[ok]):+.2g} {unit}; n = {int(ok.sum())} {plural}",
                transform=ax.transAxes, color=R.INK_BRIGHT, fontsize=8)
        cb = fig.colorbar(sc, ax=ax, fraction=0.035, pad=0.02)
        cb.set_label(unit, color=R.INK, fontsize=8)
        cb.ax.tick_params(colors=R.INK, labelsize=7.5)
    fig.suptitle(title, color=R.INK_BRIGHT, x=0.01, y=1.0, ha="left", fontsize=12)
    fig.tight_layout()
    scale = f"clipped at +/-{clip:g}" if clip else "clipped at the 98th percentile of the change"
    R._caption(fig, f"Each dot is one development {what}. Blue is lower, red higher, {scale}. "
               + caption, y=-0.02)
    R._save(fig, out, name)


def e50_map(out: Path):
    pos = _dev_stems(P3_RUN)
    d = np.array([_lag(p["stem"], "c2_daylat", "1", "dmc") - _lag(p["stem"], "c2", "1", "dmc")
                  for p in pos])
    patch_map(pos, [(d, "DMC at D-1: latitude day length minus 46 N table", "DMC units")], out,
              "qual_E-50_patch_map.png", "E-50  Where latitude-correct day length moves DMC",
              "The change is one number per patch, so a tile would be flat. Reconstructed (ours).")


def e51_map(out: Path):
    pos = _dev_stems(P3_RUN)
    panels = [(np.array([_lag(p["stem"], "c2", "1", c) - _lag(p["stem"], "flat", "1", c)
                         for p in pos]), f"{c.upper()} at D-1: C-2 start-up minus flat spin-up",
               f"{c.upper()} units") for c in ("dc", "dmc")]
    patch_map(pos, panels, out, "qual_E-51_patch_map.png",
              "E-51  Where the operational start-up moves the slow codes",
              "The change is one number per patch, so a tile would be flat. Reconstructed (ours).")


def e52_map(out: Path):
    pos = _dev_stems(P3_RUN)
    d = []
    for p in pos:
        f = R.PATCHES / f"{p['stem']}_station.json"
        v = (json.loads(f.read_text()).get("lags") or {}).get("1") or {} if f.exists() else {}
        d.append(float("nan") if v.get("fwi") is None
                 else float(v["fwi"]) - _lag(p["stem"], "c2", "1", "fwi"))
    patch_map(pos, [(np.array(d), "FWI at D-1: nearest station minus ERA5-Land", "FWI")], out,
              "qual_E-52_patch_map.png", "E-52  Where station and ERA5 weather disagree",
              "Weather is one value per patch, so a tile would be flat. Reconstructed (ours) from "
              "both sources.")


def e53_map(out: Path):
    pos = _dev_stems(P3_RUN)
    panels = [(np.array([_lag(p["stem"], "c2", "7", c) - _lag(p["stem"], "c2", "1", c)
                         for p in pos]), f"{c.upper()}: 7 days old minus 1 day old", c.upper())
              for c in ("ffmc", "fwi")]
    patch_map(pos, panels, out, "qual_E-53_patch_map.png",
              "E-53  What a week of staleness does to the codes",
              "Weather is one value per patch, so a tile would be flat. Reconstructed (ours).")


def e55_map(out: Path):
    pos = _dev_stems(P3_RUN)
    d = []
    for p in pos:
        f = R.PATCHES / f"{p['stem']}_cwfis_grid.json"
        layers = json.loads(f.read_text())["layers"] if f.exists() else {}
        v = (layers.get("fwi") or {}).get("mean")
        d.append(float("nan") if v is None else float(v) - _lag(p["stem"], "c2", "1", "fwi"))
    patch_map(pos, [(np.array(d), "FWI on D-1: ISSUED by CWFIS minus Reconstructed (ours)", "FWI")],
              out, "qual_E-55_patch_map.png", "E-55  Where the issued FWI and ours disagree",
              "CWFIS grids are held as patch statistics, so no issued map exists to draw at tile "
              "scale. Red = CWFIS issued a higher FWI than our reconstruction.")


def e18_map(out: Path):
    pos = _dev_stems(E18_RUN)
    by = {r["stem"]: r for r in R._e18_patches([p["stem"] for p in pos])}

    def gap(p, arm):
        r = by.get(p["stem"])
        if not r or not r[f"{arm}_start"] or not r["c2_start"]:
            return float("nan")
        return float((np.datetime64(r[f"{arm}_start"]) - np.datetime64(r["c2_start"]))
                     / np.timedelta64(1, "D"))
    panels = [(np.array([gap(p, a) for p in pos]), f"Season start: {n} minus ERA5 snow", "days")
              for a, n, _ in R.E18_ARMS]
    patch_map(pos, panels, out, "qual_E-18_patch_map.png",
              "E-18  Where the Sentinel-2 snow-off date moves the season start",
              "The start date is one value per patch and the run's saved tiles used the ERA5 "
              "start-up, so a tile would show nothing. Red = imagery starts the season later.")


def e56_map(out: Path):
    rows = R._e56_rows(E56_RUN)
    variant = R.E56_R0[0][0]
    use = [r for r in rows if variant in r["R0"]]
    lon = {r["stem"]: r["lon"] for r in _dev_stems(E56_RUN)}
    pos = [{"stem": r["stem"], "lon": lon[r["stem"]], "lat": r["lat"]} for r in use]
    with np.errstate(divide="ignore", invalid="ignore"):
        d = np.array([np.log10(r["R0"][variant]["hfi"] / r["issued"]["hfi"]) for r in use])
    d[~np.isfinite(d)] = np.nan
    patch_map(pos, [(d, "HFI on D-1: log10 (Reconstructed (ours) / ISSUED by CWFIS)",
                     "log10 ratio")],
              out, "qual_E-56_patch_map.png", "E-56  Where our HFI and the issued HFI disagree",
              "2024 patches where both sources give a positive HFI; 2025 is the frozen time test "
              "and is not read. Near-zero values make extreme ratios, hence the fixed clip (a "
              "factor of 30). Red = our reconstruction is above what CWFIS issued.", clip=1.5)


def e63_map(out: Path):
    Y = R._Year2024(E63_B)
    lonlat = {r["stem"]: (float(r["lon"]), float(r["lat"]))
              for r in R._read_csv(R.E63_R0_2024 / "per_patch.csv")}
    pos = [{"stem": p, "lon": lonlat[p][0], "lat": lonlat[p][1]} for p in Y.pat]
    w = np.nanmean(Y.W["r1"], axis=0) - Y.r0_w
    w[~Y.fire] = np.nan
    sign = np.where(Y.fire, 1.0, -1.0)
    rank = (R._rank(Y.S["r1"].mean(axis=0)) - R._rank(np.nan_to_num(Y.r0_s))) / len(Y.pat)
    patch_map(pos, [(w, "Within-patch AUC: R1 minus R0, 2024 fires", "AUC"),
                    (100 * sign * rank, "Between patches: rank gained by R1 over R0, 2024",
                     "percentile points")], out, "qual_E-63_patch_map.png",
              "E-63  Where R1 beats the physics on a year it never saw",
              "Regime B, 15 models averaged; R0 is HFI on SCANFI 2020 fuel; both Reconstructed "
              "(ours). Right: red means R1 moved the patch the right way (fires up, unburned "
              "down). The runs save tiles from 2019-2023 only, so a 2024 tile needs a job. "
              "2025 is frozen and was not opened.")


def _pool_preds(run: Path, arm: str, names: list[str]) -> dict:
    """Held-out predictions over the five folds, seed 0."""
    keep = ("y", "lon", "lat", "line", "group")
    zs = [np.load(p) for p in sorted((run / arm).glob("f*s0/pred.npz"))]
    return {k: np.concatenate([z[k] for z in zs])
            for k in (*keep, *(f"{n}__{t}" for n in names for t in ("pc", "height")))}


def e22_plots_map(out: Path):
    z = _pool_preds(PLOTS_RUN, "references", ["vnir6", "vnir6_swir1"])
    cell = np.round(z["lon"] * 4) / 4 + 1j * np.round(z["lat"] * 4) / 4
    cells, inv, n = np.unique(cell, return_inverse=True, return_counts=True)
    use = n >= 5
    pos = [{"lon": c.real, "lat": c.imag} for c in cells[use]]
    panels = []
    for t, j, lab, unit in (("pc", 0, "percent conifer", "% conifer"),
                            ("height", 2, "height", "m")):
        ok = np.isfinite(z["y"][:, j])
        gain = (np.abs(z[f"vnir6__{t}"] - z["y"][:, j])
                - np.abs(z[f"vnir6_swir1__{t}"] - z["y"][:, j]))
        cnt = np.bincount(inv[ok], minlength=len(cells))
        v = np.bincount(inv[ok], weights=gain[ok], minlength=len(cells)) / np.maximum(cnt, 1)
        panels.append((v[use], f"{lab}: error removed by adding SWIR1", unit))
    patch_map(pos, panels, out, "qual_E-22_plots_map.png",
              "Ground plots  Where SWIR1 helps most against measured labels",
              "A cell is 0.25 degrees with at least 5 held-out plots, seed 0. Red: "
              "adding 1610 nm to six VNIR bands lowers the absolute error against the ground "
              "measurement. Plots have no image tile; each is one point.", what="cell")


def _bin_median(v, idx, bins=40):
    return np.array([np.median(v[idx == b]) if (idx == b).sum() >= 5 else np.nan
                     for b in range(bins)])


def lidar_tracks(out: Path):
    plt = R._plt()
    names = {"config_c/VNIR": ("VNIR 6", R.ORANGE), "config_b": ("config B", R.BLUE)}
    z = _pool_preds(LIDAR_RUN, "references", list(names))
    top = np.argsort(np.bincount(z["line"]))[::-1][:4]
    fig, axes = plt.subplots(len(top), 1, figsize=(11, 2.1 * len(top)), facecolor=R.FIG_BG)
    pack = np.load(LIDAR_PACK)
    ids = pack["line_ids"]
    for ax, line in zip(axes, top, strict=True):
        i = np.flatnonzero((z["line"] == line) & np.isfinite(z["y"][:, 2]))
        cos, origin, vt, _ = strip_axes(z["lon"][i], z["lat"][i])
        s = ((np.column_stack([z["lon"][i] * cos, z["lat"][i]]) - origin) @ vt.T)[:, 0]
        bins = np.linspace(s.min(), s.max(), 41)
        idx = np.clip(np.digitize(s, bins) - 1, 0, 39)
        mid = (bins[:-1] + bins[1:]) / 2 * 111

        R._axes(ax, f"{ids[line]}: {len(i):,} held-out pixels", "", "height (m)")
        ax.plot(mid, _bin_median(z["y"][i, 2], idx), color=R.INK_BRIGHT, lw=2, label="ATL08 lidar")
        for k, (lab, col) in names.items():
            ax.plot(mid, _bin_median(z[f"{k}__height"][i], idx), color=col, lw=1.6, label=lab)
    axes[0].legend(fontsize=7.5, facecolor=R.AX_BG, edgecolor=R.SPINE, labelcolor=R.INK, ncol=3,
                   loc="upper right")
    axes[-1].set_xlabel("distance along the line (km)", color=R.INK, fontsize=8)
    fig.tight_layout()
    R._caption(fig, "Median in 40 bins along each flight line with the most held-out lidar pixels, "
               "seed 0, bins with at least 5 pixels. Lidar covers tracks, not swaths, so a strip "
               "image would be mostly empty.", y=-0.01)
    R._save(fig, out, "qual_lidar_tracks.png")


# ---- AVIRIS-NG line strips ------------------------------------------------

def strip_axes(lon, lat):
    """The track of a line, as (origin, axes, scale ranges), to bin pixels with
    strip_grid. The first principal axis is the track, so a rotated line becomes
    an upright strip. Ranges are the 0.5-99.5 % of the pixels: where a filter
    removed most of a line, a few strays must not squeeze what is left."""
    cos = np.cos(np.radians(lat.mean()))
    xy = np.column_stack([lon * cos, lat])
    origin = xy.mean(axis=0)
    _, _, vt = np.linalg.svd((xy - origin)[:: max(len(xy) // 5000, 1)], full_matrices=False)
    uv = (xy - origin) @ vt.T
    return cos, origin, vt, np.percentile(uv, [0.5, 99.5], axis=0)


def strip_grid(axes, lon, lat, height: int | None = None, width: int | None = None):
    """Along- and across-track bin of each pixel, on one line's strip_axes, so
    every panel of a line shares its bins."""
    cos, origin, vt, (lo, hi) = axes
    uv = (np.column_stack([lon * cos, lat]) - origin) @ vt.T
    f = np.clip((uv - lo) / np.maximum(hi - lo, 1e-12), 0, 1 - 1e-9)
    return (f[:, 0] * (height or STRIP[0])).astype(int), (f[:, 1] * (width or STRIP[1])).astype(int)


def strip_fill(lon, lat) -> float:
    """Share of along-track rows holding a pixel. A line the bright filter cut
    to two far-apart pieces scores low, and its strip would be nearly empty."""
    r, _ = strip_grid(strip_axes(lon, lat), lon, lat)
    return len(np.unique(r)) / STRIP[0]


def strip_mean(r, c, v, shape) -> np.ndarray:
    total, n = np.zeros(shape), np.zeros(shape)
    np.add.at(total, (r, c), v)
    np.add.at(n, (r, c), 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return total / n


def strip_mode(r, c, v, shape, n_class: int) -> np.ndarray:
    n = np.zeros((n_class, *shape))
    np.add.at(n, (v, r, c), 1)
    out = n.argmax(axis=0).astype(float)
    out[n.sum(axis=0) == 0] = np.nan
    return out


def _hs_true_colour(pack, r, c, shape, keep):
    wl = pack["wavelength"]
    out = []
    for nm in (640, 550, 470):
        i = np.flatnonzero(np.abs(wl - nm) <= 15)
        out.append(strip_mean(r, c, pack["spectra"][keep, :][:, i].mean(axis=1), shape))
    return R._stretch(np.nan_to_num(np.stack(out)))


def _strip_cell(ax, p: dict, values, j, vmax, fcmap):
    """Draw a target on a line's bins; the image, for a regression's colour bar."""
    if j is None:
        g = strip_mode(p["r"], p["c"], values.astype(int), STRIP, len(HS_FAMILIES))
        ax.imshow(np.ma.masked_invalid(g), cmap=fcmap, vmin=-0.5, vmax=len(HS_FAMILIES) - 0.5,
                  interpolation="nearest", aspect="auto")
        return None
    g = strip_mean(p["r"], p["c"], values, STRIP)
    return ax.imshow(np.ma.masked_invalid(g), cmap="viridis", vmin=0, vmax=vmax,
                     interpolation="nearest", aspect="auto")


def hs_strips(run: Path, pack_path: Path, out: Path, eid: str) -> list[str]:
    """For each outer fold, one seeded held-out line: label and each set's
    prediction. A set whose fold has not run shows 'not run'."""
    from matplotlib.colors import ListedColormap
    plt = R._plt()
    sets = HS_SETS[eid]
    pack = np.load(pack_path)
    pack = {k: pack[k] for k in ("wavelength", "spectra", "line", "lon", "lat", "line_ids")}
    folds = sorted({int(p.parent.name[1]) for p in run.glob("references/f*s0/pred.npz")})
    picks, rng = [], np.random.default_rng(0)
    for f in folds:
        z = np.load(run / "references" / f"f{f}s0" / "pred.npz")
        lines = np.unique(z["line"])
        full = [x for x in lines if strip_fill(z["lon"][z["line"] == x],
                                               z["lat"][z["line"] == x]) >= 0.5]
        line = int(rng.choice(full or lines))
        i = np.flatnonzero(z["line"] == line)
        axes = strip_axes(z["lon"][i], z["lat"][i])
        r, c = strip_grid(axes, z["lon"][i], z["lat"][i])
        keep = np.flatnonzero(pack["line"] == line)
        rp, cp = strip_grid(axes, pack["lon"][keep], pack["lat"][keep])
        picks.append({"fold": f, "line": line, "i": i, "r": r, "c": c, "y": z["y"][i],
                      "family": z["family"][i],
                      "rgb": _hs_true_colour(pack, rp, cp, STRIP, keep),
                      "group": int(z["group"][i][0])})
    fcmap = ListedColormap([R.ECO_FAMILY_COL[x] for x in HS_FAMILIES])
    made = []
    for tname, j, lab, vmax, unit in HS_TARGETS:
        cols = 2 + len(sets)
        fig, axes = plt.subplots(len(picks), cols, figsize=(1.55 * cols, 4.2 * len(picks)),
                                 facecolor=R.FIG_BG, squeeze=False,
                                 gridspec_kw={"wspace": 0.05, "hspace": 0.12, "top": 0.94,
                                              "bottom": 0.06})
        im = None
        for row, p in enumerate(picks):
            ax = axes[row, 0]
            R._blank(ax)
            ax.imshow(p["rgb"], interpolation="nearest", aspect="auto")
            ax.set_ylabel(f"fold {p['fold']}, group {p['group']}\n"
                          f"{pack['line_ids'][p['line']]}", color=R.INK, fontsize=7)
            ax = axes[row, 1]
            R._blank(ax)
            label = p["family"] if j is None else p["y"][:, j]
            im = _strip_cell(ax, p, label, j, vmax, fcmap) or im
            if row == 0:
                axes[0, 0].set_title("AVIRIS-NG\ntrue colour", color=R.INK_BRIGHT, fontsize=8,
                                     loc="left")
                ax.set_title("SCANFI\nlabel", color=R.INK_BRIGHT, fontsize=8, loc="left")
            for c, (arm, name, title) in enumerate(sets, start=2):
                ax = axes[row, c]
                R._blank(ax)
                if row == 0:
                    ax.set_title(title.replace(", ", ",\n"), color=R.INK_BRIGHT, fontsize=8,
                                 loc="left")
                f = run / arm / f"f{p['fold']}s0" / "pred.npz"
                z = np.load(f) if f.exists() else None
                if z is None or f"{name}__{tname}" not in z.files:
                    ax.text(0.5, 0.5, "not run", color=R.MUTED, ha="center",
                            transform=ax.transAxes, fontsize=8)
                    continue
                pred = z[f"{name}__{tname}"][p["i"]]
                im = _strip_cell(ax, p, pred, j, vmax, fcmap) or im
                score = (f"{np.mean(pred == label):.0%}" if j is None
                         else f"{np.sqrt(np.mean((pred - label) ** 2)):.1f} {unit}")
                ax.text(0.03, 0.01, score, transform=ax.transAxes, color=R.INK_BRIGHT, fontsize=7,
                        bbox={"facecolor": R.FIG_BG, "alpha": 0.75, "lw": 0, "pad": 1.5})
        if j is None:
            handles = [plt.Rectangle((0, 0), 1, 1, color=R.ECO_FAMILY_COL[x]) for x in HS_FAMILIES]
            fig.legend(handles, HS_FAMILIES, loc="lower center", ncol=len(HS_FAMILIES),
                       frameon=False, labelcolor=R.INK, fontsize=8, bbox_to_anchor=(0.5, 0.025))
        else:
            cax = fig.add_axes([0.3, 0.04, 0.4, 0.006])
            cb = fig.colorbar(im, cax=cax, orientation="horizontal")
            cb.set_label(lab, color=R.INK, fontsize=8)
            cb.ax.tick_params(colors=R.INK, labelsize=7)
        fig.suptitle(f"{eid}  {lab}: held-out AVIRIS-NG lines, each band set (seed 0)",
                     color=R.INK_BRIGHT, x=0.01, y=0.975, ha="left", fontsize=11)
        R._caption(fig, "One seeded held-out line per outer fold, from lines whose pixels fill at "
                   "least half the track; track upright, width stretched to be readable. Sampled "
                   "pixels are binned, so this is a strip view, not an "
                   "image. True colour comes from the line's own 640/550/470 nm reflectance: no "
                   "Sentinel-2 view is held for these lines. Bottom left: pixel agreement or RMSE "
                   f"on this line. Compare only within a row. Pack: {pack_path.parent.name}.",
                   y=0.02)
        name = f"qual_{eid}_{tname}.png"
        R._save(fig, out, name)
        made.append(name)
    return made


# ---- the register of views ------------------------------------------------

SV2, SV3 = SLOTS_V2, SLOTS_V3
BUILD = {
    "E-32": lambda: e32_tiles(RESULTS / "p2_r0"),
    "E-33": lambda: e33_tiles(RESULTS / "p2_r0"),
    "E-21": lambda: e21_tiles(RESULTS / "p3_dated"),
    "E-49": lambda: e49_tiles(RESULTS / "p3_dated"),
    "E-50": lambda: e50_map(RESULTS / "p3_dated"),
    "E-51": lambda: e51_map(RESULTS / "p3_dated"),
    "E-52": lambda: e52_map(RESULTS / "p3_dated"),
    "E-53": lambda: e53_map(RESULTS / "p3_dated"),
    "E-55": lambda: e55_map(RESULTS / "p7b_operational"),
    "E-18": lambda: e18_map(RESULTS / "p6d_startup"),
    "E-56": lambda: (e56_map(RESULTS / "p6b_cohort"), e56_tiles(RESULTS / "p6b_cohort")),
    "E-63": lambda: e63_map(RESULTS / "p6e_out_of_time"),
    "E-22": lambda: (e22_plots_map(EXT_OUT), lidar_tracks(EXT_OUT)),
    "E-36": lambda: slot_tiles(
        SV2, [("r2:pred", "R2"), ("r3_pc:pred", "R3 PC"), ("r3_pc:delta_pc", "PC correction"),
              ("r3_pc_shuffled:delta_pc", "twin's correction")], RESULTS / "p7_slots",
        "qual_E-36_pc.png", "E-36  Percent-conifer slot: one held-out tile per fold (seed 0)",
        "Flat orange is real: the correction sits pinned at its -30 bound (see corrections.png). "
        "The twin's imagery is shuffled, so it learns only that constant.",
        delta_label="correction (points)"),
    "E-37": lambda: slot_tiles(
        SV2, [("r2:pred", "R2"), ("r3_cbh:pred", "R3 CBH"), ("r3_cbh:delta_cbh", "CBH correction"),
              ("r3_cbh_shuffled:delta_cbh", "twin's correction")], RESULTS / "p7_slots",
        "qual_E-37_cbh.png", "E-37  Crown-base-height slot: one held-out tile per fold (seed 0)",
        "The flat blue is real: the correction sits pinned at its +0.7 bound on most tiles (see "
        "corrections.png). The twin's imagery is shuffled, so it learns only that constant.",
        delta_max=0.7, delta_label="correction (log factor)"),
    "E-20": lambda: slot_tiles(
        SV2, [("r2:pred", "R2, 1-day codes"), ("r2_lag7:pred", "R2, 7-day codes"),
              ("r2_lag7:pred-r2:pred", "change in rank")], RESULTS / "p7_slots",
        "qual_E-20_staleness.png", "E-20  Staleness: fresh and week-old codes (seed 0)",
        "Last column: within-tile rank with 7-day codes minus 1-day codes.",
        delta_label="change in percentile"),
    "E-38": lambda: slot_tiles(
        SV3, [("r2_cwfis:pred", "R2, CWFIS fuel"), ("r3_curing_cwfis:pred", "R3 curing"),
              ("r3_curing_cwfis:delta_curing", "curing correction"),
              ("r3_curing_cwfis_shuffled:delta_curing", "twin's correction")],
        RESULTS / "p7c_slots_v3", "qual_E-38_curing.png",
        "E-38  Curing slot: one held-out tile per fold (seed 0)",
        "Both score columns use CWFIS fuel, so the blocks are that layer's coarse cells. Curing "
        "acts on O-1 grass only, and these tiles hold little of it.",
        delta_label="correction (points)"),
    "E-57": lambda: slot_tiles(
        SV3, [("r2:pred", "R2"), ("r3_pc_offset:pred", "R3 PC, offset"),
              ("r3_pc_offset:delta_pc", "PC: imagery part"),
              ("r3_pc_offset_shuffled:delta_pc", "twin's part")], RESULTS / "p7c_slots_v3",
        "qual_E-57_pc_offset.png", "E-57  PC correction with an imagery-free offset (seed 0)",
        "The PC columns show only the imagery part, without the learned offset.",
        delta_label="imagery part of the PC correction (points)"),
    "E-58": lambda: slot_tiles(
        SV3, [("r1:pred", "R1"), ("r2:pred", "R2 zero start"), ("r2_warm:pred", "R2 from R1"),
              ("r2_lr10:pred", "R2 10x rate")], RESULTS / "p7c_slots_v3",
        "qual_E-58_r2_gap.png", "E-58  Closing R2's gap to R1 (seed 0)",
        "All maps are our models."),
}

#: (experiment, folder, kind, files or reason). "none" states why nothing exists.
QUAL = [
    ("E-32", "p2_r0", "tiles", ["qual_E-32_r0.png", "tiles.png"]),
    ("E-33", "p2_r0", "tiles", ["qual_E-33_inventories.png"]),
    ("E-21", "p3_dated", "tiles", ["qual_E-21_inventory_age.png"]),
    ("E-49", "p3_dated", "tiles", ["qual_E-49_weather_date.png"]),
    ("E-50", "p3_dated", "patch map", ["qual_E-50_patch_map.png"]),
    ("E-51", "p3_dated", "patch map", ["qual_E-51_patch_map.png"]),
    ("E-52", "p3_dated", "patch map", ["qual_E-52_patch_map.png"]),
    ("E-53", "p3_dated", "patch map", ["qual_E-53_patch_map.png"]),
    ("E-43", "p3_dated", "none", "Control on date features alone: it uses no imagery and "
     "produces no per-pixel or per-location output to view."),
    ("E-54", "p4_prefire", "tiles", ["composite_tiles.png"]),
    ("E-34", "p7_slots", "tiles", ["tiles.png"]),
    ("E-36", "p7_slots", "tiles", ["qual_E-36_pc.png"]),
    ("E-37", "p7_slots", "tiles", ["qual_E-37_cbh.png"]),
    ("E-20", "p7_slots", "tiles", ["qual_E-20_staleness.png"]),
    ("E-55", "p7b_operational", "patch map", ["qual_E-55_patch_map.png"]),
    ("E-58", "p7c_slots_v3", "tiles", ["qual_E-58_r2_gap.png"]),
    ("E-57", "p7c_slots_v3", "tiles", ["qual_E-57_pc_offset.png"]),
    ("E-38", "p7c_slots_v3", "tiles", ["qual_E-38_curing.png"]),
    ("E-22", "p6a_ecology", "tiles", ["maps_pc.png", "maps_closure.png", "maps_height.png",
                                      "maps_family.png", "tiles.png"]),
    ("E-59", "p6a_ecology", "none", "NEEDS A JOB: the saved maps use one input mode (raw + "
     "indices). Maps per mode need cluster refits with predict_eco_maps.py --mode, and "
     "sweep_eco_maps.sh does not pass --mode yet."),
    ("E-62", "p6a_ecology", "tiles", ["maps_family.png"]),
    ("E-60", "p6c_snow", "station map", ["series_map.png", "series.png"]),
    ("E-61", "p6a_hs_v3", "line strips", [f"qual_E-61_{t[0]}.png" for t in HS_TARGETS]),
    ("E-62", "p6a_hs_v3", "line strips", [f"qual_E-62_{t[0]}.png" for t in HS_TARGETS]),
    ("E-22", "p6a_external_labels", "cell map and lidar tracks",
     ["qual_E-22_plots_map.png", "qual_lidar_tracks.png"]),
    ("E-61", "p6a_hs_v2_provisional", "line strips",
     [f"qual_E-61_{t[0]}.png" for t in HS_TARGETS]),
    ("E-62", "p6a_hs_v2_provisional", "line strips",
     [f"qual_E-62_{t[0]}.png" for t in HS_TARGETS]),
    ("E-61", "p6a_hs_provisional", "none", "Void run: its labels came from the wrong ground (A-40 "
     "amendment), so a map would only show that error."),
    ("E-62", "p6a_hs_provisional", "none", "Void run, as E-61 here."),
    ("E-56", "p6b_cohort", "tiles and patch map", ["qual_E-56_cohort_tiles.png",
                                                   "qual_E-56_patch_map.png"]),
    ("E-63", "p6e_out_of_time", "patch map", ["qual_E-63_patch_map.png"]),
    ("E-18", "p6d_startup", "patch map", ["qual_E-18_patch_map.png"]),
]


def write_index():
    lines = ["# Qualitative output per experiment", "",
             "Generated by `scripts/make_experiment_qual.py`; do not edit by hand.", "",
             "| Experiment | Name | Folder | View | Files or reason |", "|---|---|---|---|---|"]
    from safari_bands.experiments import by_id
    for eid, folder, kind, what in QUAL:
        cell = what if isinstance(what, str) else ", ".join(
            f"[{f}]({folder}/{f})" for f in what)
        lines.append(f"| {eid} | {by_id(eid).name} | [{folder}]({folder}/) | {kind} | {cell} |")
    INDEX.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def write_readmes():
    """One block in each pack's README, replaced on every run."""
    from safari_bands.experiments import by_id
    for folder in sorted({q[1] for q in QUAL}):
        p = RESULTS / folder / "README.md"
        if not p.exists():
            continue
        block = [START, "## Qualitative view per experiment", ""]
        for eid, f, kind, what in QUAL:
            if f == folder:
                cell = what if isinstance(what, str) else ", ".join(f"[{x}]({x})" for x in what)
                block.append(f"- **{eid}** {by_id(eid).name} ({kind}): {cell}")
        block.append(END)
        t = p.read_text(encoding="utf-8")
        body = "\n".join(block)
        if START in t:
            head, rest = t.split(START, 1)
            t = head + body + rest.split(END, 1)[1]
        else:
            t = t.rstrip() + "\n\n" + body + "\n"
        p.write_text(t, encoding="utf-8", newline="\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--only", nargs="*", default=None, help="experiment ids (default: all)")
    ap.add_argument("--hs-run", type=Path, default=HS_RUN)
    ap.add_argument("--hs-pack", type=Path, default=HS_PACK)
    ap.add_argument("--hs-out", type=Path, default=HS_OUT)
    args = ap.parse_args(argv)
    want = set(args.only) if args.only else {*BUILD, *HS_SETS}
    for eid in sorted(want):
        if eid in HS_SETS:
            print(eid, hs_strips(args.hs_run.resolve(), args.hs_pack.resolve(),
                                 args.hs_out.resolve(), eid), flush=True)
        else:
            BUILD[eid]()
            print(eid, "done", flush=True)
    if args.only is None:
        write_index()
        write_readmes()
    return 0


if __name__ == "__main__":
    sys.exit(main())
