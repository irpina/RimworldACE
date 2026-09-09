# The exit floor: capital must not withdraw below the plant it could rebuild: design

Written before implementation. `docs/65` §3 records the defect: the
retirement clause in `_exit` deletes two of the six seeded sectors on day
45, in both regions, and no rule can rebuild them. This document says
what the floor is, which of the two candidates it takes and why, what it
does to each reading `docs/65` froze, and what it deliberately leaves
alone — because the second finding in `docs/65` §5 is not this bug and is
not fixed here.

## 1. The defect, stated as an invariant

`min_investment_capacity` (0.1) is a **build-side** floor: `_invest`
refuses to place a project smaller than it
(`economy_lab/model.py:5026`), because a plant below that size is not
worth commissioning. `_exit` uses the same constant as a **retire-side**
trigger: a withdrawal that would leave less than 0.1 takes the whole
plant instead.

For a producer whose demand is large, the two uses agree — the clause
only fires when demand has collapsed, and retiring is right. For a
producer whose *sector* is permanently smaller than the minimum plant,
they contradict each other. The seed has two such sectors in each region:

| producer | capacity | expected demand | reserve target | min plant |
|---|---:|---:|---:|---:|
| Dust tailors | 0.2500 | 0.0397 | 0.0437 | 0.1 |
| Dust herbalists | 0.2500 | 0.0397 | 0.0437 | 0.1 |

The reserve target is **below** the minimum plant, so the withdrawal can
never land legally: it stops at 0.0718 and 0.0671, the clause fires, and
the plant goes. And because `_invest` will not build below 0.1 either,
the sector cannot come back. A colony's tailor is one tailor, and the
rule deletes tailoring.

The invariant this violates:

> **Capital must not withdraw below the smallest plant it could rebuild.**

A rule that can destroy what no rule can replace is not an exit rule; it
is an irreversible shock wearing an exit rule's clothes. `docs/38`
already settled the same question for maintenance and got the opposite
answer — a loss-making sector is *disciplined, not deleted* — and this
document brings exit into line with it.

## 2. The rule

**The withdrawal is floored, and the floor is the larger of the two
sizes that matter:**

    floor_i = max(min_investment_capacity, (1 + reserve) × expected_i)
    withdrawn = min(surplus_term, capacity_i − floor_i)

with `surplus_term` the `exit_gain × (1 − r) × surplus` of `docs/64` §2,
unchanged. A producer already at or below its floor withdraws nothing.

**Retirement survives, on a condition that names what it is for.** A
producer is retired only when it expects no demand at all —
`expected_demand ≤ EPSILON` — which is the case the clause was written
for: a producer whose custom has gone, not a producer serving a small
sector faithfully. Bankruptcy (`docs/55`) is untouched and remains the
other way out; a producer that cannot pay is still retired whatever its
demand.

That is the whole change: one `max`, and a retirement condition that
reads demand instead of size.

### Why this candidate and not the other

`docs/65` §7 named two. The rejected one is **"never retire a sector's
last active seller."** It is closer to `docs/64` §2's intent and it fixes
the seed just as well, but it fails on its own terms in two ways. It
leaves a producer resting *below* the smallest plant that could replace
it, so the invariant in §1 is still violated — merely not fatally, which
is worse, because nothing then reports it. And it is a rule about
*sellers* in a model whose exit rule is otherwise entirely about
*capital*: a sector with two tiny producers would still be deletable one
at a time down to the last, which makes the protection depend on
producer count rather than on sector size. The floor does not care how
many producers there are.

The floor's cost, stated plainly: **the basket sectors will rest at 0.1,
not at their reserve target of 0.0437.** They will hold 2.5× the demand
they see, permanently, earning well below the going return and never able
to shed it. That is not an equilibrium the model would choose; it is the
model saying that a plant this small is indivisible, which is a real fact
about plant and the same fact `_invest` already asserts on the way up.
`docs/64` §6.2's "within 1% of `(1 + reserve)` times expected demand" is
therefore **still wrong after this fix**, and deliberately: the
prediction was written before the minimum plant was noticed, and it
should be replaced rather than met.

## 3. What it does not do

