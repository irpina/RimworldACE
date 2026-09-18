# What RimWorld thinks things are worth

A study of the two value systems inside RimWorld — hand-authored prices and
labor time — and what happens when you compute one independently of the other.

**Target:** RimWorld 1.6.4871 rev590, Core + Royalty, Ideology, Biotech,
Anomaly, Odyssey.
**Method:** game assemblies disassembled directly; production graph solved
from extraction outward without reference to price.
**Validation:** every derived quantity checked against RimWorld's own runtime
figures, which caught seven errors in *this analysis* before they reached
these conclusions.

---

## The short version

RimWorld prices a manufactured good as *the value of its inputs, plus one
hardcoded constant times the work to make it.* That constant is **9 silver per
work-hour**.

But the input prices it starts from — steel, wood, cloth, and ~400 other
hand-authored numbers — embed a substantially higher implicit labor rate.

Nobody ever reconciled those two numbers. The result is a seam running through
every price in the game, on a boundary nobody drew deliberately: **labor spent
extracting materials is priced several times higher than labor spent
transforming it.**

How many times higher depends on how you weight the estimate — from about **3×
across typical goods to about 14× across the game's total value**. The
direction is robust to every estimator tested; the magnitude is not. Both
figures, and what drives the difference, are in Finding 1.

---

## Finding 1 — Extraction labor is priced several times above fabrication labor

The project set out to compare two value systems that were never reconciled:
`workAmount` (labor time) versus `BaseMarketValue` (authored price). That turned
out to be the wrong pair. RimWorld already computes price *from* work, so the
comparison is partly circular by construction.

The real seam is inside `BaseMarketValue` itself.

With embodied labor solved independently of price — 653 defs, seeded at
extraction, no market value anywhere in the derivation — you can ask what labor
rate the price structure actually implies. Splitting labor by where it was
spent fits far better than one rate for all of it:

| model | R² (levels) | R² (log) |
|---|---|---|
| one rate for all labor | 0.852 | 0.548 |
| **split into extraction and fabrication** | **0.948** | **0.712** |

**The split is real in both spaces.** One extra parameter buys +0.096 R² in
levels and +0.163 in logs, and the extraction coefficient exceeds the
fabrication coefficient under every estimator tried.

### The magnitude is estimator-dependent, and that matters

| estimator | extraction | fabrication | ratio |
|---|---|---|---|
| OLS in levels | 94.8/hr | 6.8/hr | **14.0×** |
| OLS, equal relative weight | 47.9/hr | 15.7/hr | **3.1×** |
| least squares in log space | 97.6/hr | 26.1/hr | **3.7×** |

*(animal products excluded — see below)*

The 14× figure is real but concentrated: in levels, **the ten most expensive
goods carry 47% of the fit's squared-error weight**, and the top fifty carry
76%. Those are the plasteel-and-components tier — armor, bionics, ship parts —
which are material-heavy by construction. So 14× is a fair statement about
*where the game's total value sits*, and an unfair one about a typical item.

Weight every good equally instead and the gap falls to **3–4×**. That is the
number to defend. The honest headline is that extraction labor is priced
*several times* above fabrication labor, robustly, and that the exact multiple
is a choice about what you are averaging over.

### The gradient

If a single rate governed the economy, a good's implied rate would not move
with its labor mix. It moves monotonically:

| fabrication share of a good's embodied labor | n | median implied rate |
|---|---|---|
| 0–20% | 58 | **114.6** silver/hr |
| 20–40% | 42 | 90.1 |
| 40–60% | 56 | 85.9 |
| 60–80% | 151 | 33.4 |
| 80–100% | 212 | **24.2** |

**Animal products are excluded from this table**, and the reason is Finding 2.
Included, the top bucket reads 345/hr — 3.6× the fitted extraction
coefficient, which would be an outright contradiction. It isn't one: a median
over defs weights a thrumbo hide the same as a steel bar, while least squares
effectively ignores it, so the butchery artifact inflates the top bucket
without touching the fit. Excluded, the top bucket reads 114.6/hr against a
fitted 94.8 — consistent, as it should be.

**In play:** an hour at a workbench adds roughly 7–16 silver of value depending
on estimator. The same hour at a mining face adds roughly 48–95. Crafting
pays poorly; value is claimed where materials enter the colony.

### Why the direction is believable

