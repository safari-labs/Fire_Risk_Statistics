"""scripts/make_report.py

The Stage 1 interim report as a PDF: which bands, which camera and which model,
and the experiments behind each answer. Text is written here; numbers come from
the results packages in docs/results/ (cited in the text), figures are their
PNGs, and the register appendix is generated from experiments.py and phases.py,
so a rerun after new results picks up the register and figures.

    python scripts/make_report.py                 # docs/report/SAFARI_stage1_interim.pdf

Needs the `report` extra (reportlab). Fonts: Arial from C:/Windows/Fonts when
present (for glyphs such as <=, ~ and arrows), else Helvetica.
"""
from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "docs" / "results"
OUT = ROOT / "docs" / "report" / "SAFARI_stage1_interim.pdf"
sys.path.insert(0, str(ROOT / "src"))

INK = colors.HexColor("#1d2330")
MUTED = colors.HexColor("#5b6272")
ACCENT = colors.HexColor("#1f5fae")
RULE = colors.HexColor("#c9cfda")
HEAD_BG = colors.HexColor("#e8edf5")
PROV_BG = colors.HexColor("#fff6e0")
DONE_BG = colors.HexColor("#e9f5ee")


# ---------------------------------------------------------------- styles
def _fonts() -> tuple[str, str, str]:
    win = Path("C:/Windows/Fonts")
    if (win / "arial.ttf").exists():
        pdfmetrics.registerFont(TTFont("Arial", str(win / "arial.ttf")))
        pdfmetrics.registerFont(TTFont("Arial-Bold", str(win / "arialbd.ttf")))
        pdfmetrics.registerFont(TTFont("Arial-Italic", str(win / "ariali.ttf")))
        pdfmetrics.registerFont(TTFont("Arial-BoldItalic", str(win / "arialbi.ttf")))
        pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold",
                                      italic="Arial-Italic", boldItalic="Arial-BoldItalic")
        return "Arial", "Arial-Bold", "Arial-Italic"
    return "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"


BODY, BOLD, ITAL = _fonts()
SS = getSampleStyleSheet()
S = {
    "title": ParagraphStyle("t", fontName=BOLD, fontSize=22, leading=27, textColor=INK,
                            spaceAfter=10),
    "subtitle": ParagraphStyle("st", fontName=BODY, fontSize=12.5, leading=16,
                               textColor=MUTED, spaceAfter=18),
    "h1": ParagraphStyle("h1", fontName=BOLD, fontSize=15, leading=19, textColor=ACCENT,
                         spaceBefore=10, spaceAfter=7),
    "h2": ParagraphStyle("h2", fontName=BOLD, fontSize=11.5, leading=15, textColor=INK,
                         spaceBefore=8, spaceAfter=4),
    "body": ParagraphStyle("b", fontName=BODY, fontSize=9.6, leading=13.4, textColor=INK,
                           spaceAfter=5, alignment=TA_LEFT),
    "bullet": ParagraphStyle("bl", fontName=BODY, fontSize=9.6, leading=13.2, textColor=INK,
                             leftIndent=13, bulletIndent=3, spaceAfter=2.5),
    "cell": ParagraphStyle("c", fontName=BODY, fontSize=8.3, leading=10.6, textColor=INK),
    "cellb": ParagraphStyle("cb", fontName=BOLD, fontSize=8.3, leading=10.6, textColor=INK),
    "caption": ParagraphStyle("cap", fontName=ITAL, fontSize=8.2, leading=10.6,
                              textColor=MUTED, spaceBefore=2, spaceAfter=10),
    "note": ParagraphStyle("n", fontName=BODY, fontSize=8.6, leading=11.6, textColor=MUTED,
                           spaceAfter=4),
}
WIDTH = letter[0] - 4.2 * cm


def P(text, style="body"):
    return Paragraph(text, S[style])


def bullets(items):
    return [Paragraph(t, S["bullet"], bulletText="\u2022") for t in items]


def table(rows, widths, head=True, shade=None):
    """rows: list of lists of str; the first row is the header when head."""
    data = [[Paragraph(str(c), S["cellb"] if head and i == 0 else S["cell"]) for c in r]
            for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w * WIDTH for w in widths], repeatRows=1 if head else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
             ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    if head:
        style.append(("BACKGROUND", (0, 0), (-1, 0), HEAD_BG))
    for r, c in (shade or []):
        style.append(("BACKGROUND", (0, r), (-1, r), c))
    t.setStyle(TableStyle(style))
    return t


