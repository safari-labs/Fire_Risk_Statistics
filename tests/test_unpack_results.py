"""unpack_results.py: checksum checked, layout kept, escapes refused."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("unpack", ROOT / "scripts" / "unpack_results.py")
U = importlib.util.module_from_spec(spec)
spec.loader.exec_module(U)


def _archive(path: Path, members: dict[str, bytes]) -> Path:
    with tarfile.open(path, "w:gz") as tf:
        for name, data in members.items():
            ti = tarfile.TarInfo(name)
            ti.size = len(data)
            tf.addfile(ti, io.BytesIO(data))
    path.with_name(path.name + ".sha256").write_text(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n")
    return path


def test_unpacks_into_exp_and_run(tmp_path):
    a = _archive(tmp_path / "eco_v2__r1.tar.gz", {"eco_v2/r1/f0s0/result.json": b"{}",
                                                  "eco_v2/r1/fits.jsonl": b""})
    assert U.unpack(a, tmp_path / "out") == ["eco_v2/r1"]
    assert (tmp_path / "out" / "eco_v2" / "r1" / "f0s0" / "result.json").exists()


def test_a_corrupted_archive_is_refused(tmp_path):
    a = _archive(tmp_path / "x.tar.gz", {"e/r/a.txt": b"1"})
    a.write_bytes(a.read_bytes() + b"junk")
    with pytest.raises(ValueError, match="sha256"):
        U.unpack(a, tmp_path / "out")


def test_members_escaping_the_destination_are_refused(tmp_path):
    a = _archive(tmp_path / "x.tar.gz", {"../evil.txt": b"1"})
    with pytest.raises(ValueError, match="refusing"):
        U.unpack(a, tmp_path / "out")
    assert not (tmp_path / "evil.txt").exists()
