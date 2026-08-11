# RimWorld's own value formula

Read from `Assembly-CSharp.dll`, RimWorld 1.6.4871 rev590, by disassembling
IL directly (`cli_reader.py` — no decompiler was installed, so the ECMA-335
metadata/IL reader is written from scratch against `pefile`).

Everything below is transcribed from IL, not recalled. The relevant methods
are `RimWorld.StatWorker_MarketValue::GetValueUnfinalized`,
`::CalculatedBaseMarketValue`, `::CalculableRecipe`,
`Verse.ThingDef::get_BaseMarketValue`, and
`Verse.IngredientCount::get_IsFixedIngredient`.

## The dispatcher

`ThingDef.BaseMarketValue` is just `GetStatValueAbstract(StatDefOf.MarketValue)`,
which lands in `StatWorker_MarketValue.GetValueUnfinalized`. That method decides,
in this order:

1. **Pawns** — recurse on the def at Normal quality, then apply
   `PriceUtility.PawnQualityPriceFactor` and `...PriceOffset`.
2. **Authored value wins outright.** If `StatRequest.StatBases` contains a
   `MarketValue` entry, the ordinary stat path is used and the calculation
   below never runs.
3. `IFixedBaseMarketValue` on the *instance* — an interface hook with
   **zero implementors in Assembly-CSharp** in 1.6. Dead extension point in
   the base game (verified: the same scan finds 383 implementors of
   `IExposable`, so the scan works).
4. **Relics** — anything whose `StyleSourcePrecept` is a `Precept_Relic` is
   valued as if it were made of steel: `CalculatedBaseMarketValue(def, Steel)`.
5. **Otherwise** — `CalculatedBaseMarketValue(def, stuff)`.

Then `ThingComp.GetStatOffset` / stat factors are applied over the result.

So: **an explicit `<MarketValue>` in `statBases` short-circuits everything.**
The computed path exists only for defs that do not declare one.

## The calculation

```csharp
static float CalculatedBaseMarketValue(BuildableDef def, ThingDef stuffDef)
{
    float value = 0f;
    float work;
    int   yield;

    RecipeDef recipe = CalculableRecipe(def);
    if (recipe != null) {
        work  = recipe.workAmount;
        yield = recipe.products[0].count;
        foreach (IngredientCount ing in recipe.ingredients)
            value += ing.CountRequiredOfFor(ing.FixedIngredient, recipe, null)
                   * ing.FixedIngredient.BaseMarketValue;
    } else {
        work  = Mathf.Max(def.GetStatValueAbstract(StatDefOf.WorkToMake,  stuffDef),
                          def.GetStatValueAbstract(StatDefOf.WorkToBuild, stuffDef));
        yield = 1;

        foreach (ThingDefCountClass c in def.CostList)      // if non-null
            value += c.count * c.thingDef.BaseMarketValue;

        if (def.CostStuffCount > 0) {
            if (stuffDef != null)
                value += def.CostStuffCount / stuffDef.VolumePerUnit
                       * stuffDef.GetStatValueAbstract(StatDefOf.MarketValue, null);
            else
                value += def.CostStuffCount * 2f;   // "assume stuff is worth 2"
        }
    }

    if (work > 2f)
        value += work * 0.0036f;

    return value / yield;
}
```

### The constants

| constant | value | meaning |
|---|---|---|
| labor coefficient | `0.0036` silver per tick | the price of labor time |
| work threshold | `> 2f` | effectively "any work at all" |
| stuff fallback | `2f` per unit | used when no stuff is specified |

`GenDate.TicksPerHour = 2500` and `TicksPerDay = 60000` (read from the
metadata Constant table). So the labor coefficient is exactly:

> **9 silver per in-game work-hour**, at nominal work speed.

An assault rifle (`WorkToMake` 40000, cost 60 steel + 7 components) therefore
prices as `60×1.9 + 7×32 + 40000×0.0036` = `114 + 224 + 144` = **482 silver**,
of which 30% is labor and 70% is transmitted input value.

## Which recipe gets used

