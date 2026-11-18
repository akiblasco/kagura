# Phase A report: descriptive structural-break estimation of the USD/JPY–rate-differential link

Status: draft for review, 2026-11-18. Exploratory (ADR 0007), Phase A (ADR 0011), Bai intervals
per ADR 0012. Outputs: commit `02032cb`, `research/adr0007/out/phase_a/`.

## Summary

Under the Phase A daily-change specifications, model-selection procedures do not identify 2022
as a preferred structural-break date. This does not rule out changes around 2022 or resolve
long-run exchange-rate decoupling.

- **Full sample (1981–2026), primary specification:** BIC and LWZ both select one break at
  **2004-04**, where the daily slope rises from 0.51 to 4.44 % per percentage point.
- **Recent sample (2013–2026):** **BIC selects one break at 2017-10 (slope 7.97 → 4.21); LWZ
  selects no break.** The two criteria disagree on whether any break is worth adding, and
  BIC's margin is small (ΔBIC = −0.0049).
- The slope that H1a compared across fixed eras moves mostly with the **variability of the two
  series**, not with their correlation. The daily correlation of ΔUSD/JPY with Δ2Y differential
  is **higher** in 2022–2026 (0.44) than in any earlier period examined.

Nothing here is a statistical test. Break dates are least-squares partitions; break counts are
model-selection preferences; intervals are nominal.

## 1. Question and why 2022 was plausible

KAGURA asks: *has USD/JPY decoupled from the US–Japan interest-rate differential, and if so,
when and by how much?*

2022 was a natural candidate:

- the Fed began a fast tightening cycle in March 2022;
- the BOJ kept yield-curve control until 2024, so the differential widened mainly on the US side;
- USD/JPY moved from about 115 to above 150, and MOF intervened in September and October 2022;
- H1a (ADR 0006) used 2022-01 as its pre-specified era boundary. It found the daily slope fell
  from 6.44 (2013–21) to 4.05 (2022–), a −37 % change. Its frozen verdict is **inconclusive**:
  the pre-registered test could not tell whether the decline was material, meaning at least
  one third.

Phase A asks a different question from H1a: **if the data are allowed to choose where the slope
changes, where do they put the boundaries?** H1a's verdict stands as frozen. Phase A neither
confirms nor overturns it.

## 2. Method and its limits

**Frozen design (ADR 0007, ADR 0011 §7, ADR 0012):**

- Model: Δlog USD/JPY (%) on a constant and the same-day Δ2Y US–Japan differential (pp).
- Breaks: global least-squares partitions for m = 0…5 by dynamic programming.
- Candidate dates: month-start rows only, plus a daily-grid sensitivity for m = 1.
- Trimming: ε = 15 % (conventional), 10 % and 5 % (sensitivity).
- Selection: BIC and LWZ.
- Intervals: Bai (1997) intervals, robust form, with the ADR 0012 correction.
- Standard errors: HAC (Newey–West), conditional on the dates.
- Grid: 5 specifications × 2 samples × 3 trimmings = 30 cells.

**Verification:**

- The gate passed: the R comparison has 0 FAIL, and the five ADR 0011 hashes are unchanged.
- Rerunning `run_breaks.py` and `phase_a_figures.py` reproduces every output file byte for byte.
- Lint and mypy are clean; tests pass (177 passed, 1 skipped).

**What descriptive break estimation cannot do:**

- A least-squares partition always places m breaks, even when no break exists. A date is where
  the fit improves most, not evidence that something changed.
- BIC and LWZ trade fit against parameters under the model's assumptions. They express a
  preference, not a probability that a break exists. Under heteroskedastic, serially correlated
  daily errors, their behaviour is not validated here.
- Phase B (sup-F, UDmax, WDmax, sequential tests, wild bootstrap) is withheld. The ADR 0007 §9.1
  critical-value check failed and remains failed (ADR 0011 §1). **No break count is
  statistically established.**
