"""The protected-vintage guard: frozen files cannot be overwritten by the data pipeline."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from kagura import ROOT, align, data, vintage
from kagura.vintage import ProtectedVintageError


def frozen_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A data dir whose raw/usdjpy.csv is declared frozen (the real table cannot be faked)."""
    f = tmp_path / "raw" / "usdjpy.csv"
    f.parent.mkdir()
    f.write_text("observation_date,DEXJPUS\n2026-09-11,147.0\n")
    monkeypatch.setattr(vintage, "FROZEN_SHA256", {"raw/usdjpy.csv": vintage.sha256(f)})
    return tmp_path


def test_any_frozen_file_protects_the_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    d = frozen_dir(tmp_path, monkeypatch)
    assert vintage.protected_files(d) == ["raw/usdjpy.csv"]
    with pytest.raises(ProtectedVintageError, match="refusing to overwrite"):
        vintage.ensure_writable(d)


def test_a_different_vintage_is_writable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    d = frozen_dir(tmp_path, monkeypatch)
    (d / "raw" / "usdjpy.csv").write_text("a later download\n")
    vintage.ensure_writable(d)
    vintage.ensure_writable(tmp_path / "empty")


def test_download_refuses_before_fetching_into_a_frozen_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    d = frozen_dir(tmp_path, monkeypatch)
    monkeypatch.setattr(data, "DATA", d)

    def no_fetch(url: str) -> bytes:
        raise AssertionError("fetched although the directory is protected")

    monkeypatch.setattr(data, "fetch", no_fetch)
    with pytest.raises(ProtectedVintageError):
        data.build()


def test_failed_download_writes_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(data, "DATA", tmp_path)
    monkeypatch.setattr(data, "DATA_RAW", tmp_path / "raw")
    monkeypatch.setattr(data, "DATA_PROCESSED", tmp_path / "processed")
    monkeypatch.setattr(data, "fetch", lambda url: b"<html>503 Service Unavailable</html>")
    with pytest.raises(Exception):  # noqa: B017 - any parse failure; the point is what follows
        data.build()
    assert not any(tmp_path.iterdir())


def test_align_refuses_to_rebuild_a_frozen_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(align, "DATA", frozen_dir(tmp_path, monkeypatch))
    with pytest.raises(ProtectedVintageError):
        align.build()


def test_local_frozen_vintage_is_protected() -> None:
    if not vintage.protected_files(ROOT / "data"):
        pytest.skip("frozen vintage not present in data/")
    with pytest.raises(ProtectedVintageError):
        vintage.ensure_writable(ROOT / "data")


# --- review additions: partial vintages, symlinks, KAGURA_DATA, fresh downloads, H1a source --


