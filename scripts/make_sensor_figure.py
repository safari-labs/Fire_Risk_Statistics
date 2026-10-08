"""scripts/make_sensor_figure.py

The hardware decision this study resolves to, and which arm can decide it.

Two candidate pushbroom sensors, taken singly or together (ASSUMPTIONS A-18):

    VNIR pushbroom   silicon           400-1000 nm    6 bands
    SWIR pushbroom   standard InGaAs   1000-1750 nm   4 bands

The figure exists because the band count is FIXED per sensor, which changes
what the nested ranking is for. Only k=6 and k=4 are decisions; marginal gain
at k=7 in the VNIR is not a trade, it is unreachable. And Sentinel-2 splits
very unevenly across the two: ten candidate bands inside the VNIR window and
exactly one inside the SWIR window.

    python scripts/make_sensor_figure.py
"""
from __future__ import annotations

import sys
from pathlib import Path

OUT = Path("docs/results/figures")

FIG_BG, AX_BG = "#14161a", "#1b1e24"
INK, INK_BRIGHT, MUTED, SPINE = "#c7ccd4", "#eef1f5", "#79818e", "#2c313a"
S1, S2, CRIT = "#4ea1d3", "#e8973f", "#d1495b"

#: Sentinel-2 bands inside each sensor's range.
VNIR_POOL = [("B1", 443), ("B2", 490), ("B3", 560), ("B4", 665), ("B5", 705),
             ("B6", 740), ("B7", 783), ("B8", 842), ("B8A", 865), ("B9", 945)]
SWIR_POOL = [("B11", 1610)]

#: How many bands each sensor carries.
N_VNIR, N_SWIR = 6, 4


def main() -> int:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.family": "DejaVu Sans", "text.color": INK,
        "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.edgecolor": SPINE, "figure.facecolor": FIG_BG,
        "savefig.facecolor": FIG_BG,
    })

    fig, ax = plt.subplots(figsize=(10.4, 4.4), facecolor=FIG_BG)
    ax.set_facecolor(AX_BG)
    ax.set_xlim(380, 1830)
    ax.set_ylim(0, 10)
    fig.suptitle("Two candidate sensors, and what our data can decide",
                 color=INK_BRIGHT, fontsize=12.5, x=0.0, ha="left", y=1.01)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(SPINE)
    ax.set_yticks([])
    ax.set_xlabel("wavelength (nm)", fontsize=9.4)
    ax.tick_params(labelsize=8.8)

    ax.axvspan(400, 1000, ymin=0.30, ymax=0.95, color=S1, alpha=0.13, lw=0)
    ax.axvspan(1000, 1750, ymin=0.30, ymax=0.95, color=S2, alpha=0.13, lw=0)

    ax.text(700, 9.45, "VNIR pushbroom  -  silicon", color=S1,
            fontsize=10, ha="center", weight="bold")
    ax.text(700, 8.85, f"{N_VNIR} bands, 400-1000 nm", color=S1,
            fontsize=9.2, ha="center")
    ax.text(1375, 9.45, "SWIR pushbroom  -  standard InGaAs", color=S2,
            fontsize=10, ha="center", weight="bold")
    ax.text(1375, 8.85, f"{N_SWIR} bands, 1000-1750 nm", color=S2,
            fontsize=9.2, ha="center")

    # Where a SWIR band physically cannot sit.
    ax.axvspan(1350, 1450, ymin=0.30, ymax=0.72, color=CRIT, alpha=0.32, lw=0)
    ax.text(1400, 5.05, "H2O", color=CRIT, fontsize=7.6, ha="center")
    ax.text(1400, 4.45, "opaque", color=CRIT, fontsize=7.6, ha="center")
    ax.axvline(1270, ymin=0.30, ymax=0.72, color=CRIT, ls=":", lw=1.3)
    ax.text(1270, 7.5, "O2", color=CRIT, fontsize=7.6, ha="center")

    # What Sentinel-2 actually samples.
    for name, nm in VNIR_POOL:
        ax.plot([nm, nm], [5.6, 7.1], color=S1, lw=2.6,
                solid_capstyle="round")
        ax.text(nm, 7.3, name, color=INK, fontsize=7.2, ha="center",
                rotation=90, va="bottom")
    for name, nm in SWIR_POOL:
        ax.plot([nm, nm], [5.6, 7.1], color=S2, lw=2.6,
                solid_capstyle="round")
        ax.text(nm, 7.3, name, color=INK, fontsize=7.2, ha="center",
                rotation=90, va="bottom")

    ax.text(700, 3.6, f"{len(VNIR_POOL)} Sentinel-2 candidates",
            color=S1, fontsize=9.6, ha="center", weight="bold")
    ax.text(700, 2.9, f"choose {N_VNIR}", color=INK, fontsize=9, ha="center")
    ax.text(700, 2.0, "DECIDABLE WITH DATA IN HAND", color=S1,
            fontsize=9.2, ha="center", weight="bold")

    ax.text(1375, 3.6, f"{len(SWIR_POOL)} Sentinel-2 candidate",
            color=S2, fontsize=9.6, ha="center", weight="bold")
    ax.text(1375, 2.9, f"choose {N_SWIR}", color=INK, fontsize=9, ha="center")
    ax.text(1375, 2.0, "NEEDS HYPERSPECTRAL", color=S2,
            fontsize=9.2, ha="center", weight="bold")

    ax.annotate("2190 nm (config C)\nout of range",
                xy=(1750, 6.3), xytext=(1790, 6.3), color=MUTED,
                fontsize=7.8, ha="left", va="center", style="italic",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.9))

    cap = [
        "Three options: VNIR only, SWIR only, or both -- the last only if the "
        "gain justifies it. The band count is FIXED per sensor, so only k=6 "
        "and k=4 are decisions;",
        "k=7 in the VNIR is unreachable rather than a trade. Extended InGaAs "
        "is not on offer, so configuration C is retired and H1 as written "
        "(SWIR1 + SWIR2) has no real option behind it --",
        "its fallback clause, SWIR1 + 1240 nm, becomes the live question, and "
        "4 bands is exactly the budget for it.",
        "",
        "'Both' is two focal planes and must be scored WITH a misregistration "
        "term: NDMI and NMDI contrast NIR against SWIR, so the products that "
        "motivate the second sensor",
        "are the ones that cross the chain boundary.",
    ]
    fig.text(0.0, -0.30, chr(10).join(cap), color=MUTED, fontsize=8.3,
             ha="left")

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "status_sensor_decision.png"
    fig.savefig(out, dpi=170, facecolor=FIG_BG, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