- Bai intervals are nominal (§7).
- **Eligibility constraint:** in the full sample at ε = 15 %, the last eligible break date is
  **2019-10-01**. That cell cannot place a break in 2022 at all. Only the recent sample, and the
  full sample at ε = 10 % or 5 %, can.

## 3. Full sample: the link strengthened around 2004

Figures: `figures/01_regime_slopes.png` (top), `02_break_map.png`, `03_information_criteria.png`.

| ε | BIC m | LWZ m | m = 1 date |
|---|---|---|---|
| 15 % | 1 | 1 | 2004-04-01 |
| 10 % | 2 | 1 | 2004-04-01 |
| 5 % | 3 | 1 | 2004-04-01 |

- **m = 1 (all ε):** slope 0.51 (SE 0.14) before 2004-04, **4.44** (0.22) after.
  - Nominal 95 % interval: 2003-07-15 .. 2004-07-30, 381 days.
  - The daily grid puts the date at 2004-04-02. SSR is 4160.02 there against 4160.27 on the
    month grid.
- **BIC at smaller trimming** adds dates in the 1980s:
  - ε = 5 %, m = 3: 1986-11 and 1989-03, with slopes 1.09 | −2.53 | 0.21 | 4.44.
  - The 1986–89 negative regime is 520 rows long and appears only at small trimming. ADR 0007
    §3.4 says a date found only at ε = 5 % "is reported as such and never promoted".
- **Higher-m partitions** that neither criterion selects add 2011-12 and 2018-11 (ε = 15 %), or
  2009-05 and 2017-10 (ε = 10 % and 5 %).

**Reading:** across 1981–2026 the dominant pattern is a strengthening of daily co-movement, not
a weakening. Before 2004 the daily association was near zero. Figure 4 shows the correlation
moving from about 0.07 before 2004 to 0.34–0.44 afterwards.

## 4. Recent sample: BIC finds a late-2017 break, LWZ finds none

| ε | BIC m | LWZ m | m = 1 date | ΔBIC(m = 1) | ΔLWZ(m = 1) |
|---|---|---|---|---|---|
| 15 % | 1 | **0** | 2017-10-02 | −0.0049 | +0.0115 |
| 10 % | 1 | **0** | 2017-10-02 | −0.0049 | +0.0115 |
| 5 % | 1 | **0** | 2017-10-02 | −0.0049 | +0.0115 |

ΔIC is measured relative to m = 0; negative means preferred.

**m = 1:** slope **7.97** (SE 0.87) for 2013-01 to 2017-09, then **4.21** (0.29) from 2017-10
to 2026-09. The fall is 3.76, or −47 %.

- The nominal 95 % interval is 2017-03-15 .. 2020-07-20: 1,223 days, or 27–35 % of the eligible
  range.
- The daily grid puts the date at 2017-09-14.

**Exploratory post hoc sensitivity: a break forced at 2022-01.** This is not a hypothesis test,
and it was chosen after the results were seen. It uses the same cell (primary, recent, ε = 15 %),
the same model, the same 115 eligible month-start candidates and the same objective (SSR) as
Phase A. The code is in Appendix A; its output is not committed.

| Single break at | SSR | Δlog SSR vs m = 0 | ΔBIC vs m = 0 | Rank of 115 |
|---|---|---|---|---|
| 2017-10-02 (selected) | 924.847 | −0.01275 | −0.00486 | 1 |
| 2021-12-01 | 928.131 | −0.00920 | −0.00131 | 30 |
| 2022-01-05 | 928.313 | −0.00901 | −0.00112 | 31 |

- The profile minimum reproduces the `partitions.csv` m = 1 SSR exactly. Penalties per break,
  implied by `partitions.csv`, are 0.00789 (BIC) and 0.02429 (LWZ).
- A 2022-01 break obtains **71 %** of the SSR reduction that the best single break obtains. Its
  SSR is 3.47 (0.37 %) higher than at 2017-10.
- BIC would still prefer a 2022-01 break to no break, by a smaller margin. LWZ prefers no break
  to any single date.
