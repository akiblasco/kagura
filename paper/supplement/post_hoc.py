"""Post hoc descriptive supplement to the KAGURA paper (not confirmatory; written 2026-11-24).

Everything here was computed after the H1a, Phase A and Phase C results were known. Nothing
revises a frozen result. Outputs go to paper/supplement/out/.

S1 Period slope components (corr, sd, slope) with moving-block bootstrap 95 % intervals.
S2 Log decomposition of slope changes between periods, with bootstrap intervals.
S3 Information-criterion margins on the per-observation scale (as implemented) and x n.
S4 Forced single-break SSR profile, primary recent eps = 15 % (Phase A report §4).
S5 Exact pooled-slope decomposition of the H1a reference era (Phase A report §5).
S6 Daily vs monthly slope components in the H1a eras, and daily changes summed to months.

Run: uv run python paper/supplement/post_hoc.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/adr0007"))
# sys.path import; mypy resolves a different `data` module, hence the narrow ignore
from data import cell  # type: ignore[attr-defined]  # noqa: E402
from kagura import breaks, explore, h1a, models  # noqa: E402

OUT = Path(__file__).parent / "out"
SEED, B = 20261124, 2000
BLOCKS = (21, 63)  # ~1 and ~3 months of trading days; fixed before running
PERIODS = {  # the Phase A volatility-table periods (phase_a_figures.py)
    "1981-2004m3": ("1981-01-01", "2004-03-31"),
    "2004m4-2012": ("2004-04-01", "2012-12-31"),
    "2013-2017m9": ("2013-01-01", "2017-09-30"),
    "2017m10-2021": ("2017-10-01", "2021-12-31"),
    "2022-2026": ("2022-01-01", "2026-09-11"),
    "H1a ref 2013-2021": ("2013-01-01", "2021-12-31"),
}
PAIRS = [
    ("1981-2004m3", "2004m4-2012"),
    ("2004m4-2012", "2013-2017m9"),
    ("2013-2017m9", "2017m10-2021"),
    ("2017m10-2021", "2022-2026"),
    ("2013-2017m9", "2022-2026"),
    ("H1a ref 2013-2021", "2022-2026"),
]


def comps(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """corr, sd_dd, sd_fx, slope (slope = corr * sd_fx / sd_dd exactly)."""
    sx, sy = x.std(ddof=1), y.std(ddof=1)
    r = np.corrcoef(x, y)[0, 1]
    return np.array([r, sx, sy, r * sy / sx])


def mbb(x: np.ndarray, y: np.ndarray, blk: int, rng: np.random.Generator) -> np.ndarray:
    """B moving-block bootstrap draws of comps, resampling (x, y) pairs in blocks of blk."""
    n = len(x)
    k = -(-n // blk)
    out = np.empty((B, 4))
    for b in range(B):
        idx = (rng.integers(0, n - blk + 1, k)[:, None] + np.arange(blk)).ravel()[:n]
        out[b] = comps(x[idx], y[idx])
    return out


def ci(a: np.ndarray) -> tuple[float, float]:
    """Percentile interval; NaN draws (log of a non-positive bootstrap correlation) dropped."""
    lo, hi = np.nanpercentile(a, [2.5, 97.5])
    return float(lo), float(hi)


def s1_s2(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[tuple[object, ...]] = []
    draws = {}
    for blk in BLOCKS:
        rng = np.random.default_rng(SEED + blk)
        for name, (a, b) in PERIODS.items():
            p = d[(d.date >= a) & (d.date <= b)]
            x, y = p.ddiff.to_numpy(), p.dfx.to_numpy()
            est, bs = comps(x, y), mbb(x, y, blk, rng)
            draws[(blk, name)] = bs
            for i, s in enumerate(("corr", "sd_dd", "sd_fx", "slope")):
                rows.append((blk, name, len(p), s, est[i], *ci(bs[:, i])))
    s1 = pd.DataFrame(rows, columns=["block", "period", "rows", "stat", "est", "lo95", "hi95"])
    rows = []
    for blk in BLOCKS:
        for a, b in PAIRS:
            sa, sb = (
                s1[(s1.block == blk) & (s1.period == a)],
                s1[(s1.block == blk) & (s1.period == b)],
            )
            ea: dict[str, float] = dict(zip(sa["stat"].tolist(), sa["est"].tolist(), strict=True))
            eb: dict[str, float] = dict(zip(sb["stat"].tolist(), sb["est"].tolist(), strict=True))
            da, db = draws[(blk, a)], draws[(blk, b)]
            pos_a, pos_b = (
                np.where(da[:, 0] > 0, da[:, 0], np.nan),
                np.where(db[:, 0] > 0, db[:, 0], np.nan),
            )
            terms = {
                "d_corr": (eb["corr"] - ea["corr"], db[:, 0] - da[:, 0]),
                "dln_slope": (
                    np.log(eb["slope"] / ea["slope"]),
                    np.log(
                        np.where(db[:, 3] > 0, db[:, 3], np.nan)
                        / np.where(da[:, 3] > 0, da[:, 3], np.nan)
                    ),
                ),
                "dln_corr": (np.log(eb["corr"] / ea["corr"]), np.log(pos_b / pos_a)),
                "dln_sd_fx": (np.log(eb["sd_fx"] / ea["sd_fx"]), np.log(db[:, 2] / da[:, 2])),
                "minus_dln_sd_dd": (
                    -np.log(eb["sd_dd"] / ea["sd_dd"]),
                    -np.log(db[:, 1] / da[:, 1]),
                ),
            }
            for t, (e, bs) in terms.items():
                nan = float(np.isnan(bs).mean())
                lo, hi = ci(bs)
                rows.append((blk, a, b, t, e, lo, hi, float(np.nanmean(bs <= 0)), nan))
    s2 = pd.DataFrame(
        rows,
        columns=[
            "block",
            "from",
            "to",
            "term",
            "est",
            "lo95",
            "hi95",
            "share_draws_le_0",
            "share_nan",
        ],
    )
    return s1, s2


def s3() -> pd.DataFrame:
    p = pd.read_csv(ROOT / "research/adr0007/out/phase_a/partitions.csv")
    s = pd.read_csv(ROOT / "research/adr0007/out/phase_a/selection.csv")
    ic = {(r["spec"], r["sample"], r["eps"], r["p"], r["m"]): r for r in p.to_dict("records")}
    rows: list[tuple[object, ...]] = []
    for sel in s.to_dict("records"):
        k = (sel["spec"], sel["sample"], sel["eps"], sel["p"])
        n = int(sel["T"])
        for crit in ("bic", "lwz"):
            d1 = float(ic[(*k, 1)][crit]) - float(ic[(*k, 0)][crit])
            rows.append((*k, n, crit, int(sel[f"m_{crit.upper()}"]), d1, d1 * n))
    cols = ["spec", "sample", "eps", "p", "n", "criterion", "m_selected", "d_m1_vs_m0_per_obs"]
    return pd.DataFrame(rows, columns=[*cols, "d_x_n"])


def ssr(xmat: np.ndarray, y: np.ndarray) -> float:
    return float(((y - xmat @ np.linalg.lstsq(xmat, y, rcond=None)[0]) ** 2).sum())


def s4() -> pd.DataFrame:
    c = cell("primary", "recent", 0.15)
    n = len(c.y)
    s0 = ssr(c.xm, c.y)
    prof = pd.DataFrame(
        [
            (c.dates.iloc[k].date(), ssr(c.xm[:k], c.y[:k]) + ssr(c.xm[k:], c.y[k:]))
            for k in c.month_grid
            if c.h <= k <= n - c.h
        ],
        columns=["date", "ssr"],
    )
    prof["rank"] = prof.ssr.rank(method="min").astype(int)
    best = prof.ssr.min()
    prof["share_of_best_reduction"] = (s0 - prof.ssr) / (s0 - best)
    q = c.xm.shape[1]  # the implemented criteria (kagura.breaks.bic / lwz, ADR 0007 §5.2)
    prof["dbic_per_obs"] = [breaks.bic(s, n, 1, q) - breaks.bic(s0, n, 0, q) for s in prof.ssr]
    prof["dlwz_per_obs"] = [breaks.lwz(s, n, 1, q) - breaks.lwz(s0, n, 0, q) for s in prof.ssr]
    prof.attrs["n"], prof.attrs["ssr0"] = n, s0
    return prof.sort_values("rank")


def s5() -> pd.DataFrame:
    c = cell("primary", "recent", 0.15)
    d = pd.DataFrame({"date": c.dates.to_numpy(), "y": c.y, "x": c.xm[:, 1]})
    pre = d[d.date <= "2021-12-31"]
    g = [pre[pre.date < "2017-10-02"], pre[pre.date >= "2017-10-02"]]
    sxx = [((s.x - s.x.mean()) ** 2).sum() for s in g]
    sxy = [((s.x - s.x.mean()) * (s.y - s.y.mean())).sum() for s in g]
    bxx = sum(len(s) * (s.x.mean() - pre.x.mean()) ** 2 for s in g)
    bxy = sum(len(s) * (s.x.mean() - pre.x.mean()) * (s.y.mean() - pre.y.mean()) for s in g)
    den = sum(sxx) + bxx
    rows = [
        ("2013-01..2017-09 within", len(g[0]), sxy[0] / sxx[0], sxx[0] / den),
        ("2017-10..2021-12 within", len(g[1]), sxy[1] / sxx[1], sxx[1] / den),
        ("between-group", None, bxy / bxx, bxx / den),
    ]
    t = pd.DataFrame(rows, columns=["term", "rows", "slope", "weight"])
    t["contribution"] = t.slope * t.weight
    pooled = np.polyfit(pre.x, pre.y, 1)[0]
    t.loc[len(t)] = ["pooled (OLS)", len(pre), pooled, 1.0, pooled]
    return t


def s6(v: h1a.VerifiedData, daily: pd.DataFrame) -> pd.DataFrame:
    """Daily vs monthly slope components in the H1a eras.

    For daily changes summed by month, the cross-product of monthly sums splits exactly into
    same-day pairs and pairs on different days of the same month (daily data demeaned within
    the era): sum_m X_m Y_m = sum_t x_t y_t + sum_m sum_{t != s in m} x_t y_s. The share from
    same-day pairs is reported for the covariance and for each variance.
    """
    eras = {
        "ref 2013-2021": ("2013-01-01", "2021-12-31"),
        "new 2022-": ("2022-01-01", "2026-09-30"),
    }
    mon = models.monthly_changes(v.monthly, "2y").dropna()
    dd = daily.dropna()
    rows: list[tuple[object, ...]] = []
    for era, (a, b) in eras.items():
        e = dd[(dd.date >= a) & (dd.date <= b)].copy()
        e["xd"], e["yd"] = e.ddiff - e.ddiff.mean(), e.dfx - e.dfx.mean()
        e["month"] = e.date.dt.to_period("M")
        agg = e.groupby("month")[["dfx", "ddiff", "xd", "yd"]].sum()
        same = {
            "cov": (e.xd * e.yd).sum() / (agg.xd * agg.yd).sum(),
            "var_dd": (e.xd**2).sum() / (agg.xd**2).sum(),
            "var_fx": (e.yd**2).sum() / (agg.yd**2).sum(),
        }
        m = mon[(mon.date >= a) & (mon.date <= b)]
        for name, f, sh in (
            ("daily", e, None),
            ("monthly (R2, month-end levels)", m, None),
            ("daily changes summed by month", agg, same),
        ):
            r, sx, sy, sl = comps(f.ddiff.to_numpy(), f.dfx.to_numpy())
            s = sh or {}
            rows.append(
                (era, name, len(f), r, sx, sy, sl, s.get("cov"), s.get("var_dd"), s.get("var_fx"))
            )
    cols = ["era", "series", "rows", "corr", "sd_dd", "sd_fx", "slope"]
    return pd.DataFrame(
        rows,
        columns=[*cols, "same_day_share_cov", "same_day_share_var_dd", "same_day_share_var_fx"],
    )


def main() -> None:
    OUT.mkdir(exist_ok=True)
    v = h1a.load_verified()  # verifies the frozen checksums
    daily = explore.changes(v.daily, "2y", "same-day")[["date", "dfx", "ddiff"]]
    d = daily.dropna()
    d = d[d.date >= "1981-01-01"]
    s1, s2 = s1_s2(d)
    prof = s4()
    tables = {
        "s1_period_components.csv": s1,
        "s2_log_decomposition.csv": s2,
        "s3_ic_margins.csv": s3(),
        "s4_forced_break_profile.csv": prof,
        "s5_pooled_decomposition.csv": s5(),
        "s6_daily_vs_monthly.csv": s6(v, daily),
    }
    for f, t in tables.items():
        t.to_csv(OUT / f, index=False, float_format="%.6g")
    vol = pd.read_csv(ROOT / "research/adr0007/out/phase_a/figures/04_rate_volatility.csv")
    chk = s1[(s1.block == 21) & (s1.stat == "slope") & ~s1.period.str.startswith("H1a")]
    assert np.allclose(chk.est.to_numpy(), vol.slope.to_numpy(), atol=1e-4), "Phase A mismatch"
    assert int(prof.loc[prof.date.astype(str) == "2017-10-02", "rank"].iloc[0]) == 1
    print("written:", ", ".join(tables), "| n =", prof.attrs["n"])


if __name__ == "__main__":
    main()
