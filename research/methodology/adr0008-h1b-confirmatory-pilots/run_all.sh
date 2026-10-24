#!/usr/bin/env bash
# Re-run every ADR 0008 confirmatory-method pilot (synthetic data only) in a scratch copy and
# compare its printed output with reference_outputs/. Usage: ./run_all.sh <empty-output-dir>
# About 30-40 min on 10 cores (Apple M2 Max). Timing columns (ms/rep, s/rep) will differ.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$(mkdir -p "$1" && cd "$1" && pwd)"
PROJECT="$(cd "$HERE/../../.." && pwd)"
cp -R "$HERE/ak_bounds" "$HERE/wagner_wied" "$OUT/"
py() { uv run --project "$PROJECT" python "$@"; }

cd "$OUT/ak_bounds"
py check_ak_fast.py              > check_ak_fast.out
py ak_table1.py 5000             > ak_table1.out
py ak_size_pilot.py 4000         > ak_size_pilot.out
py ak_diag.py                    > ak_diag.out
py ak_calib_pilot.py             > ak_calib_pilot.out
py bounds_pilot.py 20000 800     > bounds_pilot.out
py combined_pilot.py             > combined_pilot.out

cd "$OUT/wagner_wied"
py validate.py                   > validate.out
py validate_fm.py                > validate_fm.out
py ww_limit.py 100000            > ww_limit.out
py ww_pilot.py 2000 1000         > ww_pilot.out
py ww_tables.py                  # writes ww_null_ci.out, ww_power_table.out
py ww_nocap.py                   > ww_nocap.out
py ww_big.py                     > ww_big.out

# ponytail: timing columns are stripped before comparing; everything else must match exactly
strip() { sed -E 's/ *\(?[0-9.]+ ?(ms|s)\/rep\)?//g' "$1"; }
status=0
for ref in "$HERE"/reference_outputs/*.out; do
    name="$(basename "$ref")"
    new="$(ls "$OUT"/*/"$name")"
    if diff <(strip "$ref") <(strip "$new") > /dev/null; then echo "MATCH    $name"
    else echo "DIFFERENT $name"; status=1; fi
done
exit $status
