# SNLT — research spike

Labor-time accounting against RimWorld 1.6.4871 rev590 (Core + Royalty,
Ideology, Biotech, Anomaly, Odyssey — all installed).

Three things, in the order they were built:

1. **A research spike** into RimWorld's two unreconciled value systems.
   Closed; see the headline findings below.
2. **Labor Content** — the smallest mod that puts that result in front of a
   player. Two read-only info-card stats. No gameplay change, no Harmony,
   no compiled code.
3. **An economy laboratory** — a dependency-free deterministic simulation
   where economic rules are made falsifiable before any game-runtime work.
   This is where the project is currently active.

## What happened to the original plan

The brief proposed building an input-output graph from `DefDatabase<RecipeDef>`
and solving for embodied labor by iteration. Two findings redirected it before
any solver was written:

1. **The recipe graph has three production paths, not one.** `RecipeDef` is a
   minority mechanism.
2. **RimWorld already computes market value from ingredients plus work.** For
   most fabricated goods, "does price track labor content" is true by
   construction. Running our own Leontief solve against those numbers would
   have rediscovered the game's own formula and reported it as a finding.

Revised scope, at your direction: extract the formula, then test the authored
primitives (the only genuinely empirical question), then list the overrides.

## Headline findings

**1. A 13.8× seam inside `BaseMarketValue`.** The two unreconciled value
systems are not `workAmount` versus `BaseMarketValue`, as the brief assumed.
They are *extraction labor versus fabrication labor*, priced several times
apart inside `BaseMarketValue` itself — 14.0× under OLS in levels, 3–4× under
relative or log weighting (see `robustness.py`). With embodied labor solved independently of
price, a single-rate model fits at R² 0.816; splitting labor by origin fits at
**R² 0.948** — extraction at **94.8 silver/work-hour**, fabrication at
**6.8**. RimWorld computes a good's price as authored input prices plus one
hardcoded constant times the final step's work, and those authored prices
embed an implicit labor rate an order of magnitude above that constant. In
play: an hour at a workbench adds ~7 silver, an hour at a mining face ~95.

**2. Butchery has an unbounded body-size gradient.**
`RecipeDef.WorkAmountTotal` returns a flat `workAmount`, and
`ButcherCorpseFlesh` declares **450 ticks for any carcass** — a chicken and a
thrumbo cost the same labor — while yields scale linearly with body size.
Labor efficiency therefore rises without bound in body size and nothing in the
pricing pushes back. Grazed megafauna are the most value-dense labor in the
game: `Leather_AlphaThrumbo` implies **100,000 silver/work-hour**, and the
`Leathers` category median is 3,167.

**3. A 293× husbandry spread.** Grazing and hay-feeding are genuinely
different economies. Median spread across the 66 animals with both paths is
9×, but `Meat_Thrumbo` costs 0.63 ticks/unit grazed and **182.89 hay-fed**.
Pasture access, not animal choice, is what decides whether livestock is nearly
free or expensive.

**4. Gold: the cleanest statement that RimWorld prices scarcity, not work.**
`MineableSteel`, `MineableSilver`, `MineableJade` and `MineableGold` are
defined with *identical* extraction parameters — 1500 hit points, natural
rock, yield 40, so 47.5 ticks per unit — and priced **1.9 / 1.0 / 5.0 /
10.0**. Identical labor, 10× price spread. Gold's price per unit of extraction
labor is **58.5×** what the game pays for fabrication labor, while steel,
plasteel and uranium cluster tightly at 10–13×. Where labor is meant to
matter, it is encoded in mineable hit points; where scarcity is meant to
matter, that dial is simply ignored.

## Results

| doc | question |
|---|---|
| [01-formula.md](docs/01-formula.md) | What is RimWorld's value formula, exactly? |
| [02-primitives.md](docs/02-primitives.md) | Do authored prices track extraction labor? |
| [03-overrides.md](docs/03-overrides.md) | Where did a human override the formula? |
| [04-endogenous-rate.md](docs/04-endogenous-rate.md) | What labor rate does the price structure actually imply? |
| [05-animals.md](docs/05-animals.md) | What is meat and leather worth in labor? |

