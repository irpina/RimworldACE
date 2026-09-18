# RimWorld side — the research spike, the mod, and the runtime shell

Everything in this directory touches RimWorld 1.6.4871 rev590 (Core +
Royalty, Ideology, Biotech, Anomaly, Odyssey — all installed). None of it
is where the project is currently active; the economy laboratory in
`../economy_lab/` is. It is kept here, working, for when the laboratory's
model is ready to go into a game.

Three things, in the order they were built:

| directory | |
|---|---|
| `spike/` | The closed research spike into RimWorld's two unreconciled value systems: the def reader, the value-formula transcription, the embodied-labor solver, and the analyses. `spike/FINDINGS.md` is the long-form record. |
| `mod/` | **Labor Content** — the smallest mod that puts the spike's result in front of a player. Two read-only info-card stats. No gameplay change, no Harmony. |
| `economy_mod/` | The Stage 1 runtime shell: a read-only RimWorld mod plus `Economy.Core`, a C# port of the laboratory's value, wage and price solves, verified bit-for-bit against fixtures the laboratory writes. See `economy_mod/README.md`. |

The design and results documents for all three live with the laboratory's
in the top-level `docs/` directory, because the two sides cite each other
by number throughout. `docs/01`–`docs/05` are the spike; `docs/53`–`docs/96`
are mostly the port and the shell. The laboratory's own documents are
indexed in the top-level `README.md`.

The spike's scripts read `data/` and write `out/` relative to the current
directory, so run them from `spike/`:

```bash
cd rimworld/spike
python primitives.py && python analyze_primitives.py && python overrides.py && python solver.py && python rate_test.py
```

`out/embodied_labor.csv` is the closed 653-def solve. The laboratory keeps
its own frozen copy at `../economy_lab/data/embodied_labor.csv`, so nothing
in the laboratory depends on this directory.

# The research spike

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
| [01-formula.md](../docs/01-formula.md) | What is RimWorld's value formula, exactly? |
| [02-primitives.md](../docs/02-primitives.md) | Do authored prices track extraction labor? |
| [03-overrides.md](../docs/03-overrides.md) | Where did a human override the formula? |
| [04-endogenous-rate.md](../docs/04-endogenous-rate.md) | What labor rate does the price structure actually imply? |
| [05-animals.md](../docs/05-animals.md) | What is meat and leather worth in labor? |

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
| `spike/cli_reader.py` | ECMA-335 metadata + IL reader, written from scratch on `pefile`. No decompiler was installed; this reads `Assembly-CSharp.dll` directly. |
| `spike/dump_method.py` | `python dump_method.py "Type::Method"` — disassembles by name. |
| `spike/defs.py` | Def loader with `ParentName` inheritance resolved (recursive merge by element name, as `XmlInheritance` does). |
| `spike/value_model.py` | Transcription of `CalculatedBaseMarketValue`. Reproduces the worked assault-rifle example (482) exactly. |
| `spike/primitives.py` | Extraction labor per unit → `out/primitives.csv`. `BYPRODUCT` controls mining-spoil treatment. |
| `spike/analyze_primitives.py` | Correlations, implemented inline — no new dependencies. |
| `spike/overrides.py` | Authored vs computed → `out/overrides.csv`. |
| `spike/solver.py` | Embodied-labor solve seeded at extraction, non-circular → `out/embodied_labor.csv`. Min-cost hyperpath; `SCAVENGING` is the documented swap point. |
| `spike/animals.py` | Generated meat defs, butchery yields, husbandry labor. `APPORTION` splits a carcass between meat and leather. |
| `spike/validate_animals.py` | Diffs our animal model against RimWorld's own dev-mode export in `data/`. Currently 100% on meat, body size and nutrition. |
| `spike/validate_recipes.py` | Diffs `value_model.py` against the game's Recipes table. Caught the ingredient-count bug. |
| `spike/validate_prices.py` | Diffs base and calculated market values against the game's Acquisition table: 92/92 and 33/33. Caught the inherited `roundToFiveOver`. |
| `spike/rate_test.py` | Single- vs two-rate fits, gradient by fabrication share, residuals. |
| `spike/robustness.py` | Estimator sensitivity (levels / relative / log), the bucket table with and without animal products, and plant-labor sensitivity. |

Only dependency is `pefile`, which was already installed. Nothing was
downloaded. Run everything from `spike/` (see the top of this file).

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

# The mod

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
cd rimworld/spike && python solver.py && python make_mod.py && sh ../mod/Source/build.sh
```

The build uses the `csc.exe` Windows already ships rather than the .NET SDK,
which constrains the source to C# 5. Then copy `rimworld/mod/` into `RimWorld/Mods/`
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

# The runtime shell

`economy_mod/` — a read-only RimWorld 1.6 mod that is a shell, not an
economy. It persists a world component on a daily tick, observes generated
settlements, and shows them in a read-only tab that states explicitly that
vanilla prices are unchanged. No Harmony, no gameplay mutation.

It deliberately does not run the Stage 0 model. Nothing claiming to be a
production economy goes into a save until the laboratory's material circuit is
credible.
