
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fs.data import load_concrete, load_buchwald, load_chembl, Campaign

def test_concrete_shape():
    t = load_concrete()
    assert len(t["X"]) == len(t["y"]) == 1030
    assert set(t["X"][0]) == {"cement","slag","fly_ash","water","superplasticizer","coarse_agg","fine_agg","age"}
    assert all(2.0 <= v <= 90.0 for v in t["y"])

def test_buchwald_is_a_real_grid():
    t = load_buchwald()
    assert 4500 < len(t["y"]) <= 4608
    assert len({x["base"] for x in t["X"]}) == 3
    assert len({x["ligand"] for x in t["X"]}) == 4
    assert len({x["aryl_halide"] for x in t["X"]}) == 16
    assert len({x["additive"] for x in t["X"]}) == 24

def test_campaign_meters_and_protects_holdout():
    t = load_concrete()
    c = Campaign(t, budget=5, seed=1)
    assert c.spent == 0
    got = [c.evaluate(i) for i in c.pool[:5]]
    assert c.spent == 5
    assert got == [t["y"][i] for i in c.pool[:5]]
    try:
        c.evaluate(c.pool[0]); assert False, "budget must be enforced"
    except RuntimeError:
        pass
    try:
        c.evaluate(list(c.holdout)[0]); assert False, "holdout must be unreachable"
    except RuntimeError:
        pass

def test_split_is_deterministic():
    t = load_concrete()
    a = Campaign(t, 10, seed=7); b = Campaign(t, 10, seed=7)
    assert a.holdout == b.holdout and a.pool == b.pool
    c = Campaign(t, 10, seed=8)
    assert a.holdout != c.holdout
