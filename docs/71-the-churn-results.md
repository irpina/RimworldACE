# The churn: a cobweb above unit elasticity: results

`docs/70` is the design. Its rule was built, measured against its own
predictions, and **reverted**. This document says why, and what the churn
turned out to be — because the measurement that refused the rule also
found the mechanism, and it is not the one `docs/70` §3 wrote down.

**The headline: the churn is a cobweb, and it exists because final demand
is elastic. A sector that cuts its price sells more; above unit
elasticity it sells more than proportionately, so the revenue the cut was
supposed to cost never arrives, capacity chases the demand the cut
created, and the price falls further — until the stock drains, the price
turns, and the whole thing runs backwards. Below unit elasticity every
sector converges. At the default 1.35 the cheaper sector cycles forever.**

## 1. What was built, and what it did

`docs/70` §4's floor: exit's withdrawal floored additionally at
`expected + deficit / buffer_refill_horizon_days`, the plant the
investment rule would put back at once. Three lines in `_exit`, a helper
`_rebuild_floor`, and the arithmetic of `docs/70` §3 as its docstring.

It behaved. The floors it computed were real — the seed's cooperative got
0.053 against a capacity of 0.100, an entrant 0.104 against 0.102 — and
nine `exit.*` readings moved. Every prediction about *scope* held: the
default model bit-identical (6.1), the seeded circuit bit-identical
(6.2), `cost_competition` bit-identical (6.6), and `procurement.*`,
`entry.*` and `posted.*` untouched (6.8).

And the one prediction the rule existed for failed completely.
`exit.gravitation.local_yayo_last60_range_over_level` was predicted to
fall from 0.016761 to under 1e-3. It did not move **at all** — not
reduced, not displaced onto a longer period, unchanged to the last digit.
`docs/70` §7 said a cycle that moves rather than stops would mean the
floor had become the new target; a cycle that does not notice the floor
means the floor is not on the path.

The rule is reverted. It changed nine frozen readings, including
`exit.glut.end_over_reference` from 1.0384 to 0.9284, in exchange for
nothing it was built to buy. A floor that binds where the cycle is not is
not a smaller version of the right rule; it is a different rule with no
argument behind it.

## 2. What the cycle actually does

One period of Dust Basin's yayo in `gravitation`, sampled every 45 days.
`demand` is the sector's expected demand, `spare` its capacity and
pipeline over that demand, `refill` the days the buffer branch reckons it
needs to close the stock deficit.

| day | capacity | demand | spare | stock | deficit | refill | price |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 315 | 12.565 | 11.575 | 1.457 | 169.2 | 62.3 | 42.8 | 18.818 |
| 405 | 13.247 | 12.244 | 1.593 | 166.1 | 78.8 | 49.4 | 18.550 |
| 495 | 13.697 | 12.766 | 1.689 | 154.3 | 101.0 | 59.8 | 18.050 |
| 540 | 13.989 | 13.104 | 1.737 | 148.5 | 113.6 | **65.4** | 17.752 |
| 630 | 15.170 | 14.086 | 3.107 | 142.9 | 138.8 | 44.7 | 17.253 |
| 720 | 16.609 | 14.710 | 2.830 | 170.1 | 124.1 | 43.9 | 16.973 |
| 810 | 14.755 | 12.903 | 1.852 | 231.7 | 26.3 | 14.2 | 17.227 |
| 900 | 12.801 | 11.851 | 0.951 | 228.5 | 8.5 | 9.0 | 18.535 |

Read the demand column. It is **not** constant: 11.58 → 14.71 → 11.85,
moving 27% over the cycle and moving *with* the capacity and *against*
the price. `docs/70` §3 assumed a fixed demand that exit and the buffer
branch fought over. There is no fixed demand to fight over. Demand is an
output of the price, and the price is an output of the capacity, and the
capacity is chasing the demand.

`Region.daily_demand` is `base × (price / reference) ** −elasticity`,
with `demand_elasticity` 1.35 by default. That is the loop's gain, and it
has been in the model since long before any of these rules.

Day 540 is the turn: the deficit's refill time crosses the 60-day horizon
and the buffer branch fires for the first time in the period, ordering
the capacity that takes the sector from 13.99 to 16.61 over the next six
months. That is the role the buffer branch plays — the trigger, not the
engine — and it is why turning it off in `docs/70` §1 stopped the cycle.
`docs/70` read that ablation as identifying the mechanism. It identified
a necessary condition.

## 3. The elasticity, and the threshold at one

