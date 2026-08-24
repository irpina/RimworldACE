# Labor-power, the subsistence basket, and the surplus ledger: decisions

These decisions are recorded **before** implementation, in the same spirit as
`docs/08` and `docs/11`: every choice below is a modelling convention with no
oracle to settle it, so it has to be declared, argued, and exposed rather than
discovered in the diff.

This is the session where the model stops being infrastructure and starts
being about its thesis. Everything so far — material floors, cost floors,
capital costs, reserves, rent — built a closed reproduction circuit. This
session introduces the wage relation: the distinction between **labor** (the
activity, a cost coefficient) and **labor-power** (the commodity a wage buys,
whose value is its cost of reproduction). Surplus value is only computable
once the two are separate. Collapsing them makes surplus definitionally zero.

Per the standing rule, labor value, market price, surplus value, and rent
remain four distinct ledger quantities, and money profit is not surplus value.

---

## 1. The subsistence commodity: meals

**Decision: add a fourth real commodity, `meals`, with its own production
process, rather than an abstract basket priced off existing goods.**

A real commodity keeps the reproduction of labor-power inside the material
circuit, which is the entire point: workers eat produced goods, the goods
consume labor to produce, and that labor must itself be reproduced. An
abstract basket would price labor-power off commodities nobody makes, turning
the wage into an exogenous index — exactly the collapse this session exists to
avoid.

The commodity is grounded in RimWorld's own data, like the other three:

| quantity | value | source |
|---|---|---|
| meal reference price | 15.0 | `MealSimple` `MarketValue` |
| meal embodied labor | 305 ticks | `out/embodied_labor.csv` (closed analysis) |
| meal labor value (display scale) | 4.829167 | 305 × (11.4 / 720), same scale as the others |
| meal mass | 0.44 | `Mass` stat (recorded; unused — single-output process) |

The production process is **provisioning** — aggregated farming plus cooking.
Its material inputs sit outside the modelled boundary, exactly as chemfuel's
organic feedstock does: the boundary has to stop somewhere, and the labor of
the excluded stages is already inside the 305 embodied ticks the closed
analysis measured. Provisioning therefore has `inputs={}` and
`direct_labor=305`.

**Rejected: meals consuming chemfuel.** The stylized chemfuel link exists
because the circuit needed a commodity consumed by more than one producer;
that structural purpose is already served. Wiring meals into chemfuel would
couple the subsistence sector to the depletion mechanics for no design reason
and would disturb the seeded chemfuel capacity, confounding this session's
deltas.

The material and silver ledgers extend to meals automatically: the commodity
enters `circuit_commodities`, the process enters `known_processes`, and every
existing invariant (`commodity_balances`, `cash_balance`) covers it with no
special case.

## 2. The wage

**Decision: the wage equals the current regional cost of the subsistence
basket — workers are paid at the value of labor-power.**

The basket is `{meals: 2.0}` per worker-day. RimWorld pawns consume about 1.6
nutrition per day against a 0.9-nutrition simple meal (≈1.78 meals); 2.0 is
the folk-standard two-meals-a-day schedule, rounded to a value that is exact
in binary floating point (see §7 — this is a calibration convenience,
documented as such, not a data claim).

A worker-day is **24,000 work-ticks** (`ticks_per_worker_day`): a 60,000-tick
day, sixteen waking hours, and a working share of them. This is a parameter
with a defensible reading, not a measured constant; the rate of surplus value
is linear in it, which §5 is explicit about.

At reference prices the wage is therefore 2.0 × 15 = **30 silver per
worker-day**, or 0.00125 silver per work-tick. For comparison, vanilla
RimWorld's own price formula embeds 0.0036 silver per work-tick of
*fabrication* value added — the model's workers are paid well below the value
their labor adds, which is precisely the surplus the ledger will now measure.

