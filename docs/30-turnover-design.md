# Turnover: design

Written before implementation. `docs/29` §10 named this as the next step and
showed an envelope for it. Section 7.1 below corrects that envelope — it was
wrong by a factor of four, and the reason is worth recording.

## 1. Why

The project reports two numbers as rates of profit and neither is one.

**The price system's `r` is per production period, and the period is a day.**
`docs/27` said so and `docs/29` repeated it. A uniform profit rate of 24.62
per day is not a magnitude anybody can argue about; it is a unit error
waiting to be fixed.

**The value ledger's `s/(c+v)` is computed on flows.** `c` and `v` are
capital *consumed* over the run. So the ratio is profit per unit of capital
consumed, which is a real quantity but is not the rate of profit — the rate
of profit is profit per unit of capital *advanced*, and capital advanced is a
stock. The project has been printing 1.77, then 1.73, under the heading
"value rate of profit" since `docs/23`.

Both errors have the same shape: **the model charges profit against a day's
flow while holding twenty days of stock.** It already has both halves — the
flow in the ledger, the stock in `Region.inventory` — and has never put them
together.

## 2. The correct formulation

### 2.1 Prices

Per unit of commodity *i*, let `M_i · p` be the cost the existing system
already computes: material inputs at their prices, plus the wage bundle. Let
`τ_i` be the turnover time in periods. Then the capital advanced per unit is
`τ_i (M_i · p)` and the price of production is

```
p_i  =  M_i·p  +  r · τ_i · (M_i·p)  =  (1 + r τ_i)(M_i·p)
```

Cost, plus profit at rate `r` on what was advanced to meet it. When every
`τ = 1` this is exactly `p = (1 + r)Mp` and nothing changes, which is the
right compatibility property.

The system is no longer a plain eigenproblem, because `r` enters through a
diagonal. It is solved as one: `λ(r) = ` the Perron root of
`diag(1 + rτ) M` is non-decreasing in `r` because every entry is, so
bisection on `λ(r) = 1` has a unique root, and each evaluation is the power
iteration already written.

### 2.2 Turnover time comes from the model, not from a new knob

`τ_i = production_period_days + target_inventory_days_i`. One period to make
it and the commodity's own inventory target to sell it.

Deliberately **not** an independent parameter. Inventing one would let
turnover be tuned separately from the stock the model actually holds, which
is the entire thing being corrected. `production_period_days` is exposed and
defaults to 1.0, which is what `step()` does.

### 2.3 No double counting

One unit of chemfuel is made on day 0, sits until day 20, is drawn by the
tailors, becomes part of a garment that sits until day 40. The refinery's
capital is tied up days 0–20; the tailors' capital is tied up days 20–40, and
what they advanced *includes the chemfuel price*, which already contains the
refinery's profit. So attributing each commodity's stock once, to its own
producer, and letting the buyer's advance be its own cost over its own
holding time, counts every day of every unit exactly once.

That is why the formula is `τ_i × (M_i·p)` and not a sum over separately
tracked input and output stocks.

### 2.4 The ledger measures the stock rather than assuming it

For the value side there is no need to assume `τ × flow`: the model holds the
inventory, so the advance is measured directly.

```
capital advanced  =  Σ_c (stock of c) × v(c)          commodity capital
                  +  goods in transit at their values
                  +  one period of the wage bill       variable capital
                  +  fixed capital stock               (see §3.3)
```

and the rate of profit on advances is `s per period / capital advanced`.

The price system's `τ_i` and the ledger's measured stock will not agree
exactly — inventory targets are set from *throughput* demand at full
capacity while the flow is realized output — and that disagreement is
reported rather than reconciled by fiat. The two are different objects: one
is what a uniform-profit-rate price system would require, the other is what
this economy actually ties up at RimWorld's authored prices.

## 3. Design decisions

### 3.1 The old number is kept under an honest name

