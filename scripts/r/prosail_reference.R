# Independent reference for the forward model (A-47, brief Phase 1 "done when").
#
#   Rscript scripts/r/prosail_reference.R <work dir>
#
# Called by scripts/check_forward_reference.py, which writes into <work dir>:
#   params.csv  one row per case: n cab car cbrown ant cw cm lai ala hspot
#               tts tto psi rsoil psoil
#   coeffs.csv  the Python package's PROSPECT-D coefficients on 400-2500 nm:
#               lambda nr kab kcar kant kbrown kw km
#   soil.csv    its two soil spectra: lambda soil1 soil2
# and reads back, for each coefficient set ("ours" = the Python package's,
# "r" = the R package's own):
#   leaf_R_<set>.csv, leaf_T_<set>.csv, canopy_<set>.csv  (rows = cases)
#
# Implementations: Feret's `prospect` (PROSPECT-D/PRO) and `prosail` (4SAIL),
# installed from github.com/jbferet. The "ours" run isolates the code; the
# "r" run adds the coefficient recalibration that came with PROSPECT-PRO.

suppressPackageStartupMessages({ library(prospect); library(prosail) })

args <- commandArgs(trailingOnly = TRUE)
work <- args[1]
p <- read.csv(file.path(work, "params.csv"))
k <- read.csv(file.path(work, "coeffs.csv"))
soil <- read.csv(file.path(work, "soil.csv"))

spec_r <- prospect::spec_prospect_full_range
spec_ours <- spec_r
spec_ours$nrefrac <- k$nr
spec_ours$sac_chl <- k$kab
spec_ours$sac_car <- k$kcar
spec_ours$sac_ant <- k$kant
spec_ours$sac_brown <- k$kbrown
spec_ours$sac_ewt <- k$kw
spec_ours$sac_lma <- k$km
spec_ours$sac_prot <- 0
spec_ours$sac_cbc <- 0
# Transmissivity at the leaf surface depends on the refractive index.
spec_ours$calctav_90 <- prospect::calctav(90, k$nr)
spec_ours$calctav_40 <- prospect::calctav(40, k$nr)

run <- function(spec, tag) {
  n <- nrow(p)
  lr <- matrix(NA_real_, n, nrow(spec)); lt <- lr; cs <- lr
  for (i in seq_len(n)) {
    q <- p[i, ]
    leaf <- prospect::prospect(spec_prospect = spec, n_struct = q$n, chl = q$cab,
                               car = q$car, ant = q$ant, brown = q$cbrown, ewt = q$cw,
                               lma = q$cm, alpha = 40, verbose = FALSE)
    rs <- q$rsoil * (q$psoil * soil$soil1 + (1 - q$psoil) * soil$soil2)
    can <- prosail::fourSAIL(lop = leaf, type_lidf = 2, lidf_a = q$ala, lai = q$lai,
                             hotspot = q$hspot, tts = q$tts, tto = q$tto, psi = q$psi,
                             rsoil = rs)
    lr[i, ] <- leaf$reflectance; lt[i, ] <- leaf$transmittance; cs[i, ] <- can$rsot
  }
  write.csv(lr, file.path(work, paste0("leaf_R_", tag, ".csv")), row.names = FALSE)
  write.csv(lt, file.path(work, paste0("leaf_T_", tag, ".csv")), row.names = FALSE)
  write.csv(cs, file.path(work, paste0("canopy_", tag, ".csv")), row.names = FALSE)
}

run(spec_ours, "ours")
run(spec_r, "r")

# The one structural difference found: R's campbell() bins the ellipsoidal
# leaf-angle distribution in the original 4SAIL's 13 classes (10-degree steps
# to 80, then 2-degree), Python prosail in 18 equal 5-degree classes. Same
# formula on 18 equal classes, so "ours18" isolates everything else.
campbell18 <- function(ala) {
  tx2 <- seq(0, 85, by = 5); tx1 <- tx2 + 5
  tl1 <- tx1 * (pi / 180); tl2 <- tx2 * (pi / 180)
  excent <- exp(-1.6184e-05 * ala^3 + 0.0021145 * ala^2 - 0.1239 * ala + 3.2491)
  x1 <- excent / sqrt(1 + excent^2 * tan(tl1)^2)
  x2 <- excent / sqrt(1 + excent^2 * tan(tl2)^2)
  if (excent == 1) {
    freq <- abs(cos(tl1) - cos(tl2))
  } else {
    a2 <- excent^2 / abs(1 - excent^2); a <- sqrt(a2)
    if (excent > 1) {
      f <- function(x) x * sqrt(a2 + x^2) + a2 * log(x + sqrt(a2 + x^2))
    } else {
      f <- function(x) x * sqrt(a2 - x^2) + a2 * asin(x / a)
    }
    freq <- abs(f(x1) - f(x2))
  }
  list(lidf = freq / sum(freq), litab = (tx1 + tx2) / 2)
}
assignInNamespace("campbell", campbell18, ns = "prosail")
run(spec_ours, "ours18")
writeLines(c(paste("prospect", packageVersion("prospect")),
             paste("prosail", packageVersion("prosail")),
             R.version.string), file.path(work, "versions.txt"))
