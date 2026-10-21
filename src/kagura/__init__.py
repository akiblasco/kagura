"""KAGURA: quantitative research on the yen and Japanese monetary policy."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Data directory read and written by the pipeline; relative paths are relative to ROOT.
# Default data/ holds the frozen ADR 0006 vintage (protected, see kagura.vintage). H1a always
# reads ROOT/data regardless of this setting.
DATA = ROOT / (os.environ.get("KAGURA_DATA") or "data")  # unset or empty: the default data/
DATA_RAW = DATA / "raw"
DATA_PROCESSED = DATA / "processed"
FIGURES = ROOT / "reports" / "figures"

# Modeling sample. See docs/decisions/0001-sample-period.md.
SAMPLE_START = "1981-01-01"
