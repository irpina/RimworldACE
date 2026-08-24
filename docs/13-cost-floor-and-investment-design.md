# Cost floor and investment motives: decisions before implementation

This decision document is recorded before any code changes. It addresses the
two remaining free-ledger-source problems identified in HANDOFF.md and docs/12:

1. Producers do not pay cash for inputs.
2. Capacity investment is still free.

And a structural limitation exposed by the demand-led control law:

3. Upstream capacity exactly matches restored steady-state flow and can never
   rebuild a depleted buffer.

---

## Sequencing: cost floor before buffer-rebuild investment

**Decision: implement both the cost floor and buffer-aware investment in one
session, cost floor first within the implementation.**

The brief's argument is correct: adding a buffer-rebuild investment motive to a
model where capacity entry is free would allow unlimited capacity growth.
Investment sees a stock deficit, creates capacity at no cost, and the new
capacity persists after the buffer refills. Repeated shocks would ratchet
capacity upward with no offsetting cost, which is not a cost floor — it is a
subsidy.

The converse order is also problematic. Adding a cost floor alone would close
the silver channel and change margins, but the buffer-scar from docs/12 would
remain: leaves converging to 1,451 instead of 1,600 because upstream capacity
has no headroom to refill. The cost floor changes *whether* investment happens
(via margin tests), not *what* investment targets. Without a buffer motive,
investment still sees only flow-capacity shortfall, and the scar persists
regardless of how investment is paid for.

Both interact through silver: the cost floor determines how much cash producers
retain after buying inputs, and that retained cash is what investment must now
consume. Implementing them together means the silver circuit closes in one pass
rather than requiring a temporary accounting fiction where investment consumes
silver that producers never spent.

**Implementation order within this session:**

1. Producers pay for inputs — this changes the silver ledger and the
   utilization curve.
2. Investment consumes a construction fund (silver) — this replaces free
   capacity entry.
3. Buffer-aware investment motive — this addresses the stock-scar problem.

Each step is tested and committed before the next.

---

## Part A: Producers pay cash for inputs

### What changes

`Producer.unit_cost` currently reflects only the exogenous operating cost
scaled from the yayo producer's margin. It does not include the cost of
purchased inputs. Producers consume material but not silver.

**Decision: a producer's effective unit cost includes the market price of its
inputs, evaluated at the region's current prices.**

For a process with inputs {A: 3, B: 2} producing one unit of output C, the
input cost of one unit of C is:

```
input_cost = 3 × price(A) + 2 × price(B)
```

The total unit cost driving the utilization curve becomes:

```
effective_unit_cost = operating_cost + input_cost
```

This is the missing cost floor. When input prices rise, downstream production
becomes more expensive and curtails earlier on the utilization curve, even if
material inputs are physically available. The two constraints — material
availability and financial viability — are now independent and both binding.

### Cash flow

When a producer runs, it pays for inputs at the region's current price. The
silver goes to the region's cash pool (representing the upstream producers'
revenue in aggregate). This is a simplification — individual producer cash
accounts would require tracking bilateral trades — but it closes the silver
ledger: every unit of input consumed has a corresponding silver payment, and
silver is conserved.

```
cost_of_inputs = sum(drawn[name] × region.prices[name] for each input name)
producer.cash -= cost_of_inputs
region.cash += cost_of_inputs
```

Wait — producers currently have a `cash` field but it is never populated from
sales revenue. With three producers (chemfuel, leaves, yayo) in a region, the
yayo producer's sales revenue comes from final consumption, but intermediate
producers have no revenue source — their output enters inventory and is drawn
by downstream producers, but no payment flows back.

**Decision: use a regional cash pool for input purchases, not individual
producer accounts.** The region's cash pool acts as the settlement account. A
producer buying inputs draws from the region's cash; revenue from final
consumption enters the region's cash. This is how the current arbitrage
settlement already works — it draws from destination cash and credits source
cash — and extending it to production keeps the accounting consistent.

Individual producer profitability is still calculable from the utilization curve
(which tests whether expected revenue covers effective cost), but the actual
silver movement goes through the regional pool. This avoids inventing a transfer
pricing mechanism between co-located producers.

