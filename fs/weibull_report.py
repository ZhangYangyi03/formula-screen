"""Regenerate the numbers quoted in docs/weibull.md."""
import statistics as st
from . import weibull as wb

def main():
    rows = wb.load()
    print("fibres %d | gauge lengths %s | batches %d"
          % (len(rows), sorted({r["L"] for r in rows}), len({r["batch"] for r in rows})))
    for field, unit in (("sigma", "MPa"), ("force", "mN")):
        r = wb.scatter_vs_scaling(rows, field=field)
        print("")
        print("FIELD = %s  (the same measurements, expressed the other way)" % field)
        for L, d in r["per_length"].items():
            print("   L=%2dmm  n=%3d   m=%.2f   characteristic=%.1f %s"
                  % (L, d["n"], d["m"], d["s0"], unit))
        print("   length scaling: dln(x0)/dln(L) = %+.4f +- %.4f  ->  m_scaling = %.2f"
              % (r["slope"], r["slope_se"], r["m_scaling"]))
        print("   within-length:  m_scatter = %.2f" % r["m_scatter"])
        print("   RATIO m_scaling / m_scatter = %.2f   (weakest-link requires 1.00)" % r["ratio"])

    nul = wb.shuffle_null(rows, nrep=300)
    base = wb.scatter_vs_scaling(rows)
    print("")
    print("CONTROL -- strengths pooled and redistributed at random, n_rep=300")
    print("   m_scaling in the null: median %.1f   5th percentile %.1f   minimum %.1f"
          % (st.median(nul), nul[int(.05 * len(nul))], nul[0]))
    rat = sorted(v / base["m_scatter"] for v in nul)
    print("   null ratio: median %.2f   5th percentile %.2f"
          % (rat[len(rat)//2], rat[int(.05*len(rat))]))
    print("   observed ratio %.2f ; share of nulls at or above the observed m_scaling: %.1f%%"
          % (base["ratio"], 100 * sum(1 for v in nul if v >= base["m_scaling"]) / len(nul)))
    print("   share of nulls with a 'plausible looking' m_scaling in [3,25]: %.0f%%"
          % (100 * sum(1 for v in nul if 3 <= v <= 25) / len(nul)))

    pb = wb.per_batch_moduli(rows)
    v = sorted(pb.values())
    print("")
    print("PER-BATCH moduli, %d batches at one length each: %.2f .. %.2f   sd %.2f"
          % (len(v), v[0], v[-1], st.pstdev(v)))
    for k in sorted(pb):
        print("   L=%2dmm  %s  m=%.2f" % (k[0], k[1], pb[k]))

if __name__ == "__main__":
    main()
