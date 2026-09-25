# ADR 0002 — Data sources for v0.1

Date: 2026-09-15

## Context

v0.1 needs USD/JPY, US and Japanese government yields, policy rates, and a
few macro controls, ingested reproducibly with the smallest possible
surface. Each source was downloaded and inspected before this decision.

## Options considered

1. FRED via the official API (needs a free key).
2. FRED via the public per-series CSV endpoint (no key).
3. yfinance or other market-data wrappers for USD/JPY.
4. OECD-sourced Japan CPI on FRED.
5. BIS long consumer-price series for Japan.
6. Bank of Japan time-series portal for the policy rate.

## Decision

| Series | Source | Frequency |
|---|---|---|
| usdjpy | FRED DEXJPUS (Fed H.10 noon New York rate) | daily |
| us_2y, us_10y | FRED DGS2, DGS10 (constant maturity) | daily |
| fed_funds | FRED DFF (effective rate) | daily |
| jgb_2y, jgb_10y | Ministry of Finance JGB par yields | daily |
| jp_call_rate | FRED IRSTCI01JPM156N (uncollateralized overnight call rate) | monthly |
| us_cpi | FRED CPIAUCSL | monthly |
| jp_cpi | BIS WS_LONG_CPI, M.JP.628 | monthly |
| brent | FRED DCOILBRENTEU | daily |
| vix | FRED VIXCLS | daily |

Downloads use the keyless FRED CSV endpoint (option 2), the MOF CSV files,
and the BIS SDMX CSV endpoint. Raw files are cached unchanged in data/raw/
with a manifest recording URL and download time. The parsed output is one
long table (date, series, value) in data/processed/series_long.csv.

## Rationale

- Official or primary sources only; no market-data wrappers whose
  provenance is unclear.
- No API key removes a setup step and a secret. The key becomes necessary
  only for ALFRED vintages, which a later release-date decision may need.
- Every OECD-sourced Japan CPI series on FRED stopped in June 2021. The
  BIS long series is current and keyless.
- The MOF file is the only free daily JGB history; it starts in 1974 for
  2Y but only in July 1986 for 10Y.
- The BOJ portal has no stable keyless CSV endpoint; the monthly call rate
  on FRED is adequate for a policy-rate control in v0.1.

## Risks and limitations

- The FRED CSV endpoint is public but not a documented API; if it changes,
  the fetcher moves to the official API with a key.
- The 10Y differential is only available from July 1986; the 2Y
  differential is the primary measure for the full 1981 sample.
- The Japan call rate begins in July 1985, leaving 1981 to mid-1985 without
  a policy-rate series. The discount rate was the operative instrument
  then; add FRED INTDSRJPM193N if that gap matters to a result.
- USD/JPY is a noon New York fixing, not a close. Daily changes therefore
  span a different window than a Tokyo or London close would.
- FRED and BIS values are current vintages, not real-time vintages. CPI
  revisions are small for these indices, but this is a known limitation
  until a release-date rule is decided.
