"""Official policy-event dataset (ADR 0009). Built by script from raw files; no hand editing.

Sources: MOF intervention (§3.6), FOMC (§3.4), Federal Reserve Board discount rate (§3.5),
BOJ (§3.2, §3.3). Clarifications of the frozen ADR are in ADR 0010.

Storage (§6.1): public raw files under data/events/raw/<inst>/, restricted ones (BOJ, sources
whose terms are unread) under data/events/restricted/, which is git-ignored and never
published. Every fetched file is recorded in data/events/manifest.json (§6.3).
"""

from __future__ import annotations

import bisect
import calendar
import csv
import datetime as dt
import hashlib
import html
import json
import re
import sys
import time
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
from pypdf import PdfReader

from kagura import DATA_PROCESSED, data

EVENTS = DATA_PROCESSED.parent / "events"
MANIFEST = EVENTS / "manifest.json"
SAMPLE_END = "2026-09-11"  # ADR 0009 §6.5 date range, = ADR 0006 DAILY_END

MOF_CSV = EVENTS / "raw/mof/foreign_exchange_intervention_operations.csv"
MOF_URL = (
    "https://www.mof.go.jp/english/policy/international_policy/reference/feio/"
    "foreign_exchange_intervention_operations.csv"
)
HOLIDAYS_CSV = EVENTS / "restricted/cao/syukujitsu.csv"
HOLIDAYS_URL = "https://www8.cao.go.jp/chosei/shukujitsu/syukujitsu.csv"
EPISODE_GAP = 5  # Tokyo business days (ADR 0009 §3.6), not tuned

COLUMNS = [
    "event_id", "release_id", "institution", "decision_date", "announce_ts",
    "announce_ts_source", "ts_precision", "record_publication_date", "observable",
    "fx_row_date", "fx_row_decision", "fx_row_uncertain", "policy_change", "action",
    "amount_100m_yen", "currency_pair", "episode_id", "episode_start", "linked_ids",
    "coordinated", "superseded_by", "source_file", "hand_entered", "note",
]  # fmt: skip


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch(url: str, dest: Path, licence: str, committed: bool) -> None:
    """Download url to dest and record it in the manifest (ADR 0009 §6.3)."""
    body = data.fetch(url)  # raises on any non-2xx status
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(body)
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    manifest[str(dest.relative_to(EVENTS))] = {
        "url": url,
        "downloaded_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "http_status": 200,  # data.fetch raises on any other final status
        "licence": licence,
        "committed": committed,
    }
    MANIFEST.write_text(json.dumps(dict(sorted(manifest.items())), indent=2) + "\n")


def parse_mof(path: Path = MOF_CSV) -> pd.DataFrame:
    """One row per intervention day and currency pair. Year and month cells are filled only
    on the first row of each block, so they are carried forward."""
    months = {
        m: i for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)
    }
    year = month = None
    out = []
    with path.open(encoding="cp932", newline="") as f:
        for r in csv.reader(f):
            if len(r) < 9:
                continue
            if r[3].strip().isdigit():
                year = int(r[3])
            if r[4].strip()[:3] in months:
                month = months[r[4].strip()[:3]]
            if r[5].strip().isdigit() and year and month:
                out.append(
                    {
                        "decision_date": dt.date(year, month, int(r[5])),
                        "amount_100m_yen": int(r[6].replace(",", "")),
                        "currency_pair": " ".join(r[8].split()),  # incl. U+3000
                    }
                )
    return pd.DataFrame(out)


def tokyo_business_days(holidays: set[dt.date], start: dt.date, end: dt.date) -> list[dt.date]:
    days = pd.bdate_range(start, end).date
    return [d for d in days if d not in holidays]


def load_holidays(path: Path = HOLIDAYS_CSV) -> set[dt.date]:
    """Cabinet Office public holidays plus the 31 Dec - 3 Jan bank holidays (ADR 0010 §3).
    The Cabinet calendar alone, as first built, gave 75 episodes; this calendar gives 74."""
    df = pd.read_csv(path, encoding="cp932")
    cabinet = set(pd.to_datetime(df.iloc[:, 0], format="%Y/%m/%d").dt.date)
    return cabinet | new_year_holidays(1955, 2100)


def new_year_holidays(first: int, last: int) -> set[dt.date]:
    """31 Dec to 3 Jan of every year: Tokyo bank holidays not in the Cabinet calendar."""
    return {
        d
        for y in range(first, last + 1)
        for d in (dt.date(y, 12, 31), dt.date(y, 1, 1), dt.date(y, 1, 2), dt.date(y, 1, 3))
    }


def episodes(dates: list[dt.date], holidays: set[dt.date]) -> list[int]:
    """Episode number per sorted unique date. The gap between consecutive intervention days is
    the number of Tokyo business days in (previous, current]; a new episode starts when it
    exceeds EPISODE_GAP. Interventions on a Tokyo holiday (e.g. 2024-04-29) are allowed: the
    holiday itself adds nothing to the gap."""
    bdays = tokyo_business_days(holidays, dates[0], dates[-1])
    ep, out = 1, []
    for i, d in enumerate(dates):
        if (
            i
            and bisect.bisect_right(bdays, d) - bisect.bisect_right(bdays, dates[i - 1])
            > EPISODE_GAP
        ):
            ep += 1
        out.append(ep)
    return out


def fx_row(rows: pd.DatetimeIndex, day: dt.date) -> dt.date | None:
    """First USD/JPY row on or after `day`. The end of a Tokyo calendar day (10:00 or 11:00
    New York time) precedes that New York date's noon fix (ADR 0009 §5.2)."""
    i = int(rows.searchsorted(pd.Timestamp(day)))
    return rows[i].date() if i < len(rows) else None


