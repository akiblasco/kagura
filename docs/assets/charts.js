// KAGURA interactive charts. Each <div class="kchart" data-chart="NAME"> is drawn by CHARTS[NAME].
// Real-data charts read docs/learning/data/kagura_monthly.json, generated locally from the frozen
// vintage by `make docs-figures` (gitignored). Illustrative charts say so in their captions.
(function () {
  const COLORS = {
    light: { s1: "#2a78d6", s2: "#eb6834", s3: "#199e70" },
    dark: { s1: "#3987e5", s2: "#d95926", s3: "#1baf7a" },
  };
  let dataPromise = null;

  // Resolve the data file relative to this script, so it works at any page depth.
  const SCRIPT_SRC = document.currentScript.src;
  const dataUrl = () => new URL("../learning/data/kagura_monthly.json", SCRIPT_SRC).href;
  function loadData() {
    if (!dataPromise) dataPromise = fetch(dataUrl()).then((r) => {
      if (!r.ok) throw new Error("chart data missing: run make docs-figures");
      return r.json();
    });
    return dataPromise;
  }
  function theme() {
    const dark = document.body.getAttribute("data-md-color-scheme") === "slate";
    const css = getComputedStyle(document.body);
    const v = (n) => css.getPropertyValue(n).trim();
    return {
      dark, c: dark ? COLORS.dark : COLORS.light,
      ink: v("--k-ink"), muted: v("--k-muted"), grid: v("--k-border"), surface: v("--k-surface"),
    };
  }
  function layout(t, extra) {
    return Object.assign({
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      font: { family: "IBM Plex Sans, sans-serif", size: 12, color: t.ink },
      margin: { l: 56, r: 16, t: 8, b: 40 },
      hovermode: "x unified",
      hoverlabel: { bgcolor: t.surface, bordercolor: t.grid, font: { color: t.ink } },
      xaxis: { gridcolor: t.grid, linecolor: t.grid, zeroline: false, tickfont: { color: t.muted } },
      yaxis: { gridcolor: t.grid, linecolor: t.grid, zeroline: false, tickfont: { color: t.muted } },
      showlegend: false,
    }, extra || {});
  }
  const toDate = (m) => m + "-15";
  const CONFIG = { responsive: true, displaylogo: false, modeBarButtonsToRemove: ["lasso2d", "select2d", "autoScale2d"] };
  const axisTitle = (t, ax, text, extra) => Object.assign(layout(t)[ax], { title: { text, font: { color: t.muted } } }, extra || {});
  const legendTop = (t) => ({ showlegend: true, legend: { orientation: "h", y: 1.14, font: { color: t.ink } } });

  // Seeded normal draws, so illustrative simulations look the same on every visit
  function rng(seed) {
    let a = seed >>> 0;
    const u = () => { a = (a + 0x6d2b79f5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
    return () => Math.sqrt(-2 * Math.log(u() + 1e-12)) * Math.cos(2 * Math.PI * u());
  }
  // OLS of y on a constant and x: slope, intercept, slope t-stat (classical se)
  function ols(x, y) {
    const n = x.length, mx = x.reduce((a, b) => a + b) / n, my = y.reduce((a, b) => a + b) / n;
    let sxx = 0, sxy = 0;
    for (let i = 0; i < n; i++) { sxx += (x[i] - mx) ** 2; sxy += (x[i] - mx) * (y[i] - my); }
    const b = sxy / sxx, a = my - b * mx;
    let rss = 0;
    for (let i = 0; i < n; i++) rss += (y[i] - a - b * x[i]) ** 2;
    return { b, a, t: b / Math.sqrt(rss / (n - 2) / sxx) };
  }
  const normPdf = (z) => Math.exp(-z * z / 2) / Math.sqrt(2 * Math.PI);

  const CHARTS = {
    // Home: USD/JPY 1981–2026, nominal level or real index, with ADR 0004 events and eras
    "usdjpy-history": async (el, t) => {
      const d = await loadData();
      const mode = el.dataset.mode || "nominal";
      const x = d.month.map(toDate);
      const q0 = d.q[0];
      const y = mode === "nominal" ? d.s.map((v) => Math.exp(v / 100))
                                   : d.q.map((v) => 100 * Math.exp((v - q0) / 100));
      const name = mode === "nominal" ? "USD/JPY" : "Real index (1981-01 = 100)";
      const fmt = mode === "nominal" ? "¥%{y:.1f} per $" : "%{y:.1f}";
      const shapes = d.eras.map((e, i) => ({
        type: "rect", xref: "x", yref: "paper", x0: e.start, x1: e.end > "2030" ? x[x.length - 1] : e.end,
        y0: 0, y1: 1, fillcolor: i % 2 ? t.grid : "rgba(0,0,0,0)", opacity: 0.35, line: { width: 0 }, layer: "below",
      }));
      const eraLabels = d.eras.map((e) => ({
        xref: "x", yref: "paper", x: e.start, y: 1, xanchor: "left", yanchor: "top", showarrow: false,
        text: e.label, font: { size: 10, color: t.muted },
      }));
      const ev = d.events.map((e) => {
        const i = d.month.indexOf(e.date.slice(0, 7));
        return i < 0 ? null : { x: x[i], y: y[i], label: e.label };
      }).filter(Boolean);
      Plotly.react(el, [
        { x, y, type: "scatter", mode: "lines", name, line: { color: t.c.s1, width: 2 }, hovertemplate: fmt + "<extra></extra>" },
        { x: ev.map((e) => e.x), y: ev.map((e) => e.y), type: "scatter", mode: "markers", name: "ADR 0004 event",
          marker: { size: 9, color: t.c.s2, line: { color: t.surface, width: 2 } },
          text: ev.map((e) => e.label), hovertemplate: "%{text}<extra></extra>" },
      ], layout(t, {
        shapes, annotations: eraLabels,
        yaxis: Object.assign(layout(t).yaxis, { type: mode === "nominal" ? "log" : "linear",
          title: { text: mode === "nominal" ? "yen per dollar (log scale)" : "index", font: { color: t.muted } } }),
        hovermode: "closest",
      }), CONFIG);
    },

    // Chapter: s, x and q in log-points relative to 1981-01
    "sxq": async (el, t) => {
      const d = await loadData();
      const x = d.month.map(toDate);
      const rel = (a) => a.map((v) => (v == null ? null : v - a[0]));
      const series = [["s (nominal)", d.s, t.c.s1], ["x (relative CPI)", d.x, t.c.s3], ["q = s − x (real)", d.q, t.c.s2]];
      Plotly.react(el, series.map(([n, a, c]) => ({
        x, y: rel(a), name: n, type: "scatter", mode: "lines", line: { color: c, width: 2 },
        hovertemplate: n + ": %{y:.1f}<extra></extra>", connectgaps: false,
      })), layout(t, {
        showlegend: true, legend: { orientation: "h", y: 1.12, font: { color: t.ink } },
        yaxis: Object.assign(layout(t).yaxis, { title: { text: "log-points vs 1981-01", font: { color: t.muted } } }),
        shapes: [{ type: "line", xref: "x", yref: "paper", x0: "2022-01-01", x1: "2022-01-01", y0: 0, y1: 1, line: { color: t.muted, dash: "dot", width: 1 } }],
      }), CONFIG);
    },

    // Chapter: decomposition Δs = Δq + Δx between two months (default 2021-12 → 2026-07)
    "decomp": async (el, t) => {
      const d = await loadData();
      const a = d.month.indexOf(el.dataset.from || "2021-12"), b = d.month.indexOf(el.dataset.to || "2026-07");
      const ds = d.s[b] - d.s[a], dx = d.x[b] - d.x[a], dq = d.q[b] - d.q[a];
      const labels = ["Δq real", "Δx relative prices", "Δs nominal"];
      Plotly.react(el, [{
        type: "waterfall", orientation: "h", y: labels, x: [dq, dx, ds], measure: ["relative", "relative", "total"],
        text: [dq, dx, ds].map((v) => (v > 0 ? "+" : "") + v.toFixed(2)), textposition: "outside",
        textfont: { color: t.ink }, connector: { line: { color: t.grid } },
        increasing: { marker: { color: t.c.s2 } }, decreasing: { marker: { color: t.c.s3 } }, totals: { marker: { color: t.c.s1 } },
        hovertemplate: "%{y}: %{x:.2f} log-points<extra></extra>",
      }], layout(t, {
        margin: { l: 130, r: 24, t: 8, b: 40 }, hovermode: "closest",
        xaxis: Object.assign(layout(t).xaxis, { range: [Math.min(0, ds, dq) - 2, Math.max(ds, dq, ds - dx) * 1.18], title: { text: "log-points, " + d.month[a] + " → " + d.month[b], font: { color: t.muted } } }),
        yaxis: Object.assign(layout(t).yaxis, { autorange: "reversed" }),
      }), CONFIG);
    },

    // Chapter (illustrative): percentage change vs log-point change
    "log-vs-pct": async (el, t) => {
      const r = [], lp = [];
      for (let p = -60; p <= 150; p += 1) { r.push(p); lp.push(100 * Math.log(1 + p / 100)); }
      Plotly.react(el, [
        { x: r, y: r, name: "if log-points equalled %", mode: "lines", line: { color: t.muted, dash: "dot", width: 1.5 }, hovertemplate: "%{x}%<extra></extra>" },
        { x: r, y: lp, name: "100·ln(1 + r)", mode: "lines", line: { color: t.c.s1, width: 2.5 }, hovertemplate: "%{x}% change = %{y:.1f} log-points<extra></extra>" },
      ], layout(t, {
        showlegend: true, legend: { orientation: "h", y: 1.12, font: { color: t.ink } }, hovermode: "closest",
        xaxis: Object.assign(layout(t).xaxis, { title: { text: "percentage change r (%)", font: { color: t.muted } } }),
        yaxis: Object.assign(layout(t).yaxis, { title: { text: "log-point change", font: { color: t.muted } } }),
      }), CONFIG);
    },

    // Journal: simulated null rejection ranges at nominal 2.5 % (ADR 0008 §4–§5, synthetic data)
    "size-ranges": async (el, t) => {
      const rows = [
        ["Andrews–Kim P test", 0.047, 0.107],
        ["WW FM-OLS, Andrews bw, d I(1)", 0.018, 0.028],
        ["WW FM-OLS, Andrews bw, d I(0)", 0.043, 0.077],
        ["WW D-OLS, d I(1)", 0.02, 0.23],
        ["WW FM-OLS, fixed NW bw, d I(1)", 0.02, 0.90],
      ];
      const traces = rows.map(([n, lo, hi]) => ({
        x: [lo, hi], y: [n, n], mode: "lines+markers", line: { color: t.c.s1, width: 4 },
        marker: { size: 9, color: t.c.s1, line: { color: t.surface, width: 2 } },
        hovertemplate: n + ": %{x:.3f}<extra></extra>",
      }));
      const vline = (v, txt, dash) => ({ type: "line", xref: "x", yref: "paper", x0: v, x1: v, y0: 0, y1: 1, line: { color: t.muted, dash, width: 1 } });
      Plotly.react(el, traces, layout(t, {
        margin: { l: 210, r: 16, t: 24, b: 44 }, hovermode: "closest",
        xaxis: Object.assign(layout(t).xaxis, { type: "log", range: [Math.log10(0.012), Math.log10(1)], tickvals: [0.025, 0.05, 0.1, 0.25, 0.5, 0.9], tickangle: 0,
          ticktext: ["2.5%", "5%", "10%", "25%", "50%", "90%"], title: { text: "simulated null rejection rate (log scale)", font: { color: t.muted } } }),
        shapes: [vline(0.025, "nominal", "solid"), vline(0.0375, "screen", "dash")],
        annotations: [
          { x: Math.log10(0.025), y: 1.02, xref: "x", yref: "paper", text: "nominal", showarrow: false, font: { size: 10, color: t.muted }, yanchor: "bottom" },
          { x: Math.log10(0.0375), y: 1.02, xref: "x", yref: "paper", text: "screen", showarrow: false, font: { size: 10, color: t.muted }, yanchor: "bottom", xanchor: "left" },
        ],
      }), CONFIG);
    },

    // Chapter 2: monthly Δs against Δd2 in two eras, with each era's OLS line (real data)
    "monthly-scatter": async (el, t) => {
      const d = await loadData();
      const eras = [["2013–2021", "2013-01", "2021-12", t.c.s1], ["2022–2026-07", "2022-01", "9999", t.c.s2]];
      const traces = [];
      eras.forEach(([name, lo, hi, c]) => {
        const xs = [], ys = [], lab = [];
        for (let i = 1; i < d.month.length; i++) {
          const m = d.month[i];
          if (m < lo || m > hi || d.d2[i] == null || d.d2[i - 1] == null) continue;
          xs.push(d.d2[i] - d.d2[i - 1]); ys.push(d.s[i] - d.s[i - 1]); lab.push(m);
        }
        const f = ols(xs, ys), lo2 = Math.min(...xs), hi2 = Math.max(...xs);
        traces.push({ x: xs, y: ys, text: lab, mode: "markers", type: "scatter", name: name + " months",
          marker: { size: 8, color: c, opacity: 0.75, line: { color: t.surface, width: 1 } },
          hovertemplate: "%{text}<br>Δd %{x:.2f} pp, Δs %{y:.2f}<extra></extra>" });
        traces.push({ x: [lo2, hi2], y: [f.a + f.b * lo2, f.a + f.b * hi2], mode: "lines", type: "scatter",
          name: name + " fit: slope " + f.b.toFixed(2), line: { color: c, width: 2.5 }, hoverinfo: "skip" });
      });
      Plotly.react(el, traces, layout(t, Object.assign(legendTop(t), {
        hovermode: "closest", margin: { l: 56, r: 16, t: 40, b: 44 },
        xaxis: axisTitle(t, "xaxis", "monthly change in 2Y differential Δd (pp)", { zeroline: true, zerolinecolor: t.grid }),
        yaxis: axisTitle(t, "yaxis", "monthly change in USD/JPY Δs (log-points)", { zeroline: true, zerolinecolor: t.grid }),
      })), CONFIG);
    },

    // Chapter 3: the level of s and its monthly change, stacked (real data)
    "levels-changes": async (el, t) => {
      const d = await loadData();
      const x = d.month.map(toDate);
      const lvl = d.s.map((v) => v - d.s[0]);
      const chg = d.s.map((v, i) => (i ? v - d.s[i - 1] : null));
      Plotly.react(el, [
        { x, y: lvl, type: "scatter", mode: "lines", name: "level", line: { color: t.c.s1, width: 2 }, hovertemplate: "level %{y:.1f}<extra></extra>" },
        { x, y: chg, type: "scatter", mode: "lines", name: "monthly change", xaxis: "x2", yaxis: "y2", line: { color: t.c.s3, width: 1.2 }, hovertemplate: "change %{y:.2f}<extra></extra>" },
      ], layout(t, {
        margin: { l: 56, r: 16, t: 24, b: 32 },
        xaxis: Object.assign(layout(t).xaxis, { anchor: "y", showticklabels: false }),
        xaxis2: Object.assign(layout(t).xaxis, { anchor: "y2", matches: "x" }),
        yaxis: axisTitle(t, "yaxis", "s − s₁₉₈₁₋₀₁", { domain: [0.55, 1] }),
        yaxis2: axisTitle(t, "yaxis", "Δs", { domain: [0, 0.42] }),
        annotations: [
          { xref: "paper", yref: "paper", x: 0, y: 1.04, showarrow: false, xanchor: "left", text: "Level of s: wanders, no fixed mean", font: { size: 11, color: t.muted } },
          { xref: "paper", yref: "paper", x: 0, y: 0.47, showarrow: false, xanchor: "left", text: "Monthly change Δs: fluctuates around zero", font: { size: 11, color: t.muted } },
        ],
      }), CONFIG);
    },

    // Chapter 3 (illustrative): one shock sequence fed through AR(1) processes with different φ
    "rw-vs-ar": async (el, t) => {
      const z = rng(7), T = 300, e = Array.from({ length: T }, z);
      const path = (phi) => { const y = [0]; for (let i = 1; i < T; i++) y.push(phi * y[i - 1] + e[i]); return y; };
      const idx = [...Array(T).keys()];
      const series = [["φ = 1 (random walk, unit root)", 1, t.c.s1], ["φ = 0.95 (persistent, stationary)", 0.95, t.c.s2], ["φ = 0.5 (quickly mean-reverting)", 0.5, t.c.s3]];
      Plotly.react(el, series.map(([n, p, c]) => ({ x: idx, y: path(p), name: n, mode: "lines", line: { color: c, width: 2 }, hovertemplate: n + ": %{y:.1f}<extra></extra>" })),
        layout(t, Object.assign(legendTop(t), { margin: { l: 48, r: 16, t: 48, b: 40 },
          xaxis: axisTitle(t, "xaxis", "period"), yaxis: axisTitle(t, "yaxis", "y_t", { zeroline: true, zerolinecolor: t.muted }) })), CONFIG);
    },

    // Chapter 3 (illustrative): t-statistics from regressing independent series on each other
    "spurious": async (el, t) => {
      const z = rng(11), R = 1000, T = 200, tw = [], tr = [];
      for (let r = 0; r < R; r++) {
        const ex = [], ey = [], rx = [0], ry = [0];
        for (let i = 0; i < T; i++) { const a = z(), b = z(); ex.push(a); ey.push(b); if (i) { rx.push(rx[i - 1] + a); ry.push(ry[i - 1] + b); } }
        tw.push(ols(ex, ey).t); tr.push(ols(rx, ry).t);
      }
      const share = (a) => (100 * a.filter((v) => Math.abs(v) > 1.96).length / a.length).toFixed(0) + " %";
      const bins = { start: -40, end: 40, size: 1 };
      Plotly.react(el, [
        { x: tw, type: "histogram", xbins: bins, name: "independent white noise: |t| > 1.96 in " + share(tw), marker: { color: t.c.s1, line: { color: t.surface, width: 1 } }, opacity: 0.85 },
        { x: tr, type: "histogram", xbins: bins, name: "independent random walks: |t| > 1.96 in " + share(tr), marker: { color: t.c.s2, line: { color: t.surface, width: 1 } }, opacity: 0.7 },
      ], layout(t, Object.assign(legendTop(t), { barmode: "overlay", hovermode: "closest", margin: { l: 56, r: 16, t: 56, b: 44 },
        xaxis: axisTitle(t, "xaxis", "OLS t-statistic of the slope (classical se), 1,000 simulations, T = 200", { range: [-40, 40] }),
        yaxis: axisTitle(t, "yaxis", "number of simulations"),
        shapes: [-1.96, 1.96].map((v) => ({ type: "line", xref: "x", yref: "paper", x0: v, x1: v, y0: 0, y1: 1, line: { color: t.muted, dash: "dot", width: 1 } })),
      })), CONFIG);
    },

    // Chapter 4: H1a test S on the z scale. δ̂ and se(δ̂) from notebook 02 (−0.241770, 0.461512)
    "z-test": async (el, t) => {
      const zObs = -0.241770 / 0.461512, c = 1.959964, xs = [], ys = [];
      for (let v = -4; v <= 4.0001; v += 0.02) { xs.push(v); ys.push(normPdf(v)); }
      const area = (lo, hi) => { const ax = [lo], ay = [0]; xs.forEach((v, i) => { if (v >= lo && v <= hi) { ax.push(v); ay.push(ys[i]); } }); ax.push(hi); ay.push(0); return [ax, ay]; };
      const [px, py] = area(-4, zObs), [rx, ry] = area(-4, -c);
      Plotly.react(el, [
        { x: px, y: py, fill: "toself", mode: "lines", line: { width: 0 }, fillcolor: t.c.s1, opacity: 0.35, name: "p_S = Φ(z) = 0.30", hoverinfo: "skip" },
        { x: rx, y: ry, fill: "toself", mode: "lines", line: { width: 0 }, fillcolor: t.c.s2, opacity: 0.8, name: "rejection region of S (2.5 %)", hoverinfo: "skip" },
        { x: xs, y: ys, mode: "lines", line: { color: t.ink, width: 2 }, name: "N(0, 1): distribution of z if δ = 0", hovertemplate: "z = %{x:.2f}<extra></extra>" },
      ], layout(t, Object.assign(legendTop(t), { hovermode: "closest", margin: { l: 48, r: 16, t: 64, b: 44 },
        xaxis: axisTitle(t, "xaxis", "z = δ̂ / se(δ̂)"), yaxis: axisTitle(t, "yaxis", "density"),
        shapes: [{ type: "line", xref: "x", yref: "paper", x0: zObs, x1: zObs, y0: 0, y1: 0.92, line: { color: t.c.s1, width: 2.5 } }],
        annotations: [{ x: zObs, y: 0.92, yref: "paper", text: "observed z = −0.52", showarrow: false, yanchor: "bottom", font: { color: t.ink, size: 11 } },
          { x: -c, y: 0.12, text: "−1.96", showarrow: false, xanchor: "right", font: { color: t.muted, size: 10 } }],
      })), CONFIG);
    },

    // Chapter 4 / cheatsheet: 95 % intervals for δ at three materiality thresholds (notebook 02 output)
    "delta-intervals": async (el, t) => {
      const rows = [["decline ≥ ¼ (sensitivity)", -0.778821, -1.744951, 0.187309, "inconclusive"],
        ["decline ≥ ⅓ (primary)", -0.241770, -1.146316, 0.662777, "inconclusive"],
        ["decline ≥ ½ (sensitivity)", 0.832333, 0.039577, 1.625089, "decline ruled out"]];
      Plotly.react(el, rows.map(([n, est, lo, hi, v], i) => ({
        x: [lo, est, hi], y: [n, n, n], mode: "lines+markers", type: "scatter", name: n,
        line: { color: i === 1 ? t.c.s1 : t.muted, width: 4 }, marker: { size: [9, 13, 9], color: i === 1 ? t.c.s1 : t.muted, line: { color: t.surface, width: 2 } },
        hovertemplate: n + "<br>δ̂ = " + est.toFixed(2) + ", 95 % [" + lo.toFixed(2) + ", " + hi.toFixed(2) + "]<br>" + v + "<extra></extra>",
      })), layout(t, { hovermode: "closest", margin: { l: 170, r: 110, t: 16, b: 44 },
        xaxis: axisTitle(t, "xaxis", "δ = β_new − (1 − threshold)·β_ref, % per pp"),
        shapes: [{ type: "line", xref: "x", yref: "paper", x0: 0, x1: 0, y0: 0, y1: 1, line: { color: t.ink, width: 1.5 } }],
        annotations: rows.map(([n, , , hi, v]) => ({ x: hi, y: n, text: "  " + v, showarrow: false, xanchor: "left", font: { size: 11, color: t.ink } })),
      }), CONFIG);
    },

    // Chapter 4 (illustrative): 50 simulated 95 % intervals for a known mean
    "ci-coverage": async (el, t) => {
      const z = rng(3), mu = 2, n = 25, K = 50, hit = { x: [], y: [], lo: [], hi: [] }, miss = { x: [], y: [], lo: [], hi: [] };
      for (let k = 0; k < K; k++) {
        let s = 0, ss = 0; const v = [];
        for (let i = 0; i < n; i++) { const d = mu + z(); v.push(d); s += d; }
        const m = s / n; v.forEach((d) => (ss += (d - m) ** 2));
        const h = 2.064 * Math.sqrt(ss / (n - 1) / n), g = m - h <= mu && mu <= m + h ? hit : miss;
        g.x.push(m); g.y.push(k + 1); g.lo.push(m - h); g.hi.push(m + h);
      }
      const tr = (g, name, c) => ({ x: g.x, y: g.y, mode: "markers", type: "scatter", name: name + " (" + g.x.length + ")",
        marker: { color: c, size: 7 }, error_x: { type: "data", symmetric: false, array: g.hi.map((h, i) => h - g.x[i]), arrayminus: g.x.map((m, i) => m - g.lo[i]), color: c, thickness: 2, width: 0 },
        hovertemplate: "sample %{y}: [%{customdata[0]:.2f}, %{customdata[1]:.2f}]<extra></extra>", customdata: g.lo.map((l, i) => [l, g.hi[i]]) });
      Plotly.react(el, [tr(hit, "covers the true mean", t.c.s1), tr(miss, "misses", t.c.s2)], layout(t, Object.assign(legendTop(t), {
        hovermode: "closest", margin: { l: 48, r: 16, t: 40, b: 44 },
        xaxis: axisTitle(t, "xaxis", "sample mean and 95 % interval (true mean = 2)"), yaxis: axisTitle(t, "yaxis", "sample number"),
        shapes: [{ type: "line", xref: "x", yref: "paper", x0: mu, x1: mu, y0: 0, y1: 1, line: { color: t.ink, dash: "dot", width: 1.5 } }],
      })), CONFIG);
    },
  };

  function drawAll() {
    if (!window.Plotly) return;
    const t = theme();
    document.querySelectorAll(".kchart[data-chart]").forEach((el) => {
      const f = CHARTS[el.dataset.chart];
      if (f) f(el, t).catch((e) => { el.innerHTML = '<p class="kchart-error">' + e.message + "</p>"; });
    });
  }
  // Toggle buttons: <button data-target="ID" data-mode="real">
  document.addEventListener("click", (ev) => {
    const b = ev.target.closest(".kchart-toggle button");
    if (!b) return;
    const el = document.getElementById(b.dataset.target);
    el.dataset.mode = b.dataset.mode;
    b.parentElement.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", x === b));
    CHARTS[el.dataset.chart](el, theme());
  });
  new MutationObserver(drawAll).observe(document.body, { attributes: true, attributeFilter: ["data-md-color-scheme"] });
  if (window.document$) window.document$.subscribe(drawAll); else document.addEventListener("DOMContentLoaded", drawAll);
})();
