"""scripts/check_forward_reference.py

The reference check A-47 owes (brief Phase 1, "done when: spectra reproduce a
reference implementation within tolerance"). The same cases go through our
forward model (Python `prosail` 2.0.5: PROSPECT-D + 4SAIL) and through Feret's
R packages `prospect` and `prosail` (scripts/r/prosail_reference.R):

  code:         R with OUR PROSPECT-D coefficients and soil spectra, and its
                leaf-angle classes set to ours (18 x 5 degrees). Any difference
                is an implementation difference. Tolerance: 1e-4 reflectance.
  coefficients: R's own PROSPECT coefficients against ours, on the leaf.
  leaf angles:  R as released, whose campbell() keeps the original 4SAIL's 13
                classes (10-degree steps to 80, then 2-degree). Reported, not a
                pass/fail: per band, against the atmospheric-residual sigma,
                and in SWIR as an equivalent LFMC shift through each case's own
                d(rho)/d(LFMC).

    python scripts/check_forward_reference.py                 # 64 cases per group
    python scripts/check_forward_reference.py --per-group 8   # quick

Writes docs/results/p6f_reference/ (T_reference.csv, reference.png,
summary.json) and runs/<stamp>_forward_reference/.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

from safari_bands import forward as F
from safari_bands.config.loader import load_band_set, load_priors, project_root
from safari_bands.provenance import start_run

TOL = 1e-4
SEED = 20261105
RSCRIPT = Path("C:/Program Files/R/R-4.6.1/bin/Rscript.exe")
PARAMS = ("n", "cab", "car", "cbrown", "ant", "cw", "cm", "lai", "ala", "hspot",
          "tts", "tto", "psi", "rsoil", "psoil")
DLFMC = 10.0                     # finite step for the LFMC sensitivity, %
SWIR = ("B11", "B12")

FIG_BG, AX_BG = "#0f1117", "#1a1d27"
SPINE, INK, INK_BRIGHT, MUTED = "#333344", "#cccccc", "#eeeeee", "#8b8b9a"
BLUE, ORANGE = "#3987e5", "#d95926"


def _rscript() -> str:
    found = shutil.which("Rscript")
    if found:
        return found
    if RSCRIPT.exists():
        return str(RSCRIPT)
    raise SystemExit("Rscript not found; install R and jbferet/prospect, jbferet/prosail")


def cases(per_group: int) -> tuple[dict[str, np.ndarray], list[str]]:
    pr = load_priors("lfmc_v1")
    tabs, groups = [], []
    for i, g in enumerate(pr.groups):
        tabs.append(F.sample(pr, g, n=per_group, seed=SEED + i))
        groups += [g] * per_group
    return {k: np.concatenate([t[k] for t in tabs]) for k in tabs[0]}, groups


def ours(p: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    import prosail
    model = F.Prosail()
    n = len(p["lfmc"])
    out = {k: np.empty((n, F.WAVELENGTHS.size)) for k in ("leaf_R", "leaf_T", "canopy", "wet")}
    for i in range(n):
        row = {c: float(p[c][i]) for c in F.COLUMNS}
        _, r, t = prosail.run_prospect(row["n"], row["cab"], row["car"], row["cbrown"],
                                       float(p["cw"][i]), row["cm"], ant=row["ant"],
                                       prospect_version="D")
        out["leaf_R"][i], out["leaf_T"][i] = r, t
        out["canopy"][i] = model.reflectance(row)
        out["wet"][i] = model.reflectance({**row, "lfmc": row["lfmc"] + DLFMC})
    return out


def reference(p: dict[str, np.ndarray], work: Path) -> dict[str, dict[str, np.ndarray]]:
    import pandas as pd
    import prosail
    lib = prosail.spectral_lib
    pd.DataFrame({k: p[k] for k in PARAMS}).to_csv(work / "params.csv", index=False)
    d = lib.prospectd
    pd.DataFrame({"lambda": F.WAVELENGTHS, "nr": d.nr, "kab": d.kab, "kcar": d.kcar,
                  "kant": d.kant, "kbrown": d.kbrown, "kw": d.kw, "km": d.km}
                 ).to_csv(work / "coeffs.csv", index=False)
    pd.DataFrame({"lambda": F.WAVELENGTHS, "soil1": lib.soil.rsoil1,
                  "soil2": lib.soil.rsoil2}).to_csv(work / "soil.csv", index=False)
    script = project_root() / "scripts" / "r" / "prosail_reference.R"
    proc = subprocess.run([_rscript(), str(script), str(work)], capture_output=True, text=True)
    if proc.returncode:
        raise SystemExit(f"R reference failed:\n{proc.stdout}\n{proc.stderr}")
    out = {}
    for tag in ("ours", "r", "ours18"):
        out[tag] = {k: pd.read_csv(work / f"{k}_{tag}.csv").to_numpy(float)
                    for k in ("leaf_R", "leaf_T", "canopy")}
    out["versions"] = (work / "versions.txt").read_text().splitlines()
    return out


def figure(py, ref, band_rows, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.8), facecolor=FIG_BG)
    for ax in axs:
        ax.set_facecolor(AX_BG)
        for s in ax.spines.values():
            s.set_color(SPINE)
        ax.tick_params(colors=INK, labelsize=8.5)
        ax.grid(True, color=SPINE, lw=0.6, alpha=0.6)
        ax.set_axisbelow(True)
    ax = axs[0]
    for tag, col, lab in (("ours18", BLUE, "same leaf-angle classes: code difference"),
                          ("ours", ORANGE, "reference 13 leaf-angle classes vs our 18")):
        d = np.abs(ref[tag]["canopy"] - py["canopy"])
        ax.plot(F.WAVELENGTHS, np.maximum(d.max(0), 1e-16), color=col, lw=1.4, label=lab)
    ax.axhline(TOL, color=MUTED, lw=1, ls="--")
    ax.text(2480, TOL, f"tolerance {TOL:g}", color=MUTED, fontsize=8, ha="right", va="bottom")
    ax.set_yscale("log")
    ax.set_xlabel("wavelength (nm)", color=INK, fontsize=9)
    ax.set_ylabel("largest |R - Python| over cases", color=INK, fontsize=9)
    ax.set_title("Canopy reflectance: Python prosail vs Feret's R packages", color=INK_BRIGHT,
                 fontsize=10.5, loc="left")
    leg = ax.legend(frameon=False, fontsize=8.5, loc="center right")
    for t in leg.get_texts():
        t.set_color(INK)
    ax = axs[1]
    x = np.arange(len(band_rows))
    m = np.array([r["lidf_mean"] for r in band_rows])
    lo = np.array([r["lidf_p05"] for r in band_rows])
    hi = np.array([r["lidf_p95"] for r in band_rows])
    sig = np.array([r["atm_sigma_mean"] for r in band_rows])
    ax.bar(x, m, color=ORANGE, width=0.6, label="13 minus 18 classes (mean, 5-95 %)")
    ax.errorbar(x, m, yerr=[m - lo, hi - m], fmt="none", ecolor=INK, lw=1, capsize=3)
    ax.plot(x, sig, ls="none", marker="_", ms=16, mew=2, color=MUTED,
            label="atmospheric-residual sigma (mean)")
    ax.axhline(0, color=MUTED, lw=1)
    ax.set_xticks(x, [r["band"] for r in band_rows])
    ax.set_ylabel("band reflectance", color=INK, fontsize=9)
    ax.set_title("Leaf-angle discretisation, per Sentinel-2 band", color=INK_BRIGHT,
                 fontsize=10.5, loc="left")
    leg = ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    for t in leg.get_texts():
        t.set_color(INK)
    fig.text(0.01, -0.02,
             "Cases: Sobol draws from the lfmc_v1 priors, conifer and deciduous. Python: prosail "
             "2.0.5. R: jbferet prospect 2.0.1 and prosail 3.2.0 (4SAIL). Bidirectional "
             "reflectance factor. The leaf (PROSPECT-D) agrees to 1e-14 and is not drawn. "
             "Reconstructed (ours).",
             color=MUTED, fontsize=8.5, ha="left", va="top", wrap=True)
    fig.tight_layout()
    fig.savefig(out, dpi=150, facecolor=FIG_BG, bbox_inches="tight")
    plt.close(fig)


def qual_spectra(p, groups, py, ref, out: Path) -> None:
    """Qualitative view: three conifer cases (low, middle, high LFMC), our canopy
    spectrum over the reference's, with their difference."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    con = [i for i, g in enumerate(groups) if g == "conifer"]
    order = sorted(con, key=lambda i: p["lfmc"][i])
    pick = [order[0], order[len(order) // 2], order[-1]]
    fig, axs = plt.subplots(2, 3, figsize=(13, 5.6), facecolor=FIG_BG, sharex=True,
                            gridspec_kw={"height_ratios": [2.2, 1], "hspace": 0.08})
    for j, i in enumerate(pick):
        a, d = axs[0, j], axs[1, j]
        for ax in (a, d):
            ax.set_facecolor(AX_BG)
            for sp in ax.spines.values():
                sp.set_color(SPINE)
            ax.tick_params(colors=INK, labelsize=8)
            ax.grid(True, color=SPINE, lw=0.6, alpha=0.6)
        a.plot(F.WAVELENGTHS, ref["ours"]["canopy"][i], color=ORANGE, lw=3, alpha=0.7,
               label="reference (R, 13 leaf-angle classes)")
        a.plot(F.WAVELENGTHS, py["canopy"][i], color=BLUE, lw=1.2, label="ours (Python, 18)")
        a.set_title(f"conifer, LFMC {p['lfmc'][i]:.0f} %, LAI {p['lai'][i]:.1f}, "
                    f"leaf angle {p['ala'][i]:.0f} deg", color=INK_BRIGHT, fontsize=9.5,
                    loc="left")
        d.plot(F.WAVELENGTHS, ref["ours"]["canopy"][i] - py["canopy"][i], color=ORANGE, lw=1)
        d.plot(F.WAVELENGTHS, ref["ours18"]["canopy"][i] - py["canopy"][i], color=BLUE, lw=1)
        d.axhline(0, color=MUTED, lw=0.8)
        d.set_xlabel("wavelength (nm)", color=INK, fontsize=9)
        if j == 0:
            a.set_ylabel("canopy reflectance", color=INK, fontsize=9)
            d.set_ylabel("R minus ours", color=INK, fontsize=9)
            leg = a.legend(frameon=False, fontsize=8, loc="center right")
            for t in leg.get_texts():
                t.set_color(INK)
    fig.suptitle("P6f-v2  Our forward model over the reference, three conifer cases",
                 color=INK_BRIGHT, x=0.01, y=0.99, ha="left", fontsize=12)
    fig.text(0.01, -0.01, "Bottom: orange is the reference as released (13 leaf-angle classes) "
             "minus ours; blue is the reference with our 18 classes minus ours, flat at 1e-15. "
             "Cases: the lowest, middle and highest LFMC of the conifer draws. Reconstructed "
             "(ours).", color=MUTED, fontsize=8.5, ha="left", va="top", wrap=True)
    fig.savefig(out, dpi=150, facecolor=FIG_BG, bbox_inches="tight")
    plt.close(fig)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--per-group", type=int, default=64)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)
    out = args.out or project_root() / "docs" / "results" / "p6f_reference"
    out.mkdir(parents=True, exist_ok=True)
    run = start_run("forward_reference", seed=SEED, per_group=args.per_group)

    p, groups = cases(args.per_group)
    py = ours(p)
    with tempfile.TemporaryDirectory() as tmp:
        ref = reference(p, Path(tmp))

    pr = load_priors("lfmc_v1")
    bs = load_band_set(pr.band_set)
    names = list(pr.retrieval_bands)
    _, b_py = F.band_reflectance(py["canopy"], bs, names)
    _, b_wet = F.band_reflectance(py["wet"], bs, names)
    _, b_code = F.band_reflectance(ref["ours18"]["canopy"], bs, names)
    _, b_lidf = F.band_reflectance(ref["ours"]["canopy"], bs, names)
    sens = (b_wet - b_py) / DLFMC                     # d(rho)/d(LFMC) per case, per %
    sig = F.atmospheric_sigma(b_py, pr.atmospheric_residual.absolute,
                              pr.atmospheric_residual.relative)
    rows = []
    for j, b in enumerate(names):
        shift = b_lidf[:, j] - b_py[:, j]
        row = {"band": b,
               "code_max_abs": float(np.abs(b_code[:, j] - b_py[:, j]).max()),
               "lidf_mean": float(shift.mean()),
               "lidf_p05": float(np.percentile(shift, 5)),
               "lidf_p95": float(np.percentile(shift, 95)),
               "lidf_max_abs": float(np.abs(shift).max()),
               "atm_sigma_mean": float(sig[:, j].mean()),
               "lidf_over_sigma_p95": float(np.percentile(np.abs(shift) / sig[:, j], 95))}
        if b in SWIR:                                 # where LFMC moves reflectance
            eq = shift / sens[:, j]
            row.update(lfmc_equiv_median=float(np.median(eq)),
                       lfmc_equiv_p05=float(np.percentile(eq, 5)),
                       lfmc_equiv_p95=float(np.percentile(eq, 95)))
        rows.append(row)
    import pandas as pd
    pd.DataFrame(rows).to_csv(out / "T_reference.csv", index=False, float_format="%.6g")
    figure(py, ref, rows, out / "reference.png")
    qual_spectra(p, groups, py, ref, out / "qual_P6f_spectra.png")

    def worst(tag, keys):
        return {k: float(np.abs(ref[tag][k] - py[k]).max()) for k in keys}
    leaf = ("leaf_R", "leaf_T")
    summary = {"cases": len(groups), "groups": sorted(set(groups)), "seed": SEED,
               "tolerance": TOL, "versions": ref["versions"],
               "code_max_abs": {**worst("ours", leaf), **worst("ours18", ("canopy",))},
               "coefficients_leaf_max_abs": worst("r", leaf),
               "lidf_canopy_max_abs": worst("ours", ("canopy",))["canopy"],
               "bands": rows, "run": run.directory.name}
    summary["code_passes"] = all(v <= TOL for v in summary["code_max_abs"].values())
    (out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    run.write_json("summary.json", summary)
    run.finalise(cases=len(groups), passes=summary["code_passes"])
    print("code:", {k: f"{v:.1e}" for k, v in summary["code_max_abs"].items()},
          "pass" if summary["code_passes"] else "FAIL")
    print("coefficients (leaf):", {k: f"{v:.1e}" for k, v in
                                   summary["coefficients_leaf_max_abs"].items()})
    print(f"leaf-angle classes (canopy): {summary['lidf_canopy_max_abs']:.1e}")
    for r in rows:
        extra = (f"  LFMC-equivalent {r['lfmc_equiv_median']:+.2f} % "
                 f"[{r['lfmc_equiv_p05']:+.2f}, {r['lfmc_equiv_p95']:+.2f}]" if b in SWIR
                 and "lfmc_equiv_median" in r else "")
        print(f"  {r['band']:4s} 13-18 {r['lidf_mean']:+.5f} [{r['lidf_p05']:+.5f}, "
              f"{r['lidf_p95']:+.5f}]  /sigma p95 {r['lidf_over_sigma_p95']:.2f}{extra}")
    return 0 if summary["code_passes"] else 1


if __name__ == "__main__":
    sys.exit(main())
