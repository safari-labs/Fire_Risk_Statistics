"""scripts/make_sensor_figure.py

The Mantis mode decision, and which arm of the study can decide each part.

From James's datasheet extract -- one <1U imager at TRL-9, four modes:

    Snapshot    RGB or Monochrome
    Push broom  Multispectral   6x MS bands    400-1000 nm
    Push broom  Hyperspectral   96x HS bands    470- 900 nm
    Push broom  SWIR            4x SWIR bands  1000-1750 nm

The figure exists because three things about that table are easy to miss:

  * HS has a NARROWER range than MS, so it is not a strict upgrade -- it buys
    resolution by giving up both ends of the spectrum;
  * the band COUNTS are fixed, so only k=6 and k=4 are decisions;
  * Sentinel-2 splits very unevenly across the modes, which decides what is
    answerable now and what needs hyperspectral data.

    python scripts/make_sensor_figure.py
"""
from __future__ import annotations

import sys
from pathlib import Path

OUT = Path("docs/results/figures")

FIG_BG, AX_BG = "#14161a", "#1b1e24"
INK, INK_BRIGHT, MUTED, SPINE = "#c7ccd4", "#eef1f5", "#79818e", "#2c313a"
MS_C, HS_C, SW_C, CRIT = "#4ea1d3", "#9b7fd4", "#e8973f", "#d1495b"

#: Sentinel-2 bands, and which Mantis modes can see them.
S2 = [("B1", 443), ("B2", 490), ("B3", 560), ("B4", 665), ("B5", 705),
      ("B6", 740), ("B7", 783), ("B8", 842), ("B8A", 865), ("B9", 945),
      ("B11", 1610)]

#: WorldView-3, the archive standing in for the bands Sentinel-2 lacks.
#: Eight VNIR plus four SWIR inside the Mantis SWIR window -- one platform,
#: co-registered, which is how the dichroic design sees the scene too.
WV3_VNIR = [427, 478, 546, 608, 659, 724, 831, 908]
WV3_SWIR = [1209, 1572, 1661, 1730]

#: Where the dichroic splits: SWIR reflected, VNIR transmitted.
DICHROIC_NM = 1000

MS_LO, MS_HI, N_MS = 400, 1000, 6
HS_LO, HS_HI, N_HS = 470, 900, 96
SW_LO, SW_HI, N_SW = 1000, 1750, 4

#: Of the 96 HS bands, those falling in the O2-A absorption return no surface
#: signal. A contiguous sensor cannot avoid them.
N_HS_ATMOS = 5


