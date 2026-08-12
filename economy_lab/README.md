# Stage 0 economy laboratory

This is the dependency-free, deterministic prototype for the economy mod. It
exists to make the economic rules falsifiable before UI, pawn AI, saves, or
Harmony complicate debugging.

The first slice models one commodity (`yayo`) in two regional markets:

- local production, consumption, inventory, prices, and silver;
- a costly route with finite daily capacity and delivery time;
- profitable planetary arbitrage when a regional spread covers freight;
- destruction of productive capacity;
- delayed investment in replacement capacity;
- explicit material and cash ledgers;
- fixed Labor Content value beside the market price.

Run all example scenarios:

```text
python -m economy_lab all
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
6. Every scenario conserves commodity quantities and silver exactly within
   floating-point tolerance.

These are provisional gameplay targets, not empirical elasticity claims.

## Intentionally absent from this slice

- production inputs and joint products;
- resource reserves, grades, and rent;
- labor supply, wages, and the subsistence basket;
- capital-goods and construction costs for new capacity;
- credit and bankruptcy;
- more than one commodity or two regions;
- RimWorld runtime integration.

Production and capacity entry are declared ledger sources for now. The next
slice must replace the single-output production stub with input-output
processes, then add finite extraction reserves before claiming a fully closed
material economy.
