# Worker mobility: results

Measured against `docs/106`'s eight numbered predictions. **All eight
hold.** This is the first document in this series where nothing was
refuted, which is itself worth a caveat: the rule is small, and three of
the eight predictions are arithmetic invariants of code I wrote to have
them. The two that carry the economics — 6 and 7 — are the ones to
read.

## 1. What was built

`Economy._migrate`, called from `step()` immediately after `self.day +=
1` and therefore before `_produce` and before `_bargain` reads the
employment rate whose denominator it changes. Each region's *pull* is
`(wage − mean wage) ÷ mean wage`; negative pulls send
`worker_mobility_strength × (−pull) × labor_pool`, capped at
`labor_pool − worker_days_earned`; positive pulls receive in proportion,
with the last recipient taking the remainder so the total is conserved
exactly. Regions with an infinite pool are skipped; region order is
sorted name order.

`worker_mobility_strength` defaults to `0.0` and the method returns
before touching anything at zero. A new ledger bucket,
`labor_migrated`, carries each region's signed net movement; it is
observational and nothing reads it back.

Measurement strength throughout is `0.05` — five percent of the pool per
unit of fractional wage shortfall per day. It is a chosen number, not a
calibrated one.

## 2. The predictions

| # | Prediction | Result |
|---|---|---|
| 1 | Inert by default, 322 metrics | **holds** — no nonzero delta |
| 2 | Inert at the symmetric equilibrium | **holds** — bit-identical |
| 3 | Labour conserved within 1e-12 | **holds** — drift 1.78e-15 |
| 4 | No employment rate exceeds 1 | **holds** — max 0.3657 |
| 5 | Labour flows toward the boom | **holds** — 1.1101 vs 0.8899 |
| 6 | Mobility damps the peak premium | **holds** — 0.0425 vs 0.0784 |
| 7 | The wage gap closes | **holds** — 4.3e-14 vs 5.101 |
| 8 | The bare wage share identity holds | **holds** to 6 places |

### Prediction 2, the honesty check

`docs/106` said this would be measured rather than assumed, given the
previous four documents. It was: `equilibrium(600)` with the rule on has
the same prices dict, the same pools and the same wage rates as with it
off, compared by `==` on floats rather than by tolerance. The two
regions are seeded identically, so both wages are the same number, the
mean is that number, both pulls are exactly `0.0`, and the send loop's
`if pull >= 0.0: continue` takes every branch. `labor_migrated` is
empty — not small, empty.

### Predictions 6 and 7, the economics

In `demand_boom` with bargaining, Dust Basin's final demand for yayo
rises 25%, employment climbs, and the reserve-army rule lifts the wage.
With the pool frozen, that premium peaks at **7.84%** and Dust Basin
ends the run paying **47.07** against Green River's **41.97** — a gap of
**5.10 silver per worker-day that nothing in the model could close**,
because nobody could move to collect it.

With mobility on, the peak premium is **4.25%**, a **46% reduction**,
and the terminal gap is **4.3e-14** — equalized to floating point.
0.1101 worker-days, 11% of Green River's pool, have moved to Dust Basin
by the end of the run.

This is the classical result, and getting it is the point: the boom's
wage signal is now paid for in people rather than absorbed entirely in
price. It is also the answer to `docs/97`'s A5. The reserve army is
still not *created* endogenously — total labour is conserved by
prediction 3, so nobody enters or leaves the workforce, only the region
— but it is no longer a frozen parameter either.

### Prediction 4, and what the cap actually binds on

The maximum employment rate observed over 300 stepped days is 0.3657,
well under the cap. So prediction 4 holds but is not *tested* by this
scenario: the cap never came near binding, because the laboratory
employs roughly a third of its pool. The cap is there for the case where
it would matter, and this run does not demonstrate that it works — only
that it does no harm. A scenario that drives employment toward the pool
would be the real test, and it is not in this slice.

The same caveat applies to prediction 3 in a weaker form: conservation
is exact by construction (the last recipient takes the remainder), so
measuring 1.78e-15 confirms the code does what it says rather than
discovering anything.

## 3. What this does not do

It is not the colony as first mover. `docs/50` §5 wants a settlement
that hires pawns; this moves an abstract pool between two laboratory
regions. The Stage 1 rule will be built on this, but a pawn arriving at
a settlement is a gameplay-layer concern.

It is not entry into or exit from the workforce. Wright's actors leave
employment but never the economy, and neither do these — which means
the *unemployment* the lab reports is still bounded by a total labour
supply that no rule sets.

With A5 measured, `docs/50` §5's critical path has no remaining
divergence from `docs/97`'s audit. The RimWorld mod implementation is
the next piece of work.
