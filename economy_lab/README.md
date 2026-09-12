# Stage 0 economy laboratory

This is the dependency-free, deterministic prototype for the economy mod. It
exists to make the economic rules falsifiable before UI, pawn AI, saves, or
Harmony complicate debugging.

The model is a four-commodity circuit in two regional markets:

```
chemfuel ──┬──> psychoid farm ──> psychoid leaves ──> drug lab ──> yayo
           └────────────────────────────────────────────^
provisioners ──> meals ──> workers ──> labor-power ──> every producer
```

Chemfuel is consumed by two producers, so contention for a scarce shared input
is exercised; leaves sit between two stages, so a shortage has to travel;
meals reproduce labor-power, so the wage relation lives inside the material
circuit rather than beside it. It supports:

- accounted input-output production: a producer must source real inventory,
  and one that cannot is rationed rather than subsidised;
- cost floor: a producer's effective unit cost includes the market price of its
  inputs at current regional rates, curtailing production on margin compression
  before physical inputs are exhausted;
- damped demand-led replenishment: production follows intended outflow plus a
  proportional correction toward material inventory targets;
- local production, consumption, inventory, prices, and silver;
- a costly route with finite daily capacity and delivery time;
- profitable planetary arbitrage when a regional spread covers freight;
- destruction of productive capacity, upstream or downstream;
- construction-fund investment: new capacity costs silver proportional to
  effective unit cost, drawn when commissioned;
- buffer-aware investment: stock deficits that surplus capacity cannot refill
  within a planning horizon trigger proportional additional capacity;
- finite resource reserves with ordered grade depletion: cheapest deposits
  are extracted first, and the marginal cost rises when they exhaust;
- differential rent tracked as a separate quantity: the cost advantage of
  infra-marginal regions over the most expensive active extractor;
- the wage relation: workers are paid the subsistence basket (meals) at
  current regional prices, wages enter effective unit cost, and silver
  cycles producer → wage → worker → basket purchase → producer revenue;
- a fixed regional labor pool with pro-rata rationing when it binds;
- a surplus ledger separating living, necessary, and surplus labor
  (work-ticks) from the silver wage bill — money profit is not surplus
  value;
- explicit material and silver ledgers separating final from productive
  consumption, with investment spending and reserve depletion tracked;
- fixed capital that transfers value: each sector carries its real
  RimWorld building in both silver and embodied labor, depreciating by
  use — the omission `FINDINGS.md` recorded in vanilla, repaired and
  measured at 0.353% of constant capital;
- a value ledger: c, v and s in work-ticks with the organic composition
  and the value rate of profit, and a third closing identity beside
  material and silver — value of output equals c + v + s;
- a price decomposition: inputs, wages, capital consumed, and the
  unattributed wedge between RimWorld's authored price level and anything
  the model can account for. Surplus is reported as two readings that
  name their assumption, never as one number;
- a cost-aware price anchor: the anchor moves with the sector's
  output-weighted average cost relative to its seeded cost, so upstream
  cost propagates downstream and a price no longer needs a starved
  inventory to stay above a risen cost;
- cost-weighted order allocation: a commodity's order book is shared
  among its producers by a constant elasticity on relative cost, capped
  by each producer's own limit — the cheaper producer wins more custom,
  continuously rather than all at once;
- endogenous labor values solved from the process graph: transferred
  labor plus living labor per unit of output, iterated to a fixed point
  so a cyclic graph is answerable and a non-productive one fails loudly.
  The social (output-weighted) value and each region's individual value
  are reported separately, which is where the average/marginal
  distinction shows. The authored `FINDINGS.md` figure stays untouched
  on the commodity for comparison.

Per-unit ratios and reference prices are read from RimWorld's own defs. The
modelling choices — mass apportionment for joint products, proportional input
rationing, simultaneous production, derived demand — are recorded in
`docs/08-accounted-input-design.md`. The cost floor and investment decisions
are in `docs/13-cost-floor-and-investment-design.md`. The resource reserve and
rent decisions are in `docs/15-resource-reserves-design.md`. The wage
relation, subsistence basket, and surplus ledger decisions — including the
floating-point engineering that keeps the equilibrium exactly stationary —
are in `docs/17-labor-power-and-surplus-design.md`. The value equation,
its social scope, and the technique-change scenario are in
`docs/19-endogenous-labor-values-design.md`. The cost-aware anchor and
cost-weighted allocation are in
`docs/21-competitive-transmission-design.md`. Fixed capital, the
reclassification of the operating overhead, and the value ledger are in
`docs/23-constant-capital-and-the-overhead-design.md`. Read all seven
before changing them; each was chosen deliberately and several have
defensible alternatives.

