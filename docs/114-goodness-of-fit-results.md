# Does a power law actually fit? Results

`docs/113` is the design. **Five of seven predictions hold, one is
refuted and one is split** — and the refutation is in the direction
*against* the power law, not for it.

**The headline: across 100 seeds at Wright's own scale, a lognormal fits
his firm-size data better than a power law does in 51 seeds and worse in
zero.** `docs/112` §4's "the shapes all hold" needs qualifying, and this
document qualifies it.

## 1. The scorecard

| # | prediction | result |
|---|---|---|
| 1 | pooled firm size rejected at n = 2.19M | **holds** — p = 0.00 |
| 2 | ≥ half of seeds not rejected at Wright's scale | **holds** — 64/100 |
| 3 | p falls with n | **holds** — 0.74 → 0.46 → 0.00 → 0.00 |
| 4 | lognormal undetermined in a majority | **refuted** — 49/100, and it *wins* in 51 |
| 5 | exponential beaten by the power law | **holds** — 98/100 |
| 6 | recession durations survive | **holds** — p = 0.223, after I fixed the null |
| 7 | income behaves like firm size | **split** — 46/100 not rejected; lognormal undetermined in 99/100 |

## 2. The finding: it is a heavy tail, but probably not a power law

Three independent lines point the same way.

**The lognormal wins.** Normalised log-likelihood ratio against a
lognormal, per seed, firm sizes at n ≈ 21,868:

| | seeds |
|---|---:|
| favours the **power law** (ratio ≥ +2) | **0** |
| undetermined (│ratio│ < 2) | 49 |
| favours the **lognormal** (ratio ≤ −2) | **51** |

Median **−2.03**. Not one seed in a hundred prefers the power law. The
power law is *adequate* — not rejected in 64 of 100 seeds — but the
lognormal is *better*, and "firm size follows Zipf's law" is a claim
about which family, not about adequacy.

**The exponent will not sit still.** On pooled data, as the sample grows:

| n | Wright's α | p |
|---:|---:|---:|
| 1,000 | **1.084** | 0.74 |
| 10,000 | 1.223 | 0.46 |
| 100,000 | 1.248 | 0.00 |
| 1,000,000 | 1.406 | 0.00 |
| 2,186,842 | 1.399 | 0.00 |

A genuine power law's MLE is consistent: more data should tighten the
estimate around a fixed value, not walk it from 1.08 to 1.41. Drift on
this scale is what a not-quite-power-law tail looks like when you keep
feeding it data.

**The pooled fit is rejected outright**, p = 0.00 — though on its own
that means little, for the reason in §3.

Together: the tail is heavy, several families describe it, and the
exponent depends on how much data you collected. Reporting "α = 1.038,
therefore Zipf" is more than the data supports.

### This also explains `docs/112`'s firm-size gap

`docs/112` §3 recorded a residual: our α of 1.257–1.399 against Wright's
1.038, and could only say his value sat inside our per-seed spread. The
ladder says why. **At n = 1,000 we measure 1.084.** Wright's exponent is
what you get at Wright's sample size. The gap was never a difference
between his model and our transcription; it is the same estimator drifting
on different amounts of data.

## 3. The sample-size trap, measured

`docs/113` §3 predicted that a pooled test would reject a power law for a
deviation too small to matter. It did — p = 0.00 at n = 2.19M with a KS
distance of **0.0304**, *smaller* than the 0.0714 that passed comfortably
at n = 1,000. The statistic improved and the verdict reversed, purely
because the test got more powerful.

The suite reproduced this by accident too: the same lognormal sample is
rejected as a power law at n = 8,000 and survives at n = 4,000. Both are
pinned as tests, because it is the effect the per-seed design exists to
avoid.

**A goodness-of-fit p-value without its sample size is not interpretable.**

## 4. Two of my own errors, both in the null

**The recession test.** I first ran durations against a *continuous*
exponential and got KS 0.4975, p = 0.000 — apparently a flat refutation
of Wright's fact 5. It was my null that was wrong: durations are whole
years, and a continuous fit cannot follow a step function. Against a
**geometric**, the exponential's discrete analogue, the answer is
KS 0.0270, **p = 0.223, not rejected**, with λ = 1.165 against Wright's
1.22.

**The discrete KS statistic itself** then read 0.6881 on data drawn from
the very distribution being fitted, because I carried the continuous
statistic's left-limit term onto a discrete support, where it compares
`F(1)` against an empirical zero. Dropping it gives 0.0088 on true
geometric data. Both mistakes were caught by validating against
distributions with known answers rather than by reading the code.

This is the third time in two days that an apparent failure of Wright's
model has turned out to be my estimator — after `docs/112`'s λ and its
firm-size exponent. The pattern is worth naming: **when a reimplementation
disagrees with a paper, suspect the measurement before the model.**

## 5. What this does and does not say about Wright

It does not say he is wrong, and it is not a criticism peculiar to him.
CSN re-analysed two dozen published power laws and found most of them
lost to a lognormal; Wright's firm-size distribution is in ordinary
company. His model's tail is genuinely heavy — the exponential loses in
98 of 100 seeds — and every other fact in `docs/112` stands: demises to
0.3%, unemployment to 0.6%, the shares to 2%, recessions now to 5% under
the right null.

What it says is narrower and still worth saying. **"The model generates
Zipf's law of firm size" is not established by this evidence**, by his
method or by a better one. The defensible statement is that firm size has
a heavy right tail whose exponent is around 1.1–1.4 depending on sample
size, and which a lognormal fits at least as well.

And note what made this sayable: a validated transcription. The claim is
about *his model's behaviour*, not about our reading of his prose — which
is what `docs/111` and `docs/112` bought.

## 6. What is still open

The income tail is the weakest result here: not rejected in only 46 of
100 seeds, with the lognormal comparison undetermined in 99 of 100. That
is neither a pass nor a refutation, and it is the one place where more
work would change the answer rather than confirm it.

`docs/112` §6's other item — the capped `x_min` grid — stands unchanged
and is still an approximation.
