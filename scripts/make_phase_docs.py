"""scripts/make_phase_docs.py

One visual sheet per phase: every experiment, control, check and measurement
the phase ran, each as a card -- the hypothesis (or the pass criterion, or
the question where none was registered), what was varied, what was measured,
the result, the verdict and the conclusion. Content comes from
src/safari_bands/phases.py, and for registered experiments straight from the
register, so a sheet cannot restate a hypothesis differently from how it was
registered.

Writes docs/results/<phase folder>/experiments.png and experiments.md (the
same content as text, for reading and searching).

    python scripts/make_phase_docs.py            # every phase
    python scripts/make_phase_docs.py --phase P2
"""
from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from safari_bands.phases import PHASES, VERDICTS, Phase, by_pid  # noqa: E402

# House surfaces and ink (make_result_figures.py). Verdicts are states, so
# they take the status hues -- and always carry their word, never colour alone.
FIG_BG, CARD_BG, BOX_BG = "#0f1117", "#1a1d27", "#232735"
SPINE, INK, INK_BRIGHT, MUTED = "#333344", "#cccccc", "#eeeeee", "#8b8b9a"
VERDICT_COLOUR = {"SUPPORTED": "#199e70", "PASS": "#199e70", "REFUTED": "#e66767",
                  "AT RISK": "#fab219", "MIXED": "#fab219", "FIXED": "#fab219",
                  "PARTIAL": "#7fb069",
                  "MEASURED": "#3987e5",
                  "PENDING": "#5a5f70"}
VERDICT_INK = {"AT RISK": FIG_BG, "FIXED": FIG_BG, "MIXED": FIG_BG, "PARTIAL": FIG_BG}
DPI = 150

W = 15.0                       # sheet width, inches
M = 0.3                        # outer margin
FS, FS_LABEL, FS_HEAD = 9.0, 7.2, 10.5
LH = 0.168                     # line height at FS, inches
CPI = 14.0                     # wrapped characters per inch at FS (conservative)
GAP = 0.12


def _wrap(text: str, width_in: float) -> list[str]:
    return textwrap.wrap(text, max(10, int(width_in * CPI))) or [""]


def _card_layout(entry) -> dict:
    r = entry.resolved()
    inner = W - 2 * M - 0.45
    box_w = [(inner - 0.7) * f for f in (0.29, 0.29, 0.42)]
    q = _wrap(r["question"], inner)
    boxes = [_wrap(r["independent"], box_w[0] - 0.2), _wrap(r["dependent"], box_w[1] - 0.2),
             _wrap(entry.result, box_w[2] - 0.2)]
    concl = _wrap(entry.conclusion, inner)
    box_h = max(len(b) for b in boxes) * LH + 0.36
    h = (0.16 + 0.32                       # top pad, header
         + 0.2 + len(q) * LH + GAP         # question label + text
         + box_h + GAP                     # flow row
         + 0.2 + len(concl) * LH + 0.16)   # conclusion label + text, bottom pad
    return {"r": r, "q": q, "boxes": boxes, "box_w": box_w, "box_h": box_h,
            "concl": concl, "h": h, "inner": inner}


