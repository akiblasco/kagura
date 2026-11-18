ADR 0007 break estimation, Phase A (ADR 0011). exploratory (ADR 0007), Phase A (ADR 0011).

Everything here is descriptive or model selection. Nothing is a tested claim.
- Break dates: least-squares partitions for a given m. They locate changes in a linear fit,
  not economic regimes (ADR 0007 L1).
- BIC and LWZ: model-selection results under the model's assumptions; both are shown and
  neither is "the number of breaks". Sequential-rule counts are withheld (ADR 0011 §4).
- Bai intervals: nominal level only, coverage not established; simulated coverage at nominal 95 % ranged from 76.5 % (ADR 0011 §6: T = 1,000, shift 0.15) to 97.2 % (ADR 0012 §3.2: full grid, shift 0.60, eta = 4); not a bound for these estimates. The 90 %/95 % labels are nominal, not validated coverage.
  Coverage on real data, where m and the error process are unknown, may be lower.
- Not computed: sup F(k), UDmax, WDmax, sequential tests, WF bootstrap (Phase B, withheld).
- The ADR 0007 §9.1 critical-value check FAILED as frozen (11/72; 9/66 in the frozen scope)
  and remains failed (ADR 0011 §1).