**The wage is dynamic.** It is recomputed daily from current regional prices:
if meal prices rise, the wage bill rises, every producer's effective unit cost
rises through the cost-floor machinery, and production curtails on margin.
This is the one behavioral channel wages open, and it flows entirely through
existing machinery. A wage-price spiral is possible in principle (meal price →
wage → meal producer's own cost → meal supply); it is damped by the meal
producer's ~44% margin at reference, and the subsistence-shock scenario
exercises it deliberately.

Deviations of the wage from the value of labor-power — bargaining, the reserve
army, wages above value in booms — are the interesting dynamics and are
deliberately **not** built. The wage is a single rule (basket at current
prices) with the basket exposed as a parameter, so later sessions can move
the wage off value without re-architecting.

### The wage circuit in silver

This is the first time silver cycles rather than flows one way:

```
regional pool ──wage bill──> worker cash pool ──basket purchase──> regional pool
```

Each region gains a `worker_cash` pool. Daily:

1. **Wages are paid during production**: `wage_bill = worker_days × wage_rate`,
   deducted from `region.cash`, credited to `region.worker_cash`. Wages are
   paid on labor actually performed (actual runs, after all rationing).
2. **Workers spend with a one-day lag**: the worker-days earned today buy the
   basket tomorrow (paid at day's end, bread bought in the morning). Purchases
   draw down regional inventory, are booked as **final consumption**, and the
   payment returns from `worker_cash` to `region.cash`.
3. Purchases are capped by inventory and by worker cash, scaled
   proportionally when either binds. A shortfall registers as unmet demand for
   the basket good (price pressure) and accumulates in a `basket_shortfall`
   observation — labor-power paid below its reproduction cost is a state the
   model must be able to *see*, even though nothing yet acts on it.

Worker demand for the basket is **price-inelastic** (subsistence), unlike the
elastic final demand for yayo. Workers buy the basket their worker-days
command, cash permitting — they do not respond to meal prices by eating less
except through the cash constraint.

Workers are seeded with a cash buffer (`worker_initial_cash_days`, default 30
days of the reference basket) so that floating-point drift in the pool never
spuriously triggers the cash constraint at equilibrium.

The silver identity extends: regional cash + worker cash + transport +
investment − initial (including initial worker cash) must close to
floating-point zero. The wage/purchase legs are exact transfers of the same
float amount, so conservation holds by construction; the tests assert it.

**Loud refusal:** if a region's cash cannot cover the day's wage bill, the
model raises rather than clamping employment or going negative. Credit and
bankruptcy are explicitly absent; a scenario that bankrupts a region must say
so by failing, not by silently not paying workers.

## 3. Labor supply

**Decision: a fixed regional labor pool, `labor_pool` worker-days per day,
with pro-rata rationing when demand exceeds it.**

The demand side already exists: `Process.direct_labor` per run. Daily labor
demand is planned runs × direct labor, summed over producers. When it exceeds
the pool, all producers' planned runs scale by the same factor
(`pool / demand`) — proportional, order-independent, no threshold, the same
pattern as reserve rationing. When the pool does not bind, the step is an
exact no-op (skipped, not multiplied by 1.0).

The default pool (1.0 worker-day/day per region) is roughly 3× equilibrium
employment (≈0.314 worker-days/day), so it never binds in any existing
scenario. Unemployment, mobility, and the reserve army are non-goals; the
pool exists so that labor is a real constraint the model *can* express, and a
test exercises the binding case.

## 4. What happens to the old unit_cost

**Decision: the wage bill is additive to effective unit cost. The existing
operating overheads are reinterpreted as non-labor overhead and are not
reduced.**

This is the load-bearing choice, so the alternative is worked through
numerically rather than waved at.

The economically pure alternative — split the wage *out of* the existing
overhead, on the theory that the old `unit_cost` implicitly contained labor —
is infeasible with this calibration:

- The drug lab's operating overhead is **zero** (docs/13: its entire prior
  14.0 was consumed by the 15.66 input cost). Any positive wage exceeds it.
  Under the mandated refuse-loudly rule, a subtraction design fails at
  construction, always.
- The overheads are mutually inconsistent with the labor data. Chemfuel:
  1.533 overhead over 25 ticks (0.061 silver/tick available). Leaves: 1.152
  over 46.2 (0.025). Yayo: 0 over 350 (0.000). No uniform wage rate can be
  split out of all three; the only wage every overhead covers is zero.

The additive reading is also the economically honest one here: **Stage 0
labor has been unwaged until now.** The fat margins every producer earned
(50% at reference) implicitly contained the unpaid wage fund. Making
labor-power a paid commodity moves that portion from measured margin into
cost — measured money profit falls by exactly the wage bill, which is not a
distortion but the point: surplus value was previously appearing entirely as
profit because labor-power was free.

**The loud check moves to where the hazard actually is.** The danger of an
additive wage is not a negative overhead — it is a producer silently pushed
below full utilization at reference prices, which would quietly break the
stationary equilibrium. Scenario seeding therefore asserts, at construction,
that every producer's price/effective-cost ratio at reference (including the
wage at the reference basket cost) remains at or above
`full_utilization_price_ratio`, and raises otherwise. The margins after the
wage:

| producer (Dust) | effective cost before | wage/unit | after | ratio at ref |
|---|---:|---:|---:|---:|
| drug lab | 15.660 | 0.4375 | 16.098 | 1.305 |
| psychoid farm | 1.267 | 0.0578 | 1.324 | 1.434 |
| chemfuel refinery | 1.533 | 0.0313 | 1.565 | 1.470 |
| provisioners | 10.000 | 0.3813 | 10.381 | 1.445 |

All comfortably above 1.05. River margins are slightly tighter and also pass.

Mechanically: each producer gains a `wage_cost_per_unit`, updated daily by the
economy from `labor_per_unit × wage_per_tick` (reusing the joint-product
apportionment machinery), exactly as extraction unit costs are updated daily
from the marginal grade. `effective_unit_cost` adds it. Bare-model tests that
configure no basket get a zero wage and are bit-for-bit unaffected.

## 5. The surplus ledger

**Decision: the surplus ledger is denominated in labor time (work-ticks),
kept per region, and is purely observational. The wage bill in silver is
recorded beside it, not mixed into it.**

Per region, cumulative:

- **living labor** — work-ticks actually performed (actual runs × direct
  labor);
- **necessary labor** — worker-days × the basket's labor value in ticks
  (basket quantities × commodity labor values, converted through
  `labor_value_per_tick` = 11.4/720, the scale the display values already
  use). With the meals basket: 2.0 × 305 = **610 ticks per worker-day**;
- **surplus labor** — living minus necessary;
- **wage bill** — silver actually paid (money form of variable capital);
- **worker spending** and **basket shortfall** — silver spent, and basket
  units the workers could not obtain.

The rate of surplus value is `s/v = surplus / necessary`. Nothing in the model
reads these quantities back; the one behavioral channel remains the wage in
effective cost (§4). Realization already exists through the market: a
commodity's surplus labor is realized only when it sells, and the ledger keeps
those facts separate — money profit during a glut can fall while surplus
labor performed is unchanged.

### Is s/v free or emergent? (answered in advance, verified in results)

At this stage the labor-time rate of surplus value is **determined in closed
form, not emergent**:

```
s/v = (ticks_per_worker_day − basket_labor_ticks) / basket_labor_ticks
    = (24000 − 2.0 × 305) / (2.0 × 305)
    = 23390 / 610
    ≈ 38.34
```

The chain: `ticks_per_worker_day` (a parameter), the basket quantity (a
parameter), and the meal's embodied labor (a datum from the closed analysis).
It is a free parameter dressed in data — settable by two coefficients, with
the third leg pinned by RimWorld's defs. The honest report is exactly that,
plus what would make it emergent later: endogenous labor values (meal
embodied labor computed from the process graph instead of frozen), a wage
that deviates from the basket (bargaining), and an endogenous basket.

The **money-side** ratio is a different quantity and *is* path-dependent: the
wage bill varies with meal prices while necessary labor in ticks does not.
The two must never be presented as one number.

The magnitude deserves its caveat now, before anyone anchors on it: 38 is
enormous because the basket is deliberately minimal. A RimWorld pawn's real
reproduction cost includes shelter, apparel, medicine, and recreation; a
meals-only basket understates the value of labor-power and so overstates
s/v. Extending the basket mechanically lowers it. The number to trust is the
structure, not the level.

## 6. Timing: wages today, bread tomorrow

**Decision: worker basket demand lags employment by one day.**

