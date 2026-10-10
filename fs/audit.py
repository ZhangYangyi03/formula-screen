
"""The audit layer: what a screening result is allowed to claim.

Three things happen here, and each exists because the alternative is a number
nobody can check.

1. HASHES. Every input table is hashed, and so is every file of the package and
   the tool versions that produced the run. The manifest is written to
   results/manifest.json. Without it "we used the Doyle table" is a sentence; with
   it, it is a fact about 1.2 MB of bytes.

2. HELD-OUT CHECK. The campaign may not read the held-out recipes -- the
   Campaign class enforces that -- so the recipe the campaign ended on can be
   scored against a measurement it never saw. What is reported is the held-out
   value of the best recipe the campaign found, per seed, plus the fraction of the
   held-out maximum that represents. A screening loop that only reports what it
   saw is reporting its own training set.

3. CONTROL. The same pipeline with the target permuted is run first. If a loop
   can still "find good recipes" when the outcomes are destroyed, the loop is
   reading something other than the outcomes. This is the negative control, and
   it runs before any headline number is quoted -- the same order evidence-gate
   uses, for the same reason: disprove the pipeline before trusting its score.
"""
import hashlib, json, os, platform, sys, zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def data_manifest(extra=()):
    data = os.path.join(ROOT, "data")
    out = {}
    for f in sorted(os.listdir(data)):
        p = os.path.join(data, f)
        if os.path.isfile(p):
            out[f] = {"bytes": os.path.getsize(p), "sha256": sha256(p)}
    for p in extra:
        out[os.path.relpath(p, ROOT)] = {"bytes": os.path.getsize(p), "sha256": sha256(p)}
    return out

def package_manifest():
    out = {}
    for sub in ("fs", "tests"):
        d = os.path.join(ROOT, sub)
        for f in sorted(os.listdir(d)):
            if f.endswith(".py"):
                p = os.path.join(d, f)
                out["%s/%s" % (sub, f)] = sha256(p)
    for f in ("run_all.py", "bench.py"):
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            out[f] = sha256(p)
    return out

def environment():
    return {"python": sys.version.split()[0], "platform": platform.platform(),
            "executable": sys.executable}

def write_manifest(path, extra=()):
    m = {"data": data_manifest(extra), "package": package_manifest(),
         "environment": environment()}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(m, open(path, "w"), indent=2, sort_keys=True)
    return m

def permuted_copy(table, seed=0):
    """The negative control: the same recipes, outcomes destroyed.

    A permutation keeps the marginal distribution of the target and destroys the
    relation between recipe and outcome, so a method that still scores above
    random on this is a method reading something other than the recipe.
    """
    n = len(table["y"])
    order = list(range(n))
    for i in range(n - 1, 0, -1):
        j = zlib.crc32(("%d|%d" % (i, seed)).encode()) % (i + 1)
        order[i], order[j] = order[j], order[i]
    t = dict(table)
    t["y"] = [table["y"][order[i]] for i in range(n)]
    t["name"] = table["name"]
    return t
