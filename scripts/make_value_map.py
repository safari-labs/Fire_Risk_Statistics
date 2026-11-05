"""scripts/make_value_map.py

The value map (plan P11): every CFFDRS input slot, the processes it feeds, and
what substituting it changed, from the summaries the phase packages saved. A
slot no run has reached is drawn as such, with its blocker, so the gaps are
visible next to the results.

Each row is a paired difference in AUC, a minus b on the same folds and seeds,
with the phase's bootstrap 95 % CI over whole fires. Within-patch AUC is where
a fuel slot can show; between-patch AUC is where weather can. Filled markers
are the slot against its reference; hollow markers are the slot's
shuffled-imagery twin against the same reference, which should sit on zero.
Every number is Reconstructed (ours). Verdicts come from
src/safari_bands/phases.py, newest first.

Reads docs/results/<phase>/summary.json only: nothing is trained or rescored.

    python scripts/make_value_map.py

Writes docs/results/figures/value_map.png, docs/results/value_map.md and
docs/results/value_map.csv.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_results_package as R  # noqa: E402
from make_phase_docs import VERDICT_COLOUR, VERDICT_INK  # noqa: E402

from safari_bands.outputs import latest_verdict  # noqa: E402

ROOT = R._ROOT
RESULTS = ROOT / "docs" / "results"
PNG = RESULTS / "figures" / "value_map.png"
MD, CSV = RESULTS / "value_map.md", RESULTS / "value_map.csv"

PROCESSES = (("I", "ignition"), ("S", "spread"), ("X", "intensity"))


def _summary(folder: str) -> dict:
    return json.loads((RESULTS / folder / "summary.json").read_text())


def _pair(rows, a, b, **match):
    for r in rows:
        if r["a"] == a and r["b"] == b and all(r.get(k) == v for k, v in match.items()):
            return r
    raise KeyError(f"{a} - {b} {match}")


def p7(kind: str, a: str, b: str = "r2") -> dict:
    """A contrast from the first slot sweep: within and between."""
    r = _pair(_summary("p7_slots")[kind], a, b)
    return {"within": (r["d_within"], *r["d_within_ci"]),
            "between": (r["d_between"], *r["d_between_ci"]), "n_fire": r["n_fire"]}


def p7c(kind: str, a: str, b: str, fam: str) -> dict:
    """A contrast from the second slot sweep, on one fuel family's pixels: within only."""
    r = _pair(_summary("p7c_slots_v3")[kind], a, b, fam=fam)
    return {"within": (r["d"], *r["ci"]), "between": None, "n_fire": r["n_fire"]}


def p6d(variant: str, code: str) -> dict:
    """E-18: R0's between-patch AUC with the imagery start-up minus the ERA5 rule, >= 55 N."""
    r = _summary("p6d_startup")["falsifier"]["north"][variant]["auc_minus_c2"][code]
    return {"within": None, "between": (r["d"], *r["ci"]), "n_patch": r["n"]}


