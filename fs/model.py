
"""A ridge-regression surrogate with honest uncertainty, in pure Python.

This is a Gaussian process with a linear kernel, fitted by ridge regression.
It is not a compromise for speed -- it is what gives the acquisition function
something to reason about:

    mu(x)  = ybar + w . phi(x),        w = A^-1 Phi^T (y - ybar)
    var(x) = s2 * (1 + phi(x)^T A^-1 phi(x)),   A = Phi^T Phi + lam I

The second term is what makes exploration possible: a direction that has never
been probed has a large phi^T A^-1 phi, so its interval is wide and an
acquisition function is willing to pay for it. A point predictor would make the
loop a greedy hill-climb with no way to say "I have not tried that", and the
whole comparison against random search would collapse into "which is luckier".

`solve` is Gaussian elimination with partial pivoting, written here so the
dependency list stays empty. Every prediction carries its variance into the
report; no number in this project is a bare point estimate.

s2 is the residual variance of the fit, computed on the asked points -- so it is
estimable, not a prior, and it shrinks as the campaign learns.
"""
import math

def solve(A, b):
    n = len(A)
    M = [A[i][:] + [b[i]] for i in range(n)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        if p != c:
            M[c], M[p] = M[p], M[c]
        piv = M[c][c]
        if abs(piv) < 1e-14:
            piv = 1e-14
        inv = 1.0 / piv
        for j in range(c, n + 1):
            M[c][j] *= inv
        for r in range(n):
            if r != c:
                f = M[r][c]
                if f != 0.0:
                    Mr, Mc = M[r], M[c]
                    for j in range(c, n + 1):
                        Mr[j] -= f * Mc[j]
    return [M[i][n] for i in range(n)]

def invert(A):
    n = len(A)
    cols = []
    for j in range(n):
        e = [0.0] * n
        e[j] = 1.0
        cols.append(solve(A, e))
    return [[cols[j][i] for j in range(n)] for i in range(n)]

class LinearGP:
    def __init__(self, dim, lam=1.0):
        self.dim = dim
        self.lam = float(lam)
        self.Phi = []
        self.y = []
        self.Ainv = None
        self.w = None
        self.s2 = 1.0
        self.ybar = 0.0
        self.n = 0

    def fit(self, X, y):
        self.Phi = [list(r) for r in X]
        self.y = list(y)
        n = self.n = len(self.y)
        d = self.dim
        if n == 0:
            self.ybar = 0.0; self.w = [0.0] * d; self.Ainv = [[1.0 if i == j else 0.0 for j in range(d)] for i in range(d)]
            self.s2 = 1.0
            return self
        self.ybar = sum(self.y) / n
        yc = [v - self.ybar for v in self.y]
        A = [[0.0] * d for _ in range(d)]
        for r in self.Phi:
            for i in range(d):
                ri = r[i]
                if ri == 0.0:
                    continue
                Ai = A[i]
                for j in range(i, d):
                    Ai[j] += ri * r[j]
        for i in range(d):
            for j in range(i):
                A[i][j] = A[j][i]
            A[i][i] += self.lam
        self.Ainv = invert(A)
        self.w = [sum(self.Ainv[i][j] * sum(self.Phi[k][j] * yc[k] for k in range(n))
                      for j in range(d)) for i in range(d)]
        # residual variance on the asked points
        if n > 2:
            res = []
            for r, t in zip(self.Phi, yc):
                pred = sum(self.w[i] * r[i] for i in range(d))
                res.append(t - pred)
            self.s2 = sum(v * v for v in res) / (n - 2)
            if self.s2 < 1e-12:
                self.s2 = 1e-12
        return self

    def predict(self, r):
        mu = self.ybar + sum(self.w[i] * r[i] for i in range(self.dim))
        quad = 0.0
        for i in range(self.dim):
            ri = r[i]
            if ri == 0.0:
                continue
            quad += ri * sum(self.Ainv[i][j] * r[j] for j in range(self.dim))
        var = self.s2 * (1.0 + quad)
        return mu, var

    def predict_many(self, Rs):
        """Sparse fast path. A one-hot recipe has only a handful of non-zero
        coordinates, so the quadratic form costs O(nnz^2) instead of O(d^2):
        on the 47-column Buchwald design that is 16 multiplies per candidate
        instead of 2209, which is the difference between 40 seconds and 7
        minutes for one campaign. The dense result is identical -- checked by
        test_predict_many_matches_predict."""
        Ai = self.Ainv
        out = []
        for r in Rs:
            nz = [(i, v) for i, v in enumerate(r) if v != 0.0]
            mu = self.ybar
            for i, v in nz:
                mu += self.w[i] * v
            quad = 0.0
            for i, vi in nz:
                Arow = Ai[i]
                s = 0.0
                for j, vj in nz:
                    s += Arow[j] * vj
                quad += vi * s
            out.append((mu, self.s2 * (1.0 + quad)))
        return out
