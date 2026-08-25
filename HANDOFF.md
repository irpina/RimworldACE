# Project handoff — Labor Content and Economy

**Last updated:** 2026-08-25  
**Repository:** `C:\Users\PintS\OneDrive\Documents\Projects\snlt`  
**GitHub:** `https://github.com/irpina/RimworldACE`  
**Current branch:** `master`  
**Latest Stage 0 model commit:** `a0417de` (optional history; opening stock held as state)
**Behavioral baseline:** `29e4627` (154 metrics: 5 structural scale observations, no timings)
**Sensitivity harness:** `f2c490c`  
**Pre-process predictions:** `cae1ba2`  
**Process design decisions:** `863ee42`  
**Process tests:** `57b05ed`  
**Process results:** `98ae17e`  
**Upstream behavioral baseline:** `e2a7c43`
**Hysteresis investigation:** `097e40c`
**Production-control design:** `cbeb720`
**Production-control results:** `3f9c20b`
**Cost-floor design:** `a3fcfe7`
**Cost-floor results:** `9867014`
**Reserve design:** `34bf3ba`
**Reserve implementation:** `6eed091`
**Reserve results:** `d640485`
**Wage-relation design:** `13ec465`
**Wage-relation implementation:** `27af376`
**Wage-relation results:** `5985878`
**Endogenous value design:** `0c5bbf6`
**Endogenous value implementation:** `9426caf`
**Endogenous value results:** `c3db687`
**Competitive transmission design:** `a475152`
**Competitive transmission implementation:** `a9c3016`, `9826489`
**Competitive transmission results:** `77c3078`
**Constant capital design:** `87ac0cc`
**Constant capital implementation:** `7bd916c`, `83a780a`
**Constant capital results:** `1f48794`
**Latest Stage 1 implementation:** `6794dfc`  
**Stage 1 verification checkpoint:** `906f63e`

Read this file first when taking over the project. Then read `FINDINGS.md` before
changing any labor figures or assumptions.

---

## Project direction

The long-term goal is a suite of RimWorld mods that makes economic relations
material and legible, with particular emphasis on Marxian concepts:

- embodied and socially necessary labor;
- wage labor and labor-power;
- necessary versus surplus labor;
- realization of surplus through sale;
- market-price deviations from labor value;
- resource scarcity, differential rent, and monopoly rent;
- regional markets, costly planetary trade, and arbitrage;
- class consequences for workers and the player colony as collective owner.

The player colony will eventually hire temporary outside workers rather than
turning ordinary colonists into wage workers. Hired workers remain a distinct
class, receive real silver or explicit in-kind compensation, and do not own
their output.

---

## Distance to the full suite

An honest assessment of how far the project is from the direction above.
Percentages are rough and weighted by *remaining effort*, not by concepts
ticked off — a Python demonstration is far cheaper than a shipped, save-safe,
performant, playable mod.

### The three components

| component | state | remaining |
|---|---|---|
| **Labor Content** (`mod/`) | 543 patch operations across six files, XML-only, validated | the in-game visual pass (display units, info-card ordering) — needs a human looking at real items; 104 generated meat defs need C# to reach |
| **Stage 0 lab** (`economy_lab/`) | 154 tests, 154 frozen metrics, three closing ledgers, a classical price system with an interpretable profit rate, six commodities and two regions, and a harness that runs 647 × 100 | two or three more economic sessions |
| **Stage 1 runtime** (`economy_mod/`) | about 115 lines of real C#: a daily tick, settlement observation, a read-only tab | essentially everything |

**The economics is the part that is nearly solved. The engineering that would
make it a playable suite is barely started.** Labor Content is one visual pass
from shipping; the simulation is maturing; the bridge between them is a stub.

### Coverage of the stated goals

| concept | in the lab | reaching a player |
|---|---|---|
| embodied and socially necessary labor | done, solved endogenously | yes — Labor Content, static figures |
| wage labor and labor-power | done | no |
| necessary versus surplus labor | done | no |
| realization of surplus through sale | done — money and labor s/v measured apart | no |
| price deviations from labor value | done — prices of production solved (docs/27) | no |
| differential rent | done | no |
| monopoly rent | **not started** | no |
| regional markets, costly trade, arbitrage | done | no |
| **class consequences; colony as collective owner** | **not started** | no |
| **hired outside workers** | **not started** | no |

Seven of ten concepts are demonstrated in Python. None of the dynamic ones
reach a player. The two bolded rows are the ones that are actually *gameplay*
rather than accounting, and neither has been started.

### Remaining phases

**Phase A — finish the economics** (~2–4 sessions). Prices of production,
the enlarged subsistence basket and turnover are all **done** (docs/27,
docs/29, docs/31). The two numbers the project reports as rates of
profit are now rates: 1.17 per day for the basic sector's uniform rate
and 0.0305 per day realized on capital advanced. What is left is a
capital-goods sector; exit and capacity depreciation; recreation in the
basket; monopoly rent. Optionally credit and bankruptcy. Then re-run
the stale sensitivity sweep.

**Phase B — scale test: DONE** (docs/33, one session). The lab was six
commodities and two regions; the harness now runs 647 commodities across 100
regions. After one method changed, cost is **linear** in both — 10.1× the
commodities costs 10.9× the time where it cost 22.5× — so the CPU miss is a
constant factor rather than a scaling failure, and a C# port at a
conservative 20× lands under 20 µs a tick. Ledgers close, determinism holds,
and the labor value solve reproduces the closed analysis exactly for all 447
commodities the generator did not contaminate.

**That finding is now closed too** (docs/35). `record_history=False` and
`history_every=k` land the runtime's memory at a flat 54 MiB at 647
commodities and 100 settlements, instead of 3.8 GB over a run, with the
laboratory's full history unchanged by default.

**Phase C — runtime port** (~6–10 sessions, the bulk of the work). Port the
model to deterministic C#; settlement profiles and regional membership; the
full economic state through save and load; a UI that makes value, price,
surplus and rent legible; integration with vanilla trade without
destabilising `MarketValue`, which drives storyteller wealth. Two
constraints are now measured rather than guessed: the daily update must be
**amortised across ticks** (about 1.1 s of C# work per simulated day at full
scale, against a 60,000-tick day), and the history design must change before
anything is ported.

**Phase D — the gameplay layer** (~4–8 sessions, least defined). Hired-worker
contracts: pawns arrive, work, are paid in silver or explicit in-kind, do not
own their output, and leave. Then the class consequences — the least
specified part of the whole project. No design document exists for what a
player actually *does* about any of it.

### Rough position: 35–40% of the suite

About twenty sessions of Stage 0 work have produced a rigorous simulation,
one shippable read-only mod, and — since `docs/33` — a measured answer to the
question that could have invalidated all of it. The remaining fourteen to
twenty-two sessions are mostly C#, UI, save compatibility and game design —
different skills, and less amenable to the design-doc-then-measure discipline
that has worked here.

The move from 30–35% is not a session's worth of code. It is that the largest
open risk turned out to be a constant factor rather than a rewrite.

### The three things most likely to derail it

1. ~~**Scale.**~~ **Retired** (docs/33), and the memory finding it left
   behind is closed too (docs/35). Nothing has replaced it on this list:
   the two remaining risks below are both about Stage 1 and neither is
   about whether the model works.
