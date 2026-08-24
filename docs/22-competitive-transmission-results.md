# Competitive transmission from cost to price: measured results

Recorded after implementing the design in
`docs/21-competitive-transmission-design.md`. The previous reference
describes the model with endogenous labor values but with prices anchored to
RimWorld's authored `MarketValue` and an order book shared out without regard
to cost.

## Headline

Cost now reaches price, and the cheaper producer now wins custom.

- All 83 tests pass (68 prior + 15 for the two mechanisms and the new
  scenario).
- **20 of 75 frozen metrics moved**, all in producer loss and technique
  change; the glut is untouched and equilibrium is still exactly stationary.
- The **displaced-inventory artifact from `docs/16` is gone**: Dust Basin's
  chemfuel buffer in the depletion scenario returns from 63.8% of target to
  **100%**.
- **Downstream cost-push exists for the first time.** `docs/16` recorded that
  a 49% chemfuel price rise moved the yayo price by exactly zero. It now
  moves it to 21.358.
- Producer loss converges *faster* than before — settled by day 300 rather
  than day 400, at exactly reference prices.
- All four material residuals and the cash residual close to floating-point
  zero in every scenario, including the new one. Runs are bit-identical.

## The result: value and price answer to different things

The session's two scenarios are deliberate opposites, and together they are
the clearest statement the model has yet made that labor value and market
price are distinct magnitudes rather than two names for one thing.