Run all example scenarios:

```text
python -m economy_lab all
```

Run only the scenario that actually exhausts an input buffer:

```text
python -m economy_lab input-shortage
```

Run the depletion scenario (one region's cheap chemfuel grade exhausts):

```text
python -m economy_lab depletion
```

Run the subsistence shock (meal scarcity drags the wage, and every cost,
upward):

```text
python -m economy_lab subsistence-shock
```

Run the technique change: a provisioning technique with half the living
labor enters one region, so the social value of the wage good falls and
the rate of surplus value rises in *both* regions with the working day
and the basket held fixed — relative surplus value:

```text
python -m economy_lab technique-change
```

Run the cost competition — its deliberate opposite, where the entrant
saves overhead rather than labor, so the meal *price* falls 14% while its
labor *value* does not move at all:

```text
python -m economy_lab cost-competition
```

Compare current behavior with the deliberately frozen reference. This is a
report only; movement does not make the command fail:

```text
python -m economy_lab.baseline
```

Replace the reference only when a behavioral change is understood and
intended:

```text
python -m economy_lab.baseline --write-reference
```

Run the deliberate one-at-a-time parameter sensitivity sweep. It perturbs each
exposed calibration parameter independently and writes both detailed CSV and a
plain-text ranking; it is not part of per-commit testing:

```text
python -m economy_lab.sensitivity
```

Run the gravitation scenario: the market economy with the going margin
set inside the band the authored prices give, so capital enters every
sector above it and idle capacity cuts, and the authored price structure
goes where the going margin sends it (`docs/61`, `docs/63`):

```text
python -m economy_lab gravitation
```

Run the overshoot scenario: the 60% capacity loss on the market with both
entry and exit on, 500 days, where entry's pipeline overshoots the demand
on its lead time and exit takes the surplus back out (`docs/64` to
`docs/69`):

```text
python -m economy_lab overshoot
```

Open the laboratory in a browser (`docs/48`). The viewer runs any scenario
with any parameter overridden, draws the history with the shock day
marked, lays the five ledgers out apart, compares two runs as
differences, browses the frozen metrics and the sweep's ranking, and
renders every document in `docs/`. It reads; it cannot tune. Standard
library on the server, plain HTML on the client, no dependency:

```text
python -m economy_lab.viewer
```

Run the acceptance tests:

```text
python -m unittest discover -s tests -v
```

## Current behavioral targets

The calibration is expressed relative to regional flows:

1. A shipment equal to 25% of one region's annual yayo consumption lowers its
   local price by at least 20%.
2. With the initial expensive route, the same shock moves the distant region
   by less than 5%.
3. The local price recovers half its gap within four quadrums.
4. Destroying 60% of regional capacity raises price at least 50% once stocks
   fall below ten days.
5. Delayed entry restores 80% of baseline supply within four to eight
   quadrums.
6. Every commodity traces to a declared source and sink, and silver conserves,
   within floating-point tolerance.
7. An upstream capacity loss curtails downstream output proportionally rather
   than cliffing it to zero, and registers as unmet demand for the input.

These are provisional gameplay targets, not empirical elasticity claims.

## Scope of the frozen baseline

`behavior_baseline.json` freezes 154 metrics: the original thirteen yayo
metrics, forty upstream observations of chemfuel and psychoid leaves during
the glut and producer-loss shocks, twelve labor/subsistence observations
(equilibrium employment, wage, rate of surplus value, meal settlement, and
the employment and meal-price paths through both shocks), and ten labor
value observations (the four endogenous values, and the technique-change
scenario's social, adopter, and laggard values with both regions' rate of
surplus value), and ten competitive-transmission observations (the two
contrasting scenarios' prices, the share won by the cheapest producer, and
the depletion buffer as a fraction of target), and sixteen value-ledger
observations (c, v, s and the classical ratios, the wedge as a share of
each price, and each sector's money rate of surplus value against the
uniform labor-time rate), and fourteen price-of-production observations
(the uniform profit rate, the basics count, each commodity's production
price against meals, against its labor value and against its authored
price, the aggregate profit-over-surplus ratio, and the profit rate
after the wage-good technique change), and twenty subsistence-basket
observations (the basket's labor and money cost, its share of the
working day, the workers one provisioner's day feeds, the two new wage
goods' production prices and money rates, the rank-one profit rate the
price system now departs from, and the generous-basket bound), and
fifteen turnover observations (the profit rate per period beside the
gross markup, the capital advanced itemised into commodity stock,
installed plant and the wage advance, realized turnover against the
turnover the price system assumes, the rate of profit on advances, and
the perishable-meals scenario), and five structural scale observations.
The scale figures deliberately exclude *timings*, which are
machine-dependent; what is frozen is that the labor value solve run at
647 commodities reproduces the closed analysis exactly for all 447 the
generator did not contaminate. The reporter remains observational; the
invariant tests protect correctness.

The current reference describes the model with profit charged against
capital advanced rather than capital consumed. Its design and results
are in `docs/30-turnover-design.md` and `docs/31-turnover-results.md`;
the layers beneath it are in docs/13–29. Turnover moved no behavioral
metric — it is a scalar on a price system that never fed back — but it
renamed five, because the quantity those metrics held was the gross
markup rather than a rate of profit.

## Intentionally absent from this slice

- competitive *exit*: built, measured and corrected twice (docs/64 to
  docs/69), off by default and held back for one reason only. A producer
  whose return on its capacity — its posted margin times its utilization,
  against the going margin — has been below the going one for the
  investment lead time withdraws the capacity it holds beyond a 10%
  reserve over the demand it expects, never below the larger of that
  reserve and the smallest plant the fund would build (docs/66). The
  signal works: a cost advantage draws the incumbent down to its custom
  plus the reserve, and the investment rule reading the market's demand
  instead of the plan's throughput kills the oversized entrant a shortage
  used to place. Its input works too, since docs/68: the sell-out is
  noted after the order has drawn the stock down, so a seller emptied by
  the very order it is answering sees the demand it missed, and the
  glut's basket — which used to go short every day at a price that never
  rose — is served from day 181 on (docs/69 §2). What holds the flag back
  is the cobweb (docs/70, docs/71). Final demand is price-elastic at 1.35,
  and above unit elasticity a price cut raises the sector's revenue — so
  the cheaper sector keeps building capacity for the demand its last cut
  created, until the stock drains and the loop runs backwards. Entry on
  margin is not in it: with the flag off the cycle is bit-identical. The
  first rule against it, exit's floor extended to the plant the
  investment rule would rebuild at once, was built, failed its central
  prediction and was reverted, and whether to damp the cycle at all is
  the open question;
- a price system of its own: two-thirds of every upstream price is a wedge
  the model cannot attribute, because prices are anchored to RimWorld's
  authored MarketValue while costs are built from a wage those prices
  never knew about (docs/24). Prices of production are now *computed*
  beside the authored ones but deliberately not adopted: the uniform
  markup is 24.6 over a 21-day turnover — a profit rate of 1.17 a day —
  and yayo prices at 38.7× its authored ratio to meals. Enlarging the
  basket halved that and did not fix it (docs/29);
- a capital-goods sector: building capacity spends silver but consumes no
  material, and it is what would let fixed capital — 3.5% of the capital
  advanced — into the price system (docs/31);
- equalization of profit rates across sectors — computed, not adopted;
- labor content of resource grades, so depletion moves value as well as
  cost and rent;
- absolute (monopoly) rent;
- wage deviations from value: the reserve army is done (docs/46, docs/47)
  and so is the habituation of a sustained premium into the standard
  (docs/51, docs/52); worker mobility is not;
- credit and bankruptcy;
- capacity depreciation or mothballing;
- transfer pricing and producer-level inventory: producers hold cash
  (docs/55, docs/56, off by default) but the regional pool is still a
  consignment paid out by supply share; firm-posted prices exist
  (docs/57, docs/58, off by default) and so does procurement -- producers
  owning their output and buying their inputs, no fixed point (docs/59,
  docs/60, corrected in docs/62, off by default). With every stock target
  the inventory life of its producer's own expected demand, and idle
  capacity cutting above a going margin, the market gravitates from
  above; entry on margin (docs/61, docs/63, off by default) is the
  capacity side of the same signal, and with the going margin set inside
  the authored band every sector ends at it. Exit is the bullet above;
  with it off, entry overshoots on its lead time and the capacity stays;
- more than six commodities or two regions;
- RimWorld runtime integration.

The next slice should derive prices of production from the technical
coefficients, the wage, and a uniform profit rate, instead of anchoring
them to authored MarketValue. Every other component of the overhead has
been carved out and named; what remains cannot be closed while the anchor
is imported.