def figure(path: Path, caption: str, width: float = 1.0):
    if not path.exists():
        return [P(f"[figure missing: {path.relative_to(ROOT)}]", "note")]
    iw, ih = ImageReader(str(path)).getSize()
    w = WIDTH * width
    h = w * ih / iw
    max_h = 15.5 * cm
    if h > max_h:
        w, h = w * max_h / h, max_h
    return [KeepTogether([Image(str(path), width=w, height=h),
                          P(f"{caption} <i>Source: {path.relative_to(ROOT).as_posix()}</i>",
                            "caption")])]


def box(text, bg):
    t = Table([[Paragraph(text, S["body"])]], colWidths=[WIDTH])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg),
                           ("BOX", (0, 0), (-1, -1), 0.5, RULE),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                           ("TOPPADDING", (0, 0), (-1, -1), 6),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return t


# ---------------------------------------------------------------- content
def front(date: str, commit: str):
    return [
        Spacer(1, 2.2 * cm),
        P("SAFARI Stage 1: which bands, which camera, which model", "title"),
        P("Interim report on the band design study for the SAFARI fuel-condition CubeSat "
          "imager, and the experiments behind each choice", "subtitle"),
        P(f"James Fullum, ÉTS (safari-labs). Draft of {date}.", "body"),
        P(f"Generated by <font face='{BOLD}'>scripts/make_report.py</font> at "
          f"Fire_Risk_Statistics commit {commit}.", "note"),
        Spacer(1, 0.6 * cm),
        box("<b>Status: interim.</b> The band, camera and model choices below are the current "
            "reading of the evidence, not the final P12 decision. Several runs that bear on them "
            "are in progress (section 7). Each conclusion is marked as <b>established</b> "
            "(a registered prediction tested on complete runs) or <b>provisional</b>. Every "
            "fire-danger number is our reconstruction of CFFDRS unless it is marked "
            "<b>ISSUED by CWFIS</b>. The frozen test sets have not been opened: they are read "
            "once, in P10, after the decisions are made.", PROV_BG),
        Spacer(1, 0.5 * cm),
        P("Contents", "h2"),
        *bullets(["1. Summary: the current answers",
                  "2. What the study does and how it decides",
                  "3. What imagery adds to CFFDRS",
                  "4. Which bands: the evidence",
                  "5. Which camera",
                  "6. Which model, and where it runs",
                  "7. What is still running, and what it could change",
                  "8. Limits",
                  "Appendix A. The experiment register",
                  "Appendix B. Reproducing this report"]),
        PageBreak(),
    ]


def summary():
    rows = [
        ["Decision", "Current answer", "How settled", "Main evidence"],
        ["Bands",
         "VNIR: red (665), red edge (705, 740), narrow NIR (865), with green and blue. "
         "SWIR1 near 1600 nm. SWIR2 (2190) helps, but no Dragonfly mode reaches it.",
         "Provisional: the regions are firm; exact sets wait for the E-46 re-scores.",
         "eco_v3 and hs_v4 searches; ground plots and lidar; snow-off (E-60); consensus "
         "(Q38)"],
        ["Camera",
         "Dragonfly Mantis (1U, TRL 9): the MS mode with a custom filter block "
         "(490, 560, 665, 705, 740, 865 nm) plus the SWIR mode (4 of DFA's filters), "
         "imaging together on one head.",
         "Provisional: E-66 (each Mantis mode scored on its real bands) is ready to run.",
         "A-18 and A-20 (one head, shared aperture); hs_v4: Mantis MS + SWIR ties the best "
         "measured set"],
        ["Model",
         "Onboard: the four-head ecology network (percent conifer, closure, height, fuel "
         "family). On the ground: the CFFDRS-structured fire model with fresh weather.",
         "The split is established (E-20). The network size waits for E-47.",
         "E-20: weather 3 days old costs 0.055 AUC between patches; eco_v3"],
        ["Hardware",
         "Q8 (Zynq UltraScale+) with its DPU runs every size within budget. The Q7 with "
         "FINN is possible if its buffers fit once sized. hls4ml is ruled out.",
         "Provisional: power figures and FINN buffer sizing are owed.",
         "E-48 conversion check (p12_convert)"],
    ]
    return [
        P("1. Summary: the current answers", "h1"),
        table(rows, [0.11, 0.37, 0.24, 0.28]),
        Spacer(1, 8),
        P("Five things the evidence says", "h2"),
        *bullets([
            "<b>SWIR earns its place.</b> On Sentinel-2 the first band any search picks is "
            "SWIR2 (B12) in 11 of 15 runs. On ground plots, which owe nothing to Landsat, SWIR1 "
            "lowers percent-conifer error by 1.5 % and height error by 0.33 m. SWIR1 also "
            "improves snow-off timing by about 4 days.",
            "<b>Red edge is in every best set</b> and leads percent conifer, though dropping it "
            "at six bands costs under 5 % (E-62 refuted on its second half).",
            "<b>About 5-8 bands is the range that matters.</b> Skill rises steeply to two bands "
            "and flattens; the best sets hold 7-8, and 5-6 sit about 0.008 below.",
            "<b>Within the CFFDRS structure, imagery adds little to fire-danger ranking at 99 "
            "fires</b> (about +0.01 within patches, not separable from zero). Its clearest "
            "value is mapping fuel structure, curing on grass, and keeping the inputs current.",
            "<b>Fresh weather matters more than anything imagery adds</b>, so the fire model "
            "belongs on the ground and the structure maps onboard."]),
        PageBreak(),
    ]