def frozen_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A stand-in frozen data dir: one checksummed raw file plus unchecksummed vintage files."""
    frozen = tmp_path / "frozen"
    (frozen / "raw").mkdir(parents=True)
    (frozen / "processed").mkdir()
    (frozen / "raw" / "usdjpy.csv").write_text("frozen usdjpy\n")
    (frozen / "raw" / "brent.csv").write_text("frozen brent\n")  # not in the checksum table
    (frozen / "processed" / "series_long.csv").write_text("frozen long\n")
    table = {"raw/usdjpy.csv": vintage.sha256(frozen / "raw" / "usdjpy.csv")}
    monkeypatch.setattr(vintage, "FROZEN_SHA256", table)
    monkeypatch.setattr(vintage, "FROZEN_DIR", frozen)
    return frozen


def test_part_of_the_vintage_is_enough_to_protect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    f = tmp_path / "processed" / "daily.csv"
    f.parent.mkdir()
    f.write_text("frozen daily\n")
    table = {"processed/daily.csv": vintage.sha256(f), "raw/usdjpy.csv": "0" * 64}
    monkeypatch.setattr(vintage, "FROZEN_SHA256", table)
    assert vintage.protected_files(tmp_path) == ["processed/daily.csv"]  # usdjpy absent
    with pytest.raises(ProtectedVintageError):
        vintage.ensure_writable(tmp_path, frozen_dir=tmp_path / "elsewhere")


@pytest.mark.parametrize("link", ["dir", "raw", "file", "processed_file"])
def test_symlinks_into_the_frozen_vintage_are_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, link: str
) -> None:
    frozen = frozen_tree(tmp_path, monkeypatch)
    target = tmp_path / "current"
    if link == "dir":
        target.symlink_to(frozen)
    elif link == "raw":
        target.mkdir()
        (target / "raw").symlink_to(frozen / "raw")
    elif link == "file":  # an unchecksummed frozen file reached through a file symlink
        (target / "raw").mkdir(parents=True)
        (target / "raw" / "brent.csv").symlink_to(frozen / "raw" / "brent.csv")
    else:
        (target / "processed").mkdir(parents=True)
        (target / "processed" / "series_long.csv").symlink_to(frozen / "processed/series_long.csv")
    with pytest.raises(ProtectedVintageError):
        vintage.ensure_writable(target)


def test_downloader_will_not_write_through_a_file_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    frozen = frozen_tree(tmp_path, monkeypatch)
    current = tmp_path / "current"
    (current / "raw").mkdir(parents=True)
    (current / "raw" / "brent.csv").symlink_to(frozen / "raw" / "brent.csv")
    monkeypatch.setattr(data, "DATA", current)
    monkeypatch.setattr(data, "fetch", lambda url: pytest.fail("fetched into a protected dir"))
    with pytest.raises(ProtectedVintageError):
        data.build()
    assert (frozen / "raw" / "brent.csv").read_text() == "frozen brent\n"


def test_frozen_folders_stay_protected_when_files_are_modified_or_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Protection is by path: damaging the vintage must not switch the guard off.
    frozen = frozen_tree(tmp_path, monkeypatch)
    (frozen / "raw" / "usdjpy.csv").write_text("edited\n")  # checksum no longer matches
    assert vintage.protected_files(frozen) == []
    with pytest.raises(ProtectedVintageError):
        vintage.ensure_writable(frozen)
    for f in [*(frozen / "raw").iterdir(), *(frozen / "processed").iterdir()]:
        f.unlink()  # every frozen file gone
    with pytest.raises(ProtectedVintageError):
        vintage.ensure_writable(frozen)
    (frozen / "raw").rmdir()
    (frozen / "processed").rmdir()  # even the folders gone
    with pytest.raises(ProtectedVintageError):
        vintage.ensure_writable(frozen)


def test_symlinks_are_refused_without_any_checksum_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    frozen = frozen_tree(tmp_path, monkeypatch)
    monkeypatch.setattr(vintage, "FROZEN_SHA256", {})  # no file counts as frozen by content
    current = tmp_path / "current"
    (current / "processed").mkdir(parents=True)
    (current / "processed" / "series_long.csv").symlink_to(frozen / "processed/series_long.csv")
    with pytest.raises(ProtectedVintageError):
        vintage.ensure_writable(current)
    link = tmp_path / "dirlink"
    link.symlink_to(frozen)
    with pytest.raises(ProtectedVintageError):
        vintage.ensure_writable(link)


def test_separate_destinations_remain_writable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    frozen = frozen_tree(tmp_path, monkeypatch)
    vintage.ensure_writable(frozen / "current")  # a sibling inside data/, e.g. data/current
    vintage.ensure_writable(tmp_path / "elsewhere" / "data")  # an absolute path elsewhere
    other = tmp_path / "other"
    (other / "raw").mkdir(parents=True)
    (other / "raw" / "usdjpy.csv").write_text("a later download\n")
    vintage.ensure_writable(other)  # an existing non-frozen dataset may be refreshed


def test_canonical_data_dir_refused_and_data_current_allowed() -> None:
    # The real paths: data/ is refused by path alone; data/current (the README example) is not.
    with pytest.raises(ProtectedVintageError):
        vintage.ensure_writable(ROOT / "data", frozen_dir=ROOT / "data")
    vintage.ensure_writable(ROOT / "data" / "current", frozen_dir=ROOT / "data")


def kagura_data(env_value: str | None, code: str) -> str:
    """Run ``code`` in a fresh interpreter with KAGURA_DATA set (or unset); return stdout."""
    env = {k: v for k, v in os.environ.items() if k != "KAGURA_DATA"}
    if env_value is not None:
        env["KAGURA_DATA"] = env_value
    out = subprocess.run(
        [sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True
    )
    return out.stdout.strip()


def test_kagura_data_resolves_absolute_relative_and_empty_paths(tmp_path: Path) -> None:
    show = "import kagura; print(kagura.DATA); print(kagura.DATA_RAW)"
    assert kagura_data(str(tmp_path), show).splitlines() == [str(tmp_path), str(tmp_path / "raw")]
    assert kagura_data("data/current", show).splitlines()[0] == str(ROOT / "data/current")
    assert kagura_data("", show).splitlines()[0] == str(ROOT / "data")
    assert kagura_data(None, show).splitlines()[0] == str(ROOT / "data")


FAKE_SOURCES = r'''
import pandas as pd
from kagura import data

def fake_fetch(url):
    """Offline stand-in for each source, in that source's real format."""
    days = pd.bdate_range("2024-01-01", "2024-12-31")
    months = pd.date_range("2023-01-01", "2024-12-01", freq="MS")
    if "mof.go.jp" in url:
        rows = [f"{d.year}/{d.month}/{d.day},0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0"
                for d in days]
        text = "Interest Rate,,,\nDate,1Y,2Y,3Y,4Y,5Y,6Y,7Y,8Y,9Y,10Y\n" + "\n".join(rows)
    elif "bis.org" in url:
        text = "TIME_PERIOD,OBS_VALUE\n" + "\n".join(f"{m:%Y-%m},100.0" for m in months)
    else:
        sid = url.rsplit("=", 1)[1]
        dates = months if sid in ("IRSTCI01JPM156N", "CPIAUCSL") else days
        text = f"observation_date,{sid}\n" + "\n".join(f"{d:%Y-%m-%d},2.5" for d in dates)
    return text.encode()

