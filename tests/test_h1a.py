"""Checks of the H1a orchestration, frozen-data verification and the 02 notebook.

Everything here uses synthetic data except ``test_real_data_is_the_frozen_vintage``, which
only hashes and schema-checks the local files (no model is estimated on them)."""

import ast
import json
import math
import re
from dataclasses import astuple
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import pytest

from kagura import ROOT, explore, h1a, models
from kagura.align import build_daily, build_monthly
from kagura.explore import changes
from kagura.h1a import IntegrityError

matplotlib.use("Agg")

ADR = (ROOT / "docs/decisions/0006-h1-formal-testing-protocol.md").read_text()
NOTEBOOK = ROOT / "notebooks/02_h1a_formal.ipynb"


# --- synthetic data in the shape of data/processed --------------------------------------------


def synthetic_long(seed: int = 0) -> pd.DataFrame:
    """Long table with every series the alignment needs, 1980-11 to the frozen end date.

    USD/JPY comoves with the 2Y differential (beta = 5); a few Tokyo holidays create
    carried JGB values, so the ADR 0004 exclusion rule has work to do."""
    rng = np.random.default_rng(seed)
    days = pd.bdate_range("1980-11-03", models.DAILY_END)
    n = len(days)
    walk = {
        k: rng.normal(scale=s, size=n).cumsum()
        for k, s in (("us_2y", 0.06), ("us_10y", 0.05), ("jgb_2y", 0.03), ("jgb_10y", 0.03))
    }
    ddiff = np.diff(walk["us_2y"] - walk["jgb_2y"], prepend=0.0)
    series = {
        "usdjpy": 200 * np.exp(np.cumsum(5.0 * ddiff + rng.normal(scale=0.5, size=n)) / 100),
        "us_2y": 5 + walk["us_2y"],
        "us_10y": 6 + walk["us_10y"],
        "jgb_2y": 1 + walk["jgb_2y"],
        "jgb_10y": 2 + walk["jgb_10y"],
        "fed_funds": np.full(n, 3.0),
        "brent": np.full(n, 60.0),
        "vix": np.full(n, 20.0),
    }
    holidays = set(rng.choice(n, size=200, replace=False))
    rows = [
        (d, name, v)
        for name, values in series.items()
        for i, (d, v) in enumerate(zip(days, values, strict=True))
        if not (name.startswith("jgb") and i in holidays)
    ]
    months = pd.date_range("1979-01-01", "2026-08-01", freq="MS")
    for name in ("us_cpi", "jp_cpi", "jp_call_rate"):
        rows += [(d, name, 100.0 + i * 0.1) for i, d in enumerate(months)]
    return pd.DataFrame(rows, columns=["date", "series", "value"])


@pytest.fixture(scope="module")
def frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    long = synthetic_long()
    daily = build_daily(long)
    return daily, build_monthly(long, daily)


def write_vintage(root: Path, daily: pd.DataFrame, monthly: pd.DataFrame) -> dict[str, str]:
    """Write files in the data/ layout (as align.build does) and return their checksums."""
    (root / "data/processed").mkdir(parents=True)
    (root / "data/raw").mkdir(parents=True)
    daily.to_csv(root / "data/processed/daily.csv", index=False, date_format="%Y-%m-%d")
    monthly.to_csv(root / "data/processed/monthly.csv", index=False, date_format="%Y-%m-%d")
    for rel in h1a.FROZEN_SHA256:
        if rel.startswith("raw/"):
            (root / "data" / rel).write_text(f"synthetic {rel}\n")
    return {rel: h1a.sha256(root / "data" / rel) for rel in h1a.FROZEN_SHA256}


# --- the code agrees with the frozen ADR ------------------------------------------------------


def test_frozen_checksums_are_exactly_the_adr_table() -> None:
    table = dict(re.findall(r"^\| ((?:processed|raw)/\S+) \| `([0-9a-f]{64})` \|$", ADR, re.M))
    assert table == h1a.FROZEN_SHA256


