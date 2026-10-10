
# A testable law of strength growth, and the control that could have killed it

Everything below is recomputed by `python -m fs.law_report` from
`data/concrete.csv` (SHA-256 in `results/manifest.json`). No number is typed by
hand.

## The question

Given ONE measured value of a mix -- its 28-day strength -- and the ages at which
that same mix was tested, which one-parameter law of time predicts its other
ages? And is that parameter a property of the material, or of the mix?

This is deliberately small enough to be settled by data instead of argued about.

## Two things separated

    form      which law's SHAPE is right. Tested by leaving one age out of the
              SAME mix; its own remaining ages are the only input, and the
              prediction is a genuinely untested age of that material.
    carrier   what the single parameter depends on. Tested on mixes the fit never
              saw, against a permuted-target control.

## The three candidate forms

Each carries exactly one fitted number and is anchored through the mix's own
S(28), so the comparison is about shape, not about free parameters:

    power law      S = S28 * (t/28)^n
    CEB-FIP        S = S28 * exp(k * (1 - sqrt(28/t)))     unbounded in t
    ACI-209 style  S = S28 / (1 + b * (t - 28)/28)

Only the second stays below a finite ceiling: S(inf)/S28 = exp(k). The first
diverges, the third saturates at S28/(1-b).

## Result 1 -- the form

529 (mix, age) pairs. Mean absolute error when predicting a held-out age of a
mix whose 28-day strength is known:

    power law       6.85 MPa
    CEB-FIP         3.45 MPa      <- half the error
    ACI-209        15.96 MPa
    CEB-FIP closer than the power law on 339 of 529 paired rows (64%)

The gap is not uniform in age; it is concentrated exactly where the difference
lives. Mean absolute error at long ages:

    age      n    power law   CEB-FIP
    90d     48      10.61       2.39
    91d     22      15.38       3.23
    100d    52      11.17       5.79
    180d    20       6.50       2.05
    365d    10       4.67       2.73

Measured strengths keep rising and then flatten; a power law has no flat.

## Result 2 -- the parameter

The exponent is a property of mix composition, not of the strength level. Held-out
R2 on k (136 mixes, 75/25 split, permuted-target control):

    carrier                 R2 held-out   control p95      p
    strength level ln S28      -0.057        -0.015     0.32
    water/binder               -0.002        -0.000     0.05
    composition (s,f,w/b)      +0.252        +0.053     0.000

Across 20 different splits the composition carrier gives +0.422 +- 0.145, the
water/binder ratio alone +0.105 +- 0.089, the strength level +0.111 +- 0.107.

End members, k for a mix whose binder is purely one thing, from the same fit:

    k_cement  0.021        a cement-only mix barely keeps gaining
    k_flyash  0.338
    k_slag    0.544        a slag-heavy mix keeps gaining late

## The controls, and what they rule out

    control                       real            scrambled
    form, CEB-FIP mean err        3.45 MPa        20.39 +- 1.07 MPa
    form, power law mean err      6.85 MPa        16.83 +- 0.57 MPa

Destroying the order of each mix's own measurements -- keeping the values, wiping
the mapping from age to strength -- destroys the winner completely, and it
destroys the bounded law hardest. That is the evidence that the result is about
time and not about curve flexibility.

    quantity                       real        composition shuffled control
    k_cement                       +0.021      +0.424   [1-99%: +0.276 .. +0.551]
    k_slag - k_cement              +0.523      +0.000   [1-99%: -0.159 .. +0.157]

Stated precisely, because the looser version would be wrong: only the cement end
member is individually outside the shuffled band. k_slag (+0.544) sits at the 93rd
percentile of its own control, i.e. inside it, and k_flyash at the 17th. What the
control establishes is the SPREAD: shuffling the composition labels leaves a
slag-minus-cement gap of 0.000 +- 0.08, and the measured gap is 0.523, outside the
control's 1-99% range entirely. The claim is that the parameter tracks composition,
not that each end-member value is separately resolved.

## What this does NOT establish

It is not a law in the sense of a falsified universal. It is a one-parameter
empirical fit to one 1030-row table compiled from published laboratory studies,
and the constant above it (S28) is itself data, not prediction.

It does not rank mixes. On the 8 held-out mixes that have a 180-day point, the
composition law's rank correlation with the actual 180d/28d gain is -0.07: it
gets the typical size of the late gain right and does not say which mix will
deliver it. Any use of this for selecting a mix is unsupported by these numbers.

It does not transfer. Nothing here says the parameters hold for mixes outside
this table, for other binders, for other curing regimes (steam, sealed, field),
or for the specific materials named in industry datasheets. The table is a
compilation with mixed provenance.

The held-out error reported above is the error at a SINGLE age given the mix's own
28-day value. Error compounds when several ages are chained, and the table does not
measure that.

## A case where the law says nothing useful

On the 8 held-out mixes that carry a 180-day point, the composition law's rank
correlation with the actual 180d/28d gain is -0.07, and its predicted top-3 shares
only 1 mix with the real top-3. It gets the typical size of the late gain right
(k_cement 0.021 vs k_slag 0.544 is a real spread) and still cannot say which
individual mix will deliver it -- because within the held-out set the real gain
spans only 1.08x to 1.23x of S(28), which is the size of the noise the law leaves
behind. Reported here because a law that is quoted without its blind spot is how
a measurement turns into a claim.

## Why this is a measurement and not a discovery

The bounded form beating the unbounded one at long ages is consistent with what
concrete researchers have assumed for decades (CEB-FIP's hyperbolic form exists
for this reason). What is new here is not the shape but the accounting: the form
test and the carrier test are separated, both are run against a control that
destroys the effect, and the case where the result fails to say anything useful
(ranking) is reported instead of omitted.
