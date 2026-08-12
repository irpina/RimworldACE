# Stage 0: regional market laboratory

The first executable economy prototype lives in `economy_lab/`. It is kept
separate from RimWorld so market behavior can be tested deterministically
before runtime patches, saves, UI, and pawn AI are involved.

The initial vertical slice is deliberately narrow: one commodity (`yayo`), two
regional markets, and one expensive planetary route. It already establishes
the contracts later systems must preserve:

- prices form locally from inventories and unmet effective demand;
- planetary trade occurs only when the spread covers freight and risk;
- routes have daily capacity and delivery time;
- arbitrage transfers conserved stock and pushes prices toward convergence;
- productive capacity persists and takes time to replace after destruction;
- market price and fixed labor value are separate fields;
- commodity and silver ledgers close after every scenario.

The acceptance tests use ratios of regional flows, not arbitrary item counts.
They cover equilibrium, deterministic replay, a drug glut, regional isolation,
planetary arbitrage, destruction of 60% of supply, and delayed entry.

This slice does **not** yet close the full production graph. Production is an
explicit ledger source and capacity investment has no capital-goods cost. The
next slice should introduce input-output processes. Finite resource reserves
and rent follow once production consumes accounted inputs.
