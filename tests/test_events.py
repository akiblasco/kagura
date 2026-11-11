"""ADR 0009: event-table logic on synthetic inputs, plus checks on the committed MOF table."""

import datetime as dt

import pandas as pd
import pytest

from kagura import events

D = dt.date


def test_episodes_split_on_more_than_five_business_days() -> None:
    hol = {D(2024, 4, 29)}
    # Mon 2024-04-22 -> Mon 04-29 (holiday) -> Wed 05-01: within 5 business days.
    # 05-01 -> 05-09: Thu, Fri, Mon(05-06), Tue, Wed, Thu = 6 business days -> new episode.
    dates = [D(2024, 4, 22), D(2024, 4, 29), D(2024, 5, 1), D(2024, 5, 9)]
    assert events.episodes(dates, hol) == [1, 1, 1, 2]
    # exactly 5 business days apart stays in the episode
    assert events.episodes([D(2024, 5, 1), D(2024, 5, 8)], hol) == [1, 1]


def test_new_year_bank_holidays_merge_the_1999_2000_gap() -> None:
    # 1999-12-24 -> 2000-01-04: 7 weekdays, 5 once 31 Dec - 3 Jan are excluded (ADR 0010 §3).
    dates = [D(1999, 12, 24), D(2000, 1, 4)]
    assert events.episodes(dates, set()) == [1, 2]
    assert events.episodes(dates, events.new_year_holidays(1999, 2000)) == [1, 1]


def test_fx_row_maps_to_same_or_next_new_york_row() -> None:
    rows = pd.DatetimeIndex(["2022-09-21", "2022-09-22", "2022-09-23", "2022-09-26"])
    assert events.fx_row(rows, D(2022, 9, 22)) == D(2022, 9, 22)
    assert events.fx_row(rows, D(2022, 9, 24)) == D(2022, 9, 26)  # Saturday
    assert events.fx_row(rows, D(2022, 9, 27)) is None


def test_direction_reads_the_yen_leg() -> None:
    assert events.direction("the US dollar (sold) the Japanese yen (bought)").endswith("bought")
    assert events.direction("the Euro (bought) the Japanese yen (sold)").endswith("sold")
    assert events.direction("the US dollar (sold) the German mark (bought)").endswith("no JPY leg")


def test_last_days_reads_fed_headings() -> None:
    assert events.last_days("January 31-February 1", 1995) == [D(1995, 2, 1)]
    assert events.last_days("April/May 30-1", 2013) == [D(2013, 5, 1)]
    assert events.last_days("March 28", 1995) == [D(1995, 3, 28)]
    assert events.last_days("October 21, 22, and 30", 1987) == [
        D(1987, 10, d) for d in (21, 22, 30)
    ]


ROWS = pd.bdate_range("2024-03-01", "2024-11-29")


def test_minute_releases_map_across_daylight_saving() -> None:
    # 2:00 p.m. New York is after the noon fix in both EST and EDT: next row (§5.2).
    for day, nxt in (
        (D(2024, 3, 8), D(2024, 3, 11)),
        (D(2024, 3, 11), D(2024, 3, 12)),
        (D(2024, 11, 1), D(2024, 11, 4)),
        (D(2024, 11, 4), D(2024, 11, 5)),
    ):
        f = events.announce_fields(ROWS, day, dt.time(14), events.NY, "x")
        assert f["fx_row_date"] == nxt and f["fx_row_uncertain"] is False
    # 11:50 New York is within 15 minutes of the fix: same row, flagged uncertain.
    f = events.announce_fields(ROWS, D(2024, 3, 11), dt.time(11, 50), events.NY, "x")
    assert f["fx_row_date"] == D(2024, 3, 11) and f["fx_row_uncertain"] is True
    # 12:55 Tokyo on 2024-03-19 is 23:55 EDT on 03-18: the 03-19 row, before or after the
    # US change (Tokyo has no daylight saving).
    for day in (D(2024, 3, 8), D(2024, 3, 19), D(2024, 11, 5)):
        f = events.announce_fields(ROWS, day, dt.time(12, 55), events.TOKYO, "x")
        assert f["fx_row_date"] == day


def test_day_precision_is_uncertain_only_when_the_row_could_differ() -> None:
    assert events.announce_fields(ROWS, D(2024, 3, 12), None, events.NY, "x")["fx_row_uncertain"]
    sat = events.announce_fields(ROWS, D(2024, 3, 9), None, events.NY, "x")  # whole day -> Mon
    assert sat["fx_row_date"] == D(2024, 3, 11) and sat["fx_row_uncertain"] is False


def test_discount_minutes_change_rule() -> None:
    hit = events.DM_CHANGE.search
    assert hit("Reduction in the primary credit rate from 4-3/4 percent to 4 percent")
    assert hit("Increase in the interest on reserve balances rate and in the primary credit rate")
    assert not hit("Establishment without change by twelve Reserve Banks of the existing rate")


def test_boj_coding_order() -> None:
    def docs(*titles: str) -> list[dict[str, object]]:
        return [{"title": t, "href": "/none"} for t in titles]

    assert (
        events.boj_code(
            docs("Statement on Monetary Policy (Policy unchanged, Announced at 12:55 p.m.)")
        )[0]
        is False
    )
    assert (
        events.boj_code(
            docs(
                'Introduction of the "Quantitative and Qualitative Monetary '
                'Easing" (Announced at 1:40 p.m.)'
            )
        )[0]
        is True
    )
    assert (
        events.boj_code(
            docs("Announcement of the Monetary Policy Meeting Decisions (Eased further)")
        )[0]
        is True
    )


TABLE = events.EVENTS / "policy_events.csv"


@pytest.mark.skipif(not TABLE.exists(), reason="event table not built")
def test_committed_table() -> None:
    t = pd.read_csv(TABLE, dtype=str)
    assert events.validate(t)["failures"] == []
    mof = t[t.institution == "MOF"]
    assert mof["decision_date"].min() >= "1991-04-01"
    assert (mof["observable"] == "unknown").all() and mof["fx_row_date"].isna().all()
    assert (mof["fx_row_decision"] >= mof["decision_date"]).all()
    assert mof.release_id.nunique() == 369 and len(mof) == 386 and mof.episode_id.nunique() == 74
    assert not (t.institution == "BOJ").any()  # BOJ rows never enter the public table (§6.1)
    fomc = t[t.institution == "FOMC"]
    assert fomc[fomc.decision_date < "1994-01-01"].observable.eq("delayed").all()  # §5.2
    linked = t[t.linked_ids.notna()]
    ids = set(t.release_id)
    assert all(set(x.split()) <= ids for x in linked.linked_ids)


@pytest.mark.skipif(not (events.EVENTS / "manifest.json").exists(), reason="no collection")
def test_event_checksums() -> None:
    from kagura import vintage

    bad = vintage.events_mismatches(events.EVENTS)
    if not (events.EVENTS / "restricted").exists():  # a clone without the private files
        bad = [b for b in bad if not b.startswith("restricted/")]
    assert bad == []