- **It does not touch the churn.** `docs/65` §5 found entry and exit
  alternating in Dust Basin — 73 entrants ever placed, 22 active, the
  cooperative shedding 0.4 an interval while entrants placed days earlier
  withdraw fractions — while Green River converged smoothly under
  identical rules. That is `docs/64` §7's fourth mode, it is about the
  reserve's size or the two rules' shared horizon, and both regions lost
  their tailors, so the floor is not its cause. It gets its own design.
  If it survives this fix unchanged, that is confirmation rather than
  disappointment.
- **It does not reopen the one-sided price rule** (`docs/62` §2), and it
  does not make exit return silver or matter. Construction was a sink
  (`docs/37`) and the cost of an overshoot is still the fund's.
- **It does not change the flag's default.** Exit stays off, and the
  model stays bit-identical off.

## 4. Predictions

4.1 Bit-identical off: all 322 metrics zero delta.

4.2 The seeded circuit: tailors and herbalists in both regions end at
**exactly** `min_investment_capacity`, 0.1, from 0.25; they are active;
`exit.equilibrium.garments_capacity_end` and
`medicine_capacity_end` move 0 → 0.1. The provisioners are unchanged to
the bit at 1.0036 of their reserve target, because their floor is
0.6986 and 0.1 is below it. The cooperative, the fields and the refinery
are unchanged to the bit.

4.3 The seed's flows are **not** restored to the entry run's. Capacity
still moves in three sectors, and `docs/64` §3's list of what that moves
— the plan's throughput for their inputs, and each producer's
working-capital target — still applies. What must be true instead: the
garments and medicine *price and inventory* series stop diverging after
the sectors stabilize, because production resumes.

4.4 The basket is provisioned again: `exit.glut.basket_shortfall`
94.39 → **under 1.0**, and `exit.gravitation.basket_shortfall`
115.78 → **under 1.0**. These are the readings that say the fix worked;
if either stays large the deletion was not the only thing breaking the
basket.

4.5 `demand_boom`: `exit.boom.employment_end` 0.2063 → within 5% of
entry's **0.4822**, which is `docs/64` §6.8's original prediction now
that its precondition holds.

4.6 `producer_loss` at 500 and `cost_competition`: the four clean
readings of `docs/65` §2 move by **less than 1%** — the two entrant
sizes, the yayo price at 1.1545×, and the incumbent's 1.1 — because none
of them runs through the basket and the incumbent's floor (0.2715) is
above 0.1. If they move more, the basket was inside them after all.

4.7 `regional_glut` to day 300: the level comes down from 1.3299× but
**not** inside 5% of the reference. The prediction is 1.05–1.30, and the
reason it is not `docs/64` §6.5's own prediction is §3 above: the churn
is still there. A reading inside 5% would mean the churn was the basket's
doing and `docs/65` §5 is wrong.

4.8 `gravitation`: Green River stays converged (last-60 range under
1e-4). Dust Basin's range **stays above 1%** — the churn survives — and
its chemfuel producer count stays well above entry's 13.

4.9 The three identities close as before, and `exits` still reconciles to
`capacity_lost`, in every scenario.

4.10 `python -m economy_lab overshoot` **runs**. It currently raises
`cannot price 'chemfuel': its technique requires ['garments',
'herbal_medicine'], which nothing produced` (`docs/65` §4), because
`summary()` solves the prices of production and `docs/29` made the
tailors' bench the link that makes chemfuel basic. With the basket
sectors alive at the floor, the price system has a solution again. This
is the cheapest possible check that the fix worked and should be run
first.

## 5. What would make this wrong

If 4.2's sectors do not rest at exactly 0.1, the floor is being applied
somewhere other than the withdrawal — most likely the retirement
condition is still firing, which would mean `expected_demand` reaches
EPSILON for a producer that is in fact selling.

If 4.4's shortfalls do not fall to near zero, something else deletes or
starves the basket, and the retirement clause was a symptom rather than
the cause.

If 4.6's clean readings move more than 1%, then `docs/65` §2 was wrong to
call them clean and the whole slice needs re-measuring rather than
patching.

If 4.7 and 4.8 come out *better* than predicted — the glut settling and
Dust Basin converging — then `docs/65` §5 misattributed the churn, the
alternation was downstream of the deleted basket, and there is no second
finding. That would be a good outcome and a wrong document, and it is
written down this way so it cannot be claimed afterwards either way.

## 6. Cost

One `max` and one condition in `_exit`, the twenty-two `exit.*` metrics
re-measured and re-frozen with the movement explained, the defect test in
`ExitOnReturnTests` replaced by its opposite, and a results document.
About four seconds of measurement; one small session.
