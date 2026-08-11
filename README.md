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
**R² 0.948**: extraction labor is priced at **95.4 silver/work-hour**,
fabrication labor at **6.9** — a **13.8× gap**. Implied rates fall
monotonically across five buckets as a good's fabrication share rises
(387.6 → 24.3 silver/hr). There is no single rate.

Two independent checks landed. The regression was never given RimWorld's
hardcoded `0.0036` fabrication constant and recovered **0.00263** — within
30%, a sanity check on the chain rather than an exact recovery. And the
extraction rate of 95.4/hr matches the **101/hr** estimated separately in
`02-primitives.md` from 30 hand-authored prices — agreement within 5% from
different data by a different method.

**The one line to carry forward:** the two unreconciled value systems are not
`workAmount` versus `BaseMarketValue`. They are **extraction labor versus
fabrication labor, priced 13.8× apart inside `BaseMarketValue` itself.** In
RimWorld, crafting barely pays: an hour at a workbench adds ~7 silver, an hour
at a mining face ~97.

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
| `primitives.py` | Extraction labor per unit → `out/primitives.csv`. `BYPRODUCT` controls mining-spoil treatment. |
| `analyze_primitives.py` | Correlations, implemented inline — no new dependencies. |
| `overrides.py` | Authored vs computed → `out/overrides.csv`. |
| `solver.py` | Embodied-labor solve seeded at extraction, non-circular → `out/embodied_labor.csv`. Min-cost hyperpath; `SCAVENGING` is the documented swap point. |
| `animals.py` | Generated meat defs, butchery yields, husbandry labor. `APPORTION` splits a carcass between meat and leather. |
| `rate_test.py` | Single- vs two-rate fits, gradient by fabrication share, residuals. |

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
