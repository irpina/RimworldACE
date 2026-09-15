# The ablation grid: results

`docs/109` is the design. **Four of nine predictions hold, four are
refuted, and one turned out not to be measurable.** The grid found three
things nobody knew, and one of them qualifies a document written earlier
the same day.

## 1. Prediction 1 fails immediately: the switches are not a cube

640 of 1024 cells threw. Not a defect — the model **validates rule
prerequisites**:

```
ValueError: procurement needs producer_cash and posted_prices switched on   (384 cells)
ValueError: exit_on_return needs procurement switched on                    (256 cells)
```

`docs/109` said "ten independently gated behavioural rules" and built a
free lattice on that premise. They are not independent. They form a
**dependency stack**: posted prices and producer cash underneath,
procurement on top of both, exit on top of procurement. The real design
space is 6 market-stack levels × 2 entry × 2⁵ others = **384 cells**,
which is exactly the number that survived.

Nothing was lost — the grid is complete on its true shape, and the
failure is more useful than the prediction would have been. But it is the
fifth instance of this project's recurring error in a new costume:
**I described the rules from their defaults rather than from their
validation.** `docs/101`'s rule was *before reporting a rule is absent,
search for it*; `docs/108` added *before reporting a branch is dead, find
the configuration that reaches it*. This one is **before crossing two
rules, check whether the model lets you.**

Prediction 9 dies with it. Procurement × posted prices is **not
measurable**: there is no cell with procurement on and posted prices off,
so the interaction is undefined by construction rather than small.

## 2. The predictions

| # | prediction | result |
|---|---|---|
| 1 | every cell runs | **refuted** — 640 threw, on prerequisites |
| 2 | money conserved in every cell | **holds** — max 2.14e-08, 0 over 1e-6 |
| 3 | all-off cell reproduces the scenario | **holds** — bit-for-bit |
| 4 | quantum × follow top-3 on bankruptcies | **refuted** — it ranks far below |
| 5 | the cash triple beats its pairs | **split** — yes on employment, no on bankruptcies |
| 6 | an unpredicted interaction above 20% | **holds** — several, the largest 58% |
| 7 | additive model explains >70% | **refuted** — 0.19 to 1.00 by regime |
| 8 | mobility not inert without bargaining | **holds** |
| 9 | procurement × posted interact | **not measurable** |

Prediction 2 is worth its own line: **A1 is now tested 384 times instead
of 5**, across every combination the model permits, and the worst
residual is 2.14e-08.

## 3. Finding one: procurement switches the death mechanism off

The largest interaction in the grid, at **58% of the metric's spread**,
is procurement × the producer quantum on bankruptcies. It is negative,
and what it means is blunt. With the quantum and sales-follow both on:

| regime | deaths | employment |
|---|---:|---:|
| bare | 0 | 0.7112 – 0.7123 |
| posted | 0 | 0.4524 – 0.5078 |
| cash | 8 – 10 | 0.2643 – 0.2772 |
| **cash+posted** | **8 – 51** | 0.2438 – 0.2869 |
| +procurement | **1** | 0.2847 – 0.4735 |
| +exit | **2** | 0.1765 – 0.1788 |

Under `cash+posted` the quantum raises mean bankruptcies from 0 to 29.4.
Under `+procurement` it raises them from 1 to 1 — **no effect at all**.
Procurement replaces the pool's two consumption passes with the fund and
the workers buying from producers' own stocks (`docs/59`), and that
routing keeps purses solvent enough that the wage bill stops binding.

The biggest interaction in the laboratory is **one rule disabling
another rule's mechanism entirely**. That is a more consequential kind of
non-additivity than two rules amplifying each other, and no test in the
repo would have caught it.

## 4. Finding two: `docs/105`'s two deaths were a floor

`docs/105` reported the first endogenous firm death — 2 bankruptcies, on
day 582 — in the `cash` regime, which is the only one it ran. Under the
boom the same regime gives 8–10. **Add posted prices and the same two
rules give up to 51.**

So the cascade's magnitude is dominated by a rule `docs/105` never
varied. Its qualitative finding stands exactly as written — the quantum
and sales-follow are jointly necessary, and 0 deaths become some deaths —
but "the first endogenous firm death" was the *threshold* of the
phenomenon, not its scale. A 25× range across regimes is the finding, and
it was invisible from a single configuration.

This is also why prediction 4 failed. Quantum × sales-follow scores only
+0.031 on bankruptcies pooled across the grid, and the top three pairs
are procurement × quantum (0.576), procurement × entry (0.414) and
producer cash × quantum (0.335). The `docs/105` pair is real but **it is
not the main event**; it is a small term sitting inside much larger ones
about the market stack.

## 5. Finding three: migration reverses sign, and `docs/107` is scoped

`docs/107`, written earlier today, predicted and measured that labour
flows *toward* the boom. Across the grid, Dust Basin's net migration:

| regime | net labour to Dust Basin | cells losing |
|---|---|---:|
| bare | +0.0555 … +0.1064 | 0/32 |
| cash | +0.0555 … +0.2117 | 0/32 |
| posted | −0.1926 … +0.6818 | 8/32 |
| cash+posted | −0.2172 … +0.8905 | 6/32 |
| +procurement | −0.3892 … +0.4684 | 16/32 |
| **+exit** | **−0.9383 … −0.5049** | **32/32** |

In **62 of 192** mobility-on cells the boom region *loses* labour, and
under `+exit` it loses in **every single one**.

The rule is not wrong and `docs/107` is not wrong — it measured the
`bare` regime, where the grid confirms migration is positive in 32 of 32
cells. What is wrong is the generality the wording invites. The
mechanism is legible: with exit on, capacity withdraws from Dust Basin,
employment collapses to 0.177, the reserve army loosens, the premium
goes **negative**, and labour leaves the region the boom was supposed to
attract it to. Mobility faithfully follows the wage; under exit the wage
points the other way.

**`docs/107` prediction 5 is hereby scoped to the regime it was measured
in.** Reporting it as a property of the model was the same error as
`docs/98`'s wage-share headline: a true measurement of one configuration,
stated as a fact about the laboratory.

## 6. Prediction 7: additivity is regime-dependent

The share of variance an additive six-factor model explains, by regime,
runs from **0.19 to 1.00**. Some metrics are essentially additive
everywhere (`wage_share` 0.94–1.00); others collapse exactly where the
market stack is deepest (`employment` 0.33 and `yayo_price` 0.41 under
`+procurement`; `wage_premium` 0.34 under `cash`).

So the rules are separable in the shallow regimes and **not** separable
in the deep ones. `docs/109` said prediction 7's failure "would most
change how the mod should be built, because a non-separable rule set is
one where gameplay switches cannot be reasoned about one at a time."
That is the situation, conditionally: a player-facing toggle can be
reasoned about alone in a bare economy and cannot once procurement is
underneath it.

(`cash_residual`'s low R² — 0.19 to 0.76 — is floating-point noise at
1e-8 and means nothing. It is listed for completeness, not as a result.)

## 7. What this changes

Nothing in the model. The grid reads; no rule was added or altered, and
`python -m economy_lab.baseline` is unchanged at 322 metrics.

What it changes is how results here should be reported. Three of the five
most recent documents stated a single-configuration measurement as a
property of the laboratory, and in each case a second configuration
existed that would have said otherwise. The grid is cheap — 384 cells,
about forty minutes on four cores — and it is now a standing instrument.
**Before a finding about the model goes into a document, run it across
the regimes.**

`economy_lab/grid_results.json` carries the raw cells so the arithmetic
here can be recomputed without re-running the sweep.
