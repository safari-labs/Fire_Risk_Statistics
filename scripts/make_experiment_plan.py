"""scripts/make_experiment_plan.py

Every experiment, as a table: what it varies, what it measures, what it
could conclude, whether it can run, and what runs it.

RENDERED FROM src/safari_bands/experiments.py, which docs/EXPERIMENTS.md
also renders from. Previously the plan lived inline in this file and the
same facts were restated in three documents; the AVIRIS line count was
wrong in all three at once because each had been edited separately.

Grouped by THEME rather than by readiness, with the feasibility state as a
column, because the thing a reader wants is "what does this experiment
settle" and the state is a property of today rather than of the experiment.

    python scripts/make_experiment_plan.py
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from safari_bands.experiments import (  # noqa: E402
    EXPERIMENTS,
    STATES,
    by_group,
    runnable,
)

OUT = Path("docs/results/figures")

FIG_BG, AX_BG = "#14161a", "#1b1e24"
INK, INK_BRIGHT, MUTED, SPINE = "#c7ccd4", "#eef1f5", "#79818e", "#2c313a"
HEAD = "#4ea1d3"

#: Column layout in axis units (0-100), and how many characters fit.
COLS = [
    ("ID", 0.0, 4),
    ("EXPERIMENT", 4.0, 26),
    ("VARIES (independent)", 23.0, 40),
    ("MEASURES (dependent)", 46.0, 34),
    ("STATE", 65.0, 16),
    ("RUNNER", 77.5, 38),
]


def _wrap(text: str, width: int) -> list[str]:
    return textwrap.wrap(text, width=width) or [""]


def main() -> int:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK,
                         "figure.facecolor": FIG_BG,
                         "savefig.facecolor": FIG_BG})

    groups = by_group()

    # Row heights are driven by the tallest wrapped cell, so nothing is
    # clipped and the table does not need a fixed row height that is wrong
    # for both the short rows and the long ones.
    plan: list = []
    for group, items in groups.items():
        plan.append(("__group__", group))
        for e in items:
            cells = [
                [e.eid],
                _wrap(e.name, COLS[1][2]),
                _wrap(e.independent, COLS[2][2]),
                _wrap(e.dependent, COLS[3][2]),
                _wrap(STATES[e.state]["label"], COLS[4][2]),
                _wrap(e.runner if e.runner != "--" else "(none yet)",
                      COLS[5][2]),
            ]
            plan.append((e, cells, max(len(c) for c in cells)))

    LINE = 0.175                    # height of one text line
    PAD = 0.12                      # padding inside a row
    GROUP_H = 0.52

    total = 0.0
    for item in plan:
        total += GROUP_H if item[0] == "__group__" else item[2] * LINE + PAD

    fig, ax = plt.subplots(figsize=(20.0, 0.55 + total), facecolor=FIG_BG)
    ax.set_xlim(0, 116)
    ax.set_ylim(-0.1, total + 0.95)
    ax.axis("off")
    # The axes fill the canvas; without this the default margins leave a
    # band of dead space above the header taller than several rows.
    fig.subplots_adjust(top=1.0, bottom=0.0, left=0.0, right=1.0)

    n_run = len(runnable())
    # Drawn in axis units rather than as a suptitle, so it sits a fixed
    # distance above the header row instead of at the top of a canvas whose
    # height changes with the number of experiments.
    ax.text(0, total + 0.78,
            f"Experiment register — {len(EXPERIMENTS)} experiments, "
            f"{n_run} runnable today",
            color=INK_BRIGHT, fontsize=14, va="center")

    # Column headers.
    y = total + 0.30
    for label, x, _w in COLS:
        ax.text(x, y, label, color=HEAD, fontsize=7.6, weight="bold",
                va="center")
    ax.plot([0, 116], [y - 0.17, y - 0.17], color=HEAD, lw=1.0, alpha=0.5)

    y = total
    for item in plan:
        if item[0] == "__group__":
            y -= GROUP_H
            ax.text(0, y + 0.17, item[1].upper(), color=INK_BRIGHT,
                    fontsize=9.6, weight="bold", va="center")
            ax.plot([0, 116], [y - 0.02, y - 0.02], color=SPINE, lw=0.8)
            continue

        e, cells, nlines = item
        h = nlines * LINE + PAD
        y -= h
        ax.add_patch(FancyBboxPatch(
            (0, y + 0.02), 116, h - 0.05, boxstyle="round,pad=0.01",
            facecolor=AX_BG, edgecolor="none", zorder=1))
        # A state chip, so feasibility is readable down the page.
        ax.add_patch(FancyBboxPatch(
            (-0.9, y + 0.05), 0.6, h - 0.11, boxstyle="square,pad=0",
            facecolor=STATES[e.state]["colour"], edgecolor="none",
            alpha=0.95, zorder=2))

        top = y + h - PAD / 2 - LINE / 2
        for (label, x, _w), lines in zip(COLS, cells, strict=True):
            for i, line in enumerate(lines):
                bright = label in ("ID", "EXPERIMENT")
                mono = label == "RUNNER"
                col = INK_BRIGHT if bright else INK
                if label == "STATE":
                    col = STATES[e.state]["colour"]
                if mono and e.runner == "--":
                    col = MUTED
                ax.text(x, top - i * LINE, line, color=col,
                        fontsize=7.9 if not bright else 8.3,
                        va="center", zorder=3,
                        family="monospace" if mono else None,
                        weight="bold" if (bright and i == 0) else "normal")
        # Star the primary experiments.
        if "primary" in e.tags:
            ax.text(114.6, top, "★", color="#e8c547", fontsize=10,
                    va="center", ha="right", zorder=3)

    fig.text(0.0, -0.030, chr(10).join([
        "RENDERED FROM src/safari_bands/experiments.py, which "
        "docs/EXPERIMENTS.md also renders from, so the table and the "
        "document cannot drift. The CONCLUSION each experiment could reach "
        "is in",
        "that document: it is the field that decides whether an experiment "
        "deserves GPU time, since one whose null result teaches nothing is "
        "not worth queueing.",
        "",
        "STATE is a property of today, not of the experiment. "
        + "   ".join(f"{STATES[k]['label']}: {sum(1 for e in EXPERIMENTS if e.state == k)}"
                     for k in STATES
                     if any(e.state == k for e in EXPERIMENTS)),
        "",
        "TWO CAVEATS ON EVERY NUMBER. The 35-epoch budget is a RANKING "
        "budget, so results are an order and not an accuracy until the top "
        "sets are re-run at full budget. And the fold spread is large --",
        "the one arm that has completed spanned 0.5396 to 0.7660 across six "
        "folds from a single model on a single input -- so arms must be "
        "compared as PAIRED per-fold differences through",
        "report_arms.py, never as two means read by eye.",
        "",
        "★ marks the three experiments the study turns on: E-1 names "
        "the six VNIR bands, E-11 tests a moisture index against the "
        "greenness proxy CFFDRS currently accepts, and E-22 is the primary",
        "band ranking because SCANFI gives dense per-pixel labels instead "
        "of one sparse outcome per patch.",
    ]), color=MUTED, fontsize=8.2, ha="left", linespacing=1.5)

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "experiment_plan.png"
    fig.savefig(out, dpi=150, facecolor=FIG_BG, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {out}  ({len(EXPERIMENTS)} experiments, "
          f"{len(groups)} groups, {n_run} runnable)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
