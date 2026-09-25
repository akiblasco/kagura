"""KAGURA: quantitative research on the yen and Japanese monetary policy."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "reports" / "figures"

# Modeling sample. See docs/decisions/0001-sample-period.md.
SAMPLE_START = "1981-01-01"
