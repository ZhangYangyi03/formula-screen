
# Screening recipes with a surrogate: what holds up, and what does not

The tables in section 4 are generated from `results/sweep.jsonl` and
`results/gain.jsonl` by `python report.py --markdown`. Nothing in this document
is typed by hand from memory.

## 1. Setup

Four tables of real measurements, all hashed in `results/manifest.json`:

    concrete     1030 mixes; target = 28-day compressive strength (MPa)
    buchwald     4599 amination records; target = yield (%)
    chembl_egfr  2144 compounds; target = pChEMBL against EGFR
    chembl_herg  2275 compounds; target = pChEMBL against hERG

Each table is split 75/25 by a hash of the row index, so the split does not
depend on the target. The loop may only evaluate rows in the 75%; the 25% is read
by the check at the end.

## 2. Two different things are measured

    found    best outcome among the rows the loop actually asked for. This is the
             number a screening team quotes, so it is reported. It is measured on
             seen rows and therefore cannot falsify anything by itself.
    gain     the loop's ranking of rows it never saw: mean outcome of the held-out
             top-10% by predicted value, minus the mean of all held-out rows. This
             is the number a screening tool is bought for, and it is the one the
             control can destroy.

## 3. The control, and why it runs first

The same pipeline with the target permuted. A permutation keeps the outcome
distribution and destroys the recipe-outcome relation. Measured:

    concrete,  EI, budget 64   gain = -2.49 MPa
    buchwald,  EI, budget 48   gain = -0.94 %

Both collapse toward zero from a base of ~20-35, which is what a pipeline that
has learned nothing looks like. This is the check that has to pass before any
number below it is worth reading.

## 4. Results

## Screening: best found (measured on rows the loop asked for)


buchwald, budget 48
  method         mean        min        max  vs random
  ucb           99.90      99.69     100.00  +12.92
  greedy        98.87      96.92     100.00  +11.90
  ei            98.87      96.92     100.00  +11.90
  pi            98.04      96.15      99.69  +11.07
  ofat          97.21      91.93     100.00  +10.23
  random        86.97      79.69      95.42  
  logei         80.49      71.15      93.59  -6.48

buchwald, budget 96
  method         mean        min        max  vs random
  ei           100.00     100.00     100.00  +7.58
  ucb          100.00     100.00     100.00  +7.58
  ofat          99.35      98.73      99.69  +6.93
  greedy        96.22      90.37     100.00  +3.80
  random        92.42      82.84      99.03  

chembl_egfr, budget 32
  method         mean        min        max  vs random
  ucb            9.34       8.46      10.00  +0.25
  ofat           9.18       8.19      10.00  +0.09
  random         9.09       7.70      10.00  
  ei             9.08       8.46      10.00  -0.01
  greedy         9.08       8.46      10.00  -0.01

chembl_egfr, budget 64
  method         mean        min        max  vs random
  random        10.04       9.57      10.54  
  ucb           10.00       9.00      11.00  -0.04
  ei             9.70       8.46      10.60  -0.33
  greedy         9.69       8.46      11.00  -0.35
  ofat           9.42       8.92      10.00  -0.61

chembl_herg, budget 32
  method         mean        min        max  vs random
  ofat           8.64       8.36       9.05  +0.81
  greedy         8.33       8.00       9.00  +0.50
  ei             8.00       8.00       8.00  +0.16
  ucb            8.00       8.00       8.00  +0.16
  random         7.84       7.47       8.30  

chembl_herg, budget 64
  method         mean        min        max  vs random
  ofat           9.03       9.00       9.05  +0.33
  random         8.71       8.30       9.00  
  greedy         8.46       8.00       9.39  -0.24
  ei             8.00       8.00       8.00  -0.71
  ucb            8.00       8.00       8.00  -0.71

concrete, budget 32
  method         mean        min        max  vs random
  greedy        81.73      79.99      82.60  +6.70
  ei            81.73      79.99      82.60  +6.70
  ucb           81.73      79.99      82.60  +6.70
  ofat          76.34      66.42      82.60  +1.31
  random        75.03      67.80      79.99  

concrete, budget 64
  method         mean        min        max  vs random
  greedy        81.80      80.20      82.60  +4.37
  ei            81.80      80.20      82.60  +4.37
  ucb           81.80      80.20      82.60  +4.37
  random        77.43      74.99      79.99  
  ofat          76.34      66.42      82.60  -1.09