### Effect on the utilization curve

The utilization curve already maps `price / unit_cost` to a [0, 1] output
fraction. With input prices included in `unit_cost`, the curve now responds to
upstream price movements. When a leaf shortage raises the leaf price, the drug
lab's effective cost rises, its utilization falls, and it buys fewer leaves —
a negative feedback loop that the demand-led control law cannot provide because
it operates on quantities, not margins.

### Prediction: does the cash channel add distinct behavior?

**Yes, and here is the specific claim to test.**

The demand-led control law handles the *quantity* side: when downstream
production curtails, upstream production contracts to match. But it does not
respond to *margin compression*. A scenario where input prices rise gradually
without any physical shortage would not trigger the demand-led control at all —
the upstream producer would keep making its full planned output because the
downstream producer keeps ordering it. Only when the downstream producer's
utilization drops (because its margin is squeezed) does the order signal
contract.

The cash channel therefore adds a **price-mediated curtailment** path that the
quantity-mediated demand-led control cannot reach. The two are genuinely
complementary, as docs/11 argued, and this is now testable.

**Specific metric predictions for the cost floor alone:**

The equilibrium scenario should remain exactly stationary. At reference prices,
every producer's effective unit cost — operating cost plus input prices — must
equal the unit cost that already seeds the utilization curve, because the
current calibration was specifically designed to make all producers run at full
utilization at reference prices. If the input-price component is scaled to match
the existing operating cost, nothing moves.

*But this requires re-deriving the operating cost.* The current `unit_cost` for
each producer is set by `ScenarioParameters.unit_cost()`, which scales any
reference price to match the yayo producer's margin. Once input costs are
explicit, the *remaining* operating cost must be the residual:

```
operating_cost = old_unit_cost - input_cost_at_reference_prices
```

If this residual is negative for any producer, the current calibration implicitly
assumed inputs were free and the margin is actually tighter than it appeared.
I will check this before implementing.

For the **glut** scenario: the demand-led control already eliminated upstream
hysteresis. Input costs at reference prices add no incremental signal because
the upstream prices never moved. **Prediction: zero additional movement in the
glut.** The 39 glut-related metrics should remain unchanged.

For the **producer-loss** scenario: destroying 60% of the drug labs removes 60%
of the leaf and chemfuel demand. The demand-led control contracts upstream output.
But now the upstream producers *also* see falling revenue (fewer units sold at
reference price) while their operating costs are unchanged. This is a second
curtailment path. However — the demand-led control already fully contracts
upstream to match orders. The cash channel would only bite if the remaining
producers' margins were compressed, which only happens if *their* input prices
change. Since chemfuel has no inputs in the model, and leaf's only input is
chemfuel (whose price barely moves in producer-loss), **prediction: the
producer-loss metrics will see small or zero additional movement from the cost
floor alone.** The buffer-scar (leaves at 1,451 instead of 1,600) persists
because it is an investment problem, not a cost problem.

For the **input-shortage** scenario: this is where the cash channel should be
most visible. As leaves become scarce and their price rises 5×, the drug lab's
effective cost rises sharply, and its utilization curve curtails production
*before* the material constraint fully binds. **Prediction: the input-shortage
scenario will show earlier and deeper yayo curtailment, with yayo price peaking
slightly lower (because less output is attempted against scarce inputs, so the
residual leaf stock is higher).**

---

## Part B: Investment consumes a construction fund

### What changes

`_invest()` currently creates `CapacityProject` objects freely. The new
producer appears when the project completes, with no silver spent.

**Decision: investment costs silver, drawn from the region's cash pool.**

The construction cost of a capacity project is proportional to the capacity
being built and the expected per-unit cost of operating it:

```
construction_cost = capacity × construction_cost_multiplier × unit_cost
```

`construction_cost_multiplier` is a new `ScenarioParameters` coefficient. It
represents how many days' worth of operating cost it takes to build one unit of
daily capacity — a payback period in physical terms. A multiplier of 60 means
building one unit of daily capacity costs 60 days' worth of that capacity's
unit operating cost.

