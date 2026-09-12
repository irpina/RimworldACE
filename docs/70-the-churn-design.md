# The churn: a stock target and a flow reserve fighting over one capacity: design

Written before implementation. `docs/65` §5 found it, `docs/66` and
`docs/68` were each predicted to possibly dissolve it and did not, and
`docs/69` §6 left it as the market slice's only open finding with no
design against it. This document diagnoses it, and the diagnosis is not
what `docs/64` §7 or `docs/65` §5 supposed.

**The headline: it is not entry and exit alternating. With entry on
margin switched off the cycle is bit-identical — same range, same
capacity, same price, same 488 exits. What alternates with exit is the
*investment rule's buffer branch*, and the two are fighting over one
quantity with incompatible targets: exit sizes capacity to a flow, and
the buffer rule sizes it to a stock.**

## 1. What the churn is, measured

All readings are `gravitation` at 1080 days, Dust Basin's yayo, with the
last-60-day price range over its level as the measure — the same metric
`exit.gravitation.local_yayo_last60_range_over_level` freezes.

| run | last-60 range | capacity | price | exits |
|---|---:|---:|---:|---:|
| entry + exit (the baseline) | 0.02517 | 12.134 | 18.416 | 488 |
| **entry off, exit on** | **0.02517** | **12.134** | **18.416** | **488** |
| entry on, exit off | 0.00000 | 11.481 | 19.010 | 0 |
| exit on, buffer branch off | 0.00000 | 11.297 | 19.142 | 64 |
| exit on, inventory target 5 days | 0.00000 | 12.530 | 18.455 | 27 |
| exit on, capacity reserve 0.25 | 0.00011 | 13.201 | 18.609 | 10 |

Read the second and third rows first. Entry on margin contributes
**nothing** to the cycle — turning it off changes not one figure — and
exit alone produces all of it. `docs/65` §5's "entry and exit
alternating" was a reasonable reading of a trace with both rules on, and
it is wrong. The capacity exit withdraws is rebuilt by `_invest`'s
*buffer-deficit* branch, which is the plan's rule and runs whether or not
entry is on.

Rows four to six are the same fact from three directions: remove the
buffer branch, shorten the stock it targets, or widen the reserve exit
leaves — any one of them and the cycle stops.

**It is a limit cycle, not a drift.** Dust Basin's yayo capacity is
16.597 at day 720, 12.134 at 1080 and 12.993 at 1440; its price 16.973,
18.416, 17.602. It neither settles nor diverges; it goes round.

## 2. Why one region and not the other

`docs/65` §5's framing — one region churns and the other converges under
identical rules — is true and its emphasis is misleading. The rules are
identical; the regions are not. They differ in exactly one number:
`dust_unit_cost` 14.0 against `river_unit_cost` 14.5, a 3.4% cost
advantage to Dust Basin.

| run | Dust Basin | Green River |
|---|---:|---:|
| baseline (14.0 / 14.5) | 0.02517 | 0.00000 |
| equal costs (14.0 / 14.0) | 0.02517 | **0.02517** |
| swapped (14.5 / 14.0) | **0.00000** | **0.02517** |
| no trade route | 0.02517 | 0.00000 |

The cycle follows the **cheaper sector**, exactly, and the trade route
has nothing to do with it — removing it changes nothing. With equal costs
both regions cycle, identically. So there is no regional asymmetry to
explain: there is a threshold in the rules, and 14.0 and 14.5 fall on
opposite sides of it. That is a bifurcation, and it is worth saying
plainly that a 3.4% difference in one cost decides whether a sector
settles or oscillates forever.

## 3. The mechanism

Two rules read the same capacity and want different things from it.

**Exit sizes capacity to a flow.** `_exit` withdraws down to a floor of
`(1 + capacity_reserve) × expected_demand` — 1.1 times what the producer
expects to sell in a day (`docs/64` §2, floored by `docs/66` §2).