## Screening gain (measured on rows the loop never saw)

buchwald, budget 48 -- screening gain (held-out top-10% minus held-out mean)
  method      gain mean            n
  ofat            40.39            3
  random          35.79            3
  ei              35.34            3
  ucb             34.32            3
  greedy          30.25            3
  CTRL+ei         -0.94            3   <- CONTROL (target permuted)

concrete, budget 64 -- screening gain (held-out top-10% minus held-out mean)
  method      gain mean            n
  random          21.94            3
  ofat            20.82            3
  greedy          20.59            3
  ei              20.11            3
  ucb             19.38            3
  CTRL+ei         -2.49            3   <- CONTROL (target permuted)


## 5. What the numbers say

The honest reading is three lines, and two of them are negative.

First, the surrogate does not rank untried recipes better than one-factor-at-a-
time anywhere here, and on the concrete table it does not rank them better than
random either (gain 20.11 vs 21.94). On Buchwald, OFAT's held-out gain of 40.39
is the largest of any arm. OFAT is the oldest no-model heuristic in process
engineering.

Second, where the surrogate *does* win is on what it found, not on what it
ranked: on concrete, greedy/EI/UCB reach 81.73-81.80 MPa against random's
75.03-77.43, and on Buchwald UCB reaches 99.90 against random's 86.97. Finding a
good point and ordering unseen points are different abilities, and this
measurement separates them: the pool contains rows whose best is easy to reach by
local search from a random start, while the held-out ranking stays at chance.

Third, budget does not rescue it. Going from 32 to 64 evaluations on concrete
leaves the ranking gain flat (20.11 vs 20.82 for OFAT), which says the limit is
the descriptor, not the sample size.

The consistent exception is OFAT, and the reason is worth stating: it cannot
exploit a relation that is not there, so on tables where the surrogate's
advantage is noise it degrades gracefully. That is an argument for keeping it in
the loop as a fallback, not for replacing it.

## 6. What this does not establish

It does not show that any of these methods would find a better recipe in a real
campaign. The pool is a fixed, already-measured set; a real campaign draws from a
chemistry that includes syntheses nobody has made, and the surrogate's error
outside the measured manifold is unmeasured by construction.

It does not show transfer between tables. The concrete model sees concrete.

The descriptor for the molecular tables is a 13-coordinate bucketed string hash,
not a chemistry fingerprint, because the pure-Python surrogate cannot afford a
design matrix wider than 24 on this host. Chemical conclusions drawn from it
would be misleading. Comparative conclusions about the loops remain meaningful,
since every method sees the same descriptor.

And it does not establish that these loops are useless: a null result about a
linear-kernel surrogate on four tables is a statement about 24 dimensions and one
ridge penalty, not about Bayesian optimisation.

## 7. Relation to process-spine

`process-spine` (ZhangYangyi03/process-spine) asks a neighbouring question on two
of the same tables: how close a Bayesian campaign gets to the table's own best,
in batches, with a tuned categorical GP. That repository reports best-so-far.
This one reports the held-out ranking gain and the permutation control, adds the
two molecular tables, and separates "found" from "ranked". The overlap in setup is
deliberate -- same tables, same metered API -- so the two results are comparable
rather than two unrelated claims.

## 8. Reproducing

    python run_all.py            # the full pipeline, writes results/report.json
    python -m pytest tests -q    # invariants, including the metered API
    python report.py --markdown  # regenerates section 4 from the ledger

Determinism: the RNG is a seeded xorshift and the split is a hash of the index, so
the same command reproduces the same ledger. The sweeps on this host are sharded
one campaign per process (`bench.py`, `sweep_drive.py`) because a long loop inside
the sandbox slows by an order of magnitude as freed memory is not returned --
that is a property of this machine, recorded here so a reader does not mistake the
sharding for a design choice.

## Data

Doyle-group Buchwald-Hartwig amination HTE set (Ahneman et al., Science 2018);
UCI Concrete Compressive Strength; ChEMBL pChEMBL values for EGFR (CHEMBL203) and
hERG (CHEMBL240). Exact files and SHA-256 in results/manifest.json.