**The formula.** Value = transmitted input value + `0.0036` silver per tick of
work, divided by yield, with an authored `MarketValue` short-circuiting the
whole thing. That coefficient is exactly **9 silver per work-hour**. It is a
price-of-production model with a fixed wage, not a labor theory of value —
same arithmetic, but labor's price is exogenous and value originates in
authored primitives rather than in labor.

**The primitives.** Split cleanly in two. Industrial staples (steel, plasteel,
uranium, wood, cloth) are priced labor-proportionally within a 1.48× spread,
with labor encoded as mineable hit points. Luxury and rarity-gated goods are
not: **steel, silver, jade and gold are mined from rock with identical hit
points and identical yield, and priced 1.9 / 1.0 / 5.0 / 10.0.** Same labor,
10× price spread. Gold breaks as predicted; plasteel does not — it is one of
the most labor-consistent materials in the game.

**The overrides.** 49 defs (not 25 — the first count missed `ParentName`
inheritance). 34 marked up, 12 down, 3 at parity. Every drug in the game is
marked up; Anomaly serums carry 10–11× markups. The dominant pattern is
flattening a category to one round number — all seven shell types cost 55
against computed costs from 18.75 to 92.50.

**The endogenous rate.** With embodied labor solved independently of price
(653 defs, seeded at extraction, no market value anywhere in the derivation),
a single-rate model fits at R² 0.816. Splitting labor by origin fits at
**R² 0.948**: extraction labor is priced at **94.8 silver/work-hour**,
fabrication labor at **6.8** — a **14.0× gap** in levels, narrowing to 3–4×
under relative or log weighting. Implied rates fall monotonically across five
buckets as a good's fabrication share rises (114.6 → 24.2 silver/hr, animal
products excluded). There is no single rate.

Two independent checks landed. The regression was never given RimWorld's
hardcoded `0.0036` fabrication constant and recovered **0.00263** — within
30%, a sanity check on the chain rather than an exact recovery. And the
extraction rate of 94.8/hr matches the **101/hr** estimated separately in
`02-primitives.md` from 30 hand-authored prices — agreement within 5% from
different data by a different method.

**The one line to carry forward:** the two unreconciled value systems are not
`workAmount` versus `BaseMarketValue`. They are **extraction labor versus
fabrication labor, priced several times apart inside `BaseMarketValue`
itself** — 14× across the game's total value, 3–4× across a typical good. In
RimWorld, crafting pays poorly either way.

## Structural note

Any labor ledger must walk all three production paths:

1. **Explicit `RecipeDef`** — 118 in Core.
2. **`ThingDef.recipeMaker`** — 93 in Core, synthesized at load by
   `RecipeDefGenerator`. Absent from XML on disk; present in `DefDatabase`
   at runtime.
3. **`costList`/`costStuffCount` + `WorkToBuild`** — buildings, which have no
   recipe at all.

Buildings having `WorkToBuild` and no recipe means **fixed capital is
structurally distinct in the data**, and RimWorld's own formula transfers no
value from it — a workbench contributes nothing to what it produces. All
constant capital is circulating.

## Code

