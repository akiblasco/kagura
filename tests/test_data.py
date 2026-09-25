import pandas as pd
import pytest

from kagura import DATA_PROCESSED
from kagura.data import load, parse_bis, parse_fred, parse_mof

# --- parser tests: run offline, reproduce each source's quirks -------------------------------

FRED_TEXT = "observation_date,DEXJPUS\n2024-07-03,161.5\n2024-07-04,\n2024-07-05,160.8\n"

MOF_TEXT = (
    "Interest Rate,,,,,,,,,,,,,,,(Unit : %)\n"
    "Date,1Y,2Y,3Y,4Y,5Y,6Y,7Y,8Y,9Y,10Y,15Y,20Y,25Y,30Y,40Y\n"
    "1974/9/24,10.327,9.362,8.83,8.515,8.348,8.29,8.24,8.121,8.127,-,-,-,-,-,-\n"
    "1986/7/7,5.1,5.2,5.3,5.4,5.5,5.6,5.7,5.8,5.9,6.0,-,-,-,-,-\n"
    '"  If you cannot download the latest csv data, please clear the cache.",,,,,,,,,,,,,,,\n'
)

BIS_TEXT = (
    "FREQ,REF_AREA,UNIT_MEASURE,UNIT_MULT,TIME_FORMAT,BREAKS,COVERAGE,DECIMALS,TITLE_TS,"
    "TIME_PERIOD,OBS_VALUE,OBS_CONF,OBS_PRE_BREAK,OBS_STATUS\n"
    "M,JP,628,0,,,,,,1946-08,2.838636,F,,A\n"
    "M,JP,628,0,,,,,,2026-07,120.413182,F,,A\n"
)


def test_parse_fred_drops_empty_holiday_rows() -> None:
    df = parse_fred(FRED_TEXT, "usdjpy")
    assert list(df["date"].dt.strftime("%Y-%m-%d")) == ["2024-07-03", "2024-07-05"]
    assert set(df["series"]) == {"usdjpy"}


def test_parse_mof_handles_dash_missing_and_footer() -> None:
    df = parse_mof(MOF_TEXT, "jgb")
    two = df[df["series"] == "jgb_2y"]
    ten = df[df["series"] == "jgb_10y"]
    assert len(two) == 2 and len(ten) == 1
    assert ten["date"].iloc[0] == pd.Timestamp("1986-07-07")
    assert ten["value"].iloc[0] == 6.0


def test_parse_bis_stamps_month_start() -> None:
    df = parse_bis(BIS_TEXT, "jp_cpi")
    assert df["date"].iloc[0] == pd.Timestamp("1946-08-01")
    assert df["value"].iloc[-1] == pytest.approx(120.413182)


# --- data-quality tests: run against the output of `make data` ------------------------------

EXPECTED_START = {
    "usdjpy": "1971-01-04",
    "us_2y": "1976-06-01",
    "us_10y": "1962-01-02",
    "jgb_2y": "1974-09-24",
    "jgb_10y": "1986-07-05",
    "jp_cpi": "1946-08-01",
    "us_cpi": "1947-01-01",
}
PLAUSIBLE_RANGE = {
    "usdjpy": (75, 400),
    "us_2y": (-1, 20),
    "us_10y": (-1, 20),
    "jgb_2y": (-1, 20),
    "jgb_10y": (-1, 20),
    "vix": (5, 100),
}


@pytest.fixture(scope="module")
def series_long() -> pd.DataFrame:
    if not (DATA_PROCESSED / "series_long.csv").exists():
        pytest.skip("run `make data` first")
    return load()


def test_dates_unique_and_increasing(series_long: pd.DataFrame) -> None:
    for name, g in series_long.groupby("series"):
        assert g["date"].is_monotonic_increasing and g["date"].is_unique, name


def test_expected_start_dates(series_long: pd.DataFrame) -> None:
    first = series_long.groupby("series")["date"].min()
    for name, start in EXPECTED_START.items():
        assert first[name] == pd.Timestamp(start), name


def test_values_in_plausible_range(series_long: pd.DataFrame) -> None:
    for name, (lo, hi) in PLAUSIBLE_RANGE.items():
        v = series_long.loc[series_long["series"] == name, "value"]
        assert v.between(lo, hi).all(), f"{name}: {v.min()}..{v.max()}"


def test_recent(series_long: pd.DataFrame) -> None:
    last = series_long.groupby("series")["date"].max()
    # Monthly series arrive with up to a three-month publication lag (jp_call_rate is the slowest).
    stale = last[last < pd.Timestamp.today() - pd.Timedelta(days=150)]
    assert stale.empty, f"stale series: {stale.to_dict()}"
