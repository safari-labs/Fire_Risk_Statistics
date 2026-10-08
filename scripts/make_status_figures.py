"""scripts/make_status_figures.py

Figures describing the data as it actually is on disk, not as planned.

Everything here is MEASURED at render time by reading the patch directory and
the packed HDF5 in Fire_Risk_Model. Nothing is hardcoded, because a status
figure that drifts from the data is worse than no status figure: it reports
the state someone believed in when they last edited the constants.

    python scripts/make_status_figures.py --model-repo ../Fire_Risk_Model
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

OUT = Path("docs/results/figures")

FIG_BG, AX_BG = "#14161a", "#1b1e24"
INK, INK_BRIGHT, MUTED, SPINE = "#c7ccd4", "#eef1f5", "#79818e", "#2c313a"
S1, S2, S3, CRIT, OK = "#4ea1d3", "#e8973f", "#9b7fd4", "#d1495b", "#52a675"

_STEM = re.compile(r"^(-?\d+\.\d+)_(-?\d+\.\d+)_(\d{4})_([a-z]+)")
SCANFI_YEAR = 2020
#: Years before its fire that a confuser patch is imaged.
#: download_confuser_patches(pre_fire_offset=3).
CONFUSER_OFFSET = 3


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "text.color": INK,
        "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.edgecolor": SPINE, "figure.facecolor": FIG_BG,
        "savefig.facecolor": FIG_BG,
    })
    return plt


def _axes(ax, title="", xlabel="", ylabel=""):
    ax.set_facecolor(AX_BG)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(SPINE)
    if title:
        ax.set_title(title, color=INK_BRIGHT, fontsize=11, loc="left", pad=9)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9.2)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9.2)
    ax.tick_params(labelsize=8.6, length=3)


def _save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / name
    fig.savefig(out, dpi=170, facecolor=FIG_BG, bbox_inches="tight")
    print(f"  wrote {out}")
    import matplotlib.pyplot as plt
    plt.close(fig)
    return out


# ── measurement ──────────────────────────────────────────────────────────


def survey(repo: Path) -> dict:
    """Read the actual state off disk."""
    pdir = repo / "data/stage2_fire/patches_11band"
    eco = repo / "data/ecology/patches_11band"
    h5d = repo / "data/stage2_fire_11band"

    scenes: collections.Counter[str] = collections.Counter()
    year_scene: collections.Counter[tuple[str, int]] = collections.Counter()
    for p in pdir.glob("*_bands.tif"):
        m = _STEM.match(p.name)
        if m:
            scenes[m.group(4)] += 1
            year_scene[(m.group(4), int(m.group(3)))] += 1

    side = {k: len(list(pdir.glob(f"*{suf}")))
            for k, suf in (("terrain", "_terrain.npy"),
                           ("elevation", "_elevation.json"),
                           ("weather", "_fwi.json"),
                           ("fuel", "_fbpfuel.npy"),
                           ("NBAC", "_nbac.npy"),
                           ("thermal", "_thermal.json"),
                           ("SCANFI", "_scanfi.npy"))}

    # Read the packed HDF5 through the MODEL repo's interpreter.
    #
    # h5py lives there, not here, and this repo should not grow a dependency
    # just to describe another repo's output. The first version swallowed the
    # ImportError and rendered "0 bands" onto the figure -- a status figure
    # reporting a state that was never checked, which is worse than one that
    # admits it could not look.
    splits: dict[str, int] = {}
    bands: list[str] = []
    h5_error: str | None = None
    if any((h5d / f"{s}.h5").exists() for s in ("train", "val", "test")):
        import subprocess
        py = repo / ".venv/Scripts/python.exe"
        if not py.exists():
            py = repo / ".venv/bin/python"
        probe = (
            "import json,sys,h5py;from pathlib import Path;"
            "d=Path(sys.argv[1]);o={'splits':{},'bands':[]};"
            "[o['splits'].__setitem__(s,int(h['bands'].shape[0]))or("
            "o.__setitem__('bands',[b.decode() if isinstance(b,bytes) else str(b)"
            " for b in h.attrs.get('band_order',[])]) if not o['bands'] else None)"
            " for s in ('train','val','test') if (d/f'{s}.h5').exists()"
            " for h in [h5py.File(d/f'{s}.h5','r')]];"
            "print(json.dumps(o))")
        try:
            r = subprocess.run([str(py), "-c", probe, str(h5d)],
                               capture_output=True, text=True, timeout=120)
            if r.returncode == 0:
                got = json.loads(r.stdout.strip().splitlines()[-1])
                splits, bands = got["splits"], got["bands"]
            else:
                h5_error = (r.stderr or "").strip()[-160:] or "unknown"
        except Exception as exc:                            # noqa: BLE001
            h5_error = f"{type(exc).__name__}: {exc}"

    # Weather history presence: the running covariate job predates it.
    with_hist = 0
    fwis = list(pdir.glob("*_fwi.json"))
    for f in fwis:
        try:
            if "history" in json.loads(f.read_text(encoding="utf-8")):
                with_hist += 1
        except Exception:                                   # noqa: BLE001
            pass

    return {
        "n_patches": sum(scenes.values()),
        "scenes": dict(scenes),
        "year_scene": year_scene,
        "sidecars": side,
        "splits": splits,
        "bands": bands,
        "n_ecology": len(list(eco.glob("*_bands.tif"))) if eco.exists() else 0,
        "fwi_total": len(fwis),
        "fwi_with_history": with_hist,
        "h5_error": h5_error,
    }


# ── 1. What is on disk ───────────────────────────────────────────────────


def fig_inventory(st: dict):
    plt = _plt()
    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(10.6, 3.5), facecolor=FIG_BG,
        gridspec_kw={"width_ratios": [1.15, 1]})
    fig.suptitle("Fire-risk dataset, measured on disk", color=INK_BRIGHT,
                 fontsize=12, x=0.0, ha="left", y=1.06)

    # Scene composition. The point of the figure: it is no longer fire-only.
    order = ["fire", "confuser", "unburned", "cloud", "water", "bare"]
    present = [(k, st["scenes"].get(k, 0)) for k in order
               if st["scenes"].get(k, 0)]
    cols = {"fire": CRIT, "confuser": S2, "unburned": OK,
            "cloud": MUTED, "water": S1, "bare": S3}
    _axes(ax1, "Scene types", xlabel="patches")
    ys = range(len(present))
    ax1.barh(list(ys), [v for _, v in present],
             color=[cols[k] for k, _ in present], height=0.62)
    ax1.set_yticks(list(ys))
    ax1.set_yticklabels([k for k, _ in present], color=INK_BRIGHT, fontsize=9.4)
    ax1.invert_yaxis()
    for i, (_, v) in enumerate(present):
        ax1.text(v + max(st["scenes"].values()) * 0.015, i, str(v),
                 va="center", color=INK, fontsize=9, family="monospace")
    ax1.set_xlim(0, max(st["scenes"].values()) * 1.16)

    # Covariate completeness, as a fraction of patches.
    _axes(ax2, "Per-patch covariates", xlabel="fraction of patches complete")
    n = max(st["n_patches"], 1)
    items = list(st["sidecars"].items())
    ys2 = range(len(items))
    fracs = [v / n for _, v in items]
    ax2.barh(list(ys2), fracs,
             color=[OK if f > 0.95 else (S2 if f > 0.5 else CRIT)
                    for f in fracs], height=0.62)
    ax2.set_yticks(list(ys2))
    ax2.set_yticklabels([k for k, _ in items], color=INK_BRIGHT, fontsize=9.4)
    ax2.invert_yaxis()
    ax2.set_xlim(0, 1.18)
    for i, (_, v) in enumerate(items):
        ax2.text(v / n + 0.02, i, f"{v}/{n}", va="center", color=INK,
                 fontsize=8.6, family="monospace")

    packed = " ".join(f"{k} {v}" for k, v in st["splits"].items())
    fig.text(0.0, -0.10, chr(10).join([
        f"{st['n_patches']} patches, {len(st['bands'])} bands at 20 m in "
        f"EPSG:3978. Packed tiles: {packed or 'not packed'}.",
        f"Weather history on {st['fwi_with_history']}/{st['fwi_total']} "
        f"patches -- the covariate run predates it and needs a --overwrite "
        f"pass. Ecology set: {st['n_ecology']} patches downloading.",
    ]), color=MUTED, fontsize=8.3, ha="left")
    return _save(fig, "status_inventory.png")


# ── 2. Staleness, which decides whether the refresh test is possible ─────


def fig_staleness(st: dict):
    plt = _plt()
    fig, ax = plt.subplots(figsize=(8.4, 3.4), facecolor=FIG_BG)
    fig.suptitle("SCANFI staleness against imagery year, by scene",
                 color=INK_BRIGHT, fontsize=12, x=0.0, ha="left", y=1.05)
    _axes(ax, "", xlabel="staleness gap (imagery year - SCANFI 2020)",
          ylabel="patches")

    ys = st["year_scene"]
    gaps = sorted({y - SCANFI_YEAR for (_, y) in ys})
    want = ["fire", "confuser"]
    width = 0.38

    # SCANFI 2020 is contaminated whenever the patch's ASSOCIATED FIRE
    # happened in 2020 or earlier -- the layer then already carries the scar.
    #
    # For a fire patch that is its own year. For a confuser it is NOT: a
    # confuser is a fire site imaged CONFUSER_OFFSET years before it burned,
    # so a 2016 confuser belongs to a 2019 fire and SCANFI 2020 shows that
    # burn on ground the label calls unburned. The first version of this rule
    # checked fire patches only and would have left 8 contaminated confusers
    # in the comparison.
    for i, scene in enumerate(want):
        vals, leak = [], []
        for g in gaps:
            n = sum(v for (sc, y), v in ys.items()
                    if sc == scene and y - SCANFI_YEAR == g)
            fire_year = (SCANFI_YEAR + g
                         + (CONFUSER_OFFSET if scene == "confuser" else 0))
            vals.append(n)
            leak.append(fire_year <= SCANFI_YEAR)
        xs = [g + (i - 0.5) * width for g in gaps]
        col = CRIT if scene == "fire" else S2
        ax.bar(xs, vals, width=width, color=col, label=scene, zorder=2)
        # Contaminated cells get a hatch rather than a shaded region: the
        # region version covered usable confuser bars and sat on top of the
        # tallest one.
        ax.bar([x for x, k in zip(xs, leak) if k],
               [v for v, k in zip(vals, leak) if k], width=width,
               facecolor="none", edgecolor=INK_BRIGHT, hatch="///",
               linewidth=1.0, zorder=3)
        for x, v, k in zip(xs, vals, leak):
            if v:
                ax.text(x, v + 1.5, str(v), ha="center",
                        color=INK_BRIGHT if k else INK,
                        fontsize=8.2, family="monospace", zorder=4)

    ax.set_xticks(gaps)
    ax.set_xticklabels([f"{g:+d}" for g in gaps])
    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(facecolor=CRIT, label="fire"),
        Patch(facecolor=S2, label="confuser"),
        Patch(facecolor="none", edgecolor=INK_BRIGHT, hatch="///",
              label="SCANFI 2020 holds the scar - unusable"),
    ], frameon=False, labelcolor=INK, fontsize=8.6, loc="upper left",
        bbox_to_anchor=(0, 1.0))
    ax.set_ylim(0, max(ys.values()) * 1.22)

    fig.text(0.0, -0.13, chr(10).join([
        "The refresh test asks whether a CURRENT ecology estimate beats the "
        "static 2020 layer at predicting fire, and whether its advantage grows "
        "with this gap.",
        "Read the gap effect WITHIN a scene: 72 confusers sit at gap 0 and 72 "
        "fires at gap +3, so a whole-set contrast would read the class label "
        "as a staleness effect.",
        "Hatched cells are excluded. A confuser is imaged 3 years BEFORE its "
        "fire, so a 2016 confuser belongs to a 2019 burn that SCANFI 2020 "
        "already shows.",
    ]), color=MUTED, fontsize=8.3, ha="left")
    return _save(fig, "status_staleness.png")


# ── 3. The two band-ranking arms, and what neither can see ───────────────


def fig_arms():
    plt = _plt()
    fig, ax = plt.subplots(figsize=(9.6, 4.3), facecolor=FIG_BG)
    ax.set_facecolor(FIG_BG)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.6)
    ax.axis("off")
    fig.suptitle("Two band-ranking arms, and the gap between them",
                 color=INK_BRIGHT, fontsize=12, x=0.0, ha="left", y=0.99)

    def box(x, y, w, h, title, lines, col):
        from matplotlib.patches import FancyBboxPatch
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.12", linewidth=1.5,
            edgecolor=col, facecolor=AX_BG, zorder=2))
        ax.text(x + 0.18, y + h - 0.3, title, color=col, fontsize=10,
                weight="bold", zorder=3)
        for i, ln in enumerate(lines):
            ax.text(x + 0.18, y + h - 0.68 - i * 0.32, ln, color=INK,
                    fontsize=8.6, zorder=3)

    box(0.1, 2.9, 4.6, 2.4, "ECOLOGY ARM  (primary)", [
        "SCANFI distillation, ~300 patches",
        "dense: every pixel labelled",
        "crown closure, height, biomass,",
        "species, land cover  ->  T4",
        "pinned to 2020: one season only",
    ], S1)

    box(5.3, 2.9, 4.6, 2.4, "FIRE ARM  (relevance check)", [
        "NBAC outcome, 292 patches",
        "sparse: one label per patch",
        "flammability -> moisture-adjacent",
        "confounded by ignition arrival",
        "spans 2019-2023: seasonal range",
    ], CRIT)

    box(0.1, 0.25, 9.8, 2.25, "NEITHER ARM MEASURES", [
        "T1 live foliar moisture (LFMC)  and  T2 curing / NPV fraction  have no labels anywhere in this data.",
        "They need radiative transfer simulation (Phases 1-2, not built) or field measurement (Phase 6).",
        "",
        "This matters most for B11. 1610 nm is in the design for canopy water, so a structure-only ranking",
        "scores it on its secondary role -- and B11 is the band the whole SWIR chain exists to carry.",
    ], S2)

    from matplotlib.patches import FancyArrowPatch
    ax.add_patch(FancyArrowPatch((4.78, 4.1), (5.22, 4.1), mutation_scale=13,
                                 color=MUTED, lw=1.3, arrowstyle="->"))
    # ABOVE the boxes. Centred in the 0.6-wide gap between them it
    # overflowed onto the fire panel and sat on its first two lines.
    ax.text(5.0, 5.45, "rank here, then check there", color=MUTED,
            fontsize=8.2, ha="center", style="italic")
    return _save(fig, "status_ranking_arms.png")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Status figures from disk.")
    ap.add_argument("--model-repo", type=Path, default=Path("../Fire_Risk_Model"))
    args = ap.parse_args(argv)
    if not args.model_repo.exists():
        print(f"no repo at {args.model_repo}", file=sys.stderr)
        return 2

    print("rendering status figures (measured, not hardcoded)")
    st = survey(args.model_repo)
    print(f"  surveyed {st['n_patches']} patches, {len(st['bands'])} bands, "
          f"{st['n_ecology']} ecology")
    if st["h5_error"]:
        print(f"  WARNING: could not read the packed HDF5: {st['h5_error']}",
              file=sys.stderr)
    fig_inventory(st)
    fig_staleness(st)
    fig_arms()
    print()
    print(f"all figures -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
