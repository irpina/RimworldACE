# Competitive transmission from cost to price: decisions

Recorded **before** implementation, in the style of `docs/08`, `docs/11`,
`docs/15`, `docs/17`, and `docs/19`.

`docs/20` ended with the sharpest gap the model has: a technique that halves
the living labor in a wage good lowers its labor value by 12.46% and its
price by **exactly nothing**. Two mechanisms are missing, and they are
different mechanisms:

1. **Price formation never reads cost.** The anchor is
   `Commodity.reference_price`, a static figure imported from RimWorld's
   `MarketValue`. Inventory coverage and unmet demand push the price around
   that anchor, but no change in what production costs can move it.
2. **Nothing shifts custom to the cheaper producer.** The demand-led plan
   rations every producer of a commodity by the same factor, so a producer
   with half the labor bill gets exactly the same share of the order book as
   one with twice its cost.

Without the first, cost cannot reach price at all. Without the second, a cost
advantage never spreads through the sector. This session adds both, measured
separately, and defers exit.

---

## 1. What the numbers say before we start

Two measurements taken from the current model, because they decide how much
this session can be expected to achieve.

**Effective unit cost decomposes badly for our purposes.** At equilibrium:

| producer (Dust Basin) | overhead | inputs | wages | total | wage share |
|---|---:|---:|---:|---:|---:|
| chemfuel refinery | 1.5333 | 0 | 0.0312 | 1.5646 | 2.0% |
| psychoid fields | 1.1517 | 0.1150 | 0.0578 | 1.3244 | 4.4% |
| provisioners | 10.0000 | 0 | 0.3813 | 10.3812 | 3.7% |
| drug lab | 0 | 15.6600 | 0.4375 | 16.0975 | 2.7% |

Wages are **2–4% of money cost**. Everything else is either a purchased input
or `unit_cost` — the operating overhead, which `docs/13` derived as a
calibration residual (`total_unit_cost − input_costs_at_reference`) chosen so
that every producer runs at full utilization at reference prices. That
residual has no economic interpretation: it is "everything not otherwise
modelled," and for meals and chemfuel it is over 95% of cost.

The consequence is stated here in advance rather than discovered later:
**a labor-saving innovation cannot move money prices much in this
calibration, however good the transmission mechanism is.** Halving the living
labor in a meal cuts its money cost by 1.8%, not by 12.46%. Building perfect
transmission will not change that, and tuning the overhead until the number
looks better would be fitting the instrument to a forecast.

**The depletion scenario carries an artifact worth removing.** With the cheap
grade exhausted, Dust Basin's chemfuel cost doubles to 3.098 and its
inventory settles permanently at 76.6 units — **63.8% of its 120-unit
target**. `docs/16` explained why: the only way a reference-anchored price can
sit above a doubled cost is for the coverage gap to hold it there, so the
model starves the buffer to keep the price up. A cost-aware anchor should
raise the price because cost rose, and let the inventory return toward target.

## 2. Part A — the price anchor reads cost

**Decision: the anchor moves proportionally with the sector's cost relative
to its seeded cost, blended against the authored reference price by a
competitive intensity.**

```
cost_ratio(region, c) = current_sector_cost(region, c) / seed_sector_cost(region, c)
anchor(region, c)     = reference_price(c) * (1 + kappa * (cost_ratio - 1))
desired               = clamp(anchor * exp(pressure))
```

`pressure` is unchanged — the same inventory coverage and unmet-demand terms
as before. Only the anchor they push against becomes cost-aware.

**Why a ratio against a seeded cost, and not cost times a markup.** A markup
form (`anchor = cost * markup`) needs a markup per commodity per region,
because the current calibration has each producer earning a different profit
rate on cost: 30.5% on yayo, 43.5% on leaves, 47.0% on chemfuel, 44.5% on
meals, with Green River's figures different again. Writing those down as
eight authored constants would smuggle the entire existing price structure in
as parameters. The ratio form carries exactly the same information — it *is*
a per-region, per-commodity markup — but derives it once from the seeded
state instead of asking anyone to justify eight numbers, and it makes the
economic claim explicit and modest: **prices move with cost, from wherever
they were calibrated to start.** Equalizing profit rates across sectors, which
is what a classical price of production would require, is a separate and
larger question and is not attempted here.

