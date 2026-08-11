# Animal products

The last real gap. 516 → 653 defs with an embodied-labor value.

## What had to be reconstructed

Meat defs do not exist in XML — RimWorld generates them at load. Everything
below is read from `Assembly-CSharp.dll`, not assumed:

| source | rule |
|---|---|
| `ThingDefGenerator_Meat.ImpliedMeatDefs` | defName `Meat_<race>`, `BaseMarketValue = race.meatMarketValue`, Nutrition 0.05, Mass 0.03 |
| `RaceProperties..ctor` | `meatMarketValue` defaults to **2.0** |
| XML overrides | only two exist: insects 0.5, humanlikes 0.8 |
| `StatPart_BodySize.TransformValue` | `stat *= bodySize` |
| `MeatAmount` StatDef | `defaultBaseValue` 140 → meat = 140 × bodySize |
| `LeatherAmount` StatDef | `defaultBaseValue` 0, declared per race → leather = declared × bodySize |
| `Pawn.BodySize` | `lifeStage.bodySizeFactor × race.baseBodySize` |
| `Need_Food.BaseHungerRate` | `lifeStage.hungerRateFactor × race.baseHungerRate × 2.6667e-05` per tick (×60000 = ×1.6 nutrition/day) |
| `LifeStages.xml` | baby 0.2/0.4, juvenile 0.5/0.75, adult 1.0/1.0 (bodySize/hunger factors) |

127 rearable animals result. Leather defs already exist in XML (27 of them),
so only meat needed synthesising.

## Competing husbandry paths, not an average

Both paths are hyperpath options; min-cost picks, exactly as with scavenging.

- **graze** — feed labor 0, for the 70 animals whose `foodType` includes rough
  plant matter. Pasture is finite, but that is differential rent, not labor
  content, and is deliberately out of the value calculation.
- **hay-fed** — nutrition to adulthood ÷ 0.05 per hay unit, carrying hay's own
  embodied labor. 100 animals have the life-stage data for this.

66 animals have both. **Median spread 9×**, and the tail is enormous:

| | graze | hay-fed | spread |
|---|---|---|---|
| Meat_Thrumbo | 0.63 | 182.89 | **293×** |
| Meat_AlphaThrumbo | 0.50 | 146.31 | 293× |
| Meat_Mastodon | 0.56 | 93.51 | 168× |
| Meat_Elephant | 0.63 | 92.59 | 148× |
| Meat_Megasloth | 0.63 | 57.38 | 92× |

Grazing always wins where available, so the headline numbers are grazing
numbers. The spread is the cost of *not* having pasture.

**Hunting is not modelled.** Its labor is combat time — a function of weapon,
skill and animal health, none of which is a def field. Modelling it would mean
inventing numbers, so wild animals have no production path unless rearable.

## Validated against the game's own numbers

RimWorld's dev mode exports an **Animal Economy** table that computes several
of these quantities at runtime, with every generated def present. That is a
real oracle, not a self-consistency check. The export is committed at
`data/rimworld_animal_economy.csv`; `validate_animals.py` diffs against it.

It found three genuine bugs in the first implementation:

1. **Gestation was omitted entirely.** `AnimalProductionUtility.NutritionToAdulthood`
   adds `NutritionToGestate` — the mother's food while pregnant — which I had
   ignored. And `GestationDaysEach` amortises it over the litter
   (`gestationPeriodDays / Rand.ByCurveAverage(litterSizeCurve)`), or for egg
   layers over the clutch (`eggLayIntervalDays / eggCountRange.Average`).
2. **An off-by-one in the life-stage walk.** RimWorld charges each interval at
   the hunger factor of the stage being *entered*, not the one being lived
   through.
3. **The post-process curve was missing.** Both `MeatAmount` and
   `LeatherAmount` carry `postProcessCurve` `(0,0) (5,14) (40,40)
   (100000,100000)` — identity above 40, a large boost below. Every small
   animal's yield was understated: a sparrow's raw `140 × 0.12 = 16.8` is
   really 22.8, a dryad's 1.33 is really 3.7.

Plus one field default: `gestationPeriodDays` defaults to **-1**, not 0, and
RimWorld propagates the negative — insects, which spawn from hives rather than
gestate, carry a small negative gestation cost.

