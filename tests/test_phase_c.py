"""Phase C regression tests (ADR 0009 §7.2, ADR 0013, ADR 0014) for research/adr0007/phase_c.py.

Synthetic tests use hand-built calendars, so the expected numbers are counted independently of
the implementation. Output tests read the committed public CSVs and need no restricted data.
"""

import importlib.util
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).parents[1]
RUN = ROOT / "research/adr0007"
sys.path.insert(0, str(RUN))  # phase_c imports its sibling `data`
spec = importlib.util.spec_from_file_location("phase_c", RUN / "phase_c.py")
assert spec and spec.loader
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)

DATES = pd.Series(pd.bdate_range("2000-01-03", periods=300))
CELL = SimpleNamespace(dates=DATES)
GRID = list(range(300))


def rel(rows: list[str], ids: list[str] | None = None) -> pd.DataFrame:
    n = len(rows)
    return pd.DataFrame(
        {
            "release_id": ids or [f"X{i}" for i in range(n)],
            "institution": ["FOMC"] * n,
            "row": pd.to_datetime(rows),
            "by_decision": [False] * n,
            "fx_row_uncertain": [False] * n,
        }
    )


def d(i: int) -> str:
    return str(DATES[i].date())


def test_event_before_sample_is_excluded_not_clamped_to_row_0() -> None:
    # 1999 event precedes the calendar. Clamping it to row 0 would give nearest -20.
    out = pc.stats(CELL, 20, None, None, GRID, rel(["1999-06-01", d(100)]), "1990-01-01")
    assert out["n_class_releases"] == 1
    assert out["nearest_distance_rows"] == 80


def test_event_after_sample_end_is_excluded() -> None:
    out = pc.stats(CELL, 20, None, None, GRID, rel([d(50), "2030-01-01"]), "1990-01-01")
    assert out["n_class_releases"] == 1 and out["nearest_distance_rows"] == 30


def test_break_before_coverage_is_not_covered_not_zero() -> None:
    out = pc.stats(CELL, 20, 5, 5, GRID, rel([d(100)]), d(50))
    assert out == {"status": "not covered: break before class coverage"}


def test_baseline_uses_only_covered_positions_whose_interval_fits() -> None:
    # Coverage starts at row 50; interval [k-5, k+5] must lie in rows 50..299: G = 55..294.
    out = pc.stats(CELL, 100, 5, 5, GRID, rel([d(100)]), d(50))
    assert out["baseline_n_positions"] == 240
    assert out["nearest_is_lower_bound"] is False
    far = pc.stats(CELL, 60, None, None, GRID, rel([d(200)]), d(50))
    assert far["nearest_is_lower_bound"] is True  # an earlier event could lie before coverage


def test_no_fitting_position_leaves_baseline_uncomputed() -> None:
    out = pc.stats(CELL, 150, 150, 150, GRID, rel([d(100)]), "1990-01-01")
    assert out["baseline_n_positions"] == 0
    assert "baseline_distance_percentile" not in out and out["baseline_status"].startswith("not")


def test_percentile_ties_are_inclusive() -> None:
    # Events at 100 and 200, break at 90 (distance 10). Positions within 10 rows of an event:
    # 90..110 and 190..210, i.e. 42 of 300.
    out = pc.stats(CELL, 90, None, None, GRID, rel([d(100), d(200)]), "1990-01-01")
    assert out["baseline_distance_percentile"] == round(100 * 42 / 300, 1)
    zero = pc.stats(CELL, 100, None, None, GRID, rel([d(100), d(200)]), "1990-01-01")
    assert zero["baseline_distance_percentile"] == round(100 * 2 / 300, 1)
    assert zero["within_lowest_5pct_of_baseline"] is True


def test_interval_count_and_nearest_distance_are_distinct() -> None:
    # Asymmetric interval [k-5, k+50]: the nearest event (k-6) lies outside, a farther one inside.
    out = pc.stats(CELL, 100, 5, 50, GRID, rel([d(94), d(140)]), "1990-01-01")
    assert out["events_in_interval"] == 1
    assert out["nearest_distance_rows"] == -6


def test_pending_and_not_applicable_cells_carry_no_statistics() -> None:
    cell = SimpleNamespace(dates=DATES)
    r = {(c, o): rel([d(100)]) for c in pc.CLASSES for o in pc.OBS}
    rows = pc.run_break(cell, d(90), None, r, GRID)
    assert [(x["class"], x["observability"]) for x in rows] == [
        (c, o) for c in pc.CLASSES for o in pc.OBS
    ]
    status = {(x["class"], x["observability"]): x["status"] for x in rows}
    assert (
        status[("C1", "all")].startswith("pending")
        and status[("C1", "same_day")] == (status[("C1", "all")])
    )
    for c in ("C3", "C4"):
        assert status[(c, "same_day")].startswith("not applicable")
    for x in rows:
        if x["status"] != "computed":
            assert set(x) == {"class", "observability", "status"}


