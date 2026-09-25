# ADR 0005 — Carried-share guard after a Brent source change

Date: 2026-09-25

## Context

A fresh `make data` run on 2026-09-25 was compared with the 2026-09-15
download used for the exploratory notebook. 890 historical Brent
observations (FRED `DCOILBRENTEU`, from EIA) between 1987-12-21 and
2014-10-14 that had values on 2026-09-15 are blank in the new file (for
example, 1987-12-21 was 15.40). The dates are still there, only the values
are gone. No remaining value changed, and 9 new days were added.

The pipeline handled this as designed (ADR 0003): each blank day takes the
last value within 7 days and is flagged `brent_carried`. But the result is
that Brent's carried share rose from 1.5% to 10.0%, with 30–48% of days
carried in 1994–1995, and nothing in `make data` or `make test` reported it.
A source losing history would have gone unnoticed, looking like a flat
price.

Why the values disappeared (an EIA revision, a FRED processing change, or
a temporary fault) has not been established.

## Options considered

1. Replace the Brent source (e.g. EIA directly).
2. Pin the 2026-09-15 raw file.
3. Add a check on the share of carried values, and keep the source.

## Decision

Option 3. `kagura.align.carried_share` computes, for each daily market
series, the share of its non-missing values carried from an earlier day.
The cap is `MAX_CARRIED_SHARE = 8%`.

- `make data` prints a warning for **any** series above the cap.
- `make test` **fails** if one of the four H1 inputs (US 2Y, US 10Y,
  JGB 2Y, JGB 10Y) is above the cap.

Brent is not an H1 input, so its deterioration warns but does not fail.

## Rationale

- Market holidays alone give carried shares up to about 6% (JGBs, Tokyo
  holidays: 5.3% overall, at most 6.0% in any decade). 8% leaves room for
  that while catching a loss of history the size seen here.
- The source is not replaced and data are not pinned: v0.1 does not use
  Brent for H1, and the research scope is unchanged. Pinning would also mean
  redistributing data, which the repository avoids.

## Risks and limitations

- A full-sample share can hide a short outage in a long series. A per-year
  check would be stricter; it is not needed for the failure seen so far.
- The check detects values turned into gaps. It does not detect revised
  values, which only a vintage comparison or checksum of raw files would.
- Brent in current downloads is degraded, most heavily 1992–2006, until
  the source is checked or replaced. Any later use of Brent must first
  revisit this ADR.