def method():
    slots = [
        ["Slot (CFFDRS input)", "Feeds", "Operational source", "Imagery estimate"],
        ["Fuel type", "ignition, spread, intensity", "CWFIS FBP layer or SCANFI rules",
         "ecology network, fuel family head"],
        ["Percent conifer (M-1/M-2)", "spread, intensity", "inventory", "percent-conifer head"],
        ["Canopy closure", "ignition (in-stand moisture)", "fuel-type default", "closure head"],
        ["Crown base height", "intensity (crown fire)", "FBP defaults", "height head x ratio"],
        ["Curing (O-1 grass)", "ignition, spread", "CWFIS NDVI product or default",
         "Sentinel-2 curing"],
        ["Green-up", "ignition, spread", "CWFIS green-up product", "Sentinel-2 phenology"],
        ["Foliar moisture (FMC)", "intensity", "FBP equation (date, place)",
         "LFMC retrieval (not yet usable)"],
        ["Start-up (snow-off)", "all moisture codes", "3 days after snow-off, ERA5",
         "Sentinel-2 snow-off date"],
    ]
    data = [
        ["Data", "What it is used for"],
        ["Sentinel-2 L2A composites, 904 tiles (ecology_v3)",
         "band searches for the structure estimators, against SCANFI labels"],
        ["AVIRIS-NG, 42 lines over boreal Canada (aviris_v4)",
         "band placement anywhere in 400-2500 nm, and each camera's real bands"],
        ["MAGPlot ground plots, ATL08 lidar",
         "labels that owe nothing to Landsat, to check SCANFI-based rankings"],
        ["99 fire patches (NBAC), ERA5-Land weather",
         "Stage A: what each CFFDRS input slot is worth for burned area"],
        ["NFDB lightning starts with matched controls",
         "Stage C: ignition, with weather held fixed within each set"],
        ["Globe-LFMC (2017+), PROSPECT-D + 4SAIL",
         "live fuel moisture: empirical and simulation-trained retrievals"],
    ]
    return [
        P("2. What the study does and how it decides", "h1"),
        P("SAFARI is a CubeSat imager for wildland fuel condition, feeding Canadian fire danger "
          "rating (CFFDRS). Stage 1 decides which spectral bands the camera should carry. "
          "Rather than ranking bands by how well they predict fire on their own, the study "
          "mirrors CFFDRS and asks, input by input, what an imagery estimate would change. "
          "The places where imagery can enter the CFFDRS equations are called slots."),
        table(slots, [0.24, 0.22, 0.27, 0.27]),
        P("Where imagery can enter CFFDRS. The full table, with the equations each slot feeds, "
          "is in docs/CFFDRS_CHAIN.md.", "caption"),
        P("Data", "h2"),
        table(data, [0.42, 0.58]),
        Spacer(1, 6),
        P("Rules every experiment follows", "h2"),
        *bullets([
            "Nested band sets are ranked, never single bands, and each set is judged by "
            "training the retrieval model on it (wrapper evaluation).",
            "Candidate spectra come only from radiative transfer or real hyperspectral data; "
            "no multispectral sensor's bands are interpolated into new ones.",
            "Labels are physical or independently measured, never CFFDRS outputs.",
            "Train and test are split by place (1-degree blocks), never by random rows. "
            "Selection happens inside training folds, and the frozen test sets are untouched.",
            "Every evaluation includes the sensor noise model (a placeholder until the "
            "instrument's SNR is known).",
            "No band sits in an atmospheric absorption region (rule 7).",
            "Predictions are registered before results, with what would refute them."]),
        P("How choices are made", "h2"),
        *bullets([
            "Performance decides; cost is shown beside each option but never ranks (A-41). "
            "Each P12 decision is a table of options with pros and cons, and James chooses "
            "(A-49).",
            "The four structure targets weigh equally. Six other weightings were tried; under "
            "five of them the choice did not change (p12_weights).",
            "Ties are paired: same fold and seed, one standard error of the difference.",
            "A band set counts as stable when every spectral region in it is chosen by at "
            "least 10 of the 15 searches (5 folds x 3 seeds), and the exact consensus set is "
            "then re-scored (Q38)."]),
        PageBreak(),
    ]


