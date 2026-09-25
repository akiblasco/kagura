"""Exploratory diagnostics for H1: computations and plots used by notebooks/01_exploration.

Every constant here is frozen by docs/decisions/0004-h1-exploratory-specification.md.
Do not tune them after seeing results; add a new, labelled specification instead.
"""

from __future__ import annotations

import warnings

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from statsmodels.tools.sm_exceptions import InterpolationWarning
from statsmodels.tsa.stattools import acf, adfuller, kpss

from kagura import DATA_PROCESSED, FIGURES, SAMPLE_START

# --- frozen specification (ADR 0004) ---------------------------------------------------------

WINDOWS = {"1y": 250, "3y": 750}  # rows of the USD/JPY calendar
MIN_SHARE = 0.8  # a window reports only if this share of its rows survives exclusion
MATURITIES = ("2y", "10y")  # 2y primary, 10y robustness
TIMINGS = ("same-day", "lagged")

EVENTS = {
    "1985-09-22": "Plaza Accord",
    "1987-02-22": "Louvre Accord",
    "1999-02-12": "BOJ ZIRP",
    "2001-03-19": "BOJ QE",
    "2006-03-09": "BOJ exits QE",
    "2008-09-15": "Lehman",
    "2013-04-04": "BOJ QQE",
    "2016-01-29": "BOJ negative rate",
    "2016-09-21": "BOJ YCC",
    "2022-03-16": "Fed hikes begin",
    "2022-09-22": "MOF intervention",
    "2022-12-20": "YCC band widened",
    "2024-03-19": "BOJ ends NIRP/YCC",
}

ERAS = {
    "1981–1989": ("1981-01-01", "1989-12-31"),
    "1990–1998": ("1990-01-01", "1998-12-31"),
    "1999–2012": ("1999-01-01", "2012-12-31"),
    "2013–2021": ("2013-01-01", "2021-12-31"),
    "2022–": ("2022-01-01", "2100-01-01"),
}

# Changes of these series are log changes in %; everything else is a difference in its units.
LOG_SERIES = {"usdjpy", "brent", "vix"}
DAILY_SERIES = ["usdjpy", "us_2y", "us_10y", "fed_funds", "jgb_2y", "jgb_10y", "brent", "vix"]

# Reference palette (dataviz skill): categorical slots 1-3, muted ink for context.
COLORS = ["#2a78d6", "#eb6834", "#1baf7a"]
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#8a8984", "#e6e5e0", "#fcfcfb"


# --- data ------------------------------------------------------------------------------------


def load_daily() -> pd.DataFrame:
    return pd.read_csv(DATA_PROCESSED / "daily.csv", parse_dates=["date"])


def load_monthly() -> pd.DataFrame:
    cols = ["date", "us_cpi_month", "jp_cpi_month", "jp_call_rate_month"]
    return pd.read_csv(DATA_PROCESSED / "monthly.csv", parse_dates=cols)


def era_of(dates: pd.Series) -> pd.Series:
    out = pd.Series(pd.NA, index=dates.index, dtype="string")
    for name, (start, end) in ERAS.items():
        out[dates.between(start, end)] = name
    return out


# --- H1 changes and rolling correlation --------------------------------------------------------


def changes(daily: pd.DataFrame, maturity: str, timing: str) -> pd.DataFrame:
    """Daily FX change (%, log) and differential change (pp), from SAMPLE_START.

    Rows failing the ADR 0004 exclusion rule have both changes set to NaN, so any
    later statistic sees only changes between consecutive live observations."""
    us, jgb = daily[f"us_{maturity}"], daily[f"jgb_{maturity}"]
    if timing == "same-day":
        diff = us - jgb
        drop = daily[f"diff_{maturity}_change_carried"]
    elif timing == "lagged":
        diff = us.shift(1) - jgb
        us_flag = daily[f"us_{maturity}_change_carried"].shift(1, fill_value=False)
        drop = daily[f"jgb_{maturity}_change_carried"] | us_flag
    else:
        raise ValueError(timing)
    out = pd.DataFrame(
        {
            "date": daily["date"],
            "dfx": 100 * np.log(daily["usdjpy"]).diff(),
            "ddiff": diff.diff(),
            "excluded": drop.astype(bool),
        }
    )
    out.loc[out["excluded"] | out["ddiff"].isna(), ["dfx", "ddiff"]] = np.nan
    return out[out["date"] >= SAMPLE_START].reset_index(drop=True)


