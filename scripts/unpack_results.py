"""scripts/unpack_results.py

Check and unpack a run archive from the cluster (Fire_Risk_FW
scripts/shell/bundle_run.sh) into narval_results/.

    python scripts/unpack_results.py narval_results/eco_v2__20261029-1410.tar.gz

Verifies the archive against its .sha256 beside it, refuses any member that
would land outside narval_results/ (absolute paths, '..'), unpacks keeping the
<exp>/<run_id>/... layout, and lists what arrived. The archive is kept unless
--remove is given.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "narval_results"


def sha256(path: Path, chunk: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while b := fh.read(chunk):
            h.update(b)
    return h.hexdigest()


def safe_members(tf: tarfile.TarFile, dest: Path):
    root = dest.resolve()
    for m in tf.getmembers():
        target = (dest / m.name).resolve()
        if m.issym() or m.islnk() or not target.is_relative_to(root):
            raise ValueError(f"refusing archive member {m.name!r}")
        yield m


def unpack(archive: Path, dest: Path = DEST) -> list[str]:
    sums = archive.with_name(archive.name + ".sha256")
    if not sums.exists():
        raise FileNotFoundError(f"no checksum file {sums.name} beside the archive")
    want = sums.read_text().split()[0]
    if sha256(archive) != want:
        raise ValueError(f"{archive.name}: sha256 does not match {sums.name}")
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:gz") as tf:
        members = list(safe_members(tf, dest))
        tf.extractall(dest, members=members, filter="data")
    return sorted({"/".join(m.name.split("/")[:2]) for m in members if m.isfile()})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("archive", type=Path)
    ap.add_argument("--dest", type=Path, default=DEST)
    ap.add_argument("--remove", action="store_true", help="delete the archive afterwards")
    args = ap.parse_args(argv)
    runs = unpack(args.archive, args.dest)
    for r in runs:
        n = sum(1 for p in (args.dest / r).rglob("*") if p.is_file())
        print(f"  {args.dest.name}/{r}: {n} files")
    if args.remove:
        args.archive.unlink()
        args.archive.with_name(args.archive.name + ".sha256").unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
