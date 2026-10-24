"""Synthetic-only pilot code for ADR 0008 rev 3. Never reads KAGURA data."""
import itertools
import numpy as np
from scipy import stats

# ---------------------------------------------------------------- Andrews–Kim P

def ak_p(y, X, T, m, gap=None, alpha=0.025):
    """AK (2006) P test, eqs. (7)-(15); optional matched gap at window position `gap` (0-based)."""
    N = T + m
    keep = np.ones(N, bool)
    if gap is not None:
        keep[T + gap] = False
    b = np.linalg.lstsq(X[keep], y[keep], rcond=None)[0]
    r = (y - X @ b)[T:]
    w = np.ones(m, bool)
    if gap is not None:
        w[gap] = False
    P = (r[w] ** 2).sum()

    Xp, yp = X[:T], y[:T]
    z = lambda a: np.concatenate([np.zeros((1,) + a.shape[1:]), a.cumsum(0)])
    xx, xy, yy = np.einsum("ti,tj->tij", Xp, Xp), Xp * yp[:, None], yp**2
    cxx, cxy, cyy = z(xx), z(xy), z(yy)
    h, J = -(-m // 2), T - m + 1
    j = np.arange(J)
    G = cxx[T] - (cxx[j + h] - cxx[j])            # leave-ceil(m/2)-out, eq. (10)
    g = cxy[T] - (cxy[j + h] - cxy[j])
    B = np.linalg.solve(G, g[..., None])[..., 0]
    Sxx, Sxy, Syy = cxx[j + m] - cxx[j], cxy[j + m] - cxy[j], cyy[j + m] - cyy[j]
    if gap is not None:
        Sxx, Sxy, Syy = Sxx - xx[j + gap], Sxy - xy[j + gap], Syy - yy[j + gap]
    Pj = Syy - 2 * (B * Sxy).sum(1) + np.einsum("ji,jik,jk->j", B, Sxx, B)
    rej = (P > Pj).sum() >= (1 - alpha) * J          # eq. (14)
    return P, (P <= Pj).mean(), bool(rej), Pj


def ak_p_direct(y, X, T, m, gap=None):
    """Slow reference implementation of ak_p, for checking."""
    keep = np.ones(T + m, bool)
    if gap is not None:
        keep[T + gap] = False
    b = np.linalg.lstsq(X[keep], y[keep], rcond=None)[0]
    w = np.arange(T, T + m)[keep[T:]]
    P = ((y[w] - X[w] @ b) ** 2).sum()
    h, Pj = -(-m // 2), []
    for j in range(T - m + 1):
        est = np.r_[0:j, j + h:T]
        bj = np.linalg.lstsq(X[est], y[est], rcond=None)[0]
        win = [t for t in range(j, j + m) if gap is None or t != j + gap]
        Pj.append(((y[win] - X[win] @ bj) ** 2).sum())
    return P, np.array(Pj)

# ---------------------------------------------------------------- innovations

def innov(rng, n, law, garch=(0.10, 0.85), burn=500):
    if law == "normal":
        return rng.standard_normal(n)
    if law == "t5":
        return rng.standard_t(5, n) * np.sqrt(3 / 5)
    if law == "garch":
        a, b = garch
        z = rng.standard_normal(n + burn)
        e, s2 = np.empty(n + burn), 1.0
        for t in range(n + burn):
            e[t] = np.sqrt(s2) * z[t]
            s2 = (1 - a - b) + a * e[t] ** 2 + b * s2
        return e[burn:]
    raise ValueError(law)


def ar1(rng, eps, rho, burn=1000):
    """Stationary AR(1) from given innovations (burn-in drawn N(0,1) and discarded)."""
    if rho >= 1:
        return eps.cumsum()
    e = np.r_[rng.standard_normal(burn), eps]
    u = np.empty_like(e)
    u[0] = e[0] / np.sqrt(1 - rho**2) if rho < 1 else e[0]
    for t in range(1, len(e)):
        u[t] = rho * u[t - 1] + e[t]
    return u[burn:]


def ak_dgp(rng, N, rho, law="normal", endog=0.0, drift=0.0, dtype="I1",
           pre_var_break=None, T=None, alt=None, sig_u=None):
    """s = u (beta = 0 under H0; LS residuals are invariant to beta). X = (1, x, d)."""
    psi, xi, eta, zeta = (innov(rng, N, law) for _ in range(4))
    eps = np.sqrt(1 - endog) * psi + np.sqrt(endog) * eta
    if pre_var_break is not None:                      # variance x2 for t < pre_var_break
        eps[:pre_var_break] *= np.sqrt(2)
    u = ar1(rng, eps, rho)
    x = (drift + np.sqrt(1 - endog) * xi + np.sqrt(endog) * eta).cumsum()
    if dtype == "I1":
        d = zeta.cumsum()
    else:                                              # stationary AR(.97), exogenous (AK S(c))
        d = ar1(rng, zeta, 0.97)
    if alt is not None:
        u = apply_alt(rng, u, T, alt, sig_u if sig_u is not None else (1 / np.sqrt(1 - rho**2) if rho < 1 else 1.0), law)
    return u, np.column_stack([np.ones(N), x, d])


def apply_alt(rng, u, T, alt, sig, law):
    u = u.copy(); m = len(u) - T
    kind, size = alt
    if kind == "shift":
        u[T:] += size * sig
    elif kind == "ramp":
        u[T:] += np.linspace(0, size, m) * sig
    elif kind == "rw":                                 # AK eq. (37)-type, factor sqrt(2)
        u[T:] += np.sqrt(2) * innov(rng, m, law).cumsum()
    elif kind == "var":
        u[T:] *= np.sqrt(size)
    elif kind == "early_shift":                        # starts `24` months before T
        u[T - 24:] += size * sig
    return u

# ---------------------------------------------------------------- ARDL / bounds

TAX_ROWS_LEVEL = [99, 195, 399, 465]   # 1989-04, 1997-04, 2014-04, 2019-10 with level index 0 = 1981-01
MAXLAG = 12


def full_design(s, x, d, taxes=TAX_ROWS_LEVEL, tax_window=1):
    """All candidate UECM columns on rows t = 12..N-1 (n = N-12). Column blocks returned by name."""
    N = len(s)
    rows = np.arange(MAXLAG, N)
    D = lambda v: np.r_[np.nan, np.diff(v)]
    ds, dx, dd = D(s), D(x), D(d)
    cols, names = [np.ones(len(rows))], ["const"]
    mon = rows % 12
    for k in range(1, 12):
        cols.append((mon == k) - 1 / 12); names.append(f"sea{k}")
    for e in taxes:
        for jj in range(tax_window):
            cols.append((rows == e + jj).astype(float)); names.append(f"tax{e}+{jj}")
    for v, nm in ((s, "s"), (x, "x"), (d, "d")):
        cols.append(v[rows - 1]); names.append(f"L.{nm}")
    for i in range(1, MAXLAG):
        cols.append(ds[rows - i]); names.append(f"ds{i}")
    for v, nm in ((dx, "dx"), (dd, "dd")):
        for j in range(MAXLAG):
            cols.append(v[rows - j]); names.append(f"{nm}{j}")
    X = np.column_stack(cols)
    return ds[rows], X, names


def idx_for(names, p, qx, qd):
    base = [i for i, n in enumerate(names) if n == "const" or n.startswith(("sea", "tax", "L."))]
    sr = ([names.index(f"ds{i}") for i in range(1, p)] + [names.index(f"dx{j}") for j in range(qx)]
          + [names.index(f"dd{j}") for j in range(qd)])
    return np.array(base + sr)


def _ols_gram(G, Xy, yy, S):
    Gs = G[np.ix_(S, S)]
    b = np.linalg.solve(Gs, Xy[S])
    return b, yy - b @ Xy[S], Gs


def bg_pvalue(e, Xs, lags=12):
    n = len(e)
    E = np.column_stack([np.r_[np.zeros(l), e[:-l]] for l in range(1, lags + 1)])
    Z = np.column_stack([Xs, E])
    r = e - Z @ np.linalg.lstsq(Z, e, rcond=None)[0]
    R2 = 1 - (r @ r) / ((e - e.mean()) @ (e - e.mean()))
    return stats.chi2.sf(n * R2, lags)


def f_t(y, X, names, S, G=None, Xy=None, yy=None):
    if G is None:
        G, Xy, yy = X.T @ X, X.T @ y, y @ y
    n = len(y)
    b, rss_u, Gs = _ols_gram(G, Xy, yy, S)
    lv = [k for k, i in enumerate(S) if names[i].startswith("L.")]
    R = np.array([i for k, i in enumerate(S) if k not in lv])
    _, rss_r, _ = _ols_gram(G, Xy, yy, R)
    K = len(S)
    s2 = rss_u / (n - K)
    F = ((rss_r - rss_u) / 3) / s2
    kphi = [k for k, i in enumerate(S) if names[i] == "L.s"][0]
    tphi = b[kphi] / np.sqrt(s2 * np.linalg.inv(Gs)[kphi, kphi])
    return F, tphi, b, S


ORDERS = list(itertools.product(range(1, MAXLAG + 1), repeat=3))


def select(y, X, names, bg_alpha=0.05):
    """AIC over (p,qx,qd) in 1..12^3 on the common sample, among models with BG(12) p >= bg_alpha."""
    n = len(y)
    G, Xy, yy = X.T @ X, X.T @ y, y @ y
    aic = np.empty(len(ORDERS)); Ss = []
    for k, (p, qx, qd) in enumerate(ORDERS):
        S = idx_for(names, p, qx, qd); Ss.append(S)
        _, rss, _ = _ols_gram(G, Xy, yy, S)
        aic[k] = n * np.log(rss / n) + 2 * len(S)
    for k in np.argsort(aic):
        S = Ss[k]
        b, _, _ = _ols_gram(G, Xy, yy, S)
        e = y - X[:, S] @ b
        if bg_pvalue(e, X[:, S]) >= bg_alpha:
            F, t, _, _ = f_t(y, X, names, S, G, Xy, yy)
            return ORDERS[k], F, t
    return None, np.nan, np.nan


def bounds_null_data(rng, N, bound, dgp="iid"):
    """PSS null: no levels relationship. bound='upper' -> x,d I(1); 'lower' -> x,d I(0)."""
    law = {"garch": "garch", "t5": "t5"}.get(dgp, "normal")
    eps = innov(rng, N, law)
    if dgp == "dyn":
        ds = ar1(rng, eps, 0.3); xi = ar1(rng, rng.standard_normal(N), 0.4)
        zi = ar1(rng, rng.standard_normal(N), 0.3)
        xi = xi + 0.5 * np.tile(np.r_[np.linspace(-1, 1, 6), np.linspace(1, -1, 6)], N // 12 + 1)[:N]
    else:
        ds, xi, zi = eps, rng.standard_normal(N), rng.standard_normal(N)
    drift = 0.5 if dgp == "drift" else 0.0
    s = ds.cumsum()
    if bound == "upper":
        x, d = (xi + drift).cumsum(), zi.cumsum()
    else:
        x, d = xi, zi
    return s, x, d
