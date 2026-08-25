# The enlarged subsistence basket: design

Written before implementation. `docs/27` promoted this step from third place
to next, on the argument that a meals-only basket is what makes the uniform
profit rate 38 and the derived prices unusable. This document commits, in
section 7, to a prediction that **the promotion was wrong** — that an
honestly-derived basket moves every ratio substantially and still leaves them
nowhere near defensible. Recording that before measuring it is the point.

## 1. Why

The basket has been meals-only since `docs/17`, and every headline number the
project reports is built on it:

| quantity | value | inflated because |
|---|---:|---|
| rate of surplus value s/v | 38.30 | v is the basket |
| organic composition c/v | 20.67 | v is the basket |
| value rate of profit s/(c+v) | 1.77 | v is the basket |
| uniform profit rate r | 38.34 | `r = T / (b·l) − 1` |

Necessary labor is **2.5% of the working day**. A real reproduction bundle is
food, clothing, medicine, shelter and recreation, and the value of
labor-power is understated by whatever the missing components are worth.

This has been flagged as the project's single largest caveat since `docs/17`.
It is time to stop flagging it and measure it.

## 2. What goes in the basket, and where the numbers come from

Every figure comes from `out/embodied_labor.csv` — the closed analysis's
solve for 653 RimWorld defs — and from RimWorld's own `MarketValue`. Nothing
here is chosen to hit a target.

| component | def | embodied ticks | MarketValue |
|---|---|---:|---:|
| food | `MealSimple` | 305.0 | 15.00 |
| clothing | `Apparel_BasicShirt` | 1620.0 | 85.76 |
| medicine | `MedicineHerbal` | 400.0 | 10.00 |

Two new commodities, `garments` and `herbal_medicine`, joining meals,
chemfuel, psychoid leaves and yayo.

### 2.1 Quantities per worker-day

- **Meals: 2.0.** Unchanged. A colonist needs 1.6 nutrition a day and a
  simple meal carries 0.9, so ~1.8; 2.0 has been the calibration since
  `docs/17` and moving it would confound this measurement with a re-tuning.

- **Garments: 0.125.** A cold-biome wardrobe is a shirt, pants, a tuque and
  a parka: `1620 + 1620 + 1940 + 8040 = 13,220` ticks, or **8.16
  shirt-equivalents**, replaced roughly annually. A RimWorld year is 60
  days, so 8.16/60 = 0.136/day. Rounded **down** to 0.125, which is an exact
  binary fraction — the same floating-point hygiene the rest of the
  calibration uses (`docs/17`) — and rounding down keeps the basket
  conservative against the prediction this document is making.

- **Herbal medicine: 0.125.** 7.5 doses a year. Generous for a healthy
  colonist and stingy for a RimWorld one; the same binary-fraction argument
  applies.

### 2.2 What is deliberately left out

**Shelter.** A bed is 1,812 ticks and a wooden room perhaps 3,000 more, over
a service life measured in years. That is **under 20 ticks per worker-day**
— an order of magnitude below the smallest component above. Modelling it
would need a durable consumed as a service by a worker, which is a mechanism
the model does not have and which would buy nothing. Named, quantified, and
skipped.

**Recreation.** Defensible in principle — Marx's "historical and moral
element", and RimWorld colonists genuinely need recreation daily — but the
obvious candidate is yayo, the model's own final good, and putting it in the
basket creates a wage-price feedback loop through the commodity every
existing scenario is measured on. That is a second large change wearing the
same coat as this one. Deferred, with the reasoning recorded so it is a
decision rather than an oversight.

## 3. Design decisions

### 3.1 Garment production consumes chemfuel; medicine does not

The tailoring bench is powered. `docs/08` already made exactly this
stylization twice — chemfuel as an operating input to the psychoid fields
and the drug lab — so this is precedent rather than a new liberty, and it is
flagged the same way.

The coefficient is **derived, not chosen**: the drug lab draws 0.2 chemfuel
per 350 ticks of work, so a garment at 1,620 ticks draws
`0.2 × 1620 / 350 = 0.9257`. Same energy per tick of bench time as the
existing powered process.

Herbal medicine is harvested from soil by hand and draws nothing.

