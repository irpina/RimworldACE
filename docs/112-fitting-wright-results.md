# Fitting Wright's seven facts: results

`docs/111` is the design. **Seven of ten predictions hold, two are
refuted and one is split — and both refutations are about my
estimator, not his model.** `docs/100` §3 is closed.

100 seeds, 120 months of burn-in discarded, then a 180-month window —
Wright's own "15 simulated years". 2.19M pooled firm-size samples, 1.49M
incomes, 158k firm-years of profit.

## 1. The scorecard

| # | prediction | result |
|---|---|---|
| 1 | pooled CI narrower than 0.3 | **holds** — 0.281, against a snapshot range of 1.76 |
| 2 | firm size α ∈ [0.85, 1.25] | **refuted** — 1.399 by MLE, 1.257 by his method |
| 3 | demises ∈ [9, 27]/month | **holds** — **17.95**, against his 18 |
| 4 | recession λ ∈ [0.8, 1.8] | **refuted as stated** — 0.688 by MLE, **1.285** by his |
| 5 | wage share ∈ [0.50, 0.65] | **holds** — 0.539, against his 0.55 |
| 6 | GDP growth excess kurtosis > 1 | **holds** — 2.491 |
| 7 | firm growth excess kurtosis > 1 | **holds** — 3.922 |
| 8 | profit rate skewness > 0 | **holds** — 61.4 |
| 9 | income α ∈ [0.9, 1.8], knee 10–20% | **split** — α 1.178 holds; knee at 8% |
| 10 | nothing in the laboratory moves | **holds** — 322 metrics, 23 tests |

Unpredicted and worth recording: **unemployment 0.171**, against
Wright's ~17%. Money conserved to 1.28e-09 across all 100 seeds.

## 2. The headline: the sharpest number in the paper matches

Wright's §3.4: *"In the simulation on average 18 firms die each month and
therefore on average 216 firms die each year."*

Ours: **17.95 per month, 215 per year.**

That is a 0.3% agreement on the one quantity in the paper that is a raw
count rather than a fitted exponent — no estimator between the model and
the number, so nothing can be tuned to produce it. Together with
unemployment at 0.171 against his ~17% and the wage share at 0.539
against his 0.55, the transcription is behaving like his model and not
merely like something with the same shape.

It also retires `docs/111` §2's worry. The demise fork — counting only
firings, not a firm losing its last employee to a poach — was decided on
his literal wording with the note that *"if prediction 3 fails high or
low this is the first thing to re-examine."* It did not fail. The
literal reading is right.

## 3. Both refutations are my estimator, not his model

### Recessions: the failure was entirely mine

I predicted λ ∈ [0.8, 1.8] and measured **0.688** — refuted. Then I
fitted it the way Wright did, by OLS on the log-linear histogram:

| | λ |
|---|---|
| MLE, `1/mean` | 0.688 |
| **OLS on the histogram, his method** | **1.285** |
| **Wright** | **1.22** |

The fact holds. What failed was my choice of estimator: Wright's λ is a
*histogram decay slope*, and he glosses it as "an average recession
duration of 1.22 simulated years", which for an exponential it is not —
the mean of an exponential with λ = 1.22 is 0.82. The two numbers in his
own sentence are inconsistent, and I predicted against the wrong one.
Our duration histogram — 318, 120, 33, 8, 2 for one to five years — is
exponential on his reading and matches his slope to 5%.

### Firm size: a real residual gap, and the per-seed spread is why

Here the estimator explains part and not all:

| | Wright's α |
|---|---|
| our MLE (CSN, KS-chosen `x_min` = 46) | 1.399 |
| **our OLS, his method** | **1.257** |
| **Wright** | **1.038** |

Switching to his estimator moves us a third of the way and leaves a gap.
The honest reading is in the per-seed numbers: single-seed α ranges
**0.906 to 1.978**, median 1.297. **His 1.038 sits comfortably inside
our per-seed range.** Pooling 100 seeds is not what he did — he reports
one run — and pooling across seeds steepens the tail, because each seed's
few giant firms are giant at different sizes and pooling washes out the
extreme tail that flattens any single run.

So: consistent with him, not centred on him. And the spread is the point
`docs/100` was already making. One run cannot pin this exponent to
better than about ±0.5, which means **1.038 and 1.257 are not
distinguishable on the evidence his paper presents** — his figure carries
no confidence interval, because OLS on a log-log histogram does not
produce one.

## 4. The shapes all hold

Facts 2, 3, 6 and 7 are qualitative in the paper and qualitative here:

- **Firm growth** excess kurtosis **3.922** and **GDP growth** 2.491,
  against Laplace's 3 and Gaussian's 0. Tents, not bells, measured by a
  moment rather than by eyeballing a histogram's shape.
- **Income**: a Pareto tail at α = **1.178** against his 1.3, over the
  top **8.0%** of incomes. He says the knee is "at around P(M ≥ m) = 0.1"
  and the power law "holds for at most 10% of incomes" — so 8% agrees
  with him and refutes my prediction band, which I set at 10–20% without
  reading his sentence carefully enough. Gini 0.491.
- **Profit rate** skewness **61.4** — right-skewed, emphatically, as
  his figures 10 and 11 show.

## 5. What this licenses, and what it does not

`docs/110` §4 put a question to Wright: his seven facts are attributed to
the social relations of production, but our ablation grid found that
changing the *exchange institution* — while leaving the firing rule
intact — takes firm deaths from 29 a month to none. That challenge rested
on a transcription we had only checked qualitatively.

**It is now checked quantitatively.** Demises to 0.3%, unemployment to
0.6%, wage share to 2%, recession decay to 5%, income tail and both
growth distributions in shape, and firm size consistent within the spread
his own single run cannot resolve. The instrument is Wright's model
closely enough to argue with.

What it does not license is any claim about our *laboratory*. This
validates the instrument. And it does not show Wright is wrong about
anything: the one real residual, firm size, is a gap of 0.22 in an
exponent whose single-run standard error is several times that.

The methodological finding stands on its own and is not about him
personally: **two of his seven headline numbers are estimator artifacts
in the weak sense that a different, better estimator on the same data
gives a materially different number** — 1.399 against 1.038 for firm
size, 0.688 against 1.22 for recessions. Anyone comparing a model to this
paper needs to fit the way he fitted, or the comparison measures the
estimator.

## 6. Open

`economy_lab/distributions.py` caps the candidate `x_min` grid at 200
points, which is what makes the fit tractable on 2.19M samples. The grid
is far finer than the exponent's confidence interval and moving it did
not move the answer, but it is an approximation and it is recorded here
rather than buried.

The KS goodness-of-fit test with a synthetic bootstrap — CSN's step for
asking whether a power law is the right family at all, not just what its
exponent is — is **not** implemented. The KS distances are reported
(0.0304 for firm size) but not converted to p-values. That is the
remaining piece, and the honest statement today is that we have fitted
power laws without testing whether power laws fit.
