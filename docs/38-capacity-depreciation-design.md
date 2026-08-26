# Capacity depreciation and exit: design

Written before implementation. `docs/37` §7 left this item a specific debt —
a replacement shortfall is not throttled, so a region that cannot replace its
machines runs them into the ground and nothing notices — and the handoff has
listed competitive *exit* as an omission since the beginning: a producer that
loses the order book keeps its capacity forever, keeps inflating throughput
demand and inventory targets through the full-capacity convention, and would
take its share straight back.

Section 3 is a result found while designing this, and it is the reason the
design is shaped the way it is.

## 1. Why

Three separate holes, and they close in two pieces.

**Plant does not wear out unless it is used.** `docs/23` chose use-based
depreciation deliberately, so that idle plant could not feed a rising unit
cost back into the price anchor. That was the right choice *for the price
anchor* and the wrong physics for the stock: a refinery standing idle rusts
at the same rate as a refinery running flat out.

**A replacement shortfall has no consequence.** `docs/36` made replacement
material and `docs/37` §7 named what it did not do: a region short of
components draws what it can, books the shortfall as unmet demand, and keeps
its capacity anyway. The plant is charged to the product whether or not it
was replaced. That is the last place in the model where something is consumed
and nothing is lost.

**Nothing ever exits.** Competition is for orders, never for survival. This
also blocks a result the project wants for other reasons: social labor value
cannot migrate to a superseded technique while the superseded producer keeps
its capacity, so it rests at the mix average forever (`docs/20`).

## 2. The two pieces

### 2.1 Replacement becomes time-based, and that is a consistency fix

The plant behind a producer wears at `capacity / L` per day, not
`output / L`. Buildings age on the calendar.

This is not only better physics; it removes an inconsistency that has been in
the model since `docs/36` shipped. `Region.throughput_demand` has *always*
sized the replacement draw at full capacity — the same full-capacity
convention the derived-input term uses — while `_produce` drew it at actual
output. Targets were sized for one basis and stock consumed on the other.

It costs 7–15% more matter, not more:

| good | use-based draw | time-based draw | ratio |
|---|---:|---:|---:|
| steel | 0.046640 | 0.050468 | 1.08 |
| wood | 0.012510 | 0.014401 | 1.15 |
| components | 0.001777 | 0.001898 | 1.07 |

Small because the sectors holding the plant — yayo at 67.3% of it and
psychoid leaves at 22.3% — already run at full capacity, and the sectors with
idle capacity have little plant or none.

**The value transferred to the product stays use-based.** `docs/23`'s reason
still holds and nothing about it has changed. The two bases coexist without
double counting, and the identity still closes:

```
commodities produced   =  inputs·λ  +  K/L (use)  +  direct labor
plant rebuilt (time)   =  materials·λ            +  construction labor
```

Sum the two and every term on the left appears once on the right. The gap
between time-based wear and use-based transfer is not a leak — the plant is
physically replaced, so the stock is constant; it simply transfers less to
the product than it costs to maintain. That gap *is* the fixed cost of idle
capacity, and §2.2 is what happens when a producer cannot carry it.

### 2.2 Capacity falls only where replacement fails

No decay rule, no exit rule, no threshold. Capacity is constant while the
plant is replaced, and falls by exactly the fraction of the wear that is not.
Two things can stop a replacement and both are proportional:

**Matter.** The region cannot supply the bill. The unsupplied fraction of the
day's wear is not made good and capacity falls by it. This is `docs/37` §7's
debt, and it is the whole of "runs them into the ground".

**Money.** A producer replaces plant in proportion to how much of the day's
maintenance its margin covers:

```
maintenance  =  capacity / L * machine price
margin       =  output * (price - effective unit cost)
rho          =  clamp(margin / maintenance, 0, 1)
```

Continuous, damped, and the mirror image of the entry rule: `_invest` builds
when expected revenue clears cost by a margin, and `rho` maintains in
proportion to whether it does. A producer that keeps its orders covers its
maintenance many times over and `rho` is 1, so **nothing moves in the
stationary state** and the equilibrium stays exact. A producer that loses the
order book earns nothing, covers nothing, and sheds capacity at `1/L` a day.

Retirement at `capacity < 1e-9` is housekeeping, not economics: exponential
decay never reaches zero and a list of ten-thousandth-of-a-machine producers
is a performance problem, not a market outcome.

## 3. Why the obvious design is wrong: idle decay has no stationary state

The first design here was the obvious one — idle plant decays, used plant is
replaced, so capacity converges on output. It was checked before it was
written, by iterating the capacity map offline, and it does converge. It
converges onto a wall.

`_assert_basket_provisioned` refuses a seeded circuit in which a basket good's
demand *meets or exceeds* its capacity, because a basket at exactly its
capacity has no reserve and any perturbation starves the workers. Driving
capacity down to output does precisely that, and the iteration terminates
with:

