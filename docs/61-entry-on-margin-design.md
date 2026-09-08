# Entry on margin: capital goes where the price clears cost: design

Written before implementation. `docs/60` §7 named this as the one
mechanism between the market economy and prices that gravitate:
`_invest` builds where expected price clears cost by a margin *and*
there is a shortfall, and the second condition is what leaves every
shock's price level where the shock put it. This document adds the
classical rule beside it — capital enters a sector because the sector
is profitable, whether or not it is short — and says what that should
do to each reading `docs/60` froze.

## 1. What the investment rule does today

Every fifteen days, for every region and commodity, `_invest` computes a
*shortfall*: throughput above capacity and pipeline, plus a buffer
deficit that surplus capacity cannot refill within the horizon. It
builds a fraction of that shortfall — and only that — if the expected
price clears the sector's mean effective cost by `investment_margin_threshold`
(0.18) and stock is below target. At the seed every sector's margin
clears 0.18 (measured: 0.29 for yayo up to 0.46 for chemfuel), so the
margin gate does no work there; the shortfall gate is what keeps the
seeded circuit stationary, and it is also what keeps `producer_loss` at
1.79× the reference forever. A sector selling at that price with its
stock at target and its capacity rebuilt to demand has no shortfall, so
nobody comes.

The entrant a shortfall summons uses the *first* active producer's
technique and the sector's *mean* overhead. In `cost_competition` that
is the incumbent's, not the cheaper entrant's.

## 2. The rule

Off by default (`entry_on_margin = False`), bit-identical off. On, a
second term is added to the amount `_invest` builds, and the shortfall
term is left exactly as it is:

**The signal is the margin of the expected price over the cost of the
best technique in the sector.** Best means the active producer with the
lowest effective unit cost at the region's prices; a sector with no
active producer uses the known process at 70% of the reference price,
as the shortfall rule already does. The margin is read against the
expected price (the 5% exponential average `_invest` already reads), so
a one-day spike summons nobody.

**Entry happens when the margin exceeds `entry_margin_threshold`**, and
in proportion to how far it exceeds it:

    entry = entry_gain × throughput × (margin − threshold) / threshold

capacity per investment interval. No shortfall condition and no stock
condition. A sector with its stock at target and its price at twice
cost is the case the rule exists for.

**The entrant uses the best technique.** With the flag on, every
project — whether the shortfall term or the entry term summoned it —
copies the cheapest active producer's process and overhead. This is the
one change to what the shortfall term does with the flag on, and it is
deliberate: an entrant that copies the dearest technique in a sector is
not the entrant classical competition describes.

**Everything after the amount is unchanged.** Cash cap, material cap,
minimum project size, construction spending, lead time, and the
entrant's arrival with a purse and the going price (`docs/55`,
`docs/57`).

**The threshold's default is 0.50**, above the largest seeded margin,
so the seeded circuit is exactly stationary with the flag on and every
reading below is a reading of a shock. That is a choice, not a
derivation: RimWorld's authored prices give every sector a margin
between 0.29 and 0.46 over its cost, and there is nothing in the model
that says which of those is the *going* rate. §5's `gravitation`
scenario sets the threshold *inside* that band, to measure what the
market does to the authored price structure when capital is allowed to
say that 0.30 is enough.

## 3. Why margin and not the rate of profit

`docs/30` established that the classical signal is the rate of profit
on capital advanced, not the markup, and that the two differ by
turnover. An entrant's advance is the construction outlay, which for
every bill-free process is `construction_cost_multiplier` (60) days of
effective cost; its return is the margin per unit sold; so its daily
rate of return is the margin over 60 in every sector alike, and a
threshold on one is a threshold on the other. The two rules come apart
only where a process carries a capital bill (`docs/36`), and no reading
in this document is taken there. The rate-of-return form is the right
one and is carried forward for the Department I scenarios; the margin
form is used here because it is the form the existing gate already
uses and the equivalence is exact where it is read.

## 4. What it deliberately does not do

- **No exit.** A sector below the threshold gets no entry and loses
  nothing. Producers that entry has crowded out keep their capacity and
  plan from their sales; under `producer_cash` they go bankrupt only if
  their purse idles thirty days (`docs/55`), which selling a little
  prevents. Gravitation is one-sided in this slice, and where a
  glut's level rests is still the glut's own business.
- **No expectation of the entrant's effect.** Ten entrants summoned by
  the same margin over ten intervals do not each foresee the other
  nine. The lead time is 45 days and the interval 15, so three are in
  the pipeline before the first arrives; overshoot is possible and is
  one of the things measured.
- **No change to the planned model.** The flag works with procurement
  off — `_invest` is shared — but the anchor already restores the level
  there, so an entrant adds capacity the plan will not use. Measured
  once, for the record, and not frozen.

## 5. Scenarios

Every scenario `docs/60` read, on the market model with the flag on and
the threshold at its default, so each reading sits beside the market's
own. One new scenario, `gravitation`: the seeded circuit, no shock, the
market model, and the threshold at 0.30 — above yayo's seeded margin
of 0.29 and below every other sector's — run for 720 days. It asks
where prices go when the authored structure is not a rest point.

## 6. Predictions

6.1 Bit-identical off.

6.2 Exactly stationary on, at the default threshold; and the glut is
bit-identical to the market's glut without the flag, because a
restoring force from above never fires in a glut.

6.3 `producer_loss` rests between 1.05× and 1.28× the reference (the
market's 1.79×; the planned model's 1.02×). The threshold puts the
rest at cost × 1.5, which is 1.16× the authored price; the band allows
an overshoot from the pipeline and an undershoot from the entrants'
cutting on their opening excess.

6.4 `demand_boom` ends with employment above the seeded 0.318 (the
market's 0.289; the plan's 0.397), because the entrants bring the price
down and demand back up on its own elasticity.

6.5 `cost_competition` ends with the meal price below 11 (the market's
14.21; the plan's 12.90), because every entrant copies the technique
costing 6.51 and cuts on its opening excess; and the cheap technique's
share of sales ends above 60%, because there is more than one producer
using it.

6.6 `subsistence_shock` leaves a smaller basket shortfall than the
market's 7.63 units, because entry into meals answers a margin the
sell-out signal raised.

6.7 `gravitation`: by day 720 every sector in both regions has a margin
within 0.05 of the threshold, yayo included. Yayo is below the threshold
at the seed and attracts nobody until its inputs' prices fall; that its
margin ends at the threshold is the prediction that cost propagation
through the market works in the direction the anchor never had to
carry. Each price's range over the last 60 days is under 1% of its
level.

6.8 The three identities close in every scenario, with procurement's
tolerances.

## 7. What would make this wrong

If 6.3 rests above 1.28×, the fund cannot pay for the entry the margin
summons and the cash cap is the binding rule — which would be a finding
about the fund, not about entry. If it rests below 1.05×, entry
overshoots on the lead time, and the gain or the interval is the next
parameter to read. If 6.7's yayo margin stays at 0.29, the cost fall in
its inputs does not reach its cost through the market as it reached it
through the anchor, and `_update_cost_ratios` is where to look. If a
price's range over the last 60 days exceeds 1%, entry and cutting are
oscillating on the lead time, which the classical literature predicts
and this design has not damped.
