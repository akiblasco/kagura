"""Phase C: descriptive event comparison (ADR 0009 §7, frozen protocol ADR 0013).

Proximity is not causation, and the random-date baselines are descriptive rankings, not tests
(ADR 0013 §4). Inputs are the committed Phase A outputs and the checksummed event tables.

Complete outputs go to data/events/restricted/phase_c/ (gitignored, ADR 0010 §1). Public copies
in research/adr0007/out/phase_c/ withhold every computed C0 cell (BOJ-derived) and BOJ events;
see ADR 0014.
Run: uv run python research/adr0007/phase_c.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from data import Cell, cell
from kagura import events as ev
from kagura import vintage

HERE = Path(__file__).parent
PA = HERE / "out" / "phase_a"
OUT = HERE / "out" / "phase_c"
RESTRICTED = ev.EVENTS / "restricted" / "phase_c"
END = pd.Timestamp(ev.SAMPLE_END)
CLASSES = ("C0", "C1", "C2", "C3", "C4", "C5")
OBS = ("all", "same_day")
# Coverage starts: ADR 0009 §3.8 and §4, narrowed by ADR 0010 R2 (FOMC change missing pre-1990)
# and R5 (FRB minutes from 2001-05). C0 has BOJ members only from 1998-04.
COVER = {
    "C0": "1998-04-01",
    "C2": "1990-01-01",
    "C3": "1991-04-01",
    "C4": "1981-01-01",
    "C5": "2001-05-01",
}
PENDING = {"C1": "pending: ADR 0010 §3a second BOJ coding pass not done"}
NO_SAME_DAY = {
    "C3": "no same_day members (MOF observable = unknown)",
    "C4": "no observability field for ADR 0004 markers",
}
# ADR 0004 markers, unchanged. Row = first USD/JPY row on or after the date (no announce time).
MARKERS = {
    "1985-09-22": "Plaza Accord",
    "1987-02-22": "Louvre Accord",
    "1999-02-12": "BOJ zero interest rate policy",
    "2001-03-19": "BOJ quantitative easing",
    "2006-03-09": "BOJ exits quantitative easing",
    "2008-09-15": "Lehman Brothers failure",
    "2013-04-04": "BOJ QQE",
    "2016-01-29": "BOJ negative interest rate",
    "2016-09-21": "BOJ yield curve control",
    "2022-03-16": "Fed begins 2022 hiking cycle",
    "2022-09-22": "MOF yen-buying intervention",
    "2022-12-20": "BOJ widens YCC band",
    "2024-03-19": "BOJ ends negative rate and YCC",
}
HEADLINE = {  # ADR 0013 §1, frozen
    "HC1": ("primary", "full", 0.15, 1, "2004-04-01", "2003-07-15 .. 2004-07-30"),
    "HC2": ("primary", "recent", 0.15, 1, "2017-10-02", "2017-03-15 .. 2020-07-20"),
}
NOTE = (
    "descriptive; baseline percentile is a ranking against random dates, not a p-value "
    "or test; proximity does not imply causation (ADR 0009 §7.4, ADR 0013 §4)"
)


def releases() -> dict[tuple[str, str], pd.DataFrame]:
    """One row per release (ADR 0009 §3.1), per class and observability version."""
    e = pd.read_csv(ev.EVENTS / "restricted" / "policy_events_full.csv")
    e["row"] = pd.to_datetime(e.fx_row_date.fillna(e.fx_row_decision))
    e["by_decision"] = e.fx_row_date.isna()
    agg = {
        "institution": "first",
        "row": "first",
        "by_decision": "first",
        "fx_row_uncertain": "any",
        "observable": "first",
        "decision_date": "first",
        "action": "first",
    }
    rel = e.groupby("release_id", sort=False).agg(agg).reset_index()
    chg = e.groupby("release_id").policy_change.agg(lambda s: bool(s.fillna(False).any()))
    rel["change"] = rel.release_id.map(chg)
    mof = e[(e.institution == "MOF") & e.episode_start.astype(bool)]
    c3 = mof.groupby("episode_id", sort=False).agg(agg).reset_index()
    c3 = c3.rename(columns={"episode_id": "release_id"})
    c4 = pd.DataFrame(
        {
            "release_id": [f"ADR0004-{d}" for d in MARKERS],
            "institution": "marker",
            "row": pd.to_datetime(list(MARKERS)),
            "by_decision": False,
            "fx_row_uncertain": False,
            "observable": "n/a",
            "decision_date": list(MARKERS),
            "action": list(MARKERS.values()),
        }
    )
    base = {
        "C0": rel[
            rel.institution.isin(["BOJ", "FOMC"])
            & ~((rel.institution == "BOJ") & (rel.decision_date < COVER["C0"]))
        ],
        "C2": rel[(rel.institution == "FOMC") & rel.change],
        "C3": c3,
        "C4": c4,
        "C5": rel[rel.institution == "FRB"],
    }
    out = {}
    for c, d in base.items():
        d = d[(d.row >= COVER[c]) & (d.row <= END)].sort_values("row")
        out[(c, "all")] = d
        out[(c, "same_day")] = d[d.observable == "same_day"]
    return out


def pos(dates: pd.Series, when: pd.Series | list[str]) -> np.ndarray:
    """First usable row on or after each date."""
    return np.searchsorted(dates.to_numpy(), pd.to_datetime(when).to_numpy(), "left")


def stats(
    c: Cell,
    k: int,
    lw: int | None,
    rw: int | None,
    grid: list[int],
    rel: pd.DataFrame,
    cover: str,
    shift: int = 0,
) -> dict[str, Any]:
    """ADR 0009 §7.2 statistics 1-4 for break row k with interval [k-lw, k+rw] (rows)."""
    dates, n_rows = c.dates.reset_index(drop=True), len(c.dates)
    lo = int(pos(dates, [cover])[0])
    hi = n_rows - 1  # coverage runs to the sample end
    if k < lo:
        return {"status": "not covered: break before class coverage"}
    p = pos(dates, rel.row) + shift
    keep = (p <= hi) & (rel.row >= dates.iloc[0]).to_numpy()  # in-sample events only
    p, r = p[keep], rel[keep]
    out: dict[str, Any] = {"status": "computed", "n_class_releases": len(p)}
    if lw is not None and rw is not None:
        a, b = k - lw, k + rw
        inside = (p >= a) & (p <= b)
        out["interval_partially_uncovered"] = bool(a < lo)
        out["events_in_interval"] = int(inside.sum())
        out["events_in_interval_by_decision"] = int(r.by_decision.to_numpy()[inside].sum())
        out["events_in_interval_uncertain"] = int(r.fx_row_uncertain.to_numpy()[inside].sum())
    if len(p) == 0:
        out["nearest_distance_rows"] = None
        return out
    d = p - k
    j = int(np.argmin(np.abs(d)))
    out["nearest_distance_rows"] = int(d[j])
    out["nearest_is_lower_bound"] = bool(k - lo < abs(d[j]) and lo > 0)
    out["nearest_release"] = r.release_id.iloc[j]
    out["nearest_institution"] = r.institution.iloc[j]
    out["nearest_uncertain"] = bool(r.fx_row_uncertain.iloc[j])
    gc = [
        g for g in grid if g >= lo and (lw is None or rw is None or (g - lw >= lo and g + rw <= hi))
    ]
    out["baseline_n_positions"] = len(gc)
    if not gc:  # no same-width interval fits inside coverage: baselines undefined
        out["baseline_status"] = "not computed: no covered position for this interval width"
        return out
    gd = np.array([np.abs(p - g).min() for g in gc])
    out["baseline_distance_percentile"] = round(100 * float((gd <= abs(d[j])).mean()), 1)
    if lw is not None and rw is not None:
        hit = [bool(((p >= g - lw) & (p <= g + rw)).any()) for g in gc]
        out["baseline_interval_share"] = round(float(np.mean(hit)), 3)
    out["within_lowest_5pct_of_baseline"] = bool(out["baseline_distance_percentile"] <= 5)
    return out


def interval_rows(c: Cell, k: int, ci: str) -> tuple[int, int]:
    a, b = ci.split(" .. ")
    pa, pb = pos(c.dates.reset_index(drop=True), [a, b])
    return k - int(pa), int(pb) - k


def cells_for(spec: str, sample: str, eps: float) -> Cell:
    return cell(spec, sample, eps, 1 if spec == "lag" else 0)


def eligible(c: Cell) -> list[int]:
    n_rows = len(c.dates)
    return [k for k in c.month_grid if c.h <= k <= n_rows - c.h]


def run_break(
    c: Cell,
    date: str,
    ci: str | None,
    rel: dict[tuple[str, str], pd.DataFrame],
    grid: list[int],
    shift_mof: int = 0,
) -> list[dict[str, Any]]:
    k = int(pos(c.dates.reset_index(drop=True), [date])[0])
    assert c.dates.iloc[k] == pd.Timestamp(date), (date, c.dates.iloc[k])
    lw, rw = interval_rows(c, k, ci) if ci else (None, None)
    rows = []
    for cl in CLASSES:
        for o in OBS:
            row: dict[str, Any] = {"class": cl, "observability": o}
            if cl in PENDING:
                row["status"] = PENDING[cl]
            elif o == "same_day" and cl in NO_SAME_DAY:
                row["status"] = "not applicable: " + NO_SAME_DAY[cl]
            else:
                row |= stats(
                    c, k, lw, rw, grid, rel[(cl, o)], COVER[cl], shift_mof if cl == "C3" else 0
                )
            rows.append(row)
    return rows


# C0 is the only computed class with BOJ members (C1 is pending). Every C0 statistic, not just
# the nearest release, is BOJ-derived, so public copies withhold the whole computed cell.
BOJ_DERIVED = {"C0"}
KEYS = {
    "id", "break", "ci95_nominal", "class", "observability", "status", "note", "label",
    "spec", "sample", "eps", "m", "daily_break", "mof_shift_rows",
}  # fmt: skip
WITHHELD = "computed; withheld from public output: BOJ-derived (ADR 0010 §1)"


def public(df: pd.DataFrame) -> pd.DataFrame:
    """Copy with BOJ-derived computed cells blanked and relabelled; other rows unchanged."""
    pub = df.copy()
    hit = pub["class"].isin(BOJ_DERIVED) & (pub.status == "computed")
    stat = [c for c in pub if c not in KEYS]
    pub[stat] = pub[stat].astype(object)
    pub.loc[hit, stat] = None
    pub.loc[hit, "status"] = WITHHELD
    if "nearest_institution" in pub:
        assert not (pub.nearest_institution == "BOJ").any(), "BOJ identity in public output"
    return pub


def save(df: pd.DataFrame, name: str) -> None:
    """Complete copy to restricted storage; public copy via `public` (ADR 0010 §1)."""
    df.to_csv(RESTRICTED / name, index=False)
    public(df).to_csv(OUT / name, index=False)


def main() -> None:
    bad = vintage.events_mismatches(ev.EVENTS)
    if bad:
        sys.exit(f"event checksums differ: {bad}")
    sel = pd.read_csv(PA / "selection.csv")
    brk = pd.read_csv(PA / "break_table.csv")
    part = pd.read_csv(PA / "partitions.csv")
    # Frozen headline inputs (ADR 0013 §1) must match the committed Phase A outputs.
    for hc, (sp, sa, e, m, date, ci) in HEADLINE.items():
        hit = brk[(brk.spec == sp) & (brk["sample"] == sa) & (brk.eps == e) & (brk.m == m)]
        assert hit.date.tolist() == [date] and hit.ci95_nominal.tolist() == [ci], hc
    s = sel[(sel.spec == "primary") & (sel["sample"] == "recent") & (sel.eps == 0.15)].iloc[0]
    assert (s.m_BIC, s.m_LWZ) == (1, 0), "HC2/HC3 selection changed"
    rel = releases()
    OUT.mkdir(parents=True, exist_ok=True)
    RESTRICTED.mkdir(parents=True, exist_ok=True)

    head: list[dict[str, Any]] = []
    listing: list[dict[str, Any]] = []
    for hc, (sp, sa, e, _m, date, ci) in HEADLINE.items():
        c = cells_for(sp, sa, e)
        for row in run_break(c, date, ci, rel, eligible(c)):
            head.append({"id": hc, "break": date, "ci95_nominal": ci} | row)
        k = int(pos(c.dates.reset_index(drop=True), [date])[0])
        lw, rw = interval_rows(c, k, ci)
        for (cl, o), d in rel.items():
            if o != "all":
                continue
            p = pos(c.dates.reset_index(drop=True), d.row)
            for (_, x), pi in zip(d.iterrows(), p, strict=True):
                if k - lw <= pi <= k + rw and x.row >= c.dates.iloc[0]:
                    listing.append(
                        {
                            "id": hc,
                            "class": cl,
                            "release_id": x.release_id,
                            "institution": x.institution,
                            "row_date": x.row.date(),
                            "rows_from_break": int(pi - k),
                            "same_day": x.observable == "same_day",
                            "by_decision": bool(x.by_decision),
                            "uncertain": bool(x.fx_row_uncertain),
                            "action": str(x.action)[:120],
                        }
                    )
    head.append(
        {
            "id": "HC3",
            "break": "none",
            "class": "all",
            "observability": "all",
            "status": "LWZ selects m = 0 in primary recent ε = 15 %: no date to compare",
        }
    )
    save(pd.DataFrame(head).assign(note=NOTE), "headline.csv")
    lst = pd.DataFrame(listing)
    lst[lst.institution != "BOJ"].to_csv(OUT / "headline_events_in_interval.csv", index=False)
    lst[lst.institution == "BOJ"].to_csv(RESTRICTED / "headline_boj_events.csv", index=False)

    # S1: daily grid, m = 1 dates; Phase A computed no daily interval, so statistics 1 and 3
    # are not available. Variant: every MOF row moved one row later (all are fx_row_uncertain).
    ds = pd.read_csv(PA / "daily_sensitivity.csv").drop_duplicates("sample")
    s1: list[dict[str, Any]] = []
    for _, d1 in ds.iterrows():
        c = cells_for("primary", d1["sample"], 0.15)
        n_rows = len(c.dates)
        grid = list(range(c.h, n_rows - c.h + 1))
        for shift in (0, 1):
            for res in run_break(c, d1.daily_date, None, rel, grid, shift):
                s1.append(
                    {"sample": d1["sample"], "daily_break": d1.daily_date, "mof_shift_rows": shift}
                    | res
                )
    save(pd.DataFrame(s1).assign(note=NOTE), "s1_daily.csv")

    # S2 (appendix family) and E1 (exploratory m = 4), one row per break, class, version.
    s2: list[dict[str, Any]] = []
    for key, g in brk.groupby(["spec", "sample", "eps"], sort=False):
        sp, sa, e = str(key[0]), str(key[1]), float(str(key[2]))
        c = cells_for(sp, sa, e)
        grid = eligible(c)
        for _, r in g.iterrows():
            if any((sp, sa, e, r.m, r.date) == v[:5] for v in HEADLINE.values()):
                continue
            for res in run_break(c, r.date, r.ci95_nominal, rel, grid):
                s2.append({"spec": sp, "sample": sa, "eps": e, "m": r.m, "break": r.date} | res)
    s2d = pd.DataFrame(s2)
    save(s2d, "s2_per_break.csv")
    comp = s2d[s2d.status == "computed"]
    summ = (
        comp.groupby(["class", "observability"])
        .agg(
            n_breaks=("break", "size"),
            share_with_event_in_interval=("events_in_interval", lambda v: round((v > 0).mean(), 3)),
            mean_baseline_interval_share=("baseline_interval_share", lambda v: round(v.mean(), 3)),
            share_within_lowest_5pct=(
                "within_lowest_5pct_of_baseline",
                lambda v: round(v.mean(), 3),
            ),
            median_distance_percentile=("baseline_distance_percentile", "median"),
        )
        .reset_index()
    )
    save(summ.assign(status="computed", note=NOTE), "s2_summary.csv")
    p4 = (
        part[
            (part.spec == "primary")
            & (part["sample"] == "recent")
            & (part.eps == 0.15)
            & (part.m == 4)
        ]
        .dates.iloc[0]
        .split()
    )
    e1 = s2d[
        (s2d.spec == "primary") & (s2d["sample"] == "recent") & (s2d.eps == 0.15) & (s2d.m == 4)
    ]
    assert sorted(e1["break"].unique()) == sorted(p4)
    save(e1.assign(label="exploratory, selected by neither criterion"), "e1_m4.csv")
    print(
        "written:",
        sorted(p.name for p in OUT.iterdir()),
        "| restricted:",
        sorted(p.name for p in RESTRICTED.iterdir()),
    )


if __name__ == "__main__":
    main()