#: (group, slot, processes fed, source form, reference, refs, estimate, twin, note).
#: refs[0] gives the verdict. estimate and twin are callables so a missing
#: summary fails loudly here rather than drawing an empty row.
ROWS = (
    ("Fuel", "Fuel type", "ISX", "imagery_replace", "R2", ("E-35",), None, None,
     "not run: needs eco_v3, then the E-35 sweep (A-45)"),
    ("Fuel", "Inventory: CWFIS 2019 for SCANFI", "ISX", "cffdrs swap", "R0, SCANFI", ("E-33",),
     lambda: p7("contrasts", "r0_cwfis", "r0_scanfi"), None, "physics only"),
    ("Fuel", "Percent conifer", "SX", "imagery_correct", "R2", ("E-36",),
     lambda: p7("slots", "r3_pc"), lambda: p7("twins", "r3_pc_shuffled"), "all pixels"),
    ("Fuel", "Percent conifer + offset", "SX", "imagery_correct", "R2", ("E-57",),
     lambda: p7c("offset", "r3_pc_offset", "r2", "M"),
     lambda: p7c("offset", "r3_pc_offset_shuffled", "r2", "M"), "M-1/M-2 pixels"),
    ("Fuel", "Canopy closure, in-stand FFMC", "I", "imagery_replace", "R2", ("E-39",), None, None,
     "not run: in-stand adjustment not coded"),
    ("Fuel", "Crown base height", "X", "imagery_correct", "R2", ("E-37",),
     lambda: p7("slots", "r3_cbh"), lambda: p7("twins", "r3_cbh_shuffled"), "all pixels"),
    ("Live fuel", "Foliar moisture (FMC)", "X", "imagery_correct", "R2", ("E-15",),
     lambda: p7("slots", "r3_fmc"), lambda: p7("twins", "r3_fmc_shuffled"),
     "no measured LFMC (E-16, E-29)"),
    ("Live fuel", "Curing", "IS", "imagery_correct", "R2, CWFIS fuel", ("E-38",),
     lambda: p7c("curing", "r3_curing_cwfis", "r2_cwfis", "O"),
     lambda: p7c("curing", "r3_curing_cwfis_shuffled", "r2_cwfis", "O"), "O-1 pixels"),
    ("Live fuel", "Green-up from imagery", "IS", "imagery_replace", "R2", ("E-40",), None, None,
     "not run: S2 phenology estimator not built"),
    ("Live fuel", "Leaf state forced green", "IS", "ablated", "R2", ("P7-M2",),
     lambda: p7("slots", "r2_leaf_ablated"), None, "bounds E-40"),
    ("Live fuel", "Start-up from S2 snow-off", "ISX", "imagery_replace", "R0, ERA5 rule",
     ("E-18",), lambda: p6d("c2_s2_all", "fwi"), None, "FWI, patches >= 55 N"),
    ("Weather", "Weather 7 days old", "ISX", "cffdrs, aged", "R2", ("E-20",),
     lambda: p7("slots", "r2_lag7"), None, "bounds any onboard product"),
    ("Weather", "Station weather for ERA5", "ISX", "cffdrs swap", "R2", ("P7-M2", "E-52"),
     lambda: p7("slots", "r2_station"), None, "nearest CWFIS station"),
    ("All imagery", "Free imagery branch (R4)", "ISX", "free branch", "R2", ("P7-M1",),
     lambda: p7("slots", "r4"), lambda: p7("twins", "r4_shuffled"), "upper bound on slots"),
)


def resolve() -> list[dict]:
    out = []
    for group, slot, feeds, form, ref, refs, est, twin, note in ROWS:
        e = est() if est else None
        t = twin() if twin else None
        # scored by a run but given no verdict by any phase (FMC in P7)
        none = "NO VERDICT" if e else "NOT RUN"
        out.append({"group": group, "slot": slot, "feeds": feeds, "form": form, "ref": ref,
                    "refs": refs, "verdict": latest_verdict(refs[0]) or none,
                    "est": e, "twin": t, "note": note})
    return out


def _ladder() -> list[tuple[str, float, float]]:
    rows = {r["config"]: r for r in _summary("p7_slots")["ladder"]}
    names = (("R0", "r0_scanfi"), ("R1", "r1"), ("R2", "r2"), ("R4", "r4"))
    return [(n, rows[c]["within"], rows[c]["between"]) for n, c in names]


def _stage_b() -> dict:
    return _summary("p8a_spread")


