"""The experiment register, and the ways a register rots.

A plan document is only useful while it is true. The failure mode is not a
crash, it is a table that quietly stops matching the repository: a runner
renamed, an experiment marked runnable after its data moved, a conclusion
field left empty so nobody notices the experiment cannot teach anything
either way.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from safari_bands.experiments import (
    EXPERIMENTS,
    GROUPS,
    STATES,
    Experiment,
    by_group,
    by_id,
    counts,
    runnable,
)

REPO = Path(__file__).resolve().parent.parent
FW = REPO.parent / "Fire_Risk_FW"
MODEL = REPO.parent / "Fire_Risk_Model"


def test_ids_are_unique_and_sequential():
    ids = [e.eid for e in EXPERIMENTS]
    assert len(set(ids)) == len(ids)
    nums = [int(i.split("-")[1]) for i in ids]
    assert nums == list(range(1, len(nums) + 1)), (
        "ids must run E-1..E-N with no gaps; a gap means an experiment was "
        "deleted rather than marked out of reach, and the numbers in every "
        "other document now point somewhere else")


@pytest.mark.parametrize("e", EXPERIMENTS, ids=lambda e: e.eid)
def test_every_field_is_populated(e: Experiment):
    assert e.name and e.independent and e.dependent and e.conclusion
    assert e.group in GROUPS
    assert e.state in STATES


@pytest.mark.parametrize("e", EXPERIMENTS, ids=lambda e: e.eid)
def test_an_unrunnable_experiment_names_its_blocker(e: Experiment):
    """Otherwise "not runnable" is a shrug rather than a to-do."""
    if not e.runnable:
        assert e.blocker, (
            f"{e.eid} is {e.state} but names no blocker, so nothing says "
            f"what would unblock it")


@pytest.mark.parametrize("e", EXPERIMENTS, ids=lambda e: e.eid)
def test_a_runnable_experiment_names_a_runner(e: Experiment):
    if e.runnable:
        assert e.runner != "--", (
            f"{e.eid} claims to be runnable today but names no command")


def _scripts_referenced(runner: str) -> list[str]:
    return re.findall(r"[\w./-]+\.(?:sh|py)", runner)


@pytest.fixture(scope="session")
def script_names() -> set[str]:
    """Every script basename in the three repos' script directories.

    Built once and scoped to scripts/ rather than rglob-ing whole repos per
    experiment: the repos contain data directories, and walking them 31
    times turned a millisecond check into minutes.
    """
    names: set[str] = set()
    for root in (FW, MODEL, REPO):
        if not root.exists():
            continue
        for sub in ("scripts", "src"):
            d = root / sub
            if not d.exists():
                continue
            for pat in ("*.py", "*.sh"):
                names.update(f.name for f in d.rglob(pat)
                             if ".venv" not in f.parts)
    return names


@pytest.mark.parametrize("e", EXPERIMENTS, ids=lambda e: e.eid)
def test_named_runners_exist_on_disk(e: Experiment, script_names):
    """Every script named in the register must be a real file.

    The check that catches a rename. The register is read by someone
    deciding what to launch, and a command that does not exist wastes their
    time at exactly the moment they are trying to start.
    """
    if not script_names:
        pytest.skip("sibling repos not checked out next to this one")
    for name in _scripts_referenced(e.runner):
        base = Path(name).name
        assert base in script_names, (
            f"{e.eid} names {base}, which exists in no scripts/ or src/ "
            f"directory")


def test_state_counts_add_up():
    assert sum(counts().values()) == len(EXPERIMENTS)


def test_groups_partition_the_register():
    assert sum(len(v) for v in by_group().values()) == len(EXPERIMENTS)


def test_by_id_round_trips():
    for e in EXPERIMENTS:
        assert by_id(e.eid) is e
    with pytest.raises(KeyError):
        by_id("E-999")


def test_the_primaries_are_marked_and_few():
    """The star is only useful while it is rare."""
    starred = [e for e in EXPERIMENTS if "primary" in e.tags]
    assert 1 <= len(starred) <= 4, [e.eid for e in starred]


def test_controls_exist_and_are_marked():
    """A positive finding is not reportable without them."""
    ctl = [e for e in EXPERIMENTS if "control" in e.tags]
    assert len(ctl) >= 3, "label, cohort and negative controls at minimum"


def test_something_is_runnable():
    """A register where nothing can run is a wish list."""
    assert runnable()


def test_blocked_experiments_do_not_claim_a_working_runner():
    """E-16 is the case: it must not look launchable."""
    for e in EXPERIMENTS:
        if e.state == "BLOCKED":
            assert e.runner.startswith("--"), (
                f"{e.eid} is blocked but its runner reads as a command")


@pytest.mark.parametrize("e", EXPERIMENTS, ids=lambda e: e.eid)
def test_every_experiment_states_a_hypothesis(e: Experiment):
    assert e.hypothesis, (
        f"{e.eid} has no hypothesis. An experiment without a prediction "
        f"cannot be wrong, and one that cannot be wrong is not worth the "
        f"queue time")


@pytest.mark.parametrize("e", EXPERIMENTS, ids=lambda e: e.eid)
def test_a_runnable_hypothesis_says_what_would_refute_it(e: Experiment):
    """Falsifiability, checked crudely but usefully.

    CLAUDE.md: the study's job is to TEST the brief's hypotheses, not to
    confirm them. A prediction with no stated failure condition drifts into
    a statement of belief, and the first ambiguous result gets read as
    support for it.

    Only required where the experiment can actually run -- for the
    out-of-reach ones the honest hypothesis is often "none offered".
    """
    if not e.runnable:
        return
    lowered = e.hypothesis.lower()
    assert any(k in lowered for k in ("wrong if", "unless", "refut",
                                      "would be surprising", "anything else")), (
        f"{e.eid} predicts an outcome but never says what would refute it: "
        f"{e.hypothesis[:120]}")


# ---------------------------------------------------------------------------
# Resources: what the register says a task asks for is what it asks for
# ---------------------------------------------------------------------------

def _wrapper_of(runner: str) -> Path | None:
    m = re.search(r"(sweep_\w+\.sh)", runner)
    if not m:
        return None
    hit = FW / "scripts" / "shell" / m.group(1)
    return hit if hit.exists() else None


@pytest.mark.parametrize("e", EXPERIMENTS, ids=lambda e: e.eid)
def test_a_launchable_experiment_states_its_resources(e: Experiment):
    """A runnable experiment with a wrapper must say what it asks Narval for.
    A request nobody wrote down is a request nobody checked."""
    if e.runnable and _wrapper_of(e.runner):
        assert e.resources, f"{e.eid} launches a job but states no resources"


@pytest.mark.parametrize("e", EXPERIMENTS, ids=lambda e: e.eid)
def test_stated_walltime_is_what_the_wrapper_requests(e: Experiment):
    """The register documents; the wrapper decides. If they disagree, one
    of them is stale, and it is usually the one people read."""
    m = re.search(r"--time=(\S+)", e.resources)
    w = _wrapper_of(e.runner)
    if not (m and w):
        return
    assert m.group(1).rstrip(";,") in w.read_text(encoding="utf-8"), (
        f"{e.eid} says --time={m.group(1)} but {w.name} does not request it")


def test_nothing_runnable_rests_on_the_circular_pack():
    """Every runnable experiment reads the pack the sweep defaults to, and
    that default must be the NBAC pack -- the dNBR one is circular."""
    sh = FW / "scripts" / "shell" / "sweep_bands.sh"
    if not sh.exists():
        pytest.skip("Fire_Risk_FW not checked out alongside")
    text = sh.read_text(encoding="utf-8")
    assert "stage2_fire_11band_nbac" in text
