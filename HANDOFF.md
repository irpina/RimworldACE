# Project handoff — Labor Content and Economy

**Last updated:** 2026-08-12  
**Repository:** `C:\Users\PintS\OneDrive\Documents\Projects\snlt`  
**Current branch:** `master`  
**Latest Stage 0 model commit:** `c028cd6` (demand-led production control)
**Behavioral baseline:** `05996ae` (53 metrics after production control)
**Sensitivity harness:** `f2c490c`  
**Pre-process predictions:** `cae1ba2`  
**Process design decisions:** `863ee42`  
**Process tests:** `57b05ed`  
**Process results:** `98ae17e`  
**Upstream behavioral baseline:** `e2a7c43`
**Hysteresis investigation:** `097e40c`
**Production-control design:** `cbeb720`
**Production-control results:** `3f9c20b`
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
  table and acceptance rationale.

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
- demand-led production planning: wanted output follows current final and
  productive outflow plus a damped correction toward material stock targets;
- daily production and price-sensitive consumption;
- persistent regional inventory and cash;
- damped local price formation from stocks and unmet demand;
- costly, delayed, capacity-limited arbitrage;
- destruction of productive capacity, upstream or downstream;
- delayed investment and replacement capacity;
- fixed labor value beside dynamic market price;
- explicit commodity and silver balance checks, with productive consumption
  booked separately from final consumption.

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

### Current calibrated behavior

- equilibrium remains exactly stable for four in-game years;
- a glut equal to 25% of annual regional yayo consumption lowers the local
  price from 21 to **12.791**;
- the distant region only falls to **20.106**;
- arbitrage exports **13 units** before the spread closes;
- destroying 60% of regional capacity raises the price to **38.630**;
- replacement capacity restores at least 80% of baseline supply within the
  four-to-eight-quadrum target;
- all 25 tests pass, including all prior 23 unchanged;
- commodity and silver residuals close to floating-point zero for all three
  commodities;
- identical inputs reproduce identical histories.

These are provisional gameplay targets, not empirical claims about real-world
elasticities.

### Accounted-input production changed none of them

Full comparison in `docs/09-accounted-input-results.md`. Eleven of the thirteen
predictions in `docs/07` forecast movement; all eleven are wrong. The frozen
reference was therefore **not** rewritten.

Three reasons, only one of which was anticipated:

1. **A glut cannot be damped by an input constraint.** A glut in the final good
   means producing less, which demands *fewer* inputs. The prediction was
   describing the cash channel — producers paying for what they consume — which
   is deliberately not in this slice.
2. **Capacity entry is still free**, which `docs/07` explicitly flagged as the
   assumption its producer-loss forecast depended on.
3. **Every stage carries twenty days of cover and no benchmark shock attacks an
   input.** The tightest the four frozen scenarios ever reach is 11.68 days.
   The constraint is correct and simply never binds.

The old thirteen metrics could not see the following because they watched yayo
only:

- destroying 60% of the drug labs now crashes the psychoid leaf price 74%
  (1.900 → 0.489) and chemfuel 53% (2.300 → 1.086);
- a one-off glut leaves **permanent upstream hysteresis** — yayo returns
  exactly to 21.000/200 while leaves settle at 1.698/1771 and stay there.

That instrumentation gap is now closed for price and stock paths. The baseline
adds forty upstream observations while leaving all thirteen original metrics
unchanged. It covers price and inventory extrema with their days, plus a settled
glut endpoint and terminal producer-loss endpoint for both leaves and chemfuel.

The new `input-shortage` scenario is the one that binds: 70% of Dust Basin's
psychoid fields destroyed, leaf stock draining 56/day for a silent month before
yayo notices, leaf price up 5× against yayo's 1.75×, and the drug lab running at
3 yayo/day against a capacity of 10 rather than shutting.

Run:

```text
python -m unittest discover -s tests -v
python -m economy_lab all
python -m economy_lab input-shortage
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

- local glut trough: **14.340916** on day 66;
- distant glut trough: **20.415752** on day 81;
- local half-gap recovery: **11 days / 0.733333 quadrums**;
- arbitrage exports: **12.381259 units**;
- producer-loss peak: **38.630290** on day 119;
- 80% capacity recovery: **75 days / 5 quadrums**;
- equilibrium price range: **0** in both regions.

Current upstream headline observations include:

- glut leaf settlement: **1.900000 / 1,600 units**;
- glut chemfuel settlement: **2.300000 / 120 units**;
- producer-loss leaf trough: **0.693449** on day 70;
- producer-loss chemfuel trough: **1.918998** on day 69.

The former glut hysteresis was a **control-law bug**, not a capacity reallocation
or ledger leak. It is resolved by the design in `docs/11`: planned output follows
intended outflow plus a 10% daily correction toward the existing material stock
target. The mutually dependent order plans converge deterministically from the
day's opening state, so production remains simultaneous. Leaves now stay at
1,600 and chemfuel at 120 throughout the glut, both at reference price.

The future cash cost floor does **not** replace this control. Material planning
answers how much output is wanted; input payments and liquidity will answer
whether that plan is profitable and financeable. When the cash channel lands,
actual production should be limited by both rather than using profitability as
an accidental demand signal.

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

Steps 1–4 and the production-control correction are **done** (`f52fcd0`,
`57b05ed`, `c028cd6`). Resume at step 5.

1. ~~Add `Process` definitions with material inputs, outputs, direct labor,
   capacity, and unit operating cost.~~
2. ~~Add at least three linked commodities.~~ Done as a forking circuit:
   chemfuel feeds both the psychoid fields and the drug lab.
3. ~~Require production to consume accounted inventory.~~
4. ~~Add process-level material-balance tests and an input shortage
   scenario.~~
5. **Next economic feature:** make investment consume an explicit capital-good
   or construction fund rather than creating capacity freely. This is also the
   missing half of the cost floor: the material floor landed this session, the
   cash floor did not. Consider making producers pay for their inputs at the
   same time, since `docs/09` shows that is the channel the glut prediction
   actually needed.
6. Only then add finite resource reserves, grade depletion, marginal extraction
   cost, and differential rent.
7. After the market/resource laboratory is credible, add the local subsistence
   basket and hired-worker contracts.

The excess-inventory control is implemented and the understood baseline movement
is frozen. Step 5 can now add input payments and capital-goods costs without also
having to invent a demand signal. Keep the material plan and cash constraint as
separate mechanisms.

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

- capital-goods costs for capacity investment;
- producers paying cash for their inputs — the material floor exists, the cost
  floor does not, and `unit_cost` still does not include input prices;
- labor value propagated endogenously through processes; `Process.direct_labor`
  is recorded but `Commodity.labor_value` remains the static `FINDINGS.md`
  figure;
- joint products in an actual scenario — the mass apportionment rule is
  implemented and unit-tested, but every current process has one output;
- resource reserves, grades, and rent;
- labor supply and wages;
- the poverty/subsistence basket;
- credit, bankruptcy, and liquidity-constrained consumption;
- more than three commodities or two regions;
- RimWorld save/UI/runtime integration.

Production now consumes accounted inventory, so supply finally has a material
floor. Capacity entry is still a free ledger source, so the model closes its
declared commodity ledger but is not yet a closed reproduction model.

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
