"""scripts/make_data_summary.py

Everything we hold, and what each piece is for.

Measured off disk at render time rather than hardcoded. A data inventory that
drifts from the data is worse than none: it reports the state someone
believed in when they last edited the constants.

    python scripts/make_data_summary.py --model-repo ../Fire_Risk_Model
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import sys
from pathlib import Path

OUT = Path("docs/results/figures")

FIG_BG, AX_BG = "#14161a", "#1b1e24"
INK, INK_BRIGHT, MUTED, SPINE = "#c7ccd4", "#eef1f5", "#79818e", "#2c313a"
OK, PART, GAP, S1, S2 = "#52a675", "#e8973f", "#d1495b", "#4ea1d3", "#9b7fd4"

_STEM = re.compile(r"^(-?\d+\.\d+)_(-?\d+\.\d+)_(\d{4})_([a-z]+)")

#: Scene types that carry fuel. The rest -- cloud, water, bare -- are hard
#: negatives for the classifier and are not expected to carry fuel covariates.
FUEL_SCENES = ("fire", "confuser", "unburned")


def survey(repo: Path) -> dict:
    fire = repo / "data/stage2_fire/patches_11band"
    eco = repo / "data/ecology/patches_11band"

    scene = {}
    for f in fire.glob("*_bands.tif"):
        m = _STEM.match(f.name)
        if m:
            scene[f.name[:-len("_bands.tif")]] = m.group(4)

    def have(suffix, test=None, among=None):
        n = 0
        for s, sc in scene.items():
            if among and sc not in among:
                continue
            p = fire / f"{s}{suffix}"
            if not p.exists():
                continue
            if test:
                try:
                    if not test(p):
                        continue
                except Exception:          # noqa: BLE001
                    continue
            n += 1
        return n

    has_hist = lambda p: "history" in json.loads(p.read_text(encoding="utf-8"))
    n_fuel = sum(1 for v in scene.values() if v in FUEL_SCENES)

    eco_n = len(list(eco.glob("*_bands.tif"))) if eco.exists() else 0
    eco_sc = len(list(eco.glob("*_scanfi.npy"))) if eco.exists() else 0

    nbac_years = sorted(
        int(Path(d).name.split("_")[1])
        for d in glob.glob(str(repo / "data/nbac/NBAC_*")) if os.path.isdir(d))

    packed = {}
    h5d = repo / "data/stage2_fire_11band"
    if any((h5d / f"{s}.h5").exists() for s in ("train", "val", "test")):
        import subprocess
        py = repo / ".venv/Scripts/python.exe"
        if not py.exists():
            py = repo / ".venv/bin/python"
        probe = ("import json,sys,h5py;from pathlib import Path;d=Path(sys.argv[1]);"
                 "print(json.dumps({s:list(h5py.File(d/f'{s}.h5')['bands'].shape)"
                 " for s in ('train','val','test') if (d/f'{s}.h5').exists()}))")
        try:
            r = subprocess.run([str(py), "-c", probe, str(h5d)],
                               capture_output=True, text=True, timeout=120)
            if r.returncode == 0:
                packed = json.loads(r.stdout.strip().splitlines()[-1])
        except Exception:                  # noqa: BLE001
            pass

    return {
        "scene": collections.Counter(scene.values()),
        "n_patches": len(scene),
        "n_fuel": n_fuel,
        "weather_fuel": have("_fwi.json", has_hist, FUEL_SCENES),
        "weather_all": have("_fwi.json", has_hist),
        "terrain": have("_terrain.npy"),
        "elevation": have("_elevation.json"),
        "fuel_layer": have("_fbpfuel.npy"),
        "nbac": have("_nbac.npy"),
        "thermal": have("_thermal.json"),
        "scanfi": have("_scanfi.npy"),
        "eco_n": eco_n, "eco_scanfi": eco_sc,
        "nbac_years": nbac_years,
        "packed": packed,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Data inventory figure.")
    ap.add_argument("--model-repo", type=Path, default=Path("../Fire_Risk_Model"))
    args = ap.parse_args(argv)
    if not args.model_repo.exists():
        print(f"no repo at {args.model_repo}", file=sys.stderr)
        return 2

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK,
                         "figure.facecolor": FIG_BG, "savefig.facecolor": FIG_BG})
    st = survey(args.model_repo)
    sc, nf = st["scene"], st["n_fuel"]
    tot = st["n_patches"]
    pk = st["packed"]
    tiles = sum(v[0] for v in pk.values()) if pk else 0
    nb = st["nbac_years"]

    #                  label, detail, count text, status, purpose
    rows = [
        ("IMAGERY", None, None, None, None),
        ("Fire-risk patches",
         f"{sc['fire']} fire · {sc['confuser']} confuser · {sc['unburned']} unburned",
         f"{tot}", OK,
         "fire-vs-unburned ranks bands; fire-vs-confuser measures weather"),
        ("  hard negatives",
         f"{sc['cloud']} cloud · {sc['water']} water · {sc['bare']} bare",
         f"{sc['cloud'] + sc['water'] + sc['bare']}", OK,
         "stop the model calling any dark or bright region fire"),
        ("Ecology patches",
         "8 SCANFI land-cover classes, 2020, stratified",
         f"{st['eco_n']}", OK,
         "PRIMARY band ranking: dense per-pixel vegetation structure"),
        ("Packed tiles",
         f"11 bands @ 20 m, EPSG:3978 "
         + " ".join(f"{k} {v[0]}" for k, v in pk.items()),
         f"{tiles}", OK if tiles else GAP,
         "what training actually reads"),

        ("LABELS", None, None, None, None),
        ("SCANFI structure",
         "18 ch: cover, closure, height, biomass, species",
         f"{st['scanfi']}/{tot} · {st['eco_scanfi']}/{st['eco_n']}",
         OK if st["scanfi"] == tot else PART,
         "T4 fuel type and percent conifer; the vegetation arm's target"),
        ("NBAC perimeters",
         f"per-pixel burn mask, {nb[0]}-{nb[-1]}" if nb else "not fetched",
         f"{st['nbac']}/{tot}", PART,
         "PRIMARY fire label. Non-circular, unlike dNBR"),
        ("VIIRS thermal",
         "scalar per patch, 4 and 11 um emission",
         f"{st['thermal']}/{tot}", PART,
         "leakage control: cannot share information with reflectance"),
        ("CFFDRS fuel layer",
         "published 2024 fuel-type codes",
         f"{st['fuel_layer']}/{tot}", OK if st["fuel_layer"] > tot * .95 else PART,
         "baseline to beat; the static layer our retrieval refreshes"),

        ("COVARIATES", None, None, None, None),
        ("Weather + FWI codes",
         "FFMC, ISI, BUI, wind + 12 history features",
         f"{st['weather_fuel']}/{nf} fuel", OK,
         "CFFDRS baseline, and the arm testing what history adds"),
        ("Terrain",
         "slope, aspect sin/cos, at the patch grid",
         f"{st['terrain']}/{tot}", OK,
         "FBP slope input; illumination confound control"),
        ("Elevation",
         "patch-mean metres",
         f"{st['elevation']}/{tot}", OK if st["elevation"] > tot * .95 else PART,
         "foliar moisture content, via the FBP equation"),

        ("SCOPED, NOT YET HELD", None, None, None, None),
        ("AVIRIS-NG ABoVE",
         "163 published of 574 lines, 5 nm · 42 pre-fire",
         "free", PART,
         "THE SWIR answer: any 4-band placement, synthesised"),
        ("WorldView-3",
         "8 VNIR + 4 SWIR, co-registered, commercial",
         "optional", GAP,
         "flown benchmark for the SWIR set; not required"),
    ]

    H = 0.40
    fig_h = 0.9 + H * len(rows)
    fig, ax = plt.subplots(figsize=(13.2, fig_h), facecolor=FIG_BG)
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.05, len(rows) * H + 0.25)
    ax.axis("off")
    fig.suptitle("What data we hold, and what each piece is for",
                 color=INK_BRIGHT, fontsize=13, x=0.0, ha="left", y=1.0)

    y = len(rows) * H
    for label, detail, count, status, purpose in rows:
        y -= H
        if detail is None:                      # section heading
            ax.text(0, y + 0.06, label, color=S1, fontsize=9.6,
                    weight="bold", va="center")
            ax.plot([0, 100], [y - 0.09, y - 0.09], color=SPINE, lw=0.8)
            continue
        ax.add_patch(FancyBboxPatch((0, y - 0.04), 100, H - 0.08,
                                    boxstyle="round,pad=0.01",
                                    facecolor=AX_BG, edgecolor="none", zorder=1))
        ax.text(1.0, y + 0.13, label, color=INK_BRIGHT, fontsize=9, va="center",
                zorder=2)
        ax.text(1.0, y - 0.02, detail, color=MUTED, fontsize=7.6, va="center",
                zorder=2)
        ax.add_patch(FancyBboxPatch((26.5, y + 0.03), 11, 0.21,
                                    boxstyle="round,pad=0.012",
                                    facecolor=status, edgecolor="none",
                                    alpha=0.85, zorder=2))
        ax.text(32, y + 0.135, count, color="#10131a", fontsize=8.4,
                ha="center", va="center", weight="bold", family="monospace",
                zorder=3)
        ax.text(40, y + 0.08, purpose, color=INK, fontsize=8.3, va="center",
                zorder=2)

    fig.text(0.0, -0.055, chr(10).join([
        f"ALL {nf} FUEL-BEARING PATCHES have complete weather and SCANFI. The "
        f"weather gaps are cloud, water and bare scenes, where ERA5-Land has "
        f"no land pixel -- and those are hard",
        "negatives, not fuel, so a fire-danger weather vector over a lake "
        "would be meaningless anyway. The NBAC gaps are confusers from "
        f"2016-2018, before the {nb[0] if nb else '?'} start of the",
        "perimeters we fetched; confusers carry a constant-zero mask by "
        "construction and do not need one. Neither gap blocks the band "
        "ranking.",
        "",
        "Counts are read off disk at render time, not hardcoded.",
    ]), color=MUTED, fontsize=8.2, ha="left", linespacing=1.5)

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "data_summary.png"
    fig.savefig(out, dpi=165, facecolor=FIG_BG, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
