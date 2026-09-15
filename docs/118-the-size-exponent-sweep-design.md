# The size-exponent sweep: is Wright's fit a basin or a knife edge?

Written before anything is built or run. Measured in `docs/119`.

## 1. The question

`docs/116` established that M1 is load-bearing: the baseline cell is
nearest Wright's reported value on all six scoreable targets and its
three neighbours miss every one. `docs/117` §3 named what that does *not*
establish. A 2×2 samples four corners and no interior, so we know the
rule matters and we do **not** know whether its fit survives a small
perturbation. Two readings remain open:

- **(a) basin** — a wide region of settings reproduces the facts, and
  Wright's is an unremarkable point inside it.
- **(b) knife edge** — the facts hold at one setting and nowhere near it.

Reading (b) is usually damning: real economies are not finely tuned. But
there is a third possibility this experiment exists to distinguish, and
it is the interesting one. If β = 1 is a **critical point** rather than a
tuned point — the unique exponent at which growth is scale-free — then a
knife edge is where the mathematics puts it, not where the author put it,
and "the law of value" becomes the substantive claim that real economies
sit at criticality.

## 2. The instrument

M1's linearity is "sample once per member". Make the exponent continuous:

    drawn = rng.uniform(0.0, market) / members ** (1.0 - beta)

A firm of `members` members is selected `members` times per month on
average (each member is an independent candidate under SR1), so expected
monthly revenue is proportional to `members ** beta`.

- **β = 1** → divide by `members ** 0.0` = 1.0 → the bare draw → `wright`.
- **β = 0** → divide by `members ** 1.0` → `x / members` → `neutral`.
- **β < 1** → sub-proportional. Revenue grows more slowly than payroll.
- **β > 1** → super-proportional. Revenue outruns payroll.

**Why division and not multiplication.** The natural-looking
`x * members ** (beta - 1.0)` is *not* exact at the endpoints: it rounds
`1/members` to a float and then multiplies, a double rounding. Measured
over 200,000 draws, it disagrees with `x / members` on **46,338 of them**
— 23%. The division form disagrees on **0**, at both β = 0 and β = 1,
because `m ** 1.0` and `m ** 0.0` are exact. This matters beyond
tidiness: the model is chaotic in the sense that a one-ulp change to a
draw changes the remaining pool and therefore every later draw, so an
inexact endpoint would not reproduce the existing cells' trajectories at
all, and the sweep would not be continuous with `docs/116`.

**What gets built.** `market_rule = "scaled"` plus `size_exponent: float
= 1.0` on `social_architecture.Economy`. The four existing rules keep
their exact branches, so the default path is untouched and `docs/112`,
`docs/114` and `docs/116` stay reproducible. Setting `size_exponent` to
anything but 1.0 under a rule other than `"scaled"` raises, so a silent
no-op is impossible.

## 3. What gets measured, and at what scale

**`docs/116` pooled its fits across 50 seeds, and `docs/114` says that is
the wrong scale.** The exponent estimate drifts upward with sample size
— 1.084 at n = 1,000 rising to 1.406 at n = 1,000,000 — which is why
`docs/116` reports α = 1.337 against Wright's 1.038 and the two numbers
are not comparable. This sweep fits **per seed**, at n ≈ 21,900, so the
exponents can be read against Wright's reported values directly.

Two facts cannot be fitted per seed, and the code is why. `history.gdp`
and `history.wage_shares` are **yearly** (rule 1Y), so a 180-month window
yields **15 observations**: 14 GDP growth rates, and far fewer than the
20 recession durations `geometric_goodness_of_fit` requires. Those two
stay **pooled across seeds** and are labelled as such in `docs/119`.

| fact | fitted | n per seed |
|---|---|---|
| firm-size α | per seed | ≈ 21,900 |
| firm-growth kurtosis | per seed | ≈ 4,500 |
| income tail α | per seed | ≈ 15,000 |
| profit-rate skew | per seed | ≈ 1,500 |
| demises/month | per seed | 180 |
| wage share, unemployment, largest firm, firm count | per seed | direct |
| **GDP-growth kurtosis** | **pooled** | 14 |
| **recession λ** | **pooled** | too few |

Consequences for the harness: the worker fits its own run and returns
~12 summary numbers plus the three small raw series (15 GDP, 15 shares,
180 demises), discarding the 40k-element arrays. `docs/116`'s records
would have been ~240 MB at this sweep's size; these are negligible. λ is
taken from the closed form the estimator documents,
`λ = −ln(1 − 1/mean)`, since only the point estimate is needed — no
goodness-of-fit bootstrap runs here. **This sweep asks where the facts
hold, not which distributional family they belong to**; `docs/114`
answered the family question and its answer is unchanged.

