# SNLT — research spike

Labor-time accounting against RimWorld 1.6.4871 rev590 (Core + Royalty,
Ideology, Biotech, Anomaly, Odyssey — all installed).

Research spike only. No gameplay, no Harmony, no runtime code.

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

## Results

| doc | question |
|---|---|
| [01-formula.md](docs/01-formula.md) | What is RimWorld's value formula, exactly? |
| [02-primitives.md](docs/02-primitives.md) | Do authored prices track extraction labor? |
| [03-overrides.md](docs/03-overrides.md) | Where did a human override the formula? |

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

**The one number to carry forward:** extraction labor generates a median
**101 silver per work-hour**; manufacturing labor generates exactly **9**. An
11× asymmetry between where value is created and where labor is spent, and it
is structural — the manufacturing rate is one hardcoded constant, the
extraction rate emerges from ~400 authored numbers never reconciled against it.

## Structural note for the mod (not this session)

Any future labor ledger must walk all three production paths:

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
| `primitives.py` | Extraction labor per unit → `out/primitives.csv`. |
| `analyze_primitives.py` | Correlations, implemented inline — no new dependencies. |
| `overrides.py` | Authored vs computed → `out/overrides.csv`. |

Only dependency is `pefile`, which was already installed. Nothing was
downloaded.

```bash
python primitives.py && python analyze_primitives.py && python overrides.py
```

## Known gaps

- Animal products (meat, leather, milk, wool) excluded — generated at load by
  `ThingDefGenerator_Meat`, absent from XML.
- `specialProducts` recipes (butchery, stonecutting, smelting) are excluded by
  RimWorld's own formula too, so their outputs must be authored. Not
  reconstructed, per your instruction.
- Deep drilling and alternative extraction paths not enumerated.
- `value_model.py` is validated against one worked example and internal
  consistency, not against a running game.
