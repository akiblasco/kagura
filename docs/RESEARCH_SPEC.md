# Project KAGURA — Research Specification

## 1. Mission

Project KAGURA is an open quantitative research platform for studying the Japanese yen, Japanese monetary-policy transmission, foreign-exchange intervention, market regimes, and Japanese macroeconomic outcomes.

It is not primarily a USD/JPY prediction application.

The research program asks four progressively harder questions:

1. Why is the yen moving?
2. When and why do the drivers of the yen change?
3. What is likely to happen next?
4. What would likely happen under alternative Japanese policy choices?

The long-run objective is to combine rigorous economics, econometrics, statistics, machine learning, causal inference, and natural-language processing without using complexity for its own sake.

---

## 2. Primary research question

### Initial question

> Has USD/JPY structurally decoupled from the US-Japan interest-rate differential, and if so, when and by how much?

This is deliberately narrower than the full KAGURA vision. The first public research result should establish whether the motivating puzzle actually exists in the data.

---

## 3. Research philosophy

KAGURA follows:

> Economics first. Statistics second. Machine learning third. AI fourth.

A sophisticated model is useful only when it allows us to test or estimate something a simpler model cannot adequately capture.

The project must distinguish:

- prediction from explanation
- explanation from causal identification
- statistical significance from economic significance
- in-sample fit from out-of-sample performance
- model output from policy recommendation

Negative results are valid research results.

---

## 4. Final outputs

KAGURA should eventually produce four complementary artifacts.

### 4.1 Research paper

The intellectual core.

Target:

- approximately 25–40 pages including figures/appendices
- graduate-level quantitative research quality
- explicit hypotheses
- transparent methodology
- robustness tests
- uncertainty
- limitations
- reproducibility

Potential working title:

> **Beyond Interest-Rate Differentials: Regime-Dependent Drivers of the Japanese Yen**

The paper is intended as a working paper, open to review by academic economists and
practitioners.

### 4.2 Open-source repository

The repository proves the analysis is real and reproducible.

It should contain:

- data pipelines
- reusable research code
- tests
- experiment configuration
- figures/tables
- documentation
- research decision log
- reproducibility instructions

### 4.3 Interactive dashboard

The dashboard is the communication layer.

Eventually show:

- current USD/JPY context
- fundamental-value estimate
- Yen Fundamental Gap
- regime probabilities
- macro/market drivers
- event studies
- forecast distributions
- uncertainty
- policy scenario exploration

It must not look like a retail trading signal dashboard.

### 4.4 Research presentation

A polished 15–20 minute talk suitable for academic and practitioner audiences, such as
research seminars and economics/AI events.

Narrative:

1. The yen/rates relationship
2. The break or puzzle
3. Candidate mechanisms
4. Empirical evidence
5. Regimes/nonlinearity
6. Policy implications and uncertainty

Every major result should have:
- an executive explanation
- a quantitative explanation
- a technical formulation

---

## 5. Core analytical architecture

### Engine 1 — Yen Fundamental Model

Estimate the exchange rate relationship implied by traditional macroeconomic fundamentals.

Candidate inputs:

#### Rates and yields
- BOJ policy rate
- Fed Funds rate
- Japanese 2Y JGB yield
- US 2Y Treasury yield
- Japanese 10Y JGB yield
- US 10Y Treasury yield
- yield differentials
- real-rate differentials where defensible

#### Prices
- Japanese CPI/core CPI
- US CPI/core CPI
- inflation differential
- inflation expectations where available

#### External balance
- trade balance
- current account
- exports/imports
- terms of trade
- foreign reserves

#### Commodities
- Brent
- WTI
- energy/LNG proxies where appropriate

#### Growth/business conditions
- GDP
- industrial production
- PMI
- Tankan
- consumer confidence

#### Financial conditions
- Nikkei 225
- TOPIX
- S&P 500
- VIX
- MOVE
- credit conditions where useful

#### Capital flows
- Japanese purchases of foreign securities
- foreign purchases of Japanese securities
- portfolio flows
- related institutional flow proxies

#### FX valuation
- REER
- PPP-style indicators
- BIS effective exchange-rate measures

Initial models should favor interpretability:

- OLS
- rolling regression
- ARDL
- VECM where cointegration is supported
- Elastic Net
- Bayesian regression / dynamic models later if justified

Primary conceptual output:

\[
\hat S^{fundamental}_t
\]

and a residual / deviation measure:

\[
YFG_t = S_t - \hat S^{fundamental}_t
\]

This is the **Yen Fundamental Gap**.

The exact scale/definition must be chosen carefully. Log exchange rates may be preferable.

