# ADR 0001 — Sample period

Date: 2026-09-11

## Context

The v0.1 question is whether USD/JPY decoupled from the US-Japan yield
differential. Answering "when" requires a long sample that includes the
periods in which the relationship is believed to have held.

Source availability: FRED USD/JPY from 1971, US 2Y Treasury from 1976,
MOF daily JGB yields from 1974, US and Japanese CPI from the 1950s.

## Options considered

1. Start in 1971 (end of Bretton Woods, yen floats).
2. Start in December 1980 (Japan liberalizes cross-border capital flows
   under the revised Foreign Exchange and Foreign Trade Control Law).
3. Start in 1999 (BOJ zero interest rate policy; modern regime only).
4. Start in 2000 or later.

## Decision

Ingest all available history. The modeling sample starts 1981-01-01.
The post-1999 period is reported as a robustness subsample, not the
primary sample.

## Rationale

Before capital liberalization the yield differential could not be freely
arbitraged, so the mechanism under test did not operate in the same form.
Starting in 1981 keeps the Plaza Accord (1985), Louvre Accord (1987), the
bubble and its collapse, ZIRP, QQE, and yield curve control inside the
sample, which is the regime variation the project exists to study.

## Risks and limitations

- The 2Y JGB market was thin in the 1980s; the 2Y differential is noisier
  before roughly 1990.
- The 1980s exchange rate was heavily influenced by coordinated
  intervention and trade friction, so a weak rate relationship in that
  decade is not evidence for the modern decoupling claim by itself.
- Any structural-break result must be read against the number of known
  policy regime changes in a 45-year window.