- The profile is not flat near the optimum. All 12 best candidates lie in 2017-03 .. 2018-03,
  and 2022-01 ranks 31st. **2022-01 is a clearly inferior single-break location, though not one
  that fits worse than no break under BIC.**

**Exploratory m = 4 partition** (ε = 15 %, not selected by either criterion):

| Regime | Slope |
|---|---|
| 2013-01 .. 2015-05 | 7.52 |
| 2015-06 .. 2017-09 | 8.26 |
| 2017-10 .. 2019-10 | 4.08 |
| 2019-11 .. 2021-11 | 6.66 |
| 2021-12 .. 2026-09 | 4.05 |

It hints at a second step down at 2021-12. That pattern is a hypothesis for later work, not a
result.

## 5. Why the fixed-era H1a contrast differs from estimated regimes

For a regression with an intercept, the pooled OLS slope decomposes exactly into within-group
slopes plus a between-group term:

b_pooled = [Σ_g S_xx,g · b_g + Σ_g n_g (x̄_g − x̄)(ȳ_g − ȳ)] / [Σ_g S_xx,g + Σ_g n_g (x̄_g − x̄)²]

Here S_xx,g is the within-group sum of squared deviations of Δdiff.

Applied to the H1a "old" era (2013-01-07 .. 2021-12-30, 2,007 rows) split at the Phase A date:

| Term | Rows | Slope | Weight | Contribution |
|---|---|---|---|---|
| 2013-01 .. 2017-09 (within) | 1,063 | 7.9737 | 0.4780 | 3.8116 |
| 2017-10 .. 2021-12 (within) | 944 | 5.0326 | 0.5209 | 2.6216 |
| Between-group means | — | — | 0.0011 | 0.0114 |
| **Pooled** | 2,007 | **6.4446** | 1 | 6.4446 |

The sum reproduces the pooled slope to 10⁻⁶, and the pooled slope matches the H1a reference
slope of 6.44. The between-group term is negligible because the mean daily changes barely differ
between the two periods.

So the H1a contrast of 6.44 against 4.05 compares 2022– with an average over 2013–21:

- Most of the gap is already present between 2013–17 and 2017–21.
- 2017–21 to 2022– is a smaller step, 5.03 to 4.05.

A pre-specified era boundary and an estimated regime boundary answer different questions, so
both numbers are correct descriptions. They should not be read as the same claim.

## 6. Differences across specifications

| Specification | Full sample (selection; m = 1 date; slopes) | Recent sample (selection) |
|---|---|---|
| Primary: 2Y, same day | BIC 1–3, LWZ 1; 2004-04; 0.51 → 4.44 | BIC 1 (2017-10), LWZ 0 |
| V1: US leg lagged one day | BIC 1, LWZ 0; 1996-08; −0.02 → 1.46 | BIC 0, LWZ 0 |
| V2: 10Y | BIC 3, LWZ 1; 2004-02; −0.72 → 3.75 | BIC 2 (2016-01, 2018-02), LWZ 0 |
| V3: monthly | BIC 1, LWZ 1; 2005-03; 0.52 → 7.04 | BIC 0, LWZ 0 |
| Lag-augmented (p = 1) | BIC 1–3, LWZ 1; 2004-04; 0.50 → 4.54 | BIC 1 (2017-10), LWZ 0 |

- **10Y (V2).** The full-sample rise is gradual, in three steps: −1.26 | 1.03 (1999-02) | 2.90
  (2005-12) | 4.59 (2012-02). In the recent sample, BIC isolates a high-slope window from
  2016-01 to 2018-01 (8.77) between two periods near 4, which matches the 2Y story. The V2
  recent m = 1 interval at ε = 15 % spans 143 % of the eligible range and is uninformative.
- **Monthly (V3).** The full-sample break is in 2005 and of similar shape. No recent-sample
  break is selected. The unselected m = 1 date is 2023-08, with the slope *rising* from 5.80 to
  9.88 over only 37 months.
- **Lagged US leg (V1).** Slopes are small throughout, so the association is same-day. Next-day
  FX does not respond to yesterday's US yield move.
