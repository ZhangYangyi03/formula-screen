
"""Acquisition functions: what to run next, given what has been run.

EI / PI / UCB on the surrogate's posterior, each closed-form or a short numeric
integral. Kept beside `random` and `ofat` because a screening loop that cannot
report what an uninformed baseline would have got is reporting a number with no
reference point -- and the reference point is the finding here, not the score.
"""
import math

SQRT2 = math.sqrt(2.0)

def _cdf(z):
    return 0.5 * (1.0 + math.erf(z / SQRT2))

def _pdf(z):
    return math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)

def ei(mu, var, best, xi=0.01):
    sd = math.sqrt(max(var, 1e-18))
    z = (mu - best - xi) / sd
    return (mu - best - xi) * _cdf(z) + sd * _pdf(z)

def pi(mu, var, best, xi=0.01):
    sd = math.sqrt(max(var, 1e-18))
    return _cdf((mu - best - xi) / sd)

def ucb(mu, var, best=None, kappa=2.0):
    return mu + kappa * math.sqrt(max(var, 1e-18))

def logei(mu, var, best, xi=0.01):
    """EI on the log scale: for yields and strengths, the difference between 40
    and 45 is not the same as between 90 and 95, and a linear EI cannot tell."""
    return ei(math.log(max(mu, 1e-9)), var / max(mu, 1e-9) ** 2,
              math.log(max(best, 1e-9)), xi)

ACQS = {"ei": ei, "pi": pi, "ucb": ucb, "logei": logei}
