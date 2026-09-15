# What we would put to Ian Wright

A synthesis of `docs/111`–`docs/120`, ordered by what we think would
matter most to the author of *The Social Architecture of Capitalism*.
Everything here comes from a stdlib reimplementation of the nine rules
at his three reported parameters (N = 1000, M = 100,000, ω = [10, 90]),
which conserves money to 1.3e-09 across 100 seeds.

We are not economists and have touched no empirical data. Every claim
below is about **his model's output**, which is the only thing we are in
a position to check.

---

## Two things we think are defects in the measurements, not the model

**1. The firm-size exponent is scale-dependent, so it needs an n beside
it.** Fitting by the Clauset–Shalizi–Newman protocol (MLE, `x_min` by
KS minimisation) on the model's own output, the estimate drifts
monotonically with sample size: **1.084 at n = 1,000 → 1.406 at
n = 1,000,000.** Your reported 1.038 is reproducible at small n and not
at large n, from the same runs. This dissolves what looked like a
discrepancy in our transcription and it means the number is not
comparable across studies without the sample size attached.

*(Convention note that cost us a day: your α and CSN's differ by exactly
one. α_Wright = α_CSN − 1; Zipf is 1.0 in your convention and 2.0 in
theirs.)*

**2. Fact 5 needs a geometric null, not an exponential one.** Recession
durations are whole years — integers. Tested against a **continuous**
exponential, the model's own durations give KS = 0.4975, p = 0.000,
which appears to refute your fact 5 outright. The statistic is an
artefact: a continuous CDF cannot track a step function, and with 318 of
481 durations equal to 1 the mismatch is mechanical. Against the
**geometric**, the exponential's discrete analogue, the same durations
give KS = 0.0270, p = 0.223, λ = **1.165** against your 1.22. Your fact
holds; the usual test does not test it.

---

## One result of yours that we think is weaker than stated

**3. On your own model's output, a lognormal fits firm sizes better than
a power law does.** 100 seeds at your scale, normalised log-likelihood
ratio (Vuong):

| | seeds |
|---|---|
| favours the **lognormal** (ratio ≤ −2) | **51** |
| favours the power law (ratio ≥ +2) | **0** |
| undetermined | 49 |

The power law is never preferred. It beats an *exponential* in 98 of 100,
so the distribution is certainly heavy-tailed — but "firm size follows
Zipf's law" is not supported by the data your model generates. We think
the defensible claim is heavy-tailed, with the family undetermined.

*(We hold this loosely in one respect: the income-tail version of the
same test is our weakest result — not rejected in only 46 of 100 seeds,
with the lognormal comparison undetermined in 99 of 100.)*

---

## Three things we found by varying what your paper holds fixed

Your model contains exactly one exchange mechanism, so the paper cannot
ask how much of the result is the social relations and how much is M1.
We made M1's two named ingredients — sampling once per employee ("a bias
justified by the law of value") and a random amount ("to reflect
contingency") — independently switchable, then continuous.

**4. M1 as written is load-bearing, and your attribution is correct.**
Across the 2×2, your rule is nearest your reported value on **all six**
scoreable targets (unemployment 0.173 vs ~0.17; demises 17.90 vs 18;
wage share 0.540 vs 0.55; recession λ 1.227 vs 1.22; income α 1.179 vs
1.3) and the three mutants miss on every one. Removing the size bias
takes the firm-size exponent from 1.337 to 4.715 — the tail simply
stops existing.

**5. You under-credit the law of value.** You attribute Laplace firm
growth to the random draw. It is carried by the *linearity*: main effect
on firm-growth excess kurtosis **+2.52 for linearity against −0.43 for
contingency**, the latter with the wrong sign. Remove randomness and
kurtosis stays at 2.59; remove the size bias and it collapses to −0.358,
below Gaussian. **Both** of the results you lead with rest on the
ingredient you label the law of value.

**6. Your budget constraint enforces the law of value a second time, and
we suspect you did not intend it to.** Making the exponent continuous —
expected revenue ∝ `members ** β`, with β = 1 your rule — the line

```python
if drawn > self.market:
    drawn = self.market
```

fires **0.0% of the time at β ≤ 1.0, 25% at β = 1.1, and 99% at β = 5.**
β = 1 is exactly the largest exponent at which M1 never saturates. Above
it the rule degenerates into *whoever is selected takes what is left*,
and since selection is uniform over actors a firm is still chosen in
proportion to headcount — which is β = 1 behaviour. The model does not
run away above 1; it reverts. Proportionality is therefore enforced
twice: once by the rule you wrote deliberately, and once by a constraint
that reads like an overdraft guard. We would be interested to know
whether you consider that clamp behavioural or defensive.

---

## The question we would most like to ask you

**7. Did you ever check that a single parameter setting produces all
seven facts at once?**

The paper reports the seven facts. As far as we can tell it does not
report that one setting yields all seven simultaneously, and we could
not find anyone who had checked. Sweeping β over [0, 5], scoring against
your two reported firm-level numbers (α = 1.038 and Laplace's excess
kurtosis of 3) with no bands and a relative squared loss:

| β | α | growth kurtosis | joint loss |
|---|---|---|---|
| 0.95 | 1.672 | 2.29 | 0.430 |
| **1.00** | **1.296** | **3.89** | **0.150** |
| 1.05 | 1.094 | 5.60 | 0.752 |
| 1.10 | 0.993 | 6.53 | 1.387 |

**The optimum is β = 1.00 exactly**, and the loss roughly triples per
0.05 step either way. Your parameter is not a convention you could have
chosen otherwise — it is the joint optimum of your own facts, and that
is a stronger result than the paper claims for it.

**But it is a compromise rather than a fit.** Taken alone, the firm-size
exponent wants **β = 1.078**; Laplace growth wants **β = 0.972**. They
disagree by 0.106, and at each one's optimum the other is off by roughly
a factor of two (kurtosis 6.12 where Laplace wants 3) or by 45% (α 1.505
where you report 1.038). At β = 1 neither target is met: α = 1.296,
kurtosis = 3.889.

So your two headline facts are generated by the same ingredient (point 5)
but want different strengths of it. We cannot tell whether that residual
indicates a missing mechanism or is simply what a deliberately minimal
model leaves on the table. It is invisible from inside a single-setting
model, which is our only reason for raising it.

---

## What we would not claim

None of this is evidence about real economies; we have not touched data.
It is closer to checking a proof's lemmas than to empirical economics.
Our lab reproduces your facts and then asks which of your lines produce
which of them — that can catch mis-attribution, as in points 5 and 6,
and it can never move a model toward truth. Point 3 is that limit biting
hardest: if the output cannot distinguish two distributional families,
it certainly cannot single out a mechanism.

We would also note against ourselves that one of our own headline
conclusions survived two days and was then withdrawn (`docs/120`): we
registered a one-sided band for a two-sided fact and manufactured an
"indifference above β = 1" that was not there.