**Which cost: the average, not the marginal.** The sector cost is the
output-weighted average effective unit cost across active producers of that
commodity in that region — the same output weighting `docs/19` adopted for
socially necessary labor, for the same reason, and computed from the same
realized runs.

This is a deliberate reading of the project's standing commitment that
"labor value reference: average socially necessary conditions; price/rent
reference: marginal supply conditions." That commitment is about **rent**,
and rent is where the marginal producer belongs: it is already implemented
that way, with differential rent computed against the most expensive active
extractor (`docs/15`). For manufactured goods with no binding natural
scarcity, the classical anchor is the average condition plus a profit rate,
not the worst producer in the sector. Using marginal cost here would also
make Part A nearly inert on its own — the marginal producer is by definition
the one an innovation did *not* improve — which would hide the transmission
this session is trying to measure.

**Fallbacks, matching `docs/19` section 4.** Seeded from capacity weights at
construction, since nothing has been produced. Output weights thereafter.
When no producer of a commodity is active in a region, the last ratio is held
rather than recomputed, for the same reason value is held: cost describes
conditions of production, which do not vanish because nobody produced today.

**The feedback loop, and why it is stable.** Effective cost includes input
prices, so the anchor now depends on other prices. That circularity is not an
accident to be engineered away — it is what a price of production *is*, in
dynamic form. What matters is whether it converges. The loop gains:

- *Downstream chain* (chemfuel → leaves → yayo) is acyclic, so it propagates
  and settles rather than circulating. Leaves are 94% of yayo's cost, so a
  10% leaf price move shifts the yayo anchor by 10% × 0.94 × kappa ≈ 4.7% at
  kappa = 0.5.
- *The one real cycle* is meals → wage → meal cost → meal anchor → meal
  price. Its gain is the wage share of meal cost times kappa: 0.037 × 0.5 =
  **0.018**. Two orders of magnitude inside the unit circle.

Stability is therefore expected rather than hoped for, but it is a property
to verify, not assert: every scenario is checked for divergence, and the
existing minimum and maximum price clamps stay in place as a backstop.

**Exact stationarity.** `1 + kappa * (cost_ratio − 1)` is exactly `1.0` when
`cost_ratio` is exactly `1.0`, for any kappa, because `1.0 − 1.0` is exactly
zero in binary floating point and `1.0 + 0.0` is exactly one. At equilibrium
prices do not move, so costs recompute to the identical float, so the ratio
is exactly one and the anchor is exactly `reference_price`. The four-year
exact-zero price range is preserved by construction, not by calibration. The
blend is written in this form precisely for that reason; the algebraically
equivalent `(1 − kappa) + kappa * ratio` is *not* exactly one for every
kappa.

`kappa` is `competitive_price_intensity`, default **0.5**. A conservative
default is the house style, and it makes the mechanism's strength a measured
quantity rather than an all-or-nothing switch. `kappa = 0` reproduces today's
model bit-for-bit; `kappa = 1` makes the anchor purely cost-driven. Both are
reachable from `ScenarioParameters`.

### Rejected alternatives for Part A

**Replace the reference anchor outright (kappa fixed at 1).** Tempting,
because an anchor that half-believes an authored RimWorld constant is
theoretically muddy. Rejected as a *default* because it removes the ability
to measure transmission strength — with kappa exposed, "how much of a cost
change reaches price" becomes an experiment rather than an assumption.

**Let the utilization curve do it.** Producers already curtail when price
falls toward cost, so cheaper producers already curtail later. That is a
supply response to a price, not a transmission of cost into price: it moves
quantity while leaving the anchor untouched, which is exactly the situation
`docs/20` recorded.

**Marginal-cost anchoring.** Covered above: right for rent, wrong for
manufactured goods, and nearly inert for the innovation case.

## 3. Part B — the order book goes to the cheaper producer