def cffdrs():
    ladder = [
        ["Rung", "Within-patch AUC", "Between-patch AUC"],
        ["R0: CFFDRS physics as is (HFI)", "0.669", "0.858"],
        ["R1: learned on the CFFDRS inputs", "0.719", "0.886"],
        ["R2: physics + learned residual", "0.695", "0.880"],
        ["R4: R2 + a free imagery branch", "0.704", "0.881"],
        ["FWI ISSUED by CWFIS (D-1)", "no 2 km counterpart", "0.857"],
    ]
    return [
        P("3. What imagery adds to CFFDRS", "h1"),
        P("Stage A trains a CFFDRS-structured network on the development fire patches (99 "
          "fire patches in all; a frozen share waits for P10) and asks what each "
          "slot is worth when its value comes from imagery instead of the operational source. "
          "Scores are AUC for burned pixels: within a patch (which pixels burn) and between "
          "patches (which patches burn). 300 fits: 5 folds x 3 seeds."),
        table(ladder, [0.5, 0.25, 0.25]),
        P("The P7 ladder (p7_slots). Between patches, none of our rungs separates from the FWI "
          "CWFIS issued.", "caption"),
        *bullets([
            "<b>Learning on the CFFDRS inputs beats the physics</b> (R1 - R0 +0.051 within "
            "patches, all five folds). Adding a free imagery branch on top adds about +0.01, "
            "which 83 fires cannot separate from zero. <b>Established.</b>",
            "<b>Single slots move little.</b> Percent conifer and crown base height from "
            "imagery change within-patch AUC by about 0.001. Curing from imagery helps on O-1 "
            "grass pixels (+0.013, CI above 0), the one slot with a clear gain.",
            "<b>Weather age is the largest effect measured</b> (E-20, below)."]),
        *figure(RES / "figures" / "value_map.png",
                "Figure 1. The value map: what each slot changed, by CFFDRS process."),
        P("Weather age (E-20)", "h2"),
        P("One trained model, scored with all its weather 1, 2, 3 and 7 days old. Between "
          "patches, R2 loses 0.023 at 2 days (CI reaches 0), 0.055 at 3 days and 0.051 at 7. "
          "The physics alone loses more. Within patches nothing changes, because weather is "
          "one value per patch. Training on 7-day-old weather is worse at every age. "
          "<b>Established for the decay (PARTIAL: the per-code half was not run).</b> This "
          "is why the fire model is placed on the ground (section 6)."),
        *figure(RES / "p7d_weather_age" / "weather_age.png",
                "Figure 2. Skill against the age of all the weather (E-20)."),
        P("Ignition (E-44, E-45, partial)", "h2"),
        P("NFDB lightning starts, each matched with up to five controls on the same day under "
          "the same weather. CFFDRS physics ranks the start above its controls at 0.533. "
          "Learning on the CFFDRS inputs alone (fuel, structure slots, leaf state) reaches "
          "0.586 (+0.052 [+0.033, +0.072]). The imagery rungs are still running, so whether "
          "imagery adds to ignition is not yet known. <b>Provisional (36 of 100 fits).</b>"),
        *figure(RES / "p9b_ignition_rungs" / "ignition_rungs.png",
                "Figure 3. Ignition: matched-set AUC per rung, and paired differences."),
        PageBreak(),
    ]


