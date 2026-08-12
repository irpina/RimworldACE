# Accounted input-output production: decisions

These decisions were made and written down **before** the solve was implemented,
because each one is a modelling choice with no oracle to settle it. The prior
labor study could adjudicate joint production empirically against RimWorld's own
prices (`FINDINGS.md`). Nothing here has that luxury: the Stage 0 laboratory is
the instrument, so its conventions have to be declared rather than discovered.

Everything below is a **choice**. Where a defensible alternative exists it is
named, and where the choice is exposed as a parameter that is said explicitly.

---

## 1. What a `Process` is

A `Process` is the unit of technology. A producer owns exactly one.

| field | meaning |
|---|---|
| `name` | identifier |
| `inputs` | commodity → units consumed per run |
| `outputs` | commodity → units produced per run |
| `direct_labor` | work-ticks added per run |
| `capacity_per_run` | units of producer capacity consumed per run |
| `unit_operating_cost` | silver per run, excluding materials |
| `apportionment` | joint-product cost allocation rule |

`outputs` is a mapping rather than a single commodity from the outset. Joint
production is not an edge case in this domain — the labor study hit it twice
(mining spoil, and meat/leather from one carcass) — so the single-output
special case is not worth encoding.

Capacity is expressed in **runs per day**: a producer's `capacity_per_day`
divided by `capacity_per_run` gives its maximum daily runs. With
`capacity_per_run = 1.0` and a single unit output, this reduces exactly to the
previous model's "capacity is units per day", which keeps the frozen yayo
baseline comparable.

### Labor value is still exogenous

`Process.direct_labor` is recorded but does **not** yet feed
`Commodity.labor_value`. Labor values remain the fixed figures carried over from
`FINDINGS.md`. Propagating labor value through the process graph — which is the
Stage 0 version of the embodied-labor solve — is deliberately a later slice, so
that this session's behavioral deltas are attributable to the material
constraint alone and nothing else.

---

## 2. Joint products: mass apportionment

**Decision: allocate shared process costs across joint outputs in proportion to
physical mass.**

Where a process has more than one output, its `direct_labor` and
`unit_operating_cost` have to be split among them to give any single output a
per-unit cost. The rule is mass share:

```
share(c) = mass_per_unit(c) * output_units(c)
           / sum over all outputs of the same
```

`mass_per_unit` comes from RimWorld's own `Mass` stat.

**Why this and not something else.** The alternatives are value apportionment
(split by market value of the outputs) and physical apportionment (split by
mass or volume). Value apportionment is circular here: the whole point of the
laboratory is to let prices form from material conditions, so allocating costs
by the prices those costs are meant to explain would build the answer into the
instrument. Mass is the same non-circular choice `FINDINGS.md` made for
butchery, for the same reason, and it has the additional virtue of being
already-collected data rather than a free parameter.

**What it is not.** Mass apportionment has no claim to being *correct*. It is
arbitrary in the specific sense that a process yielding one heavy worthless
output and one light valuable one will assign nearly all cost to the worthless
one. In the labor study the empirical test could not discriminate between
apportionment rules at all — every rule agreed to three decimal places — so
mass was chosen on principle and reported as such. That remains the honest
position.

**Status in this slice.** Every process in the current circuit has a single
output, so the rule is implemented and unit-tested but not exercised by the
scenarios. It is written now because the brief is right that the rule must be
fixed before the solve, not retrofitted once a byproduct appears and the
convenient answer is visible.

---

## 3. Partial input availability: proportional

**Decision: a producer holding 60% of its required inputs runs at 60%.**
The alternative — all-or-nothing — is implemented and available as the
`input_rationing` parameter, defaulting to `"proportional"`.

**Why proportional is the default.** A regional producer here is not one
workbench. It is the aggregate of every colonist, shop and refinery in a region,
and a day is its accounting period. Partial input availability at that
aggregation realistically means *fewer batches complete*, not that the whole
region downs tools. All-or-nothing would be right for a single indivisible
batch and wrong for an aggregate.

The second reason is instrumental, and worth stating because it influenced the
choice. The model already has a smooth price-driven utilization curve. Bolting
a discontinuous input constraint onto it invites limit cycles — produce
nothing, accumulate stock, produce everything, exhaust stock — that look like
economic results and are actually numerical artifacts of the discontinuity.
Since this session's job is to measure how the frozen baseline moves, a
mechanism that manufactures oscillation would corrupt the measurement. That is
a reason to *default* to proportional, not a reason to hide the alternative,
which is why it is a parameter.

**Liebig minimum.** A producer needing several inputs runs at the minimum
availability across all of them, not the average. Inputs are complements, not
substitutes; substitution between inputs is a technology choice and would need
a second `Process`, which is exactly how it should be represented.

---

## 4. Production is simultaneous

**Decision: all producers in a region draw on the region's opening inventory.
Output is added only after every draw is complete.**

