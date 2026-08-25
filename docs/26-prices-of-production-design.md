# Prices of production: design

The next economic feature after `docs/23`. Written before implementation, as
usual, so that the predictions in section 7 can be scored against what the
code actually produces.

## 1. Why

`docs/24` ended on a negative result and a conclusion drawn from it.

The negative result: the operating overhead — over 95% of money cost for the
upstream sectors — is not fixed capital, not wages, and not inputs. It is the
**authored-price wedge**: the gap between RimWorld's `MarketValue` and
everything the model can account for. Two-thirds of the upstream price sits
in it. Fixed capital, implemented from the real building data, explained
0.05%.

The conclusion: *the wedge cannot be closed while `MarketValue` is the price
anchor.* Every economically meaningful component has been carved out of it
and two-thirds remains. Closing it means computing prices from the technical
data instead of anchoring them to an authored constant.

That is the classical exercise. Given input-output coefficients, direct
labor, and a real wage, derive a price vector and a uniform rate of profit
such that every sector earns the same rate on its advances. Sraffa's *Production
of Commodities by Means of Commodities* poses it as an eigenvalue problem;
Marx poses it as the transformation of values into prices of production. They
are the same arithmetic and the model already holds every input it needs:
input coefficients, direct labor per unit, a subsistence basket, a working
day, and an iterative solver with a convergence discipline.

## 2. What is being computed

For each commodity *i*, let

- `a[i][j]` — units of *j* consumed per unit of *i* produced;
- `l[i]` — work-ticks of living labor per unit of *i*;
- `b[j]` — units of *j* in one worker-day's subsistence basket;
- `T` — work-ticks in a worker-day.

A unit of *i* requires `l[i] / T` worker-days, and therefore a physical wage
bundle of `(l[i] / T) · b`. Fold that into the input matrix:

```
M[i][j]  =  a[i][j]  +  (l[i] / T) · b[j]
```

`M` is the whole bundle of commodities advanced to produce one unit of *i* —
means of production *and* means of subsistence. The price of production
system is then

```
p  =  (1 + r) · M · p
```

Every sector marks its advances up by the same `r`. This is a homogeneous
eigen-system: `1/(1+r)` is the dominant eigenvalue of `M` and `p` is its
right eigenvector, determined up to a scale factor.

**The profit rate is therefore not a free parameter.** It follows from the
technique and the real wage alone, with no reference to any authored price.
That is precisely the property `docs/24` said was missing.

## 3. Design decisions

### 3.1 The wage closure is physical, not monetary

The wage enters as a *bundle*, not as a money magnitude. Feeding in a money
wage would smuggle the authored price level straight back into a system whose
entire purpose is to be free of it. The basket is already physical in the
model (`Region.subsistence_basket`), so this costs nothing.

Consequence: the money wage is an *output* of the computation
(`w = p · b / T` at production prices), not an input.

### 3.2 Solved by iteration, never inverted

Power iteration with a fixed positive normalization, matching
`_update_labor_values`. Same reasoning as `docs/19`: iteration converges
exactly when the system can reproduce itself with the basket paid, which is
the economically meaningful condition, and non-convergence is an explicit
error rather than a returned number. No linear algebra dependency, and
nothing is added to the dependency-free rule.

The failure message must say what failure *means*: the economy cannot both
pay the basket and replace its means of production.

### 3.3 The technique is social, weighted by realized output

Exactly the weighting `_update_labor_values` and `_sector_unit_cost` already
use: total input over total output, total labor over total output, across all
active producers in every region. One social technique per commodity, one
social price system.

Regional differences then show up as deviations from it, which is the same
relationship individual labor values already have to social ones. Building a
separate price system per region would be a different (and less classical)
exercise.

Joint outputs apportion inputs and labor by `share_of_cost`, the same mass
rule the value solve uses, so the two systems see the identical technique.

### 3.4 The basket is labor-weighted across regions

`b[j] / T` is what enters `M`, and both `b` and `T` are per-region. Where
regions differ, the social wage bundle per tick is the average of `b / T`
weighted by each region's labor performed — the same run-weighting used
everywhere else, reducing exactly to the common value when regions agree (as
they do in every current scenario).

### 3.5 Fixed capital is omitted, and the omission is measured