The regression was never told RimWorld's hardcoded fabrication constant. It
fits `b` from prices and labor amounts derived by separate routes — and returns
**0.0027 against a true value of 0.0036** in levels, within 30%. A prediction
about a number the pipeline never saw.

Independently, the extraction rate of **94.8/hr** matches the **101/hr**
estimated from a different dataset (30 hand-authored primitive prices,
Finding 4) — though see the caveats: those two share their plant-labor input,
so this is consistency, not independent corroboration.

---

## Finding 2 — Butchery has an unbounded body-size gradient

`RecipeDef.WorkAmountTotal` returns a flat `workAmount`, and
`ButcherCorpseFlesh` declares **450 ticks for any carcass**. Butchering a
chicken and butchering a thrumbo cost the same labor. Yields, meanwhile, scale
linearly with body size.

So labor efficiency rises without bound in body size, and nothing in the pricing
pushes back. Grazed megafauna are the most value-dense labor in the game by
orders of magnitude:

| | embodied labor | price | implied rate |
|---|---|---|---|
| Leather_AlphaThrumbo | 0.50 ticks | 20.0 | **100,000 silver/hr** |
| Leather_Thrumbo | 0.62 | 14.0 | 56,000/hr |
| Leather_Mastodon | 0.56 | 3.0 | 13,500/hr |
| Meat_Elephant | 0.62 | 2.0 | 8,000/hr |

Against extraction at ~95/hr and fabrication at ~7/hr. By category, `Leathers`
has a median implied rate of **3,167 silver/hr** and `MeatRaw` **769/hr** — the
two highest in the game, by a wide margin.

This is a design artifact, not a modelling artifact. One flat butchery cost
against size-scaled yields is a straight line with no ceiling.

---

## Finding 3 — A 293× husbandry spread

Grazing and hay-feeding are not variations on a theme; they are different
economies. Both were modelled as competing production paths, with the cheaper
one winning and the gap reported.

Across the 66 animals that support both, the median spread is **9×**. The tail
is far worse:

| | grazed | hay-fed | spread |
|---|---|---|---|
| Meat_Thrumbo | 0.63 | 182.89 | **293×** |
| Meat_AlphaThrumbo | 0.50 | 146.31 | 293× |
| Meat_Mastodon | 0.56 | 93.51 | 168× |
| Meat_Elephant | 0.63 | 92.59 | 148× |

Gestation dominates: a thrumbo gestates 20 days at full adult hunger, and that
is most of what raising one costs.

**Pasture access, not animal choice, is what decides whether livestock is
nearly free or ruinously expensive.** That difference is invisible in the
game's own numbers.

---

## Finding 4 — Gold: the cleanest statement that RimWorld prices scarcity, not work

Four minerals are defined with *byte-identical* extraction parameters — 1500 hit
points, natural rock, yield 40, so 47.5 ticks of mining per unit:

| mineable | hit points | yield | ticks/unit | market value |
|---|---|---|---|---|
| MineableSilver | 1500 | 40 | 47.5 | **1.0** |
| MineableSteel | 1500 | 40 | 47.5 | **1.9** |
| MineableJade | 1500 | 40 | 47.5 | **5.0** |
| MineableGold | 1500 | 40 | 47.5 | **10.0** |

Same rock, same labor, **10× price spread**. This needs no statistics to
interpret: it is four defs with identical extraction cost and deliberately
different prices.

Gold's price per unit of extraction labor is **58.5×** what the game pays for
fabrication labor.

### But the industrial materials *do* track labor

Where labor is meant to matter, it is encoded in mineable hit points:

| product | ticks/unit | market value | price per labor tick (÷ 0.0036) |
|---|---|---|---|
| WoodLog | 22.5 | 1.2 | 14.8× |
| Uranium | 125 | 6.0 | 13.3× |
| Cloth | 37.0 | 1.5 | 11.3× |
| Steel | 47.5 | 1.9 | 11.1× |
| Plasteel | 250 | 9.0 | 10.0× |

Plasteel has 8000 hit points to steel's 1500 — 5.3× the labor — and prices at
4.7× steel. **Across the five industrial staples the price-per-labor spread is
just 1.48×.** That is tight enough to be deliberate.

So the picture is two populations, not a spectrum: materials that exist to be
*consumed by production* get labor-proportional prices maintained through a
hit-points dial. Materials that exist to be *desired, hoarded or traded* get
prices set by what the designer wants them to feel worth, and the dial is
ignored.

