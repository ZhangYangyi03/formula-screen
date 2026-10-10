
"""The split must survive a process boundary.

This test exists because the first version used Python's hash() to order the
split, and hash() of a str is salted per process -- so the same seed would have
produced a different holdout in every run, and every reported number would have
been quietly unreproducible. That is the same defect evidence-gate found in its
own fingerprint code; it is checked here by re-running the split in a child
process and comparing.
"""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

CHILD = """
import json, sys
sys.path.insert(0, %r)
from fs.data import load_concrete, Campaign
c = Campaign(load_concrete(), 10, seed=3)
print(json.dumps(sorted(c.holdout)))
""" % ROOT

def test_holdout_is_identical_across_processes():
    outs = []
    for _ in range(2):
        p = subprocess.run([sys.executable, "-c", CHILD], capture_output=True, text=True, timeout=120)
        assert p.returncode == 0, p.stderr
        outs.append(json.loads(p.stdout.strip().splitlines()[-1]))
    assert outs[0] == outs[1]
    assert len(outs[0]) == 257