def bands():
    hs = [
        ["Band set (AVIRIS-NG, hs_v4)", "Combined skill", "Above fixed VNIR [95 % CI]"],
        ["Config C: 1610 + 2190 nm (extended InGaAs)", "0.288", "+0.016 [-0.003, +0.042]"],
        ["Searched SWIR, extended InGaAs, 4 bands", "0.287", "+0.015 [+0.004, +0.026]"],
        ["Sentinel-2, all 12 bands", "0.286", "+0.014 [-0.003, +0.031]"],
        ["Mantis MS + SWIR (1240, 1550, 1610, 1680)", "0.285", "+0.013 [+0.003, +0.026]"],
        ["Searched SWIR, standard InGaAs, 4 bands", "0.279", "+0.007 [-0.002, +0.015]"],
        ["Config A: 1610 nm only", "0.278", "+0.006 [-0.005, +0.017]"],
        ["Fixed six VNIR bands", "0.272", "-"],
    ]
    cons = [
        ["k", "Sentinel-2 consensus set", "Weakest region", "Stable"],
        ["1", "B12", "11 / 15", "yes"],
        ["4", "B4, B6, B8A, B12", "9 / 15", "no"],
        ["5", "B4, B5, B8A, B11, B12", "10 / 15", "yes"],
        ["6", "B4, B5, B6, B8A, B11, B12", "8 / 15", "no"],
        ["8", "B3, B4, B5, B6, B8, B8A, B11, B12", "9 / 15", "no"],
    ]
    return [
        P("4. Which bands: the evidence", "h1"),
        P("4.1 Sentinel-2 band searches (eco_v3)", "h2"),
        P("Greedy nested searches over Sentinel-2's 12 bands, inside each training fold, for "
          "the four structure targets: percent conifer, closure, height and fuel family "
          "(SCANFI labels). 15 searches per selector, with sensor noise."),
        *bullets([
            "<b>SWIR comes first</b> (E-22 supported): B12 enters at step 1 in 11 of 15 "
            "runs. Closure opens with B12 in all 15; percent conifer with red edge "
            "(B7 47 %, B6 27 %); fuel family with NIR.",
            "<b>Indices barely help as inputs</b> (E-59 mixed): raw + indices beats raw only "
            "at 8 bands, by 0.003.",
            "<b>Fuel family is the weak head:</b> conifer recall 0.79, deciduous 0.38, "
            "mixedwood 0.30. Deciduous and mixed stands are mostly called conifer."]),
        *figure(RES / "p6a_ecology_v3" / "curves.png",
                "Figure 4. Sentinel-2: skill by nested band count, per search."),
        P("4.2 Labels that owe nothing to Landsat", "h2"),
        P("SCANFI is mapped from Landsat, SWIR included, so SWIR ranking first could be the "
          "labels favouring their own bands. On MAGPlot ground plots, SWIR1 still lowers "
          "percent-conifer error by 1.51 % [1.25, 1.70] and height error by 0.33 m, in 5 of 5 "
          "folds; NIR is picked first and 1610 nm second. On ATL08 lidar height, adding "
          "2190 nm to 1610 nm helps (-0.07 m). <b>Established: SWIR's value is not a label "
          "artefact.</b>"),
        P("4.3 AVIRIS-NG: where in the spectrum (hs_v4)", "h2"),
        P("Real hyperspectral data lets bands be placed anywhere in 400-2500 nm. Searches with "
          "the six VNIR bands fixed, and fixed reference sets, all paired with the fixed VNIR "
          "on the same folds:"),
        table(hs, [0.5, 0.18, 0.32]),
        P("hs_v4 (p6a_hs_v4). Twelve options tie within one SE of the best.", "caption"),
        *bullets([
            "SWIR improves closure in every set (CIs below 0) and height on both SCANFI and "
            "lidar. It does not help percent conifer on SCANFI labels, although it does on "
            "ground plots; that remains an open puzzle.",
            "The searches agree on broad SWIR windows (about 1500-1650 nm, and 2000-2250 nm "
            "on extended InGaAs), not on a 50 nm placement.",
            "The gains are small in combined skill (at most +0.016) but consistent."]),
        P("4.4 Snow-off and live fuel moisture", "h2"),
        *bullets([
            "<b>Snow-off (E-60):</b> from VNIR alone the start-up date is off by a median "
            "19.5 days; allowing SWIR brings it to 15.7. SWIR1 buys about 4 days, counting "
            "toward the SWIR chain. <b>Established.</b>",
            "<b>Live fuel moisture (E-64):</b> on conifers neither a simulation-trained nor an "
            "empirical Sentinel-2 retrieval beats FBP's own foliar moisture equation; the "
            "simulation route is biased +31 points. The forward model's code was checked "
            "against Féret's R reference and agrees to 5e-15, so the bias is not a code "
            "error. A retrain with priors narrowed inside each fold (E-65) is running. "
            "<b>Provisional: moisture bands are not yet a requirement.</b>"]),
        P("4.5 Weighting and stability", "h2"),
        P("Re-scoring the searched sets under six weightings of the four targets barely moves "
          "the choice: under five of six, the equal-weight search's best set ties with the "
          "overall best. The 15 searches rarely agree on a whole set, so the sets were counted "
          "by spectral region (Q38). Two Sentinel-2 consensus sets are stable:"),
        table(cons, [0.06, 0.5, 0.22, 0.22], shade=[(1, DONE_BG), (3, DONE_BG)]),
        P("Consensus by region (p12_bands). Each set is being re-scored as a fixed set on the "
          "same folds (E-46).", "caption"),
        *figure(RES / "p12_bands" / "qual_E-46_band_placement.png",
                "Figure 5. Where each consensus set's bands sit, against a conifer canopy "
                "spectrum; grey: forbidden atmospheric regions.", width=0.78),
        KeepTogether([
            P("4.6 Band conclusion (provisional)", "h2"),
            box("Carry <b>red, red edge (705 and 740), narrow NIR (865), green and blue</b> "
                "on the VNIR side and <b>SWIR1 near 1600 nm</b>. SWIR2 (2190) adds height and "
                "closure skill, but no Dragonfly mode reaches it (A-18), so it is out unless a "
                "different SWIR camera is chosen. The exact set and band count follow the "
                "E-46 re-scores. The front-runners are the stable five-band Sentinel-2 set "
                "(red, red edge, narrow NIR, SWIR1, SWIR2; on Mantis without SWIR2) and the "
                "7-8-band sets.", PROV_BG)]),
        Spacer(1, 10),
    ]