`docs/26` through `docs/29` report a profit rate of 38.34, then 24.62. That
quantity does not disappear; it is the **gross markup** `k − 1`, the factor
by which a sector's price exceeds its cost. With uniform turnover
`k − 1 = r τ`, so it is exactly `r` per turnover rather than per period.

`prices_of_production` returns both. Every existing test and metric that
reads the old number is re-pointed at `gross_markup`, so the continuity of
the frozen reference is preserved and the *new* quantity is a new
observation rather than a silent redefinition.

### 3.2 Uniform turnover moves no price, and that is a result

If every `τ_i` is the same, `1 + rτ` is one constant and `p = k M p` is the
old system exactly. **Relative prices are bit-identical and only the reported
rate changes, by exactly a factor of `τ`.**

This must be asserted, not assumed, because it is the cleanest available
check that the turnover term is wired in correctly *and* it is a real
statement about the theory: turnover rescales the profit rate, and only
*differential* turnover redistributes prices between sectors.

### 3.3 Fixed capital is in the ledger's advance and not in the price system

Consistent with `docs/26` §3.5 and for the same reason: the machines are
exogenous, so a price system has nowhere to put one without mixing in an
authored magnitude. The omission now matters more than it did — a building
depreciating over 600 days is a stock 600 times its daily flow, where as a
*flow* it was 0.05% of cost — so the results document must report the size of
what is left out rather than mention it.

The value ledger has no such problem: the machines' embodied labor is known,
so the fixed capital stock enters the measured advance directly.

### 3.4 A scenario with differential turnover, grounded in the game

`perishable_meals`. RimWorld's simple meals rot in four days, so the market
cannot hold twenty days of them. Setting the meal inventory target to 4 is a
real fact about the game rather than a knob turned to make a point, and it is
the only differential turnover the current commodity set justifies.

It changes two things at once — the price system's `τ_meals`, and the model's
actual meal buffer — so the results document must report both and not
attribute one to the other.

## 4. Interface

```python
economy.prices_of_production(...)   # gains "gross_markup" and "turnover_days"
economy.capital_advanced(region=None)      # itemized dict
economy.value_rate_of_profit_on_advances(region=None)
economy.realized_turnover_days(region=None)   # advance ÷ (c + v) per period
```

`Economy(production_period_days=1.0)` and
`ScenarioParameters.production_period_days`, plus
`meal_target_inventory_days` (default 20.0, unchanged) and
`perishable_meal_days` (4.0) for the scenario.

`value_rate_of_profit` is **left alone**. It is referenced by `docs/23`,
`docs/24`, `docs/27` and `docs/29` and remains a correct measure of profit
per unit of capital consumed. Its docstring gains a pointer to the new
quantity and a sentence saying which is the rate of profit.

## 5. Non-goals

- Adopting prices of production. Still an observation.
- A capital-goods sector; recreation in the basket; capacity depreciation.
- Compound turnover. `(1 + r)^n` treats profit as reinvested within the
  turnover; the classical formulation charges `r` once on the advance, and
  §7.1 is where the difference bites.
- Per-producer inventory. The model has one regional stock per commodity and
  this design attributes it, deliberately, to the producing sector.
- Making the price system's `τ` and the ledger's measured stock agree.

## 6. Tests

1. Uniform turnover leaves every relative price **bit-identical** to the
   `docs/29` figures, and `gross_markup` unchanged.
2. `profit_rate × turnover = gross_markup` exactly, under uniform turnover.
3. `production_period_days=1` with `target_inventory_days=0` reproduces the
   pre-turnover profit rate exactly — the compatibility property of §2.1.
4. The capital advanced itemizes to its parts and every part is positive.
5. `realized_turnover_days` is far above the 21 the price system assumes, and
   the gap is the finished-goods stock of the final product.
6. The rate of profit on advances is far below the flow ratio, and both are
   reported.
7. `perishable_meals` raises `r` and moves relative prices — asserted with a
   direction, since a faster-turning wage good releases capital.
8. Equilibrium still exactly stationary in both scenarios.