**The buffer branch sizes capacity to a stock.** `_invest` wants the
region to hold `target_inventory_days` of the demand — 20 days — and to
be able to refill any deficit within `buffer_refill_horizon_days` — 60.
That needs `deficit / 60` of *spare daily capacity*, on top of the demand
itself.

The two are incompatible by arithmetic. Exit leaves spare capacity of
`0.1 × demand`, which refills `60 × 0.1 = 6` days of stock in the
horizon. The rule wants 20 days of stock. So any deficit above six days'
worth is unreachable from exit's floor, the buffer branch orders capacity
to close it, the capacity arrives 45 days later, utilization falls,
`below_going_days` runs to the investment lead time, and exit withdraws
it again. The period is the two lead times; the amplitude is whatever
stock deficit has opened in the meantime.

Neither rule is wrong on its own terms. Exit is asking "is this plant
earning the going return on what it sells?" and the buffer branch is
asking "can this sector rebuild the stock it is supposed to hold?" — and
the answers point in opposite directions whenever the second needs more
plant than the first will tolerate. A model with both, and no rule
reconciling them, oscillates.

## 4. The rule

**Capital must not withdraw the plant it would immediately rebuild.**
`_exit`'s floor gains a third term, in the market's own language rather
than the plan's:

    floor_i = max(
        min_investment_capacity,                       # docs/66
        (1 + capacity_reserve) × expected_i,           # docs/64
        expected_i + deficit_i / buffer_refill_horizon_days,
    )

with `deficit_i = max(0, target_inventory_days × expected_i − stock_i)`,
the producer's stock deficit against **its own** target — which is
`docs/62`'s per-producer target, the inventory life of its own expected
demand, and not the regional pool the buffer branch reads.

This is `docs/66` §1's invariant carried one step further. That document
said capital must not withdraw below the smallest plant the fund *could*
rebuild; this one says it must not withdraw below the plant the fund
*will* rebuild, on its own rules, within the horizon it uses. A
withdrawal that the next investment interval reverses is not a withdrawal
at all: it is a round trip that destroys capacity, spends silver
rebuilding it, and moves a price twice.

### Why this candidate and not the others

**Rejected: remove the buffer branch from the market model.** This is the
most tempting, because the buffer branch is visibly the plan's last pool
— it reads `region.inventory[name]`, a regional total, inside a model
where `docs/59` gave every producer its own stock and `docs/62` already
removed the plan's pool from the price and plan targets. And `docs/68`
weakened the case for it further: scarcity now reaches `expected_demand`
directly through the sell-out, so the flow-shortfall branch sees what
only the buffer branch used to. It kills the cycle (row four of §1).

It is rejected on measurement. With the buffer branch off, the glut's
basket shortfall goes 21.59 → **29.30** and its level 1.0384 → 1.1024:
the buffer branch is the market's only means of rebuilding a stock after
a shock, and removing it makes the recovery `docs/69` measured worse. The
right criticism of that branch is that it reads a pool, not that it
exists. Rewriting it per-producer is a larger change than this one, it
would move every `procurement.*` reading, and it should not be smuggled
in as a churn fix. It is named here as the successor question.

**Rejected: widen `capacity_reserve` to 0.25.** It works (row six) and it
is a parameter nudge of exactly the kind `docs/65` §5 said the churn must
not get. It does not say *why* 0.25; the answer would be "because 20 days
of stock over a 60-day horizon needs a quarter of the demand in spare
plant", which is the formula in §4 with the numbers already substituted
and the reasoning thrown away. A reserve is the right size for one stock
target and one horizon and wrong for every other, and the model has both
as parameters. Better to write the relation down than to hard-code one of
its solutions.

**Rejected: shorten `target_inventory_days`.** Same objection, and it
would change the whole model rather than exit.

## 5. What it does not do

- **It does not change any default.** Exit stays off; the default model
  must stay bit-identical.
- **It does not touch entry on margin**, which §1 shows is not involved.
- **It does not touch the buffer branch itself**, its regional pool
  included. That is the successor question in §4.
