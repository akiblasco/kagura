"""Phase A figures (ADR 0011 §7), drawn only from research/adr0007/out/phase_a/*.csv.

Descriptive: break dates are least-squares partitions; intervals are nominal Bai intervals,
coverage not established (ADR 0012 §3.2). Nothing here is a test.
Run: uv run python research/adr0007/phase_a_figures.py
"""

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from kagura.explore import COLORS, GRID, INK, MUTED, _figure

OUT = Path(__file__).parent / "out" / "phase_a"
FIG = OUT / "figures"
H1A = pd.Timestamp("2022-01-01")  # ADR 0006 pre-specified era boundary, for reference only


def _d(s: str) -> float:
    return float(mdates.date2num(pd.Timestamp(s)))  # type: ignore[no-untyped-call]


def regime_slopes(sel: pd.DataFrame, reg: pd.DataFrame, brk: pd.DataFrame) -> plt.Figure:
    """Static primary spec: slope on the 2Y differential by regime, BIC and LWZ partitions."""
    fig, axes = _figure(2, height=3.0)
    for ax, (sample, eps) in zip(axes, (("full", 0.05), ("recent", 0.15)), strict=True):
        s = sel[(sel.spec == "primary") & (sel["sample"] == sample) & (sel.eps == eps)].iloc[0]
        for rule, color in (("BIC", COLORS[0]), ("LWZ", COLORS[1])):
            m = int(s[f"m_{rule}"])
            r = reg[
                (reg.spec == "primary")
                & (reg["sample"] == sample)
                & (reg.eps == eps)
                & (reg.m == m)
                & (reg.coef == "dd")
            ]
            for i, row in enumerate(r.itertuples()):
                x = [pd.Timestamp(row.start), pd.Timestamp(row.end)]
                lo, hi = row.estimate - 1.96 * row.hac_se, row.estimate + 1.96 * row.hac_se
                ax.fill_between(x, lo, hi, color=color, alpha=0.12, lw=0)
                ax.plot(
                    x,
                    [row.estimate] * 2,
                    color=color,
                    lw=2,
                    label=f"{rule}, m = {m}" if i == 0 else None,
                )
            b = brk[
                (brk.spec == "primary")
                & (brk["sample"] == sample)
                & (brk.eps == eps)
                & (brk.m == m)
            ]
            for row in b.itertuples():
                a, z = row.ci95_nominal.split(" .. ")
                ax.axvspan(pd.Timestamp(a), pd.Timestamp(z), color=GRID, zorder=0)
        ax.axvline(H1A, color=MUTED, lw=0.8, ls=":")
        ax.annotate(
            "2022-01 (H1a era boundary)",
            (_d("2022-01-01"), 0.97),
            xycoords=("data", "axes fraction"),
            fontsize=7,
            color=MUTED,
            ha="right",
            va="top",
            rotation=90,
        )
        ax.axhline(0, color=MUTED, lw=0.8)
        ax.set_title(
            f"{sample.capitalize()} sample (ε = {eps:.0%}): "
            "% USD/JPY per 1 pp Δ 2Y differential, by regime",
            loc="left",
        )
        ax.legend(frameon=False, loc="upper left", fontsize=8)
    axes[-1].set_xlabel(
        "Bands: ±1.96 HAC SE, conditional on the dates. Grey: nominal 95 % Bai interval "
        "of the BIC/LWZ breaks (coverage not established).",
        fontsize=7,
        color=MUTED,
    )
    return fig


def break_map(
    sel: pd.DataFrame, part: pd.DataFrame, brk: pd.DataFrame, elig: pd.DataFrame
) -> plt.Figure:
    """Every cell: eligible range, BIC-selected break dates (filled), LWZ (ring), nominal 95 %
    intervals of the BIC dates. Lag-augmented rows are a different estimand."""
    order = [
        (sp, sa, e)
        for sa in ("full", "recent")
        for sp in ("primary", "V1", "V2", "V3", "lag")
        for e in (0.15, 0.10, 0.05)
    ]
    fig, axes = _figure(1, height=9.5)
    ax = axes[0]
    labels = []
    for y, (sp, sa, e) in enumerate(order):
        s = sel[(sel.spec == sp) & (sel["sample"] == sa) & (sel.eps == e)].iloc[0]
        ax.plot(
            [pd.Timestamp(s.first_eligible), pd.Timestamp(s.last_eligible)],
            [y, y],
            color=GRID,
            lw=5,
            solid_capstyle="round",
            zorder=0,
        )
        mb, ml = int(s.m_BIC), int(s.m_LWZ)
        b = brk[(brk.spec == sp) & (brk["sample"] == sa) & (brk.eps == e) & (brk.m == mb)]
        for row in b.itertuples():
            a, z = row.ci95_nominal.split(" .. ")
            ax.plot([pd.Timestamp(a), pd.Timestamp(z)], [y, y], color=COLORS[0], lw=1.2)
            ax.plot(pd.Timestamp(row.date), y, "o", ms=6, color=COLORS[0], mec="white", mew=1)
        p = part[(part.spec == sp) & (part["sample"] == sa) & (part.eps == e) & (part.m == ml)]
        dates = p.dates.iloc[0] if p.dates.notna().iloc[0] else ""
        for dt in str(dates).split():
            ax.plot(pd.Timestamp(dt), y + 0.28, "o", ms=6, mfc="none", mec=COLORS[1], mew=1.4)
        name = {
            "primary": "static 2Y same-day",
            "V1": "V1 lagged US leg",
            "V2": "V2 10Y",
            "V3": "V3 monthly",
            "lag": "lag-augmented (p=1)",
        }[sp]
        labels.append(f"{sa:6} {name}, ε={e:.0%}  [BIC {mb}, LWZ {ml}]")
    ax.set_yticks(range(len(order)), labels, fontsize=7, family="monospace")
    ax.invert_yaxis()
    ax.axhline(14.5, color=MUTED, lw=0.8)
    ax.axvline(H1A, color=MUTED, lw=0.8, ls=":")
    ax.grid(axis="y", visible=False)
    ax.plot(
        [], [], "o", color=COLORS[0], label="BIC partition date, with nominal 95 % Bai interval"
    )
    ax.plot([], [], "o", mfc="none", mec=COLORS[1], label="LWZ partition date")
    ax.plot([], [], color=GRID, lw=5, label="eligible candidate range")
    ax.legend(frameon=False, loc="lower left", fontsize=7, ncols=3, bbox_to_anchor=(0, 1.0))
    ax.set_title(
        "Where least-squares breaks fall, all 30 Phase A cells (descriptive; dotted: 2022-01)",
        loc="left",
        pad=22,
    )
    return fig


