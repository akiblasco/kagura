"""Wagner–Wied (2017) cointegration monitoring, FM-OLS and D-OLS, intercept only. Synthetic use only.

Detector follows cointmonitoR 0.1.0 / WW (2014 DP) eq. (37): calibration term subtracted, abs, g(s)=s^3.
"""
import numpy as np


def bartlett_lrv(e, bw):
    """One-sided Delta = sum_{j>=0} w_j Gamma_j (Gamma_j = E[e_{t-j} e_t']) and two-sided Omega."""
    T = len(e)
    G = lambda j: e[:T - j].T @ e[j:] / T
    L = int(np.floor(bw))
    Delta = G(0).copy()
    for j in range(1, L + 1):
        Delta += (1 - j / (bw + 1)) * G(j)
    Omega = Delta + Delta.T - G(0)
    return Omega, Delta


def bw_andrews_ar1(e, cap=0.97):
    """Andrews (1991) AR(1) plug-in bandwidth for the Bartlett kernel (standard formula; not re-read this session)."""
    T = len(e); num = den = 0.0
    for a in e.T:
        rho = (a[1:] @ a[:-1]) / (a[:-1] @ a[:-1]); rho = min(rho, cap)
        s2 = np.mean((a[1:] - rho * a[:-1]) ** 2)
        num += 4 * rho**2 * s2**2 / ((1 - rho) ** 6 * (1 + rho) ** 2)
        den += s2**2 / (1 - rho) ** 4
    return min(1.1447 * (num / den * T) ** (1 / 3), T - 1)


BW_RULES = {
    "andrews": bw_andrews_ar1,
    "andrews_nocap": lambda e: bw_andrews_ar1(e, cap=0.9999),   # cointReg: no cap; only bounded by T-1
    "nw": lambda e: np.floor(4 * (len(e) / 100) ** (2 / 9)),
    "large": lambda e: np.floor(12 * (len(e) / 100) ** (1 / 4)),
}


def fmols(y, X, D, bw_rule="andrews"):
    """Phillips–Hansen FM-OLS on the given (calibration) sample. X: (T,k) I(1); D: (T,p) deterministic."""
    v = np.diff(X, axis=0)
    Z = np.column_stack([D, X])
    b_ols = np.linalg.lstsq(Z, y, rcond=None)[0]
    u = (y - Z @ b_ols)[1:]
    eta = np.column_stack([u, v])
    bw = BW_RULES[bw_rule](eta)
    Om, De = bartlett_lrv(eta, bw)
    Ovv, Ovu, Ouu = Om[1:, 1:], Om[1:, 0], Om[0, 0]
    corr = np.linalg.solve(Ovv, Ovu)
    yp = y[1:] - v @ corr
    Dvu_plus = De[1:, 0] - De[1:, 1:] @ corr
    Zs = Z[1:]; n = len(yp); p = D.shape[1]
    rhs = Zs.T @ yp; rhs[p:] -= n * Dvu_plus
    theta = np.linalg.solve(Zs.T @ Zs, rhs)
    w2 = Ouu - Ovu @ corr
    return theta, corr, w2, Zs, bw


def dols(y, X, D, k1=2, k2=2):
    """D-OLS with k1 leads, k2 lags on the given sample; returns coefficients and the lead/lag builder."""
    def design(Xf, Df):
        v = np.vstack([np.full((1, Xf.shape[1]), np.nan), np.diff(Xf, axis=0)])
        T = len(Xf); cols = [Df, Xf]
        for j in range(-k1, k2 + 1):                       # Delta X_{t-j}
            sh = np.full_like(v, np.nan)
            if j >= 0: sh[j:] = v[:T - j]
            else: sh[:T + j] = v[-j:]
            cols.append(sh)
        return np.column_stack(cols)
    Z = design(X, D); ok = ~np.isnan(Z).any(1)
    theta = np.linalg.lstsq(Z[ok], y[ok], rcond=None)[0]
    return theta, design


def detector_path(uplus, M, T):
    """Package/DP form: [T^-1 sum_{M<i<=t} (S_i/sqrt T)^2 - T^-1 sum_{i<=M} (S_i/sqrt T)^2] (before /omega)."""
    S = np.cumsum(np.nan_to_num(uplus))                    # missing increments contribute 0
    sd = (S / np.sqrt(T)) ** 2 / T
    return np.cumsum(sd[M:]) - sd[:M].sum()


def ww_stat(y, X, M, est="FM", bw_rule="andrews", gap=None):
    """sup_s |H(s)| / s^3 over s = (M+1..T)/T. gap: absolute index of a missing X row (x component)."""
    T = len(y); D = np.ones((T, 1))
    Xg = X.copy()
    if gap is not None:
        Xg[gap, 0] = np.nan
    theta, corr, w2, _, bw = fmols(y[:M], X[:M], D[:M], bw_rule)       # gap is in the window, not calibration
    if est == "FM":
        v = np.vstack([np.full((1, X.shape[1]), np.nan), np.diff(Xg, axis=0)])
        up = y - v @ corr - np.column_stack([D, Xg]) @ theta
        up[0] = 0.0
    else:
        thD, design = dols(y[:M], X[:M], D[:M])
        Z = design(Xg, D)
        up = y - Z @ thD
        up[:3] = 0.0                                            # leading rows without lags (package zero-fills)
        tail = np.isnan(Z).any(1); tail[:3] = False
        up[tail] = np.nan                                       # rows touching the gap or the end leads -> 0
    H = detector_path(up, M, T) / w2
    s = np.arange(M + 1, T + 1) / T
    return np.max(np.abs(H) / s**3)
