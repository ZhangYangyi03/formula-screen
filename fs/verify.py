
"""The check that decides whether any of this works: does it point at good
untried recipes?

The campaign's own best-so-far curve cannot answer that, because it is measured
on rows the campaign was allowed to look at. The claim worth testing is the one a
screening tool is actually bought for -- "run this, it will be better than
average" -- and that is testable here, at zero cost, because the measurements
already exist:

    fit the surrogate on exactly the rows the campaign asked
    rank the HELD-OUT rows by predicted value, take the top k
    report their measured mean minus the measured mean of all held-out rows

That gap is the screening gain. It is a real number about rows the model never
saw, and it is zero when the method has learned nothing -- which is what the
permuted-outcome control in this module is for. On permuted targets the gap must
collapse; if it does not, the gap is coming from the features' correlation with
themselves and not from any recipe-outcome relation, and the whole result is void.

`gain_at_k` returns the gap for one campaign. `compare` runs it over methods,
budgets and seeds and reports the mean and the spread, plus the same statistic on
the control, because a gain without a control is the mistake this file exists to
prevent.
"""
import zlib
from .data import Campaign
from .campaign import run_campaign
from .feat import build_encoder, encode, fit_scaler, apply_scaler
from .model import LinearGP

def gain_at_k(table, index, seed, k_frac=0.1, holdout_frac=0.25):
    """Top-k of the held-out rows by predicted value, measured, minus their mean.

    Ranked strictly inside the held-out set, so a method that merely finds the
    global best pool row gains nothing here -- this measures ranking of unseen
    rows, not search of the pool.
    """
    c = Campaign(table, budget=max(len(index), 1), seed=seed, holdout_frac=holdout_frac)
    y_asked = [table["y"][i] for i in index]
    rows = [table["X"][i] for i in index]
    enc = build_encoder(table["X"])
    m, s = fit_scaler(enc, rows)
    Phi = [apply_scaler(m, s, encode(enc, r)) for r in rows]
    g = LinearGP(len(Phi[0]), lam=1.0).fit(Phi, y_asked)
    ho = sorted(c.holdout)
    ho_phi = [apply_scaler(m, s, encode(enc, table["X"][i])) for i in ho]
    preds = [p[0] for p in g.predict_many(ho_phi)]
    k = max(1, int(len(ho) * k_frac))
    top = sorted(range(len(ho)), key=lambda j: -preds[j])[:k]
    y_ho = [table["y"][i] for i in ho]
    base = sum(y_ho) / len(y_ho)
    topv = [y_ho[j] for j in top]
    return {"gain": sum(topv) / len(topv) - base, "k": k, "base": base,
            "top_mean": sum(topv) / len(topv), "n_holdout": len(ho)}

def _permute(table, seed=0):
    n = len(table["y"])
    order = list(range(n))
    for i in range(n - 1, 0, -1):
        j = zlib.crc32(("%d|%d" % (i, seed)).encode()) % (i + 1)
        order[i], order[j] = order[j], order[i]
    t = dict(table)
    t["y"] = [table["y"][order[i]] for i in range(n)]
    return t

def compare(table, budgets, methods, seeds, control=True):
    out = {}
    for b in budgets:
        for meth in methods:
            for s in seeds:
                c = Campaign(table, budget=b, seed=s)
                r = run_campaign(c, method=meth, budget=b, init=max(8, b // 8), seed=s)
                g = gain_at_k(table, r["index"], s)
                out.setdefault("%s|%d" % (meth, b), []).append(g["gain"])
    res = {k: {"gain_mean": sum(v) / len(v), "gain_vals": v} for k, v in out.items()}
    if control:
        t = _permute(table, 0)
        for meth in ("ei",):
            for b in budgets:
                vals = []
                for s in seeds:
                    c = Campaign(t, budget=b, seed=s)
                    r = run_campaign(c, method=meth, budget=b, init=max(8, b // 8), seed=s)
                    vals.append(gain_at_k(t, r["index"], s)["gain"])
                res["CONTROL|%s|%d" % (meth, b)] = {"gain_mean": sum(vals) / len(vals), "gain_vals": vals}
    return res
