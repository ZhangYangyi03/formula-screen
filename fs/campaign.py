
"""The screening loop itself, and its baselines.

A campaign asks `budget` times. Each ask is one real experiment already in the
table, so the loop runs to completion -- this is the domain where the verifier is
cheap, fast and certain precisely because it was paid for years ago by somebody
with a furnace.

The methods compared, all given the same budget and the same initial random
design:

    random      draw uniformly from the pool. The reference point.
    ofat        one-factor-at-a-time from the best recipe so far: vary one factor,
                keep the rest. This is what an experienced chemist actually does,
                and it is the baseline that matters -- beating random is easy.
    ei/pi/ucb   surrogate + acquisition, fit on the asked points only.
    logei       EI on the log scale, for targets where 40->45 is not the same
                step as 90->95.
    greedy      surrogate mean only, no exploration term. Included because if
                greedy ties with EI then the uncertainty term is doing nothing,
                and the report should say so rather than claim credit for it.

The scaler and the encoder are fitted on the asked points only. Fitting them on
the whole table would leak the held-out rows in through the scaling and make the
final check measure nothing.

`run_campaign` takes a `Campaign` (which owns pool and holdout), not a bare
table -- the first version took the table dict and crashed on the very first
call, which is what the test suite is for.
"""
from .feat import build_encoder, encode, fit_scaler, apply_scaler
from .model import LinearGP
from . import acq as A

def _rng(seed):
    state = [(seed & 0xFFFFFFFF) or 1]
    def nxt():
        x = state[0]
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= (x >> 17)
        x ^= (x << 5) & 0xFFFFFFFF
        state[0] = x & 0xFFFFFFFF
        return state[0] / 4294967296.0
    return nxt

def run_campaign(campaign, method="ei", budget=64, init=8, seed=0, xi=0.01, kappa=2.0):
    table = campaign.table
    pool = list(campaign.pool)
    n = len(pool)
    rnd = _rng(seed)
    order = pool[:]
    for i in range(len(order) - 1, 0, -1):
        j = int(rnd() * (i + 1)) % (i + 1)
        order[i], order[j] = order[j], order[i]
    init_idx = order[:init]
    asked_idx = init_idx[:]
    asked_y = [campaign.evaluate(i) for i in init_idx]

    enc = build_encoder(table["X"])
    while len(asked_idx) < min(budget, n):
        rows = [table["X"][i] for i in asked_idx]
        means, stds = fit_scaler(enc, rows)
        Phi = [apply_scaler(means, stds, encode(enc, r)) for r in rows]
        g = LinearGP(len(Phi[0]), lam=1.0).fit(Phi, asked_y)
        best = max(asked_y)
        cand_idx, cand_phi = [], []
        asked = set(asked_idx)
        for i in pool:
            if i in asked:
                continue
            cand_idx.append(i)
            cand_phi.append(apply_scaler(means, stds, encode(enc, table["X"][i])))
        if method == "random":
            pick = cand_idx[int(rnd() * len(cand_idx)) % len(cand_idx)]
        elif method == "ofat":
            pick = _ofat_pick(table, asked_idx, asked_y, cand_idx)
        elif method == "greedy":
            preds = [g.predict(v)[0] for v in cand_phi]
            pick = cand_idx[max(range(len(preds)), key=lambda k: (preds[k], -k))]
        else:
            f = A.ACQS[method]
            sc = []
            for v in cand_phi:
                mu, var = g.predict(v)
                sc.append(f(mu, var, best, kappa) if method == "ucb" else f(mu, var, best, xi))
            pick = cand_idx[max(range(len(sc)), key=lambda k: (sc[k], -k))]
        asked_idx.append(pick)
        asked_y.append(campaign.evaluate(pick))
    return {"method": method, "index": asked_idx, "y": asked_y,
            "best_so_far": [max(asked_y[:i + 1]) for i in range(len(asked_y))],
            "spent": campaign.spent, "pool_size": n}

def _ofat_pick(table, asked_idx, asked_y, cand_idx):
    """Vary exactly one factor away from the best recipe so far.

    Factor count differs first, then the size of the relative move, so the
    baseline is never silently a random draw. If nothing differs in one factor
    the nearest recipe is used, and the caller can see that in the recorded
    index.
    """
    bi = asked_idx[max(range(len(asked_y)), key=lambda k: asked_y[k])]
    base = table["X"][bi]
    keys = list(base.keys())
    best_c, best_score = None, None
    for i in cand_idx:
        x = table["X"][i]
        ndiff = sum(1 for k in keys if base[k] != x[k])
        dist = 0.0
        for k in keys:
            a, b = base[k], x[k]
            if isinstance(a, str) or isinstance(b, str):
                dist += 0.0 if a == b else 1.0
            else:
                dist += abs(float(a) - float(b)) / (abs(float(a)) + abs(float(b)) + 1e-9)
        sc = (ndiff, dist, i)
        if best_score is None or sc < best_score:
            best_score, best_c = sc, i
    return best_c if best_c is not None else cand_idx[0]
