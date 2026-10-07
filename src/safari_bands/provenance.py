"""Run directories: outputs, resolved config, git commit hash and seed.

Project convention: seed every stochastic step, and write each run's outputs,
resolved config and git commit hash to ``runs/<YYYYMMDD-HHMM>_<name>/``.

Built in Phase 0 although Phase 0 produces no scientific outputs, because every
later phase writes runs and they should all write them the same way. A band
selection result that cannot be traced to the exact config and commit that
produced it is not evidence.
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from safari_bands import __version__
from safari_bands.config.loader import project_root

RUN_TIMESTAMP_FORMAT = "%Y%m%d-%H%M"


def git_commit_hash(repo: Path | None = None) -> str:
    """Return the current commit hash, or a marker when it cannot be determined."""
    cwd = repo or project_root()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return "UNKNOWN (git unavailable)"
    if result.returncode != 0:
        return "UNKNOWN (no commits yet or not a git repository)"
    return result.stdout.strip()


def git_is_dirty(repo: Path | None = None) -> bool | None:
    """Whether the working tree has uncommitted changes.

    ``None`` when it cannot be determined. A dirty tree means the commit hash
    does not fully describe the code that ran, which a results note must say.
    """
    cwd = repo or project_root()
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return bool(result.stdout.strip())


def _to_plain(value: Any) -> Any:
    """Convert pydantic models and mappings into YAML-safe plain data."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(k): _to_plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_plain(v) for v in value]
    return value


@dataclass
class Run:
    """A single execution, with its own output directory."""

    name: str
    seed: int
    directory: Path
    started_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    def path(self, *parts: str) -> Path:
        """Path inside the run directory, creating parent directories."""
        target = self.directory.joinpath(*parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def write_resolved_config(self, **configs: Any) -> Path:
        """Write the fully resolved configuration this run used."""
        target = self.path("resolved_config.yaml")
        payload = {key: _to_plain(value) for key, value in configs.items()}
        with target.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(payload, handle, sort_keys=False, allow_unicode=True)
        return target

    def write_text(self, filename: str, text: str) -> Path:
        target = self.path(filename)
        target.write_text(text, encoding="utf-8")
        return target

    def write_json(self, filename: str, data: Any) -> Path:
        target = self.path(filename)
        target.write_text(json.dumps(_to_plain(data), indent=2), encoding="utf-8")
        return target

    def finalise(self, **extra: Any) -> Path:
        """Write the provenance record. Call once the run's work is done."""
        dirty = git_is_dirty()
        record = {
            "run_name": self.name,
            "seed": self.seed,
            "started_at": self.started_at.isoformat(),
            "finished_at": datetime.now(UTC).isoformat(),
            "git_commit": git_commit_hash(),
            "git_dirty": dirty,
            "safari_bands_version": __version__,
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            **self.metadata,
            **extra,
        }
        if dirty:
            record["warning"] = (
                "Working tree had uncommitted changes; the commit hash does not "
                "fully describe the code that produced these outputs."
            )
        target = self.path("provenance.json")
        target.write_text(json.dumps(record, indent=2), encoding="utf-8")
        return target


def start_run(
    name: str,
    seed: int = 0,
    runs_root: Path | None = None,
    **metadata: Any,
) -> Run:
    """Create ``runs/<YYYYMMDD-HHMM>_<name>/`` and return a :class:`Run`.

    A suffix is appended if the directory already exists, so two runs started
    in the same minute never overwrite each other.
    """
    root = runs_root or project_root() / "runs"
    started = datetime.now(UTC)
    stamp = started.strftime(RUN_TIMESTAMP_FORMAT)

    directory = root / f"{stamp}_{name}"
    suffix = 1
    while directory.exists():
        suffix += 1
        directory = root / f"{stamp}_{name}_{suffix}"
    directory.mkdir(parents=True)

    return Run(
        name=name,
        seed=seed,
        directory=directory,
        started_at=started,
        metadata=dict(metadata),
    )