Current state: **125/125 meat amounts, 125/125 body sizes, 100/100 nutrition
to adulthood** all within 2% of the game's own figures.

One genuine discrepancy remains, and it is RimWorld's, not ours.
`AnimalProductionUtility` omits the per-day scaling that `Need_Food` actually
applies — `hungerRateFactor × baseHungerRate × 2.6667e-05` per tick, i.e.
×1.6 per day. So the debug table's "nutrition" is 1.6× smaller than what a
pawn really eats, and `NutritionEatenPerDay` (which *does* include the 1.6)
disagrees with it. We keep the 1.6, because we convert nutrition into hay and
hay carries real nutrition; the validator divides it back out to compare.

Net effect of all corrections: the headline two-rate result did not move at
all (95.4 / 6.9 / 13.8× / R² 0.948, identical). The husbandry spread did —
median 5× → **9×**, maximum 146× → **293×**.

## Joint production: the test has limits

One carcass yields meat *and* leather, so `APPORTION` finally becomes
load-bearing. The chunk test that decisively settled mining spoil was applied
again — and **it does not discriminate**:

| apportionment | n | zero-labor defs | extraction | fabrication | a/b | R² |
|---|---|---|---|---|---|---|
| (no animals) | 510 | 0 | 96.5/hr | 6.6/hr | 14.7× | 0.948 |
| meat_only | 623 | **24** | 95.4/hr | 6.9/hr | 13.8× | 0.948 |
| count | 647 | 0 | 95.4/hr | 6.9/hr | 13.8× | 0.948 |
| mass | 647 | 0 | 95.4/hr | 6.9/hr | 13.8× | 0.948 |
| value | 647 | 0 | 95.4/hr | 6.9/hr | 13.8× | 0.948 |

Identical to three decimals. The rules genuinely differ per-def — leather
comes out at 0.000 / 1.000 / 1.000 / 1.038 ticks respectively — but animal
products are so labor-cheap that they cannot move an aggregate fit dominated
by expensive goods. Reported rather than papered over: the criterion that
adjudicated two prior decisions has a range, and this is outside it.

The choice is therefore made on principle:

- **meat_only rejected** — leaves 24 leather defs with literally zero labor
  and a positive price, an undefined implied rate.
- **value rejected** — apportioning by market value reintroduces exactly the
  circularity the solver exists to avoid.
- **mass adopted** — physical and non-circular. Coincides with `count` here
  because meat and leather both have Mass 0.03.

## The finding: butchery work does not scale with the carcass

`RecipeDef.WorkAmountTotal` returns `workAmount` for any thing whose stuff is
null, and `ButcherCorpseFlesh` declares a flat `workAmount` of **450**. So
butchering a chicken and butchering a thrumbo cost the same labor — while
yields scale linearly with body size.

Combined with free grazing, that makes grazed megafauna the most value-dense
labor in the game by orders of magnitude:

| | embodied labor | price | implied rate |
|---|---|---|---|
| Leather_AlphaThrumbo | 0.50 ticks | 20.0 | **100,000 silver/hr** |
| Leather_Thrumbo | 0.62 | 14.0 | 56,000/hr |
| Leather_Mastodon | 0.56 | 3.0 | 13,500/hr |
| Meat_AlphaThrumbo | 0.50 | 2.0 | 10,000/hr |
| Meat_Elephant | 0.62 | 2.0 | 8,000/hr |

Against extraction at ~95/hr and fabrication at ~7/hr. The `Leathers` category
has a median implied rate of **3,167 silver/hr**, the highest of any category
by a wide margin.

This is a genuine design artifact, not an artifact of the model. A single flat
butchery cost against size-scaled yields means labor efficiency rises without
bound in body size, and nothing in the pricing pushes back.

## Effect on the aggregate

The two-rate structure survives intact:

- extraction **95.4** silver/work-hour, fabrication **6.9**, **a/b = 13.8×**,
  R² **0.948** — against 96.5 / 6.6 / 14.7× / 0.948 before animals.
- Agreement with the independent primitives estimate (~101/hr) holds at ~6%.
- The gradient stays monotone, but the low-fabrication bucket jumps from
  114.6 to **387.6** silver/hr, because it is now dominated by animal
  products.

Animals add 137 defs and shift the aggregates barely at all, while occupying
the entire top of the residual distribution. In labor terms, RimWorld's
pastoral sector is nearly free.