2. **The wealth coupling.** A dynamic price system feeding `MarketValue`
   changes raid strength, because storyteller wealth reads it. Getting this
   wrong makes the mod feel broken rather than interesting. Already flagged
   under "What vanilla RimWorld's economy actually does"; it constrains the
   whole Stage 1 design.
3. **Phase D has no design.** Everything else has a clear next step; "class
   consequences for the player colony" does not. Write that design document
   *early*, while the economics is still malleable, rather than discovering
   at the end that the simulation computes the wrong things for the game.

### Recommended ordering

Finish prices of production, since it resolves the authored-price wedge and
is the natural culmination of the value work. Then **jump the queue and do
the scale test** before the remaining economics sessions: if scaling forces a
structural change, it is better to find out with four mechanisms to rework
than eight. Sketch Phase D's design document soon, so the laboratory is aimed
at a game rather than at itself.

---

## Closed analysis: do not re-derive

`FINDINGS.md` is the completed and validated analysis of RimWorld's existing
value system. Treat it as closed unless new runtime evidence directly
contradicts it.

Headline result:

- embodied labor was solved for 653 defs from extraction outward;
- no market value entered the labor derivation;
- RimWorld prices extraction labor several times above fabrication labor;
- the defensible typical-good estimate is roughly 3–4×;
- the total-value-weighted estimate is roughly 14×;
- the magnitude is estimator-dependent, but the direction is robust.

Seven modelling errors were already found and fixed. Important traps include:

- inherited XML defaults are often invisible;
- recipe `<count>` values are ingredient-value units, not thing counts;
- small-volume gold/silver and nutrition recipes require conversion;
- `gestationPeriodDays` defaults to -1;
- `MarketValue` inherits rounding over 200;
- butchery has flat work against body-size-scaled yield.

Do not install a decompiler or .NET SDK. The repository contains its own
ECMA-335 metadata/IL reader in `cli_reader.py` and `dump_method.py`.

---

## Labor Content mod

Purpose: two read-only info-card stats on producible things:

- extraction labor;
- fabrication labor.

Constraints:

- no gameplay change;
- no save impact;
- no Harmony;
- no assembly;
- RimWorld 1.6;
- graceful behavior with any combination of official expansions.

Validated scope:

- 543 XML-backed defs can be patched;
- all 543 XPath targets were previously validated;
- 104 generated meat defs have no XML node and remain a v1.1 gap.

### Current uncommitted packaging work

The working tree contains deliberate Labor Content changes that predate the
Stage 0 commits. Preserve them:

- `make_mod.py` now splits patches by Core and each expansion;
- the old combined `mod/Patches/SNLT_LaborContent.xml` is removed;
- six generated patch files replace it;
- expansion files use `PatchOperationFindMod` with expansion display names;
- all six patch files contain 543 unique operations in total;
- `About.xml` now uses the public name **Labor Content** and a parka-led
  description;
- the fabrication stat description says “several times,” not an unqualified
  14×.

These changes were XML-parsed and ownership-checked but not committed. Do not
mistake them for unrelated dirt or discard them.

The required in-game visual pass is still incomplete. Display units and info
card ordering must be decided by looking at real items in game. Current units
remain work-seconds. Do not change them purely by reasoning.

---

## What vanilla RimWorld's economy actually does

The installed target is RimWorld **1.6.4871 rev590**.

Vanilla contains material trade transactions but not a persistent market
economy:

- `MarketValue` is authored or recursively calculated from input prices plus
  `workAmount × 0.0036` silver per tick;
- normal trade begins around 1.4× MarketValue when the player buys and 0.6×
  when the player sells, then applies negotiation, difficulty, and trader
  modifiers;
- settlement stock is randomly generated from `StockGenerator` XML rules;
- settlement stock is discarded and regenerated every 30 days;
- player sales enter the current temporary stock but do not affect later
  production, demand, capacity, or prices;
- settlements have no persistent population, consumption, industry, input
  requirements, wages, investment, or economic specialization;
- surface and deep deposits are locally finite, but scanners repeatedly create
  new opportunities;
- deep drills can fall back to effectively unlimited base stone.

Keep vanilla `MarketValue` separate from the future dynamic `MarketPrice`.
`MarketValue` also drives storyteller wealth and other balance systems, so
making it volatile by default would couple price bubbles to raid strength.

---

## Economy design decisions already made

### Four separate ledgers/concepts

Never collapse these into one number:

1. **Labor value:** socially necessary labor embodied in a commodity.
2. **Market price:** current exchange price.
3. **Surplus value:** living labor beyond the reproduced value of labor-power.
4. **Rent:** income from ownership of scarce or unusually productive natural
   conditions.

Money profit is also not identical to surplus value. A commodity can contain
surplus labor and fail to realize it during a glut.

### Market topology

Markets clear regionally. Planetary trade is possible but expensive,
capacity-limited, risky, and delayed.

This resolves the scale problem:

- a player colony can dominate its local market;
- the same output barely affects distant regions;
- price differences create arbitrage opportunities;
- arbitrage consumes route capacity and pushes prices toward convergence;
- roads, caravans, pods, gravships, danger, and faction access can matter.

There are no hard regional borders. Any trade is possible when the spread
covers freight and risk.

### Socially necessary labor

The planned operational definition is output-weighted labor per unit among
active, normally functioning producers. This is an **average** production
condition.

Rent and market price may instead depend on the **marginal** producer required
to satisfy demand. The UI must label the two reference points separately:

- labor value reference: average socially necessary conditions;
- price/rent reference: marginal supply conditions.

### Resource accounting

- renewable resources have sustainable flows and possible overuse;
- minerals use finite reserve tranches with different grades;
- depletion moves extraction toward higher-labor marginal reserves;
- differential rent belongs in the money/rent ledger, not labor value;
- vanilla infinite base-stone drilling must become a large explicit bedrock
  reserve or be labelled as an open external reservoir.

### Mod compatibility

Use a closed default. Auto-classify a modded good only when its mapping is
unambiguous. Otherwise it remains outside the simulated economy, retains
vanilla behavior, and is labelled **unmodelled commodity**. It must not silently
satisfy simulated material demand.

---

## Stage 0 implementation

Stage 0 is a dependency-free deterministic Python laboratory. It exists to
validate economic behavior before RimWorld runtime work.

Locations:

- `economy_lab/model.py` — market, region, producer, route, shipment, and
  ledger mechanics;
- `economy_lab/scenarios.py` — seeded scenarios;
- `economy_lab/__main__.py` — JSON scenario runner;
- `tests/test_economy_lab.py` — behavioral and accounting tests;
- `economy_lab/README.md` — current scope and commands;
- `docs/06-stage0-economy-lab.md` — short design note;
- `docs/07-accounted-input-predictions.md` — forecasts, recorded before the fact;
- `docs/08-accounted-input-design.md` — process-model decisions and alternatives;
- `docs/09-accounted-input-results.md` — what the forecasts got wrong and why.
- `docs/10-upstream-observation-results.md` — upstream metrics, hysteresis
  investigation, and observation limits.
- `docs/11-upstream-production-control.md` — demand-control decision and
  rejected alternatives, recorded before implementation;
- `docs/12-upstream-production-control-results.md` — complete 53-metric delta
  table and acceptance rationale;