This is not decoration. It makes **chemfuel a basic commodity**: it enters
garments, garments enter the basket, and the basket enters everything. The
model has never had a basic commodity with means of production behind it,
which means it has never shown the general Sraffa case. Section 7 predicts
this matters more than it looks like it should.

### 3.2 Fixed capital for the new sectors, from the same source

| sector | building | ticks | silver |
|---|---|---:|---:|
| garments | `HandTailoringBench` | 3,687.5 | 157.2 |
| herbal medicine | `PlantPot` | 700.0 | 40.9 |

Same rule as `docs/23`: machines in proportion to the labor performed,
depreciated over `capital_service_life_days`. The hand bench rather than the
electric one, to match a process whose energy draw is already stylized
rather than measured.

### 3.3 The calibration convention is untouched

New producers get their operating overhead from the existing
`operating_overhead` rule — total unit cost is `reference_price × 14/21`,
minus input costs at reference. That is what keeps every producer at full
utilization at reference prices, which is what keeps the equilibrium exactly
stationary. Nothing about the seeding machinery changes; two more commodities
simply pass through it.

**The equilibrium scenario must still report a price range of exactly zero,
in both regions, across four in-game years.** If the enlarged basket makes
that unreachable, this document's instruction to its implementer is to stop
and report rather than to loosen the check.

### 3.4 The capacity check is generalized

`equilibrium` currently raises if meal demand exceeds provisioning capacity.
With three basket goods that check has to cover all of them, by name, with
the offending commodity in the message. A silently under-provisioned basket
would show up as a permanent shortfall rather than as an error.

### 3.5 A second scenario bounds the answer from above

`generous_basket` multiplies the non-food components hard — 3 meals, 0.5
garments and 0.5 doses a day, a bundle nobody could call stingy. Its job is
to answer "how far could an honest basket possibly go?" so that the
conclusion is a bound rather than one point estimate.

## 4. Interface

New `ScenarioParameters` fields, per the standing rule that every coefficient
is exposed: reference price, direct labor, labor value, mass, capacity and
basket quantity for each of `garments` and `herbal_medicine`;
`chemfuel_per_garment`; the two buildings' money and labor; and the three
`generous_*_per_worker_day` overrides.

No new model API. The basket is already a `Dict[str, float]` on `Region` and
every mechanism that reads it — the wage rate, worker consumption, throughput
demand, the labor value of the basket, and the price of production system's
wage bundle — is already written against an arbitrary number of goods. If any
of them turns out to assume one commodity, that is a bug this session
exposes rather than a feature it adds.

## 5. Non-goals

- Shelter as a consumed durable service (§2.2).
- Recreation, and the wage-price loop through yayo (§2.2).
- Adopting prices of production. Still an observation.
- A capital-goods sector, capacity depreciation, turnover, monopoly rent.
- Re-tuning the meal quantity, the working day, or the 14/21 cost
  convention. Changing any of those alongside the basket would make the
  measurement uninterpretable.

## 6. Tests

1. Equilibrium is still exactly stationary — zero price range, both regions,
   all six commodities, four years.
2. Material, silver and value ledgers all still close to floating-point zero
   with two more commodities in circulation.
3. Workers actually consume garments and medicine; the basket shortfall is
   zero at equilibrium.
4. The wage equals the three-good basket at current prices.
5. `basket_labor_value` equals the three components at social values.
6. Chemfuel is now basic, and the basics list has grown.
7. `r` is **no longer** `T / Σ(b·l) − 1`: the rank-one identity that held
   for pure-labor wage goods breaks, and the direction of the break is
   asserted.
8. s/v, c/v and the value rate of profit all fall, and the value rate of
   profit falls by far the least — asserted as an ordering, since that is
   the structurally interesting part.
9. `generous_basket` drives s/v lower again and still nowhere near 1.
10. The capacity check fires, by name, when a basket good is
    under-provisioned.

## 7. Predictions

Hand-derived from the coefficients before implementation.

Basket at social labor values, with fixed capital:

```
v(meals)     = 305 + 0.3588                     = 305.3588
v(chemfuel)  = 25 + 0.0449                      =  25.0449
v(garments)  = 1620 + 0.9257×25.0449 + 0.4148   = 1643.599
v(medicine)  = 400 + 0.0194                     = 400.0194

basket = 2×305.3588 + 0.125×1643.599 + 0.125×400.0194 = 866.17 ticks
```