def main() -> int:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    from safari_bands.band_names import band_label

    plt.rcParams.update({
        "font.family": "DejaVu Sans", "text.color": INK,
        "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.edgecolor": SPINE, "figure.facecolor": FIG_BG,
        "savefig.facecolor": FIG_BG,
    })

    fig, ax = plt.subplots(figsize=(11.2, 6.2), facecolor=FIG_BG)
    ax.set_facecolor(AX_BG)
    ax.set_xlim(370, 1810)
    ax.set_ylim(-0.35, 10)
    fig.suptitle("Mantis modes, and what our data can decide",
                 color=INK_BRIGHT, fontsize=12.5, x=0.0, ha="left", y=1.01)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(SPINE)
    ax.set_yticks([])
    ax.set_xlabel("wavelength (nm)", fontsize=9.6)
    ax.tick_params(labelsize=8.8)

    # Mode envelopes, stacked so the HS/MS range difference is unmissable.
    bars = [
        (MS_LO, MS_HI, 8.05, MS_C, f"Multispectral  -  {N_MS} bands",
         f"{MS_LO}-{MS_HI} nm"),
        (HS_LO, HS_HI, 6.65, HS_C, f"Hyperspectral  -  {N_HS} bands",
         f"{HS_LO}-{HS_HI} nm"),
        (SW_LO, SW_HI, 5.25, SW_C, f"SWIR  -  {N_SW} bands",
         f"{SW_LO}-{SW_HI} nm"),
    ]
    for lo, hi, y, col, label, rng in bars:
        ax.barh(y, hi - lo, left=lo, height=0.82, color=col, alpha=0.30,
                edgecolor=col, linewidth=1.6, zorder=2)
        ax.text(lo + 12, y + 0.17, label, color=col, fontsize=9.6,
                weight="bold", va="center", zorder=4)
        ax.text(lo + 12, y - 0.24, rng, color=INK, fontsize=8.6,
                va="center", zorder=4)

    # The reach HS gives up, at both ends.
    for lo, hi in ((MS_LO, HS_LO), (HS_HI, MS_HI)):
        ax.barh(6.65, hi - lo, left=lo, height=0.82, color=CRIT, alpha=0.22,
                hatch="///", edgecolor=CRIT, linewidth=0.9, zorder=3)
    ax.annotate("HS is NARROWER than MS:\nno B1 (443) and no B9 (945)",
                xy=(935, 6.65), xytext=(1065, 7.1), color=CRIT, fontsize=8.8,
                va="center", zorder=5,
                arrowprops=dict(arrowstyle="->", color=CRIT, lw=1.1))

    # Sentinel-2 sampling, and which modes reach each band.
    for name, nm in S2:
        in_ms = MS_LO <= nm <= MS_HI
        in_hs = HS_LO <= nm <= HS_HI
        in_sw = SW_LO <= nm <= SW_HI
        col = SW_C if in_sw else (MS_C if in_hs else CRIT)
        ax.plot([nm, nm], [3.15, 3.7], color=col, lw=2.6,
                solid_capstyle="round", zorder=3)
        colour = INK if (in_hs or in_sw) else CRIT
        if in_sw:
            # Beside the line, not above it: the SWIR bar sits right there.
            ax.text(nm + 14, 3.42, band_label(name), color=colour,
                    fontsize=7.3, ha="left", va="center")
        else:
            ax.text(nm + {"B8": -9, "B8A": 9}.get(name, 0), 3.82,
                    band_label(name), color=colour, fontsize=7.0,
                    ha="center", rotation=90, va="bottom")
        if in_ms and not in_hs:
            ax.plot(nm, 2.95, marker="v", color=CRIT, ms=5, zorder=4)

    # The dichroic crossover, and the band that sits in it.
    ax.axvline(DICHROIC_NM, ymin=0.33, ymax=0.97, color=INK_BRIGHT, lw=1.4,
               ls="--", alpha=0.75, zorder=5)
    ax.text(DICHROIC_NM + 10, 9.45, "dichroic", color=INK_BRIGHT,
            fontsize=8.6, ha="left", va="center", style="italic")
    ax.text(DICHROIC_NM + 10, 9.05, "SWIR reflected 90 deg", color=SW_C,
            fontsize=7.8, ha="left", va="center")
    ax.text(DICHROIC_NM - 10, 9.05, "MS transmitted", color=MS_C,
            fontsize=7.8, ha="right", va="center")

    ax.text(700, 2.25, "Sentinel-2 candidates in range", color=INK_BRIGHT,
            fontsize=9, ha="center")
    ax.text(700, 1.45, "MS: 10      HS: 8  (red = HS cannot see)",
            color=INK, fontsize=9, ha="center", family="monospace")
    ax.text(700, 0.95, "choose 6  ->  DECIDABLE NOW", color=MS_C,
            fontsize=9.4, ha="center", weight="bold")

    ax.text(1375, 2.25, "Sentinel-2 candidates in range", color=INK_BRIGHT,
            fontsize=9, ha="center")
    ax.text(1375, 1.45, "SWIR: 1  (B11 only)", color=INK, fontsize=9,
            ha="center", family="monospace")
    ax.text(1375, 0.95, "choose 4  ->  WORLDVIEW-3 SUPPLIES IT", color=SW_C,
            fontsize=9.4, ha="center", weight="bold")

    # WorldView-3 row: the archive that fills the SWIR gap.
    for nm in WV3_VNIR:
        ax.plot([nm, nm], [0.12, 0.52], color=MS_C, lw=2.0, alpha=0.75,
                solid_capstyle="round", zorder=3)
    for nm in WV3_SWIR:
        ax.plot([nm, nm], [0.12, 0.52], color=SW_C, lw=2.0,
                solid_capstyle="round", zorder=3)
    ax.text(378, 0.32, "WV-3", color=INK, fontsize=8, ha="right",
            va="center", family="monospace")
    # Below the ticks, not beside them: at the right edge it sat on the
    # 1572/1661/1730 marks it was describing.
    ax.text(1090, -0.28, "WorldView-3: 8 VNIR + 4 SWIR, one platform, "
            "co-registered", color=MUTED, fontsize=7.8, ha="center",
            va="bottom", style="italic")

    ax.legend(handles=[
        Patch(facecolor=CRIT, alpha=0.3, hatch="///", edgecolor=CRIT,
              label="range HS gives up"),
    ], loc="upper right", bbox_to_anchor=(1.0, 0.60), frameon=False,
        labelcolor=INK, fontsize=8.4)

    cap = [
        "One <1U head at TRL-9, four modes. The band counts are FIXED, so "
        "only k=6 and k=4 are decisions -- k=7 is unreachable, not a trade.",
        "",
        f"HS is not a strict upgrade on MS. It buys {N_HS} bands at ~4.5 nm "
        f"by surrendering 400-470 and 900-1000 nm, which costs exactly B1 "
        f"(coastal/aerosol) and B9 (water vapour).",
        f"That makes MS-vs-HS answerable with data already on disk: run the "
        f"VNIR selection over all ten S2 bands and see whether B1 or B9 earns "
        f"a place in the best six.",
        f"Five of the {N_HS} HS bands also fall in the O2-A absorption and "
        f"return no surface signal, so the effective surface count is "
        f"{N_HS - N_HS_ATMOS}.",
        "",
        "The SWIR mode cannot be chosen from Sentinel-2 at all -- one band in "
        "range is not a pool of four. WorldView-3 supplies it: four real "
        "measurements at 1209, 1572, 1661 and 1730 nm.",
        "WV-3 also carries eight VNIR bands, so it can supply BOTH halves "
        "co-registered -- the same way the dichroic sees the scene. Pairing "
        "WV-3 SWIR with S2 VNIR instead would add a cross-platform",
        "mismatch the real instrument does not have. Tuning the four centres "
        "freely still needs hyperspectral.",
    ]
    fig.text(0.0, -0.33, chr(10).join(cap), color=MUTED, fontsize=8.4,
             ha="left")

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "status_sensor_decision.png"
    fig.savefig(out, dpi=170, facecolor=FIG_BG, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