def camera():
    mantis = [
        ["Mantis mode", "GSD at 500 km", "Swath", "Bands", "Bit depth"],
        ["RGB snapshot", "16 m", "32 km", "standard RGB", "8 or 10"],
        ["Multispectral pushbroom", "16 m pan, 32 m MS", "32 km",
         "6 (standard: 480, 545, 660, pan 625, 780, 900)", "10 or 12"],
        ["Hyperspectral pushbroom", "32 m", "32 km", "96, 470-900 nm, chosen in orbit",
         "8 or 10"],
        ["SWIR pushbroom", "as MS (A-20)", "32 km", "4 of 12 DFA filters, 1000-1750 nm",
         "not stated"],
    ]
    options = [
        ["Option", "Pros", "Cons"],
        ["<b>A. Mantis MS (custom block) + SWIR</b> (current lean)",
         "Ties the best measured set on AVIRIS-NG (0.285 vs 0.288). The custom block carries "
         "the red edge and 865 nm the searches want. One head, one aperture: SWIR and VNIR "
         "co-registered by design. 1U, under 6 W, TRL 9.",
         "No SWIR2. Custom filters must be ordered (DFA builds them in-house). SNR not "
         "published. The 1059/1068 nm filters sit near the dichroic crossover."],
        ["B. Mantis MS (standard block) + SWIR",
         "Off the shelf.",
         "No red edge or 865 nm; pan and 780 nm overlap the O2-A absorption (rule 7, scored "
         "as published by James's decision)."],
        ["C. Mantis HS + SWIR",
         "Any VNIR set can be chosen in orbit, a hedge on the band decision.",
         "470-900 nm loses 443 nm (aerosol) and 945 nm; 96 bands raise downlink and "
         "onboard compute; untested against 6 good bands (E-66 will test it)."],
        ["D. Mantis MS only",
         "Simplest; VNIR alone reaches about 94 % of the best measured score.",
         "Loses SWIR's closure, height and snow-off gains."],
    ]
    return [
        P("5. Which camera", "h1"),
        P("The inventory (CubeSat_Sensors_and_Lenses.xlsx) and Dragonfly Aerospace's published "
          "data set the options. Two facts dominate: no Dragonfly SWIR mode reaches SWIR2 "
          "(it stops at 1750 nm, with about 1700 nm usable on standard InGaAs, A-19), and "
          "Mantis carries its MS and SWIR modes on one head, imaging at the same instant "
          "through a shared aperture with a dichroic (A-18, A-20, confirmed). Chameleon and "
          "Caiman are out of scope (James, 2026-11-06)."),
        table(mantis, [0.22, 0.17, 0.09, 0.38, 0.14]),
        P("Dragonfly Mantis datasheet and band tables (config/vendors/dragonfly.yaml, A-52). "
          "Every mode: 1U, under 0.5 kg, under 6 W imaging, TRL 9. No SNR is published.",
          "caption"),
        P("DFA's standard MS block is not the block the evidence asks for: it has no red edge "
          "and no 865 nm, and two of its bands (pan, 780 nm) overlap the oxygen absorption "
          "at 760 nm. DFA builds filter blocks in-house, so the custom block (490, 560, 665, "
          "705, 740, 865 nm) is orderable. Of DFA's 12 SWIR filters, 10 are usable: 1348 nm "
          "sits in water vapour and 1702/87 runs past the standard-InGaAs edge."),
        P("Options", "h2"),
        table(options, [0.26, 0.40, 0.34]),
        Spacer(1, 6),
        P("E-66: each Mantis mode on its real bands", "h2"),
        P("Approved and ready to run on AVIRIS-NG, on the same folds as hs_v4: the RGB proxy, "
          "the standard MS block as published and its clean subset, the custom block, all 81 "
          "HS surface channels and the best 6 of them, SWIR alone (best 4 DFA filters), and "
          "each MS block with its best 4 filters. Registered predictions: the custom block "
          "beats the standard one; MS beats SWIR alone; HS is no better than 6 well-placed "
          "bands; SWIR adds to MS; RGB is the floor."),
        box("<b>Current lean (provisional): option A,</b> the Mantis MS mode with the custom "
            "filter block plus the SWIR mode, on one head. E-66 will show whether the real "
            "filters keep it tied with the best, and how much the standard block and the HS "
            "mode give up.", PROV_BG),
        PageBreak(),
    ]


