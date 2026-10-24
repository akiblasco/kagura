"""Simulate WW (2017) limiting null distributions, k=2, intercept, g(s)=s^3.
FMD: W_hat from eq. (13); IM: P_tilde from eq. (18).
Form 'pub' = eq. (14)/(19): int_m^s X^2.  Form 'dp' = DP eq. (38) / cointmonitoR: int_m^s X^2 - int_0^m X^2."""
import sys, numpy as np
from concurrent.futures import ProcessPoolExecutor
n, K = 1000, 2
z = np.arange(1, n + 1) / n

def batch(args):
    ms, R, seed = args
    rng = np.random.default_rng(seed)
    out = {(est, form, m): [] for est in ("FMD", "IM") for form in ("pub", "dp") for m in ms}
    for _ in range(R):
        dW = rng.standard_normal(n) / np.sqrt(n); W = dW.cumsum()
        Wv = (rng.standard_normal((n, K)) / np.sqrt(n)).cumsum(0)
        J = np.column_stack([np.ones(n), Wv])                         # J(z) = [D(z), Wv(z)]
        cJ = J.cumsum(0) / n                                           # int_0^s J
        intWv = Wv.cumsum(0) / n
        f = np.column_stack([z, intWv, Wv])                            # f(s) = [int D, int Wv, Wv]
        Fz = f.cumsum(0) / n                                           # F(s) = int_0^s f
        for m in ms:
            M = int(round(m * n))
            # FMD (13): W(s) - int_0^s J' (int_0^m JJ')^-1 int_0^m J dW
            A = J[:M].T @ J[:M] / n; b = J[:M].T @ dW[:M]
            X1 = W - cJ @ np.linalg.solve(A, b)
            # IM (18): W(s) - f(s)' (int_0^m ff')^-1 int_0^m [F(m)-F(z)] dW
            Af = f[:M].T @ f[:M] / n; bf = (Fz[M - 1] - Fz[:M]).T @ dW[:M]
            X2 = W - f @ np.linalg.solve(Af, bf)
            for est, X in (("FMD", X1), ("IM", X2)):
                c = (X ** 2).cumsum() / n
                pre = c[M - 1]
                post = c[M:] - pre
                s3 = z[M:] ** 3
                out[(est, "pub", m)].append(np.max(post / s3))
                out[(est, "dp", m)].append(np.max(np.abs(post - pre) / s3))
    return out

if __name__ == "__main__":
    R, ms = int(sys.argv[1]), (0.5, 0.75, 0.9, 492 / 547)
    jobs = [(ms, R // 10, [8, i]) for i in range(10)]
    agg = {}
    with ProcessPoolExecutor(10) as ex:
        for o in ex.map(batch, jobs):
            for k, v in o.items(): agg.setdefault(k, []).extend(v)
    np.save("ww_limit.npy", {k: np.array(v) for k, v in agg.items()}, allow_pickle=True)
    for k in sorted(agg):
        v = np.array(agg[k]); q = np.quantile(v, [.9, .95, .975, .99])
        print(f"{k[0]:<4}{k[1]:<4} m={k[2]:.4f}  q90/95/97.5/99 = {np.round(q, 4).tolist()}")