def rolling_corr(x: pd.Series, y: pd.Series, window: int) -> pd.DataFrame:
    """Trailing Pearson correlation over ``window`` rows, using rows where both are present.

    Reported only when at least MIN_SHARE of the window survives. The band is a pointwise
    95% Fisher-z interval that assumes independent rows, so it is too narrow for overlapping
    windows of autocorrelated data: descriptive only."""
    ok = x.notna() & y.notna()
    n = ok.astype(float).rolling(window).sum()
    r = x.where(ok).rolling(window, min_periods=int(MIN_SHARE * window)).corr(y.where(ok))
    half = 1.96 / np.sqrt((n - 3).where(r.notna()))
    z = np.arctanh(r.clip(-0.999999, 0.999999))
    return pd.DataFrame({"r": r, "lo": np.tanh(z - half), "hi": np.tanh(z + half), "n": n})


def h1_rolling(daily: pd.DataFrame) -> pd.DataFrame:
    """All 8 frozen series: maturity x timing x window, in one long table."""
    parts = []
    for maturity in MATURITIES:
        for timing in TIMINGS:
            ch = changes(daily, maturity, timing)
            for label, window in WINDOWS.items():
                rc = rolling_corr(ch["dfx"], ch["ddiff"], window)
                parts.append(
                    rc.assign(date=ch["date"], maturity=maturity, timing=timing, window=label)
                )
    return pd.concat(parts, ignore_index=True).dropna(subset=["r"])


def exclusion_counts(daily: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for maturity in MATURITIES:
        for timing in TIMINGS:
            ch = changes(daily, maturity, timing)
            live = ch["ddiff"].notna() | ch["excluded"]  # rows where the differential exists
            rows.append(
                {
                    "maturity": maturity,
                    "timing": timing,
                    "rows_with_differential": int(live.sum()),
                    "excluded": int(ch["excluded"][live].sum()),
                    "used": int(ch["ddiff"].notna().sum()),
                }
            )
    return pd.DataFrame(rows)


# --- descriptive tables ------------------------------------------------------------------------


def coverage(daily: pd.DataFrame) -> pd.DataFrame:
    """First/last date, count, and share carried by decade for each daily series."""
    decade = (daily["date"].dt.year // 10 * 10).astype(str) + "s"
    rows = {}
    for name in DAILY_SERIES:
        present = daily[name].notna()
        row: dict[str, object] = {
            "first": daily.loc[present, "date"].min().date(),
            "last": daily.loc[present, "date"].max().date(),
            "n": int(present.sum()),
        }
        if name != "usdjpy":
            carried = daily[f"{name}_carried"][present].groupby(decade[present]).mean()
            row.update({str(d): f"{v:.1%}" for d, v in carried.items()})
        rows[name] = row
    return pd.DataFrame(rows).T.fillna("")


def one_row_change(daily: pd.DataFrame, name: str) -> pd.Series:
    v = daily[name]
    return 100 * np.log(v).diff() if name in LOG_SERIES else v.diff()


def largest_moves(daily: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """The n largest absolute one-row changes per series, flagged for investigation."""
    gap = daily["date"].diff().dt.days
    parts = []
    for name in [*DAILY_SERIES, "diff_2y", "diff_10y"]:
        ch = one_row_change(daily, name)
        top = ch.abs().nlargest(n).index
        no_flag = pd.Series(False, index=daily.index)  # USD/JPY is never carried
        flag = daily.get(f"{name}_change_carried", no_flag)
        parts.append(
            pd.DataFrame(
                {
                    "series": name,
                    "date": daily.loc[top, "date"].dt.date,
                    "prev": daily[name].shift(1)[top],
                    "value": daily.loc[top, name],
                    "change": ch[top].round(3),
                    "unit": "%" if name in LOG_SERIES else "pp",
                    "gap_days": gap[top].astype(int),
                    "change_carried": flag[top],
                }
            )
        )
    return pd.concat(parts, ignore_index=True)


def era_stats(dates: pd.Series, values: pd.Series) -> pd.DataFrame:
    """Count, mean, sd, skew, excess kurtosis and largest absolute value, per era."""
    g = values.groupby(era_of(dates))
    out = pd.DataFrame(
        {
            "n": g.count(),
            "mean": g.mean(),
            "sd": g.std(),
            "skew": g.skew(),
            "ex_kurt": g.apply(lambda s: s.kurt()),
            "max_abs": g.apply(lambda s: s.abs().max()),
        }
    )
    return out.reindex(list(ERAS)).round(3)


def stationarity(series: dict[str, pd.Series]) -> pd.DataFrame:
    """ADF (unit-root null) and KPSS (stationarity null) on each series' level and change.

    KPSS p-values come from a lookup table bounded to [0.01, 0.10]; values at a bound
    are shown as '<0.01' or '>0.10'."""
    rows = []
    for name, s in series.items():
        for form, x in (("level", s.dropna()), ("change", s.diff().dropna())):
            adf = adfuller(x, regression="c", autolag="AIC", result_object=True)
            # The bound is reported explicitly below, so the lookup-table warning adds nothing.
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", InterpolationWarning)
                kp = kpss(x, regression="c", nlags="auto", result_object=True)
            adf_stat, adf_p, kpss_stat, kpss_p = adf.statistic, adf.pvalue, kp.statistic, kp.pvalue
            bound = "<0.01" if kpss_p <= 0.01 else ">0.10" if kpss_p >= 0.1 else f"{kpss_p:.3f}"
            rows.append(
                {
                    "series": name,
                    "form": form,
                    "n": len(x),
                    "adf_stat": round(adf_stat, 2),
                    "adf_p": round(adf_p, 3),
                    "kpss_stat": round(kpss_stat, 2),
                    "kpss_p": bound,
                }
            )
    return pd.DataFrame(rows)


def yoy(long: pd.DataFrame, name: str) -> pd.Series:
    """Year-on-year % change of a monthly series, indexed by reference month."""
    s = long.loc[long["series"] == name].set_index("date")["value"].asfreq("MS")
    return (100 * (s / s.shift(12) - 1)).rename(name)


# --- plots -------------------------------------------------------------------------------------


def _figure(
    nrows: int, ncols: int = 1, height: float = 2.4, sharex: bool = False, sharey: bool = False
) -> tuple[Figure, list[Axes]]:
    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.edgecolor": MUTED,
            "axes.labelcolor": INK,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "axes.facecolor": SURFACE,
            "figure.facecolor": SURFACE,
            "lines.linewidth": 1.2,
        }
    )
    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(10, height * nrows),
        squeeze=False,
        layout="constrained",
        sharex=sharex,
        sharey=sharey,
    )
    return fig, list(axes.flat)