**The grid.** β over [0.0, 1.5] at 0.1 spacing, plus 0.85, 0.95, 1.05 and
1.15 to resolve the neighbourhood of 1 — 20 points × 50 seeds = **1000
runs**. Measured cost of one 300-month run is 2.9 s, so ≈ 12 minutes of
simulation on four cores plus the per-seed fits. (`docs/115` estimated
its own sweep at 9 minutes by guessing; this number is measured.)

## 4. The acceptance bands, fixed now

A fact "holds at β" if its reading falls in the band below. The bands are
set around **Wright's reported values**, not around our β = 1 readings,
and they are judgement calls — stated here so they cannot be adjusted
afterwards. Prediction 7 asserts β = 1 lands inside all seven; if it does
not, the band was wrong and `docs/119` will say so rather than move it.

| # | fact | Wright | band |
|---|---|---|---|
| 1 | firm-size α (Wright convention) | 1.038 | [0.8, 1.4] |
| 2 | firm-growth excess kurtosis | Laplace = 3 | ≥ 2.0 |
| 3 | GDP-growth excess kurtosis (pooled) | Laplace = 3 | ≥ 1.0 |
| 4 | demises per month | 18 | [12, 26] |
| 5 | recession λ (pooled) | 1.22 | [0.95, 1.55] |
| 6 | income tail α | 1.3 | [0.9, 1.9] |
| 7 | wage share | 0.55 | [0.45, 0.65] |

Unemployment (Wright ~0.17, band [0.10, 0.25]) is reported as an eighth
diagnostic but is not one of the seven facts and does not count toward
the all-seven region.

## 5. Numbered predictions

1. **The endpoints are bit-identical.** `scaled` at β = 1.0 reproduces
   `wright` exactly and at β = 0.0 reproduces `neutral` exactly — every
   field of the record equal, on three seeds each. If this fails the
   instrument is not the one described and every later reading is void.
2. **Money is conserved at every β**, to 1e-6.
3. **α falls monotonically in β**, crossing Wright's 1.038 near β = 1,
   with α > 2 for β ≤ 0.5 and α < 0.8 for β ≥ 1.2.
4. **Above 1 the economy condenses.** At β ≥ 1.2 the largest firm exceeds
   500 of the 1000 actors in a majority of seeds.
5. **The non-tail facts are not critical.** Wage share, demises,
   unemployment and recession λ each stay inside their band over an
   interval of β of width **≥ 0.4**.
6. **The all-seven region is narrow, and firm size is what narrows it.**
   The set of β satisfying all seven bands has width **≤ 0.3**, and at
   both its edges the binding constraint is a tail fact — α or
   firm-growth kurtosis — not one of the other five.
7. **That region is non-empty and contains β = 1.**

Predictions 6 and 7 are the substance. **Prediction 7 is the one with a
real chance of failing, and its failure would be the most consequential
result this laboratory has produced**: it would mean no single setting of
Wright's own model produces all seven facts at once, and that the paper's
joint claim does not hold even internally. He reports the seven facts;
he never reports that one parameter setting yields all seven
simultaneously, and nobody appears to have checked.

## 6. How each outcome reads

| measured | conclusion |
|---|---|
| all-seven width ≥ 0.5 | **basin.** `docs/117` reading (a). The fit is robust and Wright's claim is about as strong as a model claim gets. |
| width ≤ 0.3, centred on 1, thin tails below and condensation above | **critical point.** A knife edge, but a principled one — β = 1 is the unique scale-free exponent. "The law of value" becomes the claim that economies sit at criticality: substantive, and checkable against real data in a way the rest of this work is not. |
| width ≤ 0.3, *not* centred on 1, or edges set by a non-tail fact | **tuned.** `docs/117` reading (b) in its damaging form. |
| empty | the joint fit was never achieved at one setting. |

## 7. The main threat to predictions 3 and 4

Predictions 3 and 4 are reasoned from theory — proportional growth is
scale-free at β = 1, sub-proportional below it, runaway above — and
`docs/117` §8 catalogues four occasions where exactly that kind of
surface reasoning failed. The specific reason it may fail here is in the
code: the draw is `U[0, market]` from the **current remaining pool**, not
from a fixed monthly budget. Whoever is selected early can take the whole
pool. That is preferential depletion, a competitive coupling the clean
returns-to-scale story does not contain, and it may dominate β entirely.

If predictions 3 and 4 fail while 6 and 7 still resolve, the experiment
has done its job. If β turns out not to behave like a returns-to-scale
exponent at all, that is itself the finding, and the honest one.

## 8. What this cannot settle

It cannot revive the firm-size power law. `docs/114` stands: a lognormal
fits better in 51 of 100 seeds and worse in 0. "Tail" here means
heavy-tailed, and α is a shape reading rather than a claim of Pareto.

It cannot say anything about real economies. Locating the critical point
of a model is not evidence that economies sit at it — that would need
data this project has never touched, and `docs/117` §7's caution applies
undiminished.
