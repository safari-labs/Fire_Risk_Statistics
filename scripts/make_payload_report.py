"""scripts/make_payload_report.py

PDF report on SAFARI's payload evidence: which Dragonfly Mantis mode and bands to fly
(VNIR, SWIR or both), how large the onboard model must be, which Xiphos board it fits,
and how accurate the fuel products are expected to be. A companion to the EO coverage
report (EO_Simulation) and the RF antenna report (RF_RadiationPattern_Simulator), with
the same layout, to supplement the CUBICS 2026 application.

    python scripts/make_payload_report.py   # writes docs/report/SAFARI_payload_report.pdf

Every number is read from the committed results packages (docs/results/P12/...) and the
narval_results runs they cite; hardware figures are from the vendor datasheets.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import letter  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import inch  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.platypus import Image as RLImage  # noqa: E402
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_sensor_options as SO  # noqa: E402
from make_band_options import paired  # noqa: E402

from safari_bands.config.loader import project_root  # noqa: E402

ROOT = project_root()
RES = ROOT / "docs" / "results" / "P12"
NR = ROOT / "narval_results"
SENSORS_V1 = NR / "sensors_v1" / "20261106-1218"
SENSORS_FIXED = NR / "sensors_fixed" / "20261106-1645"
OUT = ROOT / "docs" / "report" / "SAFARI_payload_report.pdf"
FIG_R = ROOT / "docs" / "report" / "figures_payload"
TITLE = "SAFARI 3U: spectral bands, onboard model and expected product quality"
DATE = "9 November 2026"

SURFACE, INK, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#e1e0d9", "#c3c2b7"
SERIES = ("#2a78d6", "#eb6834", "#1baf7a")          # VNIR, VNIR + SWIR, SWIR (as the RF/EO reports)
RULE, HEAD, PICK = "#d9d8d4", "#eef3fb", "#fdf1e9"
GREY = "#9a998f"

SOURCES = [
    "SAFARI Stage 1 band-design study (this repository): results packages P12/p12_sensors "
    "(Mantis modes, runs sensors_v1 and sensors_fixed), P12/p12_bands (Sentinel-2 and AVIRIS-NG "
    "band "
    "consensus), P12/p12_arch (onboard model size), P12/p12_convert (FPGA conversion), all run on "
    "the "
    "Digital Research Alliance of Canada clusters (Narval, Nibi), November 2026.",
    "NASA ABoVE airborne campaign, AVIRIS-NG surface reflectance over boreal Canada and Alaska (5 "
    "nm "
    "sampling, 377–2496 nm), convolved to each candidate band set.",
    "Sentinel-2 Level-2A surface reflectance, summer 2020 median composites (ESA Copernicus).",
    "SCANFI v2 (Canadian Forest Service), 30 m maps of species crown closure, canopy closure and "
    "height "
    "for 2020, used as the training and test labels.",
    "Dragonfly Aerospace, Mantis datasheet, band tables and SWIR filter catalogue (6 November "
    "2026).",
    "Xiphos, Q7 specification sheet and Q8 specification sheet XTI-2001-2024-i Rev C (13 August "
    "2026).",
    "SAFARI 3U: Earth observation coverage, resolution and revisit (EO coverage report), and "
    "SAFARI 3U: "
    "the lowest-cost antennas for guaranteed contact (RF antenna report).",
    "SAFARI CUBICS 2026 application (draft): mission, objectives, products and schedule.",
]

# ---------------------------------------------------------------- styles (as the EO and RF reports)
FONT_DIR = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
for name, file in (("DV", "DejaVuSans"), ("DV-B", "DejaVuSans-Bold"),
                   ("DV-I", "DejaVuSans-Oblique"),
                   ("DV-BI", "DejaVuSans-BoldOblique")):
    pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / f"{file}.ttf")))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-BI")


def _style(name, font="DV", size=9.0, lead=13.0, color=INK, **kw):
    return ParagraphStyle(name, fontName=font, fontSize=size, leading=lead, textColor=color, **kw)


S = {"title": _style("title", "DV-B", 19, 24, spaceAfter=6),
     "subtitle": _style("subtitle", size=10.5, lead=14.5, color=MUTED, spaceAfter=12),
     "h1": _style("h1", "DV-B", 13.5, 18, spaceBefore=10, spaceAfter=6, keepWithNext=1),
     "h2": _style("h2", "DV-B", 10.5, 14, spaceBefore=7, spaceAfter=4, keepWithNext=1),
     "body": _style("body", spaceAfter=5),
     "bullet": _style("bullet", leftIndent=12, bulletIndent=2, spaceAfter=2),
     "caption": _style("caption", "DV-I", 8, 11, color=MUTED, spaceBefore=3, spaceAfter=10),
     "cell": _style("cell", size=7.5, lead=9.5),
     "cellb": _style("cellb", "DV-B", 7.5, 9.5),
     "note": _style("note", size=7.5, lead=10, color=MUTED, spaceAfter=8),
     "box": _style("box", size=9.5, lead=13.5)}
WIDTH = letter[0] - 1.5 * inch
_fig, _tab = [0], [0]


def P(text, style="body"):
    return Paragraph(text, S[style])


def bullets(items):
    return [Paragraph(t, S["bullet"], bulletText="•") for t in items]


def figure(path: Path, caption: str, max_h=7.4 * inch):
    _fig[0] += 1
    w, h = Image.open(path).size
    width, height = WIDTH, WIDTH * h / w
    if height > max_h:
        height, width = max_h, max_h * w / h
    return KeepTogether([RLImage(str(path), width=width, height=height),
                         P(f"Figure {_fig[0]}. {caption}", "caption")])


def table(header, rows, widths, caption=None, note=None, highlight=()):
    _tab[0] += 1
    data = [[Paragraph(h, S["cellb"]) for h in header]]
    data += [[c if isinstance(c, Paragraph) else Paragraph(str(c), S["cell"]) for c in r]
             for r in rows]
    t = Table(data, colWidths=[w * WIDTH for w in widths], repeatRows=1)
    st = [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(HEAD)),
          ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor(MUTED)),
          ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.HexColor(RULE)),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
          ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]
    for r in highlight:
        st.append(("BACKGROUND", (0, r + 1), (-1, r + 1), colors.HexColor(PICK)))
    t.setStyle(TableStyle(st))
    out = [P(f"<b>Table {_tab[0]}.</b> {caption}")] if caption else []
    out += [t, Spacer(1, 3), P(note, "note")] if note else [t, Spacer(1, 8)]
    return KeepTogether(out)


def boxed(flowables):
    t = Table([[flowables]], colWidths=[WIDTH])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(PICK)),
                           ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#eb6834")),
                           ("LEFTPADDING", (0, 0), (-1, -1), 9),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                           ("TOPPADDING", (0, 0), (-1, -1), 7),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return t


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("DV", 7.5)
    canvas.setFillColor(colors.HexColor(MUTED))
    canvas.drawString(0.75 * inch, 0.5 * inch, TITLE)
    canvas.drawRightString(letter[0] - 0.75 * inch, 0.5 * inch, f"{doc.page}")
    canvas.setStrokeColor(colors.HexColor(RULE))
    canvas.line(0.75 * inch, 0.62 * inch, letter[0] - 0.75 * inch, 0.62 * inch)
    canvas.restoreState()


def style(ax, title=""):
    ax.set_facecolor(SURFACE)
    if title:
        ax.set_title(title, loc="left", fontsize=9.5, color=INK)
    ax.grid(True, color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED, labelsize=8, length=0)
    for side, spine in ax.spines.items():
        spine.set_visible(side in ("left", "bottom"))
        spine.set_color(AXIS)
    for lab in (ax.xaxis.label, ax.yaxis.label):
        lab.set_color(MUTED)
        lab.set_size(9)


def save(fig, name):
    FIG_R.mkdir(parents=True, exist_ok=True)
    fig.patch.set_facecolor(SURFACE)
    path = FIG_R / name
    fig.savefig(path, dpi=170, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return path


# ---------------------------------------------------------------- data
#: The Mantis configurations compared (sensors_v1 / sensors_fixed / hs_v4 keys), with the
#: chain they need: "vnir", "swir" or "both".
MODES = [
    ("rgb", "RGB snapshot", "vnir"),
    ("ms_std", "VNIR, standard filter block", "vnir"),
    ("ms_custom", "VNIR, custom red-edge block", "vnir"),
    ("hs_all", "VNIR hyperspectral, all 81 channels", "vnir"),
    ("hs_select6", "VNIR hyperspectral, 6 chosen in orbit", "vnir"),
    ("swir_nearest_alone", "SWIR alone, 4 standard filters", "swir"),
    ("std_nearest", "VNIR standard + 4 SWIR filters", "both"),
    ("custom_nearest", "VNIR custom + 4 SWIR filters", "both"),
    ("s2", "Sentinel-2, 12 bands (reference)", "ref"),
]
CHAIN_COLOUR = {"vnir": SERIES[0], "both": SERIES[1], "swir": SERIES[2], "ref": GREY}
#: eval.jsonl set names, for the per-target errors.
EVAL_SET = {"ms_std": "dfa_ms_standard", "ms_custom": "sensor_mantis_vnir6",
            "swir_nearest_alone": "dfa_swir_nearest_alone", "std_nearest": "dfa_standard_nearest",
            "custom_nearest": "dfa_custom_nearest", "s2": "sentinel2_p6_12band",
            "rgb": "dfa_rgb", "hs_all": "dfa_hs_all"}


def per_target() -> dict:
    """Mean per-target error over the 15 tasks (raw + indices, with noise)."""
    acc: dict[str, list] = {}
    for run in (SENSORS_V1 / "references", SENSORS_FIXED / "references"):
        for f in run.glob("f*s*/eval.jsonl"):
            for line in f.read_text(encoding="utf-8").splitlines():
                r = json.loads(line)
                if r["mode"] == "raw+indices" and r["noisy"] and r["metrics"]:
                    acc.setdefault(r["set"], []).append(r["metrics"])
    out = {}
    for key, name in EVAL_SET.items():
        ms = acc.get(name, [])
        if ms:
            ms = ms[:15]
            out[key] = {"pc": np.mean([m["rmse_pc"] for m in ms]),
                        "closure": np.mean([m["rmse_closure"] for m in ms]),
                        "height": np.mean([m["rmse_height"] for m in ms]),
                        "family": np.mean([m["balanced_acc_family"] for m in ms]),
                        "n": len(ms)}
    return out


class Data:
    def __init__(self):
        res = SO.build(SENSORS_V1, SENSORS_FIXED)
        self.rows = {r["key"]: r for r in res["rows"]}
        self.follow = {f["contrast"]: f for f in res["followup"]}
        self.heads = per_target()
        self.arch = json.loads((RES / "p12_arch" / "summary.json").read_text(encoding="utf-8"))
        self.s2 = list(csv.DictReader((RES / "p12_bands" / "T_options_s2.csv").open(
            encoding="utf-8")))

    def gap(self, a, b):
        d, se, n = paired(self.rows[a]["per"], self.rows[b]["per"])
        return d, se


def ci(d, se):
    return f"{d:+.3f} [{d - 1.96 * se:+.3f}, {d + 1.96 * se:+.3f}]"


# ---------------------------------------------------------------- figures
def fig_modes(D: Data):
    keys = [k for k, _, _ in MODES if k in D.rows and D.rows[k].get("per") and k != "ms_std"]
    fig, ax = plt.subplots(figsize=(8.6, 3.9))
    style(ax, "Combined skill of each Mantis mode, against the VNIR standard block")
    for i, k in enumerate(keys[::-1]):
        chain = next(c for kk, _, c in MODES if kk == k)
        d, se = D.gap(k, "ms_std")
        c = CHAIN_COLOUR[chain]
        ax.plot([d - 1.96 * se, d + 1.96 * se], [i, i], color=c, lw=2.2, solid_capstyle="butt")
        ax.plot(d, i, "o", color=c, ms=6.5, mec=SURFACE, mew=1.2)
        ax.text(max(d + 1.96 * se, 0) + 0.004, i, f"{d:+.3f}", va="center", fontsize=7.5,
                color=MUTED)
    ax.axvline(0, color=AXIS, lw=1.2)
    ax.set_yticks(range(len(keys)), [next(lbl for kk, lbl, _ in MODES if kk == k)
                                     for k in keys[::-1]])
    ax.set_xlabel("difference in combined skill from the VNIR standard block "
                  "(paired by fold and seed, 95 % CI)")
    for chain, lbl in (("vnir", "VNIR chain"), ("both", "VNIR + SWIR"), ("swir", "SWIR chain"),
                       ("ref", "reference")):
        ax.plot([], [], "o", color=CHAIN_COLOUR[chain], label=lbl)
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.17), ncol=4, fontsize=7.5,
              frameon=False)
    return save(fig, "modes.png")


def fig_heads(D: Data):
    order = [("swir_nearest_alone", "SWIR alone", SERIES[2]),
             ("ms_std", "VNIR standard", SERIES[0]),
             ("std_nearest", "VNIR std + SWIR", SERIES[1]),
             ("s2", "Sentinel-2 (12)", GREY)]
    panels = [("pc", "Percent conifer, RMSE (points)"),
              ("closure", "Canopy closure, RMSE (points)"),
              ("height", "Canopy height, RMSE (m)"), ("family", "Fuel family, balanced accuracy")]
    fig, axes = plt.subplots(1, 4, figsize=(10, 2.9))
    for ax, (h, title) in zip(axes, panels, strict=True):
        style(ax, title)
        vals = [D.heads[k][h] for k, _, _ in order]
        ax.bar(range(len(order)), vals, color=[c for _, _, c in order], width=0.7)
        for i, v in enumerate(vals):
            ax.text(i, v, f"{v:.2f}" if h in ("height", "family") else f"{v:.1f}", ha="center",
                    va="bottom", fontsize=7, color=INK)
        ax.set_xticks(range(len(order)), [lbl for _, lbl, _ in order], rotation=30, ha="right",
                      fontsize=7.5)
        lo = min(vals)
        ax.set_ylim(lo * 0.85 if h != "family" else 0.3, max(vals) * 1.08)
        ax.title.set_size(8.5)
    fig.tight_layout()
    return save(fig, "heads.png")


#: label offsets (points) that keep the crowded top-right rungs readable
OFFSET = {"16x1": (-8, 8), "16x2": (-14, -13), "16x3": (-6, 8), "32x1": (-20, 9),
          "32x2": (-14, -13), "32x3": (-24, 9)}


def fig_ladder(D: Data):
    fig, ax = plt.subplots(figsize=(8.6, 3.8))
    style(ax, "Onboard model size against skill (VNIR standard-block stand-in, Sentinel-2)")
    dc = {1: SERIES[0], 2: SERIES[1], 3: SERIES[2]}
    for r in D.arch["rows"]:
        c = dc[r["depth"]]
        ax.errorbar(r["gmacs_per_scene"], r["gap"], yerr=1.96 * r["gap_se"], fmt="o", color=c,
                    mfc=c if r["tied"] else SURFACE, mew=1.6, ms=6.5, lw=1.4)
        dx, dy = OFFSET.get(r["size"], (5, -11))
        ax.annotate(f"{r['size'].replace('x', '×')} · {r['params'] / 1e3:.0f}k",
                    (r["gmacs_per_scene"], r["gap"]), textcoords="offset points",
                    xytext=(dx, dy), fontsize=7, color=MUTED)
    ax.axhline(0, color=AXIS, lw=1.2)
    ax.set_xscale("log")
    ax.set_xlabel("operations per 1000 × 1000 px scene (GMAC, log scale); label: width × depth · "
                  "parameters")
    ax.set_ylabel("skill minus the best size")
    for d, c in dc.items():
        ax.plot([], [], "o", color=c, label=f"depth {d}")
    ax.legend(loc="lower right", fontsize=7.5, frameon=False)
    return save(fig, "ladder.png")


# ---------------------------------------------------------------- report
def build():
    D = Data()
    R = D.rows
    H = D.heads
    best = next(r for r in D.arch["rows"] if r["size"] == D.arch["best"])
    rung = {r["size"]: r for r in D.arch["rows"]}
    g_std_swir = D.follow["SWIR on the standard block"]
    g_vnir_vs_swir = D.follow["MS standard alone vs fixed SWIR alone"]
    g_blocks = D.follow["custom vs standard block, both with SWIR"]
    g_cfg = D.follow["DFA nearest filters vs the configured slots"]
    stand_in = {c["against"]: c for c in D.arch["compare"]}
    s2 = {r["option"]: r for r in D.s2}
    story = []

    # ---- 1. introduction
    story += [P(TITLE, "title"),
              P("Which Dragonfly Mantis mode SAFARI should fly (VNIR, SWIR or both), which bands, "
                "how large its onboard model must be, which Xiphos board can run it, and how "
                "accurate "
                f"its fuel products are expected to be. From SAFARI's band-design study. {DATE}.",
                "subtitle"),
              P("1. Introduction", "h1")]
    story.append(P(
        "SAFARI is the 3U wildfire-risk CubeSat described in the CUBICS 2026 application. Its "
        "payload "
        "turns each image into fuel-structure layers on board: fuel type, percent conifer, canopy "
        "closure and canopy height, the forest inputs of the Canadian Fire Behaviour Prediction "
        "System. "
        "This report gives the evidence behind the payload choices in the application's primary "
        "payload "
        "description: what each camera option can retrieve, what the onboard model needs, and what "
        "accuracy to expect. It is a companion to the EO coverage report (where and how often "
        "SAFARI "
        "images) and the RF antenna report (how the data comes down)."))
    story += bullets([
        "<b>Section 2</b> describes the data and how every option was scored.",
        "<b>Section 3</b> compares the Mantis modes, VNIR against SWIR and both together.",
        "<b>Section 4</b> shows where the bands sit and why the standard filters suffice.",
        "<b>Section 5</b> sizes the onboard model and fits it to the Q7 and Q8 boards.",
        "<b>Section 6</b> gives the expected product accuracy and how it will be verified in "
        "orbit.",
        "<b>Section 7</b> sets out how far to trust the numbers; <b>section 8</b> lists the "
        "options "
        "and what comes next.",
    ])

    # ---- 2. method
    story.append(P("2. How the options were scored", "h1"))
    story.append(P(
        "A camera option is judged by what the onboard model can retrieve from it, not by band "
        "importance scores. For each option the model is retrained on exactly those bands and "
        "scored on "
        "ground it never saw. Every comparison is paired: two options are trained on the same "
        "splits and "
        "seeds, so their difference is measured directly."))
    story.append(table(
        ["Element", "What was used"],
        [["Imagery, camera comparison", "AVIRIS-NG airborne hyperspectral surface reflectance "
                                        "over boreal "
          "Canada and Alaska (NASA ABoVE), 5 nm sampling from 377 to 2496 nm, about 1.09 million "
          "development pixels. Each candidate band set is synthesised from the full spectrum with "
          "its "
          "filter response."],
         ["Imagery, band and model-size study", "Sentinel-2 summer 2020 surface-reflectance "
                                                "composites over "
          "Canada's forest regions, 904 image tiles."],
         ["Labels", "SCANFI v2 (Canadian Forest Service) 2020: percent conifer, canopy closure, "
                    "canopy "
          "height, and a seven-class fuel family (conifer, deciduous, mixedwood, open, slash, "
          "non-fuel, "
          "water)."],
         ["Model", "A compact U-Net with four output heads, the same network that will run on "
                   "board "
          "(about 31,000 parameters at the reference size)."],
         ["Validation", "Five outer folds of whole 1° blocks of ground, three training seeds each "
                        "(15 "
          "fits per option). The test blocks are never seen in training or band selection."],
         ["Sensor noise", "Every score includes a sensor noise model (placeholder values until "
                          "Dragonfly "
          "publishes per-band SNR)."],
         ["Score", "Skill per target: 1 − RMSE ÷ RMSE of predicting the training mean (fuel "
                   "family: "
          "balanced accuracy above chance). Combined skill is the mean of the four."]],
        [0.24, 0.76], caption="Data and method behind every result."))

    # ---- 3. modes
    story.append(P("3. VNIR, SWIR or both: the Mantis modes compared", "h1"))
    story.append(P(
        "The Mantis is one 1U head with several modes: an RGB snapshot camera, a six-band "
        "multispectral "
        "(VNIR) pushbroom, a hyperspectral pushbroom over 470–900 nm, and a four-filter "
        "shortwave-infrared "
        "(SWIR) pushbroom over 1000–1750 nm, chosen from Dragonfly's standard filter catalogue. "
        "VNIR and "
        "SWIR share the fore-optic through a dichroic and can image together. Figure 1 and Table 2 "
        "compare every mode on the same ground."))
    story.append(figure(fig_modes(D), "Combined skill of each Mantis mode minus the VNIR standard "
                        "block, paired by fold and seed. Blue: VNIR chain only; orange: VNIR and "
                        "SWIR "
                        "together; green: SWIR only; grey: Sentinel-2 for reference.", 3.6 * inch))
    rows = []
    for key, lbl, chain in MODES:
        r = R.get(key)
        if not r or not r.get("per"):
            continue
        h = H.get(key, {})
        rows.append([lbl, {"vnir": "VNIR", "swir": "SWIR", "both": "VNIR + SWIR",
                           "ref": "–"}[chain], f"{r['mean']:.3f}",
                     "–" if key == "ms_std" else ci(*D.gap(key, "ms_std")),
                     f"{h['pc']:.1f}" if h else "–", f"{h['closure']:.1f}" if h else "–",
                     f"{h['height']:.2f}" if h else "–", f"{h['family']:.2f}" if h else "–"])
    hl = [i for i, r in enumerate(rows) if r[0] in ("VNIR, standard filter block",
                                                     "SWIR alone, 4 standard filters",
                                                     "VNIR standard + 4 SWIR filters")]
    story.append(table(
        ["Mantis configuration", "Chain", "Skill", "Against VNIR standard [95 % CI]",
         "Conifer RMSE (pts)", "Closure RMSE (pts)", "Height RMSE (m)", "Family bal. acc."],
        rows, [0.27, 0.09, 0.07, 0.2, 0.095, 0.095, 0.09, 0.09],
        caption="Each Mantis mode on AVIRIS-NG over boreal Canada and Alaska, with sensor noise. "
                "Highlighted: the three options compared head to head below.",
        note="SWIR filters: Dragonfly L4 (1213 nm), L6 (1557), L9 (1599), L11 (1674), the "
             "catalogue filters "
             "nearest to the best SWIR placement found by searching the full spectrum. "
             "Hyperspectral "
             "'chosen in orbit' means each fold selects its own 6 channels.",
        highlight=hl))
    story.append(P("3.1 The SWIR camera against the VNIR camera", "h2"))
    story.append(P(
        "If SAFARI flies only one chain, VNIR is the better instrument: the standard VNIR block "
        "beats the "
        f"four SWIR filters by {ci(g_vnir_vs_swir['d'], g_vnir_vs_swir['se'])} in combined skill, "
        "and it "
        f"is ahead on every product (Table 2): percent conifer {H['ms_std']['pc']:.1f} against "
        f"{H['swir_nearest_alone']['pc']:.1f} points, closure {H['ms_std']['closure']:.1f} against "
        f"{H['swir_nearest_alone']['closure']:.1f}, height {H['ms_std']['height']:.2f} against "
        f"{H['swir_nearest_alone']['height']:.2f} m, fuel family {H['ms_std']['family']:.2f} "
        "against "
        f"{H['swir_nearest_alone']['family']:.2f}. SWIR alone lacks the red and near-infrared "
        "contrast "
        "that separates conifer from broadleaf and canopy from open ground."))
    story.append(P(
        "Flown together, the two are better than either. Adding the four SWIR filters to the "
        "standard "
        f"VNIR block raises combined skill by {ci(g_std_swir['d'], g_std_swir['se'])}, about "
        f"{g_std_swir['d'] / R['ms_std']['mean'] * 100:.0f} %, to {R['std_nearest']['mean']:.3f}, "
        "close to "
        f"Sentinel-2's 12 bands ({R['s2']['mean']:.3f}). Every product improves, closure most "
        f"({H['ms_std']['closure']:.1f} to {H['std_nearest']['closure']:.1f} points). With SWIR "
        "present, "
        f"the custom red-edge VNIR block no longer matters ({ci(g_blocks['d'], g_blocks['se'])}), "
        "so the "
        "standard block is enough."))
    story.append(figure(fig_heads(D), "Per-product accuracy of SWIR alone, VNIR alone, both "
                                      "together, "
                        "and Sentinel-2. Lower is better for the three RMSE panels, higher for "
                        "balanced accuracy.", 2.8 * inch))
    story.append(table(
        ["", "VNIR only (standard block)", "SWIR only (4 filters)", "VNIR + SWIR together"],
        [["Combined skill", f"{R['ms_std']['mean']:.3f}", f"{R['swir_nearest_alone']['mean']:.3f}",
          f"{R['std_nearest']['mean']:.3f}"],
         ["Bands", "480, 545, 660, 780, 900 nm + panchromatic", "1213, 1557, 1599, 1674 nm",
          "all ten"],
         ["Detector", "silicon CMOS", "standard InGaAs (top filter near its 1.7 µm cut-off)",
          "both"],
         ["GSD and swath at 500 km", "32 m (16 m pan), 32 km",
          "to confirm: 32 m and 32 km if it shares the head's optics, 14.8 m and 18 km on an "
          "earlier "
          "parts sheet", "as each chain"],
         ["Revisit (nadir)", "≈40–100 days for most altitudes (EO report)",
          "longer if the swath is 18 km: median ≈100 days at 65° N, ≈160 at 45° N",
          "set by the narrower swath where both are needed"],
         ["Readiness", "TRL 9 (Dragonfly flight heritage)", "TRL 8 on Dragonfly's parts sheet "
          "(to confirm)", "TRL 8"],
         ["Onboard inputs", "11 channels (5 bands + 6 indices)", "4 bands + indices",
          "more channels; larger first layer"],
         ["What it adds", "the fire products and vegetation indices", "moisture-sensitive bands; "
          "snow and cloud discrimination", f"+{g_std_swir['d']:.3f} skill over VNIR"],
         ["What it costs", "baseline", "second focal plane, InGaAs power and thermal control",
          "both chains' power, mass and data"]],
        [0.18, 0.27, 0.29, 0.26], caption="The two Mantis chains and their combination as options.",
        note="Power, mass and SWIR geometry for the combined head are to be confirmed with "
             "Dragonfly."))
    story.append(P(
        "The SWIR filters need no custom order: Dragonfly's catalogue filters L4, L6, L9 and L11 "
        "score "
        f"within {abs(g_cfg['d']):.3f} of the best SWIR placement found by searching the full "
        "spectrum "
        f"({ci(g_cfg['d'], g_cfg['se'])}). Searched separately in each fold, the four filters "
        "lose most "
        "of their gain to the search's own noise (Table 2 note), so they must be fixed in "
        "advance."))

    # ---- 4. bands
    story.append(P("4. Where the bands sit", "h1"))
    k5, k8 = s2["consensus, k=5"], s2["consensus, k=8"]
    story.append(P(
        "Searching Sentinel-2's bands in each training fold and keeping the bands most folds "
        "agree on "
        "gives two stable band sets. The five-band set B4, B5, B8A, B11 and B12 (red, red edge, "
        "narrow "
        f"near-infrared and both SWIR bands) scores {float(k5['skill']):.3f}, "
        f"{float(k5['gap_to_best']):.3f} ± {float(k5['gap_se']):.3f} below the best band set found "
        f"({float(k5['skill']) + float(k5['gap_to_best']):.3f}). An eight-band set ties the best "
        f"({float(k8['skill']):.3f}) but is less stable across folds."))
    si = stand_in.get("stable consensus k=5 (B4 B5 B8A B11 B12)")
    if si:
        story.append(P(
            "A Sentinel-2 stand-in for the Mantis standard VNIR block (B2, B3, B4, B7, B8A; B7 "
            "matches the "
            f"Mantis 780 nm band) comes within {abs(si['d']):.3f} ± {si['se']:.3f} of the stable "
            "five-band "
            "set on the same splits. On Sentinel-2, VNIR alone gives up little; on the "
            "hyperspectral data "
            "(section 3) SWIR adds more, because it is measured with four narrow filters rather "
            "than "
            "two broad bands."))
    story.append(P(
        "The custom red-edge VNIR block (490, 560, 665, 705, 740, 865 nm) beats the standard "
        "block by "
        f"{ci(*D.gap('ms_custom', 'ms_std'))}: not significant on its own, and nil once SWIR is "
        "added. The standard block is therefore flown, with no custom filter procurement."))

    # ---- 5. model and board
    story.append(P("5. The onboard model and the processing board", "h1"))
    story.append(P(
        "The onboard network was trained at twelve sizes (width 4–32 channels, depth 1–3) at the "
        "VNIR "
        "stand-in bands. Accuracy rises with width up to 32 channels and gains nothing from extra "
        "depth. "
        f"The best size is {best['size'].replace('x', ' × ')} ({best['params'] / 1e3:.0f} k "
        "parameters, "
        f"{best['gmacs_per_scene']:.0f} GMAC per 1000 × 1000 px scene). The 8 × 2 size used for "
        "every "
        f"band comparison is {abs(rung['8x2']['gap']):.4f} ± {rung['8x2']['gap_se']:.4f} below "
        "it, and "
        f"16 × 1 is {abs(rung['16x1']['gap']):.4f} ± {rung['16x1']['gap_se']:.4f} below."))
    story.append(figure(fig_ladder(D), "Combined skill of each model size minus the best, against "
                                       "the "
                        "operations per scene. Filled: tied with the best within one paired "
                        "standard "
                        "error.", 3.4 * inch))
    rows = []
    for s in ("8x2", "16x1", "32x1"):
        r = rung[s]
        rows.append([s.replace("x", " × "), f"{r['params'] / 1e3:.0f} k",
                     f"{r['gmacs_per_scene']:.1f}", f"{r['skill']:.3f}",
                     "best" if s == best["size"] else f"−{abs(r['gap']):.3f}",
                     f"{r['rmse_pc']:.1f} / {r['rmse_closure']:.1f} / {r['rmse_height']:.2f} / "
                     f"{r['family_ba']:.2f}",
                     f"{r['q8_dpu_s']:.2f} s", f"{r['finn_s']:.0f} s"
                     + ("" if r["q7_meets_budget"] else " (over budget)")])
    story.append(table(
        ["Size", "Params", "GMAC / scene", "Skill", "Against best",
         "Conifer / closure / height / family", "Q8 AI engine", "Q7 dataflow logic"],
        rows, [0.08, 0.08, 0.1, 0.08, 0.1, 0.27, 0.11, 0.18],
        caption="Candidate model sizes and their processing time per scene on each board (budget "
                "43 s).",
        note="Board times are from converting the network through each vendor toolchain (Q8: "
             "Vitis AI "
             "engine, 8-bit; Q7: FINN dataflow logic, 4-bit, at minimal parallelism) with 22 "
             "inputs, so "
             "they bound the 11-input VNIR model from above. A wider FINN fold would speed the Q7 "
             "at the "
             "cost of more logic; its fit is not yet measured.",
        highlight=[1, 2]))
    story.append(table(
        ["", "Xiphos Q7", "Xiphos Q8"],
        [["Processor", "Zynq-7020, 2 × Cortex-A9 at 766 MHz",
          "Zynq UltraScale+ ZU7EG, 4 × Cortex-A53, 2 × Cortex-R5"],
         ["Memory", "1 GB DDR3L (512 MB with EDAC)", "4 GB LPDDR4 with EDAC, 2 × 128 GB eMMC"],
         ["Power, mass", "2 W typical, 24 g", "5 W typical, 56 g"],
         ["Flight heritage", "Q7S in orbit since June 2016", "Q8S in orbit since September 2020"],
         ["Runs the best size (32 × 1)", "Only with a wider dataflow fold (unmeasured)",
          "Yes, ≈0.1 s"],
         ["Runs 16 × 1", "Yes, ≈35 s, about 19 % of its logic", "Yes, ≈0.03 s"]],
        [0.24, 0.38, 0.38], caption="The two processing boards (Xiphos datasheets)."))
    story.append(P(
        "Model size and board are therefore one decision. The Q8 runs the best model with a large "
        "timing "
        "margin and real-time capability at 5 W. The Q7 runs a model 0.005 below the best within "
        "the "
        "budget at 2 W. Adding the SWIR chain widens the model's first layer only, so these "
        "conclusions "
        "hold for VNIR + SWIR, to be confirmed by retraining at those bands."))

    # ---- 6. quality
    story.append(P("6. Expected product quality and its verification", "h1"))
    story.append(table(
        ["Product", "VNIR only", "VNIR + SWIR", "Verified in orbit against"],
        [["Percent conifer (RMSE, points)", f"{H['ms_std']['pc']:.1f}",
          f"{H['std_nearest']['pc']:.1f}",
          "national forest-inventory maps and plots"],
         ["Canopy closure (RMSE, points)", f"{H['ms_std']['closure']:.1f}",
          f"{H['std_nearest']['closure']:.1f}", "national forest-inventory maps and plots"],
         ["Canopy height (RMSE, m)", f"{H['ms_std']['height']:.2f}",
          f"{H['std_nearest']['height']:.2f}",
          "inventory maps; ICESat-2 canopy heights"],
         ["Fuel family (balanced accuracy, 6 classes, chance 0.17)", f"{H['ms_std']['family']:.2f}",
          f"{H['std_nearest']['family']:.2f}", "inventory maps; the CWFIS fuel-type map"]],
        [0.34, 0.12, 0.13, 0.41],
        caption="Expected accuracy of the onboard fuel layers (AVIRIS-NG, Mantis bands, with "
                "sensor "
                "noise, 8 × 2 model).",
        note="The Sentinel-2 size study (section 5) gives slightly better closure and slightly "
             "worse "
             "height on its own data; the larger model improves each by a few percent."))
    story.append(P(
        "In orbit, onboard products will be checked against ground reprocessing of the same "
        "downlinked "
        "raw scenes, radiometry against near-simultaneous Sentinel-2 overpasses, and the "
        "wildfire-risk "
        "polygons against the burned areas and fire starts that follow, as set out in the "
        "application's "
        "measurable science objectives."))

    # ---- 7. trust
    story.append(P("7. How far to trust these numbers", "h1"))
    story += bullets([
        "<b>Solid.</b> The ranking of the Mantis modes: every comparison is paired over 15 fits "
        "on ground "
        "the model never saw, and the three anchor configurations rerun in a second job "
        "reproduced their "
        "scores exactly.",
        "<b>Depends on a measurement.</b> Absolute accuracy depends on Mantis's real "
        "signal-to-noise "
        "ratio (placeholder until Dragonfly publishes it) and on the SWIR chain's real geometry. "
        "The "
        "labels are themselves mapped from Landsat, so their own error is inside every RMSE.",
        "<b>Not yet modelled.</b> The 32 m GSD against 30 m labels; the panchromatic band in the "
        "model; "
        "INT8 or 4-bit quantisation on the board (to be measured on engineering models before "
        "PDR).",
    ])

    # ---- 8. options
    story.append(P("8. Options and next steps", "h1"))
    story.append(boxed([P(
        "<b>Camera.</b> (a) VNIR standard block only: TRL 9, simplest, the baseline in the "
        "application. "
        f"(b) VNIR + four SWIR catalogue filters: +{g_std_swir['d']:.3f} combined skill (about "
        f"{g_std_swir['d'] / R['ms_std']['mean'] * 100:.0f} %), near Sentinel-2's 12 bands, at "
        "the cost "
        "of the SWIR chain's power, mass and a possibly narrower swath. (c) SWIR only: not "
        "recommended "
        f"on this evidence; {abs(g_vnir_vs_swir['d']):.3f} below VNIR alone.", "box"),
        Spacer(1, 4),
        P("<b>Model and board.</b> (a) 32 × 1 on the Q8: best accuracy, real time, 5 W. "
          "(b) 16 × 1 on the Q7: 0.005 below the best, within budget, 2 W. "
          "(c) 8 × 2 on either: the reference size, 0.011 below the best.", "box")]))
    story += bullets([
        "Retrain the size ladder on AVIRIS-NG at the true Mantis bands for VNIR, SWIR and both, "
        "including the panchromatic band, to confirm sections 3 and 5 together.",
        "Benchmark the chosen size on Q7 and Q8 engineering models: quantised accuracy, latency, "
        "power.",
        "Confirm with Dragonfly: per-band SNR, the SWIR chain's GSD, swath and TRL, and the "
        "combined "
        "head's power and mass.",
    ])

    story.append(P("Sources", "h1"))
    story += bullets(SOURCES)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUT), pagesize=letter, leftMargin=0.75 * inch,
                            rightMargin=0.75 * inch, topMargin=0.75 * inch,
                            bottomMargin=0.85 * inch, title=TITLE, author="SAFARI, ÉTS LASSENA")
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    build()