```
equilibrium 'garments' demand (0.039768/day) meets or exceeds
capacity (0.039768/day)
```

That is not an inconvenience to route around. **A rule that sheds all idle
capacity has no stationary state with a reserve, and a reserve is what an
economy facing shocks needs.** Excess capacity is not waste to be optimized
away; it is what lets the circuit absorb a bad day. The classical reading is
the same one: competition maintains reserve capacity, and a model that
eliminates it has assumed the shock away.

So capacity is not driven toward output. It is driven toward *nothing at all*
— it only ever falls when a replacement actually fails.

## 4. What this predicts about Department I

`docs/37` §6 recorded that `Make_ComponentIndustrial` loses 6.12 silver on a
32-silver component at RimWorld's authored prices once the power stylization
is applied. Under §2.2's money rule, a sector with a negative margin covers
none of its maintenance, so `rho` is zero and **the component sector decays
away**. Every other sector's plant depends on it.

This is a real consequence of a real price, and it is why §2.2 ships **off by
default**. The flagship equilibrium keeps constant capacity and a price range
of exactly zero. `capacity_exit()` is the scenario that turns the rule on, and
its job is to report what happens rather than to survive it.

The alternative was to exempt components, and the only reason to exempt them
would be to keep the scenario alive, which is the one thing the project's
rules forbid.

## 5. Deliberately not done

- **Mothballing.** Idling plant to arrest its decay is a real option and a
  third state between running and exiting. It needs a decision rule about
  *expected* future demand, which the model does not have — expectations are
  a single exponentially-smoothed price. Named, not built.
- **Moral depreciation.** Plant devalued by a better technique appearing,
  rather than by wear. `technique_change` is the scenario that would show it
  and this is not that session.
- **Re-entry after exit.** `_invest` already builds where the margin is
  there, so a sector that exits can come back through the ordinary entry
  path. No special case, and whether it actually does is a result rather
  than a design decision.
- **The sensitivity sweep**, still stale since the cost floor.

## 6. Interface

```python
ScenarioParameters(capacity_exit=True)   # default False is today
scenarios.capacity_exit()                # the scenario
economy.ledger.capacity_lost             # by region and commodity
economy.maintenance_coverage(region)     # rho, per producer
```

## 7. Tests

1. Time-based replacement leaves the capital-goods equilibrium exactly
   stationary, and its price range exactly zero.
2. The value identity still closes with the two bases side by side.
3. With the money rule off, no capacity ever moves — bit-identical.
4. A region starved of components loses capacity in the sectors whose plant
   needs them, and *only* those. Steel and wood have no bill and must not
   move.
5. Capacity lost is proportional to the shortfall, not a step: half the
   materials must lose half the wear.
6. A producer that loses its entire order book decays at `1/L` a day, and
   one that keeps it does not decay at all.

## 8. Predictions

**8.1 The time-based draw moves Department I's frozen metrics by 7–15% and
nothing else.** `capital_goods.department_one.steel_per_day` goes from
0.135916 to about 0.1459. The profit rate, the basics, and the labor values
should not move at all: replacement is 0.18% of labor and the price system
reads the plant *stock*, which time-basing does not touch.

**8.2 The capital-goods equilibrium stays exactly zero.** Replacement at
capacity is a constant where replacement at output was also a constant, so
the stationary state is no harder. If it does not, the two calibration paths
disagree about the basis and the fix is in them, not in the check.

**8.3 With the money rule on, components exit and take the rest with them.**
Components decay at `1/L` from a negative margin. Once their stock is gone,
no sector can replace plant that needs components — yayo, leaves, chemfuel
and meals — so those decay too, at the rate their own materials run out.
Garments and herbal medicine are wood-only and should survive. Steel and wood
have no plant at all and cannot decay. **Predicted survivors: steel, wood,
garments, herbal medicine.**

**8.4 The economy does not die.** Yayo and leaves decay but final demand does
not, so price rises, and `_invest` rebuilds where the margin justifies it.
The prediction is a *lower* capacity and a *higher* price, not a collapse to
zero. If everything goes to zero, the entry path is broken and that is the
finding.

**8.5 The rate of profit rises.** Fixed capital is 13.05% of the price
system's advance (`docs/37`), and shedding plant shrinks the advance. Since
89.6% of the plant sits in yayo and leaves, both non-basic, most of what is
shed will move `r` by nothing — so the rise should be small and come almost
entirely from meals and chemfuel.

## 9. What would make this wrong

- **If capacity moves in the stationary state at all**, `rho` is not exactly
  1 where it should be, and the equilibrium check will say so before anything
  else does.
- **If capacity lost is not proportional to the shortfall**, a threshold has
  crept in. Test 5.
- **If steel or wood ever loses capacity**, something is charging wear to a
  process with no bill of materials.
- **If the value identity stops closing**, the two depreciation bases are
  being mixed — most likely by booking the time-based wear as a transfer to
  the product instead of as plant rebuilt.