Across all 30 measurable primitives, correlation of extraction labor with
authored price is **+0.589** (Pearson, log-log) — moderate, and the moderation
is entirely the rarity-gated outlier group: Gauranlen seed 97×, ambrosia 83×,
psilocap 69×, gold 58×.

---

## Supporting finding — recipe ingredient counts are not counts

If you have ever read a RimWorld recipe def, this is worth knowing.

`Make_ComponentSpacer` asks for `<Gold>0.3</Gold>`. It does not consume a third
of a gold bar. It consumes **three**.

A recipe's `<count>` is denominated in *ingredient-value units*, not thing
counts, and the conversion is per-ingredient:

```csharp
CountRequiredOfFor = ceil(count / IngredientValueGetter.ValuePerUnitOf(def))
    volume getter:     IsStuff ? (smallVolume ? 0.1 : 1.0) : 1.0
    nutrition getter:  IsNutritionGivingIngestible ? Nutrition : 0
```

So gold and silver — the only two small-volume stuffs in the game — are
denominated in tenths. And every cooking recipe uses the *nutrition* getter, so
`CookMealSimple`'s `count 0.5` means **ten units** of a 0.05-nutrition food,
not half a unit.

Reading these fields at face value understates gold-bearing recipes by 10× and
meal ingredients by 20×. It is not documented anywhere, and it is invisible
unless you check against the game's own computed figures.

## Supporting finding — where the designer overrode the formula

49 defs carry an authored price *and* a computable cost, meaning someone looked
at what the formula produced and typed something else. **34 marked up, 12 down,
3 at parity.**

The dominant pattern is not repricing but **flattening a category to one round
number**:

| shell type | formula says | priced at |
|---|---|---|
| Shell_EMP | 92.5 | 55 |
| Shell_Incendiary | 65.0 | 55 |
| Shell_HighExplosive | 63.0 | 55 |
| Shell_Smoke | 47.5 | 55 |
| Shell_Toxic | 42.0 | 55 |
| Shell_Deadlife | 18.75 | 55 |

A 4.9× cost spread collapsed to a flat price. All eight inert relics sit at 500
against a computed 200; six mechanitor implants at 1200 against 640–1912.

Every authored value in the set is a round number. Not one computed value is.

Where they genuinely diverge, it is the predicted cluster: **every drug in the
game is marked up and not one is marked down**, with the Anomaly serums at
10–11× (JuggernautSerum: computed 17.50, priced 200).

---

## How it was done

**Reading the game.** No decompiler was installed, so the analysis reads
`Assembly-CSharp.dll` through a from-scratch ECMA-335 metadata and IL reader
(~700 lines, built on `pefile`). Every formula quoted here is transcribed from
disassembled IL, not recalled.

**Breaking the circularity.** RimWorld's own formula makes the central question
unaskable: it *sets* the price of labor and seeds the recursion with authored
prices, so asking what rate the data implies just returns the constant you fed
in. The solver avoids this by computing embodied labor from extraction and
production work amounts only — no market value enters the derivation at any
point. That gives an independent labor measure to regress price against.

**The solve.** Minimum-cost hyperpath from extraction, relaxed to a fixed
point; converges in 4 iterations over 653 defs. Cycles (steel → components →
machines → steel) need no special handling: option costs are non-negative and
monotone, so a cycle can never lower a cost and simply never wins.

**Judgment calls, made explicit.** Three questions had no single right answer,
and each is a documented switch rather than a silent assumption:

- *Scavenging.* Components can be mined from ancient ruins for 1250 ticks or
  manufactured for 5570. Socially necessary labor is a reproduction cost, so
  mining a manufactured good out of a finite deposit is excluded by default.
- *Mining spoil.* A granite cell drops a chunk 25% of the time. Charging chunks
  the full dig halves the extraction rate and drops R² by 0.09; treating them
  as free spoil restores both. **The data settled this one**, and it says
  RimWorld prices stone as though the chunk were free.
- *Joint production.* One carcass yields meat and leather. Here the same test
  does **not** discriminate — every apportionment rule gives identical
  aggregates to three decimals, because animal products are too labor-cheap to
  move the fit. Reported as a limit of the method rather than papered over; the
  rule was then chosen on principle (physical, non-circular).

---

## How far to trust it

Every derived quantity was checked against RimWorld's own runtime figures,
exported from the game's developer tools. This is a genuine oracle — the game
computing the same quantities at runtime with every generated def present —
not a self-consistency check.

