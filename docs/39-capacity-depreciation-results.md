# Capacity depreciation and exit: results

`docs/38` made five numbered predictions. Three were right, two were wrong,
and the two wrong ones are the same mistake made twice: **I predicted a
collapse, and what the model does instead is discipline.**

## 1. What shipped

Plant wears on the calendar rather than on output. Capacity falls by exactly
the part of a day's wear that was not made good — there is no decay rule and
no exit rule anywhere in the code. Two things can refuse a replacement:
matter (the region cannot supply the bill) and money (the producer cannot
carry the maintenance), and the second is off by default.

`capacity_exit()` is the scenario. Five metrics frozen, 170 tests.

## 2. Right: 8.1 and 8.2, the time-based draw

Predicted `capital_goods.department_one.steel_per_day` would go from 0.135916
to about 0.1459 and that nothing else would move. Measured **0.146496**, and
the profit rate, the seven basics and every labor value are unchanged **to
the last digit**:

| metric | before | after |
|---|---:|---:|
| `department_one.steel_per_day` | 0.135916 | 0.146496 |
| `department_one.labor_share` | 0.001837 | 0.001971 |
| `production.profit_rate` | 0.518250 | 0.518250 |
| `production.basics` | 7 | 7 |
| `value.components` | 5654.891129 | 5654.891129 |

The capital-goods equilibrium still reports a price range of **exactly zero**
in all nine commodities in both regions, and capacity is **exactly** constant
— `1.0` is still `1.0`, not `0.9999999999`.

The debt `docs/37` §7 named is paid, and the test pins the closed form: a
region held at zero stock loses its plant at `1/L` a day, landing on
`0.4 × (1 − 1/600)^60` to nine places.

## 3. Right: 8.4, the economy does not die

Predicted "a *lower* capacity and a *higher* price, not a collapse to zero."
That is exactly what happens — though §4 shows it happens to a different
sector than the one the prediction named.

## 4. Wrong: 8.3, the cascade that did not happen

Predicted: components decay from a negative margin, their stock runs out, no
sector can replace plant needing components, and yayo, leaves, chemfuel and
meals decay too. Predicted survivors: steel, wood, garments, herbal medicine.

**Measured: one sector loses capacity, and it does not exit.**

| day | components capacity | every other sector |
|---:|---:|---|
| 0 | 0.06250 | unchanged |
| 500 | 0.02714 | unchanged |
| 1000 | 0.01179 | unchanged |
| 2000 | 0.00222 | unchanged |
| 2250 | 0.00205 | unchanged |
| 4000 | 0.00205 | unchanged |

The decay is exact — `0.0625 × (1 − 1/600)^250 = 0.04119` and the model gives
0.04119 — and then at about day 2,200 **it stops**, and the economy sits at a
new rest point that 400 further days do not move by 1e-12 in any price or any
capacity.

### 4.1 Why it stops, which is the actual result

The component sector loses 6.12 silver on a 32-silver product (`docs/37` §6),
so it covers none of its maintenance and sheds `1/L` a day. But what it sheds
is **idle** capacity: it was running at 3% utilization, and output is fixed by
what the circuit asks of it, not by what it could make. So for two thousand
days the sector shrinks and produces exactly as much as before.

Then capacity approaches output, utilization approaches 1, the inventory
target falls with capacity, and the price machinery does what it is for:

| | day 0 | day 4000 |
|---|---:|---:|
| capacity | 0.06250 | 0.00205 |
| output | 0.001777 | 0.001793 |
| price | 32.00 | 38.34 |
| effective unit cost | 38.12 | 38.12 |
| margin per day | −0.0109 | **+0.000412** |
| maintenance per day | 0.0104 | 0.000343 |
| coverage `rho` | 0.0 | **1.0** |

**The price rose 19.8% and the maintenance bill fell by thirty times, and
they met.** The sector stops shedding at precisely the point where the margin
covers the day's upkeep, because that is the only place `rho` reaches 1.

This is the classical adjustment, and the model produced it without being
told: capital leaves a sector that cannot pay for itself until the
contraction raises the price enough that the remaining capital can. Nothing
in `_shed_capacity` knows about prices, output or equilibrium. It knows how
much of the wear was replaced.

The prediction was wrong because I reasoned about the *sector* — negative
margin, therefore death — instead of about the *plant*. A loss-making sector
that is 97% idle does not die of shedding the 97%.

## 5. Wrong: 8.5, and a convention that was never stated