- **It does not claim to fix the boom.** `docs/69` §4 found exit moving
  the boom's plant from meals into yayo. Turning the buffer branch off
  takes yayo from 35.40 to 12.10 there, so part of that swing is this
  mechanism — but employment only recovers from 0.2051 to 0.3027 and
  meals capacity stays at 0.42 against 1.66, so part of it is not. §6.5
  predicts what this rule does to it and expects to leave a residue.

## 6. Predictions

6.1 Bit-identical off: all 322 metrics zero delta at the defaults.

6.2 The seeded circuit under every flag is **not** bit-identical, and
this is the one prediction that differs in kind from `docs/66` and
`docs/68`. The seed's provisioners rest at 1.003992 of their reserve
target, and their stock target is 20 days of expected demand; if their
stock is at target the new term is zero and nothing moves, and if it is
not the floor rises. `exit.equilibrium.provisioners_over_reserve_target`
is therefore the reading to look at first: it either stays at 1.003992 —
the seed is stocked, the term is dormant, and the floor only binds after
a shock — or it moves, which says the seeded circuit was carrying a stock
deficit nobody had noticed. **Both outcomes are informative and the first
is expected.**

6.3 `exit.gravitation.local_yayo_last60_range_over_level` 0.016761 →
**under 1e-3**, and the distant region's stays at 0.000218. This is the
reading the whole document exists for. The local chemfuel producer count
should fall from 17 toward Green River's 8, and `exit.producer_loss.exits_booked`
should fall substantially, because most of those exits were round trips.

6.4 The glut keeps `docs/69`'s gains: `exit.glut.basket_shortfall` stays
**under 25** and `exit.glut.end_over_reference` stays **within 5% of
1.0384**. The floor only ever stops a withdrawal, so it cannot starve a
basket; if either reading worsens materially the new term is firing where
no rebuild was coming.

6.5 `exit.boom.employment_end` 0.2051 → **between 0.28 and 0.40**: better,
because the yayo overshoot is part of this mechanism, and short of
entry's 0.4831, because the meals side is not. A reading at or above
0.45 would mean the whole `docs/69` §4 swing was this and the boom needs
no further explanation; a reading still at 0.21 would mean none of it
was, and §3's mechanism does not reach `demand_boom`.

6.6 `cost_competition` is unchanged to the bit: its incumbent withdraws
against a stock that is at target, so the third term is zero. If it
moves, the term is not reading the target `docs/62` set.

6.7 The identities close, `exits` still reconciles to `capacity_lost`,
and `python -m economy_lab overshoot` still runs.

6.8 `procurement.*`, `entry.*` and `posted.*` are all unchanged: the rule
lives inside `_exit`, which only runs under `exit_on_return`.

## 7. What would make this wrong

If 6.3 does not fall below 1e-3, the buffer branch is not the only thing
rebuilding what exit removes, and §1's third row was a coincidence of one
scenario. Look next at the flow-shortfall branch, which reads the same
`demand` and would keep ordering if `expected_demand` itself is what
cycles.

If 6.3 holds but 6.5 stays at 0.21, the boom's meals collapse is a third
mechanism and deserves its own document rather than being attached to
this one.

If 6.2's provisioners move, the seed carries a stock deficit at rest.
That would be a finding about the seed rather than about exit, and it
would put every `equilibrium`-based reading in the slice in question —
stop and measure that before going on.

If the cycle moves rather than stops — the range falls but the capacity
now oscillates on a longer period — the floor has become the new target
and the buffer branch is chasing it. That is the case where removing the
pool (the successor question in §4) is the real answer and this rule is
a palliative, and it should be said so.

## 8. Cost

Three lines in `_exit` and the arithmetic in §3 written down as a
comment, the `exit.*` metrics re-measured and re-frozen, a test asserting
that a withdrawal never lands below what the next investment interval
would rebuild, and a results document. The `gravitation` runs at 1080
days are the slow ones; about a minute of measurement.
