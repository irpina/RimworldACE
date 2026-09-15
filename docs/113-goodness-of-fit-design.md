# Does a power law actually fit? Design

Written before any estimator is built. `docs/112` §6 recorded the gap in
one sentence: *"we have fitted power laws without testing whether power
laws fit."* This closes it, and it is likely to qualify `docs/112` §4's
"the shapes all hold".

## 1. What is missing

`power_law_fit` returns an exponent, an `x_min` and a KS distance. A KS
distance is not a verdict. 0.0304 for firm size could be an excellent fit
or a terrible one; nothing in the code says which, because the sampling
distribution of that statistic under the fitted model was never computed.

Worse, a power law can pass a goodness-of-fit test while a **lognormal
fits the same data better**. Clauset, Shalizi and Newman's own re-analysis
of two dozen published power laws found exactly that in most cases. An
exponent with a p-value beside it is still not evidence that the power
law is the right family — only that it is not grossly wrong. So the
missing piece is two tests, not one.

## 2. The two tests

### 2.1 The KS goodness-of-fit p-value (CSN §4)

1. Fit the data: get `x_min`, `alpha`, and the observed distance `D`.
2. Generate synthetic datasets of the same size that are **power-law
   above `x_min`** with the fitted exponent, and **resampled from the
   empirical data below `x_min`**, keeping the same proportion either
   side.
3. **Refit each synthetic set from scratch, re-selecting its own
   `x_min`**, and take its distance `D_i`.
4. `p` is the fraction of synthetics with `D_i >= D`.

Step 3 is the part that is easy to get wrong and expensive to get right:
holding `x_min` fixed across the synthetics makes `p` far too small,
because it denies the synthetic data the same freedom the real data had.

CSN's rule of thumb: **`p <= 0.1` rejects the power law.** Note the
direction — a *large* p means the power law is not ruled out, which is
weaker than "the power law is true".

### 2.2 The likelihood-ratio test against alternatives (CSN §5)

Compare the fitted power law against a lognormal and an exponential on
the same tail, by the normalised log-likelihood ratio. Positive favours
the power law, negative the alternative, and the value is only meaningful
against its own standard deviation — a ratio of 0.3 with a spread of 2.0
says nothing at all. Report the ratio, the spread, and whether the sign
is determined.

## 3. The sample-size trap, and why the test is run per seed

At `n = 2,186,842` — the pooled firm sizes — a KS test has enormous
power, and **will reject a power law for a deviation far too small to
matter.** Any real dataset departs from an idealised distribution
somewhere; with two million points the test finds it. A rejection at that
`n` would say nothing about Wright's model and everything about our
sample size.

So the test is run **per seed**, at roughly 22,000 firm-size samples,
which is the scale Wright himself worked at — he reports one run. The
result is then a *distribution of 100 p-values*, which is far more
informative than one pooled verdict.

To make the trap visible rather than merely avoided, the p-value is also
computed on nested subsamples — 1k, 10k, 100k, 1M — so the design's claim
that p falls with n is measured rather than asserted.

## 4. Cost

A 22k-point fit is about 0.1s. 100 synthetics per seed × 100 seeds is
10,000 fits, roughly 17 minutes on one core and 5 on four. The
subsample-ladder adds a few minutes. Affordable, and it is why the per-seed
design is preferred to a single pooled test that would have been cheaper
and worthless.

## 5. Numbered predictions

Measured in `docs/114`.

1. **The pooled firm-size power law is rejected**, `p <= 0.1`, at
   n = 2.19M. Not a finding about the model — a demonstration of §3.
2. **Per seed, it is mostly not rejected.** At least **half** of the 100
   seeds give `p > 0.1` at Wright's own scale. If this fails, the firm
   size distribution is not really a power law and `docs/112` §4 needs
   rewriting, which would be the most valuable outcome here.
3. **p falls monotonically with n** across the subsample ladder
   1k → 10k → 100k → 1M, on pooled firm sizes.
4. **The lognormal is not decisively beaten.** For firm size, the
   normalised log-likelihood ratio against a lognormal has **|ratio| <
   2** — sign undetermined — in a majority of seeds. This is CSN's
   general finding for claimed power laws and I expect it here.
5. **The exponential *is* beaten** by the power law for firm size, ratio
   positive and determined in a majority of seeds. A tail this heavy is
   not exponential.
6. **Recession durations survive.** The exponential fit of durations is
   not rejected, `p > 0.1` pooled — a small sample, so §3's trap does not
   bite.
7. **Income's Pareto tail behaves like firm size**: mostly not rejected
   per seed, lognormal not decisively beaten.

Prediction 4 is the one that would most change how `docs/112` should be
read. If it holds, then "firm size is a power law" is not something
either Wright's data or ours can establish — only something neither
rules out.

## 6. What this cannot do

It cannot make the power law *true*. A passed goodness-of-fit test is a
failure to reject, and with the lognormal sitting undefeated beside it
that is a weak claim. The honest end state is likely to be: the tail is
heavy, several families fit it, and the exponent is worth reporting with
an interval and without a family claim.

It also changes nothing in the laboratory. `python -m
economy_lab.baseline` must stay at 322 metrics; this slice only reads.
