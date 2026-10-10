
"""The law test and the controls that could have killed it.

These tests exist so that the claim in docs/law.md cannot be read without the
thing that would falsify it. If the control stops collapsing the effect, the
claim is void, and this file is what says so.
"""
import os, sys, math, random, statistics as st
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fs import law

MS = law.mixes()

def test_the_table_is_what_we_think_it_is():
    assert len(MS) == 427, len(MS)
    assert sum(1 for m in MS if m["s28"]) == 416
    assert all(len(m["pts"]) >= 1 for m in MS)

def test_a_mix_generated_from_the_law_is_recovered():
    """Feed the law its own output: each form must get its parameter back, and the
    anchor must be respected exactly (S(28) is data, not a fitted quantity)."""
    for kind in law.KINDS:
        for ktrue in (0.2, 0.45, 0.8):
            pts = [(28, 40.0)]
            for a in (3, 7, 56, 90, 365):
                pts.append((a, law.predict(a, ktrue, 40.0, kind)))
            if any(y is None for _, y in pts):
                continue
            got = law.fit(pts, 40.0, kind)
            assert abs(got - ktrue) < 1e-6, (kind, ktrue, got)

def test_bounded_form_beats_unbounded_on_long_ages():
    fs, rows = law.form_scores(MS)
    long_rows = [r for r in rows if r["age"] >= 90 and r["ceb"] is not None and r["power"] is not None]
    assert len(long_rows) >= 100, len(long_rows)
    e_ceb = st.mean([abs(r["ceb"] - r["truth"]) for r in long_rows])
    e_pow = st.mean([abs(r["power"] - r["truth"]) for r in long_rows])
    assert e_ceb < e_pow, (e_ceb, e_pow)

def test_the_form_control_collapses_the_advantage():
    """Scramble each mix's own strengths across its ages. The winner must not survive:
    this is the check that separates 'a real time law' from 'a curve that can sit on
    any increasing data'."""
    real = law.form_scores(MS)[0]
    scr = law.form_control(MS, nrep=8)
    m_pow = st.mean(scr["power"]); m_ceb = st.mean(scr["ceb"])
    assert m_ceb > real["ceb"]["mean_abs_err"] * 2, (m_ceb, real["ceb"])
    assert m_pow > real["power"]["mean_abs_err"] * 1.5, (m_pow, real["power"])

def test_the_parameter_is_a_property_of_composition_not_of_the_strength_level():
    car, n = law.carrier(MS, nperm=80)
    assert n >= 120
    assert car["level (ln S28)"]["r2_heldout"] < 0.2
    assert car["composition (s,f,w/b)"]["r2_heldout"] > 0.2
    assert car["composition (s,f,w/b)"]["p"] < 0.01, car["composition (s,f,w/b)"]

def test_end_members_are_ordered_and_the_control_brackets_the_naive_value():
    em = law.end_members(MS)
    assert em["k_cement"] < em["k_flyash"] < em["k_slag"], em
    ctrl = law.end_member_control(MS, nrep=120)
    # Only ONE end member is individually outside the shuffled control band, and the
    # claim has to be stated in the form that is actually true: the SPREAD between the
    # end members, not each end member on its own. Shuffling the composition labels
    # produces a spread of essentially zero, which is what "the parameter is not a
    # property of composition" would have looked like.
    cem = sorted(c["k_cement"] for c in ctrl)
    assert em["k_cement"] < cem[0], (em["k_cement"], cem[0], cem[-1])
    spread = sorted(c["k_slag"] - c["k_cement"] for c in ctrl)
    real_spread = em["k_slag"] - em["k_cement"]
    assert real_spread > spread[-1], (real_spread, spread[0], spread[-1])
    assert abs(spread[0]) < 0.5 * real_spread, (spread[0], real_spread)