Predicted the rate of profit would rise, since shedding plant shrinks the
advance and fixed capital is 13.05% of it.

**Measured: 0.518250 before and 0.518250 after, unchanged to six decimals.**

The reason is a convention I introduced in `docs/36` and did not write down.
`social_fixed_capital` reports the plant behind a unit of output as
`machines_per_capacity × bill` — the technique's coefficient, which is
machines per unit of daily output *at full utilization*. Idle capacity never
enters it. So shedding idle capacity cannot move `r`, and the prediction was
reasoning about a quantity the price system does not read.

The convention is defensible and is now documented: prices of production are
long-period prices for a technique operated normally, Sraffa's system has no
notion of utilization at all, and charging idle plant into a long-period
price would make it depend on a short-period fact — the same objection
`docs/23` raised against use-based depreciation in the price anchor.

But it has a consequence worth reporting, because it is a third instance of
the pattern `docs/37` §3.7 identified:

| plant, in work-ticks | |
|---|---:|
| what the price system implies (technique, full utilization) | 17,007.4 |
| what the ledger actually holds (`capital_advanced`) | 18,255.0 |
| ratio | 0.9317 |

**The two differ by 6.8%, and the difference is idle capacity.** It is small
only because the two sectors holding 89.6% of the plant — yayo and psychoid
leaves — both run at capacity. A model with more idle plant would see the two
diverge much further.

Three times now the project has found the same shape: the value ledger and
the price system measure related quantities that are not the same quantity —
`docs/30` on stocks against flows, `docs/37` on the composition of the
advance, and this on utilization. It is worth stating as a standing rule:
**no number measured in one of these accountings may be quoted into the
other without deriving it again.**

## 6. A smaller correction, found while checking the ledger

`_replace_plant` booked the **full** construction labor even when only part
of the materials arrived. The flow identity still closed — the labor was
booked as living labor and as plant value on the two sides — but the stock
story did not: it claimed to have built plant that no capacity corresponded
to. Construction labor is scaled by the supplied fraction now. You cannot put
up the part of a machine whose steel never came.

No metric moved, because in every stationary scenario the supplied fraction
is exactly 1.

## 7. On the scenario's length

`docs/38` proposed 600 days — ten years, and one service life — on the
grounds that a rule expressed as a fraction of a day's wear needs a service
life before it has said anything. That was not nearly long enough. At 600
days the picture is a decay in progress with no rest point, which is a
misleading result rather than a shorter one. The default is **4,000 days**,
because the thing worth seeing begins at about 2,200.

That is itself a finding about the mechanism: `1/L` a day is slow, and a
sector with an order of magnitude of idle capacity takes several service
lives to work through it. Any future rule expressed per-day against a
600-day life should assume the same.

## 8. What is still missing

- **Mothballing**, deliberately (`docs/38` §5): idling plant to arrest its
  decay needs a rule about *expected* future demand, and expectations here
  are one exponentially-smoothed price.
- **Moral depreciation** — plant devalued by a better technique appearing
  rather than by wear. `technique_change` is where it would show.
- **The money rule stays off by default**, and not because it is unfinished.
  Turning it on shrinks Department I by a factor of thirty over sixty-six
  years. That is a real consequence of a real RimWorld price and the
  flagship equilibrium should not carry it silently.
- **Social labor value still cannot migrate to a superseded technique.** The
  handoff listed exit as the blocker; exit exists now, but only a sector
  that cannot cover maintenance sheds, and a superseded producer with a
  positive margin covers it. Exit turns out to be necessary and not
  sufficient, and the missing piece is that a *cheaper* rival must drive the
  incumbent's margin down, which is `cost_competition`'s territory.
- **The sensitivity sweep**, still stale since the cost floor.

## 9. What would make this wrong

- If capacity moves in the capital-goods equilibrium at all, `rho` is not
  exactly 1 where it should be. Frozen as
  `capacity_exit.sectors_that_lost_capacity` = 1.
- If `capacity_exit.components.coverage` ever falls below 1.0, the rest
  point in §4 is not one and the sector is still decaying.
- If steel or wood ever appears in `capacity_lost`, something is charging
  wear to a process with no bill of materials. There is a test.
- §5's claim that the price system cannot see idle plant depends on
  `social_fixed_capital` keeping the full-utilization convention. If a
  later change makes it read the installed stock, `r` becomes
  utilization-dependent and every profit rate the project has reported
  since `docs/37` needs re-deriving.