| file | |
|---|---|
| `cli_reader.py` | ECMA-335 metadata + IL reader, written from scratch on `pefile`. No decompiler was installed; this reads `Assembly-CSharp.dll` directly. |
| `dump_method.py` | `python dump_method.py "Type::Method"` — disassembles by name. |
| `defs.py` | Def loader with `ParentName` inheritance resolved (recursive merge by element name, as `XmlInheritance` does). |
| `value_model.py` | Transcription of `CalculatedBaseMarketValue`. Reproduces the worked assault-rifle example (482) exactly. |
| `primitives.py` | Extraction labor per unit → `out/primitives.csv`. `BYPRODUCT` controls mining-spoil treatment. |
| `analyze_primitives.py` | Correlations, implemented inline — no new dependencies. |
| `overrides.py` | Authored vs computed → `out/overrides.csv`. |
| `solver.py` | Embodied-labor solve seeded at extraction, non-circular → `out/embodied_labor.csv`. Min-cost hyperpath; `SCAVENGING` is the documented swap point. |
| `animals.py` | Generated meat defs, butchery yields, husbandry labor. `APPORTION` splits a carcass between meat and leather. |
| `validate_animals.py` | Diffs our animal model against RimWorld's own dev-mode export in `data/`. Currently 100% on meat, body size and nutrition. |
| `validate_recipes.py` | Diffs `value_model.py` against the game's Recipes table. Caught the ingredient-count bug. |
| `validate_prices.py` | Diffs base and calculated market values against the game's Acquisition table: 92/92 and 33/33. Caught the inherited `roundToFiveOver`. |
| `rate_test.py` | Single- vs two-rate fits, gradient by fabrication share, residuals. |
| `robustness.py` | Estimator sensitivity (levels / relative / log), the bucket table with and without animal products, and plant-labor sensitivity. |

Only dependency is `pefile`, which was already installed. Nothing was
downloaded.

```bash
python primitives.py && python analyze_primitives.py && python overrides.py && python solver.py && python rate_test.py
```

## Known gaps

Of the 1285 defs with no embodied-labor value, most are not economic goods at
all — ~435 motes/projectiles, races, standing plants, uncraftable natural or
ancient buildings, unfinished-thing stubs. The real remainder:

- **Meat and leather are now incorporated** (see `05-animals.md`); eggs, milk
  and wool are not. Hunting is deliberately not modelled — its labor is combat
  time, which is not a def field.
- **Trade- and quest-only goods (~91 blocked)** — Shard, subcores, signal and
  nanostructuring chips, Gravcore, Neutroamine, ShuttleEngine. These are not a
  gap so much as a category: RimWorld's high-tech tier is *acquired*, not
  produced, and has no labor content by any honest accounting.
- Deep drilling and alternative extraction paths not enumerated.
- Stone is now incorporated (chunks → blocks); see `BYPRODUCT` in
  `primitives.py` for the joint-production treatment and its justification.
- `value_model.py` is validated against one worked example and internal
  consistency, not against a running game.

## The mod

`mod/` — a labor ledger. Two read-only stats on the info card of every
producible thing: labor embodied in it, split extraction vs fabrication.
No gameplay change.

**No Harmony, no gameplay change, no save impact.** Two `StatDef`s plus
generated `PatchOperationConditional` patches writing a precomputed value onto
each def — 543 defs across six files, 548 `<Operation>` elements once the five
`PatchOperationFindMod` wrappers on the expansion files are counted.

One small assembly, and one only. `StatWorker_LaborContent` overrides a single
virtual method to render each value in every unit that says something, because
`StatDef.formatString` takes exactly one value and embodied labor spans five
orders of magnitude — no single unit reads well at both ends:

| def | fabrication labor |
|---|---|
| `Steel` | 0 |
| `MealSimple` | 5 work-s · 300 ticks |
| `Apparel_Parka` | 3.2 in-game h · 133 work-s · 8,000 ticks |

The built DLL binds to exactly two RimWorld symbols, and `formatString` and
`toStringStyle` stay in the defs so the stat still renders if the worker ever
fails to load.

| | |
|---|---|
| defs patched | 543 |
| take `<match>` (def has `statBases`) | 446 |
| take `<nomatch>` (no `statBases`) | 97 |
| unresolved xpaths | 0 |
| skipped | 104 generated meat defs — no XML node exists to patch |

Values are stored in work-seconds (ticks ÷ 60, RimWorld's own work unit per
`GenText.ToStringWorkAmount`), ranging 0.008 to 6736. `toStringStyle` is
`FloatMaxTwo` rather than `WorkAmount` because the latter ceils, which would
flatten every animal product to "1".

