# ADR 0007 §9.2 independent cross-check. Not a project dependency; not run by make test or CI.
# Run from this directory: Rscript crosscheck.R
# Writes r_results.json and sessionInfo.txt, which are committed as reference files.
suppressPackageStartupMessages({
  library(strucchange)
  library(mbreaks)
  library(jsonlite)
})

eps <- 0.15
M <- 5
out <- list()
for (name in c("nile", "two_break_slope", "hetero_regimes", "ar1_errors")) {
  d <- read.csv(paste0(name, ".csv"))
  f <- if (ncol(d) == 1) y ~ 1 else y ~ x
  bp <- breakpoints(f, data = d, h = eps, breaks = M)
  parts <- list()
  for (m in 0:M) {
    b <- if (m == 0) integer(0) else as.integer(breakpoints(bp, breaks = m)$breakpoints)
    parts[[as.character(m)]] <- list(strucchange_breaks = b, ssr = bp$RSS["RSS", as.character(m)])
  }
  # mbreaks: pure structural change, homoskedastic, no prewhitening (matches kagura.breaks.sup_f).
  z <- if (ncol(d) == 1) NULL else "x"
  mb <- mdl("y", z_name = z, data = d, eps1 = eps, m = M,
            prewhit = 0, robust = 0, hetdat = 0, hetvar = 0, hetq = 0, hetomega = 0)
  out[[name]] <- list(
    T = nrow(d),
    partitions = parts,
    bic_m = as.integer(summary(bp)$RSS["BIC", , drop = TRUE] |> which.min() - 1),
    mbreaks = list(
      bic_m = mb$BIC$nbreak, lwz_m = mb$LWZ$nbreak,
      seq_m = mb$sequa$nbreak,
      supF = mb$wd$ftest[, 1],
      date = mb$sequa$date,
      ci = mb$sequa$CI
    )
  )
}
writeLines(toJSON(out, auto_unbox = TRUE, digits = NA, pretty = TRUE), "r_results.json")
writeLines(capture.output(sessionInfo()), "sessionInfo.txt")