Otherwise the day's result depends on the order producers happen to sit in a
list: run the psychoid farm before the drug lab and today's leaves are
available to today's lab; run it after and they are not. That is an invisible
one-day-per-stage difference in the propagation speed of every shock, decided
by list order.

The cost of simultaneity is that a shock takes one day per production stage to
propagate downstream. That is a real and visible property of the model rather
than a hidden one, which is the point.

### Contention for a shared input: pro-rata by requirement

When two producers want the same scarce input, each receives a share
proportional to what it asked for. This is order-independent and deterministic,
which priority ordering is not.

**Known limitation, deliberately accepted.** The allocation is a single pass. If
producer A receives its pro-rata share of chemfuel but is independently
throttled by a shortage of psychoid leaves, it consumes less chemfuel than it
was allocated, and that slack is *not* reallocated to producer B within the same
day. Slack is not destroyed — it stays in inventory and is available the next
day — so the material ledger closes exactly and the only cost is one day of
delay. Fixing this properly is a linear program; the delay is a smaller
distortion than a dependency would be, and this laboratory is dependency-free
by policy.

---

## 5. Price formation for intermediate goods: derived demand

The previous model scaled inventory targets and price pressure by a region's
**final** daily demand. Chemfuel and psychoid leaves have no final demand at
all, so that rule would give them a target inventory of zero, an unbounded
coverage gap, and an immediate collapse to the price floor.

**Decision: scale by throughput demand — final demand plus the demand derived
from local producers' input requirements at full capacity.**

This is a strict generalization: a commodity with no producers consuming it has
zero derived demand, so its behavior is unchanged. Yayo is exactly that case,
which is why the frozen yayo baseline stays comparable across this change
rather than being confounded by it.

A commodity with zero throughput in a region — neither consumed finally nor used
as an input there — has its price left untouched rather than driven to the
floor. "Not traded here" is the right reading of no demand.

---

## 6. Input shortfall registers as unmet demand

When a producer cannot source an input, the shortfall is recorded as unmet
demand **for that input**, alongside unmet final consumption demand.

Without this, an upstream shortage is invisible to the price system: the input
would run out, downstream output would fall, and the input's own price would
never register that it was scarce. Recording it is what makes a shortage
propagate as a *price* signal rather than only as a quantity.

---

## 7. Route capacity goes to the widest spread first

With more than one commodity on a route, scarce daily freight capacity has to be
allocated. The previous code iterated commodities in alphabetical order, which
was harmless with one commodity and is arbitrary with three — `chemfuel` would
have taken priority over `yayo` for no reason but the letter c.

**Decision: dispatch in descending order of gross spread net of freight.**
Arbitrageurs ship the most profitable cargo first. This is an identity on the
single-commodity model, so it does not disturb the frozen baseline.

---

## 8. What is deliberately still missing

Named here so that nothing below is mistaken for an oversight:

- **Producers do not pay for their inputs in silver.** The material constraint
  is in; the cash constraint is not. `unit_cost` remains an exogenous per-unit
  cash cost driving the utilization curve, and does not yet include the market
  price of inputs. Adding it would change the silver ledger and the price floor
  simultaneously, making this session's deltas uninterpretable.
- **Capacity investment is still free.** Capital-goods and construction costs
  are the next session. `docs/07-accounted-input-predictions.md` flags that its
  producer-loss predictions assume this is fixed, so those predictions should
  be expected to miss.
- Resource reserves, depletion, rent, wages, subsistence, credit.

---

## Provenance of the numbers

Every per-unit ratio and reference price in the circuit is read from RimWorld's
own defs rather than invented, with one exception that is flagged:

| quantity | value | source |
|---|---|---|
| psychoid leaves per yayo | 8 | `Yayo` `costList` |
| yayo direct labor | 350 ticks | `Yayo` `WorkToMake` |
| psychoid leaf direct labor | 46.2 ticks/unit | `out/embodied_labor.csv` |
| chemfuel direct labor | 25 ticks/unit | `out/embodied_labor.csv` |
| yayo reference price | 21.0 | `Yayo` `MarketValue` |
| psychoid leaves reference price | 1.9 | `PsychoidLeaves` `MarketValue` |
| chemfuel reference price | 2.3 | `Chemfuel` `MarketValue` |
| masses | 0.05 / 0.03 / 0.05 | `Mass` stat |
| **chemfuel as an input to farming and refining** | **stylized** | **not vanilla** |

The last row is the deliberate exception. Vanilla RimWorld drug labs and
psychoid fields do not consume chemfuel. It is introduced as a shared operating
input — read it as the fuel behind the generators — because the circuit needs a
commodity consumed by **more than one** producer. A pure two-stage chain cannot
exercise contention for a scarce shared input, and contention is precisely where
accounting bugs hide. Fidelity was traded for graph shape, knowingly, in one
place.