```bash
python solver.py && python make_mod.py && sh mod/Source/build.sh
```

The build uses the `csc.exe` Windows already ships rather than the .NET SDK,
which constrains the source to C# 5. Then copy `mod/` into `RimWorld/Mods/`
and enable it.

Known limits, both now cheap to fix given the assembly exists:

- meat defs are generated at load, so no patch can reach them — a short
  `StaticConstructorOnStartup` away;
- the stat is **stuff-independent**: a plasteel knife and a wooden knife
  report the same labor content, because `statBases` has no notion of stuff,
  while Market Value and Work to Make on the same card do vary. 176 of 653
  defs (27%) are stuffable. Fixing it means computing at request time from
  `req.Thing.Stuff`.

Values are also static, so they do not respond to mods that change recipes.

## The economy laboratory

`economy_lab/` — a dependency-free, deterministic stock-flow model of a small
economy. It exists so that economic rules can be made falsifiable before UI,
pawn AI, saves, or Harmony complicate debugging. Nothing here touches a
running game.

Two properties are held above everything else: **determinism** (identical
inputs give bit-identical histories) and **ledgers that close to
floating-point zero — material, silver, and value alike**. Every feature below was
designed in a committed document before it was implemented, measured against
a frozen behavioral reference afterward, and the predictions were scored
honestly whether or not they held.

The circuit is six commodities across two regional markets — three goods in
a forking production chain, plus the food, clothing and medicine that
reproduce the workers who make them:

```
chemfuel ──┬──> psychoid farm ──> psychoid leaves ──> drug lab ──> yayo
           └────────────────────────────────────────────^

provisioning ──> meals ──> the workers who staff all of the above
```

What it models: accounted input-output production; a cost floor that curtails
on margin before material runs out; damped demand-led replenishment; costly,
delayed, capacity-limited arbitrage; capacity investment that consumes a
construction fund; finite resource reserves with ordered grade depletion and
differential rent; the wage relation, with silver cycling producer → wage →
worker → basket purchase → producer; a surplus ledger in work-ticks; labor
values solved endogenously from the process graph; competitive
transmission, where the price anchor reads cost and the order book goes to
the cheaper producer; and fixed capital that transfers its value to the
product, with c, v and s accumulated in work-ticks.

Four quantities are kept strictly distinct and are never collapsed into one
number: **labor value, market price, surplus value, and rent.** Money profit
is not surplus value — a commodity can contain surplus labor and fail to
realize it in a glut.

### Three results worth reading

**1. The endogenous value solve reproduces the closed analysis.** Values
solved from the lab's own process graph agree with `solver.py`'s independent
653-def result exactly for the two commodities with no modelled inputs
(chemfuel 25 ticks, meals 305), and are high on the two downstream ones by
*precisely* the one link the design documents flagged as stylized — 1.25
ticks on psychoid leaves, 15.00 on yayo. No other discrepancy. That is the
propagation machinery validated against an independent solve rather than
against itself.

**2. The rate of surplus value is now an outcome, not a coefficient.** At
equilibrium **s/v = 38.344**. It does not move when prices do: a subsistence
shock that doubles the meal price and the money wage leaves the labor value
of a meal at exactly 305 and s/v unchanged. It moves when *technique* does: a
provisioning technique with half the living labor lowers the social value of
the wage good, and **s/v rises to 43.944 in both regions — including the one
that adopted nothing** — with the working day and the basket held fixed and
asserted in tests. That is relative surplus value, emerging from the graph
rather than from a parameter. (Both figures are from the meals-only basket
the model carried until `docs/29`; with clothing and medicine in it, s/v is
26.71 and rises to 28.70.)