```csharp
static RecipeDef CalculableRecipe(BuildableDef def)
{
    if (!def.CostList.NullOrEmpty()) return null;
    if (def.CostStuffCount > 0)      return null;

    foreach (RecipeDef r in DefDatabase<RecipeDef>.AllDefsListForReading) {
        if (r.products == null || r.products.Count != 1) continue;
        if (r.products[0].thingDef != def)               continue;
        foreach (IngredientCount ing in r.ingredients)
            if (!ing.IsFixedIngredient) return null;     // note: aborts entirely
        return r;                                        // first match wins
    }
    return null;
}
```

Three things matter here:

- **First match wins.** Not cheapest, not minimum-labor — whichever recipe
  comes first in `DefDatabase` order. A def producible two ways is priced by
  whichever def loaded first.
- **Substitutable ingredients abort the whole lookup.** `IsFixedIngredient`
  is `filter.AllowedDefCount == 1`. If *any* ingredient allows more than one
  thing, the method returns `null` — and because the `costList` was already
  known empty to reach this point, the def falls to the `else` branch and gets
  `value = work × 0.0036` with **zero input value counted**. Such items are
  priced as pure labor.
- **Multi-output recipes are invisible.** The `products.Count != 1` test
  excludes them, and `specialProducts` recipes (`Butchery`, `StoneBlocks`,
  `Smelted`) carry no `products` list at all. Butchered meat and leather, cut
  stone blocks, and smelted metal are therefore never reached by this
  calculation — their values must be authored. They are (e.g. `BlocksGranite`
  inherits `MarketValue 0.9` from the abstract `StoneBlocksBase`;
  `Leather_Plain` is 2.1).

## Is work normalized?

Yes, and it was never a question. The calculation uses `recipe.workAmount`
raw, or `GetStatValueAbstract`, which is the *def-level* stat with no pawn
attached. No pawn's work speed, skill level, or `workSpeedStat` multiplier
enters the price. RimWorld already prices at nominal labor time, which is
what the brief wanted — no normalization work is needed on our side.

Note that `workSpeedStat` (`GeneralLaborSpeed`, `SmeltingSpeed`,
`ButcheryFleshSpeed`, …) affects how long a *pawn* takes, never the value.

## Is this a labor theory of value?

Structurally, most of the way there, and more so than a hand-priced game
would need to be. The recursion is exactly a Leontief input-output solve:
each good's value is transmitted input value plus a constant times direct
labor time, and `BaseMarketValue` on the ingredient side recurses into the
same function. Iterating it to a fixed point — the plan in the brief — is
what the game does implicitly through recursive stat evaluation.

Where it departs, and the departures are the interesting part:

1. **Labor has an exogenous fixed price.** `0.0036` is a constant, set from
   outside the system. In a labor theory of value the magnitude of value
   *is* labor time; here labor time is one priced input among others, and
   its price was chosen by a designer. This makes the system closer to an
   Adam Smith adding-up-of-costs than to Marx or Ricardo.
2. **Value originates in authored primitives, not in labor.** The recursion
   bottoms out at ~400 defs with hand-set values, not at extraction labor.
   Steel is worth 1.9 because someone typed 1.9. Whether those authored
   numbers track extraction labor is the actual empirical question — see
   `02-primitives.md`.
3. **Joint production is excluded rather than apportioned.** Multi-output
   recipes are skipped entirely, so the theoretically hard case (how to
   split labor across butchery outputs) is dodged by requiring those outputs
   to be authored.
4. **Substitutable inputs collapse to pure labor.** A real bug-shaped
   artifact: those items lose their input value entirely rather than falling
   back to a cheapest-input rule, despite `GetCheapestStuffMarketValue` and
   `GetCheapestThingMarketValue` existing elsewhere in the codebase.
5. **No fixed capital.** The workbench a thing is made on contributes
   nothing. There is no depreciation transfer — constant capital is entirely
   circulating.
6. **Quality and health are post-hoc multipliers**, applied outside this
   function, so two identical labor inputs can yield different prices.

The short version: RimWorld computes prices by a cost-of-production rule
with a fixed wage, seeded by authored primitive values. It is a *price of
production* model, not a labor theory of value — but it is the same
arithmetic, and the mod's ledger can reuse the structure directly by
replacing the authored seeds with extraction labor.