**Decision: allocate a commodity's requested output across its producers by
capacity-and-cost weights, with a constant elasticity, capped by each
producer's own price-limited output.**

Today `_planned_runs` computes one factor per commodity and applies it to
every producer of that commodity. Instead:

```
weight_i  = desired_output_i * (cost_i / cheapest_cost)^(-epsilon)
share_i   = requested_output * weight_i / sum(weights)
runs_i    = min(share_i, desired_output_i) / units_per_run
```

with residual from capped producers redistributed among the uncapped ones
until nothing is left to place or every producer is at its own ceiling. The
redistribution is a deterministic water-filling loop, iterated in sorted
producer order, so it cannot depend on list order.

**`epsilon = 0` is a bit-exact no-op.** With zero elasticity every weight
collapses to `desired_output_i`, the shares become proportional to desired
output, and the arithmetic reduces to today's uniform factor exactly. That
property is what makes the change measurable: it can be switched on and off
against the same reference without any other difference.

**Why an elasticity and not "cheapest first".** Winner-take-all allocation is
a threshold-and-switch rule, which this project has rejected four times for
the same reason (`docs/08` on input rationing, `docs/11` on inventory
control, `docs/13` on investment, `docs/17` on wages): a discontinuity in an
allocation rule manufactures limit cycles that look like economic results.
Two producers whose costs differ by a hair would flip the entire order book
between them from one day to the next. A constant elasticity moves share
continuously — a small cost advantage wins a small amount of extra custom —
and `epsilon` names how sharply buyers discriminate.

**What Part B does not do.** It does not remove anyone. A dear producer that
loses share keeps its capacity, keeps inflating throughput demand and
inventory targets through the full-capacity convention, and can recover share
if its cost falls again. Exit requires capacity depreciation or mothballing,
which is a standing omission and stays one: retiring capacity introduces
hysteresis of its own and deserves to be measured alone rather than
underneath two other new mechanisms.

`epsilon` is `competitive_share_elasticity`, default **2.0**.

**Expect Part B to be nearly invisible in the existing scenarios**, because
within any region every producer of a commodity currently has the *same*
cost: they share a process, and investment gives entrants the average
overhead of the incumbents. Costs diverge in exactly two places — after the
`technique-change` scenario introduces a second technique, and in the new
scenario below.

## 4. The scenario: competition at a magnitude that shows

`technique-change` saves labor, and §1 established that labor is 2–4% of
money cost, so it will exercise the new machinery at about 1% amplitude. That
is worth measuring — it is the honest transmission strength — but it is too
small to demonstrate that the mechanism works.

**Decision: add a `cost-competition` scenario in which the entering producer
is cheaper in overhead rather than in labor.**

At day 60, Dust Basin gains a second provisioner with the same process and
**60% of the incumbent's operating overhead**
(`cheap_provisioner_overhead_fraction`, default 0.6), so its effective unit
cost is roughly 6.4 against 10.4. Read it as better equipment or a better
site: a capital-saving technique rather than a labor-saving one. Its labor
per meal is unchanged, so the *labor value* of meals does not move at all —
which makes it a clean instrument for the money-side mechanism, and a useful
contrast with `technique-change`, where value moves and money barely does.

Expected: the cheap entrant takes the larger share of the meal order book,
the sector's average cost falls, the anchor falls with it, and the meal price
falls — which lowers the wage, since the wage is the basket at current
prices, which lowers every producer's cost a little further. The rate of
surplus value should be **unchanged in labor time** (no technique changed the
labor content of a meal) while the money wage falls. Two more quantities
moving independently, which is the point of keeping four ledgers.

## 5. Predictions, recorded before implementation

**Equilibrium (2 metrics): exactly zero movement.** Engineered in §2; the
session stops and reports rather than loosening the check if this fails.

**Glut (most of ~20 metrics): little or no movement.** The glut crashes the
yayo price while leaves and chemfuel hold at reference (`docs/12`), so yayo's
cost — 97% inputs — barely moves, the ratio stays near one, and the anchor
stays near 21. Predicted: local trough within ±0.05 of 14.367961, day 66 ± 2,
distant trough and arbitrage volume unchanged, upstream extrema still
degenerate.

