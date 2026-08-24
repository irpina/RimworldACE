# Stage 0 economy laboratory

This is the dependency-free, deterministic prototype for the economy mod. It
exists to make the economic rules falsifiable before UI, pawn AI, saves, or
Harmony complicate debugging.

The model is a three-commodity circuit in two regional markets:

```
chemfuel ──┬──> psychoid farm ──> psychoid leaves ──> drug lab ──> yayo
           └────────────────────────────────────────────^
```

Chemfuel is consumed by two producers, so contention for a scarce shared input
is exercised; leaves sit between two stages, so a shortage has to travel. It
supports:

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
- explicit material and silver ledgers separating final from productive
  consumption, with investment spending and reserve depletion tracked;
- fixed Labor Content value beside the market price.

Per-unit ratios and reference prices are read from RimWorld's own defs. The
modelling choices — mass apportionment for joint products, proportional input
rationing, simultaneous production, derived demand — are recorded in
`docs/08-accounted-input-design.md`. The cost floor and investment decisions
are in `docs/13-cost-floor-and-investment-design.md`. The resource reserve and
rent decisions are in `docs/15-resource-reserves-design.md`. Read all three
before changing them; each was chosen deliberately and several have defensible
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

`behavior_baseline.json` retains the original thirteen yayo metrics and also
observes upstream chemfuel and psychoid leaves during the glut and producer-loss
shocks. For each upstream commodity it freezes post-shock price and inventory
extrema (including their days). The genuinely stationary glut path also records
its settled price and stock; the still-moving producer-loss path labels its last
observation as terminal rather than implying equilibrium. The reporter remains
observational; the invariant tests protect correctness.

The current reference describes the cost floor and buffer-aware investment
model. Its design and results are in `docs/13-cost-floor-and-investment-design.md`
and `docs/14-cost-floor-and-investment-results.md`. The resource reserve addition
did not change any existing metric; its design and results are in
`docs/15-resource-reserves-design.md` and `docs/16-resource-reserves-results.md`.

## Intentionally absent from this slice

- endogenous labor values propagated through processes;
- absolute (monopoly) rent;
- labor supply, wages, and the subsistence basket;
- credit and bankruptcy;
- capacity depreciation or mothballing;
- individual producer cash accounts and transfer pricing;
- more than three commodities or two regions;
- RimWorld runtime integration.

The next slice should add the local subsistence basket and hired-worker
contracts.
