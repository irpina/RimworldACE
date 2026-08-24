# Resource reserves, grade depletion, and differential rent: decisions before implementation

This decision document is recorded before any code changes. It addresses the
first item in HANDOFF.md's "intentionally absent" list: finite resource
reserves, grade depletion, marginal extraction cost, and differential rent.

---

## What problem this solves

Chemfuel synthesis is the only extraction process in the circuit. It currently
has no inputs and no reserve — it produces from nothing. This makes it a free
ledger source for material, just as capacity was a free ledger source for
silver before docs/13. Three economic properties are therefore missing:

1. **Finite extraction.** Extraction should draw from a bounded natural
   endowment. A region that extracts chemfuel indefinitely at constant cost is
   not a model of production from nature — it is a model of a cornucopia.

2. **Rising marginal cost.** When deposits are heterogeneous, the cheapest are
   extracted first. As they deplete, the marginal cost of extraction rises.
   The price must eventually cover the cost of the worst deposit in use, not
   only the cheapest.

3. **Differential rent.** When deposits of different quality coexist, the
   cheaper ones earn a surplus over the marginal deposit's cost. That surplus
   is rent — it accrues from natural advantage, not from more or better labor.
   The HANDOFF is explicit: differential rent belongs in the money/rent
   ledger, not labor value.

None of these can be modelled without a reserve that depletes.

---

## Non-goals for this slice

- Multiple extraction commodities. Only chemfuel has an extraction process.
  Extending to other commodities is a later generalization that changes nothing
  structurally.
- Exploration or discovery of new deposits. Reserves are seeded at scenario
  start and only decrease.
- Absolute rent (monopoly control of access). Only differential rent.
- Rent as a silver transfer to a landowner entity. Rent is observed and
  tracked, not collected by an agent.
- Reserve trading or property transfers.

---

## Part A: Reserve infrastructure

### Decision: regional reserves, not per-producer deposits

Each region has an optional `ResourceReserve` per commodity. All extraction
producers in that region share the same reserve. When the reserve depletes,
every extraction producer in the region is constrained equally.

**Why not per-producer deposits?** Per-producer deposits would allow
intra-regional differential rent (some producers on better deposits than
others). But the current model has one extraction producer per region, and
investment creates additional producers of the same type. Per-producer
deposits would require deciding which deposit a new entrant gets, whether
deposits can be subdivided, and whether producers can switch deposits. All of
that is structure for a later slice. The regional reserve is the minimal
change the HANDOFF requests.

Intra-regional differential rent can be added later by splitting a regional
reserve into producer-level deposits. The accounting machinery (grade
depletion, marginal cost, rent tracking) is the same either way.

### Reserve data model

```
ResourceGrade:
    quantity: float          # remaining extractable units of commodity
    extraction_cost: float   # operating cost per unit for this grade

ResourceReserve:
    commodity: str
    grades: List[ResourceGrade]   # ordered cheapest first
```

A `ResourceGrade` is mutable: its `quantity` decreases as material is
extracted. `extraction_cost` is fixed — it is a natural property of the
deposit, not a market outcome.

A `ResourceReserve` exposes:

- `remaining` — total extractable quantity across all grades.
- `marginal_cost()` — the extraction cost of the cheapest non-exhausted grade.
  If every grade is exhausted, returns infinity.
- `extract(amount)` — draws from the cheapest grade first, returns the actual
  amount extracted (may be less than requested if the reserve is nearly
  exhausted). The cost of extraction is the grade's cost, not the market price.

### How reserves are attached

`Region` gains a new field: `reserves: Dict[str, ResourceReserve]`, defaulting
to an empty dict. Regions without a reserve for a commodity produce it as
before (no constraint). This ensures backward compatibility if the scenario
does not configure reserves.

### Default reserve sizing

For all existing scenarios (equilibrium, glut, producer-loss, input-shortage,
arbitrage), the reserve must be large enough that no grade transition occurs
during the run. The longest scenario observation is producer-loss extended to
day 660 (convergence test). Each region consumes 6 chemfuel/day, so 660 days
requires 3,960 units from the first grade.