- `docs/13-cost-floor-and-investment-design.md` — cost floor, construction-fund
  investment, and buffer-deficit investment decisions;
- `docs/14-cost-floor-and-investment-results.md` — 53-metric comparison,
  prediction scorecard, convergence verification;
- `docs/15-resource-reserves-design.md` — finite reserves, grade depletion,
  marginal extraction cost, and differential rent decisions;
- `docs/16-resource-reserves-results.md` — prediction scorecard, depletion
  scenario timeline, permanently displaced inventory explanation;
- `docs/17-labor-power-and-surplus-design.md` — the wage relation: subsistence
  basket, labor supply, surplus ledger, treatment of the old unit cost, and
  the exact-stationarity floating-point engineering;
- `docs/34-history-detail-design.md` — history as an optional output,
  and the claim about what reads it that turned out to be false;
- `docs/35-history-detail-results.md` — memory flat at ~60 MiB instead
  of 3.8 GB over a run, and the material ledger stopped reading its own
  report to find its opening stock;
- `docs/32-scale-test-design.md` — the size question, the budget fixed
  before measuring, and the depth histogram that shaped the whole test;
- `docs/33-scale-test-results.md` — linear after one method changed,
  memory as the architectural failure, and the value solve validated at
  447 commodities;
- `docs/30-turnover-design.md` — profit charged against capital
  advanced rather than consumed, turnover read off each commodity's
  own inventory life, and the correction of `docs/29`'s envelope
  recorded before measuring;
- `docs/31-turnover-results.md` — the rate is 1.17 per day and the old
  number is the gross markup; realized turnover is 56.8 days because
  the final product's stock is in no cost flow; three sections that
  are corrections rather than results;
- `docs/28-enlarged-subsistence-basket-design.md` — clothing and
  medicine from the closed analysis, the powered tailoring bench that
  makes chemfuel basic, and the prediction that this would *not* be
  enough, recorded before it was measured;
- `docs/29-enlarged-subsistence-basket-results.md` — every ratio built
  on v falls 30% and the value rate of profit 2%; the rank-one identity
  breaks; and the constraint is RimWorld's productivity, not the
  bundle;
- `docs/26-prices-of-production-design.md` — the classical eigen-system,
  the physical wage closure, the omission of fixed capital, and the
  hand-derived predictions recorded before any code existed;
- `docs/27-prices-of-production-results.md` — meals as the only basic
  commodity, the corn-model profit rate, the aggregate invariance
  failure, and why the subsistence basket is now a prerequisite;
- `docs/25-stage0-arc-summary.md` — the narrative summary of the whole
  Stage 0 arc: what each layer measured, the three thesis-relevant
  results, the wrong predictions, and the standing caveat on every
  ratio built on v;
- `docs/23-constant-capital-and-the-overhead-design.md` — fixed capital,
  the reclassification of the operating overhead, and the c/v/s ledger
  decided in advance;
- `docs/24-constant-capital-and-the-overhead-results.md` — the overhead
  measured as the authored-price wedge, and surplus produced against
  surplus realized;
- `docs/21-competitive-transmission-design.md` — the cost-aware price
  anchor, cost-weighted order allocation, and the cost-competition
  scenario decided in advance;
- `docs/22-competitive-transmission-results.md` — the value/price contrast,
  transmission strength, and the overhead residual named as the next
  structural problem;
- `docs/19-endogenous-labor-values-design.md` — the value equation, the
  iterative solve, output-weighted social scope, and the technique-change
  scenario decided in advance;
- `docs/20-endogenous-labor-values-results.md` — validation against the
  closed analysis, relative surplus value, and the value/price divergence;
- `docs/18-labor-power-and-surplus-results.md` — s/v and its determination,
  prediction scorecard, the glut-as-layoff finding, wage-push non-propagation.

Commits:

- `54d88ce` — Add deterministic Stage 0 economy laboratory
- `d284af9` — Report Stage 0 shock extrema
- `5ae57f7` — Freeze Stage 0 behavior before input-output production
- `f2c490c` — Add Stage 0 parameter sensitivity harness
- `cae1ba2` — Record pre-process behavioral predictions
- `863ee42` — Record accounted-input design decisions before implementing
- `f52fcd0` — Replace free production with accounted input-output processes
- `57b05ed` — Add process-level material-balance tests and input-shortage scenario
- `98ae17e` — Record accounted-input results
- `e2a7c43` — Freeze newly observed upstream behavior
- `097e40c` — Document the upstream hysteresis control bug
- `cbeb720` — Decide damped upstream replenishment control
- `c028cd6` — Add damped demand-led production planning
- `3f9c20b` — Record demand-led production deltas
- `05996ae` — Refresh baseline for demand-led replenishment
- `a1e95db` — Record long-run producer-loss convergence
- `a3fcfe7` — Record cost-floor and investment design decisions
- `e0e3dc7` — Add cost floor: producers pay for inputs via effective unit cost
- `e513b0e` — Make capacity investment consume silver
- `9f9825b` — Add buffer-deficit investment motive
- `9867014` — Record cost-floor and investment results
- `faa554b` — Refresh baseline for cost floor and buffer investment
- `34bf3ba` — Record resource reserve and differential rent design decisions
- `6eed091` — Add finite resource reserves with grade depletion and differential rent
- `aa22edd` — Add depletion scenario and reserve tests
- `d640485` — Record resource reserve results
- `13ec465` — Record labor-power and surplus ledger design decisions
- `4e923fd` — Add wage-relation machinery: worker cash, basket, labor pool, surplus ledger
- `27af376` — Wire the wage relation into the circuit: meals, wages, and the surplus ledger
- `5985878` — Record labor-power results: nine of fifty-three metrics moved, s/v is 38.344
- `ecf757c` — Refresh baseline for the wage relation
- `1b74e6d` — Freeze newly observed labor and subsistence quantities
- `0c5bbf6` — Record endogenous labor value design decisions
- `9426caf` — Solve labor values endogenously from the process graph
- `fc4e06d` — Add technique-change scenario and endogenous value tests
- `36ac2a3` — Freeze ten newly observed labor value quantities
- `c3db687` — Record endogenous labor value results
- `a475152` — Record competitive transmission design decisions
- `a9c3016` — Part A: the price anchor reads cost
- `9826489` — Part B: the order book goes to the cheaper producer
- `577c869` — Refresh baseline for competitive transmission
- `213d1cd` — Freeze ten newly observed competitive transmission quantities
- `77c3078` — Record competitive transmission results
- `87ac0cc` — Record constant capital and overhead design decisions
- `7bd916c` — Fixed capital transfers its value to the product
- `83a780a` — Add the value ledger: constant capital and the price wedge
- `73d115a` — Refresh baseline for fixed capital
- `7102ca4` — Freeze sixteen newly observed value ledger quantities
- `1f48794` — Record constant capital results

### Current vertical slice

The model has a four-commodity circuit, two regional markets, and one
expensive planetary route:

```
chemfuel ──┬──> psychoid farm ──> psychoid leaves ──> drug lab ──> yayo
           └────────────────────────────────────────────^
provisioners ──> meals ──> workers ──> labor-power ──> every producer
```

Meals are the subsistence commodity (MealSimple: reference 15, 305 embodied
ticks); the provisioners' raw-food feedstock sits outside the boundary like
chemfuel's organic inputs.

It supports:

