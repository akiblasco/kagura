# Paper supplement: post hoc descriptive analyses

**Status: post hoc and descriptive.** Every table here was designed after the H1a, H1b, Phase A
and Phase C results were known. None tests a frozen hypothesis, and none revises a frozen verdict:
H1a stays inconclusive and H1b not assessable.

Run:

```bash
uv run python paper/supplement/post_hoc.py
```

The script:

- verifies the frozen-data checksums through `kagura.h1a.load_verified`;
- writes six tables to `out/`;
- asserts that it reproduces the committed Phase A volatility table and the rank-1 break at
  2017-10-02.

Repeated runs are byte-identical.

## Tables

| File | Paper | Content |
|---|---|---|
| `s1_period_components.csv` | Table 2 | Correlation, sd Δd, sd Δs and slope per period, with bootstrap 95 % intervals |
| `s2_log_decomposition.csv` | Table 3 | Δln slope = Δln corr + Δln sd Δs − Δln sd Δd, and Δcorr, per period pair, with intervals |
| `s3_ic_margins.csv` | §5.4; Phase A erratum | BIC and LWZ, m = 1 against m = 0, per observation and × n, for all 30 cells |
| `s4_forced_break_profile.csv` | §5.4 | Single-break SSR profile, primary recent ε = 15 %, over 115 candidates |
| `s5_pooled_decomposition.csv` | §5.4 | Exact pooled-slope decomposition of the H1a reference era |
| `s6_daily_vs_monthly.csv` | Table 4 | Daily, R2 monthly and summed-daily components in the H1a eras; same-day shares |

## Bootstrap design (S1, S2)

- **Data.** Primary daily changes: same-day 2Y differential and USD/JPY, with the ADR 0004
  exclusion rule applied, from 1981-01-01.
- **Periods.** The five Phase A volatility-table periods, plus the H1a reference era 2013-01-01 to
  2021-12-31.
- **Resampling.** A moving-block bootstrap (Künsch 1989). Overlapping blocks of length *l* are
  drawn with replacement, and the (Δd, Δs) pairs are resampled together. The sample is truncated
  to the period's length.
- **Block lengths.** *l* = 21 trading days is the headline and *l* = 63 the sensitivity. Both were
  fixed before the run.
- **Replications and seeds.** B = 2,000 per period and block length. The seed is
  20261124 + *l*, using numpy's `default_rng`.
- **Intervals.** 95 % percentile intervals of the bootstrap distribution.
  - For a difference between periods, the two periods' draws are paired by draw index. The
    periods were resampled independently, so this is equivalent to independent resampling.
  - Draws where a log is undefined (a non-positive bootstrap correlation or slope) are dropped.
    `share_nan` records how many; it is at most 1.4 %, and only in the 1981–2004 period.
- **Reading rule.** A difference is *statistically established* only if its interval excludes
  zero under both block lengths.

**Assumptions:**

1. Within each period the joint process is stationary, with dependence that a block of length
   *l* captures. Volatility clustering longer than *l* is not fully represented.
2. Periods are independent of one another.
3. **Date selection is ignored.** The 2004-04-01 and 2017-10-02 boundaries were *selected from
   the data* by least squares. Intervals for periods bounded by those dates are conditional on
   them, so they do not account for date-selection uncertainty and are too narrow. Only the
   H1a-era comparison has a boundary fixed in advance (2022-01).
4. Percentile intervals can be inaccurate for skewed statistics, such as log ratios of small
   correlations in 1981–2004.

## Exact daily-to-monthly decomposition (S6)

Within an H1a era, demean the daily changes at the era level, giving x_t and y_t, and sum them by
calendar month, giving X_m and Y_m. Then, exactly:

    Σ_m X_m Y_m = Σ_t x_t y_t + Σ_m Σ_{t≠s ∈ m} x_t y_s

- **Same-day share:** Σ x_t y_t / Σ X_m Y_m. The same is computed for each variance.
- **Reading it:**
  - Share = 1: no net within-month cross-day dependence.
  - Share > 1: same-day moves partly reverse within the month.
  - Share < 1: they accumulate.
- **Link to slopes.** The monthly slope of summed changes is approximately the daily slope ×
  (share of var Δd) / (share of cov). It is approximate only because the reported monthly slope
  demeans at the monthly, not the era, level.
- **Comparison.** R2 monthly values use month-end levels from `monthly.csv`, as in ADR 0006.

This is an accounting identity. It locates *where* the daily and monthly results diverge, not
*why*.

## Information criteria (S3)

The criteria are as implemented in `kagura.breaks` (ADR 0007 §5.2), with S the SSR, n the rows,
p* = (m+1)q + m and q = 2:

    BIC = ln(S/n) + p*·ln(n)/n
    LWZ = ln(S/(n − p*)) + p*·0.299·(ln n)^2.1/n

**Scaling.** Values are per observation; × n gives the total-sample scale.

**Check.** An independent recomputation for the primary recent cell (n = 3,052) gives:

| Term | Value |
|---|---:|
| Fit, n·ln(S₁/S₀) | −38.90 |
| BIC penalty, 3·ln n | +24.07 |
| ΔBIC (× n) | **−14.83** |
| LWZ penalty | +71.1 |
| ΔLWZ (× n), with the (n − p*) term | **+35.22** |

Both match `partitions.csv` to machine precision.

These are model-selection preferences under the criteria's assumptions. They are not tests that
a break exists.

## Forced-break profile (S4)

- **Same setup as Phase A:** the same cell (primary, recent, ε = 15 %), candidates (115 eligible
  month-starts), objective (SSR) and criteria.
- **Ranking:** `rank` uses minimum ranks.
- **Results:**
  - 2022-01-05 ranks 31st, and 2021-12-01 ranks 30th.
  - The top 12 candidates lie between 2017-03 and 2018-03.
  - A 2022-01 break captures 70.8 % of the best SSR reduction.
  - No candidate has ΔLWZ < 0.

## Numerical sources in the paper

Every number in the manuscript comes from one of:

- `notebooks/02_h1a_formal.ipynb`, reproduced via `kagura.h1a.analyze`;
- the H1b report and notebooks 03 and 04;
- `research/adr0007/out/phase_a/`;
- `research/adr0007/out/phase_c/`, public outputs only;
- this supplement's `out/` tables.

`paper/DRAFTING_NOTES.md` §2 maps each claim to its file.