| | `technique-change` | `cost-competition` |
|---|---|---|
| what the entrant saves | **living labor** (152.5 vs 305 ticks/meal) | **overhead** (60% of incumbent's) |
| social labor value of meals | 305 → **266.30** (−12.7%) | 305 → **305.00** (0.0%) |
| meal price | 15.00 → **14.93** (−0.47%) | 15.00 → **12.86** (−14.3%) |
| money wage | 30.00 → 29.86 | 30.00 → **25.72** |
| value of labor-power (ticks) | 610 → **532.6** | 610 → **610.0** |
| rate of surplus value | 38.34 → **42.45** | 38.34 → **38.34** |

A labor-saving innovation moves value by an order of magnitude more than it
moves price. A capital-saving innovation moves price by an order of magnitude
more than it moves value — in fact it moves value not at all, because it
changes nothing about how much labor a meal takes.

The rate of surplus value follows value, not money: it rises when living
labor per meal falls, and does **not** move when the money wage falls 14.3%,
because the labor-power that wage buys still takes the same time to
reproduce. Money profit is not surplus value; a falling money wage is not a
falling value of labor-power. Both distinctions are now numerical.

## Transmission strength, and why it is small for labor

The honest measurement this session set out to take: **how much of a cost
change reaches the price?**

For the labor-saving case, very little — and `docs/21` said so in advance and
why. Wages are **2–4% of effective unit cost** in this calibration:

| producer (Dust Basin) | overhead | inputs | wages | wage share |
|---|---:|---:|---:|---:|
| chemfuel refinery | 1.5333 | 0 | 0.0312 | 2.0% |
| psychoid fields | 1.1517 | 0.1150 | 0.0578 | 4.4% |
| provisioners | 10.0000 | 0 | 0.3813 | 3.7% |
| drug lab | 0 | 15.6600 | 0.4375 | 2.7% |

Halving the living labor in a meal cuts its money cost by 1.8%, so at
`kappa = 0.5` it moves the anchor by 0.9% and the price by 0.47%. The
mechanism is working exactly as specified; there is simply very little labor
in the money cost for it to transmit.

That is a finding about **the calibration**, not about the mechanism, and it
points at the next structural problem. The `unit_cost` operating overhead is
a residual that `docs/13` derived as *whatever makes producers run at full
utilization at reference prices*. It has no economic interpretation, and for
meals and chemfuel it is over 95% of cost. An economy whose money costs are
95% unexplained residual cannot show much of anything about labor. Naming
that is more useful than tuning it, and tuning it to make this number look
better would have been fitting the instrument to a forecast.

The `cost-competition` scenario exists to show the same machinery at a
magnitude where it is visible: a 36% cost advantage moves the sector cost
ratio to 0.715 and the price down 14.3%, with the cheap producer taking
**72.7%** of the order book.

## Prediction scorecard

### "Equilibrium: exactly zero movement" — **correct**

Price range exactly 0 for all four commodities in both regions.
`1 + kappa * (ratio − 1)` is exactly 1.0 when the ratio is exactly 1.0, so
the anchor is bit-identical to the reference price at equilibrium.

One correction was needed to get there: the seeded sector cost initially
excluded wages, because `wage_cost_per_unit` is only set during production
and was still zero at construction. The ratio therefore opened above one and
the equilibrium drifted. Wage costs are now computed once at construction,
so the seed and the daily measurement are the same quantity.

### "Glut: little or no movement" — **correct**

Exactly zero movement in every glut metric, including the degenerate
upstream extrema. The glut crashes yayo while leaves and chemfuel hold at
reference, so yayo's cost ratio stays at one and the anchor stays at 21.

### "Producer loss: substantial movement, peak falls to 26–33" — **wrong on
direction; the reasoning was half right**

The peak **rose** to 45.25 on day 126, from 38.63 on day 119.

The prediction reasoned correctly that leaves are 94% of yayo's cost and that
the leaf price crashes to 0.693 — but took the trough as the whole story. The
leaf crash happens on **day 70**; the yayo peak happens **56 days later**, by
which time leaves have not merely recovered but overshot to 2.65. The cost
ratio at the peak is 1.37, not 0.39.

Measured against a `kappa = 0` control, the anchor does exactly what was
predicted at each moment — it simply amplifies the whole cycle rather than
damping the peak:

| day | κ=0 yayo | κ=0.5 yayo | leaf price | yayo cost ratio |
|---:|---:|---:|---:|---:|
| 70 | 25.43 | **19.89** | 0.6934 | 0.394 |
| 80 | 30.40 | 26.28 | 0.9623 | 0.504 |
| 110 | 37.64 | 43.29 | 1.8311 | 0.962 |
| 126 | 36.71 | **45.25** | 2.6519 | 1.370 |
| 168 | 22.55 | 25.47 | 2.5935 | 1.352 |

Cheap inputs drag the product down early; dear inputs push it up later. This
is cost-push propagation, and its absence was exactly what `docs/16`
complained of. Whether a *shortage of yayo* should show up partly as *cheap
leaves* is a fair question to put to the model, and the answer it now gives
is a defensible one: with the drug lab crippled, leaves genuinely are in
surplus, and a lab that buys them cheaply genuinely does have a lower cost.

### "Depletion: buffer recovers to 75–90% of target" — **correct in
direction, understated in size**

It recovers to **100%**. The prediction assumed that at `kappa = 0.5` only
half the cost increase reaches the anchor, so some coverage gap would still
be needed. In fact the chemfuel cost ratio reaches 1.98, which lifts the
anchor to 2.3 × 1.49 = 3.427 — comfortably above the 3.098 cost — so no
coverage gap is required at all and the buffer fills completely.

### "Subsistence shock: meal price peak damped to the high twenties" — **correct**

35.52 → **27.83**, with the wage following from 71.04 to 55.65. Destroying
provisioning capacity creates scarcity but barely raises the *cost* of a
meal, so a cost-aware anchor pulls against the spike.

### "Technique change: price falls 0.5–1.5%" — **correct, just below the band**

0.47%. The band was slightly optimistic for the same reason it was narrow:
transmission is proportional to the wage share of cost.

### "Cost competition: 60–75% share, 15–25% cost fall, 5–12% price fall" — **share correct, both magnitudes exceeded**

Share 72.7% (in band). Sector cost fell 28.5% and price 14.3%, both beyond
the predicted bands. The prediction did not account for the second round: a
lower meal price lowers the wage, which lowers every producer's cost
including the provisioners' own, which lowers the anchor again. The loop is
the one `docs/21` computed a gain of 0.018 for — convergent, as predicted,
but not zero, and it compounds over 180 days.

## Findings beyond the predictions

### The buffer scar heals better, and faster

Producer loss now ends with upstream buffers 20–29% fuller (leaves 1878 vs
1454, chemfuel 125.4 vs 104.6 at day 210) and upstream prices 10–21% lower
(leaves 1.956 vs 2.467). The same mechanism as the depletion fix: a
reference-anchored price could only stay elevated by keeping inventory short,
so the model held buffers down to hold prices up. With cost in the anchor,
prices can be high because costs are high, and the inventory is free to
refill.

Long-run convergence improved with it. The scenario settles by **day 300**
rather than day 400, and lands exactly on reference prices (21.0000, 1.9000,
2.3000) with zero day-to-day drift.

### Part B is invisible until techniques differ

Cost-weighted allocation changed nothing at all in any existing scenario,
because every producer of a commodity currently shares a cost: they share a
process, and investment gives entrants the incumbents' average overhead. It
bites only in the two scenarios where costs genuinely differ. Verified
directly: with `epsilon = 0` the producer-loss price path is bit-identical to
the run with `epsilon = 2`.

### The mechanism is a dial, not a switch

Both mechanisms have a setting that reproduces the previous model exactly —
`competitive_price_intensity = 0` restores the authored-reference anchor,
`competitive_share_elasticity = 0` restores uniform rationing bit-for-bit.
Transmission strength is therefore a measurable quantity in this model rather
than a built-in assumption, which is what the `kappa = 0` control column in
the producer-loss table above is made of.

## What is still missing

The dear producer never leaves. It loses share — 27.3% against 72.7% — but
keeps its capacity, keeps inflating throughput demand and inventory targets
through the full-capacity convention, and would take its share straight back
if its cost fell. Competition here is competition for orders, not for
survival. Exit needs capacity depreciation or mothballing, which stays a
standing omission and is the natural next piece of work.

Profit rates are still not equalized across sectors. The ratio anchor freezes
each sector's calibrated rate of profit — 30.5% on yayo, 43.5% on leaves,
47.0% on chemfuel, 44.5% on meals — and moves prices around it. A genuine
price of production would equalize them through capital mobility, which is a
larger change than this session attempted and would move every price in the
model.

## Reference decision

Two commits, deliberately separate. The first refreshes the 20 moved metrics
and explains them; the second adds 10 newly observed quantities as a pure
insertion. 75 metrics to 85.