The model's fixed capital is exogenous: a drug lab costs 445 silver and
embodies 41,607 ticks, both imported from the closed analysis, because
buildings are not produced inside the modelled circuit. A price of production
system has nowhere to put such a thing. Including its *money* price would
mix an authored magnitude into a derived price vector, which is the exact
error the exercise exists to avoid; including its *labor* content would mix
numéraires.

So fixed capital is left out, and because `docs/24` measured it — 0.353% of
constant capital, 0.05% of cost — the size of the omission is known rather
than hidden. The proper fix is a capital-goods sector (Department I), already
on the backlog behind this step. The results document must report the gap
this opens between `r` and the ledger's rate of surplus value rather than
quietly absorbing it.

### 3.6 Two normalizations, both reported

The eigenvector fixes only relative prices. Two scalings answer two different
questions and both are cheap, since they are scalings of one solve:

- **`labor_value`** — scale so the gross output's total price equals its
  total labor value. This is Marx's first invariance postulate, and it makes
  per-commodity prices directly comparable against per-commodity values.
- **`reference_price`** — scale so the gross output's total price equals its
  total at RimWorld's authored prices. This makes the deviation from
  `MarketValue` legible commodity by commodity.

A third form, `numeraire=<commodity>`, sets one commodity's production price
to its authored reference price; it is the readable one for a small table.

Committing in advance: **whichever normalization is chosen, both of Marx's
aggregate equalities will not hold at once.** Total price can be made to equal
total value, or total profit made to equal total surplus, but not both except
by coincidence. The results document reports the failure, it does not pick
the normalization that hides it.

### 3.7 Basics and non-basics are classified and reported

A commodity is *basic* if it enters, directly or indirectly, into the
production of every commodity. Sraffa's central structural result is that `r`
depends **only on the basic subsystem**: a change in a non-basic sector's
technique changes that sector's price and nothing else.

This is worth surfacing explicitly because it is a sharp, testable
difference from the labor-value system, and because it explains the number
`r` turns out to be. Computed by reachability over `M`, which is four nodes.

### 3.8 Observation only — nothing feeds back

`prices_of_production` is a query, not a step in `step()`. It does not touch
`_update_prices`, the cost anchor, or the order book. No behavioral metric may
move; the equilibrium scenario must still report a price range of exactly
zero.

This is deliberate and is the first half of a two-part decision. Adopting
production prices as the model's actual anchor would move every price in the
model, and the honest order of operations is to *measure the thing first* and
then decide whether adopting it is an improvement. Section 7 predicts it will
not be, for a reason that is itself the useful finding.

### 3.9 Undefined rather than zero

Following `organic_composition` and `rate_of_surplus_value`: with no
subsistence basket anywhere there is no wage relation, the wage cost is zero,
and every pure-labor good would price at zero. Return `None` and say so,
rather than returning a degenerate vector. Likewise a commodity nothing
produced has no technique and cannot be priced; if a priced commodity needs
it as an input, that is a loud error, not a guess.

## 4. Interface

```python
economy.prices_of_production(numeraire="labor_value", use_capacity=False)
```

returning `None` when undefined, else

```python
{
  "profit_rate": float,          # r, per production period
  "prices": {name: float},       # normalized per `numeraire`
  "wage": float,                 # p · b / T, silver-equivalent per tick
  "basics": [name, ...],         # the basic subsystem
  "iterations": int,
}
```

New coefficients, both exposed through `ScenarioParameters` per the standing
rule: `production_price_tolerance` (1e-12) and
`production_price_max_iterations` (1000), matching the labor-value solver's
defaults so the two convergence disciplines are identical.

## 5. Non-goals

- Adopting production prices as the model's price anchor.
- A capital-goods sector. Named as the fix for §3.5, not attempted here.
- Turnover periods. `r` comes out as a rate *per production period*; the
  model's period is a day. Section 7 predicts this matters and the results
  document must not present `r` as though it were an annual rate.
- Choosing between the transformation problem's competing solutions
  (Bortkiewicz, the New Interpretation, TSSI). The model computes one
  standard simultaneous system and reports where the invariances fail.
- Absolute rent, monopoly rent, differential profit rates.

## 6. Tests

1. `r` is exactly `T / (basket at capital-free values) − 1` in the
   equilibrium scenario, to floating-point tolerance.
