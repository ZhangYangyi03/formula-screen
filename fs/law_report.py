
"""Regenerate docs/law.md's numbers. Prints them; nothing is written by hand."""
import math, statistics as st, collections
from . import law

def main():
    ms = law.mixes()
    fs, rows = law.form_scores(ms)
    print("mixes %d | with a 28d point %d | (mix, age) pairs scored %d"
          % (len(ms), sum(1 for m in ms if m["s28"]), fs["power"]["n"]))
    print("")
    print("FORM  (leave-one-age-out, same mix, anchored on its own S(28))")
    for k in law.KINDS:
        d = fs[k]
        print("   %-6s mean %6.2f MPa  median %5.2f  p90 %6.2f  n=%d"
              % (k, d["mean_abs_err"], d["median_abs_err"], d["p90"], d["n"]))
    print("   CEB-FIP closer than the power law on %d of %d paired rows (%.0f%%)"
          % (fs["ceb_beats_power"], fs["paired_n"],
             100 * fs["ceb_beats_power"] / fs["paired_n"]))
    print("")
    print("   long ages:")
    for a in (56, 90, 91, 100, 120, 180, 270, 360, 365):
        R = [r for r in rows if r["age"] == a]
        if not R:
            continue
        parts = []
        for k in law.KINDS:
            v = [abs(r[k] - r["truth"]) for r in R if r[k] is not None]
            parts.append("%s %6.2f (n=%d)" % (k, st.mean(v), len(v)) if v else "%s n/a" % k)
        print("   %5dd  %s" % (a, "   ".join(parts)))

    car, n = law.carrier(ms)
    print("")
    print("CARRIER  (held-out R2 on k; %d mixes; permuted-target control)" % n)
    for name, d in car.items():
        print("   %-22s R2 %+6.3f  control95 %+6.3f  p=%.3f  coef %s"
              % (name, d["r2_heldout"], d["perm_p95"], d["p"],
                 [round(x, 3) for x in d["coef"]]))

    print("")
    print("STABILITY  (20 splits, held-out R2)")
    agg = collections.defaultdict(list)
    for seed in range(20):
        c2, _ = law.carrier(ms, seed=seed, nperm=0)
        for name, d in c2.items():
            agg[name].append(d["r2_heldout"])
    for name, v in agg.items():
        print("   %-22s %+.3f +- %.3f   min %+.3f max %+.3f"
              % (name, st.mean(v), st.pstdev(v), min(v), max(v)))

    em = law.end_members(ms)
    print("")
    print("END MEMBERS  k at a single-component binder")
    print("   k_cement %+.3f   k_flyash %+.3f   k_slag %+.3f   (n=%d)"
          % (em["k_cement"], em["k_flyash"], em["k_slag"], em["n_mixes"]))

    print("")
    print("CONTROL 1 -- the time order of each mix's own measurements destroyed")
    scr = law.form_control(ms, nrep=40)
    for k in law.KINDS:
        v = scr[k]
        print("   %-6s real %6.2f MPa      scrambled %6.2f +- %.2f MPa (n_rep=%d)"
              % (k, fs[k]["mean_abs_err"], st.mean(v), st.pstdev(v), len(v)))

    print("")
    print("CONTROL 2 -- composition labels shuffled between mixes, 300 draws")
    ctrl = law.end_member_control(ms, nrep=300)
    for key in ("k_cement", "k_slag", "k_flyash"):
        v = sorted(c[key] for c in ctrl)
        print("   %-9s real %+.3f   control %+.3f  [%+.3f, %+.3f]  (5-95%%)"
              % (key, em[key], st.mean(v), v[15], v[285]))

if __name__ == "__main__":
    main()