def direction(pair: str) -> str:
    """Yen leg of an MOF operation, read from the record's own currency-pair label."""
    if "Japanese yen (bought)" in pair:
        return "intervention: JPY bought"
    if "Japanese yen (sold)" in pair:
        return "intervention: JPY sold"
    return "intervention: no JPY leg"


def mof_events(fx_rows: pd.DatetimeIndex, holidays: set[dt.date]) -> pd.DataFrame:
    raw = parse_mof()
    raw = raw[raw["decision_date"] <= dt.date.fromisoformat(SAMPLE_END)]
    dates: list[dt.date] = sorted(raw["decision_date"].unique())
    ep = dict(zip(dates, episodes(dates, holidays), strict=True))
    starts = {d for i, d in enumerate(dates) if i == 0 or ep[d] != ep[dates[i - 1]]}
    rows = []
    for d in dates:
        g = raw[raw["decision_date"] == d]
        rid = f"MOF-{d:%Y%m%d}-1"
        for k, r in enumerate(g.itertuples(index=False), 1):
            rows.append(
                {
                    "event_id": f"{rid}-{k}",
                    "release_id": rid,
                    "institution": "MOF",
                    "decision_date": d,
                    "announce_ts": None,
                    "announce_ts_source": "none",
                    "ts_precision": "day",
                    "record_publication_date": None,
                    "observable": "unknown",
                    "fx_row_date": None,
                    "fx_row_decision": fx_row(fx_rows, d),
                    "fx_row_uncertain": True,
                    "policy_change": True,
                    "action": direction(str(r.currency_pair)),
                    "amount_100m_yen": r.amount_100m_yen,
                    "currency_pair": r.currency_pair,
                    "episode_id": f"MOF-EP{ep[d]:03d}",
                    "episode_start": d in starts,
                    "linked_ids": "",
                    "coordinated": False,  # the MOF record flags no joint operations (§3.6)
                    "superseded_by": "",
                    "source_file": str(MOF_CSV.relative_to(EVENTS)),
                    "hand_entered": False,
                    "note": "Created by editing 'Foreign Exchange Intervention Operations' "
                    "(Ministry of Finance, Japan), PDL 1.0",
                }
            )
    return pd.DataFrame(rows, columns=COLUMNS)


# --- Shared helpers -----------------------------------------------------------------------

NY = ZoneInfo("America/New_York")
TOKYO = ZoneInfo("Asia/Tokyo")
NOON = dt.time(12)
MON = {m[:3]: i for i, m in enumerate(calendar.month_name) if m}


def page_text(raw: str) -> str:
    raw = re.sub(r"<script.*?</script>|<style.*?</style>", " ", raw, flags=re.S)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", raw)).split())


def pdf_text(path: Path) -> str:
    return " ".join(" ".join(p.extract_text() or "" for p in PdfReader(path).pages).split())


def us_date(s: str) -> dt.date:
    """'March 31, 1995', 'Feb 20, 2008', 'Dec. 15, 1998' -> date."""
    m = re.fullmatch(r"([A-Z][a-z]+)\.? (\d{1,2}), (\d{4})", s.strip())
    if not m:
        raise ValueError(s)
    return dt.date(int(m[3]), MON[m[1][:3]], int(m[2]))


def noon_row(rows: pd.DatetimeIndex, ts: dt.datetime) -> dt.date | None:
    """Row whose New York noon fix is the first at or after ts (ADR 0009 §5.2)."""
    t = ts.astimezone(NY)
    day = t.date() if t.time() <= NOON else t.date() + dt.timedelta(days=1)
    return fx_row(rows, day)


def ny_day_end_row(rows: pd.DatetimeIndex, day: dt.date) -> dt.date | None:
    """Row containing the end of a New York calendar day: the next row's noon fix."""
    return fx_row(rows, day + dt.timedelta(days=1))


def announce_fields(
    rows: pd.DatetimeIndex, day: dt.date, clock: dt.time | None, tz: ZoneInfo, source: str
) -> dict[str, object]:
    """§5.1/§5.2 fields for a release announced on local `day`, at `clock` if stated."""
    if clock is not None:
        ts = dt.datetime.combine(day, clock, tz)
        row = noon_row(rows, ts)
        fix = dt.datetime.combine(row, NOON, NY) if row else None
        near = fix is not None and abs(ts - fix) <= dt.timedelta(minutes=15)
        return {
            "announce_ts": ts.isoformat(timespec="minutes"),
            "announce_ts_source": source,
            "ts_precision": "minute",
            "observable": "same_day",
            "fx_row_date": row,
            "fx_row_uncertain": near,
        }
    first = noon_row(rows, dt.datetime.combine(day, dt.time(0), tz))
    last = noon_row(rows, dt.datetime.combine(day, dt.time(23, 59), tz))
    return {
        "announce_ts": day.isoformat(),
        "announce_ts_source": source,
        "ts_precision": "day",
        "observable": "same_day",
        "fx_row_date": fx_row(rows, day),  # the row of the announcement date
        "fx_row_uncertain": first != last,
    }


NOT_ANNOUNCED = {
    "announce_ts": None,
    "announce_ts_source": "none",
    "ts_precision": "not_announced",
    "observable": "delayed",
    "fx_row_date": None,
    "fx_row_uncertain": True,
}


def number(rows: list[dict[str, object]], inst: str) -> pd.DataFrame:
    """§3.1 IDs: n orders releases sharing a decision date, k the actions in a release."""
    df = pd.DataFrame(rows).sort_values(["decision_date", "_order"], kind="stable")
    n = df.groupby("decision_date").cumcount() + 1
    df["release_id"] = [f"{inst}-{d:%Y%m%d}-{i}" for d, i in zip(df.decision_date, n, strict=True)]
    df["event_id"] = df["release_id"] + "-1"  # one coded action per release (§3.1)
    df["institution"] = inst
    df["hand_entered"] = False
    for c in COLUMNS:
        if c not in df:
            df[c] = None
    return df[COLUMNS]