**3. The overhead is the seam, measured from the inside.** RimWorld's
authored price for a meal is 15 silver. Inputs, wages, and the depreciation
of a real `ElectricStove` account for 0.39 of it; the other **two-thirds of
the price is a wedge the model cannot attribute** to anything. Fixed
capital — implemented from the game's own building costs, repairing an
omission `FINDINGS.md` found in vanilla — explains 0.05%. This is the same
seam the research spike found from the outside: authored prices embed a
labor rate far above what the model pays. Every sector performs surplus
labor at the same rate, 38.3, but realizes wildly different amounts of it
in money — 72.6 for chemfuel, 11.2 for yayo — which is the transformation
problem as arithmetic rather than argument.

**4. Value and price answer to different things.** Two deliberately opposite
scenarios, once cost reaches price and the order book goes to the cheaper
producer. A *labor-saving* technique moves the labor value of a meal by
−12.7% and its price by −0.47%. A *capital-saving* one moves the price by
−14.3% and the value by exactly nothing. The rate of surplus value follows
value, not money: it rises in the first case and does not budge in the
second, even though the money wage there falls 14%. Transmission is weak for
labor-saving change for a measured reason — wages are 2–4% of money cost, and
the operating overhead that dominates it is the authored-price wedge: the gap
between RimWorld's `MarketValue` and anything the model can account for.

The classical answer to that wedge is now computed. Folding the subsistence
basket into the input matrix and solving `p = (1 + r)Mp` gives a price system
with no authored magnitude anywhere in it — a uniform profit rate that is an
outcome rather than a coefficient, and Sraffa's basics theorem deciding which
sector's technique can move it.

It was blamed on the meals-only basket, and that was **wrong**. Enlarging the
basket to food, clothing and medicine — every figure from the closed analysis
— cut the rate of surplus value from 38.30 to 26.71 and yayo's deviation from
its authored price from 71.6× to 38.7×, and left both unusable. The real
constraint is RimWorld's own productivity: **one provisioner's working day
feeds 39.3 workers**, so necessary labor is 3.6% of the day and no defensible
bundle changes that by an order of magnitude. The rate of surplus value this
project reports is not a calibration artifact. It is the game's.

**4. Two numbers that were not rates of profit, and now are.** The price
system charged profit against a single day's flow while the model held twenty
days of stock, and the value ledger divided surplus by capital *consumed*
rather than capital *advanced*. Both are fixed: the uniform rate is 1.17 per
day and the old figure survives as the gross markup, while the ledger reports
a rate of profit on advances of 0.0305 per day beside the 1.73 flow ratio.
Uniform turnover moves no relative price — it is a scalar — so the invariance
is asserted bit-exactly, and the circuit turns out to tie its capital up for
**56.8 days rather than 21**, because the finished stock of the final product
appears in no cost flow at all.

### Design and results documents

Each feature has a decision document written *before* implementation and a
results document scoring the predictions afterward.

