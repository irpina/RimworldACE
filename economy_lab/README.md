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
`docs/21-competitive-transmission-design.md`. Read all six before
changing them; each was chosen deliberately and several have defensible
alternatives.

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

`behavior_baseline.json` freezes 85 metrics: the original thirteen yayo
metrics, forty upstream observations of chemfuel and psychoid leaves during
the glut and producer-loss shocks, twelve labor/subsistence observations
(equilibrium employment, wage, rate of surplus value, meal settlement, and
the employment and meal-price paths through both shocks), and ten labor
value observations (the four endogenous values, and the technique-change
scenario's social, adopter, and laggard values with both regions' rate of
surplus value), and ten competitive-transmission observations (the two
contrasting scenarios' prices, the share won by the cheapest producer, and
the depletion buffer as a fraction of target). The reporter remains
observational; the invariant tests protect correctness.

The current reference describes the model with competitive transmission. Its
design and results are in `docs/21-competitive-transmission-design.md` and
`docs/22-competitive-transmission-results.md`; the layers beneath it are in
docs/13–20. Twenty of the previous 75 metrics moved, all in producer loss
and technique change.

## Intentionally absent from this slice

- competitive *exit*: a producer that loses the order book keeps its
  capacity indefinitely, so competition is for orders, not survival;
- an economic interpretation for the operating overhead, which is a
  calibration residual and over 95% of cost for meals and chemfuel — the
  reason transmission is weak for labor-saving change (docs/22);
- equalization of profit rates across sectors;
- labor content of resource grades, so depletion moves value as well as
  cost and rent;
- absolute (monopoly) rent;
- wage deviations from value: bargaining, the reserve army, mobility;
- credit and bankruptcy;
- capacity depreciation or mothballing;
- individual producer cash accounts and transfer pricing;
- more than four commodities or two regions;
- RimWorld runtime integration.

The next slice should add capacity depreciation and mothballing, so that
competition is for survival and not only for orders; or give the operating
overhead an economic interpretation, since an economy whose money costs are
mostly unexplained residual can only say so much about labor.
