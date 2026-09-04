# Firm-posted prices: the anchor becomes an initial condition: design

Written before implementation. The second of the three impositions
(`docs/55` §1 names all three): the regional price is anchored to
RimWorld's authored `MarketValue`, so that two thirds of every upstream
price is a wedge the model cannot attribute (`docs/24`) and every price
returns, after any shock, to a level nothing inside the model chose.
`HANDOFF.md` has called this "the seam `FINDINGS.md` found" and said
closing it "means deriving prices rather than importing them." This is
the first step of that derivation, and it is a smaller step than the
sentence suggests.

## 1. What the anchor does today

```
anchor  = reference_price × (1 + κ (cost_ratio − 1))          docs/21
desired = clamp(anchor × exp(pressure))
price  += speed × (desired − price)
```

`pressure` is the inventory coverage gap plus unmet demand. The price is
*proportional* control around the anchor: a glut lowers it and it
returns; a cost rise moves the anchor by a fraction `κ = 0.5` of the rise.
Two things in it are imposed from outside the agents. The **level** is
the authored price, forever: however costs or demand move, the price is
pulled back toward `reference_price` scaled by cost. And the **speed**
of cost pass-through is a coefficient chosen by the modeller rather than
an outcome of anyone's pricing.

What is *not* imposed, and is kept: the pressure signals themselves are
what a firm can see — its sector's stock against target, and orders it
could not fill — and `docs/21`'s order book already sends custom to the
cheaper producer. The model has been half a posted-price market since
`docs/22`. This finishes the half.

## 2. The rule

Off by default (`posted_prices = False`), bit-identical off. On:

**Each producer posts a price.** `Producer.posted_price`, seeded at the
commodity's reference price, so the authored price is the *initial
condition* and nothing more. Each day, after production and sales:

```
posted  ×=  (cost_today / cost_yesterday)  ×  exp(speed × pressure)
```

`cost` is the producer's own effective unit cost at the day's prices —
so cost passes through **fully and at once** (`κ` is one by construction
and stops being a parameter of the rule) — and `pressure` is the sector's
coverage gap and unmet demand, exactly the expression the anchor rule
uses, because a producer in a pooled market sees the pool. `speed` is
`price_adjustment_speed`, in its new role as an integral gain: the
pressure moves the price *level* and nothing moves it back except
opposite pressure. A glut lowers the price and the price stays lower
until stock falls short. That is what "no anchor" means, and it is the
whole change.

Written multiplicatively for the same reason `docs/21` wrote the anchor
as `1 + κ(ratio − 1)`: when cost is the identical float and pressure is
exactly zero, the factor is `1.0 × exp(0.0)`, which is exactly one, and
the posted price is the same float every day. The seeded equilibrium
keeps its exactly-zero price range.

**The regional price is what was paid.** `Region.prices[c]` becomes the
output-weighted mean of the posted prices of the producers that supplied
the pool that day, weighted by their realized output, and held where
nobody produced. With one producer per sector, which is every seeded
sector, it is that producer's posted price.

**The order book goes to the cheaper *price*.** `_allocate_orders`
weights by `(posted / cheapest posted)^-ε` instead of by cost. A producer
posting above its rivals loses custom continuously, which is the only
force in the rule that pulls a sector's posted prices together, and it is
the force competition actually is.

**Sellers are paid what they posted.** With producer cash on, a sale from
the pool credits each seller at its own posted price times its share of
the units; the buyer pays the weighted mean. Without producer cash the
regional price is all there is, as today.

**Bounds move to cost.** The clamps at `minimum_price_factor` and
`maximum_price_factor` times the reference price become the same factors
times the producer's own cost. A price cannot fall below 18% of cost or
rise above five times it, which are backstops and not economics, as they
were.

## 3. What restores the level, once the anchor is gone

Nothing in the rule does, and that is deliberate. Three things outside
it do, and they are the classical ones:

- **Below**, the utilization curve: a producer whose posted price falls
  toward its cost curtails, stock falls short, pressure turns positive.
  The floor is `full_utilization_price_ratio` times cost, 1.05.