This is a simplification. The full capital-goods story would have investment
consume specific material commodities (steel, components, etc.), which would
close a second material circuit. That is the next slice after this one. Silver
as a construction fund is the minimal change that makes investment non-free
while keeping the existing commodity set unchanged.

The silver is deducted from the region's cash when the project is commissioned
(not when it completes). This is a commitment: the silver is tied up during
construction and cannot be spent on anything else. The investment check already
uses an expected-margin test, so projects that look unprofitable are not
started.

If the region cannot afford the full construction cost, the project is scaled
down to what the region can afford, or skipped entirely if the affordable
capacity is below a minimum threshold.

### Silver conservation

The construction cost leaves the region's cash pool and enters the ledger as
`investment_spending`. The ledger tracks cumulative investment spending so the
silver balance identity becomes:

```
sum(region.cash) + transport_cash + investment_spending = initial_cash
```

This is an extension of the existing `cash_balance()` check.

### Prediction

At equilibrium, no investment occurs because there is no flow-capacity
shortfall and no buffer deficit. **Prediction: equilibrium metrics unchanged.**

In producer-loss, investment creates replacement capacity. With a cost, the
investment check must additionally confirm the region can afford it. If the
region's cash is low (from paying for inputs), investment may be delayed or
reduced. **Prediction: capacity recovery may slow by 0–15 days, depending on
how much cash the regional pool retains after input purchases.**

---

## Part C: Buffer-aware investment motive

### The problem

Docs/12 documented the post-shock buffer scar: leaves converge to 1,451 instead
of their 1,600 target because upstream capacity exactly matches restored steady
use. The replenishment controller requests more output, but both upstream
producers are at their capacity ceiling. Investment sees no *flow*-capacity
shortfall and creates nothing.

### Decision: invest for buffer deficit as well as flow deficit

**When a commodity's inventory is persistently below its target, and existing
capacity plus pipeline cannot produce enough surplus to close the gap within
a reasonable horizon, investment creates temporary additional capacity.**

The buffer investment signal is:

```
buffer_deficit = max(0, target_stock - current_stock)
buffer_surplus_capacity = max(0, existing_capacity - current_throughput_demand)
days_to_refill = buffer_deficit / max(buffer_surplus_capacity, epsilon)
```

If `days_to_refill` exceeds a threshold (a new parameter,
`buffer_refill_horizon_days`, default 60), and the standard investment margin
test passes, a buffer-refill project is created. Its capacity is sized to close
the buffer gap within the horizon:

```
buffer_capacity_needed = buffer_deficit / buffer_refill_horizon_days
```

This is added to any flow-shortfall investment, subject to the same
construction-cost and affordability tests.

### Why this is proportional, not threshold-and-switch

The buffer investment signal is continuous: a larger deficit produces a larger
capacity request; a smaller deficit produces a smaller one. When the buffer is
full, the signal is zero. There is no on/off boundary.

The horizon parameter is a planning window, not a trigger threshold. It says
"if refilling at current surplus rate would take longer than this, add
capacity." A deficit that would naturally refill in 30 days (below the 60-day
horizon) does not trigger investment. This avoids overbuilding for transient
fluctuations.

### The capacity is not marked as temporary

The brief mentioned "temporary" additional capacity. I am not implementing an
explicit expiry mechanism. Instead, the excess capacity will naturally become
idle once the buffer is full: the demand-led control law curtails production
to what is needed, so the extra capacity sits unused and produces nothing.
It persists as installed capacity but costs nothing while idle (no input
purchases, no operating cost, because utilization is zero below the
zero-utilization price ratio).

This is the simplest design that resolves the scar. If future slices need
capacity depreciation or mothballing, the idle capacity is available to attach
those mechanisms to.

### Prediction

The producer-loss leaves buffer should converge to 1,600 instead of 1,451.
The refill will take approximately `buffer_refill_horizon_days` after the
replacement yayo capacity arrives. Leaf and chemfuel terminal prices should
converge closer to their reference values.

The equilibrium scenario must remain exactly stationary: at equilibrium,
`buffer_deficit` is zero, so the mechanism produces no signal.

---

## Calibration check: input costs at reference prices

