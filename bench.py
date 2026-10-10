
"""One campaign per process, results appended as JSON lines.

Why per process: this host's sandbox caps a process at a very small heap (a
16 MB allocation raises MemoryError while 4 MB succeeds), and a long Python loop
does not return freed memory to the OS, so a sweep of 24 campaigns inside one
process dies partway through with no traceback -- it just stops. One campaign
per process keeps the peak flat, and makes a killed shard resumable instead of
a lost morning.

    python bench.py --table buchwald --method ei --budget 96 --seed 1
    python bench.py --run-all            # every shard, sequentially
"""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fs.data import load_concrete, load_buchwald, load_chembl, Campaign
from fs.campaign import run_campaign

TABLES = {
    "concrete": load_concrete,
    "buchwald": load_buchwald,
    "chembl_egfr": lambda: load_chembl("egfr"),
    "chembl_herg": lambda: load_chembl("herg"),
}
METRICS = {"concrete": "max", "buchwald": "max", "chembl_egfr": "max", "chembl_herg": "max"}

def one(table, method, budget, seed, init=None):
    t = TABLES[table]()
    c = Campaign(t, budget=budget, seed=seed, holdout_frac=0.25)
    t0 = time.time()
    r = run_campaign(c, method=method, budget=budget, init=init or max(8, budget // 8), seed=seed)
    return {"table": table, "method": method, "budget": budget, "seed": seed,
            "best": max(r["y"]), "pool_size": r["pool_size"],
            "spent": r["spent"], "seconds": round(time.time() - t0, 2)}

def run_all(out_path, shards=None, resume=True):
    done = set()
    if resume and os.path.exists(out_path):
        for line in open(out_path, encoding="utf-8"):
            try:
                d = json.loads(line)
                done.add((d["table"], d["method"], d["budget"], d["seed"]))
            except Exception:
                pass
    total = 0
    for (table, method, budget, seed) in shards:
        key = (table, method, budget, seed)
        if key in done:
            continue
        d = one(table, method, budget, seed)
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(d) + "\n")
        total += 1
        print("    %-13s %-8s b=%-4d s=%d best=%7.2f %5.1fs" %
              (table, method, budget, seed, d["best"], d["seconds"]), flush=True)
    return total

# The grid, and why it is this size: a Buchwald campaign at budget 96 takes
# ~60-90 s in a fresh process and minutes in a process that has already run
# several (this host does not return freed memory to the OS), so the whole sweep
# is sharded and resumed rather than run in one go. Methods are dropped where
# they are redundant: pi and logei are reported at budget 48 on the two
# categorical tables, where they cost seconds, and not at 96.
def default_shards():
    shards = []
    for b in (32, 64):
        for m in ("random", "ofat", "greedy", "ei", "ucb"):
            for s in (1, 2, 3):
                shards.append(("concrete", m, b, s))
    for b in (48, 96):
        for m in ("random", "ofat", "greedy", "ei", "ucb"):
            for s in (1, 2, 3):
                shards.append(("buchwald", m, b, s))
    for b in (48,):
        for m in ("pi", "logei"):
            for s in (1, 2, 3):
                shards.append(("buchwald", m, b, s))
    for tb in ("chembl_egfr", "chembl_herg"):
        for b in (32, 64):
            for m in ("random", "ofat", "greedy", "ei", "ucb"):
                for s in (1, 2, 3):
                    shards.append((tb, m, b, s))
    return shards

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--table"); ap.add_argument("--method")
    ap.add_argument("--budget", type=int); ap.add_argument("--seed", type=int)
    ap.add_argument("--out", default=os.path.join("results", "sweep.jsonl"))
    ap.add_argument("--run-all", action="store_true")
    a = ap.parse_args()
    if a.run_all:
        run_all(a.out, default_shards())
    else:
        d = one(a.table, a.method, a.budget, a.seed)
        with open(a.out, "a", encoding="utf-8") as f:
            f.write(json.dumps(d) + "\n")
        print(json.dumps(d))
