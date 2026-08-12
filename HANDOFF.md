# Project handoff — Labor Content and Economy

**Last updated:** 2026-08-11  
**Repository:** `C:\Users\PintS\OneDrive\Documents\Projects\snlt`  
**Current branch:** `master`  
**Latest Stage 0 commit:** `d284af9`  
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
- `docs/06-stage0-economy-lab.md` — short design note.

Commits:

- `54d88ce` — Add deterministic Stage 0 economy laboratory
- `d284af9` — Report Stage 0 shock extrema

### Current vertical slice

The model currently has one commodity (`yayo`), two regional markets, and one
expensive planetary route. It supports:

- daily production and price-sensitive consumption;
- persistent regional inventory and cash;
- damped local price formation from stocks and unmet demand;
- costly, delayed, capacity-limited arbitrage;
- destruction of productive capacity;
- delayed investment and replacement capacity;
- fixed labor value beside dynamic market price;
- explicit commodity and silver balance checks.

### Current calibrated behavior

- equilibrium remains exactly stable for four in-game years;
- a glut equal to 25% of annual regional yayo consumption lowers the local
  price from 21 to **12.791**;
- the distant region only falls to **20.106**;
- arbitrage exports **13 units** before the spread closes;
- destroying 60% of regional capacity raises the price to **38.630**;
- replacement capacity restores at least 80% of baseline supply within the
  four-to-eight-quadrum target;
- all eight tests pass;
- commodity and silver residuals close to floating-point zero;
- identical inputs reproduce identical histories.

These are provisional gameplay targets, not empirical claims about real-world
elasticities.

Run:

```text
python -m unittest discover -s tests -v
python -m economy_lab all
```

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

The next Stage 0 slice should replace free single-output production with
input-output processes.

Recommended order:

1. Add `Process` definitions with material inputs, outputs, direct labor,
   capacity, and unit operating cost.
2. Add at least three linked commodities, probably:
   - psychoid leaves;
   - yayo;
   - a generic subsistence/input commodity if needed for the first circuit.
3. Require production to consume accounted inventory.
4. Add process-level material-balance tests and an input shortage scenario.
5. Make investment consume an explicit capital-good or construction fund
   rather than creating capacity freely.
6. Only then add finite resource reserves, grade depletion, marginal extraction
   cost, and differential rent.
7. After the market/resource laboratory is credible, add the local subsistence
   basket and hired-worker contracts.

Two safe tracks can now proceed independently:

1. In Stage 0, replace free single-output production with accounted
   input-output processes in the order above.
2. In Stage 1, generate deterministic settlement profiles and regional
   membership, persist them, and display them read-only. Do not run a claimed
   production economy or alter vanilla prices until the Stage 0 material
   circuit is credible.

---

## Known Stage 0 omissions

- production inputs and joint products;
- resource reserves, grades, and rent;
- labor supply and wages;
- the poverty/subsistence basket;
- capital-goods costs for capacity investment;
- credit, bankruptcy, and liquidity-constrained consumption;
- more than one commodity or two regions;
- RimWorld save/UI/runtime integration.

Current production is an explicit ledger source, and capacity entry is free.
The model therefore closes its declared commodity ledger, but it is not yet a
closed reproduction model.

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