def figure(rows: list[dict]) -> None:
    plt = R._plt()
    groups = []
    for r in rows:
        if r["group"] not in groups:
            groups.append(r["group"])
    # y positions top-down, a header line before each group
    y, ys, heads = 0.0, [], []
    for g in groups:
        heads.append((g, y))
        y += 1.0
        for r in rows:
            if r["group"] == g:
                ys.append(y)
                y += 1.0
        y += 0.35
    order = [r for g in groups for r in rows if r["group"] == g]
    h = 0.34 * y + 2.2
    fig = plt.figure(figsize=(15.5, h), facecolor=R.FIG_BG)
    gs = fig.add_gridspec(1, 3, width_ratios=(7.4, 3.6, 3.6), wspace=0.06,
                          left=0.01, right=0.99, top=1 - 0.75 / h, bottom=1.25 / h)
    tab, aw, ab = (fig.add_subplot(gs[0, i]) for i in range(3))
    for ax in (tab, aw, ab):
        ax.set_ylim(y - 0.4, -1.2)
        ax.set_facecolor(R.FIG_BG)
    tab.set_xlim(0, 1)
    tab.axis("off")

    cols = {"slot": 0.0, "I": 0.365, "S": 0.395, "X": 0.425, "form": 0.46, "ref": 0.615,
            "verdict": 0.765}
    for k, label in (("slot", "slot"), ("form", "source form"), ("ref", "against"),
                     ("verdict", "experiment, verdict")):
        tab.text(cols[k], -0.75, label, color=R.MUTED, fontsize=8, va="center")
    for k, _ in PROCESSES:
        tab.text(cols[k], -0.75, k, color=R.MUTED, fontsize=8, va="center", ha="center")
    tab.text(cols["I"] - 0.012, -1.15, "  ".join(f"{k} {w}" for k, w in PROCESSES),
             color=R.MUTED, fontsize=6.5, va="center")
    for g, gy in heads:
        tab.text(0.0, gy, g.upper(), color=R.INK_BRIGHT, fontsize=8.5, va="center",
                 fontweight="bold")
        for ax in (aw, ab):
            ax.axhline(gy + 0.5, color=R.SPINE, lw=0.6)

    for r, yy in zip(order, ys, strict=True):
        tab.text(cols["slot"] + 0.012, yy, r["slot"], color=R.INK, fontsize=8.5, va="center")
        tab.text(cols["slot"] + 0.012, yy + 0.36, r["note"], color=R.MUTED, fontsize=6.3,
                 va="center")
        for k, _ in PROCESSES:
            on = k in r["feeds"]
            tab.plot(cols[k], yy, "o", ms=6, mfc=R.INK if on else "none",
                     mec=R.INK if on else R.SPINE, mew=1.0)
        tab.text(cols["form"], yy, r["form"], color=R.INK, fontsize=7.8, va="center")
        tab.text(cols["ref"], yy, r["ref"], color=R.MUTED, fontsize=7.8, va="center")
        v = r["verdict"]
        tab.text(cols["verdict"], yy, " / ".join(r["refs"]), color=R.INK, fontsize=7.8,
                 va="center")
        tab.text(cols["verdict"] + 0.115, yy, f" {v} ", fontsize=7, va="center",
                 color=VERDICT_INK.get(v, R.INK_BRIGHT),
                 bbox={"boxstyle": "round,pad=0.25", "lw": 0,
                       "fc": VERDICT_COLOUR.get(v, R.SPINE)})

    for ax, key, title in ((aw, "within", "within-patch AUC, a - b"),
                           (ab, "between", "between-patch AUC, a - b")):
        R._axes(ax, title, "", "")
        ax.set_yticks([])
        ax.axvline(0, color=R.MUTED, lw=0.8)
        ax.grid(axis="x", color=R.SPINE, lw=0.5)
        ax.spines["left"].set_visible(False)
        for r, yy in zip(order, ys, strict=True):
            e = r["est"][key] if r["est"] else None
            t = r["twin"][key] if r["twin"] and r["twin"].get(key) else None
            if e is None:
                text = "not run" if r["est"] is None else "not scored"
                ax.text(0, yy, text, color=R.MUTED, fontsize=7, va="center", ha="center",
                        style="italic")
                continue
            ax.plot([e[1], e[2]], [yy, yy], color=R.BLUE, lw=2, solid_capstyle="round")
            ax.plot(e[0], yy, "o", ms=6.5, color=R.BLUE, mec=R.FIG_BG, mew=1.5)
            if t:
                ax.plot([t[1], t[2]], [yy + 0.3, yy + 0.3], color=R.MUTED, lw=1.2)
                ax.plot(t[0], yy + 0.3, "o", ms=5, mfc=R.FIG_BG, mec=R.MUTED, mew=1.2)
    lim = max(abs(v) for r in order for k in ("within", "between")
              for s in (r["est"], r["twin"]) if s and s.get(k) for v in s[k][1:])
    from matplotlib.ticker import MultipleLocator
    step = 0.05 if lim > 0.06 else 0.02
    for ax in (aw, ab):
        ax.set_xlim(-lim * 1.1, lim * 1.1)
        ax.xaxis.set_major_locator(MultipleLocator(step))
        ax.tick_params(axis="x", labelsize=7.5)
    ab.plot([], [], "o", color=R.BLUE, label="slot vs reference")
    ab.plot([], [], "o", mfc=R.FIG_BG, mec=R.MUTED, label="shuffled twin vs reference")
    ab.legend(loc="upper left", fontsize=7, facecolor=R.AX_BG, edgecolor=R.SPINE,
              labelcolor=R.INK)

    lad = "   ".join(f"{n} {w:.3f} / {b:.3f}" for n, w, b in _ladder())
    sb = _stage_b()
    rho, ci = sb["all"]["rho"], sb["ci"]["rho"]
    fig.text(0.01, 0.98 - 0.15 / h, "Value of imagery per CFFDRS input, from the runs so far",
             color=R.INK_BRIGHT, fontsize=12, va="top")
    R._caption(fig, (
        f"Stage A (NBAC burned pixels, {order[2]['est']['n_fire']} development fires), ladder "
        f"within / between: {lad}. "
        f"Stage B (CFSDS spread, E-41): R0 Spearman {rho:.2f} [{ci[0]:.2f}, {ci[1]:.2f}] on "
        f"{sb['all']['rows']:,} fire-days of {sb['all']['fires']} fires; no slot run yet (E-42). "
        "Stage C (ignition, E-44, E-45): data being built. Each row is a paired difference "
        "on the same folds, with the phase's bootstrap 95 % CI over whole fires; the start-up "
        "row is R0 on 113 patches. All values Reconstructed (ours); the test sets were not "
        "read."), y=1.05 / h)
    PNG.parent.mkdir(parents=True, exist_ok=True)
    R._save(fig, PNG.parent, PNG.name)


