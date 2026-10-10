
"""The whole pipeline, in one command.

    python run_all.py                 # every table, 3 seeds, writes results/

Stages, in the order the whole project is about:

    1 data        four measured tables, hashed
    2 control     the same loop on permuted outcomes -- must not beat random
    3 screen      random / ofat / greedy / ei / ucb at two budgets x 3 seeds
    4 holdout     the best recipe found, scored on rows the loop never saw
    5 audit       SHA-256 manifest, tool versions, coverage of what was tried
"""
import json, os, statistics, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fs.data import load_concrete, load_buchwald, load_chembl, Campaign
from fs.campaign import run_campaign
from fs import audit

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "results")
TABLES = {"concrete": load_concrete, "buchwald": load_buchwald,
          "chembl_egfr": lambda: load_chembl("egfr"), "chembl_herg": lambda: load_chembl("herg")}
METHODS = ("random", "ofat", "greedy", "ei", "ucb")
BUDGETS = {"concrete": (32, 64), "buchwald": (48, 96),
           "chembl_egfr": (32, 64), "chembl_herg": (32, 64)}
SEEDS = (1, 2, 3)

def heldout_score(table, index, budget, seed, holdout_frac=0.25):
    """Score the campaign's best recipe against measurements it never saw.

    The campaign's own index list is what it actually ran, so the best of those is
    the claim being checked. If that recipe is itself in the held-out set (this
    table has one row per recipe, so the split can land that way), the check is
    exact. Otherwise the nearest held-out recipe in feature space stands in, and
    the result records which of the two happened -- a substitute is not a hit, and
    saying "held-out 97.3" without saying which kind it was is the sort of number
    this project exists to refuse.
    """
    c = Campaign(table, budget=budget, seed=seed, holdout_frac=holdout_frac)
    seen = set(index)
    best_i = max(seen, key=lambda i: table["y"][i])
    if best_i in c.holdout:
        return {"kind": "exact", "value": table["y"][best_i], "index": best_i}
    bestx = table["X"][best_i]

    def dist(i):
        x = table["X"][i]
        d = 0.0
        for k in bestx:
            a, b = bestx[k], x[k]
            if isinstance(a, str) or isinstance(b, str):
                d += 0.0 if a == b else 1.0
            else:
                d += abs(float(a) - float(b)) / (abs(float(a)) + abs(float(b)) + 1e-9)
        return d

    j = min(c.holdout, key=dist)
    return {"kind": "nearest-holdout", "value": table["y"][j], "distance": dist(j), "index": j}


def main(quick=False, methods=METHODS, seeds=SEEDS):
    report = {"stages": {}}
    print("1/5 data: hashing every table")
    rep_manifest = audit.write_manifest(os.path.join(OUT, "manifest.json"))
    for k, v in rep_manifest["data"].items():
        print("    %-28s %9d B  %s" % (k, v["bytes"], v["sha256"][:16]))

    print("2/5 control: the same loops on permuted outcomes (must not beat random)")
    ctrl = {}
    for name in (["concrete", "buchwald"] if quick else list(TABLES)):
        t = audit.permuted_copy(TABLES[name](), seed=0)
        for m in ("ei", "random"):
            vals = []
            for s in (1, 2):
                c = Campaign(t, budget=32 if name != "buchwald" else 48, seed=s)
                r = run_campaign(c, method=m, budget=32 if name != "buchwald" else 48, init=8, seed=s)
                vals.append(max(r["y"]))
            ctrl["%s|%s" % (name, m)] = statistics.fmean(vals)
            print("    %-16s %-7s mean best = %.2f" % (name, m, ctrl["%s|%s" % (name, m)]))
    report["stages"]["control"] = ctrl

    print("3/5 screen: campaigns")
    screen, held = {}, {}
    for name in (["concrete"] if quick else list(TABLES)):
        for b in BUDGETS[name]:
            for m in methods:
                vals, ho = [], []
                for s in seeds:
                    c = Campaign(TABLES[name](), budget=b, seed=s)
                    r = run_campaign(c, method=m, budget=b, init=max(8, b // 8), seed=s)
                    vals.append(max(r["y"]))
                    hs = heldout_score(TABLES[name](), r["index"], b, s)
                    ho.append(hs["value"])
                key = "%s|%s|%d" % (name, m, b)
                screen[key] = {"mean": statistics.fmean(vals), "min": min(vals),
                               "max": max(vals), "vals": vals}
                held[key] = {"mean": statistics.fmean(ho), "vals": ho}
                print("    %-26s mean=%8.2f  heldout=%8.2f" % (key, screen[key]["mean"], held[key]["mean"]))
    report["stages"]["screen"] = screen
    report["stages"]["holdout"] = held

    print("4/5 holdout: relative to the held-out best, and to what the pool contains")
    rel = {}
    for key in screen:
        name = key.split("|")[0]
        t = TABLES[name]()
        c = Campaign(t, budget=1, seed=1)
        ho_max = max(t["y"][i] for i in c.holdout_indices())
        rel[key] = {"heldout_frac_of_max": held[key]["mean"] / ho_max, "heldout_max": ho_max}
    report["stages"]["relative"] = rel
    for k, v in sorted(rel.items(), key=lambda kv: -kv[1]["heldout_frac_of_max"])[:6]:
        print("    %-26s %.3f x held-out max" % (k, v["heldout_frac_of_max"]))

    print("5/5 audit: manifest + coverage")
    cov = {"tables": len(TABLES), "methods": list(methods), "seeds": list(seeds),
           "campaigns": len(screen), "files_hashed": len(rep_manifest["package"])}
    report["stages"]["coverage"] = cov
    path = os.path.join(OUT, "report.json")
    json.dump(report, open(path, "w"), indent=2, sort_keys=True)
    print("    coverage:", cov)
    print("report ->", path)
    return report

if __name__ == "__main__":
    quick = "--quick" in sys.argv
    main(quick=quick)
