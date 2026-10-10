
"""Run the sweep in batches inside one process, resumable and self-limiting.

Measured on this host: a fresh process runs a Buchwald campaign in 4-9 s, but a
process that has already run twenty of them takes minutes for the twenty-first,
because freed memory is not returned to the OS and the sandbox cap is small. So
the runner takes a --limit, appends what it finished, and exits: the caller loops
until `--remaining` reports zero. A killed batch costs one batch, not the sweep.
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench import one, default_shards

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "sweep.jsonl")

def done_set():
    d = set()
    if os.path.exists(OUT):
        for line in open(OUT, encoding="utf-8"):
            try:
                x = json.loads(line)
                d.add((x["table"], x["method"], x["budget"], x["seed"]))
            except Exception:
                pass
    return d

if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    pending = [j for j in default_shards() if j not in done_set()]
    if not pending:
        print("ALL DONE"); raise SystemExit
    print("%d pending, running %d" % (len(pending), min(limit, len(pending))))
    t0 = time.time()
    for (t, m, b, s) in pending[:limit]:
        if time.time() - t0 > 400:
            break
        try:
            d = one(t, m, b, s)
        except Exception as e:
            d = {"table": t, "method": m, "budget": b, "seed": s, "error": "%s: %s" % (type(e).__name__, e)}
        with open(OUT, "a", encoding="utf-8") as f:
            f.write(json.dumps(d) + "\n")
        print("   ", {k: d[k] for k in d if k != "vals"}, flush=True)
    print("remaining:", len([j for j in default_shards() if j not in done_set()]))
