"""ADR 0011 Phase A reporting restrictions for `research/adr0007/run_breaks.py`."""

import importlib.util
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from kagura import breaks

ROOT = Path(__file__).parents[1]
RUN = ROOT / "research/adr0007"
sys.path.insert(0, str(RUN))  # run_breaks imports its sibling `data`
spec = importlib.util.spec_from_file_location("run_breaks", RUN / "run_breaks.py")
assert spec and spec.loader
rb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rb)


def synthetic_cell(spec: str = "primary") -> object:
    dates = pd.Series(pd.bdate_range("2000-01-03", periods=900))
    rng = np.random.default_rng(0)
    x = rng.normal(size=900)
    y = np.where(np.arange(900) < 450, 1.0, 0.2) * x + rng.normal(size=900)
    xm = np.column_stack([np.ones(900), x])
    grid = breaks.month_starts(dates.to_numpy())
    return rb.Cell(spec, "full", 0.15, 0, dates, y, xm, ("const", "dd"), 135, grid, 6)


def test_phase_a_outputs_only_descriptive_and_model_selection() -> None:
    out = rb.analyse_cell(synthetic_cell())
    assert set(out) == {"selection", "partitions", "breaks", "regimes", "daily"}
    for rows in out.values():
        for r in rows:
            assert r["tier"] in {"descriptive estimate", "model selection"}
            assert not [k for k in r if rb.WITHHELD.search(k)]
    # Every m = 1..5 is reported with its intervals, so alternative counts stay visible.
    assert sorted({r["m"] for r in out["breaks"]}) == [1, 2, 3, 4, 5]
    r = out["breaks"][0]
    assert r["ci_note"] == rb.CI_NOTE and "76.5-92.7" in r["ci_note"]
    for lev in ("95", "90"):
        assert {
            f"ci{lev}_width_rows",
            f"ci{lev}_width_days",
            f"ci{lev}_width_share_eligible",
        } <= set(r)
    assert "ci95" not in r  # only the "_nominal" name is used


@pytest.mark.parametrize(
    "row",
    [
        {"tier": "descriptive estimate", "supF1": 1.0},
        {"tier": "descriptive estimate", "UDmax": 1.0},
        {"tier": "descriptive estimate", "m_sequential": 2},
        {"tier": "descriptive estimate", "boot_p": 0.01},
        {"tier": "descriptive estimate", "cv5_WDmax": "12"},
        {"tier": "approximately tested"},
        {"tier": "descriptive estimate", "label": "bootstrap-supported"},
        {"label": "exploratory"},
    ],
)
def test_guard_refuses_withheld_statistics_and_strong_labels(row: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        rb.guard([row])


def test_write_applies_the_guard(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        rb.write(tmp_path / "x.csv", [{"tier": "model selection", "seq_F(2|1)": 3.0}])
    assert not (tmp_path / "x.csv").exists()


def test_gate_refuses_changed_validation_outputs(tmp_path: Path) -> None:
    rb.gate()  # the committed originals pass
    for rel in rb.ORIGINALS:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(rb.VALIDATION / rel, tmp_path / rel)
    rb.gate(tmp_path)
    p = tmp_path / "critical_values_tables.txt"
    p.write_text(p.read_text().replace("11 outside", "0 outside"))
    with pytest.raises(SystemExit):
        rb.gate(tmp_path)


def test_adr_0011_records_the_gate_hashes() -> None:
    adr = (
        ROOT / "docs/decisions/0011-validation-resolution-and-scoped-break-reporting.md"
    ).read_text()
    assert "Status: FROZEN" in adr
    for want in rb.ORIGINALS.values():
        assert want in adr