## 7. Predictions

**7.1 `docs/29`'s envelope was wrong by a factor of four, and this document
says so before measuring.** That note reasoned `1 + r ≈ 25.62 / 20`, giving
`r ≈ 0.28`. That is a *compound* correction — it asks what rate, compounded
over twenty periods, reproduces the markup. The classical formulation charges
profit once on the advance, so the correction is additive:

```
1 + r τ = k    →    r = (k − 1)/τ = 24.6238 / 21 = 1.17257 per day
```

The envelope was labelled an envelope, which is what made it cheap to be
wrong. But the error is not arithmetic slippage — it is the difference
between two economic claims, and the additive one is right.

**7.2 Not one relative price moves.** Uniform turnover, so `k` is unchanged
at 25.6238 and the price vector is bit-identical to `docs/29` §4.

**7.3 Capital advanced is 481,742 ticks**, itemized as:

| component | ticks | share |
|---|---:|---:|
| commodity capital in stock | 464,397 | 96.4% |
| fixed capital stock | 16,795 | 3.5% |
| wage advance (one period) | 550 | 0.1% |

and **96% of the commodity capital is the yayo circuit** — 63% finished yayo
awaiting sale and 33% psychoid leaves. The wage advance, which is what the
old formulation effectively charged profit against for a pure-labor good, is
a *thousandth* of the capital actually tied up.

**7.4 The value rate of profit on advances is 0.0305 per day**, against a
flow ratio of 1.7326. A factor of 57 — which is the realized turnover time in
days, and the number the model should have been dividing by all along.

**7.5 Realized turnover is 56.8 days, not 21.** The price system assumes 21
because that is production plus the inventory target. The measured figure is
nearly three times larger because the flow denominator `c + v` never sees the
finished-goods stock of the **final** product: yayo is nobody's input, so its
200 units of inventory per region are capital advanced that no cost flow
accounts for.

**7.6 A coincidence to disarm in advance.** `0.030497 × 60 = 1.83` per
RimWorld year, against a flow ratio of 1.7326. **These agreeing to 6% means
nothing.** It happens because the realized turnover (56.8 days) is close to
the length of a RimWorld year (60 days), so dividing by one and multiplying
by the other nearly cancels. If either changed the agreement would vanish.
Recorded here so that the results document cannot be read as confirmation.

**7.7 `perishable_meals` raises `r` to about 2.08 per day and makes
everything dearer relative to meals.** Solving the basic system with
`τ_meals = 5` and everything else 21:

| commodity | uniform τ | perishable meals |
|---|---:|---:|
| meals | 1 | 1 |
| chemfuel | 0.08197 | **0.3213** |
| herbal medicine | 1.31148 | **5.140** |
| garments | 7.2558 | **34.10** |
| psychoid leaves | 0.25649 | **1.311** |
| yayo | 54.146 | **475.9** |

The mechanism: a wage good that turns over fast releases capital, which lifts
the uniform rate; everything that still turns over in 21 days then carries
21 periods of a much higher rate, while meals carry only 5.

So **differential turnover widens the deviations rather than narrowing
them**, in this configuration. That is a finding about the configuration, not
a defect: RimWorld's cheap, fast-rotting wage good against slow-moving
manufactured drugs is a real structural asymmetry.

**7.8 Behavioral movement: none in the default, substantial in
`perishable_meals`.** The default changes an observation only. The scenario
cuts the meal buffer from twenty days to four, which will move meal price
dynamics and every shock that runs through them.

## 8. What would make this wrong

If any relative price in the default scenario moves, the turnover term is not
entering as a uniform diagonal and §2.1 is mis-implemented.

If `profit_rate × 21` does not equal `gross_markup` to floating point, the
bisection is not converging to the root it claims.

If the measured capital advanced comes out near `21 × (c + v)`, the ledger is
summing the same stock the flow already accounts for, and §2.3's
no-double-counting argument has not survived contact with the code.
