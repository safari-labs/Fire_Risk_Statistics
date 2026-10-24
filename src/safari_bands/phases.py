"""What each phase of the CFFDRS-mirror plan ran, and what it concluded.

The register (experiments.py) says what each experiment WILL test; this says
what each PHASE actually did. scripts/make_phase_docs.py renders it, one
visual sheet per phase, into the phase's results folder.

Three kinds of entry, kept apart on purpose:

    experiment   a registered experiment (E-n). Its hypothesis, independent
                 and dependent variables come from the register, verbatim:
                 nothing here restates them, so the sheet cannot drift from
                 what was registered.
    control      a comparison run to interpret an experiment (a resolution
                 control, a land mask). No hypothesis was registered for it,
                 and the sheet says so rather than writing one after the fact.
    check        a verification with a pass criterion (a port against its
                 reference, a split against its rule).
    measurement  a fact the plan needed (a date, a coverage, a leak), with a
                 question and no hypothesis.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from safari_bands.experiments import by_id

#: Verdicts, with what each means. A verdict is a statement about the
#: hypothesis or criterion, never about whether the result was welcome.
VERDICTS: dict[str, str] = {
    "SUPPORTED": "the registered prediction held",
    "REFUTED": "the registered prediction failed",
    "AT RISK": "the half that could run removes what the prediction needs",
    "PASS": "the check met its criterion",
    "FIXED": "the check failed, the cause was fixed, and it now passes",
    "MEASURED": "no hypothesis: a measurement or control, reported as found",
    "PENDING": "not yet run",
}

KINDS = ("experiment", "control", "check", "measurement")


@dataclass(frozen=True)
class Entry:
    ref: str
    kind: str
    verdict: str
    result: str
    conclusion: str
    #: For controls, checks and measurements only; experiments read the
    #: register. ``question`` is the pass criterion for a check.
    title: str = ""
    question: str = ""
    independent: str = ""
    dependent: str = ""

    def resolved(self) -> dict[str, str]:
        """Title, the hypothesis or question with its label, and the two
        variables -- from the register for an experiment."""
        if self.kind == "experiment":
            e = by_id(self.ref)
            return {"title": e.name, "label": "Hypothesis (registered)",
                    "question": e.hypothesis, "independent": e.independent,
                    "dependent": e.dependent}
        label = {"control": "Question (control; no hypothesis registered)",
                 "check": "Pass criterion",
                 "measurement": "Question (measurement; no hypothesis registered)"}
        return {"title": self.title, "label": label[self.kind],
                "question": self.question, "independent": self.independent,
                "dependent": self.dependent}


@dataclass(frozen=True)
class Phase:
    pid: str
    title: str
    date: str
    folder: str              # under docs/results/
    note: str                # the phase's results note, relative to folder
    summary: str
    entries: tuple[Entry, ...] = field(default_factory=tuple)


PHASES: tuple[Phase, ...] = (
    Phase(
        "P0", "Verify and freeze", "2026-10-23", "p0_verify",
        "../phase0_cffdrs_mirror.md",
        "Checked the data every later phase stands on, fixed what failed, "
        "and froze the test set. Nothing was trained or scored.",
        (
            Entry("P0-1", "measurement", "MEASURED",
                  title="Fire start dates",
                  question="Does every fire have a recorded start date, and did "
                           "the legacy 30-June design overlap the fires?",
                  independent="each patch matched to its NBAC polygon (99 fire "
                              "patches, 108 confusers)",
                  dependent="start date present; start on or before 30 June",
                  result="99 / 99 fire patches dated (HS_SDATE). 95 / 108 "
                         "confusers matched; 13 stay unmatched even with NBAC "
                         "2024-25. 66 / 99 fires started on or before 30 June.",
                  conclusion="The legacy design read weather and imagery after "
                             "most fires had started. P3 and P4 re-date both "
                             "(A-24)."),
            Entry("P0-2", "measurement", "MEASURED",
                  title="Fuel layer vintage on burned ground",
                  question="Which CWFIS fuel layers describe the ground before "
                           "the fire?",
                  independent="fuel layer: CWFIS 2024 (30 m) / 2019 (250 m) / "
                              "2014b (250 m)",
                  dependent="share of NBAC-burned pixels the layer calls non-fuel",
                  result="2024: 73.9 %. 2019: 1.0-4.5 % by fire year. 2014b: "
                         "1.2-6.0 %.",
                  conclusion="CWFIS 2024 has the burn scars written in. The "
                             "operational pre-fire fuel is the 2019 (or 2014b) "
                             "layer (A-25)."),
            Entry("P0-3", "measurement", "MEASURED",
                  title="SCANFI time step on burned ground",
                  question="Which SCANFI v2 step is pre-fire for each fire year?",
                  independent="SCANFI v2 step: 2015 / 2020 / 2025",
                  dependent="age reset, crown closure and biomass change over "
                            "burned pixels",
                  result="2015: no change. 2020: already shows the 2019-20 fires. "
                         "2025: shows every fire.",
                  conclusion="The pre-fire step is the latest one before the fire "
                             "year; 2025 is the post-fire control."),
            Entry("P0-4", "check", "FIXED",
                  title="Test split integrity",
                  question="No fire has patches in two splits.",
                  independent="grouping rule: 0.1-degree block vs block or same "
                              "fire (connected components)",
                  dependent="fires with patches in more than one split",
                  result="Block-only grouping: 8 fires in two splits, 5 of them "
                         "across train and test. New rule: none. Test set 35 "
                         "patches (11 moved in, none out); sha256 3e65e310.",
                  conclusion="No result had been reported on the old test split, "
                             "so it was fixed rather than retracted (A-27)."),
            Entry("P0-5", "check", "PASS",
                  title="SCANFI multi-step loader",
                  question="The loader that reads all nine SCANFI steps rebuilds "
                           "the legacy 2020 sidecars.",
                  independent="loader: legacy vs multi-step",
                  dependent="worst absolute difference on the 2020 sidecars",
                  result="2.4e-4 (float16 rounding). On the way, a bug that "
                         "silently served the 2020 raster for any missing year "
                         "was found and fixed.",
                  conclusion="Every SCANFI step can be compared without a silent "
                             "vintage swap."),
            Entry("P0-6", "measurement", "MEASURED",
                  title="CFSDS coverage (Stage B)",
                  question="Does the Canadian Fire Spread Dataset cover our fires?",
                  independent="CFSDS v1.1 (90 m, fires > 500 ha, 2002-2024)",
                  dependent="fire patches and fire-days covered",
                  result="All 99 fire patches; 7,835 fire-days.",
                  conclusion="Stage B (daily spread) can use the same fires; no "
                             "separate chips are needed."),
        ),
    ),
    Phase(
        "P1", "Physics port", "2026-10-23", "p1_physics", "README.md",
        "Ported FBP1992 and corrected the FWI code, both validated against the "
        "CFS reference implementation (cffdrs 1.9.2), and measured how far each "
        "imagery-replaceable input moves the physics.",
        (
            Entry("P1-1", "check", "PASS",
                  title="FBP port against cffdrs",
                  question="Every FBP output matches cffdrs to a relative "
                           "tolerance of 1e-9 on 6,000 seeded rows over 17 fuel "
                           "types.",
                  independent="implementation: our port vs cffdrs::fbp()",
                  dependent="worst relative error per output; fire type agreement",
                  result="About 1e-12 on every output; fire type agrees on "
                         "6,000 / 6,000 rows.",
                  conclusion="R0's spread and intensity are the operational "
                             "equations. D-2, absent from the package, is tested "
                             "separately as 0.2 x D-1."),
            Entry("P1-2", "check", "FIXED",
                  title="FWI codes against cffdrs",
                  question="All six FWI codes match cffdrs::fwi() to 1e-9.",
                  independent="implementation: fwi.py vs cffdrs::fwi()",
                  dependent="worst difference per code",
                  result="First run: up to 2.8 FFMC points off. Three fixes (rain "
                         "correction, FFMC constant, DMC wetting). Now about "
                         "1e-14.",
                  conclusion="Every _fwi.json built before the fix is legacy; P3 "
                             "rebuilds the weather."),
            Entry("P1-3", "measurement", "MEASURED",
                  title="What each slot can move",
                  question="How far does each input imagery could supply move "
                           "FBP?",
                  independent="fuel type, foliar moisture, crown base height, "
                              "percent conifer, leaf state -- weather held fixed",
                  dependent="rate of spread and crown fraction burned",
                  result="At ISI 30: ROS about 75 m/min (O-1a, 90 % cured) vs 11 "
                         "(D-1). FMC 85 -> 120 % delays crowning by about 4 km/h "
                         "of wind. At 0 % conifer, M-1 spreads about 5x M-2.",
                  conclusion="Fuel type, foliar moisture and leaf state carry the "
                             "most physical leverage. Whether imagery can inform "
                             "them is P6-P7's question."),
        ),
    ),
    Phase(
        "P2", "R0: CFFDRS as is, every fuel inventory", "2026-10-24", "p2_r0",
        "README.md",
        "Scored the non-learned CFFDRS reference (FBP1992 + Beverly & Wotton "
        "2007) per pixel for every fuel inventory, on 196 development patches "
        "(83 fire), legacy 30-June design. The test groups were not read.",
        (
            Entry("E-32", "experiment", "SUPPORTED",
                  result="Within fire patches, FBP HFI AUC 0.676 [0.65, 0.70] "
                         "(SCANFI pre-fire), 0.623 (CWFIS 2019). Between patches "
                         "FWI 0.738, BUI 0.765, DC 0.828; DC beats each fire's own "
                         "confuser in 88 % of 68 pairs. P(sustained flaming) about "
                         "0.5 within patches.",
                  conclusion="CFFDRS ranks both axes above chance, so imagery "
                             "deltas will be read against a real floor. NBAC "
                             "burned area does not test ignition; Stage C does."),
            Entry("E-33", "experiment", "REFUTED",
                  result="Pre-fire layers are not equal: SCANFI through the CFS "
                         "tree beats CWFIS 2019 by +0.053 [+0.037, +0.071] "
                         "(+0.031 on land). Post-fire layers DEFLATE R0: CWFIS "
                         "2024 0.21, SCANFI 2025 0.49.",
                  conclusion="Use SCANFI through the CFS tree as the pre-fire "
                             "fuel reference. The post-fire leak is large (+0.41) "
                             "but unlearned physics reads it backwards; a learner "
                             "would not, so post-fire layers stay excluded."),
            Entry("E-21", "experiment", "AT RISK",
                  result="Inventory half only: -0.005 AUC per decade of SCANFI "
                         "age [-0.015, +0.007], 79 fire patches, ages 1-13 y.",
                  conclusion="No staleness cost to recover on this sample, so the "
                             "refresh prediction is at risk before its learned "
                             "half (E-22) runs. 2005 and half of 2010 pending."),
            Entry("P2-C1", "control", "MEASURED",
                  title="Land-mask control",
                  question="Is R0's within-patch skill ranking fuel, or mapping "
                           "water and rock?",
                  independent="pixels scored: all vs a common land mask (burnable "
                              "under CWFIS 2019, 2014b and SCANFI pre-fire)",
                  dependent="within-patch HFI AUC",
                  result="SCANFI 0.676 -> 0.589; CWFIS 2019 0.623 -> 0.558; "
                         "A-11 rules 0.628 -> 0.508.",
                  conclusion="About half of R0's margin above chance is lakes "
                             "and rock. An imagery fuel map must beat 0.589 on "
                             "land."),
            Entry("P2-C2", "control", "MEASURED",
                  title="Resolution control",
                  question="Is SCANFI's advantage its content or its 30 m pixels?",
                  independent="SCANFI fuel map at 30 m vs block-moded to 250 m",
                  dependent="paired within-patch HFI AUC",
                  result="+0.014 [+0.005, +0.024] on all pixels; -0.001 "
                         "[-0.009, +0.008] on land.",
                  conclusion="The 30 m gain was the water mask. Under unlearned "
                             "FBP, finer fuel types buy nothing."),
            Entry("P2-C3", "control", "MEASURED",
                  title="Fuel rules: CFS tree vs A-11",
                  question="Do the operational CFS rules type fuel better than "
                           "our A-11 thresholds, on the same SCANFI step?",
                  independent="rule set applied to SCANFI pre-fire",
                  dependent="paired within-patch HFI AUC",
                  result="+0.048 on all pixels; +0.081 [+0.060, +0.104] on land, "
                         "where A-11 sits at chance (0.508).",
                  conclusion="A-11 is retired for fuel typing; the CFS tree is "
                             "the SCANFI fuel reference (A-31)."),
            Entry("P2-C4", "measurement", "MEASURED",
                  title="Fuel-type ordering",
                  question="Does FBP order fuel types the way they burned?",
                  independent="fuel type (types with >= 5,000 pixels)",
                  dependent="Spearman rho: mean FBP HFI vs burned share",
                  result="0.26 (CWFIS 2019), 0.29 (SCANFI), 0.02 (2014b); none "
                         "significant.",
                  conclusion="R0's within-patch skill is the coarse contrasts "
                             "(fuel vs not, conifer vs aspen), not FBP's fine "
                             "ordering of types."),
            Entry("P2-C5", "check", "PASS",
                  title="Ignition model reproduces its paper",
                  question="Beverly & Wotton (2007) Table 6 as implemented gives "
                           "the paper's own worked probabilities.",
                  independent="implementation vs the paper's figures",
                  dependent="P(sustained flaming) at the paper's example codes",
                  result="FC3 0.895 at FFMC 86; FC6 0.895 and FC8 0.960 at DMC "
                         "80, FFMC 89 (paper: about 90 %, 90 %, 96 %).",
                  conclusion="The ignition branch runs on the published model "
                             "(A-30)."),
        ),
    ),
)


def by_pid(pid: str) -> Phase:
    for p in PHASES:
        if p.pid == pid:
            return p
    raise KeyError(pid)
