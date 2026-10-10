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
