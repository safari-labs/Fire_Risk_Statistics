# ruff: noqa: E501  (report prose; the PDF, not the source, is read)
"""scripts/make_ecology_report.py

The SAFARI ecology report, one of four (Orbits, RF, Power, Ecology) that support each other
without repeating: what the sensors will measure, what that adds to the Canadian Forest Fire
Danger Rating System (CFFDRS), why these sensors rather than others, and which onboard board
runs the model. It owns those facts; the other reports cite its sections.

    python scripts/make_ecology_report.py   # writes docs/report/SAFARI_ecology_report.pdf

Everything is read from the results packages: the CFFDRS slot table (docs/CFFDRS_CHAIN.md, kept
current there), the value map (docs/results/value_map.csv), the P7 ladder, P12's Mantis-mode and
hardware packages (through make_payload_report's Data), the sensor library
(CubeSat_Sensors_and_Lenses.xlsx, with A-52's corrections), the power model's board results
(../Power_Estimator/results/tables/comm_configs.csv) and the budgets
(../Power_Estimator/results/budgets/budgets.json). The payload and Stage 1 interim reports stay
as they are.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402
from reportlab.lib.pagesizes import letter  # noqa: E402
from reportlab.lib.units import inch  # noqa: E402
from reportlab.platypus import CondPageBreak, SimpleDocTemplate, Spacer  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_payload_report as PR  # noqa: E402

ROOT = PR.ROOT
DOCS = ROOT / "docs"
RESULTS = DOCS / "results"
P12 = RESULTS / "P12"
POWER = ROOT.parent / "Power_Estimator"
OUT = DOCS / "report" / "SAFARI_ecology_report.pdf"
PR.FIG_R = DOCS / "report" / "figures_ecology"
PR.TITLE = TITLE = "SAFARI 3U: what it measures and what that adds to fire danger rating"
DATE = "20 November 2026"
P, bullets, table, figure, boxed = PR.P, PR.bullets, PR.table, PR.figure, PR.boxed
BUDGET_S = 43.0                      # Orbits report §4

MS_BANDS = [("Blue", 480, 69), ("Green", 545, 70), ("Red", 660, 60), ("Panchromatic", 625, 350),
            ("NIR1", 780, 20), ("NIR2", 900, 20)]
SWIR = [("L4", 1213), ("L6", 1557), ("L9", 1599), ("L11", 1674)]

#: the candidate cameras (sensor library rows, A-52's corrections) and the verdict against the criteria
CANDIDATES = [
    ("Dragonfly Mantis MS (6 bands)", "MS, 400–1000 nm", "32 / 32", "6", "0.5", "1", "9",
     "<b>Chosen.</b> Red and NIR in 1U at 6 W; adds the SWIR filters in the same head"),
    ("Dragonfly Mantis, SWIR mode (4 of 12 filters)", "SWIR, 1000–1750 nm", "32 / 32", "with MS", "–", "–", "9",
     "<b>Chosen with MS.</b> A mode of the same head (A-52), imaging with MS through a dichroic"),
    ("Dragonfly Mantis HS (96 bands)", "HS, 470–900 nm", "32 / 32", "6", "0.5", "1", "9",
     "No SWIR; 96 bands to store and process for skill below MS + SWIR"),
    ("Dragonfly Mantis RGB / Gecko RGB", "RGB, 400–700 nm", "16 / 32; 39 / 80–160", "6–7", "0.5", "1", "9",
     "No near-infrared: cannot separate conifer from broadleaf"),
    ("Dragonfly Chameleon MS / HS / SWIR", "MS 11, HS 96, SWIR 4", "10–20 / 11–39", "7–10", "1.6", "2.5", "8–9",
     "2.5U and 1.6 kg: does not fit a 3U with the bus and radios"),
    ("Dragonfly Caiman MS (11 bands)", "MS, 400–1000 nm", "6.5 / 13", "10", "1.4", "3", "9",
     "A whole 3U; 13 km swath halves the revisit"),
    ("CAVU s.LDU.345 (4-band mosaic)", "4 broad bands, 300–1000 nm", "8.7 / 8.7", "10", "2.0", "2", "–",
     "2 kg, 2U; blue and green share one band; 9 km swath"),
    ("nüSpace EMCCD / FLIR Blackfly S", "monochrome, 400–1100 nm", "lens", "3–15", "0.04–1.1", "0.03–1", "–",
     "No bands, no optics, no storage; Blackfly is not space-qualified"),
    ("Raptor OWL 640 M (InGaAs)", "monochrome, 600–1700 nm", "lens", "2.5", "0.17", "0.1", "–",
     "One broad SWIR band; needs a lens and filters; not space-qualified"),
    ("Extended InGaAs to 2.5 µm (generic)", "SWIR to 2500 nm", "lens", "10", "0.8", "0.8", "–",
     "Reaches SWIR2, which adds 0.0025 skill (P12f), at the cost of deep cooling"),
]

SOURCES = [
    "SAFARI Stage 1 band-design study (Fire_Risk_Statistics): the CFFDRS chain and its slots (docs/CFFDRS_CHAIN.md), "
    "its gaps (docs/CFFDRS_GAPS.md), the value map and P7 ladder (docs/results), and P12's Mantis-mode, band, "
    "model-size and hardware packages, run on the Digital Research Alliance of Canada clusters, October–November 2026.",
    "Natural Resources Canada, Canadian Forest Service: The 2025 Update to the FWI System (GLC-X-42); Development and "
    "Structure of the Canadian Forest Fire Behavior Prediction System (ST-X-3) and its 2009 update (GLC-X-10); the "
    "cffdrs R package; the CWFIS issued FWI grids.",
    "NASA ABoVE, AVIRIS-NG surface reflectance over boreal Canada and Alaska; Sentinel-2 Level-2A composites (ESA "
    "Copernicus); SCANFI v2 (Canadian Forest Service) labels.",
    "Dragonfly Aerospace: Mantis datasheet, band tables and SWIR filter catalogue (6 November 2026); the team's "
    "sensor library, CubeSat_Sensors_and_Lenses.xlsx.",
    "Xiphos Q7 and Q8 (XTI-2001-2024-i Rev C) specification sheets and the Q9 product page; TakeMe2Space AICube "
    "technical specifications rev D (10 February 2026) and satsearch listing; NVIDIA Jetson Orin NX module data.",
    "Fire_Risk_FW: FINN and Vitis AI conversions of the onboard model (P12e).",
    "SAFARI hardware cost sheet V1 (team) and the budget sheets SAFARI_CubeSat_Budgets.xlsx.",
]


# ---------------------------------------------------------------- shared with the other three reports
def four_reports_box(this):
    rows = [("Orbits", "where and when SAFARI passes and images, what it collects, when it can be reached"),
            ("RF", "the radio links: rates, reliability while tumbling, antennas, the ground segment and its cost"),
            ("Power", "what each unit draws, the solar arrays, the battery and EPS"),
            ("Ecology", "what the sensors measure, what it adds to CFFDRS, why these sensors and this board")]
    text = "<b>Four SAFARI reports</b> support each other without repeating; each fact is in one of them. " + \
        "; ".join(f"<b>{n}</b>{' (this one)' if n == this else ''}: {t}" for n, t in rows) + "."
    return boxed([P(text, "box")])


def budget_table(B, owner):
    if B is None:
        return [P("The budget sheets have not been built yet (Power_Estimator/scripts/budgets.py).")]
    ids = [b["id"] for b in B["budgets"]]
    rows = []
    for ln in B["lines"]:
        if owner not in (ln.get("owner"), ln.get("qty_owner")):
            continue
        cells = [f"<b>{ln['name']}</b>"]
        for i in ids:
            c = ln["picks"].get(i)
            cells.append("—" if not c else f"{c['item']}, US${c['cost']}<br/>{c.get('perf', '')}")
        rows.append(cells)
    w = (1 - 0.14) / len(ids)
    return [table(["Line", *[b["label"] for b in B["budgets"]]], rows, [0.14] + [w] * len(ids),
                  caption="Budget lines this report backs: the pick in each budget, its price and what it buys.",
                  note="Prices in US$, as the team's sheet. The budgets workbook (SAFARI_CubeSat_Budgets.xlsx) has "
                       "every line and total; the Recommended budget's other lines are backed by the Power and RF "
                       "reports.")]


# ---------------------------------------------------------------- data
def strip_md(s: str) -> str:
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s.strip())
    return s.replace("−", "−")


def slot_table() -> list[list[str]]:
    """The 'Where imagery can enter' table of docs/CFFDRS_CHAIN.md."""
    text = (DOCS / "CFFDRS_CHAIN.md").read_text(encoding="utf-8")
    part = text.split("## Where imagery can enter", 1)[1].split("\n## ", 1)[0]
    rows = []
    for ln in part.splitlines():
        if ln.startswith("| **"):
            c = [strip_md(x) for x in ln.strip().strip("|").split("|")]
            rows.append(c)
    return rows


def value_map() -> list[dict]:
    return list(csv.DictReader((RESULTS / "value_map.csv").open(encoding="utf-8")))


def ladder() -> dict:
    return {r["config"]: r for r in csv.DictReader((RESULTS / "P7" / "p7_slots" / "T_ladder.csv").open(encoding="utf-8"))}


def hw() -> dict:
    return json.loads((P12 / "p12_hw_mantis" / "summary.json").read_text(encoding="utf-8"))


def power_boards() -> pd.DataFrame | None:
    f = POWER / "results" / "tables" / "comm_configs.csv"
    if not f.exists():
        return None
    d = pd.read_csv(f)
    cfg = yaml.safe_load((POWER / "config" / "power.yaml").read_text(encoding="utf-8"))
    R = cfg["report"]
    d = d[(d.orbit == R["orbit"]) & (d.comm == R["comm"])]
    return d.set_index("processor") if "board Wh/day" in d.columns else None


def budgets() -> dict | None:
    f = POWER / "results" / "budgets" / "budgets.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


# ---------------------------------------------------------------- figures
def fig_boards(rows):
    fig, ax = plt.subplots(figsize=(8.4, 3.4))
    PR.style(ax, "Each board: time to process a scene against its power while on")
    offsets = {"Q7 + FINN 32×1": (8, -3), "Q8 + DPU": (8, -3), "TakeMe2Space AICube": (-10, 9),
               "Jetson Orin NX module on SAFARI's own carrier": (-60, -14), "Q9": (8, -3)}
    for name, w, s, measured, colour in rows:
        ax.plot(w, s, "o" if measured else "D", color=colour, ms=7, mec=PR.SURFACE, mew=1.2)
        dx, dy = offsets.get(name, (8, -3))
        lbl = "Orin NX module, own carrier" if name.startswith("Jetson") else name
        ax.annotate(lbl, (w, s), textcoords="offset points", xytext=(dx, dy), fontsize=7.2, color=PR.INK,
                    ha="right" if dx < 0 else "left")
    ax.axhline(BUDGET_S, color=PR.MUTED, lw=0.9, ls="--")
    ax.text(1.6, BUDGET_S * 1.15, f"{BUDGET_S:g} s a scene: the time the orbit leaves (Orbits report §4)",
            fontsize=7.2, color=PR.MUTED)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1.5, 80)
    ax.set_xticks([2, 5, 10, 20, 50], ["2", "5", "10", "20", "50"])
    ax.set_yticks([0.1, 1, 10, 100], ["0.1", "1", "10", "100"])
    ax.minorticks_off()
    ax.set_ylim(0.05, 200)
    ax.set_xlabel("board power while on (W, log scale)")
    ax.set_ylabel("seconds a scene (log scale)")
    ax.plot([], [], "o", color=PR.MUTED, label="measured through the vendor toolchain (P12e)")
    ax.plot([], [], "D", color=PR.MUTED, label="estimated (not measured)")
    ax.legend(loc="lower left", fontsize=7.2, frameon=False)
    return PR.save(fig, "boards.png")


# ---------------------------------------------------------------- report
def build():
    D = PR.Data()
    R, H = D.rows, D.heads
    g_std_swir = D.follow["SWIR on the standard block"]
    g_vnir_vs_swir = D.follow["MS standard alone vs fixed SWIR alone"]
    g_blocks = D.follow["custom vs standard block, both with SWIR"]
    vm = {r["slot"]: r for r in value_map()}
    lad = ladder()
    hws = {(c["inputs"], c["size"]): c for c in hw()["candidates"]}
    pb = power_boards()
    B = budgets()
    pcfg = yaml.safe_load((POWER / "config" / "power.yaml").read_text(encoding="utf-8"))["processors"]
    story = []

    def ci3(lo, hi):
        return f"[{float(lo):+.3f}, {float(hi):+.3f}]"

    # ---- title and summary
    story += [P(TITLE, "title"),
              P("What SAFARI's camera will measure over Canada's forests, what that adds to the Canadian Forest Fire "
                "Danger Rating System, why this camera and these bands rather than others, and which onboard board "
                f"runs the model. From SAFARI's band-design study. {DATE}.", "subtitle"),
              four_reports_box("Ecology"), Spacer(1, 8)]
    story.append(boxed([
        P("<b>SAFARI maps the state of the forest fuel, not its moisture.</b> From each scene it makes four layers "
          "that the Fire Behaviour Prediction System takes as fixed inputs today: percent conifer, canopy closure, "
          "canopy height and fuel family. It does this with the Dragonfly Mantis's standard multispectral block and "
          "four of its SWIR filters, imaged together.", "box"), Spacer(1, 4),
        P(f"Adding the SWIR filters to the multispectral block raises combined skill by "
          f"{g_std_swir['d']:+.3f}, to {R['std_nearest']['mean']:.3f}, close to Sentinel-2's 12 bands "
          f"({R['s2']['mean']:.3f}). The results so far do not show the refreshed structure layers predicting fire "
          "better than the forest inventory they would replace, and the moisture codes stay with the weather; "
          "grass curing is the one input where imagery has helped. A Xiphos Q8 runs the best model in under 0.2 s a "
          f"scene against {BUDGET_S:g} s; the Q7 fits at 2 W with less margin; the Jetson-based AICube on the team's "
          "sheet cannot take the Mantis's data and draws 20–25 W.", "box")]))

    # ---- 1. CFFDRS
    story.append(P("1. What CFFDRS computes and what it cannot see", "h1"))
    story.append(P(
        "CFFDRS rates three processes: ignition, spread, and consumption or intensity. The Fire Weather Index (FWI) "
        "System runs a daily recursion on the 13:00 weather (temperature, humidity, 10 m wind and 24 h rain) to "
        "keep three fuel moisture codes (FFMC, DMC, DC), and combines them with wind into the ISI, BUI and FWI. "
        "The Fire Behaviour Prediction (FBP) System adds the fuel type, slope, aspect, place and date, and a few "
        "fuel descriptors, and predicts rate of spread, fuel consumed and fire intensity. The study implements both "
        "and matches the cffdrs R package to 1 part in 10,000."))
    story.append(P(
        "Every input except the few in Table 1 is weather, terrain or the calendar, which no camera measures. An "
        "imager can only inform the fuel descriptors. Table 1 lists them with what operations use today and what "
        "the study has found."))
    rows = [[r[0], r[2], r[3], r[6]] for r in slot_table()]
    story.append(table(["Input (slot)", "Process", "Source today", "What the study has found"], rows,
                       [0.17, 0.14, 0.27, 0.42],
                       caption="The CFFDRS inputs an imager can inform (the study's slot table, CFFDRS_CHAIN.md).",
                       note="REFUTED: tested against the operational source on real fires and no gain found. Blocked "
                            "or not built: no label or no estimator yet."))
    story.append(P(
        "<b>Where the operational system is weakest.</b> The study's audit lists seven gaps a fuel-condition imager "
        "could address. The fuel-type layer is a fixed vintage, while harvest, insects, fire and regrowth change "
        "the forest (G2). Foliar moisture is computed from place and date, never observed (G1). Weather stations "
        "are sparse over most of the boreal (G3). The season start is keyed to snow-off by a regional rule (G4). "
        "Day-length factors are tabulated for about 46° N (G5). Fire occurrence prediction runs on 20 km cells and "
        "cannot see within them (G6). And a satellite's data arrive a day late, while CFFDRS assumes same-day noon "
        "weather (G7)."))

    # ---- 2. what SAFARI measures
    story.append(CondPageBreak(3 * inch))
    story.append(P("2. What SAFARI will measure", "h1"))
    story.append(P(
        "SAFARI carries one Dragonfly Mantis head looking straight down. Its multispectral pushbroom has six "
        "standard bands; its shortwave-infrared (SWIR) mode takes four of Dragonfly's twelve catalogue filters "
        "through a dichroic on the same aperture, so both image the same ground at the same time, at 32 m and over a "
        "32 km swath from 500 km (Orbits report §2)."))
    story.append(table(
        ["Band", "Centre (nm)", "Width (nm)", "What it carries"],
        [[n, c, w, t] for (n, c, w), t in zip(MS_BANDS, (
            "aerosol and water; blue absorption by chlorophyll", "green reflectance peak",
            "chlorophyll absorption: the red edge's base", "16 m detail for the products' boundaries",
            "canopy structure (near-infrared plateau)", "canopy structure, water vapour side"), strict=True)]
        + [[f"SWIR {n}", c, "Dragonfly catalogue", t] for (n, c), t in zip(SWIR, (
            "liquid water and leaf structure", "leaf water and dry matter", "dry matter and lignin",
            "dry matter; snow and cloud"), strict=True)],
        [0.18, 0.13, 0.17, 0.52], caption="The bands SAFARI flies: Mantis standard multispectral block and four "
                                         "SWIR filters (Dragonfly band tables, A-52)."))
    story.append(P(
        "<b>The products.</b> On board, a small U-Net turns each scene into four fuel layers, the FBP System's "
        "structure inputs: percent conifer, canopy closure, canopy height and a seven-class fuel family. From these "
        "it draws the fire-risk polygons the CUBICS application describes, about 45 kB a scene (Orbits report §4). "
        "Each place is seen every 5 days in bursts at 500 km or about every 40 days at 620 km, clear sky (Orbits "
        "report §3). That suits the slow structure inputs, which change over seasons and years. The fast inputs "
        "(curing, green-up, snow-off) come from Sentinel-2 and the CWFIS products, with SAFARI's imagery for "
        "calibration (A-41)."))

    # ---- 3. what it adds
    story.append(CondPageBreak(3 * inch))
    story.append(P("3. What it adds to CFFDRS, as the results stand", "h1"))
    r0, r1, r2, r4 = (lad[k] for k in ("r0_scanfi", "r1", "r2", "r4"))
    story.append(P(
        "The study scores every option the same way: how well it ranks the places that burned the next day, above "
        "the ones that did not, on 83 fires the models never saw (area under the curve, AUC; 0.5 is chance). It "
        f"compares within a fire's surroundings and between fires. The physics as operations run it scores "
        f"{float(r0['within']):.3f} within and {float(r0['between']):.3f} between. A learned model on the same CFFDRS "
        f"inputs reaches {float(r1['within']):.3f} and {float(r1['between']):.3f}; giving it the imagery as well "
        f"({float(r4['within']):.3f}, {float(r4['between']):.3f}) is no better than without it "
        f"({float(r2['within']):.3f}, {float(r2['between']):.3f}). The FWI that CWFIS actually issued scores 0.857 "
        "between fires, and no model separates from it."))
    order = ["Inventory: CWFIS 2019 for SCANFI", "Percent conifer", "Percent conifer + offset", "Crown base height",
             "Foliar moisture (FMC)", "Curing", "Start-up from S2 snow-off", "Weather 7 days old",
             "Free imagery branch (R4)"]
    rows = []
    for k in order:
        v = vm.get(k)
        if not v:
            continue
        w = f"{float(v['within']):+.3f} {ci3(v['within_lo'], v['within_hi'])}" if v["within"] else "–"
        b = f"{float(v['between']):+.3f} {ci3(v['between_lo'], v['between_hi'])}" if v["between"] else "–"
        rows.append([v["slot"], v["against"], w, b, v["verdict"].capitalize(), v["note"]])
    story.append(table(["Input changed", "Against", "Within a fire's area (AUC)", "Between fires (AUC)", "Verdict",
                        "Note"], rows, [0.2, 0.1, 0.19, 0.19, 0.11, 0.21],
                       caption="What changing each input did to fire prediction (difference in AUC, 95 % interval "
                               "over whole fires; the study's value map).",
                       note="Positive: better than the operational source. An interval that spans zero is no "
                            "measurable difference. R2 is the learned model on CFFDRS inputs."))
    story.append(figure(RESULTS / "figures" / "value_map.png",
                        "Every input tested, as a difference in AUC with its 95 % interval (the study's value map).",
                        3.6 * inch))
    story.append(P("<b>What has been shown.</b>", "h2"))
    story += bullets([
        "<b>Curing helps on grass.</b> Correcting the grass curing with imagery raised the within-area AUC on open "
        f"grass pixels by {float(vm['Curing']['within']):+.3f} {ci3(vm['Curing']['within_lo'], vm['Curing']['within_hi'])}, "
        "the one input where imagery has measurably improved fire prediction. It rests on few fires.",
        "<b>Fresher weather matters more than any fuel layer.</b> Weather 7 days old costs "
        f"{float(vm['Weather 7 days old']['between']):+.3f} between fires. This is why the fire-danger synthesis runs "
        "on the ground with the day's weather, and SAFARI delivers the fuel layers.",
        "<b>Refreshed structure layers have not beaten the inventory yet.</b> Percent conifer, crown base height "
        "and the fuel type from imagery each landed within noise of the inventory they would replace; percent "
        "conifer with an offset was the closest to a gain (SUPPORTED on mixedwood only).",
        "<b>The moisture codes are out of reach.</b> FFMC, DMC and DC are driven by weather and partly lie below the "
        "canopy. No optical sensor reaches them, and foliar moisture from spectra did no better than a "
        "species-by-season mean (P6f).",
    ])
    story.append(P("<b>Where the value is expected, not yet shown.</b> The case for the imager rests on the gaps "
                   "the operational system admits: a fuel map that ages (G2), whose slope against staleness is the "
                   "test the study has registered; and the within-cell distribution of fuel that a 20 km "
                   "occurrence model cannot see (G6). Both need the ecology model trained at full scale, so neither "
                   "is claimed here.", "body"))

    # ---- 4. why these sensors
    story.append(CondPageBreak(3.5 * inch))
    story.append(P("4. Why these sensors", "h1"))
    story.append(P(
        "A camera for SAFARI has to carry the bands the retrieval needs, at a ground sample distance the products "
        "can use, over a swath wide enough to revisit, inside the 3U's volume, mass and power, with flight heritage. "
        "The study measured the first two directly: red edge leads percent conifer, near-infrared leads the fuel "
        "family, and SWIR (Sentinel-2's B12) enters first in 11 of 15 band searches and leads canopy closure in all "
        "15 (P6a); going from 20 to 40 m costs 0.004 AUC (P7i), so 32 m loses almost nothing."))
    story.append(table(
        ["Camera", "Bands", "GSD / swath at 500 km (m / km)", "W", "kg", "U", "TRL", "Against SAFARI's needs"],
        [list(c) for c in CANDIDATES], [0.19, 0.13, 0.13, 0.05, 0.05, 0.05, 0.05, 0.35],
        caption="Every camera in the team's sensor library, against SAFARI's needs.",
        note="Values from the sensor library, corrected by A-52 (the Mantis SWIR mode shares the head's 32 m GSD and "
             "32 km swath). No vendor publishes prices; the team's sheet carries the Mantis at US$60,000.",
        highlight=(0, 1)))
    story.append(P(
        "Among the Mantis modes, the evidence ranks them on the same ground (Figure 2). One chain alone: the "
        f"multispectral block beats the SWIR filters by {g_vnir_vs_swir['d']:+.3f} and is ahead on every product. "
        f"Both together are better than either: {g_std_swir['d']:+.3f} over the multispectral block alone. With SWIR "
        f"present, the custom red-edge block no longer matters ({g_blocks['d']:+.3f}), so the standard block is "
        "flown and no custom filters are bought. Hyperspectral gives all 81 usable channels from 470 to 900 nm but "
        f"no SWIR, and scores {R['hs_all']['mean']:.3f} against {R['std_nearest']['mean']:.3f}. SWIR2 (about "
        "2200 nm), out of reach of standard InGaAs, adds 0.0025 to the best five-band set (P12f)."))
    story.append(figure(PR.fig_modes(D), "Combined skill of each Mantis mode minus the standard multispectral block, "
                                         "paired by fold and seed. Blue: multispectral chain; orange: with SWIR; "
                                         "green: SWIR only; grey: Sentinel-2.", 3.5 * inch))
    story.append(figure(P12 / "p12_bands" / "qual_E-46_band_placement.png",
                        "Where the chosen bands sit against the boreal reflectance spectra (P12 band placement).",
                        3.2 * inch))

    # ---- 5. boards
    story.append(CondPageBreak(4 * inch))
    story.append(P("5. Onboard processing: which board runs the model", "h1"))
    story.append(P(
        "The products are made on board so that only 45 kB a scene has to come down. The model is a compact U-Net; "
        "its best size, 32 channels wide and one or two layers deep, takes 134 to 233 billion operations a scene. "
        "A board must finish each scene within the 43 s the orbit leaves (Orbits report §4), take the Mantis's "
        "LVDS or SpaceWire data, and live within the power and heat of a 3U (Power report §5)."))
    q7 = hws[(16, "32x1")] if (16, "32x1") in hws else None
    rows, pts = [], []
    jet = pcfg["jetson_aicube"]
    cpu = pcfg["cpu_s_per_scene"]

    def energy(key):
        if pb is None or key not in pb.index:
            return "–"
        r = pb.loc[key]
        return f"{r['board Wh/day']:.1f} Wh"

    def scale(key):
        if pb is None or key not in pb.index:
            return "–"
        cfg = yaml.safe_load((POWER / "config" / "power.yaml").read_text(encoding="utf-8"))
        col = f"{cfg['report']['array']}_array_scale_needed"
        return f"×{pb.loc[key][col]:.2f}" if col in pb.columns else "–"

    board_rows = [
        ("Xiphos Q7 + FINN (4-bit), 16 × 1", "xiphos_q7", 34.6, True, "18 % of logic", "0.420",
         "yes (FPGA)", "2", "Q7S in orbit since 2016", "24", SERIES_C[0]),
        ("Xiphos Q7 + FINN (4-bit), 32 × 1", "xiphos_q7", float(q7["finn_fps6_s"]) if q7 else 34.6, True,
         "22 % of logic", f"{float(q7['skill']):.3f}" if q7 else "0.426", "yes (FPGA)", "2", "Q7S in orbit since 2016",
         "24", SERIES_C[0]),
        ("Xiphos Q8 + DPU (8-bit), 32 × 2", "xiphos_q8", float(hws[(16, "32x2")]["dpu_q8_s"]), True,
         "71 % of UltraRAM (DPU core)", f"{float(hws[(16, '32x2')]['skill']):.3f}", "yes (FPGA)", "5 (3.5 earlier "
         "sheet)", "Q8S in orbit since 2020", "64", SERIES_C[1]),
        ("TakeMe2Space AICube (Jetson Orin NX 16 GB)", "jetson_aicube", jet["s_per_scene"], False, "16 GB, ample",
         "as Q8", "no: CAN, USB, Ethernet only", "20 idle, 25 nominal, 55 peak",
         "TRL 8; tantalum shielding, no TID figure", "400", SERIES_C[2]),
        ("Jetson Orin NX module on SAFARI's own carrier", "jetson_orin_nx_15w", pcfg["jetson_orin_nx_15w"]["s_per_scene"],
         False, "16 GB", "as Q8", "only through a bridge to design", "10–25 (power modes)", "none: no such board",
         "–", PR.GREY),
        ("Xiphos Q9 (Versal AI Core)", "xiphos_q9", pcfg["xiphos_q9"]["s_per_scene"], False, "2.3 × the Q8's memory",
         "as Q8", "yes (FPGA)", "30–50", "none published", "–", PR.GREY),
    ]
    for name, key, s, measured, mem, skill, iface, w, heritage, mass, colour in board_rows:
        rows.append([name, f"{s:.2f} s" if s < 1 else f"{s:.1f} s", mem, skill, iface, w, energy(key), scale(key),
                     heritage, mass])
        wv = {"xiphos_q7": 2.0, "xiphos_q8": 5.0, "jetson_aicube": 25.0, "jetson_orin_nx_15w": 15.0,
              "xiphos_q9": 30.0}[key]
        if name.endswith("16 × 1"):
            continue
        pts.append((name.split(" (")[0].replace("Xiphos ", "") + (" 32×1" if "32 × 1" in name else ""),
                    wv, s + cpu * 0, measured, colour))
    story.append(table(
        ["Board and model", "Time a scene", "Memory used", "Skill", "Takes the Mantis's data", "Power on (W)",
         "Energy a day", "Array needed", "Heritage", "g"], rows,
        [0.17, 0.07, 0.1, 0.06, 0.12, 0.1, 0.08, 0.07, 0.14, 0.05],
        caption="The board configurations compared (P12e conversions; vendor sheets; the power model).",
        note="Time a scene: the network alone, plus about 1 s of ARM-side work on every board (power.yaml). The "
             "Jetson times are estimates: the model's operations on the Orin NX's GPU at 30 TOPS (8-bit, dense) and "
             "5 % use. Energy a day and the array needed are the power model's, with the Recommended radios; "
             "an array needed above ×1 means the arrays fall short (Power report §5).",
        highlight=(2,)))
    story.append(figure(fig_boards(pts), "Time a scene against power while on. Dashed: the 43 s each scene may take. "
                                         "Circles: converted through the vendor toolchain; diamonds: estimated.",
                        3.2 * inch))
    aic_txt = scale("jetson_aicube").replace("×", "×") + " as large as the DROP-03X arrays, against " +         scale("xiphos_q8") + " with the Q8"
    story += bullets([
        "<b>Xiphos Q8.</b> Runs the best model in under 0.2 s a scene, 200 times inside the budget, through a mature "
        "toolchain. The default DPU build uses 82 % of its block RAM, so the UltraRAM build is the one to fly. 5 W "
        "for about two minutes a pass.",
        "<b>Xiphos Q7.</b> Runs the best size within the budget (34.6 s a scene) at 2 W, but stays on for about "
        "45 minutes a pass, with the Mantis reading out all that time unless the pass is first copied to the "
        "board's storage. Its fit is an estimate until a full Vivado build.",
        f"<b>AICube (the team's sheet).</b> Fast enough many times over, but it has no LVDS or SpaceWire input for "
        "the Mantis, its 25 W nominal is more than the NanoEPS's 12 V rail gives (24 W), and its thermal design "
        f"assumes a 6U side plate. On the power model it would need the arrays {aic_txt} (Power report §5).",
        "<b>A bare Orin NX module or the Q9</b> would need a carrier SAFARI designs itself, or 30–50 W: neither fits "
        "a 3U.",
    ])

    # ---- 6. product accuracy
    story.append(P("6. Expected product accuracy", "h1"))
    story.append(table(
        ["Product", "Multispectral only", "Multispectral + SWIR", "Checked in orbit against"],
        [["Percent conifer (RMSE, points)", f"{H['ms_std']['pc']:.1f}", f"{H['std_nearest']['pc']:.1f}",
          "national forest-inventory maps and plots"],
         ["Canopy closure (RMSE, points)", f"{H['ms_std']['closure']:.1f}", f"{H['std_nearest']['closure']:.1f}",
          "national forest-inventory maps and plots"],
         ["Canopy height (RMSE, m)", f"{H['ms_std']['height']:.2f}", f"{H['std_nearest']['height']:.2f}",
          "inventory maps; ICESat-2 canopy heights"],
         ["Fuel family (balanced accuracy, chance 0.17)", f"{H['ms_std']['family']:.2f}",
          f"{H['std_nearest']['family']:.2f}", "inventory maps; the CWFIS fuel-type map"]],
        [0.34, 0.15, 0.17, 0.34],
        caption="Expected accuracy of the onboard fuel layers (AVIRIS-NG over boreal Canada and Alaska, Mantis "
                "bands, with sensor noise).",
        note="The sensor noise is a placeholder until Dragonfly publishes per-band SNR; the labels are themselves "
             "mapped from Landsat, so their own error is inside every RMSE."))

    # ---- 7. budget
    story.append(P("7. Budget lines this report backs", "h1"))
    story.append(P(
        "The camera is the same in every budget: the Mantis's standard multispectral block with four SWIR filters, "
        "the configuration section 4 supports, at the team's US$60,000. The board follows each budget's processing "
        "requirement (section 5): the Lean budget's 43 s allows the Q7; the Recommended budget's margin of two and "
        "the High performance budget's real time need the Q8."))
    story += budget_table(B, "Ecology")

    # ---- 8. trust and sources
    story.append(P("8. How far to trust these numbers", "h1"))
    story += bullets([
        "<b>Solid.</b> The ranking of the Mantis modes, and the comparisons with CFFDRS: every one is paired over "
        "whole fires or 15 fits on ground the models never saw.",
        "<b>Depends on a measurement.</b> Absolute accuracy depends on the Mantis's real signal-to-noise ratio; the "
        "board times are conversions through the vendor toolchains, not runs on hardware; the Jetson's are estimates.",
        "<b>The value of fresher fuel maps</b> is argued from the operational system's own gaps; the test of it "
        "needs the full ecology model.",
    ])
    story.append(P("Sources", "h2"))
    story += bullets(SOURCES)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUT), pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=0.75 * inch, bottomMargin=0.85 * inch, title=TITLE, author="SAFARI, ÉTS LASSENA")
    doc.build(story, onFirstPage=PR.on_page, onLaterPages=PR.on_page)
    print(f"wrote {OUT}")


SERIES_C = PR.SERIES

if __name__ == "__main__":
    build()
