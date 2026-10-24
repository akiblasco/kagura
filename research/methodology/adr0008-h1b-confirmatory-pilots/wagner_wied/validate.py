import numpy as np, pandas as pd, statsmodels.api as sm
from wwlib import fmols, dols, detector_path, ww_stat
rng = np.random.default_rng(42)
# 1. detector vs direct loop
u = rng.standard_normal(547); M, T = 492, 547
S = np.cumsum(u); direct = np.array([sum((S[i]/np.sqrt(T))**2/T for i in range(M, t)) - sum((S[i]/np.sqrt(T))**2/T for i in range(M)) for t in range(M+1, T+1)])
print("1 detector max abs diff:", np.abs(detector_path(u, M, T) - direct).max())
# 2. D-OLS vs pandas-shift design + statsmodels
X = rng.standard_normal((300, 2)).cumsum(0); y = 1 + X @ [1, 2] + rng.standard_normal(300)
th, _ = dols(y, X, np.ones((300, 1)))
df = pd.DataFrame(X, columns=["x", "d"]); dv = df.diff()
Z = pd.concat([pd.Series(1.0, index=df.index, name="c"), df] + [dv.shift(j).add_suffix(f"_{j}") for j in range(-2, 3)], axis=1).dropna()
print("2 D-OLS max abs coef diff vs statsmodels:", np.abs(th - sm.OLS(y[Z.index], Z).fit().params.values).max())
# 3. FM-OLS properties: endogenous, serially correlated; T=500
R = 2000; bo = []; bf = []; tf = []
for r in range(R):
    e = rng.standard_normal((501, 3)); v = np.empty((501, 2)); uu = np.empty(501); v[0] = e[0, 1:]; uu[0] = e[0, 0]
    for t in range(1, 501):
        v[t] = 0.5 * v[t-1] + e[t, 1:]; uu[t] = 0.6 * uu[t-1] + e[t, 0] + 0.8 * e[t, 1]       # endogeneity via e1
    X = v.cumsum(0)[1:]; y = X @ [1., 2.] + uu[1:]
    Zo = np.column_stack([np.ones(500), X]); bo.append(np.linalg.lstsq(Zo, y, rcond=None)[0][1:] - [1, 2])
    theta, corr, w2, Zs, _ = fmols(y, X, np.ones((500, 1)))
    bf.append(theta[1:] - [1, 2]); se = np.sqrt(w2 * np.diag(np.linalg.inv(Zs.T @ Zs)))[1:]
    tf.append((theta[1:] - [1, 2]) / se)
bo, bf, tf = map(np.array, (bo, bf, tf))
print("3 mean bias OLS:", bo.mean(0).round(4), " FM:", bf.mean(0).round(4), "| FM t-test 5% rejection:", (np.abs(tf) > 1.96).mean(0).round(3), "(MC se ~0.005)")