def _events(ax: Axes, label: bool = False) -> None:
    for i, (date, name) in enumerate(EVENTS.items()):
        # matplotlib.dates ships without type hints; axvline wants the numeric date.
        x = float(mdates.date2num(pd.Timestamp(date)))  # type: ignore[no-untyped-call]
        ax.axvline(x, color=MUTED, lw=0.6, ls=":", zorder=0)
        if label:
            ax.annotate(
                name,
                (x, 1 if i % 2 == 0 else 0.55),  # alternate heights: 2022 events are close
                xycoords=("data", "axes fraction"),
                rotation=90,
                fontsize=6.5,
                color=MUTED,
                va="top",
                ha="right",
            )


def _log_yaxis(ax: Axes) -> None:
    ax.set_yscale("log")
    ax.set_yticks([80, 100, 150, 200, 300], labels=["80", "100", "150", "200", "300"])
    ax.minorticks_off()


def _sample(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["date"] >= SAMPLE_START]


def plot_levels(daily: pd.DataFrame) -> Figure:
    d = _sample(daily)
    fig, axes = _figure(3, sharex=True)
    specs = [
        ("usdjpy", "USD/JPY (log scale)"),
        ("diff_2y", "2Y differential, US − JGB (pp)"),
        ("diff_10y", "10Y differential, US − JGB (pp)"),
    ]
    for i, (ax, (col, title)) in enumerate(zip(axes, specs, strict=True)):
        ax.plot(d["date"], d[col], color=COLORS[0])
        ax.set_title(title, loc="left", fontsize=9)
        _events(ax, label=i == 0)
    _log_yaxis(axes[0])
    return fig


def plot_legs(daily: pd.DataFrame) -> Figure:
    d = _sample(daily)
    fig, axes = _figure(2, sharex=True)
    for ax, m in zip(axes, MATURITIES, strict=True):
        ax.plot(d["date"], d[f"us_{m}"], color=COLORS[0], label=f"US {m.upper()}")
        ax.plot(d["date"], d[f"jgb_{m}"], color=COLORS[1], label=f"JGB {m.upper()}")
        ax.set_title(f"{m.upper()} yields, the two legs of the differential (%)", loc="left")
        ax.legend(frameon=False, loc="upper right")
        _events(ax)
    return fig


