
"""Four measured tables, one schema.

Every table here is a list of experiments somebody actually ran, each with the
recipe as input and the measured outcome as target. That is the whole point: the
verifier of a screening loop is a row that was already paid for, so the loop can
be run to completion on a laptop -- no simulator in the middle, no DFT, no
docking score standing in for a measurement.

A recipe is a dict of feature -> value. Categorical factors (which ligand, which
base, which halide) and continuous factors (how much cement) are handled by one
interface: the model one-hot-encodes categoricals, so a campaign does not need to
know which is which.

    concrete      1030 real concrete mixes, 7 mix proportions + age -> 28-day
                  compressive strength (MPa). Lab-measured.
    buchwald      4599 real HTE amination experiments (Doyle group plate data),
                  4 factors x 24/16/4/4 levels -> % yield.
    egfr/herg     ChEMBL measured IC50 (pChEMBL) for two targets, with the
                  publication each measurement came from -- so a screening claim
                  can be re-checked on molecules or on papers it has never seen.
"""
import csv, os, zlib

# hash() is salted per process in Python 3 -- the split must not depend on it.
def _stable_hash(i, seed):
    return zlib.crc32(("%d|%d" % (i, seed)).encode("utf-8"))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

def _rows(name):
    with open(os.path.join(DATA, name), encoding="utf-8", errors="ignore", newline="") as f:
        return list(csv.DictReader(f))

def load_concrete():
    X, y = [], []
    for r in _rows("concrete.csv"):
        X.append({k: float(r[k]) for k in
                  ("cement", "slag", "fly_ash", "water", "superplasticizer",
                   "coarse_agg", "fine_agg", "age")})
        y.append(float(r["strength"]))
    return {"name": "concrete", "kind": "material",
            "recipe": "mix proportions (kg/m3) + curing age",
            "target": "compressive strength (MPa), laboratory",
            "X": X, "y": y}

def load_buchwald():
    X, y = [], []
    for r in _rows("buchwald_amination.csv"):
        if r["yield"].strip() == "":
            continue
        X.append({"base": r["base"], "ligand": r["ligand"],
                  "aryl_halide": r["aryl_halide_number"], "additive": r["additive_number"]})
        y.append(float(r["yield"]))
    return {"name": "buchwald", "kind": "chemistry",
            "recipe": "base x ligand x aryl halide x additive (4 factors, 4608 grid)",
            "target": "isolated yield (%)", "X": X, "y": y}

def load_chembl(which="egfr"):
    name = "egfr_chembl203_ic50.csv" if which == "egfr" else "herg_chembl240_ic50.csv"
    X, y, meta = [], [], []
    for r in _rows(name):
        X.append({"smiles": r["smiles"]})
        y.append(float(r["pchembl_value"]))
        meta.append({"document": r["document_chembl_id"], "assay": r["assay_chembl_id"],
                     "year": int(r["document_year"]), "molecule": r["molecule_chembl_id"]})
    return {"name": "chembl_" + which, "kind": "biomedicine",
            "recipe": "molecule (SMILES)", "target": "measured pChEMBL (IC50)",
            "X": X, "y": y, "meta": meta}

class Campaign:
    """One table, with an API that looks like a prospective screening campaign.

    The table never shows a method more than the campaign budget has "spent": ask
    for a candidate's outcome and you are charged one evaluation. A held-out set
    can be carved off first, which is how a screened candidate gets checked
    against a measurement the loop never saw.
    """

    def __init__(self, table, budget, seed=0, holdout_frac=0.25):
        self.table = table
        n = len(table["y"])
        idx = list(range(n))
        # deterministic split: sort by a hash of the index and seed, not by value
        order = sorted(idx, key=lambda i: (_stable_hash(i, seed), i))
        nhold = int(n * holdout_frac)
        self.holdout = set(order[:nhold])
        self.pool = [i for i in order[nhold:]]
        self.budget = budget
        self.spent = 0
        self.asked = {}

    def features(self, i):
        return self.table["X"][i]

    def target(self, i):
        return self.table["y"][i]

    def evaluate(self, i):
        """The single metered operation: one real experiment."""
        if self.spent >= self.budget:
            raise RuntimeError("budget exhausted")
        if i in self.holdout:
            raise RuntimeError("index %d is held out; screening may not read it" % i)
        self.spent += 1
        self.asked[i] = self.asked.get(i, 0) + 1
        return self.target(i)

    def remaining(self):
        return self.budget - self.spent

    def holdout_indices(self):
        return sorted(self.holdout)