- **Lag-augmented model: a different estimand.** It is the same-day slope after conditioning on
  lagged FX and lagged differential changes, so its coefficients are not comparable with the
  static slopes. What can be compared is the dates, which agree: 2004-04 and 2017-10.

Robust across these: a full-sample strengthening around 2004–05, and the absence of a selected
2022 break.

Not robust: the number of breaks, the 1980s dates, and the 2015–18 detail.

## 7. Interval widths, and why their coverage is not established

| Cell (m = 1) | Nominal 95 % interval | Width |
|---|---|---|
| Primary full | 2003-07-15 .. 2004-07-30 | 381 days |
| Lag-augmented full | 2003-07-25 .. 2004-06-30 | 341 days |
| Lag-augmented recent | 2017-04-26 .. 2019-01-10 | 624 days |
| V3 full | 2003-02-28 .. 2007-02-28 | 1,461 days |
| Primary recent | 2017-03-15 .. 2020-07-20 | 1,223 days |
| V1 full | 1991-05-10 .. 1997-07-29 | 2,272 days |
| V2 recent, ε = 15 % | 2015-02-02 .. 2024-08-01 | 3,468 days, truncated |

Bai's interval is derived for one true break of shrinking size in a correctly specified model.
Here m is unknown, the model is a deliberate simplification, the errors are heteroskedastic and
serially correlated, and the dates sit on a month grid.

In simulations, coverage at nominal 95 % ranged from 76.5 % (ADR 0011 §6) to 97.2 % (ADR 0012
§3.2), depending on design. **That range is not a bound for these estimates.** Widths are
reported as a rough sense of how sharply the fit locates a date, not as confidence sets.

## 8. Competing economic interpretations

None of these is tested here. They are not mutually exclusive.

**1. Changing rate volatility and yield-curve control.**

| Period | sd Δdiff (pp) | sd ΔFX (%) | corr | slope |
|---|---|---|---|---|
| 1981 .. 2004-03 | 0.093 | 0.68 | 0.07 | 0.51 |
| 2004-04 .. 2012 | 0.056 | 0.67 | 0.34 | 4.14 |
| 2013 .. 2017-09 | 0.030 | 0.66 | 0.36 | 7.97 |
| 2017-10 .. 2021 | 0.033 | 0.40 | 0.42 | 5.03 |
| 2022 .. 2026-09 | 0.073 | 0.68 | 0.44 | 4.05 |

Source: `figures/04_rate_volatility.csv`, figure 4. The slope equals corr × sd(ΔFX) / sd(Δdiff).

- The high 2013–17 slope comes with an unusually quiet differential: the zero lower bound, then
  negative rates and yield-curve control pinning the Japanese leg. The correlation in that
  period was not unusually high.
- After 2017, FX volatility fell to historic lows (2017–21).
- From 2022, rate volatility more than doubled.
- Correlation rose in every period.

On the correlation measure, the 2022– period shows the **closest** daily co-movement in the
sample. ADR 0006 had already noted, before H1a was run, that the correlation was higher in
2022– (0.44 against 0.37).

**The estimand is unchanged.** The H1a slope, % USD/JPY per pp, remains the primary short-run
sensitivity measure. Correlation and relative volatility are reported only as complementary
descriptive measures that help read the slope. They are not alternative definitions of
decoupling chosen after seeing these results. Long-run (level) decoupling remains H1b's
separate question.

**2. Composition of shocks.** When the differential barely moves, the few days it does move are
dominated by specific news, such as US data and FOMC days. The slope then describes FX's
response to those shocks. When rate volatility is broad-based (2022–), it averages over many
kinds of news, including risk-off moves and intervention days, where yen and yields may move
differently. A changed slope can therefore reflect a changed mix of shocks rather than a
changed transmission.

**3. Observation timing (ADR 0012 L19).** FX is the New York noon fix, yields close around
15:30, and FOMC statements arrive at 14:00–14:15 ET. Afternoon news therefore reaches FX one row
after yields.

