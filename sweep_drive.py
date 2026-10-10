
"""Detached driver: one fresh child process per shard.

Measured here: a fresh process finishes a Buchwald campaign in 4-20 s, while a
process that has already run twenty takes minutes, because freed memory is not
returned to the OS inside this sandbox. So the driver never does the work
itself -- it spawns `bench.py` once per pending shard, appends to the same JSONL,
and moves on. Peak memory is a single campaign's, and a crash costs one shard.
"""
import json, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "sweep.jsonl")
sys.path.insert(0, HERE)
from bench import default_shards

def done():
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
    shards = default_shards()
    while True:
        pend = [j for j in shards if j not in done()]
        if not pend:
            print("ALL DONE %s" % time.strftime("%H:%M:%S"), flush=True)
            break
        for (t, m, b, s) in pend:
            print("start %s %s %d %d %s" % (t, m, b, s, time.strftime("%H:%M:%S")), flush=True)
            try:
                p = subprocess.run([sys.executable, "bench.py", "--table", t, "--method", m,
                                    "--budget", str(b), "--seed", str(s), "--out", OUT],
                                   cwd=HERE, capture_output=True, text=True, timeout=900)
                if p.returncode != 0:
                    print("  FAIL %s" % p.stderr[-300:], flush=True)
            except Exception as e:
                print("  ERR %s: %s" % (type(e).__name__, e), flush=True)
        time.sleep(1)
    print("remaining %d" % len([j for j in shards if j not in done()]), flush=True)
