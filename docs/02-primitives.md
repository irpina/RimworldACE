# Are the authored primitive prices labor prices?

This is the only genuinely empirical question in the spike. The ~400 defs with
a hand-authored `MarketValue` are where RimWorld's value recursion bottoms out
(see `01-formula.md`). If those numbers track extraction labor, the game's
whole price structure is a labor theory of value with authored seeds. If they
don't, the seeds are something else and the labor content is decoration.

**They mostly don't. The break is clean and it is exactly the scarcity
boundary.**

## Method

30 primitives have both an authored `MarketValue` and a computable extraction
path. Extraction labor is measured in ticks at nominal work speed.

**Mining**, from `JobDriver_Mine::DoDamage` and `::ResetTicksToPickHit` (IL):

```
damage per hit = 80 if building.isNaturalRock else 40
ticks per hit  = round(100 / MiningSpeed)   -> 100 at nominal
ticks per cell = ceil(MaxHitPoints / damagePerHit) * 100
labor per unit = ticks per cell / building.mineableYield
```

**Harvesting**, from `plant.harvestWork` / `plant.harvestYield`, plus
`sowWork` where the plant is sowable.

Growing time is deliberately excluded — it is elapsed time with no pawn
attached, so it is not labor. Mining assumes full `MiningYield`. Prospecting
and travel are not counted.

## The decisive case

Four minerals are defined with *identical* extraction parameters:

| mineable | MaxHitPoints | natural rock | yield | ticks/unit | MarketValue |
|---|---|---|---|---|---|
| MineableSteel | 1500 | yes | 40 | 47.5 | **1.9** |
| MineableSilver | 1500 | yes | 40 | 47.5 | **1.0** |
| MineableJade | 1500 | yes | 40 | 47.5 | **5.0** |
| MineableGold | 1500 | yes | 40 | 47.5 | **10.0** |

Same rock, same hit points, same yield, same labor — **a 10× price spread**.
Whatever sets the price of gold, it is not the labor to extract it. This is
not a noisy correlation that needs statistics to interpret; it is four defs
with byte-identical extraction cost and deliberately different prices.

## But the industrial materials do track labor

Where Tynan *wants* labor to matter, he encodes it in `MaxHitPoints`:

| product | ticks/unit | MarketValue | price per labor tick, ÷ 0.0036 |
|---|---|---|---|
| WoodLog | 22.5 | 1.2 | 14.8× |
| Uranium | 125 | 6.0 | 13.3× |
| Cloth | 37.0 | 1.5 | 11.3× |
| Steel | 47.5 | 1.9 | 11.1× |
| Plasteel | 250 | 9.0 | 10.0× |

Plasteel has 8000 hit points to steel's 1500 — 5.3× the labor — and is priced
4.7× steel. Uranium, 4000 hit points, sits in the same band. **Across the five
industrial staples the price-per-labor spread is 1.48×.** That is tight enough
to be deliberate.

So the prediction in the brief was half right: **gold breaks, plasteel does
not.** Plasteel is one of the most labor-consistent materials in the game.

## The whole set

Correlation across all 30 (see `out/primitives.csv`):

| measure | value |
|---|---|
| Pearson, log labor vs log price | **+0.589** |
| Spearman rank | +0.539 |
| Pearson, raw | +0.384 |

Moderate, and the moderation is entirely driven by a legible outlier group.
Median price per unit of extraction labor is 11.3× the game's own
manufacturing labor price, with a 98× spread from the cheapest to the dearest.

**Priced far above their labor** — rarity- and role-gated goods:

| product | × labor-consistent rate | why |
|---|---|---|
| GauranlenSeed | 97.2× | quest/event-gated, not producible on demand |
| Ambrosia | 83.3× | spawns only from a map event |
| Drug_Psilocap | 69.4× | drug |
| Gold | 58.5× | luxury/beauty material |
| RawFungus | 53.6× | cave-biome gated |
| Obsidian | 37.0× | luxury/beauty material |
| Jade | 29.2× | luxury/beauty material |

**Priced below** — Dye (1.0×), Bioferrite (2.2×), Chocolate (3.9×),
RawToxipotato (3.9×), RawRice (5.0×), Silver (5.8×).

Silver's position is definitional rather than economic: silver *is* the unit
of account, pinned at `MarketValue 1`, so its ratio measures the numéraire,
not a judgment about mining.

## The finding that matters for the mod

**Extraction labor and manufacturing labor are priced an order of magnitude
apart.**

- An hour of extraction labor generates a median **101 silver** of value.
- An hour of manufacturing labor generates exactly **9 silver** — the fixed
  `0.0036 × 2500` coefficient, by construction.

An 11× asymmetry, and it is structural rather than incidental: the
manufacturing rate is a single hardcoded constant while the extraction rate
emerges from ~400 independently authored numbers that were never reconciled
against it. In RimWorld's economy essentially all value originates at the
point of extraction, and crafting adds a comparatively negligible margin over
the value of its inputs.

## Verdict

Tynan prices **industrial inputs by labor** and **luxury, currency, and
rarity-gated goods by role**. The dividing line is not a spectrum with noise
on it — it is two populations. Materials that exist to be consumed by
production get labor-proportional prices maintained through a hit-points
dial; materials that exist to be desired, hoarded, or traded get prices set
by what the designer wants them to feel worth.

That is precisely the use-value/scarcity boundary the mod cares about, and it
is already drawn in the data. The labor ledger does not need to impose it —
it needs to *read* it, and the residual against a labor-consistent baseline
is a usable measure of how far a good's price is set by rarity rather than
production.

## Caveats

- 30 primitives is a small n, and the strong claim rests on the four-mineral
  identity case rather than on the correlation.
- Alternative extraction paths (deep drilling, smelting slag, tree-farming vs
  wild harvest) are not enumerated; the cheapest-labor path per product is
  used where more than one was found.
- Animal products (meat, leather, milk, wool) are excluded — their defs are
  generated at load by `ThingDefGenerator_Meat` and are not present in XML.
- `MiningYield` and `PlantHarvestYield` are taken at nominal; both vary with
  pawn stats in play.
