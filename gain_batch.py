
"""Screening gain: measured on held-out rows, with the permuted-target control.

Batched like the sweep, for the same measured reason: inside this sandbox a child
process that has already run several campaigns slows by an order of magnitude, so
each invocation does a bounded number of jobs and exits. The driver calls it
repeatedly and stops on ALL DONE.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fs.data import load_concrete, load_buchwald, Campaign
from fs.campaign import run_campaign
from fs.verify import gain_at_k, _permute

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "gain.jsonl")
BATCH = 6

def jobs():
    js = []
    for tb, b in (("concrete", 64), ("buchwald", 48)):
        for m in ("random", "ofat", "greedy", "ei", "ucb"):
            for s in (1, 2, 3):
                js.append((tb, m, b, s, False))
        for s in (1, 2, 3):
            js.append((tb, "ei", b, s, True))
    return js

def done():
    d = set()
    if os.path.exists(OUT):
        for line in open(OUT, encoding="utf-8"):
            try:
                x = json.loads(line)
                d.add((x["table"], x["method"], x["budget"], x["seed"], x["control"]))
            except Exception:
                pass
    return d

if __name__ == "__main__":
    d = done()
    todo = [j for j in jobs() if j not in d]
    if not todo:
        print("ALL DONE")
        raise SystemExit
    for (tb, m, b, s, ctrl) in todo[:BATCH]:
        tab = load_concrete() if tb == "concrete" else load_buchwald()
        if ctrl:
            tab = _permute(tab, 0)
        c = Campaign(tab, budget=b, seed=s)
        r = run_campaign(c, method=m, budget=b, init=max(8, b // 8), seed=s)
        g = gain_at_k(tab, r["index"], s)
        d2 = {"table": tb, "method": m, "budget": b, "seed": s, "control": ctrl,
              "gain": g["gain"], "base": g["base"], "top_mean": g["top_mean"], "k": g["k"]}
        with open(OUT, "a", encoding="utf-8") as f:
            f.write(json.dumps(d2) + "\n")
        print(d2, flush=True)
    print("remaining", len([j for j in jobs() if j not in done()]))
