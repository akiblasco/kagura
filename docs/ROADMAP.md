# Project KAGURA — Roadmap

This roadmap keeps the research incremental. Every phase should produce a useful result even if later phases are never completed.

## v0.1 — Fundamentals & Structural Breaks

### Research question
Has USD/JPY structurally decoupled from the US-Japan interest-rate differential, and if so, when and by how much?

### Build
- repository foundation
- data catalog
- USD/JPY ingestion
- BOJ/Fed rates
- US Treasury/JGB yields
- core controls such as inflation, oil, and risk sentiment
- canonical time alignment
- rolling correlations
- rolling regressions
- baseline fundamental model
- structural-break analysis
- first Yen Fundamental Gap

### Output
- reproducible repo
- first core charts
- short technical writeup

---

## v0.2 — Carry, Positioning & Regimes

### Research questions
- Does yen positioning explain part of the Fundamental Gap?
- Are exchange-rate sensitivities state dependent?

### Build
- CFTC positioning
- carry measures
- volatility/momentum
- interaction regressions
- additional change-point methods
- HMM/regime prototype

### Output
**Research Note #1 or #2:** Carry Trades and the Yen Fundamental Gap

---

## v0.3 — Forecasting Benchmark

### Research question
Do nonlinear/regime-aware models improve genuinely out-of-sample forecasts?

### Build
- random-walk benchmark
- ARIMA/statistical baselines
- Elastic Net
- XGBoost/LightGBM
- strict walk-forward evaluation
- probabilistic forecasts where appropriate
- regime-aware ensemble if justified

### Output
- forecasting benchmark report
- forecast-distribution component for future dashboard

---

## v0.4 — Policy Event & Intervention Study

### Research questions
- How do BOJ surprises affect USD/JPY and Japanese assets?
- When does FX intervention have persistent effects?

### Build
- policy-event database
- intervention database
- event studies
- local projections
- initial causal-identification framework

### Output
**Research Note:** When Does Japanese FX Intervention Work?

---

## v0.5 — Central-Bank NLP

### Research question
Does central-bank communication contain incremental measurable information beyond prices/rates?

### Build
- BOJ/Fed/MOF text corpus
- dictionary baseline
- embeddings
- finance NLP baseline
- LLM structured extraction
- out-of-sample incremental-value tests

### Output
Potential standalone AI/economics paper.

---

## v0.6 — Scenario & Counterfactual Layer

### Research question
How do estimated Japanese policy trade-offs vary by state/regime?

### Build
- integrate causal estimates
- probabilistic scenario engine
- configurable economic objective/welfare weights
- uncertainty visualization

### Output
KAGURA Scenario Lab prototype.

---

## v0.7 — Public Research Dashboard

Build only after analytical outputs are credible.

Views:
- Yen Observatory
- Fundamental Gap
- Regime Monitor
- Policy Event Explorer
- Forecast Distribution
- Scenario Lab

---

## v0.8 — Flagship Paper

Working title:

> Beyond Interest-Rate Differentials: Regime-Dependent Drivers of the Japanese Yen

Include:
- motivation
- literature
- hypotheses
- data
- econometrics
- regime results
- positioning
- robustness
- interpretation
- limitations

---

## v0.9 — Presentation & Communication

Create:
- 15–20 minute research talk
- executive version
- technical appendix
- Japanese executive summary
- polished README/research site

---

## v1.0 — Public Research Release

Release only when:
- core claims are reproducible
- tests pass
- data licensing is documented
- methodology is understandable
- uncertainty and limitations are explicit
- dashboard does not overstate conclusions
- paper and repo tell one coherent story

---

# Suggested first 12 weeks

## Weeks 1–2 — Foundation
- repository
- environment
- data-source inventory
- literature notes
- baseline market dataset
- first plots
- hypotheses frozen for initial study

## Weeks 3–4 — Fundamentals
- OLS
- rolling regression
- ARDL investigation
- cointegration/VECM investigation
- Elastic Net benchmark
- Yen Fundamental Gap v1

## Weeks 5–6 — Stability
- rolling betas
- structural-break tests
- change-point detection
- sensitivity to sample period/specification

## Weeks 7–8 — Carry/Positioning
- CFTC
- carry
- volatility
- momentum
- interaction effects

## Weeks 9–10 — Forecast Benchmark
- random walk
- statistical baseline
- Elastic Net
- tree boosting
- walk-forward evaluation

## Weeks 11–12 — First Public Research Note
Produce:
- approximately 8–12 pages
- reproducible figures
- GitHub release
- concise public explanation
- optional dashboard prototype containing only validated results

---

# Current next step

Do not begin with ML.

Begin by making v0.1 trustworthy:

```text
data provenance
→ temporal alignment
→ USD/JPY + yield differentials
→ exploratory visualization
→ rolling relationship
→ fundamental baseline
→ structural-break evidence
→ residual/Fundamental Gap
```

Only then decide what additional model the evidence justifies.