**Producer loss (most of ~20 metrics): substantial movement, downward on the
peak.** This is where Part A bites hardest. When 60% of yayo capacity is
destroyed, the surviving labs cannot absorb the leaves, so the leaf price
crashes to 0.693 — and leaves are 94% of yayo's cost. The yayo cost ratio
falls to roughly 0.4, dragging the anchor from 21 to about 14.6 at
kappa = 0.5, against a scarcity pressure pushing the other way. Predicted:
the peak falls well below 38.630290, plausibly into the **26–33** range, and
the capacity-recovery day moves later because a lower price means a thinner
margin and slower investment. This is a large, deliberate behavioral change,
and it is the one most likely to be judged wrong on grounds of realism rather
than arithmetic: a shortage of yayo now shows up partly as cheap inputs
rather than wholly as an expensive product.

**Depletion: the displaced-inventory artifact should shrink.** Chemfuel cost
doubles, so the anchor rises about 50% at kappa = 0.5, so less of the price
increase has to come from a starved buffer. Predicted: Dust chemfuel
inventory recovers from 63.8% of target to **75–90%**, and the settled price
lands near the current 3.36 by a different route. It should not fully return
to target at kappa = 0.5, since only half the cost increase reaches the
anchor.

**Subsistence shock: the meal price spike should be damped.** Destroying
provisioning capacity raises meal scarcity but barely raises meal *cost*
(wages are 3.7% of it), so a cost-aware anchor pulls against the spike.
Predicted: the meal price peak falls below its current 16.4 in the loss
scenario and the shock scenario's peak of ~35.5 drops noticeably — perhaps to
the high twenties.

**Technique change: price finally moves, and only slightly.** Predicted meal
price falls by **0.5–1.5%** — the honest transmission strength for a
labor-saving innovation in this calibration. Labor value still falls 12.46%.
The gap between those two numbers is this session's real result.

**Cost competition: the mechanism visible at scale.** Predicted the cheap
entrant takes 60–75% of meal output, sector average cost falls 15–25%, and
the meal price falls **5–12%**, with the labor-time rate of surplus value
unchanged to five figures.

## 6. Non-goals

- **Exit, depreciation, and mothballing.** Named in §3; deserves its own
  session.
- **Equalization of profit rates across sectors.** The ratio anchor freezes
  each sector's calibrated profit rate. A genuine price of production would
  equalize them and is a much larger change.
- **Giving the operating-overhead residual an economic interpretation.** §1
  names this as the structural weakness this session will expose. Fixing it
  means recalibrating every producer and moving every metric, and it should
  not ride along underneath two new mechanisms.
- Labor content of resource grades; wage bargaining; absolute rent; credit;
  RimWorld runtime work; sensitivity re-run. Unchanged non-goals.

## 7. New parameters

| parameter | default | meaning |
|---|---|---|
| `competitive_price_intensity` | 0.5 | how much of a relative cost change reaches the price anchor; 0 reproduces today's model exactly |
| `competitive_share_elasticity` | 2.0 | how sharply the order book favours the cheaper producer; 0 is a bit-exact no-op |
| `cheap_provisioner_overhead_fraction` | 0.6 | the cost-competition entrant's overhead, as a fraction of the incumbent's |
| `cost_competition_day` | 60 | when it enters |

## 8. Implementation order

1. Part A alone: seed costs, the sector cost, the cost-aware anchor.
   Measure the full 75-metric delta and understand it before continuing.
2. Part B alone: cost-weighted allocation with capacity capping. Measure
   again, separately, so the two mechanisms' effects are never conflated.
3. The `cost-competition` scenario.
4. Tests: exact equilibrium under both mechanisms, `kappa = 0` and
   `epsilon = 0` reproducing the old model, stability in every scenario,
   the depletion artifact shrinking, share going to the cheaper producer,
   ledgers closing, determinism.
5. Reference rewrite in its own commit with the deltas explained; new
   metrics frozen separately as newly observed quantities.
