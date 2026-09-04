# Procurement: producers own their output and buy their inputs: design

Written before implementation, and after `docs/58` found that it has to
come before firm-posted prices can be well defined rather than after
them. The third of the three impositions (`docs/55` §1): production is a
regional plan solved as a daily fixed point, and orders are allocated by
a central water-filling rule. In Tesfatsion's terms this is the
coordinator the ACE Trading World exercise says to remove, and replace
with "procurement processes driven solely by interactions among the
agents actually residing within the model."

## 1. What the plan does today, and what it hides

`_planned_runs` computes, for every region and every day, a fixed point:
each producer's runs are what the sector's *requested output* — intended
outflow plus a correction toward the stock target — gives it after
`_allocate_orders` shares the request by cost or by posted price. Then
every producer draws its inputs from one regional pool, and every unit it
makes lands in the pool. Nobody owns anything; nobody decides anything
that the plan has not already decided.

Three consequences, each now measured:

- **Prices have no firm-level signal.** `docs/58` §3: with one pool, a
  producer can only respond to the pool's stock and the pool's unmet
  demand, and in a contested sector the one that is not selling raises
  its price when the pool runs short, because the pool's shortage is the
  only thing it can see.
- **Revenue has no owner.** `docs/56` pays a sale out by *supply share*,
  which is the plan's allocation read back as a property right. An
  import sold from the pool pays the local producer.
- **The plan converges by construction.** `docs/44` §"Two defects"
  records that `_planned_runs` once converged on a tolerance rather than
  a fixed point and nobody noticed until Department I made the graph
  cyclic. A procurement market has no fixed point to miss.

## 2. The rule

Off by default (`procurement = False`), bit-identical off. On, the day's
production is replaced by a sequence of decisions each producer makes
with what it holds and what it can see:

**Each producer holds its own stock**: `Producer.stock`, of its own
output, and `Producer.inputs_on_hand`, of what it has bought. The
regional pool disappears for producers; `Region.inventory` becomes the
sum of producers' stocks plus what the fund and the workers hold, and
every reading that depends on it — throughput targets, the price
pressure, the material identity — reads the sum.

**A producer decides how much to make** from its own stock against its
own target (`target_inventory_days` of its recent sales), its posted
price against its cost (the utilization curve, unchanged), and the
inputs it holds. It makes the minimum of the three. There is no sector
request and no fixed point.

**A producer buys inputs for tomorrow** from other producers' stocks at
their posted prices, cheapest first, up to what it plans to run and what
its purse can pay. A seller sells to buyers in the order they arrive,
which is the producer order, and rations pro rata when it runs out. This
is the procurement process: a bilateral posted-price market, one pass a
day, no clearing condition.

**Workers and the fund buy the same way**: from producers' stocks, at
posted prices, cheapest first.

**Sales are the firm-level signal.** A producer's posted price moves by
its own stock against its own target and its own unfilled orders; the
pool's pressure is gone because the pool is gone. `docs/57`'s rule
becomes well defined: what it lacked was a stock to respond to.

**Exports and imports are producers' sales.** Arbitrage buys from the
cheapest source producer and sells into the destination as a stock the
fund holds and sells on, which is what an importer is.

## 3. What stays exactly stationary

The seeded circuit's runs are the stationary runs of `docs/17` §7. In
procurement, each producer's decision at the seeded state must
reproduce those runs to the bit: stock at target, price at the seeded
ratio to cost, inputs on hand exactly one day's draw. The seeding must
therefore place the pool's stock into producers' hands in the proportions
the plan would have drawn, and give each producer one day of inputs.
That is a seeding change, not a rule change, and it has to be verified
by the exact-zero price range before any scenario runs.

## 4. What it deliberately does not do

- No search or matching beyond cheapest-first in producer order. No
  reputation, no contracts.
- No expectations. A producer plans from its stock and yesterday's
  sales.
- No credit: a producer buys what its purse pays for. `docs/55` is a
  prerequisite and stays on whenever procurement is on.
- No change to the value solve, the ledgers, the wage rule or the price
  of production.

## 5. Scenarios

Every existing scenario with `procurement = True`. The readings the
design cares about are the four `docs/58` could not settle: the glut's
resting level, the shortage's peak, and the two contested-sector
scenarios' posted-price spread.

## 6. Predictions

6.1 Bit-identical off. 6.2 Exactly stationary on, from the reseeded
state. 6.3 The glut rests within 15% of the reference rather than
overshooting: a producer whose own stock is above target cuts and stops
cutting when it is not, and there is no pool for a curtailed rival's
shortage to leak in from. 6.4 In `technique_change` the two provisioners'
posted prices end within 5% of each other and the cheaper one holds the
larger share, because the one losing custom sees its own stock rise.
6.5 The material and silver identities close with producer-level stock
inside them. 6.6 A day costs less than the fixed point did, because a
pass is not an iteration.

## 7. What would make this wrong

If 6.2 fails, the seeding has not placed stock where the plan drew from,
and the price range will say by how much. If 6.3 still overshoots, the
integral gain is the problem and not the pool, and `docs/58` §2's
diagnosis was incomplete.