data.fetch = fake_fetch
'''


def test_fresh_download_goes_to_kagura_data_and_leaves_frozen_files_untouched(
    tmp_path: Path,
) -> None:
    frozen = {p: (p.stat().st_mtime_ns, vintage.sha256(p)) for p in frozen_files()}
    code = FAKE_SOURCES + (
        "from kagura import align, DATA\n"
        "data.build(); daily, monthly = align.build()\n"
        "print(DATA); print(len(daily), len(monthly))\n"
    )
    out = kagura_data(str(tmp_path / "current"), code).splitlines()
    assert out[0] == str(tmp_path / "current") and int(out[1].split()[0]) > 200
    for rel in (
        "raw/manifest.json",
        "raw/usdjpy.csv",
        "processed/series_long.csv",
        "processed/daily.csv",
        "processed/monthly.csv",
    ):
        assert (tmp_path / "current" / rel).is_file(), rel
    assert {p: (p.stat().st_mtime_ns, vintage.sha256(p)) for p in frozen_files()} == frozen


def frozen_files() -> list[Path]:
    """Every file of the local frozen vintage (checksummed or not); empty if absent."""
    return sorted(p for sub in ("raw", "processed") for p in (ROOT / "data" / sub).glob("*.*"))


def test_h1a_reads_the_frozen_dir_whatever_kagura_data_says(tmp_path: Path) -> None:
    source = (ROOT / "src/kagura/h1a.py").read_text()
    assert "DATA_PROCESSED" not in source and "KAGURA_DATA" not in source
    assert "from kagura import ROOT" in source
    if not vintage.protected_files(ROOT / "data"):
        pytest.skip("frozen vintage not present in data/")
    # A tampered copy in KAGURA_DATA is ignored; H1a verifies and loads ROOT/data.
    (tmp_path / "processed").mkdir()
    (tmp_path / "processed" / "daily.csv").write_text("date,usdjpy\n2030-01-01,1\n")
    code = (
        "from kagura import h1a, DATA\n"
        "d = h1a.load_verified()\n"
        "print(DATA); print(d.daily['date'].max().date())\n"
    )
    out = kagura_data(str(tmp_path), code).splitlines()
    assert out == [str(tmp_path), "2026-09-11"]
