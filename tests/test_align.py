import pandas as pd
import pytest

from kagura import DATA_PROCESSED
from kagura.align import (
    AVAILABLE_AFTER,
    MARKET,
    MAX_CARRIED_SHARE,
    build_daily,
    build_monthly,
    carried_share,
)


def _long(rows: list[tuple[str, str, float]]) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=["date", "series", "value"])
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values(["series", "date"]).reset_index(drop=True)


# --- offline tests on synthetic data ---------------------------------------------------------


def test_daily_carries_latest_prior_value_within_cap_and_flags_it() -> None:
    fx = [(d, "usdjpy", 150.0) for d in ["2024-01-05", "2024-01-08", "2024-01-09", "2024-01-22"]]
    # JGB: Saturday quote, Monday holiday, then a two-week gap.
    jgb = [
        (d, "jgb_2y", v) for d, v in [("2024-01-05", 0.1), ("2024-01-06", 0.2), ("2024-01-09", 0.3)]
    ]
    d = build_daily(_long(fx + jgb)).set_index("date")
    assert d["jgb_2y"].tolist()[:3] == [0.1, 0.2, 0.3]  # Monday carries Saturday, not Friday
    assert d["jgb_2y_carried"].tolist() == [False, True, False, False]
    assert pd.isna(d.loc["2024-01-22", "jgb_2y"])  # 13 days stale: missing, not carried
    assert len(d) == 4  # the calendar is exactly the USD/JPY days


def test_change_carried_flags_carried_rows_and_the_next_live_row() -> None:
    days = ["2024-04-26", "2024-04-29", "2024-04-30", "2024-05-01", "2024-05-02", "2024-05-03"]
    fx = [(d, "usdjpy", 150.0) for d in days]
    us = [(d, "us_2y", 5.0) for d in days]
    # Tokyo closed on Monday 29 April and Friday 3 May.
    jgb = [(d, "jgb_2y", 0.3) for d in days if d not in ("2024-04-29", "2024-05-03")]
    d = build_daily(_long(fx + us + jgb))
    assert d["jgb_2y_carried"].tolist() == [False, True, False, False, False, True]
    # The 30 April change spans the closure (26 Apr -> 30 Apr), so it is flagged too.
    assert d["jgb_2y_change_carried"].tolist() == [False, True, True, False, False, True]
    assert not d["us_2y_change_carried"].any()
    # A differential is affected when either leg is.
    assert d["diff_2y_change_carried"].tolist() == d["jgb_2y_change_carried"].tolist()


def test_monthly_uses_only_released_values() -> None:
    fx = [(d, "usdjpy", 150.0) for d in ["2024-08-30", "2024-09-13", "2024-09-30"]]
    cpi = [
        (d, "us_cpi", v) for d, v in [("2024-07-01", 1.0), ("2024-08-01", 2.0), ("2024-09-01", 3.0)]
    ]
    jp = [("2024-07-01", "jp_cpi", 1.0), ("2024-08-01", "jp_cpi", 2.0)]
    call = [("2024-08-01", "jp_call_rate", 0.2), ("2024-09-01", "jp_call_rate", 0.3)]
    long = _long(fx + cpi + jp + call)
    m = build_monthly(long, build_daily(long)).set_index("date")
    # August month-end: July US CPI (released Aug 15) is known, August CPI is not.
    assert m.loc["2024-08-30", "us_cpi_month"] == pd.Timestamp("2024-07-01")
    # July Japan CPI is assumed known on Saturday 31 August, after the Friday month-end.
    assert pd.isna(m.loc["2024-08-30", "jp_cpi"])
    # September month-end: August CPI (US Sep 15, Japan Sep 30) and August call rate are known.
    sep = m.loc["2024-09-30"]
    assert sep["us_cpi"] == 2.0 and sep["jp_cpi"] == 2.0 and sep["jp_call_rate"] == 0.2


def test_monthly_drops_unfinished_final_month() -> None:
    fx = [(d, "usdjpy", 150.0) for d in ["2024-08-30", "2024-09-13"]]
    long = _long(fx + [("2024-07-01", s, 1.0) for s in AVAILABLE_AFTER])
    assert build_monthly(long, build_daily(long))["date"].tolist() == [pd.Timestamp("2024-08-30")]


# --- data-quality tests: run against the output of `make data` ------------------------------


@pytest.fixture(scope="module")
def monthly() -> pd.DataFrame:
    if not (DATA_PROCESSED / "monthly.csv").exists():
        pytest.skip("run `make data` first")
    cols = ["date"] + [f"{s}_month" for s in AVAILABLE_AFTER]
    return pd.read_csv(DATA_PROCESSED / "monthly.csv", parse_dates=cols)


def test_no_monthly_value_before_its_availability_date(monthly: pd.DataFrame) -> None:
    for name, lag in AVAILABLE_AFTER.items():
        known = monthly.dropna(subset=[f"{name}_month"])
        assert (known[f"{name}_month"] + lag <= known["date"]).all(), name


def test_carried_flag_only_where_value_present() -> None:
    if not (DATA_PROCESSED / "daily.csv").exists():
        pytest.skip("run `make data` first")
    d = pd.read_csv(DATA_PROCESSED / "daily.csv")
    assert d["usdjpy"].notna().all()
    for name in MARKET:
        assert not (d[f"{name}_carried"] & d[name].isna()).any(), name


def test_h1_inputs_not_degraded_by_carrying() -> None:
    """Fails if a source loses history and gaps are silently filled by carrying.

    Only the H1 yield legs fail the test; other series get a warning from ``make data``."""
    if not (DATA_PROCESSED / "daily.csv").exists():
        pytest.skip("run `make data` first")
    shares = carried_share(pd.read_csv(DATA_PROCESSED / "daily.csv"))
    for name in ("us_2y", "us_10y", "jgb_2y", "jgb_10y"):
        assert shares[name] <= MAX_CARRIED_SHARE, f"{name}: {shares[name]:.1%} carried"
