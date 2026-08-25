# Prices of production: results

Recorded after implementing the design in
`docs/26-prices-of-production-design.md`.

## Headline

The classical price system solves, the uniform profit rate comes out of the
technique and the real wage with no authored price anywhere in the
derivation, and **the answer is that these prices are worse than the ones
they were meant to replace.**

- All 111 tests pass (97 prior + 14).
- **No behavioral metric moved.** The computation is an observation; nothing
  feeds back into prices, costs, or the order book. 100 metrics to 114 by
  pure insertion.
- The uniform profit rate is **38.344**, and it is fixed by the wage good
  alone. Meals is the only basic commodity in the whole circuit.
- Yayo's price of production is **71.6×** its authored ratio to meals.
- Total price can be made to equal total value, and total profit is then
  **1.526×** total surplus. The two invariance postulates do not both hold.
- Every prediction in `docs/26` §7 held except **7.5**, which was wrong for
  an instructive reason recorded in §6.

`docs/24` concluded that the authored-price wedge could not be closed while
`MarketValue` is the anchor, and named this as the resolution. It is not the
resolution. The blocker is not the price theory; it is the **meals-only
subsistence basket**, which has been carried as a caveat since `docs/17` and
is now a hard prerequisite.

## 1. Meals is the only basic commodity

Sraffa's distinction: a commodity is *basic* if it enters, directly or
indirectly, into the production of every commodity. The classification the
solver computes is a single name.

| commodity | enters | basic |
|---|---|---|
| meals | every sector, through the wage | **yes** |
| chemfuel | psychoid leaves, yayo | no |
| psychoid leaves | yayo | no |
| yayo | nothing | no |

Meals reach every sector because every sector employs labor and labor is
reproduced by the basket. Chemfuel does not, because the provisioning
process has no modelled inputs — the raw-food stages sit outside the
boundary, exactly as `docs/17` set them.

The consequence is the whole of section 2: `r` depends **only** on the basic
subsystem, so the entire material circuit — the refinery, the fields, the
drug lab, their input ratios and their labor — has no influence on the
profit rate at all.

## 2. The profit rate is a corn model, and equals the rate of surplus value

With one basic commodity produced by labor alone, the system collapses to

```
r  =  T / (b · l)  −  1  =  24000 / (2 × 305)  −  1  =  38.344262
```

the working day over the labor embodied in a day's basket. That is the
*rate of surplus value*, arrived at from the price side without a single
value magnitude entering the computation.

**When the wage good is produced without means of production, the uniform
profit rate and the rate of surplus value are the same number.** It is
Ricardo's corn model, falling out of the model's own data rather than being
assumed.

The two figures the laboratory now reports do differ, by exactly one thing:

| quantity | value |
|---|---:|
| price system, `r` | 38.344262 |
| value ledger, cumulative s/v | 38.298137 |
| gap | **0.1204%** |

The price system omits fixed capital (`docs/26` §3.5) while the value system
carries it. Tested rather than tolerated: the difference between the two
baskets is asserted to equal the basket quantity times the plant's embodied
labor per meal, to nine places.

That gap is also the second reason the exercise cannot be closed here.
Bringing fixed capital into the price system means making machinery a
produced commodity — Department I, the next item on the backlog.

## 3. The prices, and why they are unusable

Relative to the wage good, because the eigenvector fixes only relative
prices:

| commodity | labor value | **price of production** | authored |
|---|---:|---:|---:|
| meals | 1 | **1** | 1 |
| chemfuel | 0.08202 | **0.08197** | 0.15333 |
| psychoid leaves | 0.15554 | **0.31272** | 0.12667 |
| yayo | 2.41020 | **100.22318** | 1.40000 |

Read the last row again. A uniform profit rate of 38 says a unit of yayo
should exchange for a hundred meals. RimWorld says one and a half.

The mechanism is compounding, and it is not a bug:

- chemfuel and meals are pure-labor goods, so each is `(1 + r) · w · l` and
  the markup cancels in their ratio — **chemfuel prices at exactly its
  direct-labor ratio, 25/305**, asserted to twelve places;