# --- FOMC (§3.4) --------------------------------------------------------------------------

FED = EVENTS / "raw/fed"
FED_SITE = "https://www.federalreserve.gov"
FED_LICENCE = (
    "Federal Reserve Board: public domain, cite the Board (federalreserve.gov/disclaimer.htm)"
)
TARGET_TABLE_START = dt.date(1990, 1, 1)  # first year of the Board's openmarket archive table
QE_START = dt.date(2008, 11, 25)  # first asset-purchase announcement


def last_days(text: str, year: int) -> list[dt.date]:
    """Decision dates (last day) in a heading's date part: 'January 31-February 1',
    'April/May 30-1', 'October 21, 22, and 30' (one date per call)."""
    m = re.fullmatch(
        r"([A-Za-z]+)(?:/([A-Za-z]+))? ([\d, and]+?)(?:-(?:([A-Za-z]+) )?(\d+))?", text
    )
    if not m:
        raise ValueError(text)
    month = MON[(m[4] or m[2] or m[1])[:3]]
    if m[5]:
        return [dt.date(year, month, int(m[5]))]
    return [dt.date(year, month, int(d)) for d in re.findall(r"\d+", m[3])]


def fomc_calendar() -> list[dict[str, object]]:
    """Every meeting, call and notation vote on the Fed's historical pages (1981-2020) and
    meeting calendar (2021-), with its statement link and minutes release date."""
    out: list[dict[str, object]] = []
    rel = r"\(Released ([A-Z][a-z]+\.? \d{1,2}, \d{4})\)"
    for year in range(1981, 2021):
        src = FED / f"fomchistorical{year}.htm"
        for panel in re.split(
            r'<div class="panel panel-default[^"]*">', src.read_text(encoding="utf-8")
        )[1:]:
            h = re.search(r"<h5[^>]*>(.*?)</h5>", panel, re.S)
            if not h:
                continue
            head = " ".join(h[1].split())
            kind = (
                "cancelled"
                if "(cancelled)" in head
                else "unscheduled"
                if "(unscheduled)" in head
                else "notation vote"
                if "notation vote" in head
                else "call"
                if "Conference Call" in head
                else "meeting"
            )
            when = re.split(r" Meeting| Conference| \(", head)[0]
            stmt = re.search(r'href="([^"]+)">Statement</a>', panel)
            minutes = re.search(rel, panel) or re.search(
                r"Released ([A-Z][a-z]+\.? \d+, \d{4})", panel
            )
            for d in last_days(when, year):
                out.append(
                    {
                        "decision_date": d,
                        "kind": kind,
                        "heading": head,
                        "statement": stmt[1] if stmt else None,
                        "minutes": us_date(minutes[1]) if minutes else None,
                        "source_file": str(src.relative_to(EVENTS)),
                    }
                )
    src = FED / "fomccalendars.htm"
    page = src.read_text(encoding="utf-8")
    for block in re.split(r'<h4><a id="\d+">', page)[1:]:
        year = int(block[:4])
        for row in re.split(r'<div class="[^"]*\brow fomc-meeting"', block)[1:]:
            month = re.search(r"<strong>([A-Za-z/]+)</strong>", row)
            date = re.search(r"fomc-meeting__date[^>]*>([^<]*)<", row)
            if not month or not date:
                continue
            kind = (
                "notation vote"
                if "notation vote" in date[1]
                else ("unscheduled" if "unscheduled" in date[1] else "meeting")
            )
            days = re.sub(r"[^\d-]", "", date[1].split("(")[0])
            d = last_days(f"{month[1]} {days}", year)[0]
            stmt = re.search(
                r'Statement:</strong><br>\s*<a href="[^"]+">PDF</a> \| <a href="([^"]+)"', row
            )
            minutes = re.search(r"\(Released ([A-Z][a-z]+\.? \d{1,2}, \d{4})\)", row)
            out.append(
                {
                    "decision_date": d,
                    "kind": kind,
                    "heading": f"{month[1]} {date[1]} - {year}",
                    "statement": stmt[1] if stmt else None,
                    "minutes": us_date(minutes[1]) if minutes else None,
                    "source_file": str(src.relative_to(EVENTS)),
                }
            )
    return out


