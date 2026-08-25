# The enlarged subsistence basket: results

Recorded after implementing the design in
`docs/28-enlarged-subsistence-basket-design.md`.

## Headline

The basket is now food, clothing and medicine, built from RimWorld's own
numbers. Every ratio built on the value of labor-power falls by about 30%.
**And `docs/27` was wrong to call this the prerequisite for a usable price
system**, exactly as `docs/28` §7.6 predicted it would be.

- All 124 tests pass (111 prior + 13).
- The equilibrium is still **exactly stationary** — zero price range, six
  commodities, both regions, four in-game years — and all three ledgers
  still close.
- Rate of surplus value **38.30 → 26.71**. Organic composition
  **20.67 → 14.42**. Value rate of profit **1.768 → 1.733**, which is the
  interesting one.
- Uniform profit rate **38.34 → 24.62**, and for the first time it is *not*
  the rate of surplus value. Chemfuel became a basic commodity and the
  general Sraffa case arrived with it.
- Yayo's price of production against its authored ratio: **71.6× → 38.7×**.
  Halved, and still unusable.
- The reason no basket can fix this, as one number: **one provisioner's
  working day feeds 39.3 workers.**

## 1. What the basket costs, and what it buys

| component | def | ticks each | per worker-day | ticks | silver |
|---|---|---:|---:|---:|---:|
| meals | `MealSimple` | 305.36 | 2.0 | 610.72 | 30.00 |
| garments | `Apparel_BasicShirt` | 1643.60 | 0.125 | 205.45 | 10.72 |
| herbal medicine | `MedicineHerbal` | 400.02 | 0.125 | 50.00 | 1.25 |
| **basket** | | | | **866.17** | **41.97** |

Necessary labor rises from **2.54% to 3.61%** of the working day. Meals
remain 70.5% of the basket by labor and 71.5% by money — clothing and
medicine together are less than a third of a bundle that is still
food-dominated, because in RimWorld's data everything except food is cheap
in labor.

The value of labor-power was understated by 42%. It is now understated by
less, and the direction of every correction was as predicted.

## 2. Two of three headline ratios fall; the third barely moves

| quantity | meals only | enlarged | change |
|---|---:|---:|---:|
| rate of surplus value s/v | 38.298 | **26.708** | −30.3% |
| organic composition c/v | 20.666 | **14.415** | −30.2% |
| value rate of profit s/(c+v) | 1.7677 | **1.7326** | **−2.0%** |

This is the structurally interesting result and it was predicted (`docs/28`
§7.3). `s/v` and `c/v` are ratios *to* variable capital, so a 43% larger `v`
moves both by 30%. The value rate of profit has constant capital in the
denominator as well, and `c` is fourteen times `v` even after the
enlargement — so the same change moves it by 2%.

**Enlarging the basket repairs two of the three ratios and does almost
nothing to the third.** Anyone reading `s/v` or `c/v` from this project
should know they were badly inflated and are now merely inflated; anyone
reading the value rate of profit should know the basket was never its
problem.

The meals-only model is now reachable as a parameter override rather than
as a memory, and a test anchors it to the figures `docs/24` and `docs/27`
published — 38.29814, 20.66573, 1.76768, and a profit rate of 38.344262.
Every comparison above is against that control in the same run, not against
a number copied out of an old document.

## 3. Chemfuel became basic, and `r` stopped being `s/v`

The tailoring bench is powered. That one material input into one wage good
is enough to change the *shape* of the price system.

| | meals only | enlarged |
|---|---|---|
| basic commodities | `meals` | `chemfuel`, `garments`, `herbal_medicine`, `meals` |
| uniform profit rate `r` | 38.344 | **24.624** |
| rank-one rate `T/Σ(b·l) − 1` | 38.344 | 26.826 |
| `r` ÷ rank-one | **1.0000** | **0.9179** |

Until now `r` was exactly the rate of surplus value, and `docs/27` explained
why with a corn model. The real reason is more general and worth stating
properly, because it is what just broke:

> With no material inputs to any wage good, the augmented input matrix
> restricted to the basket is the outer product `(l/T)·bᵀ`. A rank-one
> matrix has one non-zero eigenvalue, `Σ b·l / T`. So `r = T/Σ(b·l) − 1 =
> s/v` for **any** number of pure-labor wage goods, not just one.

Add a single material input and the rank collapses no longer. `r` falls
**8.2% below** the rank-one figure and **7.8% below** the rate of surplus
value — where in `docs/27` the only gap was the 0.12% of omitted fixed
capital, in the opposite direction.

The mechanism is the general Sraffa case in one line: **the price system
marks material inputs up by `1 + r` and the value system does not.**
Chemfuel enters a garment's value at 25.04 ticks flat, and enters its price
at 25.6 times its own price.

A control scenario removes the chemfuel link and nothing else. Chemfuel
drops out of the basics, the rank-one identity returns **exactly**, and `r`
sits above `s/v` again by the fixed-capital term. The break is that one
input and not an artifact of the enlargement.

## 4. Prices of production: better by half, still unusable

Relative to meals:

