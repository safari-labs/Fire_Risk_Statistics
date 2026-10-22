"""scripts/make_experiments_doc.py

Generate docs/EXPERIMENTS.md from the register.

Generated, not hand-written, so the table and the figure cannot disagree --
they are both rendered from src/safari_bands/experiments.py. A hand-kept
table drifts: the AVIRIS line count was wrong in three documents at once
because each had been edited separately.

    python scripts/make_experiments_doc.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from safari_bands.experiments import (  # noqa: E402
    EXPERIMENTS,
    STATES,
    by_group,
    by_state,
    runnable,
)

OUT = Path("docs/EXPERIMENTS.md")


def _cell(s: str) -> str:
    """Make a string safe inside a markdown table cell."""
    return s.replace("|", "\\|").replace("\n", " ").strip()


def main() -> int:
    L: list[str] = []
    L.append("# Experiment register")
    L.append("")
    L.append("**Generated from `src/safari_bands/experiments.py` by "
             "`scripts/make_experiments_doc.py`. Do not edit by hand** -- "
             "the figure `docs/results/figures/experiment_plan.png` renders "
             "from the same register, and a hand-kept copy drifts.")
    L.append("")
    L.append(f"{len(EXPERIMENTS)} experiments. **{len(runnable())} can run "
             f"today** on data already packed and staged.")
    L.append("")

    # ── State summary ────────────────────────────────────────────────────
    L.append("## Feasibility at a glance")
    L.append("")
    L.append("| State | Count | What it means | Experiments |")
    L.append("|---|---|---|---|")
    st = by_state()
    for key, meta in STATES.items():
        if key not in st:
            continue
        ids = ", ".join(e.eid for e in st[key])
        L.append(f"| **{meta['label']}** | {len(st[key])} | "
                 f"{meta['detail']} | {ids} |")
    L.append("")
    L.append("Numbering note: E-17 to E-20 were an earlier E-1 to E-4 from "
             "the CFFDRS gap audit. They were renumbered into this single "
             "register rather than left as a second scheme; "
             "`docs/CFFDRS_GAPS.md` points at the new ids.")
    L.append("")

    # ── The main table, by group ─────────────────────────────────────────
    L.append("## Experiments")
    L.append("")
    for group, items in by_group().items():
        L.append(f"### {group}")
        L.append("")
        L.append("| ID | Experiment | Independent variable | Dependent "
                 "variable | Hypothesis | State | Runner |")
        L.append("|---|---|---|---|---|---|---|")
        for e in items:
            star = " \u2605" if "primary" in e.tags else ""
            ctl = " (control)" if "control" in e.tags else ""
            runner = f"`{e.runner}`" if e.runner != "--" else "*none yet*"
            L.append(
                f"| **{e.eid}** | {_cell(e.name)}{star}{ctl} | "
                f"{_cell(e.independent)} | {_cell(e.dependent)} | "
                f"{_cell(e.hypothesis)} | "
                f"{STATES[e.state]['label']} | {runner} |")
        L.append("")

    # ── Conclusions, which is the part worth reading ─────────────────────
    L.append("## Hypotheses and conclusions")
    L.append("")
    L.append("Each experiment carries a falsifiable **prediction** and "
             "the condition that would refute it, then what could be "
             "**concluded** either way. The conclusion field is what "
             "decides whether an experiment deserves GPU time: one whose "
             "null result teaches nothing is not worth queueing, and "
             "writing it down is how that gets noticed before the run.")
    L.append("")
    L.append("The hypotheses are written to be capable of being wrong. "
             "`CLAUDE.md` is explicit that the study's job is to **test** "
             "the brief's hypotheses rather than confirm them, so each "
             "states what being wrong would look like. Where a prediction "
             "comes from the brief (H1, H2, H3) it is attributed; the rest "
             "are this study's own and carry no more authority than that.")
    L.append("")
    for group, items in by_group().items():
        L.append(f"### {group}")
        L.append("")
        for e in items:
            L.append(f"**{e.eid} — {e.name}**")
            L.append("")
            if e.hypothesis:
                L.append(f"*Hypothesis:* {e.hypothesis}")
                L.append("")
            L.append(e.conclusion)
            if e.note:
                L.append("")
                L.append(f"*Note:* {e.note}")
            if e.blocker:
                L.append("")
                L.append(f"*Blocked on:* {e.blocker}")
            if e.gap:
                L.append("")
                L.append(f"*CFFDRS gap:* {e.gap}")
            L.append("")

    # ── Runnable-now shortlist ───────────────────────────────────────────
    L.append("## Runnable today")
    L.append("")
    L.append("| ID | Experiment | Command |")
    L.append("|---|---|---|")
    for e in runnable():
        L.append(f"| **{e.eid}** | {_cell(e.name)} | `{e.runner}` |")
    L.append("")
    L.append("All of these read the `stage2_fire_11band` pack already in "
             "`~/scratch` on Narval. None needs a new download or a "
             "re-pack.")
    L.append("")
    L.append("Two standing caveats on every number they produce. The "
             "35-epoch budget is a **ranking** budget, so the output is an "
             "order and not an accuracy until the top sets are re-run at "
             "full budget. And the fold spread is large -- the one arm that "
             "has completed spanned 0.5396 to 0.7660 across six folds from "
             "a single model on a single input -- so results must be read "
             "as **paired** per-fold contrasts via `report_arms.py`, never "
             "as two means compared by eye.")
    L.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"  wrote {OUT}  ({len(EXPERIMENTS)} experiments, "
          f"{len(runnable())} runnable)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