Today's plan targets a known constant (yesterday's earned worker-days ×
basket), workers spend today what they earned yesterday, and today's earnings
are stored for tomorrow. Beyond the payday reading, the lag is what keeps the
planning fixed point unchanged: same-day spending would couple every
producer's labor into the meal order inside the plan iteration, adding a new
self-referential loop whose truncated convergence (the existing 1e-9
tolerance) would leak a daily drift into meal inventory and destroy the exact
equilibrium. With the lag, the meal order is a constant within the day, the
legacy plan arithmetic is bit-for-bit untouched, and propagation keeps the
established one-day-per-stage rhythm (docs/08).

## 7. Exact stationarity: the floating-point engineering

The equilibrium scenario must still report a price range of **exactly 0** —
not 1e-13, zero. The existing model achieves this because its calibration
lands on binary-exact daily flows (10.0 yayo, 80.0 leaves, 6.0 chemfuel
against inventories of 200/1600/120: every add and subtract is exact). Worker
consumption is computed from labor sums like 80 × 46.2 that are *not* exact,
and a full-mantissa daily flow added to and subtracted from a ~28-unit
inventory rounds — a drift of ~1e-15/day that compounds into a visible price
tick within the four-year window. Three measures make the circuit exact:

1. **Employment is quantized** to a grid of 2^-20 worker-days (≈0.09 seconds
   of work): `worker_days = floor(raw × 2^20) / 2^20`, computed with exact
   power-of-two scaling. The day's basket demand then carries at most ~20
   significant mantissa bits, so adding it to and removing it from a
   double-precision inventory is **exact**, and a stationary day returns the
   inventory to the identical float. This is numeric quantization in the
   units of the instrument, documented as such — not an economic threshold:
   the response surface steps at one part in a million of a worker-day,
   far below anything any control reads.
2. **Power-of-two calibration where the model multiplies**: basket quantity
   2.0, meal capacity 1.0/day, labor pool 1.0. The plan's pro-rata factor for
   meals is then `demand / 1.0` and the meal producer's runs are
   `1.0 × factor` — both exact, so planned meal output equals worker demand
   to the bit.
3. **Seeded at the quantized fixed point**: the seeding solves
   `wd = Q((L_legacy + basket_labor × wd × E) / tpd)` by iterating the exact
   runtime float map until it repeats **exactly**, asserts convergence within
   256 iterations (the map's contraction is ≈0.025, so a persistent 2-cycle
   or non-repeat is a calibration failure and raises loudly), and stores the
   result as day-zero earned worker-days. Day one then reproduces it
   identically.

Rejected alternatives: loosening the exact-zero check (forbidden by the
brief); netting all inventory deltas into one application per day (would
change the float path of every existing scenario and disturb the frozen
metrics for a purely numerical reason); recalibrating the legacy labor data
to binary-nice values (tunes closed data to the instrument).

If, despite this, the equilibrium test shows a nonzero range, the session
stops and reports per the brief rather than weakening the check.

## 8. Interactions with existing mechanisms

- **Cost floor**: the wage is one more term in effective unit cost; the
  utilization curve needs no change.
- **Demand-led planning**: worker basket demand joins intended outflow as a
  constant (lagged); inventory targets and price pressure for meals scale by
  a worker component in throughput demand (full-capacity labor × basket),
  the same full-capacity convention the derived-input component uses.
- **Investment**: entrants' margin tests automatically see wage costs;
  provisioning capacity can be rebuilt after destruction through the
  existing machinery (`known_processes` covers meals).
- **Arbitrage**: meals can in principle move between regions; at reference
  the spread is zero and freight is 3.85, so no route activates in existing
  scenarios.
- **Reserves and rent**: untouched. Rent remains a separate ledger quantity;
  nothing about wages enters it.

## 9. Non-goals (from the brief, restated as commitments)

No wage bargaining, worker mood, mobility, or reserve army. No unemployment
dynamics beyond the pool arithmetic. No worker organization. No endogenous
SNLT updating. No RimWorld runtime work. No sensitivity re-run.

## 10. New parameters (all through ScenarioParameters)

