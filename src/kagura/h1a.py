"""H1a analysis orchestration: frozen-data verification and assembly of the ADR 0006 specs.

No econometrics is computed here; every estimate comes from ``kagura.models`` (and the
change tables from ``kagura.explore``). This module only

1. refuses to run unless the data on disk are byte-for-byte the frozen vintage
   (docs/decisions/0006-h1-formal-testing-protocol.md §9.2), and
2. builds the primary specification and the R1-R3 robustness variants exactly as §4 and
   §9.1 define them, then hands them to the validated functions.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from kagura import ROOT, SAMPLE_START
from kagura.explore import changes, exclusion_counts
from kagura.models import (
    DAILY_END,
    MONTHLY_END,
    NEW,
    REF,
    EraFit,
    H1aResult,
    LegTest,
    Spec,
    Wald,
    era_equality,
    era_regression,
    h1a_test,
    leg_changes,
    leg_spread,
    monthly_changes,
    opposite_legs,
    robustness_label,
    two_leg_regression,
)

# --- frozen data vintage (ADR 0006 §9.2) ------------------------------------------------------

# Paths relative to data/, exactly as in the ADR 0006 §9.2 table.

FROZEN_SHA256 = {
    "processed/daily.csv": "edfc95cf676d3647b6af3667b3b34fc74b4b6e692d750bf6ab8008de9105cd99",
    "processed/monthly.csv": "3f19c005d8db1ab1963488b2af748dcb6f956fe3a6a6cf6f4acdafda92a56215",
    "raw/manifest.json": "c0f5676e888751690cf8a5ad86df63c8727b5a02f63302b33fb535e315bee51c",
    "raw/usdjpy.csv": "0ea1de1993e69827ccfdddc390af8f8f5abf15c566f4c4cd5a6072495b773965",
    "raw/us_2y.csv": "1289774410381729569844068b657a7cc11a56a699669509bf6ed26a0db572a4",
    "raw/us_10y.csv": "94c1e5b98460d7de645be32f3211853c3d749724ecb12cac33bc84623ea759b4",
    "raw/jgb.csv": "997a8f95dc20c884d506c627ac075b1e93a357410094058ac19f3effead2e353",
    "raw/jgb_current.csv": "8da8cc83668bf280f1849ce2e6fab752881fc771b87d4691887bdb85e2f9f519",
}

# Columns the H1a analysis reads. Extra columns are allowed.
DAILY_COLUMNS = [
    "date",
    "usdjpy",
    *(f"{leg}_{m}" for leg in ("us", "jgb") for m in ("2y", "10y")),
    *(f"diff_{m}" for m in ("2y", "10y")),
    *(f"{s}_change_carried" for s in ("us_2y", "us_10y", "jgb_2y", "jgb_10y")),
    "diff_2y_change_carried",
    "diff_10y_change_carried",
]
MONTHLY_COLUMNS = ["date", "usdjpy", "diff_2y", "diff_10y"]


class IntegrityError(RuntimeError):
    """The data on disk are not the frozen ADR 0006 vintage, or not in the expected shape."""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify_checksums(root: Path = ROOT, expected: dict[str, str] = FROZEN_SHA256) -> None:
    """Raise IntegrityError listing every missing file and every checksum mismatch."""
    problems = []
    for rel, want in expected.items():
        path = root / "data" / rel
        if not path.is_file():
            problems.append(f"missing: {rel}")
        elif (got := sha256(path)) != want:
            problems.append(f"checksum mismatch: {rel}\n    expected {want}\n    found    {got}")
    if problems:
        raise IntegrityError(
            "Data are not the frozen ADR 0006 §9.2 vintage; refusing to run.\n  "
            + "\n  ".join(problems)
        )


def validate_daily(daily: pd.DataFrame) -> None:
    """Schema and sample boundaries of daily.csv: required columns, strictly increasing
    dates, a USD/JPY row on every calendar row, coverage from before SAMPLE_START, and a
    last observation exactly at DAILY_END."""
    _require_columns(daily, DAILY_COLUMNS, "daily.csv")
    dates = daily["date"]
    if not dates.is_monotonic_increasing or dates.duplicated().any():
        raise IntegrityError("daily.csv: dates are not strictly increasing")
    if daily["usdjpy"].isna().any():
        raise IntegrityError("daily.csv: USD/JPY defines the calendar and must have no gaps")
    if dates.iloc[0] > pd.Timestamp(SAMPLE_START):
        raise IntegrityError(f"daily.csv starts {dates.iloc[0]:%Y-%m-%d}, after {SAMPLE_START}")
    if dates.iloc[-1] != pd.Timestamp(DAILY_END):
        raise IntegrityError(f"daily.csv ends {dates.iloc[-1]:%Y-%m-%d}, expected {DAILY_END}")


def validate_monthly(monthly: pd.DataFrame) -> None:
    """Schema and boundaries of monthly.csv: one row per calendar month with no gaps, a
    December-1980 base row for the January-1981 change, and a last month equal to
    MONTHLY_END's month."""
    _require_columns(monthly, MONTHLY_COLUMNS, "monthly.csv")
    months = monthly["date"].dt.to_period("M")
    steps = months.diff().dropna().map(lambda o: o.n)
    if months.duplicated().any() or (steps != 1).any():
        raise IntegrityError("monthly.csv: not exactly one row per calendar month")
    base = pd.Period(SAMPLE_START, "M") - 1
    if months.iloc[0] > base:
        raise IntegrityError(f"monthly.csv starts {months.iloc[0]}, after the {base} base month")
    last = pd.Period(MONTHLY_END, "M")
    if months.iloc[-1] != last:
        raise IntegrityError(f"monthly.csv ends {months.iloc[-1]}, expected {last}")


