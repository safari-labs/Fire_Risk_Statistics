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
    L.append("## Read this first: the label")
    L.append("")
    L.append("**Every result on the original 11-band pack trained on a "
             "circular label.** Its `/mask` is not NBAC: for fire scenes, "
             "`download.py` writes `_mask.tif` as **dNBR > 0.27**, and NBAC "
             "sat in a `_nbac.npy` sidecar that nothing in the tile or pack "
             "path read. All 861 fire tiles across the three splits "
             "reproduce `_mask.tif`'s dNBR exactly; against the patches' own "
             "NBAC masks the mean IoU is 0.755. dNBR is "
             "`NBR_pre - NBR_post` with `NBR = (B8 - B11)/(B8 + B11)`, so "
             "`NBR_pre` is reconstructible from the input bands -- rule 3's "
             "circularity. `sweep_bands.py --label nbac` was validated, "
             "printed and recorded, and never read.")
    L.append("")
    L.append("The damage concentrates where it matters most: B8, B8A and "
             "B11 in the ranking, and E-11 above all, because NDMI is "
             "`(B8A - B11)/(B8A + B11)` -- nearly the label's own input.")
    L.append("")
    L.append("**Fixed:** `stage2_fire_11band_nbac` swaps NBAC into the fire "
             "masks and changes nothing else -- tiles, splits and bands are "
             "byte-identical, so the held-out test set does not move. It "
             "declares `label_source = nbac`, and the sweep refuses any pack "
             "that does not declare one. NBAC marks 43% more burned pixels "
             "than dNBR did in the fire tiles: perimeters are filled "
             "polygons, so they include the inclusions dNBR skipped.")
    L.append("")
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
        L.append("| ID | Experiment | Hypothesis | Independent "
                 "variable | Dependent variable | State | Runner |")
        L.append("|---|---|---|---|---|---|---|")
        for e in items:
            star = " \u2605" if "primary" in e.tags else ""
            ctl = " (control)" if "control" in e.tags else ""
            runner = f"`{e.runner}`" if e.runner != "--" else "*none yet*"
            L.append(
                f"| **{e.eid}** | {_cell(e.name)}{star}{ctl} | "
                f"{_cell(e.hypothesis)} | "
                f"{_cell(e.independent)} | {_cell(e.dependent)} | "
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
    L.append("| ID | Experiment | Command | Narval resources per task |")
    L.append("|---|---|---|---|")
    for e in runnable():
        L.append(f"| **{e.eid}** | {_cell(e.name)} | `{e.runner}` | "
                 f"{_cell(e.resources) or '--'} |")
    L.append("")
    L.append("All of these read the **`stage2_fire_11band_nbac`** pack. "
             "It replaces the one already in `~/scratch`, which the sweep "
             "now refuses.")
    L.append("")
    L.append("### How the resources were derived")
    L.append("")
    L.append("From the only completed runs (the imagery-free G1 floor, six "
             "folds): every 35-epoch fit took **122 s**, identical across "
             "folds, with the GPU at **0.2-0.6% utilisation** and 0.6 GB of "
             "GPU memory; venv build and staging took under 45 s; sacct "
             "MaxRSS 1.04 GB. Identical times on a 337-parameter model is an "
             "input-bound signature -- the cost is h5py decompressing tiles "
             "in the DataLoader, not the GPU.")
    L.append("")
    L.append("- **`--time`** is 2 x (fits x 2.5 min) + 2 min, rounded up to "
             "30 min. 2.5 min is the measured 122 s plus a margin, because "
             "no CNN fit has completed yet. The old request was 11:00:00 "
             "for every job, including two-minute ones; jobs of 3 h or less "
             "can start on far more of Narval.")
    L.append("- **`--cpus-per-task=12`**: one A100's share of a 48-core, "
             "4-GPU node, so free in billing -- and since the job is "
             "CPU-bound, the workers are where speed comes from. Ten "
             "DataLoader workers, kept alive across epochs.")
    L.append("- **`--mem=16G`**: 1.04 GB measured at load plus ten workers' "
             "buffers.")
    L.append("- **Fit counts are simulated** by running each search through "
             "the real greedy and leave-one-out code with a counting scorer. "
             "Memoisation made the old formula wrong: it said 63 fits for "
             "`vnir_swir`, which is 51.")
    L.append("")
    L.append("The whole programme is about **50 GPU-hours**. Recalibrate "
             "once real CNN fits exist: every fit now appends its wall time "
             "to `fits.jsonl`, and `narval_resources.py --runs` re-derives "
             "every request from them. If a fit takes under ~1.4 min, the "
             "band arms fit the 3 h bin.")
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