- accounted input-output production: producers own a `Process` and must source
  real inventory; one that cannot is rationed, not subsidised;
- **cost floor**: producers' effective unit cost includes input prices at
  current regional rates, driving the utilization curve; the drug lab
  curtails on cost before running out of physical inputs;
- demand-led production planning: wanted output follows current final and
  productive outflow plus a damped correction toward material stock targets;
- daily production and price-sensitive consumption;
- persistent regional inventory and cash;
- damped local price formation from stocks and unmet demand;
- costly, delayed, capacity-limited arbitrage;
- destruction of productive capacity, upstream or downstream;
- **construction-fund investment**: capacity investment consumes silver from
  the regional pool at `construction_cost_multiplier × effective_unit_cost`
  per unit of daily capacity;
- **buffer-aware investment**: when a commodity's stock is persistently below
  target and surplus capacity cannot close the gap within
  `buffer_refill_horizon_days`, additional capacity is built;
- **finite resource reserves**: extraction producers draw from a bounded
  regional endowment with ordered grades; when the cheapest grade exhausts,
  the marginal cost rises and the utilization curve responds;
- **differential rent**: the cost advantage of infra-marginal regions over
  the most expensive active extractor, tracked as a separate quantity in the
  ledger (not collapsed into labor value or profit);
- **the wage relation**: workers are paid the subsistence basket (2 meals)
  at current regional prices; the wage enters effective unit cost through
  the cost-floor machinery; silver cycles producer → wage → worker → basket
  purchase → producer revenue and conserves exactly;
- **a fixed regional labor pool** with pro-rata rationing when planned
  labor exceeds it (never binding in the seeded scenarios);
- **the surplus ledger**: living, necessary, and surplus labor in
  work-ticks per region, observational, with the silver wage bill and
  basket shortfall recorded beside them — money profit is not surplus
  value, and the money wage is not necessary labor;
- **fixed capital that transfers value**: each sector carries its real
  RimWorld building (`DrugLab`, `HydroponicsBasin`, `BiofuelRefinery`,
  `ElectricStove`) in both silver and embodied labor, depreciating by use
  over a service life. This repairs the omission `FINDINGS.md` recorded in
  vanilla — where fixed capital transfers nothing — and measures it as
  0.353% of constant capital;
- **the value ledger**: c (circulating plus fixed), v, and s in work-ticks,
  with the organic composition and the value rate of profit. A third
  closing identity beside material and silver: value of output = c + v + s;
- **the price decomposition**: every unit's price split into inputs, wages,
  capital consumed, and the **unattributed wedge** — the gap between
  RimWorld's authored price level and anything the model can account for.
  Surplus is reported as two readings that name their assumption, never as
  a single number;
- **a cost-aware price anchor**: the anchor moves with the sector's
  output-weighted average cost relative to its seeded cost, blended by
  `competitive_price_intensity` (default 0.5, and 0 restores the
  authored-reference anchor exactly). Upstream cost now propagates to
  downstream prices, which `docs/16` recorded as impossible;
- **cost-weighted order allocation**: a commodity's order book is shared
  among its producers by `(cost/cheapest)^-epsilon`, capped by each
  producer's own limit, with the residual redistributed by water-filling.
  `competitive_share_elasticity = 0` is a bit-exact no-op;
- **endogenous labor values**: transferred labor plus living labor per unit
  of output, solved from the process graph by iteration (so a cyclic graph
  is answerable and a non-productive one fails loudly), aggregated as total
  labor over total output across active producers. Per-region individual
  values sit beside the social value, which is where the average/marginal
  distinction becomes visible. `Commodity.labor_value` keeps the authored
  `FINDINGS.md` figure, untouched, for comparison;
- explicit commodity and silver balance checks, with productive consumption
  booked separately from final consumption, investment spending and reserve
  depletion tracked.

### Process-model decisions — read before changing

`docs/08-accounted-input-design.md` records each choice and its alternatives.
The load-bearing ones:

- **joint products are apportioned by mass**, not by value, because value
  apportionment would be circular in a laboratory whose purpose is to let
  prices form from material conditions. Implemented and unit-tested; no current
  process actually has a byproduct;
- **partial input availability is proportional** — 60% of inputs means 60% of
  output. `all_or_nothing` exists as a parameter. Proportional is the default
  because a regional producer is an aggregate of many small runs, and because a
  discontinuity here would manufacture limit cycles that look like economic
  results;
- **production is simultaneous** against opening stock, so results do not
  depend on producer list order. Cost: one day per stage of propagation delay;
- **contention is pro-rata by requirement**, single pass. A producer throttled
  by another input leaves slack unallocated that day; the slack stays in
  inventory, so nothing is destroyed and the ledger closes;
- **inventory targets scale by throughput demand** (final plus derived).
  Without this, intermediate goods would have a target of zero and collapse to
  the price floor;
- **freight goes to the widest spread first**, not alphabetically.

Per-unit ratios and reference prices are read from RimWorld defs. One link is a
flagged stylization: vanilla drug labs and psychoid fields do not consume
chemfuel. It is there because the circuit needs a commodity consumed by more
than one producer, and contention is where accounting bugs hide.

**Cost floor and investment decisions** are in
`docs/13-cost-floor-and-investment-design.md`. The load-bearing additions:

- **effective unit cost includes input prices**: `Producer.unit_cost` is now
  operating overhead only; `effective_unit_cost(prices)` adds inputs at
  current regional prices. The drug lab's operating overhead is zero (its
  prior 14.0 was entirely consumed by the 15.66 input cost);
- **investment consumes silver**: `construction_cost_multiplier` (default 60)
  days of effective cost per unit of daily capacity, deducted when
  commissioned. If the region cannot afford it, the project scales down;
- **buffer-deficit investment**: when stock is below target and surplus
  capacity cannot refill within `buffer_refill_horizon_days` (default 60),
  additional capacity is built. The signal is proportional, not threshold;
- **input purchases are internal**: the silver payment for inputs stays within
  the regional pool (the producer buys from its own region). The behavioral
  effect comes through the utilization curve seeing a higher cost, not through
  a silver movement between entities.

**Resource reserve and rent decisions** are in
`docs/15-resource-reserves-design.md`. The load-bearing additions:

- **regional reserves with ordered grades**: each region has a
  `ResourceReserve` per extraction commodity with grade tranches ordered
  cheapest first. All extraction producers in a region share the same reserve;
- **dynamic marginal cost**: each day, extraction producers' `unit_cost` is
  updated to the marginal grade's cost before the utilization curve is
  evaluated. The cost floor machinery picks this up with no API change;
- **reserve rationing**: when total wanted extraction exceeds remaining
  reserve, all extraction producers are scaled down pro-rata;
- **differential rent**: the cost advantage of infra-marginal regions over
  the most expensive active extractor, accumulated in the ledger per commodity.
  Rent is observed, not transferred;
- **reserve depletion tracking**: `Ledger.reserve_depletion` equals production
  for extraction commodities (a testable accounting identity).

**Wage-relation decisions** are in `docs/17-labor-power-and-surplus-design.md`.
The load-bearing additions:

- **labor vs labor-power**: labor is the activity (a cost coefficient);
  labor-power is the commodity a wage buys, valued at its reproduction cost.
  Surplus value is only computable because the two are separate;
