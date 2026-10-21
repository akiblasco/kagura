"""Protected data vintages: checksums of frozen files, and a guard against overwriting them.

The ADR 0006 vintage (downloaded 2026-09-15) lives in data/raw and data/processed. It is
not redistributed, so overwriting it would make the H1a result irreproducible. Every
writer of a data directory (``kagura.data.build``, ``kagura.align.build``) calls
``ensure_writable`` first. Fresh downloads go to another directory via ``KAGURA_DATA``.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from kagura import ROOT

# Where the frozen vintage lives. H1a always reads this directory (kagura.h1a).
FROZEN_DIR = ROOT / "data"

# ADR 0006 §9.2, paths relative to the data directory. Frozen: do not edit.
FROZEN_SHA256 = {
    "processed/daily.csv": "edfc95cf676d3647b6af3667b3b34fc74b4b6e692d750bf6ab8008de9105cd99",
    "processed/monthly.csv": "3f19c005d8db1ab1963488b2af748dcb6f956fe3a6a6cf6f4acdafda92a56215",
    "raw/manifest.json": "c0f5676e888751690cf8a5ad86df63c8727b5a02f63302b33fb535e315bee51c",
    "raw/usdjpy.csv": "0ea1de1993e69827ccfdddc390af8f8f5abf15c566f4c4cd5a6072495b773965",
    "raw/us_2y.csv": "1289774410381729569844068b657a7cc11a56a699669509bf6ed26a0db572a4",
    "raw/us_10y.csv": "94c1e5b98460d7de645be32f3211853c3d749724ecb12cac33bc84623ea759b4",
    "raw/jgb.csv": "997a8f95dc20c884d506c627ac075b1e93a357410094058ac19f3effead2e353",
    "raw/jgb_current.csv": "8da8cc83668bf280f1849ce2e6fab752881fc771b87d4691887bdb85e2f9f519",
}


class ProtectedVintageError(RuntimeError):
    """A write was attempted into a data directory that holds a protected vintage."""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def protected_files(data_dir: Path) -> list[str]:
    """Files in ``data_dir`` that are byte-for-byte part of the frozen vintage."""
    return [
        rel
        for rel, want in FROZEN_SHA256.items()
        if (data_dir / rel).is_file() and sha256(data_dir / rel) == want
    ]


def _links_into_frozen(data_dir: Path, frozen_dir: Path) -> list[str]:
    """Paths under ``data_dir``/raw and /processed (the folders, or files in them) that
    resolve, through any symlink, into the frozen directory's raw/ or processed/ folder.

    Writing to such a path would overwrite frozen-vintage files, including ones ADR 0006
    does not checksum (e.g. raw/brent.csv, processed/series_long.csv)."""
    if not protected_files(frozen_dir):
        return []
    guarded = [(frozen_dir / sub).resolve() for sub in ("raw", "processed")]
    hits = []
    for sub in ("raw", "processed"):
        folder = data_dir / sub
        for path in [folder, *(folder.iterdir() if folder.is_dir() else [])]:
            real = path.resolve()
            if any(real == g or g in real.parents for g in guarded):
                hits.append(str(path))
    return hits


def ensure_writable(data_dir: Path, frozen_dir: Path | None = None) -> None:
    """Refuse to write into ``data_dir`` if it holds any frozen file, or if any of its
    write targets resolves (through symlinks) into the frozen directory's raw/ or
    processed/ folder. Any single checksum match protects the whole directory: its other
    files (e.g. series_long.csv) belong to the same vintage even though ADR 0006 does not
    checksum them. ``frozen_dir`` defaults to FROZEN_DIR (read at call time)."""
    found = protected_files(data_dir) or _links_into_frozen(
        data_dir, FROZEN_DIR if frozen_dir is None else frozen_dir
    )
    if found:
        raise ProtectedVintageError(
            f"{data_dir} holds the frozen ADR 0006 vintage ({', '.join(found)}); refusing to "
            "overwrite it. Download into another directory instead, e.g.\n"
            "    KAGURA_DATA=data/current make data"
        )
