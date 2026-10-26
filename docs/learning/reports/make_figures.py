"""Learning-companion figures and chart data (no re-estimation).

Static figures are read from committed notebook outputs. Interactive-chart data are derived
from the frozen data vintage via kagura.longrun.load_monthly (checksum-verified) and written
to docs/learning/data/, which is gitignored: KAGURA does not redistribute source data.

Run: uv run python docs/learning/reports/make_figures.py
"""

import json
import re
import shutil
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).parent / "figures"
INK, MUTED, GRID, ACCENT = "#1f1f1f", "#6b6b6b", "#e6e6e6", "#2a6fdb"
plt.rcParams.update({"font.size": 12, "axes.titlesize": 14, "axes.labelsize": 12})


def notebook_text(path: Path) -> str:
    cells = json.loads(path.read_text())["cells"]
    return "\n".join(
        "".join(o.get("text", "")) or "".join(o.get("data", {}).get("text/plain", ""))
        for c in cells
        if c["cell_type"] == "code"
        for o in c.get("outputs", [])
    )


def h1a_era_betas() -> list[tuple[str, float, float]]:
    """(era, beta, HAC se) from notebook 02's primary-regression table."""
    text = notebook_text(ROOT / "notebooks/02_h1a_formal.ipynb")
    rows = re.findall(r"^beta:(\S+)\s+(-?[\d.]+)\s+([\d.]+)$", text, re.M)
    seen: dict[str, tuple[float, float]] = {}
    for era, b, se in rows:
        seen.setdefault(era, (float(b), float(se)))
    assert len(seen) == 5, seen
    return [(e, b, se) for e, (b, se) in seen.items()]


def fig_h1a_era_betas() -> None:
    eras = h1a_era_betas()
    fig, ax = plt.subplots(figsize=(9, 5), dpi=200)
    for i, (_, b, se) in enumerate(eras):
        ax.plot([i, i], [b - 1.959964 * se, b + 1.959964 * se], color=ACCENT, lw=2)
        ax.plot(i, b, "o", ms=8, color=ACCENT, mec="white", mew=2)
        ax.annotate(
            f"{b:.2f}",
            (i, b),
            xytext=(10, 0),
            textcoords="offset points",
            va="center",
            color=INK,
            fontsize=9,
        )
    ref = {e: b for e, b, _ in eras}["2013–2021"]
    ax.axhline(2 / 3 * ref, color=MUTED, ls="--", lw=1)
    ax.text(4.3, 2 / 3 * ref + 0.15, "⅔ × β(2013–21)", color=MUTED, fontsize=10, va="bottom")
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_xticks(range(len(eras)), [e for e, _, _ in eras])
    ax.set_xlim(-0.5, 5.4)
    ax.set_ylabel("% USD/JPY per 1 pp change\nin 2Y US–JGB differential", color=INK)
    ax.set_title(
        "H1a: daily FX–rate-differential slope by era (95% HAC intervals)",
        loc="left",
        color=INK,
        fontsize=11,
    )
    ax.grid(axis="y", color=GRID)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(
        0.01,
        0.01,
        "Source: notebooks/02_h1a_formal.ipynb (frozen vintage 2026-09-15, "
        "ADR 0006). Daily, same-day timing, 1981-01 to 2026-09-11.",
        fontsize=9,
        color=MUTED,
    )
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUT / "h1a_era_betas.png")


def chart_data() -> None:
    """Monthly s, x, q, d2 (ADR 0008 §2 definitions) plus ADR 0004 events and eras."""
    from kagura.explore import ERAS, EVENTS
    from kagura.longrun import load_monthly

    df = load_monthly()
    data = {
        "source": "KAGURA frozen vintage 2026-09-15 (ADR 0006 §9.2) + CPI files (ADR 0008); "
        "kagura.longrun.load_monthly",
        "month": [str(p) for p in df.index],
        **{
            c: [None if v != v else round(float(v), 4) for v in df[c]]
            for c in ("s", "x", "q", "d2")
        },
        "events": [{"date": d, "label": lab} for d, lab in EVENTS.items()],
        "eras": [{"label": k, "start": a, "end": b} for k, (a, b) in ERAS.items()],
    }
    out = Path(__file__).parents[1] / "data"
    out.mkdir(exist_ok=True)
    (out / "kagura_monthly.json").write_text(json.dumps(data, ensure_ascii=False))


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    fig_h1a_era_betas()
    chart_data()
    # Existing notebook figures shown in the reports, copied so the site and GitHub render them
    for name in (
        "01_levels.png",
        "04_acf.png",
        "h1a_rolling_beta.png",
        "h1b_01_nominal_real.png",
        "h1b_02_stability.png",
    ):
        shutil.copy2(ROOT / "reports/figures" / name, OUT / name)