- **the wage is additive to effective cost**: the old operating overheads are
  reinterpreted as non-labor overhead. Splitting a wage out of them is
  numerically impossible (the drug lab's overhead is zero against 350 ticks
  of labor); the fat pre-wage margins implicitly contained the unpaid wage
  fund, and making labor-power a paid commodity moves that portion from
  measured profit into cost. The loud check is at seeding: any producer
  pushed below full utilization at reference prices raises;
- **wages today, bread tomorrow**: worker basket demand lags employment by
  one day, keeping the planning fixed point unchanged;
- **exact-stationarity engineering**: employment quantized to a 2^-20
  worker-day grid, power-of-two basket (2 meals) and provisioning capacity
  (1.0/day), and seeding at the exactly-repeating quantized fixed point.
  This is why the four-commodity equilibrium reports a price range of
  exactly zero rather than 1e-13;
- **s/v is closed-form at this stage**: (24000 − 610)/610 = 38.344, set by
  the working day and basket parameters plus the meal's embodied labor.
  It becomes emergent only with endogenous labor values, wage bargaining,
  or an endogenous basket — all deliberately later.

### Current calibrated behavior

- equilibrium remains exactly stable for four in-game years, now for four
  commodities including meals, with the wage circuit running daily;
- the equilibrium wage is **30 silver per worker-day**, employment is
  **0.314 worker-days/day** per region, and the rate of surplus value is
  **38.344** (labor-time ratio, constant through every shock);
- a glut equal to 25% of annual regional yayo consumption lowers the local
  price from 21 to **14.368** (shallower again — the wage raised the drug
  lab's curtailment threshold);
- the distant region only falls to **20.464**;
- arbitrage exports **11 units** before the spread closes;
- destroying 60% of regional capacity raises the price to **38.630**;
- replacement capacity restores at least 80% of baseline supply within the
  four-to-eight-quadrum target;
- post-shock upstream buffers refill to target rather than persisting as
  scar tissue (converges by day 400, identical endpoint to the pre-wage
  model);
- destroying 70% of one region's provisioning triples the meal price and
  the wage, records a 9-meal basket shortfall and forced worker savings,
  and rebuilds through ordinary investment — without moving yayo or leaf
  prices at all (wage share of cost is too small to curtail);
- all 154 tests pass;
- commodity and silver residuals close to floating-point zero for all four
  commodities, including investment spending and the wage circuit;
- identical inputs reproduce identical histories.

These are provisional gameplay targets, not empirical claims about real-world
elasticities.

### History of behavioral changes

**Accounted-input production** (`docs/09`): moved zero of thirteen original
metrics because the material constraint never binds at 20-day cover, capacity
entry was free, and gluts cannot be damped by an input constraint. But it
exposed upstream effects invisible to the yayo-only metrics: permanent
hysteresis and a 74% leaf price crash on downstream capacity loss.

**Demand-led production control** (`docs/12`): moved 39 of 53 metrics.
Resolved the glut hysteresis. Upstream prices stay at reference throughout the
glut. Producer-loss terminal values shift because investment targets follow
throughput demand.

**Cost floor and investment** (`docs/14`): moved 16 of 53 metrics. The cost
floor tightened the drug lab's margin (effective cost 15.66 vs prior 14.0),
causing the glut trough to shallow (14.34 → 14.36), recovery to accelerate
(11 → 9 days), and arbitrage volume to drop (12.38 → 11). The cost channel
pre-empts material rationing in the input-shortage scenario: the drug lab
curtails on cost before running out of leaves. Buffer-aware investment
resolves the post-shock upstream scar — prices return to reference by day 400
with stocks at their enlarged targets.

**Resource reserves and differential rent** (`docs/16`): moved zero of 53
metrics. The reserve infrastructure is invisible to existing scenarios (default
100,000-unit reserves at current operating overhead). The new depletion
scenario exercises grade transition: Dust Basin's cheap chemfuel grade (600
units) exhausts at day 100, marginal cost doubles, chemfuel price rises from
2.30 to 3.33. Downstream prices (leaves, yayo) are unaffected — the chemfuel
input share is too small (0.2/yayo, 0.05/leaf) for a 44% chemfuel price
increase to push downstream margins into curtailment. Green River earns
1,816 silver in differential rent over 300 days. All ledgers close.

**The wage relation** (`docs/18`): moved nine of 53 metrics, all through the
one designed channel (the wage in effective unit cost). The glut trough
shallowed (14.356 → 14.368) and half-recovery quickened (9 → 8 days);
producer-loss day-210 transients drifted 1–2% while the converged day-400
endpoint is identical. Equilibrium, the producer-loss peak, arbitrage, and
every upstream extremum are exactly unchanged. New findings: the glut is a
mass layoff (employment collapses to 0.0002 worker-days on day 62) that
subsistence production absorbs with a perfectly flat meal price; the
producer-loss cycle produces the first real-wage dynamics (wage 23.40 →
32.80); and wage-push does not propagate at this calibration because the
wage is ~2.7% of the drug lab's cost — the labor-side counterpart of the
chemfuel input-share finding in docs/16.

The `input-shortage` scenario exercises the material constraint: 70% of Dust
Basin's psychoid fields destroyed, leaf price up 2.6× and yayo up 1.66×.
With the cost floor, the drug lab curtails smoothly through cost rather than
waiting for physical leaf exhaustion.

Run:

```text
python -m unittest discover -s tests -v
python -m economy_lab all
python -m economy_lab input-shortage
python -m economy_lab depletion
python -m economy_lab subsistence-shock
python -m economy_lab technique-change
python -m economy_lab cost-competition
python -m economy_lab.baseline
python -m economy_lab.sensitivity
```

The sensitivity sweep has **not** been re-run since accounted inputs landed;
`sensitivity_results.csv` and `sensitivity_ranking.txt` describe the free-
production model. Re-run it once the model stabilizes, and expect the new
process ratios, derived-demand price rule, and exposed `replenishment_rate` to
change the ranking. The committed stale output covers 31 parameters; a fresh
run will include 32.

### Behavioral observation checkpoint

`economy_lab/behavior_baseline.json` freezes 65 current behavioral metrics:
thirteen final-good observations, forty upstream observations, and twelve
labor/subsistence observations. `python -m economy_lab.baseline` re-runs the
scenarios and prints reference, current value, absolute delta, and percentage
delta. It is deliberately a report rather than a pass/fail test; the 51-test
suite remains the authoritative invariant checks. Replace the reference only
with `--write-reference` after an understood behavioral change, and say why
the numbers moved in the commit message.

Current frozen headline metrics include:

- local glut trough: **14.367961** on day 66;
- distant glut trough: **20.464413** on day 80;
- local half-gap recovery: **8 days / 0.533 quadrums**;
- arbitrage exports: **11 units**;
- producer-loss peak: **38.630290** on day 119;
- 80% capacity recovery: **75 days / 5 quadrums**;
- equilibrium price range: **0** in both regions, all six commodities.

Current upstream headline observations include:

- glut leaf settlement: **1.900000 / 1,600 units**;
- glut chemfuel settlement: **2.300000 / 120 units**;
- producer-loss leaf trough: **0.693449** on day 70;
- producer-loss chemfuel trough: **1.918998** on day 69;
- producer-loss leaf terminal: **2.467308 / 1,454.371** (day 210, still in
  buffer-rebuild transit; converges to 1.900 / 1,891 by day 400);
