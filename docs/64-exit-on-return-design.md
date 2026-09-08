# Exit: capital leaves a sector that cannot earn the going return: design

Written before implementation. `docs/63` §7 named this as the missing
counterpart of entry: a producer that cannot earn the going margin at
the utilization it has should, after a time, take its capacity out.
This document says what "cannot earn", "after a time" and "take out"
are, what the rule does to the seeded circuit — which it cannot leave
alone, and this document says why before measuring — and what it
should do to each reading `docs/63` froze.

## 1. What the model does with idle capacity today

Three things remove capacity, and none of them is exit. A shock
(`destroy_capacity`) removes it by fiat. Bankruptcy (`docs/55`) removes
a producer whose purse has been unable to pay for thirty days, which a
producer that sells a little never is. Maintenance (`docs/38`) sheds the
part of a day's wear a producer cannot make good, which touches only a
process with a capital bill, and every reading in `docs/60` to `docs/63`
is taken on processes without one. For those, capacity is forever.

What the market does with idle capacity is cut, and only while the
margin is above the going one (`docs/62`). Below it, nothing. The state
that leaves is measured at day 500 of `producer_loss` with entry on:
twenty yayo producers hold 22.3 units of capacity against 10.5 units of
demand seen, every one of them at the going margin to the third
decimal, seven of them running below a third of their capacity, and the
price at 0.89× the reference where no rule moves it.

The same run shows a second thing, which the build of entry did not
read and which decides part of this design. The *shortfall* rule in
`_invest` placed leaves entrants of 66, 37, 25 and 25 units and chemfuel
entrants of 7, 4, 2.4 and 2.4 units — capacity the sectors had no use
for; the leaves sector ends at 42% utilization with its price below its
cost. It did so because the shortfall it reads is throughput above
capacity, and throughput (`Region.throughput_demands`) is every
producer's input draw *at full capacity* plus final demand *at the
reference price*. A yayo sector with 22 units of capacity running at
half draws leaves, on that reckoning, for 22. That is `docs/62`'s
hidden plan again, on the capacity side: the stock target was the plan's
pool, and the investment rule's demand is the plan's throughput. It
matters here because exit and that rule cannot coexist. Whatever exit
withdraws below the plan's throughput, the shortfall rule rebuilds at
the next interval, wherever the market's demand is below the reference
demand — which is everywhere the price is above the reference.

## 2. The rule

Off by default (`exit_on_return = False`), bit-identical off. It needs
procurement, as procurement needs purses and posted prices: the signal
is a producer's expected demand against its own posted price, and
neither exists without it.

**The signal is the producer's return relative to the going one.**
`docs/30` established that the classical signal is the rate of profit
on capital advanced, and `docs/61` §3 showed that for a bill-free
process the margin and the rate of profit are the same number over 60
*per unit sold*. Capital is advanced per unit of *capacity*. So the
return on capital is the margin times the utilization, and a producer
earning the going margin on half its capacity earns half the going
return:

    r = u × m / going_margin

with `u` the producer's expected demand over its full-capacity output,
capped at one, and `m` its posted margin over its effective cost. Both
are numbers the producer already keeps (`docs/62`). A return below the
going one — `r < 1` — is the condition for leaving; a margin above the
going one, with capacity idle, is still the condition for cutting. Both
can hold at once, and where they do both act: the cut brings the margin
down and demand up, the withdrawal brings capacity down, and the rest
they share is the going margin at a capacity the demand uses.

**What leaves is the surplus beyond a reserve.** A producer keeps
`capacity_reserve` (0.10) spare over the demand it expects, so that a
demand a tenth larger is served without a sell-out; capacity beyond
`(1 + reserve) × expected demand` is surplus. A producer with a return
below the going one and no surplus has nothing to withdraw: it is
earning too little on capacity it uses, and its answer is the price,
not the plant.

**After a time is the lead time.** A producer counts the consecutive
days on which its return has been below the going one with a surplus
to withdraw, and withdraws only once the count reaches
`investment_lead_days` (45). Capital leaves on the horizon on which it
arrives, and no new number says how long that is. A glut whose trough
is shorter than the lead draws no exit.

