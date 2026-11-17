# ADR 0007 §9.2 independent cross-check. Not a project dependency; not run by make test or CI.
# Run from this directory (see README.md for the environment):
#   Rscript crosscheck.R
# Writes r_results.json and sessionInfo.txt, which are committed as reference files.
#
# mbreaks' internal procedures are called directly with every option set explicitly, so no
# wrapper default (prewhit = 1, robust = 1, ...) is applied silently.
suppressPackageStartupMessages({
  library(strucchange)
  library(mbreaks)
  library(jsonlite)
})
ns <- asNamespace("mbreaks")
mb <- function(f) get(f, envir = ns)

eps1 <- 0.15
M <- 5
signif <- 2  # 5 % (mbreaks rows: 1 = 10 %, 2 = 5 %, 3 = 2.5 %, 4 = 1 %)
configs <- list(
  homo     = list(robust = 0, hetdat = 1, hetvar = 0, prewhit = 0, hetq = 1, hetomega = 1),
  homo_het = list(robust = 0, hetdat = 1, hetvar = 1, prewhit = 0, hetq = 1, hetomega = 1),
  hac      = list(robust = 1, hetdat = 1, hetvar = 1, prewhit = 0, hetq = 1, hetomega = 1),
  hac_pw   = list(robust = 1, hetdat = 1, hetvar = 1, prewhit = 1, hetq = 1, hetomega = 1)
)

out <- list()
for (name in c("nile", "two_break_slope", "hetero_regimes", "ar1_errors")) {
  d <- read.csv(paste0(name, ".csv"))
  # strucchange: every row a candidate, h = eps1 * T.
  f <- if (ncol(d) == 1) y ~ 1 else y ~ x
  bp <- breakpoints(f, data = d, h = eps1, breaks = M)
  rss <- summary(bp)$RSS
  parts <- list()
  for (m in 0:M) {
    b <- if (m == 0) integer(0) else as.integer(breakpoints(bp, breaks = m)$breakpoints)
    parts[[as.character(m)]] <- list(breaks = b, ssr = unname(rss["RSS", as.character(m)]))
  }

  df <- mb("process_data")(y_name = "y", z_name = if (ncol(d) == 1) NULL else "x",
                           x_name = NULL, data = d, const = 1)
  y <- df$y; z <- df$z; x <- df$x; p <- df$p; q <- df$q
  bigT <- nrow(y)
  h <- floor(eps1 * bigT)
  glob <- mb("doglob")(y, z, x, M, 1e-5, h, 10, 0, 0, 0, eps1)
  datevec <- glob$datevec
  res <- list()
  for (cn in names(configs)) {
    o <- configs[[cn]]
    ftest <- sapply(1:M, function(k) mb("pftest")(y, z, k, q, bigT, datevec, o$prewhit,
                                                  o$robust, x, p, o$hetdat, o$hetvar))
    sq <- mb("sequa")(M, signif, q, h, bigT, o$robust, o$prewhit, z, y, x, p,
                      o$hetdat, o$hetvar, eps1)
    est <- lapply(1:3, function(k) {
      e <- mb("estim")(k, q, z, y, datevec[1:k, k, drop = FALSE], o$robust, o$prewhit,
                       o$hetomega, o$hetq, x, p, o$hetdat, o$hetvar)
      list(breaks = as.integer(datevec[1:k, k]), CI = unname(e$CI),
           beta = as.vector(e$beta), SE = as.vector(e$SE))
    })
    res[[cn]] <- list(ftest = ftest, seq_m = sq$nbreak,
                      seq_breaks = as.integer(sort(sq$dv0)), estim = est)
  }
  out[[name]] <- list(
    T = bigT, h = h, q = q,
    strucchange = parts,
    mbreaks_global = lapply(1:M, function(k) as.integer(datevec[1:k, k])),
    cv_supF = unname(mb("getcv1")(signif, eps1)[q, 1:M]),
    cv_seq = unname(mb("getcv2")(signif, eps1)[q, 1:M]),
    cv_dmax = unname(mb("getdmax")(signif, eps1)[q, 1]),
    mbreaks = res
  )
}

grid <- expand.grid(eta = c(0.5, 1, 2.5), phi1s = c(0.7, 1, 2), phi2s = c(0.5, 1, 3))
out$cvg <- lapply(seq_len(nrow(grid)), function(i) {
  g <- grid[i, ]
  list(eta = g$eta, phi1s = g$phi1s, phi2s = g$phi2s,
       c = as.vector(mb("cvg")(g$eta, g$phi1s, g$phi2s)))
})
writeLines(toJSON(out, auto_unbox = TRUE, digits = NA, pretty = TRUE), "r_results.json")
# The home directory is replaced by "~" so no local path is committed.
writeLines(gsub(path.expand("~"), "~", capture.output(sessionInfo()), fixed = TRUE),
           "sessionInfo.txt")