- producer-loss chemfuel terminal: **2.917596 / 104.624** (same — converges
  to 2.300 / 151 by day 400).

Labor and subsistence observations (frozen at `1b74e6d`):

- equilibrium employment: **0.314065 worker-days/day**; wage **30 silver**;
- rate of surplus value: **38.344367** (labor-time ratio);
- meal settlement: **15.000000 / 12.751667**;
- glut employment trough: **0.000202** on day 62, meal price range **0**;
- producer-loss employment trough: **0.058332** on day 62; meal price
  cycles **11.697630 – 16.398671**.

The former glut hysteresis was a **control-law bug**, not a capacity reallocation
or ledger leak. It is resolved by the design in `docs/11`: planned output follows
intended outflow plus a 10% daily correction toward the existing material stock
target. The mutually dependent order plans converge deterministically from the
day's opening state, so production remains simultaneous. Leaves now stay at
1,600 and chemfuel at 120 throughout the glut, both at reference price.

The cash cost floor (`docs/13`, `docs/14`) does **not** replace this control.
Material planning answers how much output is wanted; the cost floor answers
whether the plan is profitable. Actual production is limited by both — the
minimum of what the demand-led plan requests and what the utilization curve
(now informed by input costs) allows.

Two interpretation notes:

- glut upstream extrema are degenerate by design: price peak and trough are
  both the reference price on day 61, and stock peak/trough both equal the
  unchanged buffer. They mean "no upstream excursion," not a timed trough;
- extending producer loss to day 660 now shows full convergence: leaves
  settle at **1.900 / 1,891** and chemfuel at **2.300 / 151**, both at
  reference price with stocks at target. The enlarged stocks reflect
  additional installed capacity from buffer-rebuild investment. The former
  permanent buffer scar (`docs/12`) is resolved.

Arbitrage is currently single-commodity by calibration, not design. Standard
freight is **3.85** after risk markup while the glut's widest intermediate spread
is about **0.2**. Falling freight or rising upstream volatility can therefore
switch multi-commodity arbitrage on abruptly, with goods competing for route
capacity.

Recovery-day metrics are quantized to daily threshold crossings. Add a
continuous complement—preferably area between the price path and baseline over
a fixed window—in a later observation session, without changing the existing
metric semantics.

`python -m economy_lab.sensitivity` deliberately runs a one-at-a-time ±10%
sweep over 31 exposed calibration parameters. It writes:

- `economy_lab/sensitivity_results.csv` — 806 detailed parameter/output rows;
- `economy_lab/sensitivity_ranking.txt` — parameters ranked by their strongest
  normalized output response.

The sweep did not reveal one overwhelmingly dominant coefficient. Daily demand
and productive capacity tied for the strongest response through arbitrage
volume; reference price and Dust Basin unit cost followed through a quantized
two-day movement in glut recovery. Investment timing and fraction most strongly
control capacity recovery. Integer scheduling makes the investment-interval
response phase-sensitive rather than smooth.

Twelve parameters produced no movement in the captured outputs at ±10%:
expectation smoothing, initial cash, investment margin threshold, labor value,
all three loss-route settings, both price clamps, River unit cost, speculative
inventory limit, and unmet-demand price pressure. These are scenario-local
findings, not proof that the parameters are globally irrelevant.

The sensitivity refactor exposed previously hard-coded coefficients through
`ScenarioParameters` while preserving every default. The baseline report
remains all-zero after the refactor and all eight tests pass.

Predicted changes from accounted-input production are frozen in
`docs/07-accounted-input-predictions.md`. The expected pattern is a shallower,
shorter glut; a higher, longer producer-loss shortage; and near-stationary
equilibrium. Compare actual changes against the prediction, but do not tune the
new model merely to make the forecast come true.

---

## Stage 1 runtime shell

Stage 1 has begun as an isolated read-only RimWorld 1.6 mod in `economy_mod`.
Commit `6794dfc` adds:

- a persistent `EconomyWorldComponent` with a 60,000-tick daily cadence;
- observation of generated world settlements;
- a read-only Economy main tab, ordered between Animals and Wildlife;
- explicit UI copy that vanilla prices remain unchanged;
- no Harmony and no gameplay mutation.

Runtime verification on RimWorld 1.6.4871 rev591 passed:

- the assembly built with zero warnings;
- the mod loaded beside Labor Content with no XML or assembly errors;
- the tab appeared and initially observed 105 settlements;
- after the player settlement appeared it observed 106;
- crossing one in-game day incremented the economy counter from 0 to 1;
- `Autosave-4.rws` serialized `completedDays=1`,
  `lastProcessedTick=60000`, and `observedSettlementCount=106`;
- all eight deterministic Stage 0 tests still pass after adding the runtime
  project.

Save serialization is confirmed. A deliberate save/reload read-back test has
not yet been completed, so do not report reload persistence as verified.

The local build toolchain is:

- .NET SDK 8.0.424 at
  `C:\Users\PintS\Documents\Codex\tools\dotnet-sdk-8`;
- target framework `net472`;
- official `Microsoft.NETFramework.ReferenceAssemblies` 1.0.3 build package;
- direct references to RimWorld's shipped managed assemblies.

The user explicitly approved installing these required build dependencies.

The mod is development-linked into RimWorld's `Mods` folder as
`SocialProductionEconomy`. The build command and overrideable game path are
documented in `economy_mod/README.md`.

This is intentionally a runtime shell, not integration of the incomplete
Stage 0 production model.

---

## Immediate next work

Steps 1–10 are **done**.

1. ~~Add `Process` definitions with material inputs, outputs, direct labor,
   capacity, and unit operating cost.~~
2. ~~Add at least three linked commodities.~~ Done as a forking circuit:
   chemfuel feeds both the psychoid fields and the drug lab.
3. ~~Require production to consume accounted inventory.~~
4. ~~Add process-level material-balance tests and an input shortage
   scenario.~~
5. ~~Make investment consume a construction fund; add cost floor and buffer
   investment.~~ Done: producers' effective cost includes input prices,
   investment costs silver, buffer deficits trigger proportional investment.
6. ~~Add finite resource reserves, grade depletion, marginal extraction cost,
   and differential rent.~~ Done: chemfuel synthesis draws from a regional
   reserve with ordered grades; differential rent tracked in the ledger.

7. ~~Add the local subsistence basket and wage labor.~~ Done: meals are the
   fourth commodity, workers are paid the basket at current prices, the
   surplus ledger separates living/necessary/surplus labor from the money
   wage bill, and the silver circuit closes. Hired-worker *contracts* (the
   player colony hiring outside workers) remain a Stage 1 gameplay concern.

8. ~~Propagate labor values endogenously through the process graph.~~ Done:
   values are solved by iteration, validated against the closed analysis
   (exact for the two input-free commodities, high by exactly the stylized
   chemfuel link for the two downstream ones), and the rate of surplus
   value is now an outcome. A technique change in the wage-goods sector
   moves it from 38.344 to 43.944 with the working day and the basket held
   fixed — relative surplus value, emergent (docs/20).