| parameter | default | meaning |
|---|---|---|
| `meal_reference_price` | 15.0 | `MealSimple` MarketValue |
| `meal_direct_labor` | 305.0 | embodied ticks (closed analysis) |
| `meal_labor_value` | 4.829167 | display scale, 305 × 11.4/720 |
| `meal_mass` | 0.44 | Mass stat (recorded, unused) |
| `meal_capacity_per_day` | 1.0 | provisioning capacity per region |
| `meals_per_worker_day` | 2.0 | the subsistence basket |
| `ticks_per_worker_day` | 24000.0 | the working day |
| `labor_pool_worker_days` | 1.0 | regional labor supply per day |
| `worker_initial_cash_days` | 30.0 | worker cash buffer at seeding |
| `labor_value_per_tick` | 11.4/720 | display-scale conversion |
| `employment_quantum` | 2^-20 | worker-day grid (numeric, §7) |

## 11. Predictions, recorded before implementation

Derived quantities at equilibrium (both regions):

- employment ≈ **0.3141 worker-days/day** (7346/23390, then quantized);
- wage bill ≈ **9.42 silver/day**, exactly returned through meal purchases;
- meal output = worker demand ≈ **0.628 meals/day**;
- rate of surplus value **s/v ≈ 38.34**, identical in both regions,
  constant over time at equilibrium.

Frozen-metric movements (53 metrics):

1. **Equilibrium (2): zero movement.** Price range exactly 0 for all four
   commodities in both regions — engineered in §7, asserted at seeding.
2. **Glut local trough: up slightly** (shallower), from 14.3565 to roughly
   **14.36–14.38**. The drug lab's full-utilization threshold price rises
   from 16.44 to 16.90 (+2.8%), so cost curtailment starts earlier in the
   price fall. The prior cost-floor session moved the trough +0.02 for a
   +12% threshold shift; +2.8% should move it well under +0.01, possibly
   invisible at six decimals. Trough day 66 ± 2. A second-order easing
   (employment falls → meal price sags ~1% → wage sags → costs sag) works
   the other way and is smaller still.
3. **Glut distant trough, recovery days, arbitrage volume: unchanged**
   (20.4644; 9 days; 11 units). The spread path barely moves.
4. **Glut upstream extrema: remain degenerate** (reference price on day 61,
   stocks at buffer). The demand-led plan, not the wage, is what holds
   upstream stationary through the glut.
5. **Producer-loss peak: essentially unchanged** (38.6303 ± 0.1, day 119
   ± 2). The surviving labs run at full utilization regardless (price far
   above cost), and investment timing is quantized coarsely enough (15-day
   interval, margin ~0.86 vs threshold 0.18) that entry lands on the same
   days.
6. **Producer-loss leaf trough: up slightly** from 0.6934 (the farm's
   zero-utilization price rises 0.887 → 0.927, so farms idle marginally
   earlier in the crash); day 70 ± 2. Chemfuel trough 1.9190 ± 0.01.
7. **Producer-loss terminals (day-210 transients): small drifts, ≤ 1%**,
   in whichever direction the slightly earlier upstream idling tips the
   still-converging buffer rebuild.
8. **New, not moved: meal metrics and the surplus ledger.** To be frozen in
   their own commit as newly observed quantities, not changed behavior.
   Candidates: equilibrium employment, wage rate, s/v, meal settlement
   price/stock, and the glut employment dip.

The riskiest prediction is (1); it is engineered rather than hoped for, and
the session stops if it fails. The vaguest is (7), for the reason docs/14
already recorded: day-210 terminals are transients of a ~460-day recovery.

## 12. Implementation order

1. Model: meals-agnostic wage machinery (worker cash, basket, labor pool,
   quantization, surplus ledger) with all defaults inert — bare tests
   bit-identical.
2. Scenarios: the meals commodity, provisioning process and producers, basket
   configuration, quantized-fixed-point seeding, seeding assertions.
3. Tests: wage-circuit closure, exact equilibrium for four commodities,
   surplus identities, labor-pool rationing, subsistence shock, loud-failure
   cases.
4. Subsistence-shock scenario (`subsistence-shock`): destroy most of one
   region's provisioning capacity; watch meal price, the wage, and every
   producer's cost rise together — the wage-push channel, exercised.
5. Baseline: record deltas against these predictions; reference rewrite and
   new-metric freeze in separate commits.