- leaves take chemfuel, so the markup applies once to the chemfuel and again
  to the leaves — **2.01× the value ratio**;
- yayo takes eight leaves, so the markup applies twice more on a large
  quantity — **41.6× the value ratio**, and **71.6×** the authored one.

A gross markup of 39.34 meeting a two-stage input chain gives roughly 39²
on the input-heavy part. Nothing in the arithmetic is wrong. The input to
the arithmetic is wrong.

### The other normalization is no kinder

Scaled so that gross output totals what it totals at RimWorld's prices:

| commodity | price of production | authored | ratio |
|---|---:|---:|---:|
| chemfuel | 0.031 | 2.300 | 0.013 |
| psychoid leaves | 0.117 | 1.900 | 0.062 |
| meals | 0.375 | 15.000 | 0.025 |
| yayo | 37.543 | 21.000 | 1.788 |

Yayo swallows the entire envelope — it is 64% of gross output by value and
97% of it by production price — so everything else is crushed toward zero. A
meal at 0.37 silver while a unit of yayo is 37.54 is not a price system any
player would accept and not one this project should ship.

## 4. Marx's two invariance postulates

Normalized so that total price equals total value, per day of gross output
at equilibrium:

| quantity | work-ticks |
|---|---:|
| total price of gross output | 23,002.7 |
| total value of gross output | 23,002.7 |
| living labor | 15,075.2 |
| necessary labor | 383.6 |
| **total surplus value** | **14,691.5** |
| **total profit** | **22,418.1** |
| **profit / surplus** | **1.5259** |

The first equality is imposed by the normalization. The second then misses
by 53%. Choosing the other normalization moves the discrepancy into the
first equality instead; it does not remove it.

This is the transformation problem stated as a measurement rather than an
argument, and it is a companion to `docs/24`'s sectoral result. There, every
sector performed surplus labor at the same rate while realizing wildly
different money rates — 72.58 for chemfuel against 11.18 for yayo. Here the
*aggregate* fails to reconcile as well, in the same direction and for the
same structural reason: a uniform profit rate distributes surplus by size of
advance, and value distributes it by labor performed.

## 5. What actually blocks adoption

Two things, neither of which is the price theory.

**The subsistence basket is meals only.** `r = T / (b · l) − 1` says the
profit rate *is* the reciprocal of the basket's share of the working day.
Necessary labor is 2.5% of the day here, so `r` is 38 rather than something
near 1. Every headline ratio the project reports already carried this
caveat; the caveat has now propagated into the price system, where it does
visible damage rather than merely inflating a number.

The size of the correction needed is worth stating plainly. A profit rate of
1.0 — a rate of surplus value of 100%, which is a defensible order of
magnitude — needs a basket embodying half a working day, 12,000 ticks. In
meals alone that is **39 meals per worker-day**. The basket cannot be fixed
by feeding workers more; it has to contain shelter, clothing, medicine and
recreation, which is exactly what `docs/17` said it should eventually
contain and exactly what has not been built.

**There is no turnover period.** `r` is a rate per production period and the
model's period is one day. A daily 38 is not comparable to any empirical
profit rate, and this document does not present it as one. Capital that
turns over once a day is an artifact of a laboratory in which capacity is
denominated per day; real turnover is months, and the eventual runtime model
will need an explicit turnover time before any profit rate it computes can
be shown to a player.

So the backlog reorders itself with evidence rather than by taste. The
enlarged basket stops being the third item behind capacity depreciation and a
capital-goods sector, and becomes a **prerequisite** for the price system
that `docs/24` named as the destination.

## 6. Prediction scorecard

Predictions were hand-derived from the coefficients before any code existed,
so this scores the implementation against an independent derivation as well
as scoring the reasoning.

### Correct