| commodity | labor value | price of production | authored | p/v |
|---|---:|---:|---:|---:|
| meals | 1 | 1 | 1 | 1.000 |
| chemfuel | 0.08202 | 0.08197 | 0.15333 | 0.999 |
| herbal medicine | 1.31000 | 1.31148 | 0.66667 | 1.001 |
| garments | 5.38252 | **7.25577** | 5.71733 | **1.348** |
| psychoid leaves | 0.15554 | 0.25649 | 0.12667 | 1.649 |
| yayo | 2.41020 | **54.14603** | 1.40000 | **22.465** |

Yayo against its authored ratio falls from 71.6× to **38.7×**. Leaves fall
from 2.01× their value ratio to 1.65×. Every deviation shrinks, in exact
proportion to the fall in `r`, and none of it is enough: a unit of yayo
still prices at fifty-four meals where RimWorld says one and a half.

Two of the new rows are instructive. **Herbal medicine prices within 0.1% of
its value ratio**, because it is a pure-labor good like meals and the markup
cancels — the same identity chemfuel satisfies. **Garments deviate by 34.8%**
in the opposite direction, and they are the only wage good with a material
input. The two new commodities happen to sit on either side of the
distinction this session added.

Marx's aggregate reconciliation improves marginally: with total price
normalized to total value, total profit is **1.516×** total surplus, against
1.526 before. Enlarging the basket does not close the transformation gap
either.

## 5. The result: it is not the basket, it is the productivity

`docs/27` concluded that "the enlarged subsistence basket is now a
prerequisite" for adopting prices of production, and reordered the backlog
on that basis. **That was wrong, and `docs/28` §7.6 committed to expecting
it to be wrong before this session ran.**

The arithmetic is not subtle. `r ≈ T / (basket labor) − 1`, so a profit rate
near 1 needs a basket embodying half a working day: 12,000 ticks. The honest
basket embodies 866. To close that gap in meals alone a worker would have to
eat **39 meals a day**.

The constraint is RimWorld's own productivity:

```
one provisioner's working day  =  24,000 ticks  =  78.6 simple meals
                                              =  39.3 workers fed
```

A simple meal embodies 305 ticks *including its farming* — that is the
closed analysis's figure, solved from extraction outward. One cook feeds
thirty-nine people. Historically that is a late-industrial food system, and
it is what the game's authored work amounts say.

**So the rate of surplus value this project reports is not a calibration
artifact to be tuned away. It is RimWorld's, and the model's job is to
report it.** The colony that accumulates wealth implausibly fast is doing so
because its labor is implausibly productive, which is a statement about the
game rather than about the laboratory.

`generous_basket` bounds this from above. Three meals, half a garment and
half a dose per worker-day — a bundle nobody could call stingy, 8.07% of the
working day — and the figures are:

| quantity | default | generous |
|---|---:|---:|
| basket, share of the working day | 3.61% | 8.07% |
| rate of surplus value | 26.71 | **11.38** |
| organic composition | 14.42 | 6.15 |
| value rate of profit | 1.733 | 1.592 |
| uniform profit rate | 24.62 | 10.65 |

Still an order of magnitude above anything the literature works with, and
the scenario is still exactly stationary, so it is a measurement rather than
a shortage.

## 6. What the multi-good basket dissolved

`docs/24` reported that for the wage good the money and labor rates of
surplus value agreed — 38.33 against 38.30 — and **refused to treat the
agreement as evidence**, because with a meals-only basket both figures were
the same expression in the same wage and the same basket. It would have
agreed whatever the truth was.

With three goods in the basket that derivation no longer closes:

| sector | money s/v | labor s/v |
|---|---:|---:|
| chemfuel | 51.59 | 26.71 |
| **garments** | **28.51** | 26.71 |
| **meals** | **27.11** | 26.71 |
| psychoid leaves | 21.08 | 26.71 |
| **herbal medicine** | **13.29** | 26.71 |
| yayo | 7.71 | 26.71 |

The three wage goods now straddle the labor-time rate rather than one of
them sitting on it by construction. Meals land within 1.5% and that is a
small real difference rather than a tautology; garments realize more than
they produce and medicine less than half. The caveat `docs/24` attached to
its own headline can be retired, and the sectoral spread it reported —
surplus produced against surplus realized — survives the change intact.

## 7. Two defects the session surfaced

**The basket capacity guard only knew about meals.** It has checked "meal
demand exceeds provisioning capacity" since `docs/17` and would have let an
under-provisioned garment or medicine sector through as a permanent ledger
shortfall. It now checks every basket good and names the one that is short.

**The seeding guard applied the wage twice.** `_assert_reference_full_
utilization` added `wage_cost` on top of `effective_unit_cost`, which has
carried the wage since `docs/17`. Over-strict rather than unsafe — it would
refuse configurations the model handles fine — but wrong, and the
generous-basket scenario fell straight into the gap. The guard now reads
exactly the cost `Producer.utilization` compares against, so its threshold
is the model's own.

Both were found by adding a second and third good to a mechanism that had
only ever seen one. That is the argument for stress scenarios that are
deliberately implausible.

## 8. Prediction scorecard

