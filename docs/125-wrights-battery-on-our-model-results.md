# Wright's battery on our own model: results

Measures `docs/124`. Four predictions passed, four failed, one resolved.
**The headline is a negative result: our laboratory does not reproduce
Wright's signature, and three of his seven measures are not the same
quantity in our ontology even when they share a name.**

## 1. Task one: Wright's estimator, calibrated

`ols_histogram_fit` added to `distributions.py`, fitted to
`P(x) ∝ x^−(α+1)` exactly as his Fig. 2 caption specifies, so its α needs
no convention conversion.

### On planted data of known exponent

Median over 5 seeds. `mc` is the minimum bin count kept.

| true α | n | MLE | OLS mc=1 | mc=2 | mc=5 | mc=10 |
|---|---|---|---|---|---|---|
| 0.8 | 10,000 | 0.779 | **−0.338** | 0.376 | 0.605 | 0.635 |
| 1.0 | 20,000 | 0.934 | **−0.114** | 0.547 | 0.789 | 0.830 |
| 1.3 | 20,000 | 1.213 | 0.248 | 0.897 | 1.055 | 1.078 |
| 1.5 | 10,000 | 1.411 | 0.532 | 1.082 | 1.228 | 1.229 |
| 1.5 | 100,000 | 1.431 | 0.568 | 1.201 | 1.309 | 1.309 |
| 2.0 | 20,000 | 1.754 | 0.933 | 1.633 | 1.659 | 1.664 |

**Prediction 1 — pass.** OLS keeping all bins is low by ~1.0 at true 1.5,
far past the 0.3 asserted. On *continuous* planted data the MLE recovers
1.500 as 1.504. On *discrete* data it reads about 0.16 low, which is our
sampler — flooring a continuous Pareto is not the zeta the discrete MLE
assumes — and is pinned as a test so it cannot later be mistaken for an
OLS effect.

**Prediction 2 — pass.** The bias is not sampling noise: at true 1.5 it
moves only 0.532 → 0.568 between n = 10,000 and n = 100,000, inside the
0.10 asserted. It persists undiminished at every n.

**Prediction 3 — pass, everywhere.** Raising `mc` moves the estimate
monotonically toward truth at every true α and every n.

**The failure mode is worse than "biased."** For true α ≤ 1.0 — Zipf, the
case Wright's whole firm-size claim is about — OLS keeping all bins
returns a **negative exponent**, which is not a distribution. Sparse
upper-tail bins carrying counts of 1 and 2 dominate the regression.

### Inverting his 1.038

On SA output, both estimators on the same samples (30 seeds):

| β | MLE | OLS | gap |
|---|---|---|---|
| 0.90 | 1.982 | 1.174 | 0.808 |
| 0.95 | 1.628 | 0.824 | 0.803 |
| **1.00** | **1.268** | **0.498** | **0.769** |
| 1.05 | 1.094 | 0.327 | 0.767 |

**Prediction 4 — resolved, and against the transcription.** Inverting
1.038 through this mapping implies a true (MLE) α of **1.844**, where our
transcription at β = 1 measures 1.268.

The like-for-like comparison is the fairer one, and it says the same
thing more modestly. Wright's caption does not say whether he dropped
sparse bins, so we tried every rule:

| min_count | 1 | 2 | 3 | 5 | 10 | 20 |
|---|---|---|---|---|---|---|
| OLS α on our data at β = 1 | 0.498 | 0.746 | 0.829 | 0.867 | **0.882** | 0.846 |

**It saturates at ≈0.88 and never reaches 1.038.** So bin handling does
not explain the difference. Estimator choice explains roughly 0.4 of the
apparent gap; a residual of about **0.16, with our transcription
thicker-tailed, is not explained by anything we have tried.**

This is the sharpest form of `docs/122` §2's warning: it is a
transcription question, and only a reader with his code or his Fig. 2
data can settle it. `docs/121` must be updated to say this rather than
its current point 1.

## 2. Task two: the battery

8 seeds per model, identical measurement code, our model configured per
`docs/124` §3 with investment slowed (see §3).

| measure | our model | SA (control) | Wright |
|---|---|---|---|
| firm-size observations | 73 | 21,588 | — |
| largest firm | 6 | 784 | ~1000 |
| firm-size α (MLE) | 0.628 | 1.226 | — |
| firm-growth ex. kurtosis | 8.921 | 4.373 | 3 (Laplace) |
| GDP-growth ex. kurtosis | 2.553 | 0.236 | 3 (Laplace) |
| **wage share** | **0.0200** | **0.5357** | **0.55** |
| demises /firm/month | 1.861 | 0.159 | ~0.18 |
| unemployment | 0.980 | 0.166 | ~0.17 |
| profit-rate skew | −0.271 | 13.064 | positive |

