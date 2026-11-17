# ADR 0007 §9.2 — independent R cross-check

R is **not** a project dependency. It runs in its own micromamba environment, outside `uv`,
`make test` and CI. The committed reference files let `tests/test_breaks.py` re-check the
Python implementation without R.

## Environment (as used on 2026-11-17)

| Component | Version | Source |
|---|---|---|
| micromamba | 2.10.0 | `~/.local/bin/micromamba` |
| R | 4.5.3 (2026-03-11), aarch64-apple-darwin | conda-forge `r-base` |
| strucchange | 1.6-0 | conda-forge `r-strucchange` |
| mbreaks | 1.0.1 | CRAN |
| jsonlite | 2.0.0 | conda-forge `r-jsonlite` |

Full details, including BLAS, are in `sessionInfo.txt`.

Commands that created the environment:

```sh
~/.local/bin/micromamba create -y -r ~/.local/mamba -n kagura-r -c conda-forge \
    r-base r-strucchange r-jsonlite
~/.local/bin/micromamba run -r ~/.local/mamba -n kagura-r \
    Rscript -e 'install.packages("mbreaks", repos = "https://cloud.r-project.org")'
```

## Reproduce

From the repository root:

```sh
uv run python research/methodology/adr0007-break-grid/r-crosscheck/make_fixtures.py
cd research/methodology/adr0007-break-grid/r-crosscheck
~/.local/bin/micromamba run -r ~/.local/mamba -n kagura-r Rscript crosscheck.R
cd -
uv run python research/methodology/adr0007-break-grid/r-crosscheck/compare.py
```

Running `crosscheck.R` twice gives byte-identical `r_results.json`.

## Files

| File | Content |
|---|---|
| `make_fixtures.py` | Four fixtures: Nile (mean shift), two slope breaks, heteroskedastic regimes, AR(1) errors. Fixed seeds, T = 100 or 400, written with `%.17g` |
| `crosscheck.R` | `strucchange::breakpoints` (h = 15 %, all rows candidates, m = 0…5) and the `mbreaks` internals `doglob`, `pftest`, `sequa`, `estim`/`interval`, `cvg`, with four explicit option sets |
| `r_results.json`, `sessionInfo.txt` | R output (reference files) |
| `compare.py` → `comparison_adr0012.txt` | Item-by-item comparison; interval bounds exact (ADR 0012) |
| `comparison.txt` | The ADR 0011 original (one-row tolerance, before the ADR 0012 correction), kept unchanged |

**What agreement shows.** Implementation fidelity: the Python port computes what
`strucchange` and `mbreaks` compute. It is not evidence that either is correct. ADR 0012 found
a defect that both share and that this comparison could not detect.

## Option sets compared

| Name | robust | hetdat | hetvar | prewhit | kernel |
|---|---|---|---|---|---|
| `homo` | 0 | 1 | 0 | 0 | — |
| `homo_het` | 0 | 1 | 1 | 0 | — |
| `hac` | 1 | 1 | 1 | 0 | QS, Andrews AR(1) bandwidth |
| `hac_pw` | 1 | 1 | 1 | 1 | QS, Andrews AR(1) bandwidth |

`hetq` and `hetomega` are 1 throughout. The ADR 0007 protocol uses the `hac` structure with the
Bartlett kernel and the ADR 0006 §4.4 lag instead of QS; `mbreaks` has no Bartlett option, so
the kernel swap is checked separately against statsmodels' Newey–West
(`tests/test_breaks.py::test_bartlett_lrv_matches_statsmodels`).

## Differences that are explained, not failures

The comparison labels these "convention". Each one is reproduced exactly by `compare.py`
before it is given that label.

1. **`mbreaks::interval` upper bounds.** The rounding and "+ 1" of the upper bounds sit inside
   the loop over breaks, so break i of an m-break model gets m − i + 1 additions instead of
   one. Python applies it once. With m = 3, break 1's upper bounds in `mbreaks` are exactly
   2 rows higher. Since ADR 0012, bounds must match exactly, so a one-row difference is also
   labelled "convention" (it was a "pass" under the one-row tolerance).
2. **`mbreaks::psigmq`** (robust = 0, hetvar = 1 only). A middle regime's variance sums
   rows b[j−1]…b[j] (1-based, inclusive), one row more than the regime, over b[j] − b[j−1].
   Python uses the regime's own rows. Reproducing the `mbreaks` rows gives its sup F and
   SEs to 1e-6. The ADR 0007 protocol uses robust = 1, which does not call `psigmq`.
3. **`mbreaks::interval` robust `phi2s`** (ADR 0012). `mbreaks` divides Δ'Ω₂Δ by Δ'Q₁Δ;
   Python divides by Δ'Q₂Δ. `compare.mbreaks_interval` reproduces the `mbreaks` value.