**7.1 The rate of surplus value falls from 38.30 to 26.71.** `T / 866.17 − 1`.
Necessary labor rises from 2.5% to **3.6%** of the working day.

**7.2 The organic composition falls from 20.67 to roughly 14.6**, tracking
`v` almost exactly, since the garments sector adds well under 1% to `c`.

**7.3 The value rate of profit barely moves: 1.77 → about 1.72.** This is
the interesting one. `s/(c+v)` has `c` in the denominator, and `c` is twenty
times `v`, so a 42% enlargement of `v` moves the ratio by 3%. **Enlarging the
basket fixes two of the three headline ratios and does almost nothing to the
third.**

**7.4 The uniform profit rate falls to 24.62, and — for the first time — is
not the rate of surplus value.** With pure-labor wage goods the augmented
matrix restricted to the basket is the outer product `(l/T)·bᵀ`, whose only
non-zero eigenvalue is `Σ b·l/T`; that rank-one structure is why `r` has
been exactly `s/v` until now, however many wage goods there are. One material
input into one wage good breaks it. Solving the resulting quadratic:

```
305k(2.827868 + 0.00948469k) = 24000   →   k = 25.6238,  r = 24.6238
```

against `Σ b·l / T` giving `r₀ = 26.8261`. So `r` sits **8.2% below** the
rank-one figure, and **7.8% below s/v** — a real structural divergence, not
the 0.12% fixed-capital omission of `docs/27`.

The mechanism is worth stating because it is the general Sraffa case in one
sentence: **the price system marks material inputs up by `k` and the value
system does not.** Chemfuel enters a garment's value at 25 ticks flat and
enters its price at 25.6 times its own price.

**7.5 Prices of production improve and remain unusable.** With `k = 25.62`
instead of 39.34, relative to meals:

| commodity | labor value | price of production | authored |
|---|---:|---:|---:|
| meals | 1 | 1 | 1 |
| chemfuel | 0.08202 | 0.08197 | 0.15333 |
| herbal medicine | 1.31005 | 1.31148 | 0.66667 |
| garments | 5.38253 | **7.25575** | 5.71733 |
| psychoid leaves | 0.15554 | 0.25649 | 0.12667 |
| yayo | 2.41020 | **54.1462** | 1.40000 |

Yayo against its authored ratio falls from **71.6× to 38.7×**. Better by
nearly half, and still absurd.

**7.6 The headline: `docs/27` reordered the backlog on a wrong premise, and
this document expects to have to say so.** The basket was not what stood
between the model and a usable price system. What stands there is RimWorld's
own productivity: a simple meal embodies 305 ticks and a worker performs
24,000 a day, so **one provisioner feeds thirty-nine workers**. A profit rate
near 1 needs a basket embodying half a working day — 12,000 ticks, or
**39 meals a day**, or seven shirts a day. No bundle a person could defend
gets within an order of magnitude.

If that holds, the honest conclusion is that the rate of surplus value the
model reports is not an artifact to be calibrated away. It is what RimWorld's
authored work amounts say, and the question shifts from "how do we fix the
basket" to "is the excluded upstream labor, or the working day, or the
boundary of the modelled circuit, where the missing labor actually is".

**7.7 `generous_basket` reaches s/v ≈ 11.4 and stops.** Basket 1,937.9 ticks.
An indefensibly large bundle still leaves the rate of surplus value an order
of magnitude above anything in the literature.

**7.8 Behavioral metrics move, and should.** Unlike the last two sessions
this is a real change to the model. Wages roughly 1.4×, every producer's
effective cost up by the wage component, employment up ~1.7% from two new
sectors. The frozen reference will need rewriting with the movement
explained, not suppressed.

## 8. What would make this wrong

If s/v lands near 1 rather than near 27, the basket quantities in §2.1 have
been mis-derived by an order of magnitude and every conclusion here is void.

If `r` comes out exactly `T / Σ(b·l) − 1` after the chemfuel link lands, the
link is not reaching the price system and §7.4's structural claim is untested
rather than confirmed.

If the equilibrium stops being exactly stationary, the seeding convention
does not generalize past one basket good, and that is a finding about the
calibration machinery which must be reported before any economics is drawn
from the run.