**The amount, at each investment interval, is proportional to how far
below.** Mirroring the entry term:

    withdrawn = exit_gain × (1 − r) × surplus

with `exit_gain` 1.0. Zero at the going return, zero with no surplus,
and geometric toward the reserve otherwise: a producer at half the
going return with a unit of surplus takes out half a unit, then a
quarter. Withdrawn capacity is booked to `capacity_lost`, as a shock's
and a bankruptcy's are, and to a new `exits` ledger with the day, the
region, the producer and the amount.

**A producer below the minimum plant leaves entirely.** Capacity that
the withdrawal would take below `min_investment_capacity` (0.1) — a
plant smaller than the smallest the fund would build — goes to zero,
the producer is retired, and its purse and its stock return to the fund
as a bankrupt's do. A sector whose whole demand is below that size is
then served by nobody; no scenario has one, and the case is recorded
rather than handled.

**Nothing comes back.** Construction was a sink (`docs/37`): the silver
became plant and the model keeps no plant account. Exit returns no
silver and no matter. The cost of an overshoot is the fund's, and it is
paid.

**The investment rule reads the market's demand.** With the flag on,
the `demand` `_invest` reads for a sector — for the shortfall, the
buffer deficit, the inventory days and the entry term's scale — is the
sum of its active producers' expected demand, and the plan's throughput
only where the sector has no producer to expect anything. This is the
one change to what the shortfall term does with the flag on, and §1
says why it is not optional: without it the rule rebuilds what exit
withdraws. It is the capacity-side twin of `docs/62`'s correction and
is made under this flag rather than as a correction to procurement
because procurement's readings do not depend on it — nothing withdrew
capacity there for the plan to rebuild — and because the shortfall
rule's demand is what `docs/61` deliberately left as it was.

## 3. Why it cannot leave the seeded circuit alone

Every rule so far has been exactly stationary on the seeded circuit
with its flag on, and each one managed that because it fires only
*above* something the seed is below — a going margin of 0.50 above
every seeded margin. Exit fires below, and the seed is below it
everywhere. Measured with the market and entry on, at day 240:

| producer (Dust Basin) | capacity | demand expected | capacity / demand | margin | r |
|---|---:|---:|---:|---:|---:|
| yayo cooperative | 10.00 | 10.00 | 1.00 | 0.291 | 0.58 |
| psychoid fields | 80.00 | 80.00 | 1.00 | 0.410 | 0.82 |
| refinery | 6.23 | 6.04 | 1.03 | 0.458 | 0.89 |
| provisioners | 1.00 | 0.635 | 1.58 | 0.424 | 0.54 |
| tailors | 0.25 | 0.040 | 6.30 | 0.429 | 0.14 |
| herbalists | 0.25 | 0.040 | 6.30 | 0.358 | 0.11 |

The authored capacities of the three basket sectors are 1.6 to 6.3
times their demand: a colony's tailor is one tailor, whatever the
colony wears. No rule that reads idle capacity or the return on it can
be silent there, and a threshold low enough to be silent — below a
return of 0.11 — would be silent in the overshoot this rule exists for,
where the returns are 0.08 to 0.98. The reserve does not help: the
surplus is 84% of the plant.

So this design gives up exact stationarity of the seed's *capacity*
and keeps it for everything else, and says which is which before
measuring. The three basket sectors withdraw their authored surplus
from day 45; no price, stock, sale, or purse moves, because each of
those producers' ceiling — its capacity at the utilization curve, which
is at one above 1.05× cost — stays above its plan, so its runs, its
sales and its stock are the same floats. What does move besides
capacity: the plan's throughput for their inputs, which the fund's
price and the arbitrage targets read (`docs/60`), and which at the seed
neither acts on; and each producer's working-capital target, which is a
day at full capacity, so a one-time distribution to the fund. Prediction
6.2 says exactly this, and if the flows move it is a finding.

## 4. What it deliberately does not do

- **No raise from below.** A price below the going margin with its
  capacity fully used stays where it is: the one-sided price rule
  (`docs/62` §2, the symmetric term tried and taken out) is not
  reopened. Exit restores the *reach* of the sell-out — capacity near
  demand, so the next increase is scarce and raises — and not the level.
  Where a level rests below the reference after exit, it is the
  one-sided rule's and is recorded as such.
