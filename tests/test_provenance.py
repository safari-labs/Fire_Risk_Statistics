"""Run directories record enough to reproduce a result."""

from __future__ import annotations

import json

import yaml

from safari_bands.provenance import RUN_TIMESTAMP_FORMAT, git_commit_hash, start_run


def test_run_directory_is_named_by_timestamp_and_name(tmp_path):
    run = start_run("demo", seed=42, runs_root=tmp_path)
    assert run.directory.is_dir()
    stamp, _, name = run.directory.name.partition("_")
    assert name == "demo"
    assert len(stamp) == len(run.started_at.strftime(RUN_TIMESTAMP_FORMAT))


def test_two_runs_in_the_same_minute_do_not_collide(tmp_path):
    first = start_run("demo", runs_root=tmp_path)
    second = start_run("demo", runs_root=tmp_path)
    assert first.directory != second.directory
    assert second.directory.is_dir()


def test_resolved_config_round_trips(tmp_path, band_sets):
    run = start_run("demo", seed=7, runs_root=tmp_path)
    target = run.write_resolved_config(band_sets={"config_b": band_sets["config_b"]})

    written = yaml.safe_load(target.read_text(encoding="utf-8"))
    bands = written["band_sets"]["config_b"]["bands"]
    centres = [b["centre_nm"] for b in bands]

    assert 1240.0 in centres
    assert 1610.0 in centres


def test_finalise_records_seed_and_commit(tmp_path):
    run = start_run("demo", seed=1234, runs_root=tmp_path)
    target = run.finalise()

    record = json.loads(target.read_text(encoding="utf-8"))
    assert record["seed"] == 1234
    assert record["run_name"] == "demo"
    assert record["git_commit"] == git_commit_hash()
    assert "python_version" in record
    assert "finished_at" in record


def test_dirty_tree_is_flagged(tmp_path, monkeypatch):
    """A dirty tree means the commit hash does not describe what ran."""
    monkeypatch.setattr("safari_bands.provenance.git_is_dirty", lambda repo=None: True)
    run = start_run("demo", runs_root=tmp_path)
    record = json.loads(run.finalise().read_text(encoding="utf-8"))

    assert record["git_dirty"] is True
    assert "uncommitted changes" in record["warning"]


def test_run_path_creates_parent_directories(tmp_path):
    run = start_run("demo", runs_root=tmp_path)
    target = run.path("figures", "spectra.png")
    assert target.parent.is_dir()


def test_write_json_and_text(tmp_path):
    run = start_run("demo", runs_root=tmp_path)
    run.write_text("notes.txt", "hello")
    run.write_json("data.json", {"a": 1})

    assert (run.directory / "notes.txt").read_text(encoding="utf-8") == "hello"
    assert json.loads((run.directory / "data.json").read_text(encoding="utf-8")) == {"a": 1}