**Default: 100,000 units in a single grade at the current operating overhead.**

At 6 units/day, this lasts ~16,667 days (~278 in-game years). No existing
scenario reaches even 1% depletion. The first grade's extraction cost equals
the current `operating_overhead(CHEMFUEL, region_cost)` — 1.5333 for Dust
Basin, 1.5881 for Green River — so the equilibrium price path is identical.

---

## Part B: Dynamic marginal extraction cost

### Decision: update extraction producers' unit_cost each day

At the start of each production step, before the utilization curve is
evaluated, every extraction producer's `unit_cost` is set to the marginal
grade cost of its region's reserve. This is a controlled mutation at a single
point in the simulation loop, analogous to how `output_total` is already
updated during production.

**Why not a new method on Producer?** The cost floor already uses
`effective_unit_cost(prices)`, which computes `self.unit_cost + input_cost /
output`. For extraction processes with no inputs, `effective_unit_cost`
returns `self.unit_cost`. By updating `unit_cost` to the marginal grade cost,
the entire cost floor and utilization machinery picks it up with no API
change. No new parameter passing, no new method signature.

### Integration with the production loop

Current `_produce()` flow:

1. Compute `desired_runs` per producer (uses utilization → effective_unit_cost)
2. Compute `_planned_runs` (demand-led control)
3. Pro-rata input rationing
4. Execute: draw inputs, add outputs

With reserves:

