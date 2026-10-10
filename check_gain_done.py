import sys
t=open('results/gain.log',errors='ignore').read()
sys.exit(0 if 'ALL DONE' in t[-2000:] else 1)
