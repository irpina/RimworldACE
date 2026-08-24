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
- fixed Labor Content value beside the market price.

Per-unit ratios and reference prices are read from RimWorld's own defs. The
modelling choices — mass apportionment for joint products, proportional input
rationing, simultaneous production, derived demand — are recorded in
`docs/08-accounted-input-design.md`. The cost floor and investment decisions
are in `docs/13-cost-floor-and-investment-design.md`. The resource reserve and
rent decisions are in `docs/15-resource-reserves-design.md`. The wage
relation, subsistence basket, and surplus ledger decisions — including the
floating-point engineering that keeps the equilibrium exactly stationary —
are in `docs/17-labor-power-and-surplus-design.md`. Read all four before
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

`behavior_baseline.json` freezes 65 metrics: the original thirteen yayo
metrics, forty upstream observations of chemfuel and psychoid leaves during
the glut and producer-loss shocks, and twelve labor/subsistence observations
(equilibrium employment, wage, rate of surplus value, meal settlement, and
the employment and meal-price paths through both shocks). The reporter
remains observational; the invariant tests protect correctness.

The current reference describes the model with the wage relation. Its design
and results are in `docs/17-labor-power-and-surplus-design.md` and
`docs/18-labor-power-and-surplus-results.md`; the cost floor and reserve
layers beneath it are in docs/13–16.

## Intentionally absent from this slice

- endogenous labor values propagated through processes (the rate of surplus
  value is therefore still closed-form, not emergent — docs/18);
- absolute (monopoly) rent;
- wage deviations from value: bargaining, the reserve army, mobility;
- credit and bankruptcy;
- capacity depreciation or mothballing;
- individual producer cash accounts and transfer pricing;
- more than four commodities or two regions;
- RimWorld runtime integration.

The next slice should propagate labor values endogenously through the
process graph, turning the frozen `FINDINGS.md` figures into model
quantities.