0. **New: update extraction unit_cost** from marginal grade cost
1. Compute `desired_runs` (now reflecting the current grade's cost)
2. Compute `_planned_runs` (unchanged)
3. Pro-rata input rationing (unchanged for non-extraction inputs)
4. **New: reserve rationing** — limit total extraction output to remaining
   reserve, pro-rata across producers if multiple share the same reserve
5. Execute: draw inputs, add outputs
6. **New: deduct extracted quantity from reserve**

### Reserve rationing detail

If total wanted extraction exceeds the remaining reserve, all extraction
producers for that commodity are scaled down by the same ratio:

```
reserve_ration = min(1.0, remaining / total_wanted_output)
```

This is the same logic as the existing input rationing, applied to the
natural endowment. It is proportional and order-independent.

### What happens when the reserve exhausts

When a reserve's `remaining` drops to zero, `marginal_cost()` returns
infinity. The producer's `unit_cost` becomes infinite, the utilization curve
gives zero, and the producer idles. Production of that commodity in that
region stops. Downstream producers then face rising input prices (if
inter-regional trade exists) or physical shortage (if it doesn't).

This is the correct economic behavior: exhaustion of a natural resource
should halt extraction, not continue at the old cost.

---

## Part C: Differential rent tracking

### What is differential rent

When two regions extract the same commodity but at different costs, the
cheaper region earns a surplus over what the marginal (most expensive) active
extractor earns. That surplus is differential rent — income from a natural
advantage, not from more or better labor.

Classical definition: for an infra-marginal extractor with cost C_i, and the
most expensive active extractor with cost C_m:

```
rent_per_unit = max(0, C_m − C_i)
total_rent = rent_per_unit × output
```

### Decision: rent is observed, not transferred

Differential rent is computed and tracked in the `Ledger` as a separate
quantity. It is not a silver transfer to a landowner entity. There is no
landowner entity in Stage 0 — the region itself is the implicit owner.

The rent is computed at each production step:

1. Find the global marginal cost: the highest marginal extraction cost among
   all regions with non-exhausted reserves for that commodity.
2. For each region with a lower marginal cost, compute the rent as
   `(global_marginal − local_marginal) × amount_extracted`.
3. Accumulate in `Ledger.differential_rent[commodity]`.

If all regions have the same marginal cost, differential rent is zero. If one
region has exhausted its reserve entirely (marginal cost = infinity), it is
excluded from the global marginal cost calculation (it is not an active
extractor). The marginal cost is set by the most expensive *active* extractor.

### Rent in the snapshot

The history snapshot gains:
- `reserve_remaining` per commodity per region
- `marginal_extraction_cost` per commodity per region

These are raw observations; differential rent is derived from them.

---

## Part D: Ledger and material accounting

### New ledger field

`Ledger.reserve_depletion: Dict[str, float]` — total extracted from reserves.
`Ledger.differential_rent: Dict[str, float]` — total rent earned by
infra-marginal extractors.

### Accounting identity

For extraction commodities, every unit produced must have been drawn from a
reserve:

```
reserve_depletion[commodity] == production[commodity]
          (for commodities with reserves)
```

This is testable. If it fails, the reserve is leaking or overcounting.

### Commodity balance

The existing `commodity_balance()` is unchanged. It tracks:
`initial_stock + production + injection − destruction − consumption −
intermediate_consumption − current_stock = 0`. Production is still a source;
the reserve constrains how much production is possible, but the material
identity is the same.

The reserve itself is *not* a commodity. It does not enter the commodity
material balance. It is an exogenous natural endowment that depletes as a
side effect of production. Think of it as the ore body: a source of material,
but not itself traded or stocked as a commodity.

### Cash balance

Unchanged. Reserve depletion does not move silver — the producer pays the
operating cost (which varies by grade) but does not buy the reserve from
anyone. Rent is observed, not paid. Silver still balances.

---

## Part E: Depletion scenario

### Purpose

A new scenario that exercises reserve depletion, grade transition, rising
marginal cost, and differential rent. Existing scenarios keep their large
default reserves and remain unchanged.

### Design

The depletion scenario starts one region (Dust Basin) with a small,
two-grade reserve:

- **Grade 1:** 600 units at the current operating overhead (1.5333).
  At 6 units/day, this depletes around day 100.
- **Grade 2:** 100,000 units at 2× the current overhead (3.0667).
  This is expensive but abundant — it won't deplete in any practical run.

Green River keeps the default large single-grade reserve (100,000 at 1.5881).

The scenario runs for 240 days. Around day 160 (60 equilibrium + 100
depletion), Dust Basin's Grade 1 exhausts and the marginal cost jumps. The
remaining 80 days observe the price response.

### Why asymmetric reserves?

Having the two regions on different grades creates differential rent: Green
River's Grade 1 (cost 1.5881) is cheaper than Dust Basin's Grade 2 (cost
3.0667), so Green River earns rent on its chemfuel extraction. This is the
Ricardian extensive margin.

If both regions had identical reserves, grade transitions would happen
simultaneously and there would be no inter-regional cost difference — hence
no differential rent. The asymmetry is the minimal setup that exercises rent.

---

## Calibration check: equilibrium stationarity preserved

At reference prices with the default 100,000-unit first grade:

- Dust Basin chemfuel marginal cost = 1.5333 (identical to current overhead)
- Green River chemfuel marginal cost = 1.5881 (identical to current overhead)
- No reserve depletion visible in 240 days

The utilization curve, cost floor, investment logic, and demand-led planning
all see the same costs as before. The equilibrium price path is unchanged.
The four-year stationarity requirement is preserved.

---

## Interaction with existing mechanisms

### Cost floor

The cost floor uses `effective_unit_cost(prices)`, which returns
`self.unit_cost + input_cost / output`. For chemfuel (no inputs), this is
just `self.unit_cost`, which now equals the marginal grade cost. When the
grade changes, the effective cost rises, and the utilization curve curtails
the producer. Downstream producers see rising chemfuel prices, which raises
their own effective costs — the price signal propagates through the cost
channel as designed in docs/13.

### Investment

New extraction capacity built via `_invest()` draws from the same regional
reserve. The new producer's `unit_cost` is set to the current marginal grade
cost (via `assumed_overhead` in the investment logic). Each day, `_produce()`
updates it to the current marginal cost, so the producer always operates at
the current grade, not a stale historical one.

Investment does not create new reserves. Adding extraction capacity
accelerates depletion. This is the correct economic relationship: investment
can increase the rate of extraction but not the natural endowment.

### Buffer investment

The buffer-deficit investment logic considers current demand and supply. If
reserve depletion reduces chemfuel output, inventories will fall below
target, triggering buffer investment. But the new capacity will also be
constrained by the reserve. If the reserve is nearly exhausted, the new
capacity produces zero. The investment was wasted — but that is a natural
economic outcome, not a bug. Agents cannot foresee reserve exhaustion in
this slice.

### Demand-led production control

Unchanged. The planned-runs logic does not depend on reserve state. It plans
how much output is *wanted*; the reserve constraint limits how much is
*possible*. This is the same separation as between planning and rationing.

---

## Predictions

### Existing 53 metrics: zero movement

All existing scenarios use the default 100,000-unit first grade at the
current operating overhead. No grade transition, no cost change, no reserve
constraint. All 53 frozen metrics should remain at their exact current
values.

If any existing metric moves, the reserve infrastructure has a bug — it
should be invisible when the reserve doesn't bind.

### Depletion scenario: grade transition raises chemfuel price

Around day 160, Dust Basin's Grade 1 (600 units at cost 1.5333) exhausts.
The marginal cost jumps to Grade 2 (cost 3.0667 — a 2× increase).

The chemfuel price in Dust Basin should rise toward 3.0667 or above. The
utilization curve gives full utilization at price/cost ≥ 1.05, so the new
equilibrium price should be at least 3.0667 × 1.05 ≈ 3.220.

### Depletion scenario: downstream price propagation

The cost floor propagates chemfuel price increases downstream:

- Psychoid leaves: input cost rises by chemfuel_per_leaf × price_increase =
  0.05 × (new_chemfuel_price − 2.3) per unit.
- Yayo: input cost rises through both the direct chemfuel input and the
  indirect path through leaves.

Both leaf and yayo prices should rise after the grade transition, but with
a delay (one day per production stage of propagation).

### Depletion scenario: differential rent appears

While both regions extract at their Grade 1 cost (before Dust Basin's grade
change), differential rent is minimal — the cost difference is 1.5881 −
1.5333 = 0.0548 per unit.

After Dust Basin moves to Grade 2 (cost 3.0667), Green River's Grade 1
(cost 1.5881) earns substantial rent: 3.0667 − 1.5881 = 1.4786 per unit
of chemfuel extracted. This is genuine Ricardian rent — income from a
superior natural endowment.

### Depletion scenario: chemfuel arbitrage may activate

With Dust Basin's chemfuel price above 3.0 and Green River's around 2.3,
the spread may exceed freight cost. If chemfuel arbitrage activates, Green
River exports chemfuel to Dust Basin. This would be a new arbitrage flow
that exercises the multi-commodity arbitrage path already built into the
dispatch logic.

Whether it actually activates depends on the standard freight cost (3.5 +
risk markup = 3.85). The spread of ~0.7 is well below 3.85, so chemfuel
arbitrage probably does *not* activate with the standard route. The loss
route's freight (7.0 + risk markup) is even wider. If this prediction is
wrong and arbitrage does activate, it would mean the spread is wider than
expected or the freight calculation differs.

### Depletion scenario: ledger closes

Material and silver balances should close to floating-point zero. The
reserve depletion should exactly equal chemfuel production. No new silver
flows are introduced.

---

## Implementation order

1. Add `ResourceGrade` and `ResourceReserve` to model.py
2. Add `reserves` field to `Region`
3. Update `_produce()`: marginal cost update, reserve rationing, depletion
4. Add `reserve_depletion` and `differential_rent` to `Ledger`
5. Add reserve data to history snapshots
6. Update `scenarios.py`: default reserves, depletion scenario
7. Tests: reserve depletion, grade transition, rent, balances, equilibrium
8. Run baseline to confirm zero delta on existing 53 metrics
9. Record results vs predictions

Each step is tested and committed before the next.