def model():
    conv = [
        ["Flow", "Converts", "Fits at <= 80 % of a board", "Seconds per 1000 x 1000 px scene"],
        ["hls4ml", "12 of 12 sizes; C simulation matches to 0.0014",
         "none (the ranked 8x2 size needs 258 % of the Q8's memory)", "not measured"],
        ["DPU on the Q8 (INT8)", "12 of 12, each one DPU subgraph",
         "fixed overlay, mostly idle", "0.015 at 8x2, at most 0.28"],
        ["FINN (W4A4 / W8A8)", "24 of 24",
         "Q8: 23 of 24; Q7: 20 of 24 (buffers not yet sized)",
         "8.6 at 8x2; 138 at the largest sizes"],
    ]
    return [
        P("6. Which model, and where it runs", "h1"),
        P("Onboard, or on the ground?", "h2"),
        P("The structure estimators (percent conifer, closure, height, fuel family) need no "
          "weather, so they can run onboard and downlink small maps. The fire-danger model "
          "needs weather, and E-20 shows that weather even 3 days old costs about 0.05 AUC "
          "between patches, while training on stale weather does not recover it. A product "
          "uplinked from orbit is 1-2 days old at best. <b>So the fire model runs on the "
          "ground with fresh weather, and the onboard model is the ecology network "
          "(established split, A-41).</b>"),
        P("The onboard model", "h2"),
        P("TinyEcologyUNet: a small U-Net over the chosen bands and their indices, with four "
          "heads. The bands were ranked with base 8 channels and depth 2 (about 32,000 "
          "parameters). E-47 (registered) trains 12 sizes, base 4-32 channels by depth 1-3, at "
          "the chosen bands; the hypothesis is that the ranked size is within one paired SE "
          "of the best. It waits for the band set."),
        P("Does it fit the flight computer? (E-48 pre-check)", "h2"),
        table(conv, [0.18, 0.26, 0.30, 0.26]),
        P("All 12 sizes, 22 inputs (8 bands with indices), untrained. Budget: 43 s per scene. "
          "The index step divides, so it runs as a separate pointwise stage, as the existing "
          "ratios front end does (0 memory, 6 % of the Q8's logic).", "caption"),
        *figure(RES / "p12_convert" / "convert.png",
                "Figure 6. Memory share of the Q8 and seconds per scene, by network size and "
                "flow."),
        box("<b>Hardware options (provisional):</b> the <b>Q8 with its DPU</b> is safe on time "
            "for every size (3.5 W typical board, mostly idle); the <b>Q7 with FINN</b> "
            "(2 W board) fits on FINN's estimates, but only buffer sizing, which needs Vivado on "
            "Linux, will confirm it. hls4ml cannot carry a U-Net of useful size on either.",
            PROV_BG),
        PageBreak(),
    ]


