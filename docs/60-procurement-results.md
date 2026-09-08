# Procurement: producers own their output and buy their inputs: results

`docs/59` set out six predictions. Four held, one held after a change the
design had not foreseen, and one was wrong. Along the way the build found
the defect behind `docs/58` §5, and that document carries a correction.

**The headline: the laboratory now runs with no production fixed point
and no pool. Every producer plans from its own sales and stock, buys from
the sellers it can afford with custom split continuously by price, and
asks a price that answers its own excess and its own sell-outs. The
seeded circuit is exactly stationary from the reseeded state, and all
three identities close with producers' stocks inside them.**

## 1. What shipped

One flag (`procurement`), needing `producer_cash` and `posted_prices`.
Per producer: a stock of its own output, an inputs-on-hand account, sales
today and yesterday, and sell-outs today. Per region: the fund's stock and
its own asking price. A morning market where producers buy inputs and
plant matter; a production pass into each producer's stock; an evening
market where the fund and the workers buy; exports bought from producers
by the destination's fund and imports held by the fund. The plan of
`_planned_runs`, the order book of `_allocate_orders`, the pool's supply
shares of `docs/56` and the pool's pressure of `docs/58` are all bypassed
when the flag is on and untouched when it is off. Seventeen metrics
frozen (280 total), eight tests (222 in the laboratory suite), and every pre-existing
metric unchanged except the three the `docs/58` correction moved (§2).

Three things the design did not specify had to be decided, and each is
recorded here because each changed a result.

**Custom is split continuously by price.** Cheapest-first, as designed,
is Bertrand competition: a seller a hair cheaper takes everything, the
loser's stock rises, it cuts below the other, and two provisioners with
capacity to spare each raced to 6.5 silver against a cost of 10.3. The
market now splits a buyer's custom by what each seller holds, weighted by
its price against the cheapest to the constant elasticity `docs/21`
already uses for the order book. One seller still takes everything.

**A producer does not ask less than the price at which it would make
nothing.** The clamp's floor moves from 18% of cost to the utilization
curve's zero, 70%.

**An empty warehouse is not scarcity.** The design's own-stock signal
read a stock below target as pressure to raise, so an entrant filling
its warehouse raised its price and never sold. The signal is now
*excess* stock, which cuts, and *sell-outs* — demand a buyer brought to
a seller that had sold today and had nothing left — which raise. A stock
merely below target does neither. And the target a producer's price reads
its stock against is its share of the sector's *sales*, not of its
capacity, so an incumbent is not made to cut because a rival appeared,
and a rival selling nothing holds nothing but excess.

## 2. The `docs/58` correction, and the three metrics that moved

A producer added after seeding — an entrant, or a producer a scenario
appended — began with a posted price of zero, which the clamp raised to
18% of cost. `docs/58` §5 read the oscillation this caused as the shared
pool giving a contested sector the wrong signal. With every producer
asking the going price from its first day, the pool rule converges: the
provisioners' posted spread ends at **1e-5** in both scenarios and the
`cost_competition` meal price at 15.11, not 8.69. The three frozen
`posted.*` readings moved from a defect's numbers to the rule's, and
`docs/58` §5a says so.

## 3. Held: 6.1, 6.2, 6.3, 6.5

**6.2** Price range `0.0` and stock range `0.0` over 240 days, every
producer's stock equal to the region's inventory of its good, every
inputs-on-hand account back at `0.0` each evening. The seeding placed the
pool in producers' hands and one day's outflow in their sales, and the
first day repeated the seed to the bit.

**6.3** The glut's trough is **0.930×** the reference on day 81 and it
rests at **0.993×** — below the reference, no overshoot, inside the 15%
the design allowed — against the planned model's trough of 0.684× and
its return to 1.000×. It is shallower because the injected stock is the
fund's, and the fund cuts its asking price on its own excess at the same
small gain producers use; the producer cuts only when the fund's sales
leave *its* stock in excess. A glut in a market of owners is a slow
sale, not a crash.

