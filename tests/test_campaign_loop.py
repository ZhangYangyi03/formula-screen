
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fs.data import load_concrete, load_buchwald, Campaign
from fs.campaign import run_campaign, _ofat_pick

def _camp(table=None, budget=40, seed=2):
    return Campaign(table or load_concrete(), budget=budget, seed=seed)

def test_campaign_respects_budget_and_never_touches_holdout():
    c = _camp(budget=40, seed=2)
    r = run_campaign(c, method="ei", budget=40, init=8, seed=2)
    assert r["spent"] == 40, r["spent"]
    assert not (set(r["index"]) & c.holdout)

def test_best_so_far_is_monotone():
    c = _camp(budget=32, seed=5)
    r = run_campaign(c, method="ei", budget=32, init=8, seed=5)
    b = r["best_so_far"]
    assert all(b[i] >= b[i - 1] - 1e-9 for i in range(1, len(b)))
    assert b[-1] == max(r["y"])

def test_methods_are_deterministic_given_a_seed():
    a = run_campaign(_camp(budget=24, seed=11), method="ei", budget=24, init=8, seed=11)
    b = run_campaign(_camp(budget=24, seed=11), method="ei", budget=24, init=8, seed=11)
    assert a["index"] == b["index"] and a["y"] == b["y"]

def test_ofat_actually_moves_one_factor():
    t = load_buchwald()
    c = Campaign(t, budget=30, seed=1)
    asked = c.pool[:10]
    ys = [t["y"][i] for i in asked]
    cand = c.pool[10:400]
    pick = _ofat_pick(t, asked, ys, cand)
    bi = asked[max(range(len(ys)), key=lambda k: ys[k])]
    base, x = t["X"][bi], t["X"][pick]
    assert sum(1 for k in base if base[k] != x[k]) == 1

def test_all_methods_produce_finite_values():
    for m in ["random", "ofat", "greedy", "ei", "pi", "ucb", "logei"]:
        r = run_campaign(_camp(budget=20, seed=4), method=m, budget=20, init=6, seed=4)
        assert len(r["y"]) == 20
        assert all(math.isfinite(v) for v in r["y"])
