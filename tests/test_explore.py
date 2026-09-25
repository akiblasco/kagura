import numpy as np
import pandas as pd
import pytest

from kagura.align import build_daily
from kagura.explore import changes, rolling_corr, stationarity, yoy


def test_changes_lagged_variant_and_exclusion() -> None:
    days = pd.bdate_range("2024-04-24", periods=6).strftime("%Y-%m-%d")
    fx = [(d, "usdjpy", 150.0 + i) for i, d in enumerate(days)]
    us = [(d, "us_2y", 5.0 + i / 10) for i, d in enumerate(days)]
    # JGB missing on row 3 (a Tokyo holiday): rows 3 and 4 are flagged.
    jgb = [(d, "jgb_2y", 0.3) for i, d in enumerate(days) if i != 3]
    long = pd.DataFrame(fx + us + jgb, columns=["date", "series", "value"])
    long["date"] = pd.to_datetime(long["date"])
    daily = build_daily(long)

    same = changes(daily, "2y", "same-day")
    assert same["excluded"].tolist() == [False, False, False, True, True, False]
    assert same["ddiff"].isna().tolist() == [True, False, False, True, True, False]
    assert same["ddiff"].iloc[5] == pytest.approx(0.1)
    assert same["dfx"].iloc[1] == pytest.approx(100 * np.log(151 / 150))

    lag = changes(daily, "2y", "lagged")
    # First two rows have no lagged change; the JGB flag drops rows 3 and 4 as before.
    assert lag["ddiff"].isna().tolist() == [True, True, False, True, True, False]
    assert lag["ddiff"].iloc[2] == pytest.approx(0.1)  # us[1] - us[0], JGB unchanged


def test_rolling_corr_uses_pairs_and_enforces_minimum() -> None:
    rng = np.random.default_rng(0)
    x = pd.Series(rng.normal(size=100))
    y = 2 * x + 1
    y[:5] = np.nan  # 95 usable pairs
    r = rolling_corr(x, y, window=100)
    assert r["r"].iloc[-1] == pytest.approx(1.0)
    assert r["n"].iloc[-1] == 95
    assert r["r"].iloc[:84].isna().all()  # windows with fewer than 80 pairs report nothing
    neg = rolling_corr(x, -x + rng.normal(scale=1, size=100), window=100).iloc[-1]
    assert neg["lo"] < neg["r"] < neg["hi"] < 0


def test_yoy_is_twelve_month_change_by_reference_month() -> None:
    dates = pd.date_range("2020-01-01", periods=13, freq="MS")
    long = pd.DataFrame({"date": dates, "series": "us_cpi", "value": [100.0] * 12 + [103.0]})
    s = yoy(long, "us_cpi")
    assert s.isna().sum() == 12 and s.iloc[-1] == pytest.approx(3.0)


def test_stationarity_separates_random_walk_from_noise() -> None:
    walk = pd.Series(np.random.default_rng(1).normal(size=500).cumsum())
    t = stationarity({"walk": walk}).set_index("form")
    adf_p, kpss_p = t["adf_p"], t["kpss_p"]
    assert adf_p["level"] > 0.05 and kpss_p["level"] == "<0.01"
    # KPSS falsely rejects white noise 5% of the time, so only require no rejection at 1%.
    assert adf_p["change"] < 0.01 and kpss_p["change"] != "<0.01"