def _require_columns(df: pd.DataFrame, columns: list[str], name: str) -> None:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise IntegrityError(f"{name}: missing columns {missing}")


@dataclass(frozen=True)
class VerifiedData:
    """daily.csv and monthly.csv as returned by ``load_verified``, i.e. only after the
    checksum, schema and boundary checks passed. ``analyze`` accepts nothing else, so the
    estimation cannot be reached from unverified files. (Tests build it from synthetic
    frames directly; analysis code must not.)"""

    daily: pd.DataFrame
    monthly: pd.DataFrame


def load_verified(root: Path = ROOT, expected: dict[str, str] = FROZEN_SHA256) -> VerifiedData:
    """Verify checksums, then load and validate daily.csv and monthly.csv. Raises
    IntegrityError before anything is returned if any check fails."""
    verify_checksums(root, expected)
    processed = root / "data" / "processed"
    daily = pd.read_csv(processed / "daily.csv", parse_dates=["date"])
    monthly = pd.read_csv(processed / "monthly.csv", parse_dates=["date"])
    validate_daily(daily)
    validate_monthly(monthly)
    return VerifiedData(daily, monthly)


# --- specification assembly (ADR 0006 §4, §6, §9.1) -------------------------------------------


def specifications(daily: pd.DataFrame, monthly: pd.DataFrame) -> dict[Spec, pd.DataFrame]:
    """Change tables for the primary specification and the R1-R3 variants (§4.1, §9.1).

    primary: daily, 2Y, same-day; R1: daily, 2Y, lagged US leg; R2: monthly, 2Y;
    R3: daily, 10Y, same-day. Each differs from the primary in exactly one respect."""
    return {
        "primary": changes(daily, "2y", "same-day"),
        "R1": changes(daily, "2y", "lagged"),
        "R2": monthly_changes(monthly, "2y"),
        "R3": changes(daily, "10y", "same-day"),
    }


@dataclass(frozen=True)
class H1aAnalysis:
    """Everything the H1a notebook reports, grouped by ADR 0006 status.

    Confirmatory: ``results["primary"]`` only. Robustness: ``results["R1".."R3"]`` and
    ``robustness``. Secondary: ``era_equality``. Descriptive: the two-leg fields."""

    fits: dict[Spec, EraFit]
    results: dict[Spec, H1aResult]
    robustness: str
    era_equality: Wald
    two_leg: EraFit
    legs: dict[str, LegTest]
    leg_spread: pd.DataFrame
    exclusions: pd.DataFrame

    @property
    def primary(self) -> H1aResult:
        return self.results["primary"]


def analyze(data: VerifiedData) -> H1aAnalysis:
    """Run every ADR 0006 H1a analysis with the validated functions, in protocol order.

    Takes only ``VerifiedData``: the output of ``load_verified`` (§9.2 checks passed)."""
    if not isinstance(data, VerifiedData):
        raise TypeError("analyze() needs the VerifiedData returned by load_verified()")
    daily, monthly = data.daily, data.monthly
    specs = specifications(daily, monthly)
    fits = {spec: era_regression(ch) for spec, ch in specs.items()}
    results = {spec: h1a_test(fit, spec) for spec, fit in fits.items()}
    legs = leg_changes(daily, "2y")
    two_leg = two_leg_regression(legs)
    return H1aAnalysis(
        fits=fits,
        results=results,
        robustness=robustness_label(results["primary"], [results[s] for s in ("R1", "R2", "R3")]),
        era_equality=era_equality(fits["primary"]),
        two_leg=two_leg,
        legs=opposite_legs(two_leg),
        leg_spread=leg_spread(legs),
        exclusions=exclusion_counts(daily[daily["date"] <= DAILY_END]),
    )