Every prediction in `docs/28` §7 held.

| prediction | predicted | measured |
|---|---|---|
| 7.1 rate of surplus value | 26.71 | **26.708** |
| 7.2 organic composition | ≈14.6 | 14.415 |
| 7.3 value rate of profit | ≈1.72 | 1.733 |
| 7.4 uniform profit rate | 24.6238 | **24.62388** |
| 7.4 rank-one rate | 26.8261 | 26.82609 |
| 7.4 `r` below rank-one | 8.2% | 8.21% |
| 7.4 `r` below s/v | 7.8% | 7.80% |
| 7.5 garments / meals | 7.25575 | 7.25577 |
| 7.5 medicine / meals | 1.31148 | 1.31148 |
| 7.5 yayo / meals | 54.1462 | 54.14603 |
| 7.5 yayo against authored | 38.7× | 38.68× |
| 7.6 workers fed per provisioner | 39 | 39.30 |
| 7.7 generous basket s/v | 11.38 | 11.385 |
| 7.8 behavioral metrics move | yes | 66 of 114 |

**This scorecard is worth less than the last four**, and the reason should
be recorded. The price and profit-rate figures were derived by hand from the
same coefficients the code reads, so agreeing with them tests the
*implementation* — which is a real check, and it caught nothing this time —
not the economics. The two predictions that carried information were §7.3,
that the value rate of profit would barely move, and §7.6, that the
conclusion would be negative. Both were genuine forecasts about structure
rather than arithmetic, and both held.

The closest thing to a miss is 7.3: predicted "about 1.72", measured 1.733,
so the movement was 2.0% where the prediction implied about 3%. The
direction and the reasoning were right and the magnitude was slightly over-
estimated.

## 9. Behavioral movement, explained

66 of 114 metrics moved, and this is the first session in three where any
did. The reference is rewritten with the movement explained rather than
suppressed. The four groups:

- **The wage and everything it touches** (+39.9%). Every producer's
  effective unit cost carries a larger wage, so `cost_competition` and
  `technique_change` wage and price metrics move with it.
- **All the value ratios** (−30%), per section 2.
- **Employment, +1.1%.** Two new sectors perform labor. This also lifts
  `glut.local.employment_trough` from 0.000202 to 0.000412: the tailors and
  herbalists keep working through a yayo glut that idles the drug lab.
- **The chemfuel buffers, +4% to +11%.** The refinery now carries capacity
  headroom for the tailors' draw, and inventory targets are set from
  capacity. `producer_loss.local.chemfuel.*` shifts accordingly; the shock
  itself is unchanged in kind.

One movement is worth naming on its own. In `technique_change`, the gain a
labor-saving provisioning technique delivers to the profit rate falls from
**1.149× to 1.086×**. Relative surplus value is diluted by the enlarged
basket exactly as it should be: cheapening one good in a three-good bundle
moves the value of labor-power less than cheapening the only good in a
one-good bundle. The mechanism is intact and its magnitude now depends on
the basket, which is correct.

The `subsistence_shock` scenario is *deeper* than before, not shallower: the
meal price peaks at **74.43** on day 119 and the wage at **161.68**. The
terminal figures are lower only because the larger meal buffer lets the run
recover further by day 240. The shock also now propagates into the *other*
wage goods — garments peak at 91.57 against a reference of 85.76 — which is
a channel that could not exist while the basket held one commodity.

## 10. Where this leaves the next step

The basket is done and it did not unlock the price system. The leading
candidate for what would is the one `docs/27` §5 named second and nobody has
touched: **turnover**.

`r` is a rate per production period, and the model's production period is
one day. But the model's own inventory targets are **twenty days** of
throughput, so the capital actually tied up is roughly twenty times the
daily flow the price system charges profit against. A first-order
correction — scaling the advance by the turnover time — puts `1 + r` at
about `25.62 / 20 ≈ 1.28`, so a profit rate near **0.28 per turnover
period** rather than 24.6 per day.

**That is back-of-envelope arithmetic in a results document, not a
measurement**, and it is exactly the kind of estimate `docs/22` got wrong by
tracking the right mechanism at the wrong moment. It needs its own design
document and its own scorecard. But it is the first candidate that changes
`r` by the right order of magnitude for the right reason, and unlike the
basket it does not require inventing consumption nobody would defend.

Revised ordering:

1. **Turnover**, and with it the distinction between capital advanced (a
   stock the model already holds) and capital consumed (a flow it already
   accounts for). Cheapest remaining change with the largest expected
   effect.
2. **A capital-goods sector**, unchanged: building capacity still spends
   silver without consuming material, and it is what would let fixed capital
   into the price system.
3. **Capacity depreciation and exit**, unchanged.

And the standing recommendation from `HANDOFF.md` still holds: the scale
test should jump the queue once the economics reaches a natural stopping
point. After turnover would be a defensible place to stop.

## Reference decision

Two commits. The first adds the two commodities, generalizes the seeding
solver to a material balance, fixes both guards and rewrites the thirteen
tests that had encoded a one-good basket; 111 tests to 124. The second
refreshes the reference — 66 metrics moved, 20 added, 114 to 134.
