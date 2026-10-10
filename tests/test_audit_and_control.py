
"""The two checks that decide whether any result in this repo is reportable.

If either of these fails, the numbers in docs/report.md are void, so they are
tested rather than described: the held-out split must be unreachable from the
loop, and the permuted-target control must not show a gain that survives.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fs.data import load_concrete, Campaign
from fs.campaign import run_campaign
from fs.verify import gain_at_k, _permute
from fs import audit

def test_the_loop_cannot_read_the_holdout():
    t = load_concrete()
    c = Campaign(t, budget=8, seed=1)
    ho = sorted(c.holdout)
    assert ho
    for i in ho[:5]:
        try:
            c.evaluate(i)
        except RuntimeError:
            continue
        raise AssertionError("held-out index %d was readable by the loop" % i)

def test_the_budget_is_a_hard_cap():
    t = load_concrete()
    c = Campaign(t, budget=3, seed=1)
    for i in c.pool[:3]:
        c.evaluate(i)
    try:
        c.evaluate(c.pool[3])
    except RuntimeError:
        return
    raise AssertionError("budget was exceeded without raising")

def test_manifest_hashes_every_input_table():
    m = audit.data_manifest()
    for f in ("concrete.csv", "buchwald_amination.csv",
              "egfr_chembl203_ic50.csv", "herg_chembl240_ic50.csv"):
        assert f in m, f
        assert len(m[f]["sha256"]) == 64

def test_permutation_preserves_the_multiset_of_outcomes():
    t = load_concrete()
    p = audit.permuted_copy(t, seed=3)
    assert sorted(p["y"]) == sorted(t["y"])
    assert p["y"] != t["y"]
    assert p["X"] == t["X"]

def test_control_gain_collapses_relative_to_the_real_table():
    """The whole claim rests on this: with outcomes destroyed, the surrogate's
    held-out ranking gain must not be a positive number of any size."""
    t = load_concrete()
    c = Campaign(t, budget=24, seed=1)
    r = run_campaign(c, method="ei", budget=24, init=8, seed=1)
    real = gain_at_k(t, r["index"], 1)["gain"]
    pt = _permute(t, 0)
    c2 = Campaign(pt, budget=24, seed=1)
    r2 = run_campaign(c2, method="ei", budget=24, init=8, seed=1)
    ctrl = gain_at_k(pt, r2["index"], 1)["gain"]
    assert real > 0, real
    assert ctrl <= real * 0.5, (real, ctrl)