def test_public_copy_withholds_boj_derived_cells() -> None:
    df = pd.DataFrame(
        {
            "class": ["C0", "C0", "C2", "C1"],
            "observability": ["all"] * 4,
            "status": ["computed", "not covered: x", "computed", "pending: x"],
            "nearest_release": ["BOJ-SYNTHETIC-1", None, "FOMC-20040630-1", None],
            "nearest_institution": ["BOJ", None, "FOMC", None],
            "baseline_distance_percentile": [74.8, None, 58.7, None],
        }
    )
    pub = pc.public(df)
    assert pub.status[0] == pc.WITHHELD
    assert pub.loc[0, ["nearest_release", "baseline_distance_percentile"]].isna().all()
    assert pub.loc[1:].astype(str).equals(df.loc[1:].astype(str))  # other rows untouched
    assert df.nearest_release[0] == "BOJ-SYNTHETIC-1"  # complete copy not mutated


def test_public_copy_refuses_boj_identity_outside_c0() -> None:
    df = pd.DataFrame(
        {
            "class": ["C2"],
            "observability": ["all"],
            "status": ["computed"],
            "nearest_institution": ["BOJ"],
        }
    )
    with pytest.raises(AssertionError):
        pc.public(df)


# Committed public outputs (ADR 0013 §1 and §4, ADR 0014)

PUB = RUN / "out" / "phase_c"


def test_headline_table_has_every_cell_in_fixed_order() -> None:
    h = pd.read_csv(PUB / "headline.csv")
    order = [(i, c, o) for i in ("HC1", "HC2") for c in pc.CLASSES for o in pc.OBS]
    assert list(zip(h.id[:24], h["class"][:24], h.observability[:24], strict=True)) == order
    st = h.status[:24].str.split(":").str[0].str.split(";").str[0].value_counts().to_dict()
    assert st == {"computed": 16, "pending": 4, "not applicable": 4}
    assert (h.status[:24] == pc.WITHHELD).sum() == 4  # C0 x 2 breaks x 2 versions
    hc3 = h.iloc[24]
    assert len(h) == 25 and hc3.id == "HC3" and hc3["break"] == "none"
    assert hc3.status.startswith("LWZ selects m = 0")
    assert h.loc[h.status == "computed", "within_lowest_5pct_of_baseline"].eq(False).all()


def test_public_outputs_contain_no_boj_identity_or_value() -> None:
    for f in PUB.glob("*.csv"):
        text = f.read_text()
        assert not re.search(r"BOJ-\d{8}", text), f.name
        df = pd.read_csv(f)
        if "nearest_institution" in df:
            assert not (df.nearest_institution == "BOJ").any(), f.name
        if "institution" in df:
            assert not (df.institution == "BOJ").any(), f.name
        if "class" in df and "status" in df:
            c0 = df[df["class"] == "C0"]
            assert not (c0.status == "computed").any(), f.name
            stat = [c for c in df if c not in pc.KEYS]
            assert c0[stat].isna().all().all(), f.name


def test_exploratory_e1_stays_labelled_and_out_of_headline() -> None:
    e1 = pd.read_csv(PUB / "e1_m4.csv")
    assert (e1.label == "exploratory, selected by neither criterion").all()
    assert sorted(e1["break"].unique()) == ["2015-06-01", "2017-10-02", "2019-11-01", "2021-12-01"]
    assert "2019-11-01" not in set(pd.read_csv(PUB / "headline.csv")["break"])


# Event identities and overlaps: need the restricted table (absent in public clones)

FULL = pc.ev.EVENTS / "restricted" / "policy_events_full.csv"


@pytest.mark.skipif(not FULL.exists(), reason="restricted event table not present")
def test_class_overlaps_and_stable_identifiers() -> None:
    r = pc.releases()
    ids = {k: set(v.release_id) for k, v in r.items()}
    for k, v in r.items():
        assert v.release_id.is_unique, k  # one row per release / episode
        assert v.row.is_monotonic_increasing, k
        assert ids[(k[0], "same_day")] <= ids[(k[0], "all")]
    # C0 contains every FOMC change inside C0 coverage (1998-04, ADR 0014 convention 4)
    c2 = r[("C2", "all")]
    assert set(c2[c2.row >= pc.COVER["C0"]].release_id) <= ids[("C0", "all")]
    assert all(re.fullmatch(r"FRB-\d{8}-\d+", i) for i in ids[("C5", "all")])
    assert all(re.fullmatch(r"MOF-EP\d{3}", i) for i in ids[("C3", "all")])
    assert len(ids[("C4", "all")]) == 13
    assert pc.releases()[("C0", "all")].release_id.tolist() == r[("C0", "all")].release_id.tolist()
    assert np.all(r[("C0", "all")].row >= pd.Timestamp(pc.COVER["C0"]))