def render(phase: Phase, out_dir: Path) -> Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    layouts = [_card_layout(e) for e in phase.entries]
    head_h = 1.05
    H = head_h + sum(L["h"] + 0.22 for L in layouts) + 0.5
    fig = plt.figure(figsize=(W, H), facecolor=FIG_BG)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")

    ax.text(M, 0.42, f"{phase.pid}  {phase.title}", color=INK_BRIGHT, fontsize=15,
            va="center")
    ax.text(W - M, 0.42, phase.date, color=MUTED, fontsize=10, va="center", ha="right")
    for i, line in enumerate(_wrap(phase.summary, W - 2 * M)):
        ax.text(M, 0.78 + i * LH, line, color=INK, fontsize=FS, va="center")

    y = head_h + 0.1 + (len(_wrap(phase.summary, W - 2 * M)) - 1) * LH
    for e, L in zip(phase.entries, layouts, strict=True):
        r, col = L["r"], VERDICT_COLOUR[e.verdict]
        x0, x1 = M, W - M
        ax.add_patch(FancyBboxPatch((x0, y), x1 - x0, L["h"],
                                    boxstyle="round,pad=0,rounding_size=0.08",
                                    fc=CARD_BG, ec=SPINE, lw=0.8))
        ax.add_patch(FancyBboxPatch((x0, y), 0.09, L["h"],
                                    boxstyle="round,pad=0,rounding_size=0.04",
                                    fc=col, ec="none"))
        cx = x0 + 0.3
        cy = y + 0.16 + 0.16
        ax.text(cx, cy, f"{e.ref}", color=INK_BRIGHT, fontsize=FS_HEAD,
                fontweight="bold", va="center")
        ax.text(cx + 0.75, cy, r["title"], color=INK_BRIGHT, fontsize=FS_HEAD, va="center")
        ax.text(x1 - 1.75, cy, e.kind.upper(), color=MUTED, fontsize=FS_LABEL,
                va="center", ha="right")
        ax.text(x1 - 0.2, cy, f"  {e.verdict}  ", color=VERDICT_INK.get(e.verdict, "#ffffff"),
                fontsize=FS_LABEL + 1, fontweight="bold", va="center", ha="right",
                bbox={"boxstyle": "round,pad=0.35", "fc": col, "ec": "none"})

        cy += 0.16 + 0.2
        ax.text(cx, cy, r["label"].upper(), color=MUTED, fontsize=FS_LABEL, va="center")
        for i, line in enumerate(L["q"]):
            ax.text(cx, cy + (i + 1) * LH, line, color=INK, fontsize=FS, va="center")
        cy += len(L["q"]) * LH + GAP + 0.08

        bx = cx
        titles = ("VARIED  (independent)", "MEASURED  (dependent)", "RESULT")
        for k, (lines, bw) in enumerate(zip(L["boxes"], L["box_w"], strict=True)):
            ax.add_patch(FancyBboxPatch((bx, cy), bw, L["box_h"],
                                        boxstyle="round,pad=0,rounding_size=0.06",
                                        fc=BOX_BG, ec=col if k == 2 else SPINE, lw=0.9))
            ax.text(bx + 0.1, cy + 0.16, titles[k], color=MUTED, fontsize=FS_LABEL,
                    va="center")
            for i, line in enumerate(lines):
                ax.text(bx + 0.1, cy + 0.36 + i * LH, line,
                        color=INK_BRIGHT if k == 2 else INK, fontsize=FS, va="center")
            if k < 2:
                ax.add_patch(FancyArrowPatch((bx + bw + 0.06, cy + L["box_h"] / 2),
                                             (bx + bw + 0.29, cy + L["box_h"] / 2),
                                             arrowstyle="-|>", mutation_scale=11,
                                             color=MUTED, lw=1.2))
            bx += bw + 0.35
        cy += L["box_h"] + GAP + 0.1

        ax.text(cx, cy, "CONCLUSION", color=MUTED, fontsize=FS_LABEL, va="center")
        for i, line in enumerate(L["concl"]):
            ax.text(cx, cy + (i + 1) * LH, line, color=INK_BRIGHT, fontsize=FS, va="center")
        y += L["h"] + 0.22

    legend = "   ".join(f"{v}: {VERDICTS[v]}" for v in sorted({e.verdict for e in phase.entries}))
    for i, line in enumerate(_wrap(legend, W - 2 * M)):
        ax.text(M, y + 0.1 + i * LH, line, color=MUTED, fontsize=FS_LABEL + 0.5, va="center")

    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "experiments.png"
    fig.savefig(p, dpi=DPI, facecolor=FIG_BG)
    plt.close(fig)
    return p


def markdown(phase: Phase) -> str:
    lines = [f"# {phase.pid}: {phase.title} ({phase.date})", "",
             "What this phase ran and concluded. Generated by "
             "`scripts/make_phase_docs.py` from `src/safari_bands/phases.py`; "
             "registered hypotheses are quoted from the register, verbatim. "
             f"Full results: [{phase.note}]({phase.note}).", "",
             phase.summary, "", "![experiments](experiments.png)", ""]
    for e in phase.entries:
        r = e.resolved()
        lines += [f"## {e.ref}: {r['title']} ({e.kind}): **{e.verdict}**", "",
                  "| | |", "|---|---|",
                  f"| {r['label']} | {r['question']} |",
                  f"| Varied (independent) | {r['independent']} |",
                  f"| Measured (dependent) | {r['dependent']} |",
                  f"| Result | {e.result} |",
                  f"| Verdict | **{e.verdict}**: {VERDICTS[e.verdict]} |",
                  f"| Conclusion | {e.conclusion} |", ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--phase", default=None)
    args = ap.parse_args(argv)
    phases = [by_pid(args.phase)] if args.phase else list(PHASES)
    for ph in phases:
        out = _ROOT / "docs" / "results" / ph.folder
        p = render(ph, out)
        (out / "experiments.md").write_text(markdown(ph), encoding="utf-8")
        print(f"  wrote {p.relative_to(_ROOT)} and experiments.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