- **Above**, entry: `_invest` builds where expected price clears cost by
  `investment_margin_threshold` *and* there is a shortfall. New capacity
  fills the pool and pressure turns negative.
- **Across sectors**, nothing yet. A sector's profit rate is wherever its
  history left it. Profit-rate equalization is what the price of
  production computes as a reading (`docs/26`), and whether posted
  prices gravitate toward it is a question this design *asks* (§6.6)
  rather than assumes.

Between the floor and the entry threshold the level is neutrally stable:
a price can rest anywhere in the band. That is not a defect to engineer
out; it is the property a market without an anchor has, and the
scenarios measure how wide the band is in practice.

## 4. What it deliberately does not do

- It does not change the demand curve. `daily_demand` scales base demand
  by `(price / reference_price)^-elasticity`; the reference there is a
  fact about consumers' response, not a price anyone posts, and it stays.
- It does not change the pressure signals or their coefficients.
- It does not touch the labor value solve, the price of production, the
  ledgers or the wage rule. The wage still reads the regional price of
  the basket.
- It does not give a producer its own inventory. That is `docs/59`.
- It does not re-run the sweep.

## 5. Scenarios

Every existing scenario, with `posted_prices = True` via the parameter.
The readings come from four: `equilibrium` (stationarity), `regional_glut`
(the level after a shock, against the anchored model's recovery),
`technique_change` and `cost_competition` (full pass-through against
`docs/22`'s half), and `producer_loss` (the price rise a shortage
produces when nothing caps it but the bound).

New parameter: `posted_prices` (False). `price_adjustment_speed` and
`competitive_share_elasticity` are reused; `competitive_price_intensity`
is inert under the rule and stays for the anchored model.

## 6. Predictions

6.1 **Bit-identical off.** All 251 frozen metrics unchanged.

6.2 **Exactly stationary on.** Price range `0.0` over 240 days.

6.3 **The glut does not recover.** In `regional_glut` the yayo price
falls to a trough within 10% of the anchored model's, then climbs only
as far as stock returning to target lets it: on day 180 it is between
**60% and 85%** of the reference, where the anchored model is back
within 5% (`docs/06`'s target 3, half the gap in four quadrums, is
**not met**). The band in §3 is real and this is its width.

6.4 **Cost passes through in full.** In `technique_change` the meal price
falls by the full cost fall — between **0.9× and 1.1×** the ratio of the
cost falls — where `docs/22` measured 0.47% on a 12.7% value fall at
`κ = 0.5`. In `cost_competition` the meal price falls **20 to 30%**
where the anchored model fell 14.3%.

6.5 **A shortage is capped only by the bound.** In `producer_loss` the
yayo price peaks between **2× and 4×** the reference, against the
anchored model's peak, and does not come back down to the reference:
the entrant's capacity brings it to wherever stock reaching target stops
the integral, predicted **1.2× to 1.8×** on day 210.

6.6 **Profit rates do not equalize.** The dispersion of sector markups
(posted price over cost) across the six seeded sectors on day 240 of the
equilibrium is what it was seeded at, because nothing in the rule moves
a sector's level without pressure. This is the negative result the
design expects and the reason the price of production stays a reading.

6.7 **Two producers of one good converge.** In `cost_competition` the two
provisioners' posted prices end within **5%** of each other, because the
one posting higher loses the order book, and the pool's pressure is
common to both.

6.8 **The ledgers close** in every scenario, and with producer cash on as
well: sellers paid at their own posted price sum to what the buyer paid.

## 7. What would make this wrong

If 6.2 fails, some path recomputes cost to a different float on a
stationary day; find it. If 6.3 shows the price returning to the
reference, the anchor is still in the rule somewhere — the demand curve's
reference is the suspect. If 6.7 fails, the order book is not reading
posted prices.

## 8. Non-goals

No profit-rate equalization rule. No expectations beyond the smoothed
price `_invest` already reads. No price discrimination between buyers.
No producer inventory. No removal of `reference_price` from the demand
curve or from the seeding.