- V1's small slopes say the next-row response is weak on average.
- If the share of afternoon news varied by era, the same-day slope would move with it.
- MOF New York-afternoon interventions (ADR 0012 L21) add the same issue for 2022 and 2024
  specifically.
- The monthly V3 specification, which is immune to intraday timing, still dates the
  full-sample rise to 2005 and selects no recent break.

**4. Model dependence.** Dates and counts depend on:

- the criterion (BIC adds breaks, LWZ is conservative);
- the maturity (10Y shows gradual steps);
- the frequency;
- trimming, which decides whether 2022 is even eligible in the full sample.

**5. Level versus change decoupling.** All Phase A models are in daily or monthly changes. Long-run
divergence between the level of USD/JPY and the differential is H1b's question and is not
addressed here.

## 9. What Phase A does not establish

- That any break exists, or how many. There are no tests; BIC and LWZ express preferences.
- That 2017-10 or 2004-04 is the date of an economic change. The intervals are wide and nominal.
- That nothing changed around 2022. A forced 2022-01 split still captures 71 % of the best
  single-break SSR reduction, though it ranks 31st of 115. The exploratory m = 4 partition has
  a step at 2021-12.
- Any cause. No event comparison has been run (Phase C), and estimated dates near policy events
  would not imply causation (ADR 0009 §7.4).
- Anything about long-run level decoupling (H1b).
- Any revision of H1a's frozen inconclusive verdict.

## Files

| File | Content |
|---|---|
| `out/phase_a/selection.csv` | m chosen by BIC and LWZ; T, h, candidates and eligible range per cell |
| `out/phase_a/partitions.csv` | m = 0…5: SSR, BIC, LWZ, dates |
| `out/phase_a/break_table.csv` | Every break with nominal 90/95 % intervals and widths |
| `out/phase_a/regime_table.csv` | Regime coefficients and HAC SE |
| `out/phase_a/daily_sensitivity.csv` | Primary m = 1 on the daily grid |
| `out/phase_a/figures/01–04` | Regime slopes, break map, information criteria, volatility decomposition |
| `out/phase_a/figures/04_rate_volatility.csv` | The §8 table |

Reproduce:

```bash
uv run python research/adr0007/run_breaks.py
uv run python research/adr0007/phase_a_figures.py
```

## Appendix A: post hoc checks (§4, §5), not committed as output

```python
import sys, numpy as np, pandas as pd

sys.path.insert(0, "research/adr0007")
from data import cell

c = cell("primary", "recent", 0.15)
T = len(c.y)


def ssr(X, y):
    return float(((y - X @ np.linalg.lstsq(X, y, rcond=None)[0]) ** 2).sum())


# §4: single-break SSR profile over the same eligible month-start candidates
s0 = ssr(c.xm, c.y)
prof = pd.DataFrame(
    [
        (c.dates.iloc[k].date(), ssr(c.xm[:k], c.y[:k]) + ssr(c.xm[k:], c.y[k:]))
        for k in c.month_grid
        if c.h <= k <= T - c.h
    ],
    columns=["date", "ssr"],
)
prof["rank"] = prof.ssr.rank().astype(int)
print(prof.sort_values("ssr").head(31))
# §5: exact pooled-OLS decomposition of the 2013-21 slope
d = pd.DataFrame({"date": c.dates.to_numpy(), "y": c.y, "x": c.xm[:, 1]})
P = d[d.date <= "2021-12-31"]
g = [P[P.date < "2017-10-02"], P[P.date >= "2017-10-02"]]
sxx = [((s.x - s.x.mean()) ** 2).sum() for s in g]
sxy = [((s.x - s.x.mean()) * (s.y - s.y.mean())).sum() for s in g]
bxx = sum(len(s) * (s.x.mean() - P.x.mean()) ** 2 for s in g)
bxy = sum(len(s) * (s.x.mean() - P.x.mean()) * (s.y.mean() - P.y.mean()) for s in g)
print((sum(sxy) + bxy) / (sum(sxx) + bxx))  # = pooled slope
```