9. ~~Add competitive transmission from cost to price.~~ Done: the price
   anchor reads the sector's cost and the order book goes to the cheaper
   producer. The `docs/16` displaced-inventory artifact is resolved (the
   depletion buffer returns from 63.8% of target to 100%) and downstream
   cost-push exists for the first time. Two contrasting scenarios now
   separate value from price numerically: labor-saving moves value 12.7%
   and price 0.47%; capital-saving moves price 14.3% and value not at all
   (docs/22).

10. ~~Give the operating overhead an economic interpretation.~~ Done, and
    the answer is negative in a useful way: it is the gap between
    RimWorld's authored price level and anything the model can account
    for. Fixed capital — now implemented from the real building data —
    explains 0.05% of it; two-thirds of the upstream price remains
    unattributed. The wedge is reported under its own name, surplus is
    given as two readings that state their assumption, and the classical
    magnitudes are computable at last: organic composition 20.67, value
    rate of profit 1.77 (docs/24).

**Scope note:** for where these sit against the whole mod suite — the
runtime port and the gameplay layer — see "Distance to the full suite"
above. The scale question that section carried as its largest open risk is
**retired** (step 14); what replaces it is narrower and known.

11. ~~Prices of production.~~ Done as an observation, and the result is
    negative in a way that reorders everything behind it. The classical
    system solves — `p = (1 + r)Mp` with the subsistence basket folded
    into the input matrix — and the uniform profit rate comes out of the
    technique and the real wage with no authored price in the derivation.
    But **meals is the only basic commodity** in the circuit, so `r` is
    fixed by the wage good alone and reduces to a corn model:
    `r = 38.344`, which is the rate of surplus value arrived at from the
    price side. A gross markup of 39.34 then meets yayo's two-stage input
    chain twice, pricing it at **71.6×** its authored ratio to meals.
    Nothing is wrong with the arithmetic; the input to it is. Also
    measured: total price can be made to equal total value, and total
    profit is then 1.526× total surplus (docs/27).

    Nothing feeds back. Prices, costs and the order book are untouched and
    the frozen reference did not move by a digit.

12. ~~An enlarged subsistence basket.~~ Done, and it settled the question
    `docs/27` opened by answering it in the negative. Clothing
    (`Apparel_BasicShirt`, 1620 ticks) and medicine (`MedicineHerbal`,
    400) join meals, every figure from the closed analysis. Necessary
    labor rises from 2.5% to **3.6%** of the working day; s/v falls
    **38.30 → 26.71**, c/v **20.67 → 14.42**, and the value rate of profit
    only **1.768 → 1.733**, because `c` is fourteen times `v` either way.
    The uniform profit rate falls **38.34 → 24.62** and yayo's deviation
    from its authored price **71.6× → 38.7×** — halved, and still
    unusable (docs/29).

    Two structural gains beyond the numbers. The tailors' bench is
    powered, which makes **chemfuel a basic commodity** and breaks the
    rank-one identity that had kept `r` exactly equal to s/v; the model
    has reached the general Sraffa case, with a control scenario that
    restores the identity when the link is removed. And `docs/24`'s
    refusal to read the money/labor agreement for meals as evidence can
    be **retired**: with three goods in the basket that identity
    dissolves and the wage goods straddle the labor-time rate instead.

    **The caveat this was meant to remove is only partly removed, and the
    reason is a finding rather than a shortfall.** `r ≈ T / (basket
    labor) − 1`, and one provisioner's working day feeds **39.3 workers**
    on RimWorld's own numbers. A profit rate near 1 needs a basket
    embodying half a working day — 39 meals a day. The
    `generous_basket` scenario bounds it: an indefensible bundle still
    leaves s/v above eleven. The rate of surplus value this project
    reports is roughly the game's own.

13. ~~Turnover.~~ Done, and both of the project's rates of profit are now
    rates. Capital is advanced for one production period plus the
    commodity's own inventory life, so `p_i = (1 + r τ_i)(M_i · p)`. The
    price system's rate is **1.1726 per day** and the number `docs/26`
    through `docs/29` reported survives as the **gross markup**, 24.62.
    The value ledger gains a rate of profit on capital *advanced* —
    **0.0305 per day** — beside the flow ratio it has printed since
    `docs/23`, and the two differ by the realized turnover.

    **Uniform turnover moves no relative price.** `1 + rτ` is a scalar,
    so it rescales the rate and redistributes nothing; the invariance is
    asserted bit-exactly, which is why the uniform case is solved in
    closed form rather than searched for. Only *differential* turnover
    moves a price, and `perishable_meals` — RimWorld's simple meals rot
    after four days — lifts the rate to 2.08 and widens every deviation,
    yayo from 54 meals to 476 (docs/31).

    Realized turnover is **56.8 days**, not the 21 the price system
    assumes, because yayo is nobody's input: its finished stock is 63% of
    all commodity capital and appears in no cost flow. Take it out and
    the figure lands at 22.1.

    Also: a **third seeding defect** of the `docs/29` family — stocks were
    seeded from the global inventory target rather than the commodity's
    own, invisible while they were equal. Caught only because the
    stationarity invariant is exact rather than tolerance-based.

14. ~~The scale test.~~ Done in one session, and the answer is better
    than expected for a different reason than expected (docs/33).
    `economy_lab/scale.py` builds an economy of any size from the real def
    population; it runs **647 commodities across 100 regions**.

    **The architecture is linear**, in commodities and in regions, after
    one method changed: `throughput_demand` is O(producers) and was being
    called once per commodity inside a fixed point, so a day was
    O(commodities × producers) several times over. `throughput_demands`
    computes them all in one pass. 10.1× the commodities now costs 10.9×
    the time where it cost 22.5×.

    **CPU fails in Python and would pass in C#.** 22.3 s per simulated day
    at full scale against a 50 ms budget — but linear, and amortisable
    across a 60,000-tick day. A conservative 20× port lands under 20 µs a
    tick.

    **Memory fails architecturally.** `Economy.history` grows ~16 MiB per
    simulated day at full scale, 3.8 GB over a run. That is a design
    decision, not an implementation cost, and it is now on the critical
    path for the port.

    **Everything correctness-shaped held**, and one result came free: run
    at 647 commodities rather than four, the labor value solve reproduces
    the closed analysis's embodied labor **exactly** for all 447
    commodities the generator did not contaminate. `docs/20` validated it
    on four.

    Also found: the equivalence test for the new batch method caught a
    one-ulp divergence the reasoning had missed, because CPython's `sum`
    compensates its float error and a `+=` loop does not. The frozen
    reference did not notice — it rounds to six decimals — and the test
    did.

