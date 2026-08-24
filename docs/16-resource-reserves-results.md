# Resource reserves and differential rent: measured results

This comparison was recorded after implementing the reserve infrastructure
from `docs/15-resource-reserves-design.md`. The old reference describes the
cost floor and buffer-aware investment without finite reserves.

## Headline

Finite resource reserves with grade depletion and differential rent are
implemented and working.

- All 38 tests pass (30 prior + 8 reserve-specific).
- All 53 frozen baseline metrics are exactly unchanged.
- Four-year equilibrium price and inventory paths remain exactly stationary
  for all three commodities in both regions.
- Repeated scenarios produce identical histories.
- All material residuals close to floating-point zero.
- Silver balances close to floating-point zero.
- Reserve depletion equals chemfuel production to floating-point precision.
- The depletion scenario exercises grade transition, cost increase,
  differential rent, and all ledgers close.

Zero of 53 frozen observations move. The reserve infrastructure is invisible
to existing scenarios, exactly as designed.

## Prediction scorecard

### "Existing 53 metrics: zero movement" — **correct**

All 53 metrics unchanged. The 100,000-unit default reserve at the current
operating overhead cost makes reserves invisible when they don't bind.

### "Grade transition raises chemfuel price" — **correct**

Dust Basin's Grade 1 (600 units at cost 1.5333) exhausts at day 100. The
marginal cost jumps to Grade 2 (cost 3.0667). The chemfuel price rises from
2.3000 to 3.3259 over 50 days, settling by day 150.

The settled price of 3.3259 is above the predicted minimum of 3.22 (which
was `marginal_cost × full_utilization_ratio = 3.0667 × 1.05`). The actual
equilibrium is higher because the reference price (2.3) is now below cost
(3.07), so the price formation model must hold the price up through
permanently depleted inventory — Dust Basin's chemfuel inventory settles at
77.85 (65% of target), creating enough upward pressure to maintain the
3.33 price.

This is economically correct: when cheap deposits run out, the old reference
price is obsolete. The market maintains the higher price through scarcity.

### "Downstream price propagation" — **wrong**

Predicted that leaf and yayo prices would rise "with a delay." They did not
move at all. Both remain at exactly their reference prices.

The prediction failed because it overlooked the quantitative impact. The
chemfuel price increase of +1.03 per unit translates to:

- Psychoid farm: +0.05 × 1.03 = +0.051 per leaf (on a base effective cost
  of ~0.12). Ratio drops from 1.44 to 1.42 — still well above the 1.05
  full-utilization threshold.
- Drug lab: +0.2 × 1.03 = +0.206 per yayo (on a base effective cost of
  ~15.66). Ratio drops from 1.34 to 1.32 — still well above threshold.

The chemfuel input share in both downstream products is too small for a 44%
chemfuel price increase to push them into curtailment. A 1.3% increase in
the drug lab's effective cost does not move the needle when the margin is
32%.

This is an important structural finding: **cost-push propagation is
proportional to input share**, and chemfuel's share in the downstream
products is small by design (0.2 per yayo, 0.05 per leaf). Significant
downstream price impact would require either a much larger chemfuel price
increase or a higher chemfuel input share.

### "Differential rent appears" — **correct**

Total differential rent of 1,815.69 silver accumulated over 300 days.

Before day 100 (while both regions extract from their first grade), rent is
minimal — the cost difference between Dust Basin (1.5333) and Green River
(1.5881) is only 0.0548 per unit.

After day 100 (Dust Basin on Grade 2 at 3.0667, Green River still on Grade
1 at 1.5881), the advantage widens to 1.4786 per unit. At 6 chemfuel/day
extraction in Green River, this generates about 8.87 silver/day in
differential rent.

### "Chemfuel arbitrage may activate" — **correct (did not activate)**

The prediction correctly noted the spread (~1.03) would be below standard
freight cost (3.85). No chemfuel was traded between regions. Zero imports
and zero exports of chemfuel in both regions.

## Depletion scenario timeline

| day | Dust marginal cost | Dust chemfuel price | Dust inventory | Green price |
|---:|---:|---:|---:|---:|
| 0 | 1.5333 | 2.3000 | 120.0 | 2.3000 |
| 99 | 1.5333 | 2.3000 | 120.0 | 2.3000 |
| 100 | **3.0667** | 2.3000 | 120.0 | 2.3000 |
| 101 | 3.0667 | 2.3233 | 119.1 | 2.3000 |
| 110 | 3.0667 | 2.9435 | 97.5 | 2.3000 |
| 120 | 3.0667 | 3.2881 | 82.2 | 2.3000 |
| 150 | 3.0667 | 3.3258 | 77.8 | 2.3000 |
| 300 | 3.0667 | **3.3259** | **77.8** | 2.3000 |

The transition is abrupt at day 100 (the cheap grade exhausts) but the price
adjusts smoothly over ~50 days due to the damped price formation. Green
River is entirely unaffected — its price, inventory, and extraction cost
remain at reference throughout.

## Why the chemfuel inventory is permanently displaced

At the new equilibrium, Dust Basin's chemfuel inventory settles at 77.85
(65% of its 120-unit target). This is not a bug — it is the only
self-consistent solution:

1. The price formation formula pushes toward `reference_price × exp(pressure)`.
2. At full inventory (120 units), pressure = 0, desired price = 2.30.
3. At 2.30, the utilization ratio is 2.30/3.07 = 0.75, barely above the
   zero-utilization threshold (0.70). Production is ~14% of capacity.
4. At 14% production, demand exceeds supply, inventory falls further.
5. Equilibrium is where the depleted inventory creates enough upward pressure
   to hold the price at the level that supports full production.

At 77.85 units: coverage_gap = (120 - 77.85)/120 = 0.351, pressure = 1.05
× 0.351 = 0.369, desired = 2.3 × exp(0.369) = 3.326. The price/cost ratio
is 3.326/3.067 = 1.085 > 1.05, so full utilization. Supply equals demand.
Stable.

The permanent inventory displacement reflects the fact that the commodity's
reference price is now below the marginal extraction cost. In the real
economy, this would eventually lead to an updated reference — the "new
normal." The current model's static reference prices are a documented
limitation.

## What the model gained

Three properties that were previously absent:

1. **Finite extraction.** Chemfuel synthesis now draws from a bounded
   regional reserve. A region that extracts enough will exhaust its cheap
   deposits and face rising costs. The reserve constraint limits production
   when the endowment runs out.

2. **Rising marginal cost.** When the cheapest grade depletes, the marginal
   extraction cost jumps to the next grade. The utilization curve responds
   through the existing cost floor mechanism — no new production logic was
   needed. The drug lab curtails not because chemfuel is physically gone, but
   because its price rose above the threshold that makes production
   profitable at the current yayo price.

3. **Differential rent.** The cost advantage of a region with better
   deposits is tracked as a separate quantity. Green River earns 1,815.69
   silver in differential rent over 300 days when Dust Basin moves to its
   expensive grade. Rent is observed, not transferred — there is no
   landowner entity yet.

## Accounting identities

- `reserve_depletion[chemfuel]` = 3,557.85 = `production[chemfuel]` ✓
- All three material residuals = 0.0 ✓
- Cash residual = 0.0 ✓
- No investment spending triggered in this scenario ✓

## Reference decision

The existing 53 baseline metrics are unchanged — no reference rewrite is
needed. The reserve infrastructure is purely additive: it constrains
extraction processes and tracks depletion and rent, but does not alter any
existing production, pricing, or investment path when reserves are large.

The depletion scenario is a new capability, not a replacement for an existing
one.
