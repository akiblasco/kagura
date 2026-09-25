# Project KAGURA — Research Hypotheses

These are the initial confirmatory hypotheses for the research program.

They should be timestamped/frozen before the corresponding empirical analyses are performed. Subsequent ideas discovered from the data should be labeled **exploratory** rather than retroactively treated as preregistered hypotheses.

---

## H1 — Yield Differential Decoupling

### Claim
The explanatory relationship between US-Japan yield differentials and USD/JPY has weakened or changed materially relative to earlier historical periods.

### Initial tests
- rolling correlation
- rolling regression beta
- rolling explanatory power
- parameter-stability tests
- structural-break tests
- alternative 2Y/10Y differentials
- nominal versus real-rate variants where defensible

### Evidence against H1
A stable specification with approximately stable coefficients and explanatory power adequately describes both historical and recent samples.

---

## H2 — Carry Amplification

### Claim
Large speculative short-yen/carry positioning amplifies the exchange-rate response to monetary-policy or relative-rate shocks.

Conceptually:

\[
\Delta FX_t =
\beta_0+
\beta_1 Shock_t+
\beta_2 Carry_t+
\beta_3 Shock_t \times Carry_t+
\epsilon_t
\]

The main quantity of interest is the interaction term:

\[
\beta_3
\]

### Evidence against H2
Policy/rate sensitivity does not vary systematically with positioning or carry state after reasonable controls.

---

## H3 — Regime Dependence

### Claim
The drivers of USD/JPY differ materially across market regimes.

### Potential tests
- structural-break models
- time-varying coefficients
- HMM/latent-state models
- regime-specific regressions
- state-dependent local projections later

### Evidence against H3
A stable single-regime specification performs comparably and inferred regimes have little interpretable difference.

---

## H4 — Intervention Persistence

### Claim
Japanese FX intervention produces more persistent exchange-rate effects when it is aligned with evolving monetary-policy expectations and/or coordinated with other authorities.

### Potential moderators
- intervention size
- unilateral versus coordinated action
- BOJ stance
- rate expectations
- carry positioning
- volatility regime

### Evidence against H4
Persistence is not materially related to policy alignment/coordination after controlling for market state, or the historical event sample is insufficient for credible inference.

---

## H5 — Policy Communication Contains Incremental Information

### Claim
BOJ communication contains measurable information about subsequent FX/market dynamics beyond contemporaneous observable rates and macro variables.

### Evaluation
Compare:

\[
Model_{macro}
\]

with:

\[
Model_{macro+text}
\]

using strict out-of-sample evaluation.

### Evidence against H5
Text-derived factors fail to improve calibration, explanatory power, event response estimation, or forecasting after reasonable controls.

A null result is acceptable.

---

## H6 — Nonlinear Models Help Selectively

### Claim
Nonlinear ML models improve performance primarily during stressed, highly positioned, or regime-transition periods rather than uniformly across all market states.

### Evaluation
Compare model families by regime/state rather than only using one aggregate performance number.

### Evidence against H6
ML improvements are uniform, nonexistent, or vanish under stricter temporal validation.

---

## H7 — Yen Strength Is Not Equivalent to Welfare Improvement

### Claim
Policies that strengthen the yen do not necessarily maximize broader Japanese economic welfare once inflation, real wages, growth, employment, financial conditions, exporter performance, and debt-service costs are considered.

This is primarily a policy-simulation hypothesis and should be investigated only after the underlying empirical relationships are credible.

### Evidence against H7
Within credible model uncertainty, policies that strengthen JPY also monotonically improve all major welfare components across plausible preference weights—a result that would itself require substantial scrutiny.

---

# Exploratory questions

The following are interesting but should initially remain exploratory:

- Does speculative positioning explain the Yen Fundamental Gap?
- Does oil sensitivity vary with yen regimes?
- Are BOJ communication surprises more important when market-implied rate probabilities are highly concentrated?
- Does intervention effectiveness exhibit diminishing returns?
- Are JPY responses asymmetric between hawkish and dovish surprises?
- Does the yen behave differently during global risk-off episodes because of its historical funding/safe-haven role?
- Do foreign and domestic capital-flow components explain different portions of residual FX movement?
- Can regime-transition probabilities provide useful early-warning information without overfitting?

Exploratory findings may motivate future preregistered hypotheses.