**Prediction 8 — pass.** The control reproduces `docs/119`: α 1.226
against 1.296 (within the 0.10 asserted) and growth kurtosis 4.373
against 3.889 (within 0.5). The instrument is sound, so the left column
is a reading about our model and not about broken measurement code.

**Prediction 5 — fail, and I should have known at design time.** I
predicted our wage share would land in [0.45, 0.65] because it is "an
accounting identity, ontology-independent." It reads **0.0200**.

`docs/99` had already measured this and derived it in closed form:
`wage share = necessary ÷ living = VLP ÷ ticks_per_worker_day`, giving
**0.0361** in the calibrated scenario. **My own prediction contradicted
our own prior document**, which I did not check.

The deeper error is a category mistake. Wright's wage share is a **money
flow ratio** — wages paid over revenue. Ours is a **value ratio** —
necessary over living labour, fixed by the subsistence basket and the
tick normalisation. They share a name and measure different things, and
comparing them was meaningless. A like-for-like comparison needs money
wages over money revenue, which we did not measure and which is the
obvious follow-up.

The second half of prediction 5 holds: firm-growth kurtosis is 8.921,
outside the two-sided Laplace band [1.5, 4.5]. Our firm growth is not
Laplace.

**Prediction 6 — fail, with the sign reversed.** I predicted employment
would correlate above 0.9 with authored `capacity_per_day`. Spearman ρ is
**−0.402**. Larger authored capacity goes with *less* employment, because
the high-capacity producers are deep upstream sectors with low direct
labour. Firm size in our model is not the authored capacity — but §3
shows it is not an emergent firm-size distribution either.

**Prediction 7 — fail, by 37×.** I predicted our demise rate would be
below 0.05 per firm per month "because our producers meet demand rather
than gamble." It is **1.861** — an order of magnitude above Wright's
0.18. Our producers do not fail to gamble; they fail constantly.

**Prediction 9 — pass.** 322 baseline metrics at zero delta, 249 tests
green, cash conserved to 1e-8 throughout.

## 3. The finding under the failures: our model has no firm-size distribution

The configuration search in `docs/124` §3 ran into a constraint that the
design underestimated, and it is the real result here.

- The employment quantum, which makes "firm size in whole workers"
  meaningful, is reachable **only inside the `producer_cash` branch**.
  Firm deaths need the same branch. So integer firm sizes and firm
  dynamics arrive together or not at all.
- With `producer_cash` **on**, the economy collapses to **≈14 producers
  employing anyone**, out of 400, with 499 bankruptcies — and this is
  **insensitive to the producer endowment across a 1000× range** (50 to
  50,000 silver, identical outcome). It is structural: `synthetic_economy`
  spreads a daily final demand of 1.0 across hundreds of commodities, so
  most producers are sub-viable under a hard budget constraint and die.
- With `producer_cash` **off**, 308 producers employ — but there are no
  bankruptcies and no integer sizes.

**So the two things Wright's battery needs are mutually exclusive in our
lab as it currently stands.** The 73 firm-size observations and largest
firm of 6 in §2 are not a thin tail; they are an economy with about three
employing firms per month. Fitting an exponent to that is not a
measurement, and the 0.628 in the table should be read as unavailable.

One thing worth recording precisely, because it looked like a defect:
**silver is conserved exactly throughout** (`cash_balance` = 0 to 1e-8).
At the shipped 15-day investment interval the regions spend 15.7M silver
on construction and cannot make payroll by day ~250. That is not a leak —
it is capacity purchase, and the `RuntimeError` is the model correctly
refusing to silently stop paying workers.

## 4. What this leaves

The docking question was whether our extra apparatus still produces
capitalism's statistical signature. **The answer is that we cannot
currently ask it.** Not because the apparatus distorts the signature, but
because at the only scale where a distribution exists, our model cannot
run the rules that generate firm dynamics without collapsing to a dozen
firms.

Three concrete follow-ups, in value order:

1. **Measure a money wage share** (wages paid ÷ revenue) so §2's row is a
   comparison rather than a category error. Cheap, and it is the one fact
   most likely to transfer.
2. **A scenario with viable demand per producer.** `synthetic_economy`
   was built to test scaling, not to be an economy where most firms can
   live. A generator that gives each producer non-trivial final demand
   would make the battery askable.
3. **Put the residual α gap to Wright**, per §1.

And `docs/121` needs amending before it is sent: point 1's claim about
the sample size is already withdrawn by `docs/123` §2, and §1 above now
replaces it with a sharper and more honest statement.

## 5. Method note

Prediction 5 failed against a number **already in our own repository**.
`docs/123` §7 concluded *"before stating what an author did, find the
sentence where they did it"* after three such failures about Wright's
paper. This is the same failure about our own documents, so the rule
generalises and should be stated without the qualifier:

> **Before predicting a quantity, search the record for it. The most
> expensive assertions are the ones about work you have already done.**