def target_changes() -> list[dict[str, object]]:
    """Federal-funds target changes from the Board's tables (1990-2002 and 2003-)."""
    out = []
    for name in ("openmarket_archive.htm", "openmarket.htm"):
        page = (FED / name).read_text(encoding="utf-8")
        for block in re.split(r"<h4>(?=\d{4}</h4>)", page)[1:]:
            year = int(block[:4])
            for r in re.findall(r"<tr[^>]*>(.*?)</tr>", block, re.S):
                cells = [page_text(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
                if len(cells) != 4:
                    continue
                m = re.match(r"([A-Z][a-z]+) (\d+)", cells[0])
                if not m:
                    continue
                up, down = (c if c not in ("...", "", "0") else "" for c in cells[1:3])
                move = f"+{up}" if up else f"-{down}"  # e.g. "-75-100" (2008-12-16)
                out.append(
                    {
                        "date": dt.date(year, MON[m[1][:3]], int(m[2])),
                        "bp": move,
                        "level": cells[3],
                        "source_file": f"raw/fed/{name}",
                    }
                )
    return sorted(out, key=lambda c: c["date"])  # type: ignore[arg-type, return-value]


def statement_file(link: str) -> Path:
    return FED / "statements" / link.strip("/").replace("/", "_")


def statement_time(link: str) -> tuple[dt.date, dt.time | None]:
    """Announcement date (the Board's dated URL) and the 'For release at' time, if stated."""
    text = page_text(statement_file(link).read_text(encoding="utf-8", errors="replace"))
    # The date printed above the release line; the URL date is a fallback only (the Board's
    # 2007-06-28 statement sits at ...20070618a.htm).
    stated = re.search(
        rf"({MONTHS_RE} \d{{1,2}}, \d{{4}})(?: [^.]{{0,60}}?)? For (?:immediate )?release", text
    ) or re.search(rf"Release Date: ({MONTHS_RE} \d{{1,2}}, \d{{4}})", text)
    day = (
        us_date(stated[1])
        if stated
        else dt.datetime.strptime(re.findall(r"\d{8}", link)[-1], "%Y%m%d").date()
    )
    m = re.search(r"For release at (\d{1,2}):(\d{2}) ([ap])\.m\. (E[SD]T)", text)
    if not m:
        return day, None
    hour = int(m[1]) % 12 + (12 if m[3] == "p" else 0)
    clock = dt.time(hour, int(m[2]))
    if dt.datetime.combine(day, clock, NY).tzname() != m[4]:  # §6.5 time-zone check
        raise ValueError(f"{link}: stated {m[4]} disagrees with the IANA rule for {day}")
    return day, clock


def note_link(statement: Path) -> str | None:
    """The Implementation Note linked from a statement page (2008 onward), if any."""
    m = re.search(
        r'href="([^"]+)">\s*Implementation Note',
        statement.read_text(encoding="utf-8", errors="replace"),
    )
    return m[1] if m else None


def release_text(statement: Path) -> str:
    """Statement text plus its Implementation Note, where the Board publishes the related
    discount-rate action in later years."""
    text = page_text(statement.read_text(encoding="utf-8", errors="replace"))
    note = note_link(statement)
    if note and statement_file(note).exists():
        text += " " + page_text(statement_file(note).read_text(encoding="utf-8", errors="replace"))
    return text


COORDINATED = re.compile(
    r"\b(coordinated|jointly|joint)\b[^.]{0,150}\bcentral banks?\b|"
    r"\bcentral banks?\b[^.]{0,150}\b(coordinated|jointly|joint)\b",
    re.I,
)


def fomc_events(rows: pd.DatetimeIndex) -> tuple[pd.DataFrame, dict[str, list[dict[str, object]]]]:
    """§3.4 releases. Returns the table and an audit record of everything left out."""
    cal = [c for c in fomc_calendar() if c["decision_date"] <= dt.date.fromisoformat(SAMPLE_END)]  # type: ignore[operator]
    by_date: dict[dt.date, list[dict[str, object]]] = {}
    for c in cal:
        if c["kind"] != "cancelled":
            by_date.setdefault(c["decision_date"], []).append(c)  # type: ignore[arg-type]
    intermeeting = []
    for ch in target_changes():
        d: dt.date = ch["date"]  # type: ignore[assignment]
        if d > dt.date.fromisoformat(SAMPLE_END):
            continue
        # The table dates the change (decision or effective day). Its source is a meeting,
        # call or vote decided, or announced by statement, on that day, the day before or
        # the business day before (2020-03-04 in the table: decided 03-02, announced 03-03;
        # 2020-03-16: Sunday 03-15 meeting); else intermeeting.
        prev = (pd.Timestamp(d) - pd.offsets.BDay(1)).date()
        before = (d, d - dt.timedelta(days=1), prev)
        hit = next((by_date[x] for x in before if x in by_date), None) or next(
            (
                v
                for v in by_date.values()
                if v[0].get("statement")
                and v[0]["decision_date"] >= prev - dt.timedelta(days=7)  # type: ignore[operator]
                and statement_time(str(v[0]["statement"]))[0] in before
            ),
            None,
        )
        if hit:
            hit[0]["change"] = ch
        else:
            intermeeting.append(ch)
    out: list[dict[str, object]] = []
    dropped = []
    for c in cal:
        if c["kind"] == "cancelled":
            dropped.append(c)
            continue
        if c["kind"] in ("call", "notation vote") and not c.get("statement") and "change" not in c:
            dropped.append(c)  # §3.4: calls and votes enter only with a policy decision
            continue
        out.append(fomc_row(rows, c))
    for ch in intermeeting:
        out.append(
            fomc_row(
                rows,
                {
                    "decision_date": ch["date"],
                    "kind": "intermeeting",
                    "heading": "target change with no meeting or call that day "
                    "or the previous business day",
                    "statement": None,
                    "minutes": None,
                    "change": ch,
                    "source_file": ch["source_file"],
                },
            )
        )
    audit = {"dropped": dropped, "intermeeting": intermeeting}
    return number(out, "FOMC"), audit


def fomc_row(rows: pd.DatetimeIndex, c: dict[str, object]) -> dict[str, object]:
    d: dt.date = c["decision_date"]  # type: ignore[assignment]
    ch = c.get("change")
    stmt = c.get("statement")
    notes = [f"{c['kind']}: {c['heading']}"]
    coordinated = False
    if stmt and d >= dt.date(1994, 1, 1):
        day, clock = statement_time(str(stmt))
        ann = announce_fields(
            rows, day, clock, NY, str(statement_file(str(stmt)).relative_to(EVENTS))
        )
        coordinated = bool(COORDINATED.search(release_text(statement_file(str(stmt)))))
    else:
        ann = dict(NOT_ANNOUNCED)
    if d < TARGET_TABLE_START:
        change, action = None, "not coded: no Board target-change table before 1990 (C2 gap)"
    elif isinstance(ch, dict):
        change = True
        action = f"funds target {ch['bp']} bp to {ch['level']} (Board table {ch['date']})"
    else:
        change, action = False, "funds target unchanged"
    if d >= QE_START:
        notes.append(
            "asset-purchase size/pace changes not coded (§3.4); policy_change "
            "reflects the funds target only"
        )
    if c["kind"] == "intermeeting":
        notes.append(
            "decision date = Board table date; basis of the decision not on the historical page"
        )
    return {
        **ann,
        "_order": 0,
        "decision_date": d,
        "record_publication_date": c.get("minutes"),
        "fx_row_decision": ny_day_end_row(rows, d),
        "policy_change": change,
        "action": action,
        "linked_ids": "",
        "coordinated": coordinated,  # §3.5: only where the release itself says so
        "superseded_by": "",
        "source_file": c["source_file"],
        "note": "; ".join(notes),
    }


# --- Federal Reserve Board discount rate (§3.5) -------------------------------------------

DISCOUNT_MINUTES = FED / "discount_minutes"
DM_HEAD = re.compile(
    r"(?:\b[A-Z][A-Z()&,/ ]{5,}[A-Z)]|Discount and Advance Rates|Monetary Policy Implementation)"
    r"\s*[-–—]{1,2}\s+"  # noqa: RUF001 (en and em dashes occur in the PDFs)
)
DM_CHANGE = re.compile(
    r"\b(increase|decrease|reduction|cut)s?\b.{0,120}?\b(discount|primary credit)( and advance)? "
    r"rate|the Board approved [^.]*\((an increase|a decrease|a reduction) from",
    re.I,
)
MONTHS_RE = "(?:" + "|".join(calendar.month_name[1:]) + ")"


def minutes_release(path: Path) -> dt.date:
    return dt.datetime.strptime(re.findall(r"\d{8}", path.name)[-1], "%Y%m%d").date()


def frb_entries() -> list[dict[str, object]]:
    """Every entry of the Board's discount-rate minutes (2001-05 onward): heading summary,
    action date, and whether it approves a change in the discount/primary credit rate.
    Layout-mode text keeps the right-aligned outcome and date lines below each heading."""
    out = []
    for f in sorted(DISCOUNT_MINUTES.glob("*.pdf")):
        text = "\n".join(p.extract_text(extraction_mode="layout") for p in PdfReader(f).pages)
        heads = list(DM_HEAD.finditer(text))
        ends = [h.start() for h in heads[1:]] + [len(text)] if heads else []
        for h, end in zip(heads, ends, strict=True):
            body = text[h.end() : end]
            right = re.search(
                rf"\n {{20,}}(\S[^\n]*)\n+ {{20,}}({MONTHS_RE}\s+\d{{1,2}},\s+\d{{4}})\.", body
            )
            summary = " ".join(body[: right.start() if right else 400].split())
            outcome = " ".join(right[1].split()) if right else ""
            change = (
                bool(DM_CHANGE.search(summary))
                and not re.match(r"Requests? by", summary)
                and outcome == "Approved."
            )
            # No outcome line (2 entries, releases of 2008-02-26 and 2010-04-13): the approval
            # date is not printed, so the entry is logged, not dated by guess (§6.4).
            out.append(
                {
                    "file": f,
                    "summary": summary,
                    "outcome": outcome or None,
                    "date": us_date(" ".join(right[2].split())) if right else None,
                    "change": change,
                }
            )
    return out


def frb_events(rows: pd.DatetimeIndex, fomc: pd.DataFrame) -> pd.DataFrame:
    """One release per Board approval of a discount/primary-credit rate change. An approval on
    an FOMC statement date whose statement mentions the rate is linked to that release and
    takes its announcement fields; other approvals have no primary announcement time."""
    stated = fomc[fomc.announce_ts.notna()].copy()
    stated["day"] = stated.announce_ts.str[:10]
    out: list[dict[str, object]] = []
    seen: set[tuple[dt.date, str]] = set()
    for e in frb_entries():
        if not e["change"] or e["date"] is None or e["date"] > dt.date.fromisoformat(SAMPLE_END):  # type: ignore[operator]
            continue
        d: dt.date = e["date"]  # type: ignore[assignment]
        key = (d, str(e["summary"])[:80])
        if key in seen:  # the same entry reprinted in a later minutes release
            continue
        seen.add(key)
        f: Path = e["file"]  # type: ignore[assignment]
        link = stated[(stated.decision_date == d) | (stated.day == d.isoformat())]
        linked = ""
        ann: dict[str, object] = {**NOT_ANNOUNCED, "observable": "unknown"}
        for _, r in link.iterrows():
            if re.search(
                r"discount rate|primary credit rate",
                release_text(EVENTS / r.announce_ts_source),
                re.I,
            ):
                linked = str(r.release_id)
                ann = {
                    c: r[c]
                    for c in (
                        "announce_ts",
                        "announce_ts_source",
                        "ts_precision",
                        "observable",
                        "fx_row_date",
                        "fx_row_uncertain",
                        "coordinated",
                    )
                }
        out.append(
            {
                **ann,
                "_order": 0,
                "decision_date": d,
                "record_publication_date": minutes_release(f),
                "fx_row_decision": ny_day_end_row(rows, d),
                "policy_change": True,
                "action": str(e["summary"])[:200],
                "linked_ids": linked,
                "coordinated": ann.get("coordinated", False),
                "superseded_by": "",
                "source_file": str(f.relative_to(EVENTS)),
                "note": "Board approval date from the discount-rate minutes"
                + ("" if linked else "; announcement time not in a collected primary record"),
            }
        )
    return number(out, "FRB")


# --- BOJ (§3.2, §3.3), restricted -----------------------------------------------------------

BOJ = EVENTS / "restricted/boj"
BOJ_SITE = "https://www.boj.or.jp"
BOJ_LICENCE = "BOJ: restricted (ADR 0009 §6.1); copy with credit, no alteration without permission"
NOT_DECISION = re.compile(
    r"^\((Reference|Short Note|Chart)|^Review of Monetary Policy|^Comprehensive Assessment|"
    r"^Joint Statement|^The \"Price Stability Target\" under|^On the Request from the Government"
)
GENERIC = re.compile(
    r"^(Statement on Monetary Policy|On Today's Decision at the Monetary Policy Meeting|"
    r"On the Current Monetary Policy|On Today's Monetary Policy Meeting|"
    r"On Monetary Policy Decisions|"
    r"Announcement of the Monetary Policy Meeting [Dd]ecisions?)$"
)
UNCHANGED = re.compile(r"unchanged|maintained", re.I)
FACILITY = re.compile(
    r"Fund-Provisioning|Lending Facility|Funds-Supplying Operation|Lending Arrangement|"
    r"Year 2000|Money Market Operation Tools|Liquidity Provision|New Line of Credit|"
    r"Purchases of ETFs and J-REITs|Chairman's Instructions"
)
CHANGE_TEXT = re.compile(
    r"decided[^.]{0,200}?\bto (change|raise|lower|increase|reduce|widen|modify|"
    r"abolish|end|terminate|discontinue|revise|lift|conduct yield curve control with greater "
    r"flexibility|further increase the flexibility)\b"
)
GUIDELINE_TEXT = re.compile(
    r"[Cc]hange in the guideline for money market operations|"
    r"decided[^.]{0,200}?\bto (change|lower|raise|reduce) (the guideline|policy interest rates)"
)
OFFICIAL_RATE_END = dt.date(1998, 3, 31)  # §3.3 period: discount-rate changes only


def boj_statements() -> list[dict[str, object]]:
    """Every item of the BOJ's yearly statement indexes: date, link, title, stated time."""
    out = []
    for year in range(1998, 2027):
        src = BOJ / f"state_{year}_index.htm"
        page = src.read_text(encoding="utf-8", errors="replace")
        for d, href, title in re.findall(
            r'<tr>\s*<td>(.*?)</td>\s*<td>\s*<a href="([^"]+)"[^>]*>(.*?)</a>', page, re.S
        ):
            title = re.sub(r"\[PDF.*", "", page_text(title)).strip()
            clock = re.search(r"Announced at (\d{1,2}):(\d{2}) ?([ap])\.?m", title)
            label = re.sub(r"\s*\(.*\)\s*$", "", title)  # title without the bracketed label
            out.append(
                {
                    "date": us_date(page_text(d)),
                    "href": href,
                    "title": title,
                    "label": label,
                    "source_file": str(src.relative_to(EVENTS)),
                    "clock": dt.time(
                        int(clock[1]) % 12 + (12 if clock[3] == "p" else 0), int(clock[2])
                    )
                    if clock
                    else None,
                }
            )
    return out


def boj_meetings() -> list[dict[str, object]]:
    """MPM decision dates (last meeting day) and minutes release dates, from the minutes
    indexes (§6.5 count source). Meetings whose minutes are not yet out come from the
    current schedule page."""
    out = []
    for year in range(1998, 2027):
        src = BOJ / f"minu_{year}_index.htm"
        for r in re.findall(
            r"<tr>(.*?)</tr>", src.read_text(encoding="utf-8", errors="replace"), re.S
        ):
            t = page_text(r)
            m = re.match(
                r"([A-Z][a-z]+\.? \d{1,2}, \d{4}) Meeting ?on (.+?)(?:,? (\d{4}))?(?: \[|$)", t
            )
            if not m:
                continue
            # last 'Month d' of e.g. 'October 31 and November 1'; the year is printed from
            # 2008 on, and each earlier page lists one year's meetings
            last = re.findall(r"([A-Z][a-z]+) ([\d ,and]+)", m[2])[-1]
            day = re.findall(r"\d+", last[1])[-1]
            out.append(
                {
                    "decision_date": dt.date(int(m[3] or year), MON[last[0][:3]], int(day)),
                    "minutes": us_date(m[1]),
                    "source_file": str(src.relative_to(EVENTS)),
                }
            )
    return out


def boj_text(href: str) -> str:
    f = BOJ / "statements" / href.rsplit("/", 1)[1]
    if f.suffix == ".pdf":
        return pdf_text(f)
    return page_text(f.read_text(encoding="utf-8", errors="replace"))


def boj_code(docs: list[dict[str, object]]) -> tuple[bool, str, str]:
    """§3.2 policy_change from the decision documents of one meeting: (value, action, basis).
    Scripted pass: BOJ's own 'unchanged' label first, then the document title, then the
    decision sentence of a generically titled statement. Facility-only items are 'anything
    else' (§3.2) and false."""
    titles = [str(x["title"]) for x in docs]
    if any(UNCHANGED.search(t) for t in titles):
        return False, "; ".join(titles), "BOJ label unchanged/maintained"

    def specific_part(t: str) -> str:
        """Title text beyond a generic heading, e.g. 'Eased further' in a bracketed label."""
        label = re.sub(r"\s*\(.*$", "", t)
        extra = re.sub(r",?\s*Announced at [^)]*", "", t[len(label) :]).strip(" ()-")
        return extra if GENERIC.match(label) else t

    specific = [specific_part(t) for t in titles if specific_part(t)]
    if specific:
        if all(FACILITY.search(t) for t in specific):
            for x in docs:  # a facility title can head a guideline change (2008-12-19)
                m = GUIDELINE_TEXT.search(boj_text(str(x["href"])))
                if m:
                    return True, m[0][:200], "statement text: guideline change"
            return False, "; ".join(specific), "facility/operation item only (§3.2 'anything else')"
        return True, "; ".join(specific), "decision title"
    for x in docs:
        m = CHANGE_TEXT.search(boj_text(str(x["href"])))
        if m:
            return True, m[0][:200], "statement text: decision sentence"
    return False, "; ".join(titles), "statement text: no change sentence"


def boj_events(rows: pd.DatetimeIndex) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    end = dt.date.fromisoformat(SAMPLE_END)
    stmts = [s for s in boj_statements() if not NOT_DECISION.search(str(s["title"]))]
    by_date: dict[dt.date, list[dict[str, object]]] = {}
    for s in stmts:
        by_date.setdefault(s["date"], []).append(s)  # type: ignore[arg-type]
    meetings: dict[dt.date, dict[str, object]] = {m["decision_date"]: m for m in boj_meetings()}  # type: ignore[misc]
    log: list[dict[str, object]] = []
    out: list[dict[str, object]] = []
    for d in sorted(set(meetings) | set(by_date)):
        if d > end or d < dt.date(1998, 4, 1):
            continue
        docs = by_date.get(d, [])
        m = meetings.get(d)
        if not docs:
            log.append({"date": d, "issue": "MPM in minutes index without a decision document"})
            continue
        if not m:
            log.append(
                {
                    "date": d,
                    "issue": "decision document without an MPM in the minutes "
                    "index (minutes not yet released, or not an MPM)",
                    "titles": [x["title"] for x in docs],
                }
            )
        change, action, basis = boj_code(docs)
        log.append(
            {
                "date": d,
                "issue": "coding",
                "policy_change": change,
                "basis": basis,
                "action": action,
                "titles": " || ".join(str(x["title"]) for x in docs),
            }
        )
        clock = next((x["clock"] for x in docs if x["clock"]), None)
        ann = announce_fields(rows, d, clock, TOKYO, str(docs[0]["source_file"]))  # type: ignore[arg-type]
        out.append(
            {
                **ann,
                "_order": 0,
                "decision_date": d,
                "record_publication_date": m["minutes"] if m else None,
                "fx_row_decision": fx_row(rows, d),
                "policy_change": change,
                "action": action[:200],
                "linked_ids": "",
                "coordinated": False,
                "superseded_by": "",
                "source_file": str(docs[0]["source_file"]),
                "note": f"scripted pass 1 ({basis}); second independent pass pending",
            }
        )
    for d, rate, src in boj_discount_changes():
        if d > OFFICIAL_RATE_END:
            continue
        out.append(
            {
                **NOT_ANNOUNCED,
                "observable": "unknown",
                "ts_precision": "day",
                "_order": 0,
                "decision_date": d,
                "record_publication_date": None,
                "fx_row_decision": fx_row(rows, d),
                "policy_change": True,
                "action": f"official discount rate to {rate} %",
                "linked_ids": "",
                "coordinated": False,
                "superseded_by": "",
                "source_file": src,
                "note": "§3.3: effective date in the BOJ series; decision and "
                "announcement dates not in the source",
            }
        )
    return number(out, "BOJ"), log


def boj_discount_changes() -> list[tuple[dt.date, str, str]]:
    """(effective date, rate, source) for every official discount / basic loan rate level
    from 1981 (cdab0100: to 2001-01; cdab0101: 2001-01 onward)."""
    out = []
    for name in ("cdab0100.csv", "cdab0101.csv"):
        src = BOJ / "discount" / name
        with src.open(encoding="cp932", newline="") as f:
            for r in csv.reader(f):
                if r and re.fullmatch(r"\d{4}\.\d{2}\.\d{2}", r[0]) and r[1].strip():
                    d = dt.datetime.strptime(r[0], "%Y.%m.%d").date()
                    if dt.date(1981, 1, 1) <= d <= dt.date.fromisoformat(SAMPLE_END):
                        out.append((d, r[1].strip(), str(src.relative_to(EVENTS))))
    return out


# --- Collect -------------------------------------------------------------------------------

CAO_LICENCE = "Cabinet Office holiday CSV: terms unread, restricted (ADR 0009 §6.1)"
MOF_LICENCE = "MOF: Public Data License 1.0; derived rows labelled as edited (ADR 0009 §6.2)"


def get(url: str, dest: Path, licence: str, committed: bool) -> Path:
    """fetch() unless the file is already collected: the collected vintage is what is
    checksummed (§8 D5), so a rerun never silently replaces it."""
    if not dest.exists():
        fetch(url, dest, licence, committed)
        time.sleep(0.25)  # polite to the publishers' servers
    return dest


def collect() -> None:
    """Download every source file the build reads. Idempotent; see get()."""
    get(MOF_URL, MOF_CSV, MOF_LICENCE, True)
    get(HOLIDAYS_URL, HOLIDAYS_CSV, CAO_LICENCE, False)
    mp = f"{FED_SITE}/monetarypolicy/"
    for year in range(1981, 2021):
        get(f"{mp}fomchistorical{year}.htm", FED / f"fomchistorical{year}.htm", FED_LICENCE, True)
    for name in (
        "fomccalendars.htm",
        "openmarket.htm",
        "openmarket_archive.htm",
        "discountrate-archive.htm",
        "discount-rate-minutes.htm",
    ):
        get(mp + name, FED / name, FED_LICENCE, True)
    for c in fomc_calendar():
        if c["statement"]:
            st = get(
                FED_SITE + str(c["statement"]),
                statement_file(str(c["statement"])),
                FED_LICENCE,
                True,
            )
            note = note_link(st)
            if note:
                get(FED_SITE + note, statement_file(note), FED_LICENCE, True)
    for name in ("discountrate-archive.htm", "discount-rate-minutes.htm"):
        for h in re.findall(r'href="([^"]+\.pdf)\s*"', (FED / name).read_text(encoding="utf-8")):
            url = h if h.startswith("http") else FED_SITE + h
            dest = DISCOUNT_MINUTES / url.split("federalreserve.gov/")[1].replace("/", "_")
            if (
                re.search(r"monetary|attachment|bcreg", dest.name)
                and "bcreg20070904" not in dest.name
            ):
                get(url, dest, FED_LICENCE, True)  # bcreg20070904b1.pdf: link is dead (404)
    for year in range(1998, 2027):
        get(
            f"{BOJ_SITE}/en/mopo/mpmdeci/state_{year}/index.htm",
            BOJ / f"state_{year}_index.htm",
            BOJ_LICENCE,
            False,
        )
        get(
            f"{BOJ_SITE}/en/mopo/mpmsche_minu/minu_{year}/index.htm",
            BOJ / f"minu_{year}_index.htm",
            BOJ_LICENCE,
            False,
        )
    for name in ("cdab0100.csv", "cdab0101.csv"):
        get(
            f"{BOJ_SITE}/en/statistics/boj/other/discount/{name}",
            BOJ / "discount" / name,
            BOJ_LICENCE,
            False,
        )
    for s in boj_statements():
        if not NOT_DECISION.search(str(s["title"])):
            href = str(s["href"])
            get(BOJ_SITE + href, BOJ / "statements" / href.rsplit("/", 1)[1], BOJ_LICENCE, False)


# --- Build ---------------------------------------------------------------------------------


def build() -> pd.DataFrame:
    """Public table (MOF, FOMC, FRB) and the restricted full table (adds BOJ, §6.1)."""
    from kagura.explore import load_daily

    daily = load_daily()
    fx_rows = pd.DatetimeIndex(daily.loc[daily["usdjpy"].notna(), "date"])
    fomc, _ = fomc_events(fx_rows)
    frb = frb_events(fx_rows, fomc)
    back = frb[frb.linked_ids != ""].groupby("linked_ids").release_id.agg(" ".join)
    fomc["linked_ids"] = fomc.release_id.map(back).fillna("")  # §3.5: both rows name the other
    public = pd.concat([mof_events(fx_rows, load_holidays()), fomc, frb], ignore_index=True)
    public.to_csv(EVENTS / "policy_events.csv", index=False)
    boj, log = boj_events(fx_rows)
    pd.concat([public, boj], ignore_index=True).to_csv(
        BOJ.parent / "policy_events_full.csv", index=False
    )
    # every BOJ coding decision and gap, for the second independent pass (§6.4); restricted
    pd.DataFrame(log).to_csv(BOJ.parent / "boj_coding_log.csv", index=False)
    return public


ANCHORS = {
    "BOJ": ["1999-02-12", "2001-03-19", "2013-04-04", "2016-01-29", "2016-09-21", "2024-03-19"],
    "MOF": ["2022-09-22"],
}


def validate(table: pd.DataFrame) -> dict[str, object]:
    """ADR 0009 §6.5 checks on a built table (strings, as read back from CSV). Returns the
    failures and the per-year counts; an empty failure list means every check passed."""
    t = table.fillna("")
    fail: list[str] = []
    if not t.event_id.is_unique:
        fail.append("duplicate event_id")
    if not t.release_id.str.fullmatch(r"(BOJ|FOMC|FRB|MOF)-\d{8}-\d+").all():
        fail.append("release_id pattern")
    if not (t.event_id.str.slice(0, -2) == t.release_id).all():
        fail.append("event_id is not release_id-k")
    if not t.release_id.str[-10:-2].eq(t.decision_date.str.replace("-", "")).all():
        fail.append("release_id date differs from decision_date")
    dupes = t[t.institution != "MOF"].duplicated(["institution", "decision_date", "action"])
    if dupes.any():
        fail.append(f"duplicate releases: {t[t.institution != 'MOF'][dupes].release_id.tolist()}")
    if not t.decision_date.between("1981-01-01", SAMPLE_END).all():
        fail.append("decision_date outside 1981-01-01..SAMPLE_END")
    ann = t.announce_ts.str[:10]
    late = t[(ann != "") & (ann < t.decision_date)]
    if len(late):
        fail.append(f"announced before decision: {late.release_id.tolist()}")
    pub = t[(t.record_publication_date != "") & (ann != "") & (t.record_publication_date < ann)]
    if len(pub):
        fail.append(f"record published before announcement: {pub.release_id.tolist()}")
    if (t[t.observable == "same_day"].fx_row_date == "").any():
        fail.append("same_day release without fx_row_date")
    if (t[t.observable != "same_day"].fx_row_date != "").any():
        fail.append("fx_row_date on a release that was not announced same day")
    for inst, days in ANCHORS.items():
        for d in days:
            rows = t[(t.institution == inst) & (t.decision_date == d)]
            if inst in set(t.institution) and not (rows.policy_change == "True").any():
                fail.append(f"anchor {inst} {d} missing or not a policy change")
    years = t.assign(year=t.decision_date.str[:4])
    counts = years.groupby(["institution", "year"]).release_id.nunique().unstack(0).fillna(0)
    return {"failures": fail, "releases_per_year": counts.astype(int)}


if __name__ == "__main__":
    if sys.argv[1:] == ["collect"]:
        collect()
    else:
        build()
        full = pd.read_csv(BOJ.parent / "policy_events_full.csv", dtype=str)
        failures: list[str] = validate(full)["failures"]  # type: ignore[assignment]
        print("\n".join(failures) or "validation: all §6.5 checks passed")
