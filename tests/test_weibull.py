
"""A real law on real data, and the control that shows what a failure looks like."""
import os, sys, math, statistics as st
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fs import weibull as wb

ROWS = wb.load()

def test_the_derived_table_is_intact():
    assert len(ROWS) == 255, len(ROWS)
    assert sorted({r["L"] for r in ROWS}) == [30, 50, 70]
    assert len({r["batch"] for r in ROWS}) == 17
    assert all(r["sigma"] > 0 and r["area"] > 0 for r in ROWS)

def test_weibull_mle_recovers_a_known_modulus():
    """Feed it synthetic Weibull samples; the estimator must get m back."""
    import random
    rnd = random.Random(0)
    for mtrue in (2.0, 5.0, 12.0):
        x = [1000.0 * (-math.log(1 - rnd.random())) ** (1 / mtrue) for _ in range(4000)]
        m, s0 = wb.weibull_mle(x)
        assert abs(m - mtrue) / mtrue < 0.10, (mtrue, m)

def test_characteristic_strength_falls_with_gauge_length():
    r = wb.scatter_vs_scaling(ROWS)
    s0 = [r["per_length"][L]["s0"] for L in (30, 50, 70)]
    assert s0[0] > s0[1] > s0[2], s0
    assert r["slope"] < 0

def test_the_disagreement_is_the_result_and_it_is_large():
    """Weakest-link requires m_scaling == m_scatter. It does not hold here, in the
    direction that says the length effect is bigger than the within-length scatter
    can account for. If this ever started agreeing, docs/weibull.md would be wrong."""
    r = wb.scatter_vs_scaling(ROWS)
    assert r["m_scaling"] > 1.3 * r["m_scatter"], r
    rf = wb.scatter_vs_scaling(ROWS, field="force")
    assert rf["m_scaling"] > 1.3 * rf["m_scatter"], rf

def test_the_control_is_much_larger_than_the_effect_not_smaller():
    """This is the honest hard part. The shuffle-null, which contains no length effect
    at all, produces an EVEN LARGER ratio than the data does. So the ratio test as run
    cannot separate signal from construction, and the test asserts that fact rather
    than pretending otherwise."""
    r = wb.scatter_vs_scaling(ROWS)
    nul = wb.shuffle_null(ROWS, nrep=40, seed=3)
    assert st.median(nul) > r["m_scaling"], (st.median(nul), r["m_scaling"])

def test_one_modulus_does_not_describe_the_batches_either():
    pb = wb.per_batch_moduli(ROWS)
    v = list(pb.values())
    assert len(v) >= 14
    assert st.pstdev(v) > 1.0, st.pstdev(v)