def test_frozen_constants_match_the_adr_text() -> None:
    assert "1981-01-01 to **2026-09-11**" in ADR and models.DAILY_END == "2026-09-11"
    assert "1981-01 to **2026-08**" in ADR and models.MONTHLY_END.startswith("2026-08")
    assert "α = 0.025" in ADR and models.ALPHA == 0.025
    assert "χ²(4), α = 0.05" in ADR and models.WALD_ALPHA == 0.05
    assert "δ = β_new − (2/3) · β_ref" in ADR and models.MATERIAL == pytest.approx(1 / 3)
    assert "**ref**: 2013–2021 | 2013-01-01 | 2021-12-31" in ADR
    assert models.REF == "2013–2021" and explore.ERAS[models.REF] == ("2013-01-01", "2021-12-31")
    assert "**new**: 2022– | 2022-01-01" in ADR and explore.ERAS[models.NEW][0] == "2022-01-01"
    assert explore.WINDOWS == {"1y": 250, "3y": 750} and explore.MIN_SHARE == 0.8


# --- checksum verification --------------------------------------------------------------------


def test_verify_checksums_passes_on_untouched_files(
    tmp_path: Path, frames: tuple[pd.DataFrame, pd.DataFrame]
) -> None:
    expected = write_vintage(tmp_path, *frames)
    h1a.verify_checksums(tmp_path, expected)
    assert set(expected) == set(h1a.FROZEN_SHA256)


def test_any_byte_change_or_missing_file_stops_with_every_problem_listed(
    tmp_path: Path, frames: tuple[pd.DataFrame, pd.DataFrame]
) -> None:
    expected = write_vintage(tmp_path, *frames)
    daily_csv = tmp_path / "data/processed/daily.csv"
    daily_csv.write_bytes(daily_csv.read_bytes().replace(b"\n", b"\r\n", 1))  # one byte
    (tmp_path / "data/raw/jgb.csv").unlink()
    with pytest.raises(IntegrityError) as err:
        h1a.verify_checksums(tmp_path, expected)
    msg = str(err.value)
    assert "checksum mismatch: processed/daily.csv" in msg and "missing: raw/jgb.csv" in msg
    assert "refusing to run" in msg


def test_load_verified_returns_nothing_when_data_were_modified(
    tmp_path: Path, frames: tuple[pd.DataFrame, pd.DataFrame]
) -> None:
    expected = write_vintage(tmp_path, *frames)
    data = h1a.load_verified(tmp_path, expected)
    daily, monthly = data.daily, data.monthly
    assert daily["date"].iloc[-1] == pd.Timestamp(models.DAILY_END)
    assert monthly["date"].dt.to_period("M").iloc[-1] == pd.Period("2026-08", "M")
    monthly_csv = tmp_path / "data/processed/monthly.csv"
    monthly_csv.write_text(monthly_csv.read_text().replace("2026-08-31", "2026-08-30"))
    with pytest.raises(IntegrityError, match="monthly.csv"):
        h1a.load_verified(tmp_path, expected)


def test_sha256_matches_hashlib_reference(tmp_path: Path) -> None:
    import hashlib

    p = tmp_path / "f.bin"
    p.write_bytes(bytes(range(256)) * 10_000)  # larger than one read block
    assert h1a.sha256(p) == hashlib.sha256(p.read_bytes()).hexdigest()


# --- schema and boundary validation -----------------------------------------------------------


