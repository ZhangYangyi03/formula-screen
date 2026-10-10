
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fs.model import LinearGP, solve, invert
from fs.feat import build_encoder, encode, fit_scaler, apply_scaler
from fs.data import load_buchwald, Campaign

def test_solve_matches_known_system():
    A = [[4.0, 1.0], [1.0, 3.0]]
    b = [1.0, 2.0]
    x = solve(A, b)
    assert abs(4 * x[0] + x[1] - 1.0) < 1e-9
    assert abs(x[0] + 3 * x[1] - 2.0) < 1e-9

def test_invert_is_a_right_inverse():
    A = [[2.0, 0.5, 0.0], [0.5, 3.0, 1.0], [0.0, 1.0, 4.0]]
    Ai = invert(A)
    for i in range(3):
        for j in range(3):
            got = sum(A[i][k] * Ai[k][j] for k in range(3))
            assert abs(got - (1.0 if i == j else 0.0)) < 1e-9

def test_predict_many_matches_predict_on_a_real_design():
    t = load_buchwald()
    c = Campaign(t, budget=20, seed=3)
    rows = [t["X"][i] for i in c.pool[:15]]
    ys = [t["y"][i] for i in c.pool[:15]]
    enc = build_encoder(t["X"])
    m, s = fit_scaler(enc, rows)
    Phi = [apply_scaler(m, s, encode(enc, r)) for r in rows]
    g = LinearGP(len(Phi[0]), lam=1.0).fit(Phi, ys)
    cand_phi = [apply_scaler(m, s, encode(enc, t["X"][i])) for i in c.pool[15:60]]
    dense = [g.predict(v) for v in cand_phi]
    sparse = g.predict_many(cand_phi)
    for (a, b), (a2, b2) in zip(dense, sparse):
        assert abs(a - a2) < 1e-9 and abs(b - b2) < 1e-9

def test_variance_shrinks_as_the_campaign_learns():
    """A wide interval must mean "not yet probed"; after asking around a point
    the interval at that point must be narrower than at an unasked far one."""
    t = load_buchwald()
    c = Campaign(t, budget=40, seed=1)
    enc = build_encoder(t["X"])
    rows = [t["X"][i] for i in c.pool[:30]]
    ys = [t["y"][i] for i in c.pool[:30]]
    m, s = fit_scaler(enc, rows)
    Phi = [apply_scaler(m, s, encode(enc, r)) for r in rows]
    g = LinearGP(len(Phi[0]), lam=1.0).fit(Phi, ys)
    v_seen = g.predict(Phi[0])[1]
    v_far = g.predict(apply_scaler(m, s, encode(enc, t["X"][c.pool[3000]])))[1]
    assert v_far > v_seen, (v_far, v_seen)