`gravitation`, 1080 days, Dust Basin's yayo, everything else at the
defaults:

| demand elasticity | last-60 range | capacity | exits |
|---:|---:|---:|---:|
| 0.00 | 0.00000 | 10.000 | 150 |
| 0.15 | 0.00000 | 10.413 | 143 |
| 0.30 | 0.00000 | 11.004 | 87 |
| 0.60 | 0.00000 | 11.604 | 138 |
| 0.90 | 0.00000 | 11.985 | 175 |
| **1.20** | **0.02583** | 11.737 | 415 |
| **1.35** (default) | **0.02517** | 12.134 | 488 |

The bifurcation sits between 0.9 and 1.2 — at, or very near, **unit
elasticity**, which is exactly where the economics says it should be.
Below one, a price cut costs the sector revenue, and a sector losing
revenue stops cutting. Above one, a price cut *raises* revenue: the
demand it creates more than pays for the price it gives up, so nothing in
the sector's own books tells it to stop, and it keeps building capacity
for the demand its last cut created. The stock is what eventually stops
it, and stocks turn slowly, which is why the period is measured in
hundreds of days.

This also explains `docs/70` §2's cost bifurcation without needing a
separate account of it. Dust Basin's 3.4% cost advantage is not a
different rule; it is room to keep cutting. The dearer sector hits its
cost and stops before the elastic response compounds; the cheaper one has
further to fall, so it completes the loop. Equal costs and both regions
cycle identically, which `docs/70` §2 measured and could not explain.

## 4. What stands from `docs/70`

Three findings survive intact, and they are the reason that document was
worth writing even though its rule was not worth keeping:

- **Entry on margin is not involved.** With it off the cycle is
  bit-identical: same range, same capacity, same price, same 488 exits.
  `docs/65` §5's "entry and exit alternating" is wrong, and this is now
  measured twice.
- **The buffer branch is necessary to it**, as the trigger. Removing it,
  shortening the stock it targets, or widening exit's reserve each stops
  the cycle — all three by denying the trigger, none by touching the
  engine.
- **The cycle follows the cheaper sector, not the region**, and the trade
  route has nothing to do with it.

What does not stand is `docs/70` §3's mechanism — a stock target and a
flow reserve fighting over a fixed capacity — and §4's rule with it.

## 5. What the rule should be, and why it is not in this document

The engine is a price rule with positive feedback and no term that reads
its own gain. Three candidates, none built:

1. **Cut on excess, not on idleness, above unit elasticity.** The posted
   price cuts while capacity is idle (`docs/62`). Where demand is elastic
   enough, idleness is self-replenishing: the cut removes it by creating
   demand, so the rule never runs out of reason to cut. A price rule that
   read the revenue it was giving up would stop at unit elasticity of its
   own accord.
2. **Let investment read the price it will cause.** `_invest` sizes
   capacity against `expected_demand`, which is demand at *today's*
   price. The capacity arrives 45 days later and lowers the price, which
   raises demand again. A rule that discounted the demand its own
   pipeline will create is the standard answer to a cobweb and the most
   invasive of the three.
3. **Damp the expectation instead of the rule.** `expectation_alpha` is
   0.05; the cycle's period is hundreds of days, so the expectation
   tracks the swing rather than averaging it. This is the parameter
   answer and it is the weakest: it would slow the cycle, not remove its
   cause.

The first is the one this laboratory's arc points at, because it is the
same kind of correction as `docs/62` — a rule reading the wrong quantity
— rather than a new mechanism. It needs its own design, and it should not
be written in a results document.

**It is also the first thing in this slice that is not obviously a
defect.** A model of capitalist competition in which cheap sectors
overbuild, crash and rebuild is not self-evidently wrong; `docs/64` §7
listed "a real cycle" among the modes exit might produce, and this is
one, with a period and a threshold and a cause. Whether to damp it or to
keep it and measure it is a question about what the laboratory is for,
and the next document should answer that before it changes anything.

## 6. The reference

Unchanged: **322** metrics, every one at zero delta, because the rule was
reverted. `docs/70` stays in the repository as the design that was
refused, with this document as its correction — the same relation
`docs/60` has to `docs/62`.

## 7. Cost

The rule built and reverted; four ablation sweeps of `gravitation` at
1080 days (entry, buffer, reserve, inventory target), a six-point
elasticity sweep, a cost-swap triple, and one 72-interval instrumented
trace: about six minutes of measurement. None of the traces is frozen.