def plot_scatter_by_era(monthly: pd.DataFrame) -> Figure:
    m = _sample(monthly).dropna(subset=["diff_2y"])
    era = era_of(m["date"])
    fig, axes = _figure(1, len(ERAS), height=2.8, sharex=True, sharey=True)
    for ax, name in zip(axes, ERAS, strict=True):
        ax.scatter(m["diff_2y"], m["usdjpy"], s=6, color=GRID, lw=0)
        sel = m[era == name]
        ax.scatter(sel["diff_2y"], sel["usdjpy"], s=9, color=COLORS[0], lw=0)
        ax.set_title(name, fontsize=9)
        ax.set_xlabel("2Y diff (pp)")
    _log_yaxis(axes[0])
    axes[0].set_ylabel("USD/JPY, month-end (log)")
    return fig


def plot_acf(series: dict[str, pd.Series], nlags: int = 36) -> Figure:
    fig, axes = _figure(len(series), 2, height=1.8, sharex=True, sharey=True)
    for i, (name, s) in enumerate(series.items()):
        for j, (form, x) in enumerate((("level", s.dropna()), ("change", s.diff().dropna()))):
            ax = axes[2 * i + j]
            ax.bar(range(1, nlags + 1), acf(x, nlags=nlags)[1:], color=COLORS[0], width=0.7)
            ax.axhspan(-1.96 / np.sqrt(len(x)), 1.96 / np.sqrt(len(x)), color=GRID, zorder=0)
            ax.set_title(f"{name}, {form}", loc="left", fontsize=9)
    axes[-1].set_xlabel("lag (months)")
    axes[-2].set_xlabel("lag (months)")
    return fig


def plot_changes(daily: pd.DataFrame) -> Figure:
    ch = changes(daily, "2y", "same-day")
    fig, axes = _figure(2, sharex=True)
    axes[0].plot(ch["date"], ch["dfx"], color=COLORS[0], lw=0.5)
    axes[0].set_title("Daily USD/JPY change, % (log)", loc="left")
    axes[1].plot(ch["date"], ch["ddiff"], color=COLORS[0], lw=0.5)
    axes[1].set_title("Daily 2Y differential change, pp (excluded rows removed)", loc="left")
    for ax in axes:
        _events(ax)
    return fig


def plot_inflation(us: pd.Series, jp: pd.Series) -> Figure:
    fig, axes = _figure(1, height=3.2)
    ax = axes[0]
    for s, label, c in ((us, "US CPI", COLORS[0]), (jp, "Japan CPI", COLORS[1])):
        s = s[s.index >= SAMPLE_START]
        ax.plot(s.index, s, color=c, label=label)
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.axhline(2, color=MUTED, lw=0.6, ls="--")
    ax.set_title("Year-on-year CPI inflation, % (by reference month)", loc="left")
    ax.legend(frameon=False, loc="upper right")
    _events(ax)
    return fig


def plot_rolling(h1: pd.DataFrame) -> Figure:
    fig, axes = _figure(2, 2, height=2.8, sharex=True, sharey=True)
    for i, maturity in enumerate(MATURITIES):
        for j, window in enumerate(WINDOWS):
            ax = axes[2 * i + j]
            for timing, c in zip(TIMINGS, COLORS, strict=False):
                d = h1[(h1.maturity == maturity) & (h1.window == window) & (h1.timing == timing)]
                ax.fill_between(d["date"], d["lo"], d["hi"], color=c, alpha=0.15, lw=0)
                ax.plot(d["date"], d["r"], color=c, label=timing)
            ax.axhline(0, color=MUTED, lw=0.8)
            role = "primary" if maturity == "2y" else "robustness"
            ax.set_title(f"{maturity.upper()} diff ({role}), {window} window", loc="left")
            _events(ax)
    fig.legend(*axes[0].get_legend_handles_labels(), frameon=False, loc="outside upper right")
    axes[0].set_ylabel("corr(ΔlogFX, Δdiff)")
    axes[2].set_ylabel("corr(ΔlogFX, Δdiff)")
    return fig


def save(fig: Figure, name: str) -> None:
    fig.savefig(FIGURES / f"{name}.png", dpi=150)