Before implementing, verify that the existing operating costs are consistent
with explicit input payments. For each producer in the circuit:

| producer | current unit_cost | inputs at reference prices | residual |
|---|---|---|---|
| drug lab (yayo) | 14.0 | 8 × 1.9 + 0.2 × 2.3 = 15.66 | **−1.66** |
| psychoid farm (leaves) | 1.2667 | 0.05 × 2.3 = 0.115 | 1.1517 |
| chemfuel refinery | 1.5333 | (none) | 1.5333 |

**The drug lab has a negative residual.** Its current unit cost of 14.0 is less
than the cost of its inputs at reference prices (15.66). This means the
original calibration implicitly assumed inputs were free — the yayo producer's
margin was set from `reference_price × dust_unit_cost / reference_price` =
14.0, which is a pure operating cost that never contemplated paying 15.66 for
inputs.

This is expected. The utilization curve needs to be re-derived with input costs
included. The new effective cost at reference prices is:

```
drug lab:   operating_residual + input_cost = 0 + 15.66 = 15.66  (but see below)
```

Since the operating cost was meant to represent everything *except* inputs, and
inputs now have an explicit price, the operating residual for the drug lab
becomes zero (or a small positive value representing non-material overhead).
The simplest resolution: set `unit_operating_cost` on each `Process` to the
non-material operating overhead, and compute total unit cost dynamically as
`operating_cost + input_cost_at_current_prices`.

**Decision: re-derive unit costs so that `effective_cost = operating_overhead +
input_cost_at_reference_prices` equals the current unit cost.** This means:

| producer | operating_overhead | input_cost_at_ref | effective_cost |
|---|---|---|---|
| drug lab | 14.0 − 15.66 → **0** | 15.66 | 15.66 |
| psychoid farm | 1.2667 − 0.115 = 1.1517 | 0.115 | 1.2667 |
| chemfuel refinery | 1.5333 | 0 | 1.5333 |

The drug lab's operating overhead is set to zero because the entire margin was
already consumed by the implicit input cost. Its effective cost *rises* from
14.0 to 15.66, which means at the reference price of 21.0 its margin narrows.

To keep the equilibrium exactly stationary, the utilization curve thresholds
must be recalibrated so that full utilization still occurs at the reference
price with the new effective cost. The ratio `price / effective_cost` at
reference is:

- drug lab: 21.0 / 15.66 = 1.341 → well above `full_utilization_price_ratio` (1.05)
- psychoid farm: 1.9 / 1.2667 = 1.500 → also above
- chemfuel refinery: 2.3 / 1.5333 = 1.500 → also above

All three are above 1.05, so the utilization curve already returns 1.0 at
reference prices with the new costs. **The equilibrium is preserved without
changing the utilization thresholds.**

The key insight: the unit cost was previously `reference_price × region_cost /
yayo_reference_price`. With `dust_unit_cost = 14.0` and `reference_price = 21.0`,
the yayo unit cost was 14.0 and the yayo ratio was 21.0/14.0 = 1.5. With
inputs costing 15.66, the new ratio is 21.0/15.66 = 1.341. Still well above
1.05. The equilibrium holds.

But: the `unit_cost()` helper in `ScenarioParameters` must be adjusted. It
currently scales all producers to the same margin. With explicit input costs,
the scaling must preserve the *residual operating overhead* as the unit cost
and compute input costs dynamically. The total effective cost then depends on
current prices, which is the whole point.

---

## Summary of new parameters

| parameter | meaning | default |
|---|---|---|
| `construction_cost_multiplier` | days of unit-cost equivalent to build one unit of daily capacity | 60 |
| `buffer_refill_horizon_days` | planning horizon for buffer-refill investment | 60 |
| `min_investment_capacity` | minimum capacity for a project to be worth starting | 0.1 |

All exposed through `ScenarioParameters`.

---

## What this session does not add

- Material capital goods (steel, components) as investment inputs — silver is
  the construction fund.
- Individual producer cash accounts or transfer pricing.
- Capacity depreciation or mothballing.
- Resource reserves, rent, wages, subsistence.
- Endogenous labor value propagation.
