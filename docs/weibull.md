
# Weakest-link on real carbon fibre, and what the honest answer is

Recomputed by `python -m fs.weibull_report` from
`data/carbon_fiber_single_filament.csv`, which was converted from three open
workbooks (Zenodo 18435237, CC-BY-4.0); both the workbooks' SHA-256 and the
derived CSV's are in `results/manifest.json`.

## The law, and why it is falsifiable

Weakest-link (Weibull 1939): a fibre fails at its worst flaw, so strength is an
extreme-value quantity and across specimens it follows a two-parameter Weibull
distribution with modulus m. The falsifiable part is this: the SAME m governs two
things that are measured completely separately.

    within one gauge length    how wide the strength scatter is
    across gauge lengths       how far the distribution's scale shifts

If the law holds, the m fitted to the first and the m implied by the second
agree. This is not a curve-fitting preference -- it is a consistency condition
between two independent measurements of one material.

## The data

    255 single-filament tensile tests
    30 mm  51 fibres      50 mm  154 fibres      70 mm  50 fibres
    17 fibre batches, each measured at exactly ONE gauge length

The last line is important and is the study's largest weakness: the comparison
across gauge lengths is a comparison BETWEEN batches. There is no fibre
population measured at two lengths, so a batch-to-batch difference in flaw
severity is indistinguishable from a length effect.

## Result 1 -- the consistency condition fails, and by how much

    length    n     m (within-length)   characteristic strength
    30 mm    51          6.82                 3754.9 MPa
    50 mm   154          7.77                 3566.4 MPa
    70 mm    50          5.16                 3456.0 MPa

    length scaling  dln(sigma0)/dln(L) = -0.0982 +- 0.0020
    -> m_scaling  = 10.19
       m_scatter  =  6.58
       RATIO      =  1.55        law requires 1.00

The same test on FORCE instead of stress -- which removes the fibre-area
measurement from the comparison, since stress = force/area and the measured
areas scatter with a 9-11% coefficient of variation:

    m_scaling  = 9.71      m_scatter = 5.36      RATIO = 1.81

Both directions disagree the same way: the length effect is larger than the
within-length scatter can account for, i.e. the 70 mm fibres are weaker than
weakest-link extrapolation from the 30 mm scatter permits.

## Result 2 -- and here is why that statement cannot be made

The obvious control destroys it. Pool all 255 strengths, redistribute them among
the three length groups at random, and refit: by construction those surrogates
contain no length effect at all.

    statistic                    observed     shuffle-null
    m_scaling                      10.19      median 37.4, 5th pct 15.2, min 10.0
    ratio m_scaling/m_scatter       1.55      median 5.69, 5th pct 2.31
    share of nulls >= observed                99.3%
    share of nulls with a "plausible" m_scaling in [3, 25]      26%

So the test as run has no discriminating power here: three group estimates of a
scale parameter, each from 50-154 samples, produce a ratio of 1.5-6 under the
null. A number like 1.55 is what this estimator produces when there is nothing
there. The disagreement is real, but it is not evidence against weakest-link,
because this design cannot produce evidence either way.

## Result 3 -- the same data says the modulus is not one number

    per-batch Weibull moduli (16 batches, one length each)
    range 4.74 .. 10.85      sd 1.73

The between-batch spread of m (sd 1.73) is the same size as the disagreement
between the two estimates of the single law (1.55 ratio). Given that every batch
sits at one length only, that is exactly what the confound would look like.

## What this does NOT establish

It does not refute weakest-link. Weakest-link is well supported on fibres
measured properly, with many specimens at each of several lengths from one
population, and with the gauge length decoupled from fibre handling. This dataset
is not that design, and no analysis of it can settle the question.

It does not establish a length effect of -0.098 per log-length as a material
property: the between-batch spread is the same size as the effect.

It does not transfer to T800 or to any named commercial fibre. The dataset does
not name the fibre; the batches are labelled T2269-T2285, and the workbooks'
own Weibull numbers (m = 7.39 / 6.71 / 3.60) differ from the ones computed here
from the raw per-fibre values (6.82 / 7.77 / 5.16), which is itself a reason to
treat the dataset's derived columns as derived.

## What the exercise did produce

A reusable instrument rather than a claim: `fs/weibull.py` fits the modulus by
maximum likelihood, runs the scatter-versus-scaling consistency test on stress or
on force, and ships the shuffle-null that shows how much of the result a design
like this can support. `tests/test_weibull.py` asserts that the disagreement
exists AND that the control is larger than it -- so a future reader cannot quote
the first without meeting the second.

The one thing worth keeping from this run is negative and general: a control can
be *bigger* than the effect, not merely noisy around it. When three groups are
compared, the null distribution of a group-wise ratio includes values far from 1,
and a report that quoted 1.55 as evidence would have been quoting its own
estimator.
