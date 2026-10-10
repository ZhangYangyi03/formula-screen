
"""Recipes to vectors, in pure Python.

No numpy, no sklearn. Two reasons, both measured:

  * this host refuses large BLAS allocations inside the sandbox (a 500x500
    Cholesky raised MemoryError), so a pipeline that needs them is a pipeline
    that does not run here;
  * a recipe table is small. 47 one-hot columns and ~200 asked experiments is a
    48x48 system. Gaussian elimination on that is instant in plain Python, and
    leaving the numeric stack out means the whole run is reproducible on any
    machine with CPython.

Standardisation statistics come from the ASKED points only. That is deliberate:
computing mean and std over the whole table would leak the held-out rows into
the model through its scaling, and the held-out check that follows would then be
measuring nothing.
"""
import math

def is_categorical(values):
    return isinstance(values[0], str)

VEC_KEYS = ("smiles",)

def build_encoder(X, vec_dim=24):
    keys = sorted(X[0].keys())
    cat_levels = {}
    num_keys = []
    for k in keys:
        if k in VEC_KEYS:
            continue
        col = [x[k] for x in X]
        if is_categorical(col):
            cat_levels[k] = sorted(set(col))
        else:
            num_keys.append(k)
    return {"keys": keys, "cat": cat_levels, "num": num_keys, "vec": [k for k in keys if k in VEC_KEYS],
            "vec_dim": vec_dim}

def encode(enc, x):
    """One-hot for categoricals, raw value for numerics (scaled later)."""
    v = []
    for k in enc["keys"]:
        if k in enc["vec"]:
            v.extend(smiles_vector(str(x.get(k, "")), dim=enc["vec_dim"] - N_ATOM_FEATS))
            continue
        if k in enc["cat"]:
            lv = enc["cat"][k]
            v.extend(1.0 if x.get(k) == L else 0.0 for L in lv)
        else:
            v.append(float(x.get(k, 0.0)))
    return v

def fit_scaler(enc, rows):
    """mean/std over rows, for the numeric columns only."""
    means, stds = [], []
    for j, k in enumerate(enc["keys"]):
        if k in enc["cat"]:
            means.append(0.0); stds.append(1.0)
    for k in enc["num"]:
        vals = [float(r[k]) for r in rows]
        m = sum(vals) / len(vals)
        var = sum((v - m) ** 2 for v in vals) / max(1, len(vals) - 1)
        s = math.sqrt(var) if var > 1e-12 else 1.0
        means.append(m); stds.append(s)
    # re-order to match encode()'s column order
    out_m, out_s = [], []
    for k in enc["keys"]:
        if k in enc["vec"]:
            out_m.extend([0.0] * (enc["vec_dim"] - N_ATOM_FEATS)); out_s.extend([1.0] * (enc["vec_dim"] - N_ATOM_FEATS))
        elif k in enc["cat"]:
            out_m.extend([0.0] * len(enc["cat"][k])); out_s.extend([1.0] * len(enc["cat"][k]))
        else:
            i = enc["num"].index(k)
            out_m.append(means[i]); out_s.append(stds[i])
    return out_m, out_s

def apply_scaler(means, stds, v):
    return [(vi - mi) / si for vi, mi, si in zip(v, means, stds)]


# ---------------------------------------------------------------- fingerprints

ELEMENTS = ("Cl", "Br", "Si", "Na", "Ca", "Li", "Mg", "Al", "Fe", "Zn",
            "C", "N", "O", "S", "P", "F", "I", "H", "B", "K", "Se", "Cu")

N_ATOM_FEATS = 11

def smiles_vector(smiles, dim=128, k=4):
    """A fixed-width projection of a SMILES string, pure Python.

    Counting Morgan bits would need a real chemistry toolkit, and the point here
    is not to be a good descriptor -- it is to be a descriptor whose width is a
    constant SMALL INT, because the surrogate inverts a dim x dim matrix in pure
    Python: at dim=139 one campaign took longer than four minutes and was killed,
    at dim=24 the same campaign is seconds. This host raises MemoryError on a
    16 MB allocation inside the sandbox, so "just use numpy and a proper
    fingerprint" is not available here; the width is a constraint, not a taste.

    The cost of that, stated rather than hidden: two different molecules can
    collide in a bucket, so the model is coarser than it would be with a proper
    fingerprint. It is the same vector for every method compared, so the
    comparison is unaffected; what is affected is the absolute level.
    """
    import zlib
    v = [0.0] * dim
    n_atoms = 0
    counts = {}
    i = 0
    while i < len(smiles):
        two = smiles[i:i + 2]
        if two in ELEMENTS and len(two) == 2:
            counts[two] = counts.get(two, 0) + 1; n_atoms += 1; i += 2; continue
        one = smiles[i]
        if one in ELEMENTS:
            counts[one] = counts.get(one, 0) + 1; n_atoms += 1
        i += 1
    feats = [float(n_atoms), float(sum(1 for c in smiles if c in "cnos")),
             float(sum(1 for c in smiles if c in "[]")),
             float(smiles.count("(")), float(smiles.count("="))]
    for e in ("N", "O", "S", "F", "Cl", "Br"):
        feats.append(float(counts.get(e, 0)) / (n_atoms or 1))
    for j, s in enumerate(smiles[i:i + k] for i in range(max(1, len(smiles) - k + 1))):
        v[zlib.crc32(s.encode()) % dim] += 1.0
    norm = sum(x * x for x in v) ** 0.5 or 1.0
    v = [x / norm for x in v]
    return feats + v
