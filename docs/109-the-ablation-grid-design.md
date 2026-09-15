# The ablation grid: design

Written before the grid is built or run. No cell has been executed and
no metric inspected; the predictions in §4 are what I expect to be
wrong about.

## 1. Why

The laboratory carries **ten independently gated behavioural rules**,
every one off by default and bit-identical when off. That discipline was
kept so each rule could be attributed. It has been used that way once:
`docs/105` crossed the producer quantum with sales-follow-production and
found the two are **only jointly effective** — quantum alone gives 0
bankruptcies and a peak consecutive idle of 1, the flag alone gives 0,
and together they give 29 idle days and the first endogenous firm death
in the project's history.

That was found by hand, because I had a reason to look there. There is
no reason to believe it is the only such pair. Ten switches have 45
pairs, 120 triples and 1024 subsets in total, and **exactly one cross
has ever been run deliberately**.

A run costs 1.4 seconds. The full factorial is 1024 runs, about 25
minutes. There is no methodological reason to prefer a 2-way sweep when
the whole lattice is affordable, and a 2-way sweep would have *missed*
`docs/105`'s finding if `producer_cash` had also been a factor, because
that result is really a three-way: no purse, no shortfall, no death.

## 2. The factors

Ten, at the values the scenarios themselves use:

| factor | off | on |
|---|---|---|
| `producer_cash` | False | True |
| `posted_prices` | False | True |
| `procurement` | False | True |
| `entry_on_margin` | False | True |
| `exit_on_return` | False | True |
| `producer_employment_quantum` | 0.0 | 1e-3 |
| `sales_follow_production` | False | True |
| `worker_mobility_strength` | 0.0 | 0.05 |
| `wage_bargaining_strength` | 0.0 | 1.0 |
| `habituation_speed` | 0.0 | 0.02 |

Held fixed: `capital_goods=True`, so Department I exists and the
machinists `docs/105` killed are present in every cell. Without it the
one interaction we already know about cannot appear, and a grid that
cannot reproduce a known result is not calibrated.

**The shock.** `demand_boom`'s: sixty days of seeding, then Dust Basin's
final demand for yayo times 1.25, then 1140 days. A boom is chosen over
`equilibrium` because at the symmetric seed most of these rules are
inert by construction — the wage premium is zero, both regions' wages
are equal, and nothing is above or below a going margin. A grid run on a
stationary circuit would measure ten rules doing nothing.

## 3. The arithmetic

For each metric *m* and each subset *S* of the ten factors, the grid
gives `m(S)`. The **interaction** of a pair (A, B) is the standard
second difference, averaged over every setting of the other eight:

```
I(A,B) = mean over C of  m(ABC) - m(AC) - m(BC) + m(C)
```

Zero means the two rules are additive: B does the same thing whether or
not A is on. Nonzero means one rule changes what the other does, and
the magnitude says by how much. Three-way interactions are the same
construction one level up.

Interactions are reported **relative to the metric's own spread** across
the grid, because an interaction of 0.01 means nothing until you know
whether the metric ranges over 0.1 or 1000.

**Fourteen metrics**, chosen to span the ledgers rather than to be
comprehensive: employment, bankruptcies, exits, capacity lost,
terminal yayo and meals prices, the realized wage share, peak wage
premium, total production, the cash-balance residual, fund wage
support, net labour migrated, liquidity curtailment, and the rate of
surplus value.

## 4. Numbered predictions

Measured in `docs/110`.

1. **Every cell runs.** 1024 of 1024 complete without an exception. If
   any cell throws, that is a defect found by the grid and worth more
   than the grid's own result.
2. **Money is conserved in every cell.** `cash_balance()` within 1e-6,
   all 1024. This is A1 tested 1024 times instead of 5.
3. **The all-off cell reproduces the committed scenario**, bit-for-bit
   against `demand_boom` with `capital_goods` on. The grid's zero point
   must be the model's.
4. **The known interaction reappears and is large.** Quantum ×
   sales-follow is among the **top three** pairwise interactions on
   bankruptcies. If the grid cannot rediscover `docs/105` it is not
   measuring what I think it measures.
5. **It is really a three-way.** The `producer_cash` × quantum ×
   sales-follow triple is larger, relative to spread, than any of the
   three pairs inside it — because without a purse there is nothing to
   be short of.
6. **At least one interaction I did not predict** exceeds 20% of its
   metric's spread. *This is the gamble and the reason to run.* If it
   fails, the finding is that the laboratory's rules are close to
   additive, which is a real and reassuring result about the model's
   design — and would mean `docs/105`'s pair is special rather than
   typical.
7. **Main effects dominate overall.** Across the fourteen metrics, an
   additive model of the ten main effects explains **more than 70%** of
   the variance. The rules were built to be separable and mostly should
   be.
8. **Mobility is not inert without bargaining.** `worker_mobility` has a
   nonzero main effect on net labour migrated with `wage_bargaining`
   **off**, because the boom moves Dust Basin's prices, which moves its
   basket cost, which moves its wage even at zero premium. I believe
   this but have never checked it, and `docs/107` measured mobility only
   with bargaining on.
9. **Procurement and posted prices interact.** Both rewrite how a sale
   is matched to a seller; I expect them non-additive on terminal
   prices, at above 20% of spread.

Predictions 6 and 9 are the ones I expect to be most informative.
Prediction 7 is the one whose failure would most change how the mod
should be built, because a non-separable rule set is one where
gameplay switches cannot be reasoned about one at a time.

## 5. What this is not

It is not a sensitivity analysis. `economy_lab.sensitivity` already
perturbs continuous calibration parameters one at a time; this crosses
**discrete rules** and looks only for non-additivity.

It is not a search for the best configuration. There is no objective
function and no cell is "right". A large interaction is a fact about the
model's structure, not a recommendation.

It changes no default behaviour and adds no rule. `python -m
economy_lab.baseline` must show 322 metrics unchanged, since the grid
only reads.