# --- display tables (formatting only) ---------------------------------------------------------


def results_table(results: dict[Spec, H1aResult]) -> pd.DataFrame:
    """One row per specification: slopes, the δ test, the gate and the outcome category."""
    rows = {}
    for spec, r in results.items():
        rows[spec] = {
            "status": "confirmatory" if spec == "primary" else "robustness",
            "n_ref": r.n[REF],
            "n_new": r.n[NEW],
            "hac_lag": r.lag,
            "beta_ref": r.beta_ref.estimate,
            "beta_new": r.beta_new.estimate,
            "delta": r.delta.estimate,
            "L (97.5% lower)": r.delta.lower,
            "U (97.5% upper)": r.delta.upper,
            "p_S": r.delta.p_below,
            "p_R": r.delta.p_above,
            "gate": r.gate,
            "outcome": r.outcome,
        }
    return pd.DataFrame(rows).T


def effects_table(r: H1aResult) -> pd.DataFrame:
    """Coefficients and effect sizes for one specification, with 95% two-sided intervals
    (each endpoint is the one-sided 97.5% bound used by the decision rules)."""
    rows = {
        "beta_ref (% per pp)": r.beta_ref,
        "beta_new (% per pp)": r.beta_new,
        "absolute change beta_new - beta_ref": r.absolute_change,
        "delta = beta_new - (2/3) beta_ref": r.delta,
        **{f"delta at decline {k:g} (sensitivity)": d for k, d in r.sensitivity.items()},
    }
    cols = {
        n: {"estimate": d.estimate, "se": d.se, "lower": d.lower, "upper": d.upper}
        for n, d in rows.items()
    }
    return pd.DataFrame(cols).T


def format_set(intervals: list[tuple[float, float]], digits: int = 4) -> str:
    """Readable confidence set, e.g. "[-0.52, -0.21]", "(-∞, -3.1] ∪ [0.8, ∞)",
    "(-∞, ∞): unbounded" or "∅: empty". Infinite ends use open brackets; finite ends
    are closed, as in ``models.fieller``. Never truncates an unbounded set."""
    if not intervals:
        return "∅: empty"

    def end(x: float) -> str:
        return ("-∞" if x < 0 else "∞") if math.isinf(x) else f"{x:.{digits}f}"

    parts = [
        f"{'(' if math.isinf(lo) else '['}{end(lo)}, {end(hi)}{')' if math.isinf(hi) else ']'}"
        for lo, hi in intervals
    ]
    text = " ∪ ".join(parts)
    if any(math.isinf(b) for iv in intervals for b in iv):
        text += ": unbounded (β_ref is not distinguishable from zero at this level)"
    return text


# --- provenance (reproducibility section) -----------------------------------------------------


def vintage_table(root: Path = ROOT) -> pd.DataFrame:
    """The frozen files with their expected SHA-256 and, for raw files, the download time
    recorded in data/raw/manifest.json. Call after ``load_verified`` has passed."""
    manifest = json.loads((root / "data" / "raw" / "manifest.json").read_text())
    rows = {}
    for rel, digest in FROZEN_SHA256.items():
        name = Path(rel).stem
        downloaded = manifest.get(name, {}).get("downloaded_at", "")
        rows[rel] = {"sha256": digest, "downloaded_at": downloaded}
    return pd.DataFrame(rows).T


def provenance(root: Path = ROOT) -> dict[str, str]:
    """Git commit, working-tree state and package versions for the reproducibility record."""
    import platform
    from importlib.metadata import version

    def git(*args: str) -> str:
        out = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
        return out.stdout.strip() if out.returncode == 0 else "unavailable"

    return {
        "git_commit": git("rev-parse", "HEAD"),
        "working_tree": "clean" if git("status", "--porcelain") == "" else "modified",
        "python": platform.python_version(),
        **{pkg: version(pkg) for pkg in ("pandas", "numpy", "statsmodels", "matplotlib")},
    }
