
# formula-screen

Recipe screening where the verifier is cheap, fast and certain.

The question this project answers is narrow and checkable: given a table of
recipes somebody already measured, does a surrogate-guided screening loop find
better recipes in fewer tries than the baselines a chemist would actually use --
and can the claim be audited, rather than asserted?

Four measured tables, one metered loop, one held-out check, one negative control.
No data is invented and no outcome is simulated: every evaluation the loop
"spends" is a real measurement that exists in a published dataset. That is the
whole reason the domain was chosen -- the intermediate verifier is already paid
for, so a full loop can run to completion on a laptop.

    python run_all.py --quick     # ~1 minute, one table
    python run_all.py             # every table, 3 seeds, writes results/report.json
    python -m pytest tests -q     # the invariants

## What it does

    1 data      four tables, hashed with SHA-256 (results/manifest.json)
    2 control   the same loop on permuted outcomes -- must not beat random
    3 screen    random / ofat / greedy / ei / ucb, two budgets x 3 seeds
    4 heldout   the best recipe found, scored on rows the loop never saw
    5 audit     manifest, coverage, and what was and was not established

The metered API is the point. `Campaign.evaluate(i)` charges one evaluation and
refuses held-out indices, so a loop cannot quietly look at the answer. Every
method compared gets the same initial random design and the same budget.

## The baselines, and why these

    random   uniform draws. Beat this and you have beaten nothing.
    ofat     one-factor-at-a-time from the best recipe so far. This is what an
             experienced chemist does by hand, and it is the baseline that
             matters. Beating random is easy; beating OFAT is the claim.
    greedy   surrogate mean, no exploration. If greedy ties with EI, the
             uncertainty term is doing nothing and the report says so.
    ei/pi/ucb  posterior mean and variance from a linear-kernel GP.

## What is deliberately not here

No experimental validation. The four tables are finished data; nothing in this
repo can predict a synthesis that has never been run. What it can do is say, with
a measured held-out number behind it, whether a loop ranks untried recipes better
than chance -- and that is a smaller claim than "AI discovered a material".

No numpy. This host raises MemoryError on a 16 MB allocation inside the sandbox,
so the surrogate inverts its design matrix by hand in pure Python. The dim is
capped at 24 for the categorical tables for exactly that reason, which costs
descriptor quality and is stated in `fs/feat.py` rather than hidden.


A second question, in `docs/law.md` and `fs/law.py`: given ONE measured value of a
mix -- its 28-day strength -- and the ages it was tested at, which one-parameter
law of time predicts its other ages, and is that parameter a property of the
material or of the mix? The bounded form (CEB-FIP, S = S28*exp(k(1-sqrt(28/t))))
halves the long-age error of a power law (2.39 vs 10.61 MPa at 90d), and the
parameter k is carried by composition (held-out R2 +0.25 to +0.42, p<0.001) and
not by the strength level (R2 -0.06). Both claims are run against controls that
destroy the effect; the case where the law fails to rank mixes is in the same
document. `python -m fs.law_report` regenerates every number.

## Reproducing

Every number in `docs/report.md` comes from `results/sweep.jsonl`, which is
appended one line per campaign by `bench.py` (one shard per process, because a
long loop on this host slows to minutes as freed memory is not returned). The
manifest hashes every input table and every source file, so a result can be tied
to the exact bytes that produced it.