| check | result |
|---|---|
| base market value, all categories | **92/92** |
| calculated market value (the override set) | **33/33** |
| recipe ingredient values | 6/6 |
| recipe product values | 13/13 |
| animal meat yields | **125/125** |
| animal body sizes | **125/125** |
| animal nutrition-to-adulthood | **100/100** |

Those checks caught **seven errors in this analysis**, all now fixed. They are
mistakes in the modelling, not defects in RimWorld:

1. Gestation omitted from animal rearing cost entirely.
2. An off-by-one in the life-stage walk (RimWorld charges each interval at the
   rate of the stage being *entered*).
3. Missing `postProcessCurve` on meat and leather yields — every small animal
   understated.
4. `gestationPeriodDays` defaults to **−1**, not 0, and the negative propagates.
5. Recipe `<count>` read as a thing count (see the supporting finding above).
6. Pairing the cheapest count with a different alternative's price.
7. `MarketValue` inherits `roundToFiveOver = 200` from an abstract parent, so
   values above 200 round to the nearest 5. This is why an assault rifle
   computing to 482 actually prices at 480.

Errors 4 and 7 share a cause worth naming: **RimWorld's defaults and inherited
fields are invisible in the XML you can read.** Both were found only because
the game's own numbers disagreed.

### What is *not* validated

**Plant harvest labor.** Mining labor was verified against `JobDriver_Mine` IL.
Plant harvest was taken directly from `harvestWork`/`harvestYield` with no
cross-check against the game.

The exposure is bounded, but not by the argument you might reach for first: the
30-primitive estimate and the full solve are *not* independent here — 22 of
those 30 primitives are harvested, and both estimates read the same
`harvestWork` field. Their agreement is shared-input consistency, not
corroboration.

The real bound is direct sensitivity. Scaling every plant's harvest labor and
re-solving:

| harvest labor scaled | extraction | fabrication | ratio | R² |
|---|---|---|---|---|
| ×0.50 | 92.4/hr | 7.6/hr | 12.1× | 0.940 |
| ×1.00 | 94.8/hr | 6.8/hr | 14.0× | 0.948 |
| ×2.00 | 93.7/hr | 6.7/hr | 13.9× | 0.951 |

**A factor-of-two error in plant harvest labor moves the extraction
coefficient by about 3%.** Aggregate extraction labor is dominated by minerals
feeding the expensive material-heavy goods, so plants simply do not carry
enough weight to threaten Finding 1. The caveat is real but small.

### Other limits

- 1285 defs have no embodied-labor value. Most are not economic goods at all —
  motes, projectiles, races, standing plants, construction stubs. The
  meaningful remainder is ~91 trade- and quest-only goods (shards, subcores,
  chips, Gravcore, Neutroamine). Those are **not a gap but a category**:
  RimWorld's high-tech tier is *acquired, not produced*, and has no labor
  content by any honest accounting.
- Hunting is deliberately not modelled — its labor is combat time, a function
  of weapon, skill and animal health, none of which is a def field. Modelling
  it would mean inventing numbers.
- Eggs, milk and wool are not incorporated.
- Extraction assumes nominal mining speed and yield, and excludes prospecting,
  hauling and travel. Real extraction labor is *higher*, which would widen the
  14× gap, not narrow it.

---

## The playable version

A mod puts this in front of a player: two read-only stats on the info card of
every producible thing — labor embodied in it, split extraction versus
fabrication. No gameplay change, no save impact.

It needs **no compiled code at all**. A `StatDef` with the default worker
simply reads `statBases`, so precomputed values can be written in by XML patch.

| | |
|---|---|
| defs patched | 543 |
| xpaths resolving | 543/543 |
| skipped | 104 generated meat defs — no XML node exists to patch |

What a player sees: steel `0.79s / 0s`, granite blocks `0s / 1.33s`, a
component `9.5s / 83.33s`, an assault rifle `114s / 1250s`, a parka
`0.67s / 133.33s`.

That parka line is the point. It is almost pure fabrication labor, because
grazed leather costs essentially nothing — a fact invisible in any spreadsheet
but obvious the moment it sits on the item.

---

## One line to carry forward

The two unreconciled value systems in RimWorld are not `workAmount` versus
`BaseMarketValue`.

They are **extraction labor versus fabrication labor, priced several times
apart inside `BaseMarketValue` itself** — roughly 3× across typical goods and
14× across the game's total value. A seam nobody drew on purpose, running
through every price in the game.