---

### Engine 2 — Structural Break and Regime Detection

Question:

> Does one stable relationship describe USD/JPY across the full sample?

Methods may include:

- rolling correlations
- rolling coefficients
- Chow tests for pre-specified breaks
- Bai-Perron multiple-break methods
- CUSUM-style diagnostics
- Bayesian or algorithmic change-point detection

Later, use latent-state methods such as:

- Hidden Markov Models
- Gaussian mixtures
- Bayesian state-space models

Possible economic interpretations might eventually include:

- conventional macro
- carry accumulation
- carry unwind
- risk-off
- intervention risk
- monetary normalization

Do not assign economic names to statistical regimes before examining their properties.

---

### Engine 3 — Carry and Positioning

Candidate data:

- CFTC yen futures positioning
- leveraged-fund positioning
- asset-manager positioning
- rate/carry measures
- implied volatility
- FX risk reversals
- momentum
- funding conditions

Potential interaction specification:

\[
\Delta FX_t =
\beta_0 +
\beta_1 Shock_t +
\beta_2 Carry_t +
\beta_3 Shock_t \times Carry_t +
\epsilon_t
\]

Research question:

> Does market positioning amplify or dampen the exchange-rate response to policy/rate shocks?

A later composite **Yen Carry Pressure Index** may be constructed, but weights should be empirically motivated rather than chosen for aesthetics.

---

### Engine 4 — Forecasting

Only after the explanatory foundation exists.

Horizons may include:

- 1 day
- 5 days
- 20 days
- 60 days

Targets may include:

- return
- direction
- volatility
- probability distribution
- regime-transition probability

Mandatory baselines:

- random walk
- historical/simple statistical benchmark
- ARIMA or related time-series baseline
- VAR where justified
- GARCH for volatility questions
- Elastic Net

Potential nonlinear models:

- XGBoost
- LightGBM
- CatBoost
- temporal neural networks only if justified
- deep learning only if simpler approaches establish a reason

Validation must preserve chronology.

Prefer:

- expanding-window validation
- rolling-window validation
- strict out-of-sample tests

Possible metrics:

#### Regression
- MAE
- RMSE
- out-of-sample R²

#### Direction
- accuracy
- balanced accuracy
- MCC
- Brier score for probabilistic direction

#### Distribution
- calibration
- CRPS
- log score

Economic/trading metrics may be secondary diagnostics, not the primary scientific objective.

---

### Engine 5 — Causal Policy Analysis

Prediction does not identify policy effects.

Build a structured event database containing:

- BOJ decisions
- unexpected rate changes
- YCC changes
- guidance changes
- Outlook Reports
- MOF intervention
- rate checks/verbal intervention where defensibly identified
- Fed decisions
- major fiscal-policy announcements

Potential methods:

- event studies
- local projections
- SVAR
- matching/synthetic-control approaches where identification permits
- difference-in-differences only when a credible comparison exists

Local-projection concept:

\[
Y_{t+h}-Y_t =
\alpha_h+
\beta_h Shock_t+
\Gamma_h X_t+
\epsilon_{t+h}
\]

with impulse response:

\[
IRF_h = \beta_h
\]

Potential outcomes:

- USD/JPY
- JGB yields
- Nikkei/TOPIX
- bank equities
- exporter equities
- volatility
- inflation and macro variables at longer horizons

---

### Engine 6 — Central-Bank Communication AI

Use LLM/NLP methods where they are naturally useful: extracting information from policy language.

Corpus may include:

- BOJ statements
- BOJ speeches
- Outlook Reports
- meeting summaries/minutes
- MOF statements
- Fed statements
- FOMC minutes

Potential structured factors:

- hawkishness
- inflation concern
- growth concern
- currency concern
- policy uncertainty
- intervention concern

Compare:

1. dictionary methods
2. finance-oriented language models
3. embeddings + statistical downstream model
4. modern LLM structured extraction

Test whether textual signals add incremental information beyond observable market/macro variables.

LLMs must not directly decide the economic conclusion.

---

## 6. Policy Surprise Engine

Estimate market expectation prior to policy events using defensible market measures.

Concept:

\[
PolicySurprise_t = Actual_t - Expected_t
\]

For communication, a textual surprise could compare ex-ante expected tone with the observed policy statement.

Study market responses across horizons such as:

- minutes
- hours
- 1 day
- 5 days
- 20 days

This component requires careful timestamped data and should not be faked using daily data if intraday identification is claimed.

---

## 7. FX Intervention Study

Create a historical Japanese intervention database with fields such as:

- date
- timestamp when available
- direction
- size
- unilateral/coordinated
- market context
- USD/JPY before/after
- volatility
- yield differential
- positioning
- BOJ regime

Possible research question:

> Under what conditions does Japanese FX intervention produce persistent rather than temporary exchange-rate effects?

Possible moderators:

- intervention size
- coordination
- positioning
- monetary-policy alignment
- market regime
- surprise

---

## 8. Policy Scenario Simulator

This is a late-stage component.

It should not claim to identify the objectively correct Japanese policy.

Potential policy vector:

\[
a_t =
[
Rate,
FXIntervention,
JGBPolicy,
FiscalSupport,
EnergySupport
]
\]

Potential state:

\[
x_t =
[
Inflation,
Growth,
RealWages,
FX,
DebtService,
Unemployment,
FinancialConditions
]
\]

Potential transition model:

\[
x_{t+1}=f(x_t,a_t,\epsilon_t)
\]

A configurable welfare/objective function may later illustrate policy trade-offs:

\[
W =
w_g G
-w_\pi(\pi-\pi^*)^2
+w_w RW
-w_u U
-w_v V_{FX}
-w_d DebtService
\]

Weights must not be presented as objectively correct.

The simulator should show conditional scenarios and uncertainty, not deterministic policy prescriptions.

---

## 9. Data architecture

Maintain datasets appropriate to their native frequency instead of blindly forcing everything into one table.

Potential layers:

```text
market_intraday
market_daily
positioning_weekly
macro_monthly
policy_events
text_documents
intervention_events
```

A canonical daily modeling dataset can be built from these sources with explicit transformation metadata.

Crucially distinguish where possible:

- observation/reference date
- publication/release date
- vintage date

A macro observation must not enter a historical model before the market could actually have known it.

---

## 10. Statistical rigor

Check where relevant:

- stationarity
- cointegration
- autocorrelation
- heteroskedasticity
- multicollinearity
- structural breaks
- residual behavior
- parameter instability
- look-ahead bias
- data leakage
- multiple-hypothesis testing

Potential tools:

- HAC/Newey-West standard errors
- bootstrap confidence intervals
- block bootstrap
- placebo tests
- alternative variable definitions
- alternative sample windows
- robustness specifications

Do not treat SHAP or model feature importance as causal evidence.

---

## 11. Reproducibility

Important experiments should record:

```text
experiment_id
git_commit
dataset_version
feature_set
model
hyperparameters
training_window
test_window
seed
metrics
```

Potential infrastructure later:

- MLflow or W&B when useful
- DVC if dataset versioning warrants it
- GitHub Actions
- pytest
- Ruff
- mypy
- pre-commit

Do not add tooling for appearance.

---

## 12. Public narrative

The central story should initially be:

### Act I — Expected relationship
USD/JPY historically responds strongly to relative rates/yields.

### Act II — Puzzle
That relationship appears to weaken or change in recent periods.

### Act III — Measurement
Quantify when, how much, and whether the change is statistically robust.

### Act IV — Mechanisms
Test positioning, carry, risk, flows, expectations, and regime dependence.

### Act V — Policy
Estimate how BOJ/MOF actions propagate under different market states.

### Act VI — Implications
Discuss policy trade-offs and uncertainty without pretending the model identifies one correct exchange rate.

---

## 13. Definition of KAGURA v0.1

v0.1 is complete when:

- repository architecture is reproducible
- core data-source interfaces exist
- USD/JPY history is ingested and validated
- US Treasury and Japanese JGB yield data are integrated
- policy-rate data are integrated
- a small set of justified macro controls exists
- transformations are documented
- time alignment avoids obvious look-ahead bias
- rolling relationships are plotted
- baseline regressions are estimated
- structural-break candidates are analyzed
- a first Yen Fundamental Gap measure exists
- unit/data-quality tests pass
- results are documented
- the first research findings can be explained clearly

No deep learning is required for v0.1.

---

## 14. Long-run definition of KAGURA 1.0

Possible 1.0 deliverables:

- flagship research paper
- reproducible public GitHub repo
- interactive research dashboard
- historical policy/intervention event database
- regime model
- forecasting benchmark/model
- central-bank NLP analysis
- policy scenario explorer
- polished 15–20 minute presentation
- short executive summary
- Japanese-language executive summary

---

## 15. Success criterion

Success is not:

> “A Transformer predicted USD/JPY with impressive accuracy.”

A much stronger outcome is:

> “We documented a statistically and economically meaningful change in the relationship between the yen and traditional fundamentals, identified conditions under which positioning and market regimes alter that relationship, and measured how policy shocks propagate differently across those states.”

That is the standard the project should aim for.