def _fmt(e) -> str:
    return "" if not e else f"{e[0]:+.4f} [{e[1]:+.4f}, {e[2]:+.4f}]"


def tables(rows: list[dict]) -> None:
    fields = ("group", "slot", "feeds", "form", "against", "refs", "verdict", "within",
              "within_lo", "within_hi", "between", "between_lo", "between_hi", "twin_within",
              "twin_within_lo", "twin_within_hi", "note")
    with CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(fields)
        for r in rows:
            def trip(s, k):
                return list(s[k]) if s and s.get(k) else ["", "", ""]
            w.writerow([r["group"], r["slot"], r["feeds"], r["form"], r["ref"],
                        " ".join(r["refs"]), r["verdict"], *trip(r["est"], "within"),
                        *trip(r["est"], "between"), *trip(r["twin"], "within"), r["note"]])
    L = ["# Value map: what each CFFDRS input slot changed",
         "",
         "Generated by `scripts/make_value_map.py` from the phase summaries; do not edit. "
         "Paired differences a - b in AUC with the phase's bootstrap 95 % CI over whole fires. "
         "All values Reconstructed (ours).",
         "",
         "![value map](figures/value_map.png)",
         "",
         "| group | slot | feeds | source form | against | experiment | verdict | within-patch "
         "| between-patch | shuffled twin, within | note |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        tw = _fmt(r["twin"]["within"]) if r["twin"] else ""
        L.append(f"| {r['group']} | {r['slot']} | {r['feeds']} | {r['form']} | {r['ref']} | "
                 f"{', '.join(r['refs'])} | {r['verdict']} | "
                 f"{_fmt(r['est']['within']) if r['est'] else 'not run'} | "
                 f"{_fmt(r['est']['between']) if r['est'] else ''} | {tw} | {r['note']} |")
    L += ["", "Feeds: I ignition, S spread, X intensity."]
    MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"  wrote {R._rel(MD)}, {R._rel(CSV)}")


def main() -> int:
    rows = resolve()
    figure(rows)
    tables(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