| prediction | predicted | measured |
|---|---|---|
| 7.1 meals is the only basic | meals | meals |
| 7.2 profit rate | 38.344262 | **38.344262** |
| 7.3 gap to ledger s/v | ≈0.12% | **0.1204%** |
| 7.4 chemfuel relative to meals | 0.08197 | 0.08197 |
| 7.4 leaves relative to meals | 0.31271 | 0.31272 |
| 7.4 yayo relative to meals | 100.2296 | 100.22318 |
| 7.6 yayo against authored | ≈72× | **71.59×** |
| 7.8 profit / surplus | ≈1.52 | **1.5259** |
| 7.9 behavioral movement | none | none |

The residual differences in 7.4 and 7.8 are the fixed-capital term working
through the labor values used in the normalization, plus hand-arithmetic
rounding. Neither is a discrepancy in the solve.

### Wrong: 7.5, "chemfuel's production price equals its value ratio exactly"

It does not. The measured ratio of the two is **0.999383** — right to four
figures, and not exact.

The reasoning was that both meals and chemfuel are pure-labor goods, so both
systems scale with `l` and the ratio survives. That is true of the *price*
system, where chemfuel prices at exactly `25/305`. It is not true of the
*value* system, because since `docs/23` labor values carry the labor
embodied in each sector's plant, and the drug-lab-to-stove ratio is not the
same as the direct-labor ratio.

The prediction forgot the model's own most recent feature. That is worth
recording as more than an arithmetic slip: the omission in §3.5 is not
cosmetic bookkeeping, it changes which identities hold exactly. The test
now asserts the exact identity where one exists — against direct labor — and
asserts the value ratio equals `(l + capital) / (l + capital)` separately,
so both facts are pinned rather than approximated.

### Not wrong, but under-stated

`docs/26` §7.7 predicted the conclusion would be negative and named the
meals-only basket. It did not anticipate how *far* the deviations would go:
"far less defensible than the authored ones" was written expecting something
like a factor of five, not seventy-two. The direction was right and the
magnitude was not estimated at all.

## 7. What this adds, and what it does not

**Adds.** A price system with no authored magnitude in it, and a profit rate
that is an outcome rather than a coefficient — the same promotion `docs/20`
gave the rate of surplus value. Sraffa's basics theorem, asserted on a
purpose-built three-good economy: changing the non-basic sector's technique
leaves the profit rate *bit-identical* while changing the wage good's moves
it from 1.0 to 1.5. And a numerical statement of the transformation problem
at the aggregate level to sit beside `docs/24`'s sectoral one.

Relative surplus value now shows in the price system too. In
`technique_change`, halving the living labor in part of society's meal
output lifts the uniform profit rate from **38.34 to 44.06** — with the
working day, the basket and every material technique untouched. The wage
good is the only lever on `r` because it is the only basic commodity.

**Does not add.** The model's prices are unchanged and the equilibrium is
still exactly stationary. The authored-price wedge measured in `docs/24` is
still two-thirds of the upstream price and is not closed by this session.
`r` remains uninterpretable as an empirical rate until there is a turnover
period, and incomparable to the value rate of profit 1.77 for a structural
reason rather than a numerical one: `r` sees only basics, while `s/(c+v)`
sees all the capital in the economy.

## 8. Where this leaves the next step

The backlog behind `docs/24` was: capacity depreciation and exit, a
capital-goods sector, an enlarged basket. This session's result promotes the
third and gives the second a second reason to exist.

1. **Enlarge the subsistence basket.** Now a prerequisite rather than a
   caveat, and the cheapest of the three. It brings s/v, c/v, the value rate
   of profit *and* the price of production system down to defensible
   magnitudes in one change, and it is the only one of the three that makes
   every existing headline number more trustworthy.
2. **A capital-goods sector.** Independently needed — building capacity
   still spends silver without consuming material — and it is also what
   would let fixed capital into the price system and close the 0.12% gap
   honestly.
3. **Capacity depreciation and exit**, unchanged in priority.

And the standing recommendation from the roadmap in `HANDOFF.md` is
unaffected: the scale test should still jump the queue once the economics
reaches a natural stopping point, because a structural surprise is cheaper
to absorb with fewer mechanisms in place.

## Reference decision

Two commits. The first implements the solver and its tests with no metric
moving; the second adds fourteen observations as a pure insertion. 100
metrics to 114.