def ic_curves(part: pd.DataFrame) -> plt.Figure:
    """BIC and LWZ by m, relative to m = 0 (lower is preferred), primary spec."""
    fig, axes = _figure(2, 3, height=2.3, sharex=True)
    for i, sa in enumerate(("full", "recent")):
        for j, e in enumerate((0.15, 0.10, 0.05)):
            ax = axes[3 * i + j]
            p = part[
                (part.spec == "primary") & (part["sample"] == sa) & (part.eps == e)
            ].sort_values("m")
            for col, c, lab in (("bic", COLORS[0], "BIC"), ("lwz", COLORS[1], "LWZ")):
                v = p[col].to_numpy() - p[col].iloc[0]
                ax.plot(p.m, v, "-o", color=c, ms=4, label=lab)
                k = int(np.argmin(v))
                ax.plot(p.m.iloc[k], v[k], "o", ms=9, mfc="none", mec=INK, mew=1)
            ax.axhline(0, color=MUTED, lw=0.8)
            ax.set_title(f"{sa}, ε = {e:.0%}", loc="left", fontsize=8)
    axes[0].legend(frameon=False, fontsize=7)
    for ax in axes[3:]:
        ax.set_xlabel("m (breaks)")
    axes[0].set_ylabel("IC − IC(m=0)")
    axes[3].set_ylabel("IC − IC(m=0)")
    return fig


# Estimated primary m = 1 dates (full 2004-04, recent BIC 2017-10) and the H1a boundary 2022-01.
PERIODS = (
    ("1981-01-01", "2004-03-31"),
    ("2004-04-01", "2012-12-31"),
    ("2013-01-01", "2017-09-30"),
    ("2017-10-01", "2021-12-31"),
    ("2022-01-01", "2026-09-11"),
)


def rate_volatility() -> plt.Figure:
    """Does the slope move because the regressor's variability moves, or because co-movement
    does? slope = corr × sd(ΔFX) / sd(Δdiff). Primary spec rows; descriptive, no SEs."""
    from data import cell  # frozen-checksum loader, only needed for this figure

    c = cell("primary", "full", 0.15)
    d = pd.DataFrame({"date": c.dates.to_numpy(), "fx": c.y, "dd": c.xm[:, 1]})
    rows = []
    for a, z in PERIODS:
        s = d[(d.date >= a) & (d.date <= z)]
        r, sx, sd = s.fx.corr(s.dd), s.fx.std(), s.dd.std()
        rows.append((a, z, len(s), sd, sx, r, r * sx / sd))
    t = pd.DataFrame(rows, columns=["start", "end", "rows", "sd_dd", "sd_fx", "corr", "slope"])
    t.round(4).to_csv(FIG / "04_rate_volatility.csv", index=False)
    print(t.round(4).to_string(index=False))
    roll = d.set_index("date").rolling(250, min_periods=200)
    fig, axes = _figure(3, height=2.2, sharex=True)
    series = (
        (roll.dd.std(), "sd of Δ 2Y differential (pp), 250 rows"),
        (roll.fx.std(), "sd of Δ log USD/JPY (%), 250 rows"),
        (roll.fx.corr(d.set_index("date").dd), "corr(ΔFX, Δdiff), 250 rows"),
    )
    for ax, (s, title) in zip(axes, series, strict=True):
        ax.plot(s.index, s.to_numpy(), color=COLORS[0], lw=1.2)
        for x in ("2004-04-01", "2017-10-02"):
            ax.axvline(pd.Timestamp(x), color=INK, lw=0.8, ls="--")
        ax.axvline(H1A, color=MUTED, lw=0.8, ls=":")
        ax.set_title(title, loc="left", fontsize=8)
    axes[-1].set_xlabel(
        "Dashed: primary m = 1 dates (full 2004-04, recent BIC 2017-10). Dotted: 2022-01 "
        "(H1a era boundary). Trailing windows.",
        fontsize=7,
        color=MUTED,
    )
    return fig


def main() -> None:
    FIG.mkdir(exist_ok=True)
    sel = pd.read_csv(OUT / "selection.csv")
    part = pd.read_csv(OUT / "partitions.csv")
    brk = pd.read_csv(OUT / "break_table.csv")
    reg = pd.read_csv(OUT / "regime_table.csv")
    for name, fig in (
        ("01_regime_slopes", regime_slopes(sel, reg, brk)),
        ("02_break_map", break_map(sel, part, brk, sel)),
        ("03_information_criteria", ic_curves(part)),
        ("04_rate_volatility", rate_volatility()),
    ):
        fig.savefig(FIG / f"{name}.png", dpi=200)
        plt.close(fig)
    print("written:", sorted(p.name for p in FIG.iterdir()))


if __name__ == "__main__":
    main()