def test_validate_daily_accepts_the_expected_shape_and_rejects_each_violation(
    frames: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    daily, _ = frames
    h1a.validate_daily(daily)
    cases = {
        "missing columns": daily.drop(columns="jgb_10y"),
        "strictly increasing": daily.iloc[::-1],
        "no gaps": daily.assign(usdjpy=daily["usdjpy"].where(daily.index != 500)),
        "after 1981-01-01": daily[daily["date"] >= "1982-01-01"],
        "expected 2026-09-11": daily.iloc[:-1],
    }
    for match, bad in cases.items():
        with pytest.raises(IntegrityError, match=match):
            h1a.validate_daily(bad)


def test_validate_monthly_accepts_the_expected_shape_and_rejects_each_violation(
    frames: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    _, monthly = frames
    h1a.validate_monthly(monthly)
    cases = {
        "missing columns": monthly.drop(columns="diff_10y"),
        "one row per calendar month": monthly.drop(index=200),
        "base month": monthly[monthly["date"] >= "1981-01-01"],
        "expected 2026-08": monthly.iloc[:-1],
    }
    for match, bad in cases.items():
        with pytest.raises(IntegrityError, match=match):
            h1a.validate_monthly(bad)


# --- specification assembly and orchestration -------------------------------------------------


def test_specifications_are_exactly_the_frozen_variants(
    frames: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    daily, monthly = frames
    specs = h1a.specifications(daily, monthly)
    assert list(specs) == ["primary", "R1", "R2", "R3"]
    expected: dict[models.Spec, pd.DataFrame] = {
        "primary": changes(daily, "2y", "same-day"),
        "R1": changes(daily, "2y", "lagged"),
        "R2": models.monthly_changes(monthly, "2y"),
        "R3": changes(daily, "10y", "same-day"),
    }
    for spec, ch in expected.items():
        pd.testing.assert_frame_equal(specs[spec], ch)
    assert specs["R2"]["date"].dt.to_period("M").iloc[0] == pd.Period("1981-01", "M")


def test_analyze_uses_the_validated_functions_and_keeps_roles_apart(
    frames: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    daily, monthly = frames
    a = h1a.analyze(h1a.VerifiedData(daily, monthly))
    direct = models.h1a_test(models.era_regression(changes(daily, "2y", "same-day")))
    assert astuple(a.primary.delta) == astuple(direct.delta)
    assert a.primary.outcome == direct.outcome and a.primary.spec == "primary"
    assert {s: r.spec for s, r in a.results.items()} == {
        "primary": "primary",
        "R1": "R1",
        "R2": "R2",
        "R3": "R3",
    }
    assert a.robustness == models.robustness_label(
        a.primary, [a.results["R1"], a.results["R2"], a.results["R3"]]
    )
    assert a.era_equality.df == 4
    assert list(a.legs) == list(explore.ERAS) and all(t.identified for t in a.legs.values())
    assert a.fits["R2"].lag == models.hac_lag(a.fits["R2"].nobs)
    # The synthetic DGP has beta = 5 in every era on the primary spec.
    assert abs(a.primary.beta_ref.estimate - 5) < 4 * a.primary.beta_ref.se
    assert a.primary.outcome == "ruled out"


def test_tables_label_confirmatory_and_robustness_rows(
    frames: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    a = h1a.analyze(h1a.VerifiedData(*frames))
    t = h1a.results_table(a.results)
    assert t.loc["primary", "status"] == "confirmatory"
    assert set(t.loc[["R1", "R2", "R3"], "status"]) == {"robustness"}
    assert (t["outcome"] == [r.outcome for r in a.results.values()]).all()
    e = h1a.effects_table(a.primary)
    row = e.loc["delta = beta_new - (2/3) beta_ref"]
    assert (row["lower"], row["upper"]) == (a.primary.delta.lower, a.primary.delta.upper)


def test_provenance_reports_commit_and_versions() -> None:
    p = h1a.provenance()
    assert re.fullmatch(r"[0-9a-f]{40}|unavailable", p["git_commit"])
    assert p["source_tree"] in {"clean", "modified"} and "statsmodels" in p


def test_provenance_ignores_generated_outputs_but_not_source_edits(tmp_path: Path) -> None:
    import subprocess

    def git(*args: str) -> None:
        subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

    (tmp_path / "src").mkdir()
    (tmp_path / "notebooks").mkdir()
    (tmp_path / "src" / "m.py").write_text("x = 1\n")
    (tmp_path / "notebooks" / "n.ipynb").write_text("{}\n")
    git("init", "-q")
    git("add", ".")
    git("commit", "-q", "-m", "init")
    (tmp_path / "notebooks" / "n.ipynb").write_text('{"executed": true}\n')  # outputs written
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "fig.png").write_bytes(b"png")  # new untracked figure
    assert h1a.provenance(tmp_path)["source_tree"] == "clean"
    (tmp_path / "src" / "m.py").write_text("x = 2\n")  # a real code change
    assert h1a.provenance(tmp_path)["source_tree"] == "modified"


# --- the real data (integrity only: no model is run) ------------------------------------------


def test_real_data_is_the_frozen_vintage() -> None:
    if not (ROOT / "data/processed/daily.csv").exists():
        pytest.skip("data not downloaded; run `make data`")
    data = h1a.load_verified()  # checksums, schema, dates, boundaries; no model is run
    assert len(data.daily) > 0 and len(data.monthly) > 0
    assert set(h1a.vintage_table().index) == set(h1a.FROZEN_SHA256)


# --- the 02 notebook --------------------------------------------------------------------------


def notebook_cells() -> list[dict[str, object]]:
    cells: list[dict[str, object]] = json.loads(NOTEBOOK.read_text())["cells"]
    return cells


def source(cell: dict[str, object]) -> str:
    src = cell["source"]
    return "".join(src) if isinstance(src, list) else str(src)


def test_notebook_has_the_twelve_sections_in_order_with_status_labels() -> None:
    headings = [
        line
        for c in notebook_cells()
        if c["cell_type"] == "markdown"
        for line in source(c).splitlines()
        if line.startswith("## ")
    ]
    assert [int(h.split(".")[0][3:]) for h in headings] == list(range(1, 13))
    labels = {
        4: "CONFIRMATORY",
        5: "CONFIRMATORY",
        6: "CONFIRMATORY",
        7: "SECONDARY",
        8: "DESCRIPTIVE",
        9: "DESCRIPTIVE",
        10: "ROBUSTNESS",
    }
    for number, label in labels.items():
        assert label in headings[number - 1], headings[number - 1]


def test_notebook_is_unexecuted_or_one_complete_clean_run() -> None:
    # Either never run, or the stored record of one top-to-bottom run with no errors: cells
    # numbered 1..n in order (no partial or re-ordered execution), every cell with output.
    cells = [c for c in notebook_cells() if c["cell_type"] == "code"]
    counts = [c["execution_count"] for c in cells]
    if all(n is None for n in counts):
        assert all(c["outputs"] == [] for c in cells)
        return
    assert counts == list(range(1, len(cells) + 1))
    outputs = [o for c in cells for o in c["outputs"]]  # type: ignore[attr-defined]
    assert all(o["output_type"] != "error" and o.get("name") != "stderr" for o in outputs)
    assert all(c["outputs"] for c in cells)


def test_notebook_never_reimplements_the_econometrics() -> None:
    code = [source(c) for c in notebook_cells() if c["cell_type"] == "code"]
    text = "\n".join(code)
    forbidden_calls = ("era_regression(", "h1a_test(", "two_leg_regression(", "era_equality(")
    for forbidden in (
        "statsmodels",
        "OLS",
        "np.linalg",
        "cov_type",
        "read_csv",
        "polyfit",
        "load_daily",  # explore loaders follow KAGURA_DATA; H1a must read only the frozen data/
        "load_monthly",
        "DATA_PROCESSED",
        *forbidden_calls,
    ):  # estimation only through h1a.analyze
        assert forbidden not in text, forbidden

    # The first cell that uses the data variable is the one that creates it, via the verifier.
    def uses_daily(c: str) -> bool:
        return any(isinstance(n, ast.Name) and n.id == "daily" for n in ast.walk(ast.parse(c)))

    first_data = next(c for c in code if uses_daily(c))
    assert "data = h1a.load_verified()\ndaily, monthly = data.daily, data.monthly" in first_data
    # Every function or constant the notebook uses exists in the validated modules.
    modules = {"h1a": h1a, "m": models, "ex": explore}
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            module = modules.get(node.value.id)
            if module is not None:
                assert hasattr(module, node.attr), f"{node.value.id}.{node.attr}"


def test_notebook_runs_end_to_end_on_synthetic_data(
    monkeypatch: pytest.MonkeyPatch, frames: tuple[pd.DataFrame, pd.DataFrame]
) -> None:
    import matplotlib.pyplot as plt

    monkeypatch.setattr(h1a, "load_verified", lambda: h1a.VerifiedData(*frames))
    monkeypatch.setattr(h1a, "vintage_table", lambda: pd.DataFrame())
    monkeypatch.setattr(explore, "save", lambda fig, name: None)  # no files written
    namespace: dict[str, object] = {}
    for c in notebook_cells():
        if c["cell_type"] == "code":
            exec(compile(source(c), str(NOTEBOOK), "exec"), namespace)  # noqa: S102
    plt.close("all")
    analysis = namespace["analysis"]
    assert isinstance(analysis, h1a.H1aAnalysis) and analysis.primary.outcome == "ruled out"


# --- audit: nothing is estimated before the integrity check -----------------------------------


def test_analyze_refuses_anything_but_verified_data(
    frames: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    with pytest.raises(TypeError, match="VerifiedData"):
        h1a.analyze(frames)  # type: ignore[arg-type]  # a raw (daily, monthly) tuple


def test_failed_verification_stops_before_any_estimation(
    tmp_path: Path, frames: tuple[pd.DataFrame, pd.DataFrame], monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = write_vintage(tmp_path, *frames)
    (tmp_path / "data/raw/us_2y.csv").write_text("tampered\n")
    calls: list[str] = []
    monkeypatch.setattr(h1a, "era_regression", lambda ch: calls.append("estimated"))
    with pytest.raises(IntegrityError):
        h1a.analyze(h1a.load_verified(tmp_path, expected))
    assert calls == []


def test_notebook_verifies_before_it_estimates() -> None:
    code = [source(c) for c in notebook_cells() if c["cell_type"] == "code"]
    verify = next(i for i, c in enumerate(code) if "h1a.load_verified()" in c)
    estimate = next(i for i, c in enumerate(code) if "h1a.analyze(" in c)
    assert verify < estimate
    assert "h1a.analyze(data)" in code[estimate]
    assert sum("h1a.analyze(" in c for c in code) == 1  # estimation happens exactly once
    assert all("allow-errors" not in line for line in (ROOT / "Makefile").read_text().splitlines())


def test_makefile_has_a_dedicated_target_for_notebook_02() -> None:
    lines = (ROOT / "Makefile").read_text().splitlines()
    i = lines.index("h1a:")
    assert (
        "nbconvert --to notebook --execute --inplace notebooks/02_h1a_formal.ipynb" in lines[i + 1]
    )
    research = lines.index("research:")
    assert "02_h1a_formal" not in lines[research + 1]  # `make research` does not run H1a


# --- confidence-set formatting ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("intervals", "text"),
    [
        ([(-0.52, -0.21)], "[-0.5200, -0.2100]"),
        ([(-math.inf, -3.1), (0.8, math.inf)], "(-∞, -3.1000] ∪ [0.8000, ∞): unbounded"),
        ([(-math.inf, math.inf)], "(-∞, ∞): unbounded"),
        ([(0.25, math.inf)], "[0.2500, ∞): unbounded"),
        ([], "∅: empty"),
    ],
)
def test_format_set_shows_bounded_and_unbounded_sets(
    intervals: list[tuple[float, float]], text: str
) -> None:
    assert h1a.format_set(intervals).startswith(text)


def test_format_set_on_real_fieller_output(frames: tuple[pd.DataFrame, pd.DataFrame]) -> None:
    from test_models import synthetic

    strong = models.h1a_test(models.era_regression(synthetic(6.0, 3.0)))
    assert "∞" not in h1a.format_set(strong.relative_change_set)
    weak = models.h1a_test(models.era_regression(synthetic(0.0, 3.0, noise=1.0)))
    assert "unbounded" in h1a.format_set(weak.relative_change_set)