2. Meals is the only basic commodity; the classification is asserted.
3. Changing a **non-basic** sector's technique (yayo's direct labor) leaves
   `r` bit-identical and changes only that sector's price.
4. Changing the **basic** sector's technique (meals) moves `r`.
5. Chemfuel's production price relative to meals equals its labor value
   relative to meals, exactly — both are pure-labor goods.
6. `numeraire="labor_value"` makes total price equal total value exactly.
7. Total profit does **not** equal total surplus under that normalization —
   asserted as a positive statement about the gap, not tolerated as slack.
8. A bare model with no basket returns `None`.
9. Non-convergence raises with a message naming the condition.
10. No behavioral metric moves; equilibrium price range still exactly zero.

## 7. Predictions

Derived by hand from the coefficients before writing any code, so the
implementation is checked against an independent derivation rather than
against itself. Coefficients: chemfuel `l=25`, no inputs; leaves `l=46.2`,
`0.05` chemfuel; yayo `l=350`, `8` leaves and `0.2` chemfuel; meals `l=305`,
no inputs. Basket 2 meals, `T = 24000`.

**7.1 The only basic commodity is meals.** Meals enter every sector through
the wage. Chemfuel enters leaves and yayo but *not* meals, whose process has
no modelled inputs — so chemfuel, leaves and yayo are all non-basic.

**7.2 `r = 38.3443`**, because a single basic good with no means of
production reduces the system to a corn model:

```
r  =  T / (b_meals · l_meals) − 1  =  24000 / (2 × 305) − 1  =  38.344262
```

**7.3 `r` equals the rate of surplus value exactly**, for the same reason.
When the wage good is produced by labor alone, the profit rate and the rate
of surplus value are the same number. The ledger's cumulative s/v is
**38.298**, lower by the fixed-capital term that §3.5 omits; the predicted
gap is therefore about **0.12%**, and the identity against the capital-free
basket value should hold to floating-point tolerance.

**7.4 Relative prices, meals = 1:**

| commodity | labor value | price of production | authored |
|---|---:|---:|---:|
| meals | 1 | 1 | 1 |
| chemfuel | 0.08197 | **0.08197** | 0.15333 |
| psychoid leaves | 0.15557 | **0.31271** | 0.12667 |
| yayo | 2.40852 | **100.2296** | 1.40000 |

**7.5 Chemfuel's production price equals its value ratio exactly.** Both it
and meals are pure-labor goods, so the markup is proportional to labor in
both systems and the ratio `25/305` survives untouched.

**7.6 Yayo's production price is absurd — about 72× the authored ratio.** The
markup compounds: `(1+r)` applies to leaves, and again to the leaves embodied
in yayo, so an eight-to-one input ratio meets a 39-fold gross markup twice.

**7.7 The headline conclusion will be negative, and useful.** Prices of
production computed from *this* technique set will not rescue the price
system; they will produce prices far less defensible than the authored ones.
The cause is not the price theory but two things the model has not yet fixed:

- the **meals-only basket**, flagged since `docs/17`, which makes necessary
  labor 2.5% of the working day and therefore `r` roughly 38 rather than
  roughly 1;
- the **absent turnover period**, since the model's production period is one
  day, so `r` is a *daily* rate and cannot be compared to any empirical
  profit rate at all.

If this holds, the backlog reorders itself with evidence: the enlarged basket
stops being a caveat on the headline numbers and becomes a **prerequisite**
for adopting production prices at all.

**7.8 Aggregate invariance fails by roughly 50%.** Normalized so total price
equals total value (≈ 22,973 ticks of gross output per day), total profit
should come out near **22,389** against a total surplus near **14,698** — a
ratio of about **1.52**. Total price = total value and total profit = total
surplus cannot both hold, and the gap here is large rather than marginal.

**7.9 No behavioral metric moves.** The computation is a query.

## 8. What would make this wrong

If `r` comes out near 1.77 — the ledger's value rate of profit — then the
basics/non-basics reasoning in 7.1 is wrong and the whole economy's constant
capital is entering `r`, which would mean the implementation is not solving
the system section 2 describes.

If yayo's production price comes out near its authored price, the markup is
not compounding through the input chain and the eigenvector is wrong.

Either would be an implementation error rather than a finding, and the
results document must say which it is before drawing any economics from the
numbers.