15. **Next — two small sessions, then the economics resumes.**

    *~~Reshape `Economy.history`~~* — done (docs/35).
    `record_history=False` and `history_every=k`, defaulting to today's
    behaviour, put the runtime's memory at a flat 54 MiB instead of 3.8
    GB over a run. The design's claim that nothing reads history back was
    wrong — `commodity_balance` took its opening stock from `history[0]`
    — and the opening stock is state now.

    *`_allocate_orders`* is now the largest single cost in a simulated day.
    The **bit-identical** part is done: the commodity grouping is hoisted
    out of the fixed point instead of rebuilt on every iteration, one-
    element sectors skip their sort, and `id()` calls halved from 191,796
    to 94,260 over three days. It bought little — the cost is per-sector
    dictionary construction, not the bookkeeping around it.

    **The remaining win is not bit-identical, and that is the decision the
    session has to make.** The overwhelmingly common case is a sector with
    one producer, where the whole water-filling apparatus reduces to
    `min(wanted, ceiling)` — except that the loop computes
    `remaining * w / total_weight` with `total_weight == w`, and
    `x * w / w` is not exactly `x` in floating point. A fast path would
    move results in the last bits, so it needs a design document that
    says whether that is acceptable and a reference refresh that explains
    the movement. It is not a refactor.

    Then the economics, unchanged in order:

    *A capital-goods sector (Department I).* Machinery as a produced
    commodity that investment consumes materially. Building capacity still
    spends silver without consuming anything, which is the last place
    something appears from nothing. Since `docs/27` it has a second
    reason to exist: it is what would let fixed capital into the price
    system — now 3.5% of the capital advanced, where its depreciation was
    0.05% of cost.

    *Capacity depreciation and mothballing*, so that competition is for
    survival and not only for orders. Today a producer that loses the
    order book keeps its capacity forever, keeps inflating throughput
    demand and inventory targets through the full-capacity convention,
    and would take its share straight back. Exit is also what would let
    the social labor value migrate to a superseded technique rather than
    resting at the mix average. Time-based depreciation belongs here too,
    since idle capacity is its subject.

    *Recreation in the basket*, deliberately deferred in `docs/28` §2.2.
    The obvious candidate is yayo, which would make the model's own final
    good basic and create a wage-price loop through the commodity every
    scenario is measured on. Worth doing on its own, not alongside
    something else.

    Other candidates: labor content of resource grades; wage deviations
    from the value of labor-power; absolute rent; credit and bankruptcy.

The sensitivity sweep has not been re-run since the cost floor landed;
`sensitivity_results.csv` describes the free-production model. Re-run it once
the model stabilizes. New parameters to include: `construction_cost_multiplier`,
`min_investment_capacity`, `buffer_refill_horizon_days`,
`chemfuel_reserve_per_region`, `chemfuel_expensive_cost_multiplier`,
`meal_capacity_per_day`, `meals_per_worker_day`, `ticks_per_worker_day`,
`labor_pool_worker_days`, `worker_initial_cash_days`. Note that
`meals_per_worker_day` and `meal_capacity_per_day` are part of the
exact-stationarity engineering (docs/17 §7): a ±10% perturbation will break
the exact zero equilibrium range by design, which the sweep should report,
not "fix".

Two safe tracks can now proceed independently:

1. In Stage 0, replace free single-output production with accounted
   input-output processes in the order above.
2. In Stage 1, generate deterministic settlement profiles and regional
   membership, persist them, and display them read-only. Do not run a claimed
   production economy or alter vanilla prices until the Stage 0 material
   circuit is credible.

Before any behavior change, run the baseline reporter once. After the change,
run it again and record the deltas before deciding whether to update the
reference. Run the sensitivity sweep deliberately after the model stabilizes;
it is not intended for per-commit testing.

---

## Known Stage 0 omissions

- ~~capital-goods costs for capacity investment~~ — done;
- ~~producers paying cash for their inputs~~ — done via effective unit cost;
- ~~labor value propagated endogenously through processes~~ — done;
  `Commodity.labor_value` deliberately keeps the authored `FINDINGS.md`
  figure and the solved values live on the `Economy` beside it, so the two
  can be compared rather than conflated;
- ~~competitive transmission from cost to price~~ — done (`docs/22`);
  transmission strength is now a measured quantity, and it is small for
  labor-saving change because wages are 2-4% of money cost;
- competitive *exit*: a producer that loses the order book keeps its
  capacity indefinitely, so competition is for orders and not survival;
- ~~an economic interpretation for the `unit_cost` operating overhead~~ —
  done, and the answer is that it is the authored-price wedge (`docs/24`);
  it is now named and measured, but not removed, and removing it means
  abandoning `MarketValue` as the price anchor;
- a capital-goods sector: building capacity spends silver but consumes no
  material, so capital stock still appears from nothing;
- equalization of profit rates across sectors: *computed* as an
  observation since `docs/27`, but not adopted — the cost anchor still
  freezes each sector's calibrated rate of profit rather than
  equalizing it. Enlarging the basket halved the deviations without
  making them usable (docs/29); turnover is the next candidate;
- ~~turnover~~ — done (`docs/31`). Capital is advanced for one
  production period plus the commodity's own inventory life, the price
  system's rate is 1.17 per day against a gross markup of 24.62, and
  the ledger reports a rate of profit on advances (0.0305/day) beside
  the flow ratio it has printed since `docs/23`;
- labor content of resource grades: a poorer deposit costs more silver but
  no more labor, so depletion moves cost and rent but not value;
- joint products in an actual scenario — the mass apportionment rule is
  implemented and unit-tested, but every current process has one output;
- ~~resource reserves, grades, and differential rent~~ — done for chemfuel;
  absolute (monopoly) rent is still absent;
- ~~labor supply and wages~~ — done: fixed regional pool, wage at the value
  of labor-power, surplus ledger;
- ~~the subsistence basket~~ — done, and enlarged to food, clothing and
  medicine (docs/29). Necessary labor is 3.6% of the working day rather
  than 2.5%, so the value of labor-power is still understated but the
  remaining understatement is small: shelter is under 20 ticks a
  worker-day and recreation was deferred deliberately. s/v is 26.71 and
  the honest reading is that it is roughly RimWorld's own figure;
- wage deviations from value: bargaining, the reserve army, worker mobility;
- credit, bankruptcy, and liquidity-constrained consumption (workers are
  cash-constrained on the basket, but nothing else is);
- capacity depreciation or mothballing (idle surplus from buffer investment
  persists indefinitely);
- individual producer cash accounts and transfer pricing (wages are paid
  from the regional pool; producer-level exploitation accounts need
  producer-level cash);
- more than six commodities or two regions;
- RimWorld save/UI/runtime integration.

Production consumes accounted inventory and pays a cost floor that now
includes wages. Capacity investment consumes silver. Extraction draws from
finite reserves with grade depletion and differential rent. Workers are paid
the reproduction cost of labor-power and buy real meals; surplus labor is
measured, not asserted. All material and silver ledgers close, with silver
now cycling rather than flowing one way. labor values are solved from the
process graph and reproduce the closed analysis exactly, save for the one
link `docs/08` declared stylized.

The reproduction circuit is closed in both directions: goods are made from
goods and labor, and labor is reproduced by goods. Cost reaches price, the
cheaper producer wins custom, and three ledgers now close to floating-point
zero — material, silver, and value.

What it lacks is a price system of its own. Two-thirds of every upstream
price is a wedge the model cannot account for, because prices are anchored
to RimWorld's authored `MarketValue` while costs are built from a wage the
authored prices never knew about. Every other component has been carved out
and named; what remains is the seam `FINDINGS.md` found, and closing it
means deriving prices rather than importing them.

---

## Working rules

- Keep commits small.
- Preserve unrelated working-tree changes.
- Ask before adding dependencies.
- Do not re-litigate the closed labor figures without new evidence.
- Keep labor value, market price, surplus, profit, and rent distinct.
- Express calibration tests as ratios of regional flows, not arbitrary item
  counts.
- Prefer deterministic scenarios and invariant checks before adding features.
- Update this file after every meaningful design decision or implementation
  checkpoint.