| doc | |
|---|---|
| **[25-stage0-arc-summary.md](docs/25-stage0-arc-summary.md)** | **Start here: what the laboratory has learned, and what it got wrong** |
| **[44-phase-a-arc-summary.md](docs/44-phase-a-arc-summary.md)** | **Then here: closing the last holes, and the proxy that keeps failing** |
| [06-stage0-economy-lab.md](docs/06-stage0-economy-lab.md) | The laboratory's purpose and shape |
| [07](docs/07-accounted-input-predictions.md) · [08](docs/08-accounted-input-design.md) · [09](docs/09-accounted-input-results.md) | Accounted input-output production: joint products by mass, proportional rationing, simultaneous production |
| [10](docs/10-upstream-observation-results.md) · [11](docs/11-upstream-production-control.md) · [12](docs/12-upstream-production-control-results.md) | The upstream hysteresis bug and the damped demand-led control that fixed it |
| [13](docs/13-cost-floor-and-investment-design.md) · [14](docs/14-cost-floor-and-investment-results.md) | Cost floor, construction-fund investment, buffer-deficit investment |
| [15](docs/15-resource-reserves-design.md) · [16](docs/16-resource-reserves-results.md) | Finite reserves, grade depletion, differential rent |
| [17](docs/17-labor-power-and-surplus-design.md) · [18](docs/18-labor-power-and-surplus-results.md) | Labor-power, the subsistence basket, the wage circuit, the surplus ledger |
| [19](docs/19-endogenous-labor-values-design.md) · [20](docs/20-endogenous-labor-values-results.md) | Endogenous labor values and relative surplus value |
| [21](docs/21-competitive-transmission-design.md) · [22](docs/22-competitive-transmission-results.md) | Competitive transmission: the cost-aware price anchor and the cost-weighted order book |
| [23](docs/23-constant-capital-and-the-overhead-design.md) · [24](docs/24-constant-capital-and-the-overhead-results.md) | Fixed capital, the value ledger, and what the operating overhead actually is |
| [26](docs/26-prices-of-production-design.md) · [27](docs/27-prices-of-production-results.md) | Prices of production: Sraffa's basics, the corn-model profit rate, and the aggregate invariance failure |
| [28](docs/28-enlarged-subsistence-basket-design.md) · [29](docs/29-enlarged-subsistence-basket-results.md) | Clothing and medicine in the basket, and why the constraint was never the basket |
| [30](docs/30-turnover-design.md) · [31](docs/31-turnover-results.md) | Turnover: profit on capital advanced, and the two rates that were not rates |
| [32](docs/32-scale-test-design.md) · [33](docs/33-scale-test-results.md) | The scale test: 647 commodities across 100 regions, and what the runtime port cannot keep |
| [34](docs/34-history-detail-design.md) · [35](docs/35-history-detail-results.md) | Making history optional, and a ledger that was reading its own report |
| [36](docs/36-capital-goods-sector-design.md) · [37](docs/37-capital-goods-sector-results.md) | Department I: machines that are produced, and the nine tenths of the fixed capital that move nothing |
| [38](docs/38-capacity-depreciation-design.md) · [39](docs/39-capacity-depreciation-results.md) | Capacity depreciation and exit: a loss-making sector is disciplined rather than deleted |
| [40](docs/40-recreation-in-the-basket-design.md) · [41](docs/41-recreation-in-the-basket-results.md) | Recreation in the basket: basicness is binary, and its economic weight is not |
| [42](docs/42-absolute-rent-design.md) · [43](docs/43-absolute-rent-results.md) | Absolute rent: Marx's condition holds exactly without fixed capital, and breaks with it |

### Running it

```bash
python -m unittest discover -s tests      # 183 acceptance and invariant tests
python -m economy_lab all                 # every scenario, as JSON
python -m economy_lab technique-change    # relative surplus value
python -m economy_lab cost-competition    # undercutting, and its price effect
python -m economy_lab generous-basket     # the basket, pushed past defensible
python -m economy_lab perishable-meals    # differential turnover: meals rot
python -m economy_lab capital-goods       # Department I: the machines are produced
python -m economy_lab capacity-exit       # competition for survival, not only for orders
python -m economy_lab recreation-basket   # the workers' basket holds the workers' product
python -m economy_lab.baseline            # 182 frozen metrics vs current
python -m economy_lab.scale --sweep       # the size ladder, 6 to 6,470 producers
```

`behavior_baseline.json` freezes 182 behavioral metrics. The baseline reporter
is deliberately a *report*, not a pass/fail test — the invariant tests protect
correctness, while the reporter makes every behavioral change visible and
forces it to be explained before the reference is rewritten.

## The runtime shell

`economy_mod/` — a read-only RimWorld 1.6 mod that is currently a shell, not
an economy. It persists a world component on a daily tick, observes generated
settlements, and shows them in a read-only tab that states explicitly that
vanilla prices are unchanged. No Harmony, no gameplay mutation.

It deliberately does not run the Stage 0 model. Nothing claiming to be a
production economy goes into a save until the laboratory's material circuit is
credible.
