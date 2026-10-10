
"""Turn results/sweep.jsonl and results/gain.jsonl into the tables in
docs/report.md.

Separate from the sweep on purpose: the sweep is expensive and resumable, the
report is cheap and rerunnable. Nothing here recomputes a campaign; it aggregates
what the ledger already holds, so a claim in the writeup can always be traced to
a line of JSON with a table, a method, a budget and a seed in it.

    python report.py            # print
    python report.py --markdown # write docs/report_tables.md
"""
import collections, json, os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SWEEP = os.path.join(ROOT, "results", "sweep.jsonl")
GAIN = os.path.join(ROOT, "results", "gain.jsonl")

def load(path, key):
    rows = []
    if not os.path.exists(path):
        return {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        if key in d:
            rows.append(d)
    uniq = {}
    for d in rows:
        uniq[(d["table"], d["method"], d["budget"], d["seed"], d.get("control", False))] = d
    return uniq

def agg(uniq, field="best"):
    g = collections.defaultdict(list)
    for (t, m, b, s, c), d in uniq.items():
        g[(t, b, m)].append(d[field])
    return g

def table_lines(uniq, field="best", control=False):
    g = agg(uniq, field)
    out = []
    for t in sorted({k[0] for k in g}):
        for b in sorted({k[1] for k in g if k[0] == t}):
            rows = sorted([k for k in g if k[0] == t and k[1] == b], key=lambda k: -sum(g[k]) / len(g[k]))
            rand = g.get((t, b, "random"), [])
            rmean = sum(rand) / len(rand) if rand else None
            out.append("")
            out.append("%s, budget %d" % (t, b))
            out.append("  %-8s %10s %10s %10s  %s" % ("method", "mean", "min", "max", "vs random"))
            for k in rows:
                v = g[k]
                mean = sum(v) / len(v)
                d = "" if rmean is None or k[2] == "random" else "%+.2f" % (mean - rmean)
                out.append("  %-8s %10.2f %10.2f %10.2f  %s" % (k[2], mean, min(v), max(v), d))
    return out

def gain_lines(uniq):
    g = collections.defaultdict(list)
    for (t, m, b, s, c), d in uniq.items():
        g[(t, b, m, c)].append(d["gain"])
    out = []
    for t in sorted({k[0] for k in g}):
        for b in sorted({k[1] for k in g if k[0] == t}):
            out.append("")
            out.append("%s, budget %d -- screening gain (held-out top-10%% minus held-out mean)"
                       % (t, b))
            out.append("  %-8s %12s %12s" % ("method", "gain mean", "n"))
            keys = sorted([k for k in g if k[0] == t and k[1] == b and not k[3]],
                          key=lambda k: -sum(g[k]) / len(g[k]))
            for k in keys:
                v = g[k]
                out.append("  %-8s %12.2f %12d" % (k[2], sum(v) / len(v), len(v)))
            for k in [k for k in g if k[0] == t and k[1] == b and k[3]]:
                v = g[k]
                out.append("  %-8s %12.2f %12d   <- CONTROL (target permuted)"
                           % ("CTRL+" + k[2], sum(v) / len(v), len(v)))
    return out

def main():
    s = load(SWEEP, "best")
    g = load(GAIN, "gain")
    print("campaigns recorded: %d sweep, %d gain" % (len(s), len(g)))
    lines = ["## Screening: best found (measured on rows the loop asked for)", ""]
    lines += table_lines(s)
    if g:
        lines += ["", "## Screening gain (measured on rows the loop never saw)"]
        lines += gain_lines(g)
    txt = "\n".join(lines)
    print(txt)
    if "--markdown" in sys.argv:
        p = os.path.join(ROOT, "docs", "report_tables.md")
        open(p, "w", encoding="utf-8").write(txt + "\n")
        print("\nwrote", p)
    return txt

if __name__ == "__main__":
    main()