**6.5** Cash, value and material residuals of order 1e-9, 1e-8 and 1e-11
in every scenario. The one exception is not the market's: a technique
change leaves a value residual of 52.9 with procurement and **50.6
without it**, because output is valued at the day's opening values
(`docs/23`) and a technique mix that moves day to day is not one basis.
That has been true since `docs/19` and no test asserted otherwise; one
does now, that the two residuals are the same residual.

## 4. Held, once the signal was right: 6.4

The two provisioners end within **0.13%** of each other in
`technique_change` and `cost_competition` alike, and the cheaper one
holds the larger share — **50.07%** against 49.93%. The design predicted
the ordering; the margin is thin because nothing in a producer's rule
makes it *seek* share. It cuts on excess and raises on sell-outs, and a
producer selling its half has neither.

That thinness is the result. In `cost_competition` the entrant's cost is
6.51 against the incumbent's 10.51, and the meal price ends at **14.21**:
five percent below where it started, and above the planned model's 12.90.
The entrant asks the going price on arrival, passes through only changes
in its own cost, and never has an excess to cut on. Its advantage is a
markup of 2.2 that nobody competes away. The planned model's price fell
because the anchor read the sector's *average* cost; the market's price
does not fall because no one in it is trying to undercut. What would
make it fall is the mechanism `docs/58` §4 named for the level: entry
that responds to a margin and not only to a shortfall.

## 5. Wrong: 6.6

A 240-day equilibrium costs **0.111 s** with procurement and 0.109 s
without. A pass is not an iteration, but a pass that walks every seller
for every buyer of every input is not free either, and the fixed point
at six commodities converges in one or two iterations. The prediction
would hold at scale, where the fixed point is the day's cost
(`docs/33`); it does not hold here, and it was made here.

## 6. What the market does that the plan did not

Beside the readings above, three of the shock scenarios say what a
dynamically complete economy does with a shock, and each is a number the
planned model cannot produce.

**A shortage is priced by the sellers who ran out, and the level stays.**
`producer_loss` peaks at **1.794×** the reference on day 190 and ends at
1.788×, with capacity rebuilt to 13.19 units a day (the planned model:
peak 2.150×, back to 1.023×, capacity 11.90). The entrants arrive, ask
the going price, sell at it, and have no excess to cut on.

**A demand boom is absorbed by price.** Employment on day 360 is
**0.289** worker-days — *below* the seeded 0.318 — with yayo at 1.265×
the reference. The seller sold out, raised, demand fell on its elasticity,
and the investment rule built for a shortfall that the higher price had
already removed. The planned model's boom lifted employment to 0.397.

**A subsistence shock is a shortfall, not a spike.** Meals peak at
**1.214×** their reference with a basket shortfall of 7.63 units, against
the planned model's 4.96× spike and 5.70 units. The sell-out signal
raises at two percent a day; the pool's pressure raised at the anchored
rule's proportional gain. Workers go short for longer and pay less.

All three are the same finding from three sides: with no anchor, no
average-cost pass-through and no entry on margin, a shock's price is
permanent. `docs/58` §4 said this of the pool rule; it is true of the
market too, and it is not a defect of either. It is what the classical
gravitation mechanism is *for*, and the model does not have it yet.

## 7. Carried forward

**Entry on margin** is now the one mechanism between this economy and
prices that gravitate. `_invest` builds where expected price clears cost
by a margin *and* there is a shortfall; the second condition is what
keeps every level where a shock left it. Its removal, or a second rule
beside it, is the next design.

**The planned model stays the default**, because 231 readings and
forty documents rest on it and because the market changes every shock.
The market is the laboratory's answer to Tesfatsion's exercise and the
model the game should eventually carry; which of the two the frozen
reference follows is a decision for after entry on margin, not before.

**The C# port** (`docs/53`) should carry the market and not the plan.
There is no fixed point to transliterate, and the market's day is a
sequence of purchases — exactly the shape a runtime amortising across
ticks wants.

## 8. Cost

Seven runs of 240 to 360 days, about 1.5 seconds of the metric
collection.
