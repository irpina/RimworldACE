# Project handoff — Labor Content and Economy

**Last updated:** 2026-08-24  
**Repository:** `C:\Users\PintS\OneDrive\Documents\Projects\snlt`  
**GitHub:** `https://github.com/irpina/RimworldACE`  
**Current branch:** `master`  
**Latest Stage 0 model commit:** `6eed091` (resource reserves + differential rent)
**Behavioral baseline:** `faa554b` (53 metrics, unchanged by reserves)
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
  scenario timeline, permanently displaced inventory explanation.

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

### Current vertical slice

The model has a three-commodity circuit that forks, two regional markets, and
one expensive planetary route:

```
chemfuel ──┬──> psychoid farm ──> psychoid leaves ──> drug lab ──> yayo
           └────────────────────────────────────────────^
```

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
- fixed labor value beside dynamic market price;
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

### Current calibrated behavior

- equilibrium remains exactly stable for four in-game years;
- a glut equal to 25% of annual regional yayo consumption lowers the local
  price from 21 to **14.356** (shallower than previously — the drug lab now
  curtails on cost during the glut);
- the distant region only falls to **20.464**;
- arbitrage exports **11 units** before the spread closes;
- destroying 60% of regional capacity raises the price to **38.630**;
- replacement capacity restores at least 80% of baseline supply within the
  four-to-eight-quadrum target;
- post-shock upstream buffers refill to target rather than persisting as
  scar tissue (converges by day 400);
- all 38 tests pass;
- commodity and silver residuals close to floating-point zero for all three
  commodities, including investment spending;
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

`economy_lab/behavior_baseline.json` freezes 53 current behavioral metrics: the
original thirteen final-good observations plus forty upstream observations.
`python -m economy_lab.baseline` re-runs the scenarios and prints reference,
current value, absolute delta, and percentage delta. It is deliberately a
report rather than a pass/fail test; the 25-test suite remains the
authoritative invariant checks. Replace the reference only with
`--write-reference` after an understood behavioral change, and say why the
numbers moved in the commit message.

Current frozen headline metrics include:

- local glut trough: **14.356472** on day 66;
- distant glut trough: **20.464413** on day 80;
- local half-gap recovery: **9 days / 0.6 quadrums**;
- arbitrage exports: **11 units**;
- producer-loss peak: **38.630290** on day 119;
- 80% capacity recovery: **75 days / 5 quadrums**;
- equilibrium price range: **0** in both regions.

Current upstream headline observations include:

- glut leaf settlement: **1.900000 / 1,600 units**;
- glut chemfuel settlement: **2.300000 / 120 units**;
- producer-loss leaf trough: **0.693449** on day 70;
- producer-loss chemfuel trough: **1.918998** on day 69;
- producer-loss leaf terminal: **2.507273 / 1,425.509** (day 210, still in
  buffer-rebuild transit; converges to 1.900 / 1,891 by day 400);
- producer-loss chemfuel terminal: **2.934490 / 103.895** (same — converges
  to 2.300 / 151 by day 400).

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

Steps 1–6 are **done**.

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

7. **Next economic feature:** add the local subsistence basket and
   hired-worker contracts.

The sensitivity sweep has not been re-run since the cost floor landed;
`sensitivity_results.csv` describes the free-production model. Re-run it once
the model stabilizes. New parameters to include: `construction_cost_multiplier`,
`min_investment_capacity`, `buffer_refill_horizon_days`,
`chemfuel_reserve_per_region`, `chemfuel_expensive_cost_multiplier`.

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
- labor value propagated endogenously through processes; `Process.direct_labor`
  is recorded but `Commodity.labor_value` remains the static `FINDINGS.md`
  figure;
- joint products in an actual scenario — the mass apportionment rule is
  implemented and unit-tested, but every current process has one output;
- ~~resource reserves, grades, and differential rent~~ — done for chemfuel;
  absolute (monopoly) rent is still absent;
- labor supply and wages;
- the poverty/subsistence basket;
- credit, bankruptcy, and liquidity-constrained consumption;
- capacity depreciation or mothballing (idle surplus from buffer investment
  persists indefinitely);
- individual producer cash accounts and transfer pricing;
- more than three commodities or two regions;
- RimWorld save/UI/runtime integration.

Production consumes accounted inventory and pays a cost floor. Capacity
investment consumes silver. Extraction draws from finite reserves with grade
depletion and differential rent. All material and silver ledgers close. The
model is closer to a closed reproduction model but still lacks wages and
the subsistence basket.

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