- **No foresight.** A glut's trough draws exit; when the fund's stock is
  gone the withdrawn capacity is missed, the sell-outs raise, and entry
  answers 45 days later. That is the classical cycle, and this design
  damps it with the lead and the reserve and nothing else. Its
  amplitude is one of the things measured.
- **No change to the planned model.** The flag refuses without
  procurement, as procurement refuses without purses.

## 5. Scenarios

Every scenario `docs/63` read, on the market with entry and exit both
on at the default going margin, so each reading sits beside entry's;
`producer_loss` run to day 500 as well as day 210, and `regional_glut`
to day 300 as well as day 180, because exit's work is after the
horizon the earlier documents set. `gravitation` with exit added. One
new catalog scenario, `overshoot`: the 60% capacity loss with entry and
exit, 500 days, where entry's pipeline overshoots and exit takes the
surplus out.

## 6. Predictions

6.1 Bit-identical off.

6.2 The seeded circuit: every price, stock and sales series in both
regions bit-identical to the market's with entry on, for every
commodity; the capacity of tailors, herbalists and provisioners ends
within 1% of `(1 + reserve)` times their expected demand; the capacity
of the cooperative, the fields and the refinery is unchanged to the bit;
the first withdrawal is on day 45.

6.3 `producer_loss` at day 500: yayo capacity between 1.0 and 1.2 times
the demand seen (entry alone: 2.1 times), and fewer than the entry run's
twenty producers. No project is placed in leaves or chemfuel larger
than that sector's expected demand: the 66-unit leaves entrant does not
appear.

6.4 `producer_loss` at day 500: the yayo price rests between 0.95× and
1.20× the reference (entry alone: 0.89×). The rest is cost times one
plus the going margin either way; what changes is the cost, because the
leaves sector is no longer flooded by the plan's throughput and its
price is cut only by the shortage's own fall in yayo's draw.

6.5 `regional_glut`: the trough outlasts the lead (83 days below 0.95×
against 45), so exit fires; when the fund's stock is gone the price
overshoots the reference — a peak above 1.03× after day 150 — and by
day 300 it is within 5% of the reference with yayo capacity between 1.0
and 1.2 times demand. The glut is no longer the market's own run.

6.6 `cost_competition`: the incumbent, at 37% of the custom and a return
below the going one, withdraws to its custom plus the reserve — capacity
below 0.5 from 1.0 — and the meal price and the cheap technique's share
are within 2% of entry's, because the split is by price and the
incumbent's price does not move.

6.7 `gravitation` with exit, 720 days: every sector in both regions ends
with capacity between 1.0 and 1.15 times its expected demand, its
margin within 0.07 of the going one, and its price's range over the
last 60 days under 1% of its level; chemfuel ends with fewer than the
thirteen producers entry alone left it.

6.8 `demand_boom`: employment on day 360 within 5% of entry's 0.482,
because employment is realized runs and those are demand either way;
the yayo price ends above entry's 0.88×, because the surplus the
shortfall rule built for the boom leaves and the sell-out can reach
again.

6.9 The three identities close in every scenario, with procurement's
tolerances, and the `exits` ledger sums to what `capacity_lost` gained
under the flag.

## 7. What would make this wrong

If 6.2's flows move, the plan's throughput is inside a flow at the
seed — the fund's price or the arbitrage targets — and the correction
`docs/62` made to the stock target is owed there too. If 6.5's price is
not within 5% at day 300, the lead and the reserve do not damp the
classical cycle, and a longer memory for the return than for demand is
the next parameter to read. If 6.4 rests below 0.95×, the cost is
depressed by a one-sided rule that exit cannot reach, and a raise from
below — the term `docs/62` removed — is the next design, with the reason
it was removed answered first. If a sector shows exits and projects
alternating, the shortfall rule with expected demand is rebuilding
what exit withdraws inside the reserve, and the reserve is the wrong
size.

## 8. Cost

The entry readings again with exit on, plus a 500-day loss run and a
300-day glut run: about five seconds in all, none frozen at the long
horizon beyond the readings named.