def pending():
    rows = [
        ["Run", "Question", "Could change"],
        ["E-46 re-scores (Narval)", "Each consensus band set scored as a fixed set",
         "the band count and exact set"],
        ["E-66 sensors_v1 (ready)", "What each Mantis mode offers on its real bands",
         "the camera option and its filter block"],
        ["E-45 ignition, remaining fits", "Does imagery add to ignition ranking?",
         "whether imagery carries ignition value"],
        ["E-65 LFMC v2 (Narval)", "Does a right-sized prior make the simulation retrieval "
         "work?", "whether moisture bands (1240 nm) become a requirement"],
        ["E-35 fuel slot", "Does an imagery fuel map beat the inventory in CFFDRS?",
         "the value of the structure estimators to fire danger"],
        ["E-47 size ladder", "Smallest network within one SE of the best",
         "the onboard model size and hardware fit"],
        ["E-48 buffer sizing, power", "Q7 with FINN, and watts per option",
         "the flight computer"],
    ]
    return [
        P("7. What is still running, and what it could change", "h1"),
        table(rows, [0.26, 0.42, 0.32]),
        Spacer(1, 6),
        P("Once these land, P12 writes the three option tables (bands, architecture, "
          "hardware) for James to choose from, and P10 scores the chosen configuration once on "
          "every frozen test set."),
        P("8. Limits", "h1"),
        *bullets([
            "Most structure labels are SCANFI, which is mapped from Landsat; ground plots and "
            "lidar check the main rankings but cover fewer targets.",
            "Stage A rests on 99 fire patches, 72 of them from 2023; between-patch "
            "comparisons have wide intervals.",
            "Sensor noise is a placeholder model: no Mantis SNR is published, so camera "
            "comparisons are spectral, not radiometric.",
            "GSD and swath are not modelled: training data are at 20 m, Mantis MS at 32 m.",
            "Globe-LFMC has no Canadian sites; US jack and red pine stand in.",
            "The turbid-medium canopy model (4SAIL) is a simplification for conifer stands."]),
        PageBreak(),
    ]


def appendix():
    from safari_bands.experiments import EXPERIMENTS
    from safari_bands.phases import PHASES
    verdict = {}
    for ph in PHASES:
        for e in ph.entries:
            if e.kind == "experiment":
                verdict[e.ref] = e.verdict
    rows = [["ID", "Experiment", "State", "Latest verdict"]]
    for e in EXPERIMENTS:
        rows.append([e.eid, e.name, e.state.replace("_", " ").lower(),
                     verdict.get(e.eid, "-")])
    return [
        P("Appendix A. The experiment register", "h1"),
        P("Every registered experiment, its state and the latest verdict recorded in a phase "
          "sheet. Hypotheses, variables and full results are in docs/EXPERIMENTS.md and the "
          "results packages under docs/results/.", "note"),
        table(rows, [0.08, 0.56, 0.16, 0.20]),
        Spacer(1, 10),
        P("Appendix B. Reproducing this report", "h1"),
        *bullets([
            "Repositories: Fire_Risk_Statistics (design, analysis, this report), "
            "Fire_Risk_Model (data and packs), Fire_Risk_FW (models, cluster runners, FPGA "
            "flows).",
            "Every results package is regenerated by the command at the top of its README; "
            "cluster runs are copied to narval_results/.",
            "Decisions and their reasons: docs/ASSUMPTIONS.md (A-1 to A-52); open questions: "
            "docs/OPEN_QUESTIONS.md; the plan: docs/PLAN_NEXT.md.",
            "This report: python scripts/make_report.py (needs the report extra)."]),
    ]


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(BODY, 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(2.1 * cm, 1.2 * cm, "SAFARI Stage 1 interim report. Provisional "
                      "conclusions; our reconstruction unless marked ISSUED by CWFIS.")
    canvas.drawRightString(letter[0] - 2.1 * cm, 1.2 * cm, f"{doc.page}")
    canvas.restoreState()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--date", default=dt.date.today().isoformat())
    args = ap.parse_args(argv)
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip() or "unknown"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(args.out), pagesize=letter, leftMargin=2.1 * cm,
                            rightMargin=2.1 * cm, topMargin=1.9 * cm, bottomMargin=2.0 * cm,
                            title="SAFARI Stage 1 interim report", author="James Fullum",
                            subject="Bands, camera and model for the SAFARI CubeSat")
    story = [*front(args.date, commit), *summary(), *method(), *cffdrs(), *bands(),
             *camera(), *model(), *pending(), *appendix()]
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
