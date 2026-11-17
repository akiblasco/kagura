# Exports the Bai-Perron 5 % critical values for q = 2 and q = 10 as distributed in mbreaks
# 1.0.1 (MIT). Used only as the ADR 0007 §6.1 / §9.1 check, never as reference values.
# Run: Rscript export_tables.R   (environment: r-crosscheck/README.md)
suppressPackageStartupMessages({ library(mbreaks); library(jsonlite) })
ns <- asNamespace("mbreaks"); mb <- function(f) get(f, envir = ns)
out <- list()
for (e in c(0.05, 0.10, 0.15)) for (q in c(2, 10)) {
  out[[sprintf("eps%.2f_q%d", e, q)]] <- list(
    eps = e, q = q,
    supF = unname(mb("getcv1")(2, e)[q, 1:5]),
    seq = unname(mb("getcv2")(2, e)[q, 1:5]),
    dmax = unname(mb("getdmax")(2, e)[q, ])
  )
}
writeLines(toJSON(out, auto_unbox = TRUE, digits = NA, pretty = TRUE), "tables_mbreaks.json")
