# Fitting Wright's seven facts: design

Written before any recorder or estimator is built. `docs/100` §3 left
this open and named it honestly: *"No exponent here is claimed to match
Wright's fitted values. The paper reports fits; these are bare Hill
readings on single snapshots."* This closes it.

## 1. What is actually missing

Not capability and not compute — a 300-month run at N=1000 costs **2.8
seconds**, so a hundred seeds is five minutes. Three things:

**The instrument has no memory.** `firm_sizes()`, `incomes()` and
`unemployment_rate()` all read *current state*. Four of Wright's seven
facts are about events over time and nothing records them.

**Bare Hill is not a fit.** `docs/100`'s readings ranged **0.465 to
2.225** over months 240–300 — one snapshot is nearly pure noise. Wright
pools; §3.2 says his α is "for data collected over 15 simulated years".

**Three definitions had to be read off the paper.** They now have been,
and they are transcribed in §2 rather than invented.

## 2. Wright's seven measures, quoted

| # | fact | his measure rule | his result |
|---|---|---|---|
| 1 | firm size | *"After each month count the number of employees in each firm"*, pooled over 15 years | `P(x) ∝ x^−(α+1)`, **α = 1.038** (Axtell: 1.059) |
| 2 | firm growth | *"After each year calculate the current size `s_t` for a firm that traded at some point during the year… growth rate is `s_t/s_{t−1}`. If a firm ceased trading `s_t = 1`; if it began trading `s_{t−1} = 1`"* | Laplace on log growth |
| 3 | GDP growth | *"At the close of year t calculate the total firm income `X_t` received during that year (i.e. all income received during application of rule M1). The GDP growth rate is `X_t/X_{t−1}`"* | Laplace on log growth |
| 4 | firm demises | *"After each month count the number of firm demises… A firm demise occurs when a firm fires all its employees"* | lognormal; **≈18/month, 216/year** |
| 5 | recession duration | *"A recession begins when `X_t/X_{t−1} < 1` and ends when `X_{t+k}/X_{t+k−1} ≥ 1`"* | exponential, **λ = 1.22** |
| 6 | income | *"After each year calculate the total income received by each actor… Both wage income (from W1) and capitalist income (from M1)"* | lognormal bulk + Pareto tail **α = 1.3**, knee at ccdf ≈ 0.1 |
| 7 | rate of profit | *"After each year calculate the profit rate for each firm trading at the close… `p_i = 100(r_i/w_i − 1)`"* | gamma-like, right-skewed |

Plus the shares: wage share **0.55**, profit share **0.45**.

### Two definitional forks, decided here

**A demise is a *firing*.** Wright's rule says "fires all its employees",
so it is counted in F1 and only there. A firm that loses its last
employee to a rival's H1 poach also ceases to trade, and is *not* counted.
This is the paper's literal wording; the alternative reading would raise
the count, and if prediction 3 fails high or low this is the first thing
to re-examine.

**Revenue is gross.** Facts 3 and 7 need M1 receipts *before* wages. The
instrument's current `revenue` accumulator is already net of the wage
bill (`_pay` subtracts from it), so a **separate gross accumulator** is
needed rather than a reinterpretation of the existing one. Conflating
them would inflate GDP and deflate every profit rate.

### The exponent trap

Wright writes `P(x) ∝ x^−(α+1)`. The standard estimator (Clauset,
Shalizi & Newman) fits `p(x) ∝ x^−α_CSN`. So **α_Wright = α_CSN − 1**,
and Zipf is α_Wright = 1.0 ⟺ α_CSN = 2.0. Reporting one against the
other would manufacture a match or a mismatch out of nothing. Every
figure in `docs/112` will be labelled with which convention it is in.

## 3. What gets built

**A recorder**, opt-in, on `social_architecture.Economy`. Off by default
so existing runs and the 23 committed tests stay bit-identical. It
records per month: every firm's size, and the demise count. Per year:
each trading firm's gross revenue and wages paid, each actor's income,
and GDP as the year's total M1 receipts.

**`economy_lab/distributions.py`**, stdlib only — the project has no
third-party dependency and this slice does not introduce one. The usual
tools (numpy, scipy, the `powerlaw` package) are all unavailable, so the
estimators are written rather than imported:

- power-law MLE with `x_min` chosen by KS minimisation (CSN), discrete
  and continuous forms, with a bootstrap confidence interval;
- lognormal and exponential MLE;
- Laplace fit, plus excess kurtosis (Laplace is 3, Gaussian 0) as the
  shape test that does not depend on binning;
- skewness, for fact 7.

No OLS-on-a-histogram. Wright used it; it is the wrong estimator for a
tail and the reason his figures carry no confidence intervals. Where our
MLE disagrees with his OLS that will be *reported as a methodological
difference*, not as his model failing.

## 4. Numbered predictions

Measured in `docs/112`. 100 seeds × 300 months unless stated.

1. **Pooling fixes the noise.** The firm-size exponent from 15 pooled
   years has a bootstrap 95% CI **narrower than 0.3**, against
   `docs/100`'s snapshot range of 1.76.
2. **Firm size is Zipf-consistent.** α_Wright ∈ **[0.85, 1.25]**,
   containing his 1.038.
3. **Demises ≈ 18/month.** Our mean ∈ **[9, 27]**. This is the sharpest
   quantitative target in the paper and the one I most expect to miss.
4. **Recessions are exponential with λ near 1.22.** λ ∈ **[0.8, 1.8]**.
5. **The wage share is ≈ 0.55.** Mean ∈ **[0.50, 0.65]**. `docs/100`
   read 0.595 on one seed; this is the multi-seed version.
6. **GDP log growth is leptokurtic**, excess kurtosis **> 1** — Laplace
   is 3, Gaussian 0. A tent, not a bell.
7. **Firm log growth is leptokurtic**, excess kurtosis **> 1**.
8. **The profit rate is right-skewed**, skewness **> 0**.
9. **Income has a Pareto tail**, α_Wright ∈ **[0.9, 1.8]** with the knee
   in the top 10–20% of incomes.
10. **Nothing in the laboratory moves.** 322 baseline metrics unchanged,
    and the instrument with the recorder **off** is bit-identical to
    before.

Predictions 3 and 4 carry the most information: they are the only two
where Wright reports a *number* rather than a shape, so they are the only
two that can fail quantitatively rather than qualitatively.

## 5. What a failure would and would not mean

If the shapes hold and the numbers miss, the transcription is faithful
and some measurement convention differs — the demise fork in §2 is the
likeliest culprit, and it is a one-line change to test the other reading.

If a **shape** fails — growth not leptokurtic, no Pareto tail — that is
evidence the transcription is wrong somewhere, and `docs/100` §2 already
lists six rule bodies that were wrong once. That would be the valuable
outcome, and it is why this is worth doing before leaning on the
instrument any further.

What it cannot do either way is validate our own laboratory. This
validates the **instrument** — whether our Wright is Wright enough to
argue with, which `docs/110` §4's challenge to his generality currently
assumes without having checked.
